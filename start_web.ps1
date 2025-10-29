# Start Web UI Script - Windows PowerShell
# Launches the Streamlit web interface for Ground Station Core

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Ground Station Core - Web UI" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[ OK ] Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "[FAIL] Python not found. Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Check if streamlit is installed
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

python -c "import streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Streamlit not installed" -ForegroundColor Red
    Write-Host ""
    $install = Read-Host "Install required packages? (y/N)"
    
    if ($install -eq 'y' -or $install -eq 'Y') {
        Write-Host ""
        Write-Host "Installing web UI dependencies..." -ForegroundColor Yellow
        pip install streamlit plotly pandas skyfield requests
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[ OK ] Installation complete" -ForegroundColor Green
        }
        else {
            Write-Host "[FAIL] Installation failed" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "Please install manually: pip install streamlit plotly pandas" -ForegroundColor Yellow
        exit 1
    }
}
else {
    Write-Host "[ OK ] Streamlit installed" -ForegroundColor Green
}

# Check if API server is running
Write-Host ""
Write-Host "Checking API server..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[ OK ] API server is running at http://localhost:8000" -ForegroundColor Green
}
catch {
    Write-Host "[WARN] API server not detected at http://localhost:8000" -ForegroundColor Yellow
    Write-Host "       The web UI will work, but some features may be limited." -ForegroundColor Gray
    Write-Host "       To start API server: python backend/api_server.py" -ForegroundColor Gray
}

# Launch Streamlit
Write-Host ""
Write-Host "Starting Web UI..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Web UI will open in your browser" -ForegroundColor Green
Write-Host "URL: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Start Streamlit
streamlit run streamlit_ui.py --server.headless true
