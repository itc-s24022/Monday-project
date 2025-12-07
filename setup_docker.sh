#!/bin/bash

set -e

echo "=== PostgreSQL Setup for Flask Todo App (Docker) ==="

# Fixed database configuration
DB_NAME="todo_db"
DB_USER="todo_user"
DB_PASSWORD="todo_password"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first:"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first:"
    echo "https://docs.docker.com/compose/install/"
    exit 1
fi

# Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U ${DB_USER} -d ${DB_NAME} > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Install Python PostgreSQL adapter if not already installed
echo "Installing Python dependencies..."
pip3 install -q psycopg2-binary flask flask-sqlalchemy 2>/dev/null || pip3 install psycopg2-binary flask flask-sqlalchemy

# Update app.py with PostgreSQL connection
echo "Updating app.py for PostgreSQL..."
if grep -q "sqlite:///db.sqlite" app.py; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|sqlite:///db.sqlite|postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}|g" app.py
    else
        sed -i "s|sqlite:///db.sqlite|postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}|g" app.py
    fi
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
echo "PostgreSQL is running in Docker container 'flask_todo_postgres'"
echo ""
echo "Useful commands:"
echo "  - Start: docker-compose up -d"
echo "  - Stop: docker-compose down"
echo "  - Logs: docker-compose logs -f postgres"
echo "  - Connect to psql: docker-compose exec postgres psql -U ${DB_USER} -d ${DB_NAME}"
echo ""
echo "Run the app with: python3 app.py"
