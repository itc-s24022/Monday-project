#!/bin/bash

# スクリプトの実行中にエラーが発生した場合、即座に終了する
set -e

echo "=== PostgreSQL Setup for Flask Todo App (Docker) ==="

# Fixed database configuration (app.py および docker-compose.yml と一致させること)
DB_NAME="todo_db"
DB_USER="todo_user"
DB_PASSWORD="todo_password"

# --- 依存関係のチェック ---

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first:"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi


# Check if Docker Compose is available
if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first:"
    echo "https://docs.docker.com/compose/install/"
    exit 1
fi


# Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker compose up -d

echo "Waiting for PostgreSQL to be ready..."
# docker compose exec に修正 (古い docker-compose ではなく新しい構文を使用)
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U ${DB_USER} -d ${DB_NAME} > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# --- Python環境のセットアップ (venv) ---

echo "Setting up Python virtual environment..."
python3 -m venv venv || { echo "Error: Failed to create venv. Ensure python3-venv is installed."; exit 1; }

# venvを有効化
source venv/bin/activate
echo "Virtual environment activated."

# Python依存ライブラリのインストール
echo "Installing Python dependencies..."
# venv 内ではシステムパッケージエラーは発生しないため、シンプルな pip install でOK
pip install -q psycopg2-binary flask flask-sqlalchemy

# --- アプリケーション設定の更新 ---

echo "Updating app.py for PostgreSQL..."
# app.pyにDB設定情報がなかったため、今回は置換をスキップし、
# app.pyで直接PostgreSQL接続を設定している前提とする。

# --- データベーステーブルの初期化 ---

echo "Initializing database tables..."
# 仮想環境がアクティブなので、python3 で venv の Python を使用
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# --- 完了メッセージ ---

echo ""
echo "=== Setup Complete! ==="
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo "Connection string: postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}"
echo ""
echo "PostgreSQL is running in Docker container 'flask_todo_postgres'"
echo ""
echo "Run the app with: python3 app.py"
echo "To exit venv, run: deactivate"
echo ""

# 実行後も venv を維持したい場合は、この行をコメントアウトしてください
# deactivate