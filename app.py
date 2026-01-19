from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
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

def get_today_tasks(firebase_uid=None):
    """当日のタスク一覧を取得"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT id, task_name, category, memo, start_time, end_time, 
               duration_seconds, created_date, created_at
        FROM tasks
        WHERE created_date = CURRENT_DATE
    """
    params = []
    
    if firebase_uid:
        query += " AND firebase_uid = %s"
        params.append(firebase_uid)
    
    query += " ORDER BY created_at DESC"
    
    cur.execute(query, params)
    tasks = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return tasks

# ==================== フロントエンド画面 ====================

@app.route('/')
def index():
    """タスク登録画面表示（当日のタスク一覧含む）"""
    try:
        tasks = get_today_tasks()
        return render_template('index.html', tasks=tasks)
    except Exception as e:
        return render_template('index.html', tasks=[], error=str(e))

@app.route('/report')
def report():
    """月次レポート画面表示"""
    return render_template('report.html')

# ==================== タスク操作API ====================

@app.route('/task/add', methods=['POST'])
def add_task():
    """新規タスク登録"""
    try:
        data = request.get_json()
        
        task_name = data.get('task_name')
        category = data.get('category')
        memo = data.get('memo', '')
        firebase_uid = data.get('firebase_uid')
        
        if not task_name or not category:
            return jsonify({'error': 'task_nameとcategoryは必須です'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            INSERT INTO tasks (task_name, category, memo, firebase_uid)
            VALUES (%s, %s, %s, %s)
            RETURNING id, task_name, category, memo, created_date, created_at
        """, (task_name, category, memo, firebase_uid))
        
        new_task = cur.fetchone()
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'task': dict(new_task)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/task/start', methods=['POST'])
def start_task():
    """タイマー開始（start_time記録）"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        firebase_uid = data.get('firebase_uid')
        
        if not task_id:
            return jsonify({'error': 'task_idは必須です'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # タスクの存在確認
        query = "SELECT id, start_time FROM tasks WHERE id = %s"
        params = [task_id]
        
        if firebase_uid:
            query += " AND firebase_uid = %s"
            params.append(firebase_uid)
        
        cur.execute(query, params)
        task = cur.fetchone()
        
        if not task:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクが見つかりません'}), 404
        
        if task['start_time']:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクは既に開始されています'}), 400
        
        # start_timeを現在時刻で更新
        cur.execute("""
            UPDATE tasks
            SET start_time = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, task_name, start_time
        """, (task_id,))
        
        updated_task = cur.fetchone()
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'task': dict(updated_task)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/task/stop', methods=['POST'])
def stop_task():
    """タイマー停止（end_time, duration_seconds記録）"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        firebase_uid = data.get('firebase_uid')
        
        if not task_id:
            return jsonify({'error': 'task_idは必須です'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # タスクの存在確認とstart_timeの確認
        query = "SELECT id, start_time, end_time FROM tasks WHERE id = %s"
        params = [task_id]
        
        if firebase_uid:
            query += " AND firebase_uid = %s"
            params.append(firebase_uid)
        
        cur.execute(query, params)
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
        
        # end_timeとduration_secondsを更新
        cur.execute("""
            UPDATE tasks
            SET end_time = CURRENT_TIMESTAMP,
                duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time))::INTEGER
            WHERE id = %s
            RETURNING id, task_name, start_time, end_time, duration_seconds
        """, (task_id,))
        
        updated_task = cur.fetchone()
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'task': dict(updated_task)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/task/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    """タスク削除"""
    try:
        data = request.get_json() or {}
        firebase_uid = data.get('firebase_uid')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # タスクの存在確認
        query = "SELECT id FROM tasks WHERE id = %s"
        params = [task_id]
        
        if firebase_uid:
            query += " AND firebase_uid = %s"
            params.append(firebase_uid)
        
        cur.execute(query, params)
        task = cur.fetchone()
        
        if not task:
            cur.close()
            conn.close()
            return jsonify({'error': 'タスクが見つかりません'}), 404
        
        # タスク削除
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'タスクを削除しました'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== レポートAPI ====================

@app.route('/api/report/monthly', methods=['GET'])
def get_monthly_report():
    """月次集計データ取得（JSON）"""
    try:
        # パラメータ取得
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        group_by = request.args.get('group_by', 'category')  # category or project
        firebase_uid = request.args.get('firebase_uid')
        
        # デフォルト値：現在の年月
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # バリデーション
        if not (1 <= month <= 12):
            return jsonify({'error': '月は1-12の範囲で指定してください'}), 400
        
        if group_by not in ['category', 'project']:
            return jsonify({'error': 'group_byはcategoryまたはprojectを指定してください'}), 400
        
        # 月の開始日と終了日を計算
        start_date = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year}-{month:02d}-{last_day}"
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # グループごとの集計クエリ
        group_column = 'category' if group_by == 'category' else 'task_name'
        
        query = f"""
            SELECT 
                {group_column} as name,
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
        
        # 月全体の合計を取得
        total_query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(duration_seconds) as total_seconds,
                ROUND(SUM(duration_seconds) / 3600.0, 2) as total_hours
            FROM tasks
            WHERE created_date >= %s AND created_date <= %s
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
            'totals': dict(totals) if totals else {
                'total_tasks': 0,
                'total_seconds': 0,
                'total_hours': 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """CSV形式でエクスポート"""
    try:
        # パラメータ取得
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        firebase_uid = request.args.get('firebase_uid')
        
        # デフォルト値：現在の年月
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # 月の開始日と終了日を計算
        start_date = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year}-{month:02d}-{last_day}"
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                id, task_name, category, memo, start_time, end_time,
                duration_seconds, created_date, created_at
            FROM tasks
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
        
        # CSVファイルを作成
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行
        writer.writerow([
            'ID', 'タスク名', 'カテゴリ', 'メモ', '開始時刻', 
            '終了時刻', '作業時間(秒)', '作業時間(時間)', '作成日', '作成日時'
        ])
        
        # データ行
        for task in tasks:
            hours = round(task['duration_seconds'] / 3600, 2) if task['duration_seconds'] else 0
            writer.writerow([
                task['id'],
                task['task_name'],
                task['category'],
                task['memo'] or '',
                task['start_time'].strftime('%Y-%m-%d %H:%M:%S') if task['start_time'] else '',
                task['end_time'].strftime('%Y-%m-%d %H:%M:%S') if task['end_time'] else '',
                task['duration_seconds'],
                hours,
                task['created_date'].strftime('%Y-%m-%d'),
                task['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # CSVファイルを返す
        output.seek(0)
        filename = f'tasks_{year}_{month:02d}.csv'
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM付きUTF-8
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ヘルスチェック ====================

@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# ==================== エラーハンドラー ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'エンドポイントが見つかりません'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'サーバーエラーが発生しました'}), 500

# ==================== アプリケーション起動 ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)