# Apple Disease Detector - Windows Deployment Script
Write-Host "Apple Disease Detector - Deployment Script" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

# Check prerequisites
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is required" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Compose is required" -ForegroundColor Red
    exit 1
}

# Load environment
if (Test-Path ".env") {
    Write-Host "Loading .env configuration" -ForegroundColor Green
} else {
    Write-Host "No .env file found, using defaults" -ForegroundColor Yellow
    Copy-Item "backend/.env.example" ".env"
}

# Build and start
Write-Host "Building services..." -ForegroundColor Cyan
docker-compose build --no-cache

Write-Host "Starting services..." -ForegroundColor Cyan
docker-compose up -d

# Health check
Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host "Checking health..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/ping" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Backend is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "Backend health check failed" -ForegroundColor Red
    docker-compose logs backend
    exit 1
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Frontend is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "Frontend health check failed" -ForegroundColor Red
    docker-compose logs frontend
    exit 1
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Frontend: http://localhost" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "To stop: docker-compose down" -ForegroundColor Gray
