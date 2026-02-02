from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, date
from calendar import monthrange
import os
import io
import csv
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, auth, firestore

load_dotenv()

app = Flask(__name__)

# ==================== Firebase Admin / Firestore 初期化 ====================

APP_DIR = Path(__file__).resolve().parent

# .env の GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json を想定
cred_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./serviceAccountKey.json")
cred_path = (APP_DIR / cred_env).resolve() if cred_env.startswith("./") else Path(cred_env).expanduser().resolve()

if not cred_path.exists():
    raise FileNotFoundError(
        f"[Firebase] service account key not found: {cred_path}\n"
        f"Fix: Put serviceAccountKey.json next to app.py OR set GOOGLE_APPLICATION_CREDENTIALS in .env"
    )

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(str(cred_path)))

fs = firestore.client()

# ==================== Auth Decorator ====================

def require_firebase_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer token"}), 401

        id_token = auth_header.split("Bearer ")[1].strip()
        try:
            decoded = auth.verify_id_token(id_token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        request.firebase_uid = decoded["uid"]
        return fn(*args, **kwargs)
    return wrapper

def tasks_ref(uid: str):
    # users/{uid}/tasks/{docId}
    return fs.collection("users").document(uid).collection("tasks")

def _to_iso(value):
    if value is None:
        return None
    # Firestore Timestamp -> datetime
    if hasattr(value, "to_datetime"):
        value = value.to_datetime()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

def _doc_to_task(doc):
    d = doc.to_dict() or {}
    return {
        "id": doc.id,  # Firestore docId（文字列）
        "task_name": d.get("task_name"),
        "category": d.get("category"),
        "memo": d.get("memo", ""),
        "created_date": d.get("created_date"),          # "YYYY-MM-DD"
        "created_at": _to_iso(d.get("created_at")),     # ISO
        "start_time": _to_iso(d.get("start_time")),     # ISO
        "end_time": _to_iso(d.get("end_time")),         # ISO
        "duration_seconds": int(d.get("duration_seconds") or 0),
    }

# ==================== 画面表示 ====================

@app.route("/")
def index():
    return render_template("index.html")

# ==================== API ====================

@app.route("/api/task/add", methods=["POST"])
@require_firebase_auth
def api_add_task():
    uid = request.firebase_uid
    data = request.get_json() or {}

    task_name = data.get("task_name")
    category = data.get("category")
    memo = data.get("memo", "")
    created_date = data.get("created_date")  # optional "YYYY-MM-DD"

    if not task_name or not category:
        return jsonify({"error": "task_nameとcategoryは必須です"}), 400

    if created_date:
        try:
            datetime.strptime(created_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "created_date形式が不正です (YYYY-MM-DD)"}), 400
    else:
        created_date = date.today().isoformat()

    doc_ref = tasks_ref(uid).document()  # 自動docId
    payload = {
        "task_name": task_name,
        "category": category,
        "memo": memo,
        "created_date": created_date,
        "created_at": firestore.SERVER_TIMESTAMP,
        "start_time": None,
        "end_time": None,
        "duration_seconds": 0,
    }
    doc_ref.set(payload)

    return jsonify({
        "success": True,
        "task": {
            "id": doc_ref.id,
            "task_name": task_name,
            "category": category,
            "memo": memo,
            "created_date": created_date,
            "created_at": None,
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
        }
    }), 201

@app.route("/api/tasks/date")
@require_firebase_auth
def api_tasks_by_date():
    uid = request.firebase_uid
    date_str = request.args.get("date")

    if not date_str:
        return jsonify({"error": "dateパラメータは必須です"}), 400
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "日付形式が不正です (YYYY-MM-DD)"}), 400

    # インデックス不要にするため order_by を削除
    q = tasks_ref(uid).where("created_date", "==", date_str)

    docs = list(q.stream())
    tasks = [_doc_to_task(d) for d in docs]
    # Python側でソート（created_atの降順）
    tasks.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    
    return jsonify({"success": True, "tasks": tasks}), 200

@app.route("/api/tasks/today")
@require_firebase_auth
def api_tasks_today():
    uid = request.firebase_uid
    today = date.today().isoformat()
    
    # インデックス不要にするため order_by を削除
    q = tasks_ref(uid).where("created_date", "==", today)
    
    docs = list(q.stream())
    tasks = [_doc_to_task(d) for d in docs]
    # Python側でソート（created_atの降順）
    tasks.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    
    return jsonify({"success": True, "tasks": tasks}), 200

@app.route("/api/task/start", methods=["POST"])
@require_firebase_auth
def api_task_start():
    uid = request.firebase_uid
    data = request.get_json() or {}
    task_id = data.get("task_id")  # Firestore docId（文字列）

    if not task_id:
        return jsonify({"error": "task_idは必須です"}), 400

    doc_ref = tasks_ref(uid).document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"error": "タスクが見つかりません"}), 404

    d = doc.to_dict() or {}
    if d.get("start_time") is not None:
        return jsonify({"error": "タスクは既に開始されています"}), 400

    doc_ref.update({"start_time": firestore.SERVER_TIMESTAMP})
    doc2 = doc_ref.get()
    return jsonify({"success": True, "task": _doc_to_task(doc2)}), 200

