from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv
import csv
import io
from calendar import monthrange

load_dotenv()

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'todo_db'),
    'user': os.getenv('DB_USER', 'todo_user'),
    'password': os.getenv('DB_PASSWORD', 'todo_password'),
    'port': os.getenv('DB_PORT', '5432')
}

def get_db_connection():
    """データベース接続を取得"""
    return psycopg2.connect(**DB_CONFIG)

# ==================== 画面表示 ====================

@app.route('/')
def index():
    """タスク登録画面（当日のタスク一覧含む）"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM tasks 
            WHERE created_date = CURRENT_DATE 
            ORDER BY created_at DESC
        """)
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        
        db_info = {
            'type': 'PostgreSQL',
            'database': DB_CONFIG['database'],
            'user': DB_CONFIG['user'],
            'host': f"{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        }
        
        return render_template('index.html', tasks=tasks, db_info=db_info)
    except Exception as e:
        return render_template('index.html', tasks=[], error=str(e))

@app.route('/report')
def report():
    """月次レポート画面"""
    return render_template('report.html')

# ==================== HTMLフォーム用の互換ルート ====================

@app.route('/add', methods=['POST'])
def add_task_form():
    """HTMLフォームからのタスク登録（互換性用）"""
    task_name = request.form.get('title')
    category = request.form.get('category', 'その他')  # デフォルトカテゴリ
    
    if not task_name:
        return render_template('index.html', tasks=[], error='タスク名を入力してください')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO tasks (task_name, category, memo)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (task_name, category, ''))
        conn.commit()
        cur.close()
        conn.close()
        
        # リダイレクトで画面を再読み込み
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('index.html', tasks=[], error=str(e))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task_form(task_id):
    """HTMLフォームからのタスク削除（互換性用）"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            cur.close()
            conn.close()
            return redirect(url_for('index'))
        
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return redirect(url_for('index'))

# ==================== API エンドポイント ====================

@app.route('/api/task/add', methods=['POST'])
def add_task():
    """新規タスク登録
    
    Request Body (JSON):
        {
            "task_name": "タスク名",
            "category": "カテゴリ",
            "memo": "メモ (オプション)",
            "firebase_uid": "ユーザーID (オプション)"
        }
    
    Response:
        201: {"success": true, "task": {...}}
        400: {"error": "エラーメッセージ"}
    """
    data = request.get_json()
    task_name = data.get('task_name')
    category = data.get('category')
    memo = data.get('memo', '')
    firebase_uid = data.get('firebase_uid')
    
    if not task_name or not category:
        return jsonify({'error': 'task_nameとcategoryは必須です'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO tasks (task_name, category, memo, firebase_uid)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """, (task_name, category, memo, firebase_uid))
        new_task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'task': dict(new_task)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/today')
def get_today_tasks():
    """今日のタスク一覧を取得"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM tasks 
            WHERE created_date = CURRENT_DATE 
            ORDER BY created_at DESC
        """)
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'tasks': [dict(t) for t in tasks]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/task/start', methods=['POST'])
def start_task():
    """タイマー開始
    
    Request Body (JSON):
        {
            "task_id": 1,
            "firebase_uid": "ユーザーID (オプション)"
        }
    
    Response:
        200: {"success": true, "task": {...}}
        400/404: {"error": "エラーメッセージ"}
    """
    data = request.get_json()
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'task_idは必須です'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT start_time FROM tasks WHERE id = %s", (task_id,))
        task = cur.fetchone()
        
        if not task:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクが見つかりません'}), 404
        
        if task['start_time']:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクは既に開始されています'}), 400
        
        cur.execute("""
            UPDATE tasks SET start_time = CURRENT_TIMESTAMP
            WHERE id = %s RETURNING id, task_name, start_time
        """, (task_id,))
        updated_task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'task': dict(updated_task)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/task/stop', methods=['POST'])
