# Ground Station Core - Windows Startup Script
# This script starts the API server and UI

Write-Host "Ground Station Core - Starting..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
    Write-Host "  Activating virtual environment..." -ForegroundColor Cyan
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "! Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
        & "venv\Scripts\Activate.ps1"
        
        Write-Host "  Installing dependencies..." -ForegroundColor Cyan
        pip install --upgrade pip
        pip install -r requirements.txt
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "! Some dependencies may have failed to install" -ForegroundColor Yellow
            Write-Host "  This is normal if SDR libraries are not available" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        pause
        exit 1
    }
}

Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "! .env file not found" -ForegroundColor Yellow
    if (Test-Path ".env.template") {
        Write-Host "  Copying .env.template to .env..." -ForegroundColor Cyan
        Copy-Item ".env.template" ".env"
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host "  Please edit .env with your settings before running again" -ForegroundColor Yellow
        pause
        exit 0
    } else {
        Write-Host "  Running with default configuration" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Green
Write-Host "-------------------" -ForegroundColor Green
Write-Host ""

# Function to check if API server is running
function Test-APIServer {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $true
    } catch {
        return $false
    }
}

# Ask user what to start
Write-Host "What would you like to start?" -ForegroundColor Cyan
Write-Host "1. API Server only" -ForegroundColor White
Write-Host "2. UI only (requires API server to be running)" -ForegroundColor White
Write-Host "3. Both API Server and UI" -ForegroundColor White
Write-Host "4. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting API Server..." -ForegroundColor Green
        Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "API documentation at: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        python backend\api_server.py
    }
    
    "2" {
        Write-Host ""
        # Check if API server is running
        if (Test-APIServer) {
            Write-Host "✓ API Server is running" -ForegroundColor Green
        } else {
            Write-Host "! API Server is not running" -ForegroundColor Yellow
            Write-Host "  Some features may not work properly" -ForegroundColor Yellow
            Write-Host "  Start the API server in another window first" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Starting UI..." -ForegroundColor Green
        python launch.py
    }
    
    "3" {
        Write-Host ""
        Write-Host "Starting API Server in background..." -ForegroundColor Green
        
        # Start API server in background
        $apiJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            & "venv\Scripts\Activate.ps1"
            python backend\api_server.py
        }
        
        Write-Host "✓ API Server started (Job ID: $($apiJob.Id))" -ForegroundColor Green
        Write-Host "  Waiting for API to be ready..." -ForegroundColor Cyan
        
        # Wait for API to be ready (max 10 seconds)
        $timeout = 10
        $elapsed = 0
        while (-not (Test-APIServer) -and $elapsed -lt $timeout) {
            Start-Sleep -Seconds 1
            $elapsed++
            Write-Host "." -NoNewline
        }
        Write-Host ""
        
        if (Test-APIServer) {
            Write-Host "✓ API Server is ready" -ForegroundColor Green
            Write-Host "  API: http://localhost:8000" -ForegroundColor Cyan
            Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Cyan
        } else {
            Write-Host "! API Server may not be ready yet" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Starting UI..." -ForegroundColor Green
        python launch.py
        
        # Clean up API server job when UI closes
        Write-Host ""
        Write-Host "Stopping API Server..." -ForegroundColor Yellow
        Stop-Job -Job $apiJob
        Remove-Job -Job $apiJob
        Write-Host "✓ API Server stopped" -ForegroundColor Green
    }
    
    "4" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Ground Station Core stopped" -ForegroundColor Green
