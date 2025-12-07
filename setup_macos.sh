#!/bin/bash

set -e

echo "=== PostgreSQL Setup for Flask Todo App (macOS) ==="

# Fixed database configuration
DB_NAME="todo_db"
DB_USER="todo_user"
DB_PASSWORD="todo_password"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is not installed. Please install Homebrew first:"
    echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Install PostgreSQL if not already installed
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    brew install postgresql@14
else
    echo "PostgreSQL is already installed."
fi

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
brew services start postgresql@14 || brew services restart postgresql@14

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 3

# Create database user and database
echo "Creating database and user..."

# Drop existing database and user if they exist
psql postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
psql postgres -c "DROP USER IF EXISTS ${DB_USER};" 2>/dev/null || true

# Create new user and database
psql postgres -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
psql postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

# Install Python PostgreSQL adapter
echo "Installing Python dependencies..."
pip3 install -q psycopg2-binary flask flask-sqlalchemy

# Update app.py with PostgreSQL connection
echo "Updating app.py for PostgreSQL..."
if grep -q "sqlite:///db.sqlite" app.py; then
    sed -i '' "s|sqlite:///db.sqlite|postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}|g" app.py
    echo "app.py updated successfully."
else
    echo "app.py already configured for PostgreSQL."
fi

# Initialize database tables
echo "Initializing database tables..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

echo ""
echo "=== Setup Complete! ==="
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo "Connection string: postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}"
echo ""
echo "Run the app with: python3 app.py"
