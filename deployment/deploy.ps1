# Production Deployment Script for Windows

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Face Recognition System - Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✓ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Create .env if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    
    # Generate random secret key
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    (Get-Content .env) -replace 'SECRET_KEY=.*', "SECRET_KEY=$secretKey" | Set-Content .env
    
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host "Please edit .env file with your settings" -ForegroundColor Yellow
    
    Read-Host "Press Enter to continue after editing .env"
}

# Pull latest code (if git repo)
if (Test-Path .git) {
    Write-Host "Pulling latest code..." -ForegroundColor Yellow
    git pull origin master
}

# Build Docker images
Write-Host "Building Docker images..." -ForegroundColor Yellow
docker-compose build

# Stop existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start services
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "`nService Status:" -ForegroundColor Yellow
docker-compose ps

# Run health check
Write-Host "`nRunning health check..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Application is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Application health check failed" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs app" -ForegroundColor Yellow
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost/api/docs"
Write-Host "Health Check: http://localhost/health"
Write-Host "`nUseful commands:"
Write-Host "  View logs: " -NoNewline; Write-Host "docker-compose logs -f" -ForegroundColor Yellow
Write-Host "  Stop services: " -NoNewline; Write-Host "docker-compose down" -ForegroundColor Yellow
Write-Host "  Restart services: " -NoNewline; Write-Host "docker-compose restart" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
