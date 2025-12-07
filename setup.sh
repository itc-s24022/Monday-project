#!/bin/bash

set -e

echo "=== PostgreSQL Setup for Flask Todo App ==="

# Fixed database configuration
DB_NAME="todo_db"
DB_USER="todo_user"
DB_PASSWORD="todo_password"

# Update package list
echo "Updating package list..."
sudo apt-get update -qq

# Install PostgreSQL
echo "Installing PostgreSQL..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib > /dev/null

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
sudo service postgresql start

# Wait for PostgreSQL to be ready
sleep 2

# Create database user and database
echo "Creating database and user..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS ${DB_USER};" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

# Install Python PostgreSQL adapter
echo "Installing Python dependencies..."
pip3 install -q psycopg2-binary flask flask-sqlalchemy

# Update app.py with PostgreSQL connection
echo "Updating app.py for PostgreSQL..."
sed -i "s|sqlite:///db.sqlite|postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}|g" app.py

# Initialize database tables
echo "Initializing database tables..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

echo ""
echo "=== Setup Complete! ==="
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo ""
echo "Run the app with: python3 app.py"
