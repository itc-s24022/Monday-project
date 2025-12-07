#!/bin/bash

echo "=== PostgreSQL起動テストスクリプト ==="
echo ""
echo "このスクリプトは、PostgreSQLがセットアップされた環境で"
echo "アプリケーションをPostgreSQLモードで起動する方法を示します。"
echo ""

# データベース設定
DB_NAME="todo_db"
DB_USER="todo_user"
DB_PASSWORD="todo_password"

echo "【前提条件】"
echo "1. PostgreSQLがインストール済みで起動していること"
echo "2. データベース '${DB_NAME}' とユーザー '${DB_USER}' が作成済みであること"
echo ""

echo "【PostgreSQLセットアップ方法】"
echo "Ubuntu: ./setup.sh"
echo "macOS:  ./setup_macos.sh"
echo "Docker: ./setup_docker.sh"
echo ""

echo "【PostgreSQL起動確認】"
if command -v psql &> /dev/null; then
    echo "✓ psqlコマンドが見つかりました"

    # PostgreSQL接続テスト
    if PGPASSWORD=${DB_PASSWORD} psql -U ${DB_USER} -d ${DB_NAME} -h localhost -c "SELECT version();" &> /dev/null; then
        echo "✓ PostgreSQLに接続できました"
        echo ""
        echo "【データベース情報】"
        PGPASSWORD=${DB_PASSWORD} psql -U ${DB_USER} -d ${DB_NAME} -h localhost -c "SELECT version();" | head -3
        echo ""
        echo "【テーブル一覧】"
        PGPASSWORD=${DB_PASSWORD} psql -U ${DB_USER} -d ${DB_NAME} -h localhost -c "\dt"
        echo ""

        echo "【Flask appをPostgreSQLで起動】"
        echo "コマンド: USE_POSTGRESQL=1 python3 app.py"
        echo ""
        echo "実行しますか? (yes/no)"
        read -r response
        if [[ "$response" == "yes" ]]; then
            echo "起動中..."
            USE_POSTGRESQL=1 python3 app.py
        else
            echo "スキップしました"
        fi
    else
        echo "✗ PostgreSQLに接続できませんでした"
        echo ""
        echo "【トラブルシューティング】"
        echo "1. PostgreSQLサービスが起動しているか確認:"
        echo "   brew services list | grep postgresql"
        echo ""
        echo "2. サービスを起動:"
        echo "   brew services start postgresql@14"
        echo ""
        echo "3. データベースとユーザーを作成:"
        echo "   createuser -s ${DB_USER}"
        echo "   createdb -O ${DB_USER} ${DB_NAME}"
        echo "   psql postgres -c \"ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';\""
    fi
else
    echo "✗ PostgreSQLがインストールされていません"
    echo ""
    echo "【インストール方法】"
    echo "Ubuntu: sudo apt-get install postgresql"
    echo "macOS:  brew install postgresql@14"
    echo "Docker: docker-compose up -d"
fi
