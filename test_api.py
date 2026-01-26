#!/usr/bin/env python3
"""
APIテストスクリプト
使い方: python test_api.py
"""

import requests
import json
from datetime import datetime
import time

# APIのベースURL
BASE_URL = "http://localhost:5000"

# テスト用Firebase UID（実際のFirebase認証を使う場合は適切なUIDに変更）
TEST_FIREBASE_UID = "test_user_123"

def print_section(title):
    """セクションタイトルを表示"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response, description=""):
    """レスポンスを整形して表示"""
    if description:
        print(f"\n{description}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print("-" * 60)

def test_health_check():
    """ヘルスチェックテスト"""
    print_section("1. ヘルスチェック")
    
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "GET /health")
    
    return response.status_code == 200

def test_add_task():
    """タスク追加テスト"""
    print_section("2. タスク追加")
    
    tasks = [
        {
            "task_name": "バックエンド開発",
            "category": "開発",
            "memo": "Flask APIの実装",
            "firebase_uid": TEST_FIREBASE_UID
        },
        {
            "task_name": "データベース設計",
            "category": "設計",
            "memo": "PostgreSQLのテーブル設計",
            "firebase_uid": TEST_FIREBASE_UID
        },
        {
            "task_name": "ドキュメント作成",
            "category": "ドキュメント",
            "memo": "API仕様書の作成",
            "firebase_uid": TEST_FIREBASE_UID
        }
    ]
    
    task_ids = []
    
    for task in tasks:
        response = requests.post(
            f"{BASE_URL}/api/task/add",
            json=task,
            headers={"Content-Type": "application/json"}
        )
        print_response(response, f"POST /api/task/add - {task['task_name']}")
        
        if response.status_code == 201:
            task_id = response.json().get('task', {}).get('id')
            if task_id:
                task_ids.append(task_id)
    
    return task_ids

def test_start_task(task_id):
    """タスク開始テスト"""
    print_section("3. タスク開始")
    
    response = requests.post(
        f"{BASE_URL}/api/task/start",
        json={
            "task_id": task_id,
            "firebase_uid": TEST_FIREBASE_UID
        },
        headers={"Content-Type": "application/json"}
    )
    print_response(response, f"POST /api/task/start - Task ID: {task_id}")
    
    return response.status_code == 200

def test_stop_task(task_id):
    """タスク停止テスト"""
    print_section("4. タスク停止")
    
    # 少し待機してから停止（duration_secondsが0にならないように）
    print("3秒待機中...")
    time.sleep(3)
    
    response = requests.post(
        f"{BASE_URL}/api/task/stop",
        json={
            "task_id": task_id,
            "firebase_uid": TEST_FIREBASE_UID
        },
        headers={"Content-Type": "application/json"}
    )
    print_response(response, f"POST /api/task/stop - Task ID: {task_id}")
    
    return response.status_code == 200

def test_get_monthly_report():
    """月次レポート取得テスト"""
    print_section("5. 月次レポート取得")
    
    now = datetime.now()
    
    # カテゴリ別集計
    response1 = requests.get(
        f"{BASE_URL}/api/report/monthly",
        params={
            "year": now.year,
            "month": now.month,
            "group_by": "category",
            "firebase_uid": TEST_FIREBASE_UID
        }
    )
    print_response(response1, "GET /api/report/monthly - カテゴリ別集計")
    
    # プロジェクト別集計
    response2 = requests.get(
        f"{BASE_URL}/api/report/monthly",
        params={
            "year": now.year,
            "month": now.month,
            "group_by": "project",
            "firebase_uid": TEST_FIREBASE_UID
        }
    )
    print_response(response2, "GET /api/report/monthly - プロジェクト別集計")
    
    return response1.status_code == 200

def test_export_csv():
    """CSVエクスポートテスト"""
    print_section("6. CSVエクスポート")
    
    now = datetime.now()
    
    response = requests.get(
        f"{BASE_URL}/api/export/csv",
        params={
            "year": now.year,
            "month": now.month,
            "firebase_uid": TEST_FIREBASE_UID
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        filename = f"test_export_{now.year}_{now.month:02d}.csv"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"CSV file saved: {filename}")
        print(f"Content preview (first 200 chars):\n{response.content[:200].decode('utf-8-sig')}")
    else:
        print(f"Error: {response.text}")
    
    print("-" * 60)
    
    return response.status_code == 200

def test_delete_task(task_id):
    """タスク削除テスト"""
    print_section("7. タスク削除")
    
    response = requests.post(
        f"{BASE_URL}/api/task/delete/{task_id}",
        json={
            "firebase_uid": TEST_FIREBASE_UID
        },
        headers={"Content-Type": "application/json"}
    )
    print_response(response, f"POST /api/task/delete/{task_id}")
    
    return response.status_code == 200

def test_error_cases():
    """エラーケーステスト"""
    print_section("8. エラーケーステスト")
    
    # 必須パラメータなしでタスク追加
    response1 = requests.post(
        f"{BASE_URL}/api/task/add",
        json={"memo": "メモのみ"},
        headers={"Content-Type": "application/json"}
    )
    print_response(response1, "POST /api/task/add - 必須パラメータなし（エラーを期待）")
    
    # 存在しないタスクを開始
    response2 = requests.post(
        f"{BASE_URL}/api/task/start",
        json={"task_id": 99999, "firebase_uid": TEST_FIREBASE_UID},
        headers={"Content-Type": "application/json"}
    )
    print_response(response2, "POST /api/task/start - 存在しないタスク（エラーを期待）")
    
    # 存在しないタスクを削除
    response3 = requests.post(
        f"{BASE_URL}/api/task/delete/99999",
        json={"firebase_uid": TEST_FIREBASE_UID},
        headers={"Content-Type": "application/json"}
    )
    print_response(response3, "POST /api/task/delete/99999 - 存在しないタスク（エラーを期待）")

def run_all_tests():
    """すべてのテストを実行"""
    print("\n" + "🚀 " * 20)
    print("API統合テスト開始")
    print("🚀 " * 20)
    
    results = []
    
    try:
        # 1. ヘルスチェック
        result = test_health_check()
        results.append(("ヘルスチェック", result))
        
        if not result:
            print("\n⚠️  サーバーに接続できません。app.pyが起動しているか確認してください。")
            return
        
        # 2. タスク追加
        task_ids = test_add_task()
        results.append(("タスク追加", len(task_ids) > 0))
        
        if len(task_ids) == 0:
            print("\n⚠️  タスクが追加できませんでした。")
            return
        
        # 3. タスク開始（最初のタスク）
        if len(task_ids) > 0:
            result = test_start_task(task_ids[0])
            results.append(("タスク開始", result))
            
            # 4. タスク停止
            if result:
                result = test_stop_task(task_ids[0])
                results.append(("タスク停止", result))
        
        # 5. 月次レポート取得
        result = test_get_monthly_report()
        results.append(("月次レポート取得", result))
        
        # 6. CSVエクスポート
        result = test_export_csv()
        results.append(("CSVエクスポート", result))
        
        # 7. タスク削除（最後のタスク）
        if len(task_ids) > 0:
            result = test_delete_task(task_ids[-1])
            results.append(("タスク削除", result))
        
        # 8. エラーケース
        test_error_cases()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ サーバーに接続できません。")
        print("以下を確認してください：")
        print("1. app.pyが起動しているか: python app.py")
        print("2. ポート5000が使用可能か")
        print("3. PostgreSQLが起動しているか")
        return
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 結果サマリー
    print_section("テスト結果サマリー")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"合計: {passed}/{total} テスト成功")
    print("="*60)
    
    if passed == total:
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print(f"\n⚠️  {total - passed}個のテストが失敗しました。")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║         Task Management API Test Suite                  ║
╚══════════════════════════════════════════════════════════╝

前提条件:
1. PostgreSQLが起動している
2. todo_dbデータベースが作成されている
3. app.pyが起動している (python app.py)

テスト開始...
""")
    
    run_all_tests()
    
    print("\n✨ テスト完了")

