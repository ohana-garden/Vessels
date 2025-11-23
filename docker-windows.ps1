#!/usr/bin/env pwsh
# ============================================================================
# Vessels Platform - Windows Docker Desktop Launcher (PowerShell)
# ============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet('build','run','stop','logs','shell','clean')]
    [string]$Command = 'run'
)

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  VESSELS - Single Container Deployment" -ForegroundColor Cyan
Write-Host "  Windows Docker Desktop" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✓ Docker is running..." -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

function Build-Vessels {
    Write-Host "Building Vessels Docker image..." -ForegroundColor Yellow
    Write-Host "This may take several minutes on first build..." -ForegroundColor Gray
    Write-Host ""

    docker build -t vessels:latest .

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Build failed!" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "✓ Build complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Run with './docker-windows.ps1 run'" -ForegroundColor Cyan
    Write-Host ""
}

function Start-Vessels {
    Write-Host "Checking for existing container..." -ForegroundColor Gray

    $existing = docker ps -a --filter "name=vessels-platform" --format "{{.Names}}"
    if ($existing -eq "vessels-platform") {
        Write-Host "Stopping existing container..." -ForegroundColor Yellow
        docker stop vessels-platform | Out-Null
        docker rm vessels-platform | Out-Null
    }

    Write-Host "Starting Vessels Platform..." -ForegroundColor Yellow
    Write-Host ""

    docker run -d `
        --name vessels-platform `
        -p 5000:5000 `
        -p 6379:6379 `
        -v vessels-data:/data/falkordb `
        -v vessels-workdir:/app/work_dir `
        --restart unless-stopped `
        vessels:latest

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Failed to start container!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Did you build the image first?" -ForegroundColor Yellow
        Write-Host "Run: ./docker-windows.ps1 build" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }

    Write-Host ""
    Write-Host "✓ Vessels Platform is starting..." -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for services to be ready..." -ForegroundColor Gray
    Start-Sleep -Seconds 5

    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   VESSELS PLATFORM IS RUNNING" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Web Interface: " -NoNewline
    Write-Host "http://localhost:5000" -ForegroundColor Cyan
    Write-Host "FalkorDB:      " -NoNewline
    Write-Host "localhost:6379" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Container name: vessels-platform" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  ./docker-windows.ps1 logs   - View logs"
    Write-Host "  ./docker-windows.ps1 shell  - Open shell"
    Write-Host "  ./docker-windows.ps1 stop   - Stop container"
    Write-Host ""
}

function Stop-Vessels {
    Write-Host "Stopping Vessels Platform..." -ForegroundColor Yellow
    docker stop vessels-platform
    docker rm vessels-platform
    Write-Host ""
    Write-Host "✓ Container stopped and removed" -ForegroundColor Green
    Write-Host ""
}

function Show-Logs {
    Write-Host "Showing Vessels logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    Write-Host ""
    docker logs -f vessels-platform
}

function Open-Shell {
    Write-Host "Opening shell in Vessels container..." -ForegroundColor Yellow
    Write-Host ""
    docker exec -it vessels-platform /bin/bash
}

function Remove-Vessels {
    Write-Host "This will remove the Vessels container and image." -ForegroundColor Yellow
    Write-Host "Data volumes will be preserved." -ForegroundColor Gray
    Write-Host ""

    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Cancelled." -ForegroundColor Gray
        return
    }

    Write-Host ""
    Write-Host "Removing container..." -ForegroundColor Yellow
    docker stop vessels-platform 2>&1 | Out-Null
    docker rm vessels-platform 2>&1 | Out-Null

    Write-Host "Removing image..." -ForegroundColor Yellow
    docker rmi vessels:latest

    Write-Host ""
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
    Write-Host ""
    Write-Host "To remove data volumes as well, run:" -ForegroundColor Yellow
    Write-Host "  docker volume rm vessels-data vessels-workdir" -ForegroundColor Cyan
    Write-Host ""
}

# Execute command
switch ($Command) {
    'build' { Build-Vessels }
    'run'   { Start-Vessels }
    'stop'  { Stop-Vessels }
    'logs'  { Show-Logs }
    'shell' { Open-Shell }
    'clean' { Remove-Vessels }
}
