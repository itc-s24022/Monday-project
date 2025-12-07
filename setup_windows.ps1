# PostgreSQL Setup for Flask Todo App (Windows PowerShell)
# Run this script in PowerShell as Administrator

Write-Host "=== PostgreSQL Setup for Flask Todo App (Windows) ===" -ForegroundColor Green
Write-Host ""

# Fixed database configuration
$DB_NAME = "todo_db"
$DB_USER = "todo_user"
$DB_PASSWORD = "todo_password"

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Warning: This script should be run as Administrator for best results." -ForegroundColor Yellow
    Write-Host "Some operations may fail without administrator privileges." -ForegroundColor Yellow
    Write-Host ""
}

# Check if Chocolatey is installed
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey is not installed. Installing Chocolatey..." -ForegroundColor Yellow
    Write-Host ""
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install Chocolatey." -ForegroundColor Red
        Write-Host "Please install Chocolatey manually: https://chocolatey.org/install" -ForegroundColor Red
        exit 1
    }

    Write-Host "Chocolatey installed successfully!" -ForegroundColor Green
    Write-Host "Please restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 0
}

# Check if PostgreSQL is installed
$pgInstalled = Get-Command psql -ErrorAction SilentlyContinue

if (-not $pgInstalled) {
    Write-Host "Installing PostgreSQL..." -ForegroundColor Yellow
    choco install postgresql14 -y --params '/Password:admin123'

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install PostgreSQL." -ForegroundColor Red
        exit 1
    }

    Write-Host "PostgreSQL installed successfully!" -ForegroundColor Green
    Write-Host "Please restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "PostgreSQL is already installed." -ForegroundColor Green
}

# Start PostgreSQL service
Write-Host "Starting PostgreSQL service..." -ForegroundColor Yellow
$service = Get-Service -Name postgresql* -ErrorAction SilentlyContinue

if ($service) {
    Start-Service -Name $service.Name -ErrorAction SilentlyContinue
    Write-Host "PostgreSQL service started." -ForegroundColor Green
} else {
    Write-Host "Warning: PostgreSQL service not found. It may need to be configured manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Set PostgreSQL bin directory in PATH for this session
$env:Path += ";C:\Program Files\PostgreSQL\14\bin"

# Create database user and database
Write-Host "Creating database and user..." -ForegroundColor Yellow

# Drop existing database and user if they exist
$env:PGPASSWORD = "admin123"
psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>$null
psql -U postgres -c "DROP USER IF EXISTS $DB_USER;" 2>$null

# Create new user and database
psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create user." -ForegroundColor Red
    Write-Host "Try running psql manually: psql -U postgres" -ForegroundColor Yellow
    exit 1
}

psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

Write-Host "Database and user created successfully!" -ForegroundColor Green

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install Python dependencies." -ForegroundColor Red
    exit 1
}

Write-Host "Python dependencies installed successfully!" -ForegroundColor Green

# Update app.py with PostgreSQL connection (create backup first)
Write-Host ""
Write-Host "Note: app.py uses environment variable to switch databases." -ForegroundColor Cyan
Write-Host "No modification needed to app.py" -ForegroundColor Cyan

# Initialize database tables
Write-Host ""
Write-Host "Initializing database tables..." -ForegroundColor Yellow
$env:USE_POSTGRESQL = "1"
python -c "from app import app, db; app.app_context().push(); db.create_all()"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to initialize database tables." -ForegroundColor Red
    exit 1
}

Write-Host "Database tables initialized successfully!" -ForegroundColor Green

# Display summary
Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host "Database: $DB_NAME" -ForegroundColor Cyan
Write-Host "User: $DB_USER" -ForegroundColor Cyan
Write-Host "Password: $DB_PASSWORD" -ForegroundColor Cyan
Write-Host "Connection string: postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the app with PostgreSQL:" -ForegroundColor Yellow
Write-Host '  $env:USE_POSTGRESQL="1"; python app.py' -ForegroundColor White
Write-Host ""
Write-Host "To run the app with SQLite (default):" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor White
Write-Host ""
