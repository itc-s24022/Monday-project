#!/bin/bash

set -e

echo "=== PostgreSQL Setup for Flask Todo App (WSL/Windows) ==="

# Fixed database configuration
DB_NAME="todo_db"
DB_USER="todo_user"
DB_PASSWORD="todo_password"

# Check if running in WSL
if ! grep -q Microsoft /proc/version 2>/dev/null; then
    echo "Warning: This script is designed for WSL (Windows Subsystem for Linux)"
    echo "If you are on native Linux, use ./setup.sh instead"
    echo ""
fi

# Update package list
echo "Updating package list..."
sudo apt-get update -qq

# Install PostgreSQL
echo "Installing PostgreSQL..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib > /dev/null

# Start PostgreSQL service (WSL specific)
echo "Starting PostgreSQL service..."
sudo service postgresql start

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 3

# Create database user and database
echo "Creating database and user..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS ${DB_USER};" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

# Install Python PostgreSQL adapter
echo "Installing Python dependencies..."
pip3 install -q psycopg2-binary flask flask-sqlalchemy 2>/dev/null || pip3 install psycopg2-binary flask flask-sqlalchemy

# Initialize database tables
echo "Initializing database tables..."
python3 -c "from app import app, db; import os; os.environ['USE_POSTGRESQL']='1'; app.app_context().push(); db.create_all()"

echo ""
echo "=== Setup Complete! ==="
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo "Connection string: postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}"
echo ""
echo "To start PostgreSQL service (WSL):"
echo "  sudo service postgresql start"
echo ""
echo "To run the app with PostgreSQL:"
echo "  USE_POSTGRESQL=1 python3 app.py"
echo ""
echo "To run the app with SQLite (default):"
echo "  python3 app.py"
echo ""
