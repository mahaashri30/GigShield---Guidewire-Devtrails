#!/usr/bin/env pwsh
<#
SUSANOO INFRASTRUCTURE SETUP SCRIPT
Installs and configures:
- PostgreSQL database
- Redis cache server
- Tesseract-OCR binary

Run this script in PowerShell as Administrator
#>

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       SUSANOO INFRASTRUCTURE SETUP SCRIPT (Windows)            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "❌ This script must run as Administrator!" -ForegroundColor Red
    Write-Host "   Please restart PowerShell as Administrator and run again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Check if Docker is installed
Write-Host "Checking for Docker installation..." -ForegroundColor Yellow
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerInstalled) {
    Write-Host "✅ Docker found: $(docker --version)" -ForegroundColor Green
} else {
    Write-Host "❌ Docker not found. Installing Docker Desktop is recommended." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ STEP 1: Setting up PostgreSQL Database                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($dockerInstalled) {
    Write-Host "Option 1: Using Docker (Recommended)" -ForegroundColor Green
    Write-Host "Command: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=susanoo_password postgres:15" -ForegroundColor White
    Write-Host ""
    
    $useDocker = Read-Host "Use Docker for PostgreSQL? (y/n)"
    if ($useDocker -eq 'y' -or $useDocker -eq 'Y') {
        Write-Host "Starting PostgreSQL Docker container..." -ForegroundColor Yellow
        docker run -d --name susanoo-postgres `
            -p 5432:5432 `
            -e POSTGRES_USER=susanoo `
            -e POSTGRES_PASSWORD=susanoo_password `
            -e POSTGRES_DB=susanoo `
            -v susanoo-postgres-data:/var/lib/postgresql/data `
            postgres:15
        
        Write-Host "✅ PostgreSQL started!" -ForegroundColor Green
        Write-Host "   Host: localhost" -ForegroundColor White
        Write-Host "   Port: 5432" -ForegroundColor White
        Write-Host "   User: susanoo" -ForegroundColor White
        Write-Host "   Password: susanoo_password" -ForegroundColor White
        Write-Host "   Database: susanoo" -ForegroundColor White
        
        $pgReady = $false
        $attempts = 0
        while (-not $pgReady -and $attempts -lt 30) {
            try {
                docker exec susanoo-postgres pg_isready -U susanoo | Out-Null
                $pgReady = $true
                Write-Host "✅ PostgreSQL is ready!" -ForegroundColor Green
            } catch {
                $attempts++
                Write-Host "   Waiting for PostgreSQL to be ready... ($attempts/30)" -ForegroundColor Yellow
                Start-Sleep -Seconds 1
            }
        }
    }
} else {
    Write-Host "Option 2: Manual Installation" -ForegroundColor Green
    Write-Host "Download PostgreSQL 15: https://www.postgresql.org/download/windows/" -ForegroundColor White
    Write-Host "   During installation:" -ForegroundColor Yellow
    Write-Host "   - Password: susanoo_password" -ForegroundColor Yellow
    Write-Host "   - Port: 5432" -ForegroundColor Yellow
    Read-Host "Press Enter after PostgreSQL installation is complete"
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ STEP 2: Setting up Redis Cache Server                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($dockerInstalled) {
    Write-Host "Starting Redis Docker container..." -ForegroundColor Yellow
    docker run -d --name susanoo-redis `
        -p 6379:6379 `
        redis:7-alpine
    
    Write-Host "✅ Redis started!" -ForegroundColor Green
    Write-Host "   Host: localhost" -ForegroundColor White
    Write-Host "   Port: 6379" -ForegroundColor White
    
    Start-Sleep -Seconds 2
    $redisTest = docker exec susanoo-redis redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis is responding!" -ForegroundColor Green
    }
} else {
    Write-Host "Redis requires Docker on Windows." -ForegroundColor Red
    Write-Host "Please install Docker Desktop first." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ STEP 3: Installing Tesseract-OCR Binary                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$tesseractInstalled = Get-Command tesseract -ErrorAction SilentlyContinue
if ($tesseractInstalled) {
    Write-Host "✅ Tesseract already installed: $(tesseract --version | Select-Object -First 1)" -ForegroundColor Green
} else {
    Write-Host "Tesseract not found. Downloading installer..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual Installation Instructions:" -ForegroundColor Green
    Write-Host "1. Download: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
    Write-Host "2. Download: tesseract-ocr-w64-setup-v5.*.exe" -ForegroundColor White
    Write-Host "3. Run installer with default settings" -ForegroundColor White
    Write-Host "4. Default path: C:\Program Files\Tesseract-OCR" -ForegroundColor White
    Write-Host ""
    
    $installTesseract = Read-Host "Download Tesseract installer now? (y/n)"
    if ($installTesseract -eq 'y' -or $installTesseract -eq 'Y') {
        Start-Process "https://github.com/UB-Mannheim/tesseract/wiki"
        Write-Host "Opening download page in browser..." -ForegroundColor Yellow
        Read-Host "After downloading, run the .exe installer. Press Enter when complete"
    }
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ STEP 4: Configuring Environment Variables                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Creating .env file for backend..." -ForegroundColor Yellow

$envContent = @"
# Database Configuration
DATABASE_URL=postgresql+asyncpg://susanoo:susanoo_password@localhost:5432/susanoo
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=susanoo
DATABASE_PASSWORD=susanoo_password
DATABASE_NAME=susanoo

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OTP Configuration (2Factor.in)
OTP_API_KEY=your_2factor_api_key_here

# Gemini AI Configuration (Optional - for enhanced OCR)
GEMINI_API_KEY=your_gemini_api_key_here

# Tesseract Configuration
TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe

# Application Configuration
APP_NAME=Susanoo
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000

# AWS/Firebase Configuration (Optional)
# FIREBASE_PROJECT_ID=your_project_id
# FIREBASE_PRIVATE_KEY=your_private_key
# FIREBASE_CLIENT_EMAIL=your_client_email
"@

Set-Content -Path "c:\Users\vdmah\OneDrive\Desktop\Susanoo\backend\.env" -Value $envContent -Force
Write-Host "✅ Created backend\.env file" -ForegroundColor Green
Write-Host "   Location: backend\.env" -ForegroundColor White
Write-Host "   ⚠️  Remember to update API keys before production!" -ForegroundColor Yellow

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ STEP 5: Verifying Infrastructure Setup                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($dockerInstalled) {
    Write-Host "Running Docker containers:" -ForegroundColor Yellow
    docker ps --filter "name=susanoo" --format "table {{.Names}}\t{{.Status}}"
    Write-Host ""
}

$tesseractFinal = Get-Command tesseract -ErrorAction SilentlyContinue
if ($tesseractFinal) {
    Write-Host "✅ Tesseract available: $(tesseract --version | Select-Object -First 1)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Tesseract not found in PATH. Make sure installation is complete." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ INFRASTRUCTURE SETUP COMPLETE! ✅                              ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Update .env file with your API keys:" -ForegroundColor White
Write-Host "   - OTP_API_KEY (from 2Factor.in)" -ForegroundColor Gray
Write-Host "   - GEMINI_API_KEY (from Google Cloud)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test backend server startup:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Verify database migration (if needed):" -ForegroundColor White
Write-Host "   python -c \"from app.models.models import Base; Base.metadata.create_all()\"" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Run verification tests:" -ForegroundColor White
Write-Host "   python test_verification_system.py" -ForegroundColor Gray
Write-Host "   python test_verification_advanced.py" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Access API documentation:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"