def stop_task():
    """タイマー停止
    
    Request Body (JSON):
        {
            "task_id": 1,
            "firebase_uid": "ユーザーID (オプション)"
        }
    
    Response:
        200: {"success": true, "task": {...}}
        400/404: {"error": "エラーメッセージ"}
    """
    data = request.get_json()
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'task_idは必須です'}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT start_time, end_time FROM tasks WHERE id = %s", (task_id,))
        task = cur.fetchone()
        
        if not task:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクが見つかりません'}), 404
        
        if not task['start_time']:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクが開始されていません'}), 400
        
        if task['end_time']:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクは既に停止されています'}), 400
        
        cur.execute("""
            UPDATE tasks
            SET end_time = CURRENT_TIMESTAMP,
                duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time))::INTEGER
            WHERE id = %s RETURNING *
        """, (task_id,))
        updated_task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'task': dict(updated_task)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/task/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    """タスク削除
    
    Response:
        200: {"success": true, "message": "..."}
        404: {"error": "エラーメッセージ"}
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
        deleted = cur.fetchone()
        
        if not deleted:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクが見つかりません'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'タスクを削除しました'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report/monthly', methods=['GET'])
def get_monthly_report():
    """月次集計データ取得
    
    Query Parameters:
        year: 年 (デフォルト: 現在の年)
        month: 月 (デフォルト: 現在の月)
        group_by: category または project (デフォルト: category)
        firebase_uid: ユーザーID (オプション)
    
    Response:
        200: {"success": true, "data": [...], "totals": {...}}
    """
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month
    group_by = request.args.get('group_by', 'category')
    firebase_uid = request.args.get('firebase_uid')
    
    if not (1 <= month <= 12):
        return jsonify({'error': '月は1-12の範囲で指定してください'}), 400
    
    try:
        start_date = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year}-{month:02d}-{last_day}"
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        group_column = 'category' if group_by == 'category' else 'task_name'
        query = f"""
            SELECT {group_column} as name,
                   COUNT(*) as task_count,
                   SUM(duration_seconds) as total_seconds,
                   ROUND(SUM(duration_seconds) / 3600.0, 2) as total_hours
            FROM tasks
            WHERE created_date >= %s AND created_date <= %s
        """
        params = [start_date, end_date]
        
        if firebase_uid:
            query += " AND firebase_uid = %s"
            params.append(firebase_uid)
        
        query += f" GROUP BY {group_column} ORDER BY total_seconds DESC"
        cur.execute(query, params)
        grouped_data = cur.fetchall()
        
        # 合計
        total_query = """
            SELECT COUNT(*) as total_tasks,
                   SUM(duration_seconds) as total_seconds,
                   ROUND(SUM(duration_seconds) / 3600.0, 2) as total_hours
            FROM tasks WHERE created_date >= %s AND created_date <= %s
        """
        total_params = [start_date, end_date]
        if firebase_uid:
            total_query += " AND firebase_uid = %s"
            total_params.append(firebase_uid)
        
        cur.execute(total_query, total_params)
        totals = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'group_by': group_by,
            'data': [dict(row) for row in grouped_data],
            'totals': dict(totals) if totals else {'total_tasks': 0, 'total_seconds': 0, 'total_hours': 0}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """CSV形式でエクスポート
    
    Query Parameters:
        year: 年 (デフォルト: 現在の年)
        month: 月 (デフォルト: 現在の月)
        firebase_uid: ユーザーID (オプション)
    """
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month
    firebase_uid = request.args.get('firebase_uid')
    
    try:
        start_date = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year}-{month:02d}-{last_day}"
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT * FROM tasks
            WHERE created_date >= %s AND created_date <= %s
        """
        params = [start_date, end_date]
        if firebase_uid:
            query += " AND firebase_uid = %s"
            params.append(firebase_uid)
        query += " ORDER BY created_date, created_at"
        
        cur.execute(query, params)
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'タスク名', 'カテゴリ', 'メモ', '開始時刻', '終了時刻', '作業時間(秒)', '作業時間(時間)', '作成日', '作成日時'])
        
        for task in tasks:
            hours = round(task['duration_seconds'] / 3600, 2) if task['duration_seconds'] else 0
            writer.writerow([
                task['id'], task['task_name'], task['category'], task['memo'] or '',
                task['start_time'].strftime('%Y-%m-%d %H:%M:%S') if task['start_time'] else '',
                task['end_time'].strftime('%Y-%m-%d %H:%M:%S') if task['end_time'] else '',
                task['duration_seconds'], hours,
                task['created_date'].strftime('%Y-%m-%d'),
                task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'tasks_{year}_{month:02d}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'エンドポイントが見つかりません'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