@app.route("/api/task/stop", methods=["POST"])
@require_firebase_auth
def api_task_stop():
    uid = request.firebase_uid
    data = request.get_json() or {}
    task_id = data.get("task_id")

    if not task_id:
        return jsonify({"error": "task_idは必須です"}), 400

    doc_ref = tasks_ref(uid).document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"error": "タスクが見つかりません"}), 404

    d = doc.to_dict() or {}
    start_time = d.get("start_time")
    end_time = d.get("end_time")

    if start_time is None:
        return jsonify({"error": "タスクが開始されていません"}), 400
    if end_time is not None:
        return jsonify({"error": "タスクは既に停止されています"}), 400

    # Timestamp -> datetime
    start_dt = start_time.to_datetime() if hasattr(start_time, "to_datetime") else start_time
    now_dt = datetime.utcnow()
    duration_seconds = int((now_dt - start_dt.replace(tzinfo=None)).total_seconds())
    if duration_seconds < 0:
        duration_seconds = 0

    doc_ref.update({
        "end_time": firestore.SERVER_TIMESTAMP,
        "duration_seconds": duration_seconds,
    })
    doc2 = doc_ref.get()
    return jsonify({"success": True, "task": _doc_to_task(doc2)}), 200

@app.route("/api/task/update/<task_id>", methods=["POST"])
@require_firebase_auth
def api_task_update(task_id):
    uid = request.firebase_uid
    data = request.get_json() or {}

    task_name = data.get("task_name")
    category = data.get("category")
    memo = data.get("memo", "")

    if not task_name or not category:
        return jsonify({"error": "task_nameとcategoryは必須です"}), 400

    doc_ref = tasks_ref(uid).document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"error": "タスクが見つかりません"}), 404

    doc_ref.update({
        "task_name": task_name,
        "category": category,
        "memo": memo,
    })
    doc2 = doc_ref.get()
    return jsonify({"success": True, "task": _doc_to_task(doc2)}), 200

@app.route("/api/task/delete/<task_id>", methods=["POST"])
@require_firebase_auth
def api_task_delete(task_id):
    uid = request.firebase_uid
    doc_ref = tasks_ref(uid).document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"error": "タスクが見つかりません"}), 404

    doc_ref.delete()
    return jsonify({"success": True, "message": "タスクを削除しました"}), 200

@app.route("/api/report/monthly", methods=["GET"])
@require_firebase_auth
def api_report_monthly():
    uid = request.firebase_uid

    year = request.args.get("year", type=int) or datetime.now().year
    month = request.args.get("month", type=int) or datetime.now().month
    group_by = request.args.get("group_by", "category")  # category / project

    if not (1 <= month <= 12):
        return jsonify({"error": "月は1-12の範囲で指定してください"}), 400

    group_field = "category" if group_by == "category" else "task_name"

    start_date = f"{year}-{month:02d}-01"
    _, last_day = monthrange(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"

    q = (tasks_ref(uid)
         .where("created_date", ">=", start_date)
         .where("created_date", "<=", end_date))

    docs = list(q.stream())
    rows = [d.to_dict() or {} for d in docs]

    grouped = {}
    total_seconds = 0
    total_tasks = 0
    unique_days = set()

    for r in rows:
        total_tasks += 1
        unique_days.add(r.get("created_date"))
        sec = int(r.get("duration_seconds") or 0)
        total_seconds += sec

        key = r.get(group_field) or "(未設定)"
        if key not in grouped:
            grouped[key] = {"name": key, "task_count": 0, "total_seconds": 0}
        grouped[key]["task_count"] += 1
        grouped[key]["total_seconds"] += sec

    data = []
    for v in grouped.values():
        v["total_hours"] = round(v["total_seconds"] / 3600.0, 1)  # 小数第1位に変更
        data.append(v)
    data.sort(key=lambda x: x["total_seconds"], reverse=True)

    totals = {
        "total_days": len(unique_days),
        "total_tasks": total_tasks,
        "total_seconds": total_seconds,
        "total_hours": round(total_seconds / 3600.0, 1),  # 小数第1位に変更
    }

    return jsonify({
        "success": True,
        "year": year,
        "month": month,
        "group_by": group_by,
        "data": data,
        "totals": totals,
    }), 200

@app.route("/api/export/csv", methods=["GET"])
@require_firebase_auth
def api_export_csv():
    uid = request.firebase_uid

    year = request.args.get("year", type=int) or datetime.now().year
    month = request.args.get("month", type=int) or datetime.now().month

    start_date = f"{year}-{month:02d}-01"
    _, last_day = monthrange(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"

    # インデックス不要にするため order_by を削除
    q = (tasks_ref(uid)
         .where("created_date", ">=", start_date)
         .where("created_date", "<=", end_date))

    docs = list(q.stream())
    tasks = [_doc_to_task(d) for d in docs]
    # Python側でソート（created_dateの昇順）
    tasks.sort(key=lambda x: x.get("created_date") or "")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID(docId)", "タスク名", "カテゴリ", "メモ",
        "開始時刻", "終了時刻", "作業時間(秒)", "作業時間(時間)",
        "作成日", "作成日時"
    ])

    for t in tasks:
        hours = round((t.get("duration_seconds") or 0) / 3600.0, 2)
        writer.writerow([
            t["id"],
            t.get("task_name"),
            t.get("category"),
            t.get("memo") or "",
            t.get("start_time") or "",
            t.get("end_time") or "",
            t.get("duration_seconds") or 0,
            hours,
            t.get("created_date") or "",
            t.get("created_at") or "",
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"tasks_{year}_{month:02d}.csv",
    )

@app.route("/health")
def health_check():
    try:
        fs.collection("_health").document("ping").set({"at": firestore.SERVER_TIMESTAMP}, merge=True)
        return jsonify({"status": "healthy", "firestore": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "firestore": "disconnected", "error": str(e)}), 500

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "エンドポイントが見つかりません"}), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
