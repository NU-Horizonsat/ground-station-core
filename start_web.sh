#!/bin/bash
# Start Web UI Script - Linux/macOS
# Launches the Streamlit web interface for Ground Station Core

echo "======================================"
echo "  Ground Station Core - Web UI"
echo "======================================"
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "✗ Python not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✓ Python found: $PYTHON_VERSION"

# Check if streamlit is installed
echo ""
echo "Checking dependencies..."

if ! $PYTHON_CMD -c "import streamlit" &> /dev/null; then
    echo "✗ Streamlit not installed"
    echo ""
    read -p "Install required packages? (y/N): " install
    
    if [ "$install" = "y" ] || [ "$install" = "Y" ]; then
        echo ""
        echo "Installing web UI dependencies..."
        $PYTHON_CMD -m pip install streamlit plotly pandas skyfield requests
        
        if [ $? -eq 0 ]; then
            echo "✓ Installation complete"
        else
            echo "✗ Installation failed"
            exit 1
        fi
    else
        echo "Please install manually: pip install streamlit plotly pandas"
        exit 1
    fi
else
    echo "✓ Streamlit installed"
fi

# Check if API server is running
echo ""
echo "Checking API server..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API server is running at http://localhost:8000"
else
    echo "⚠ API server not detected at http://localhost:8000"
    echo "  The web UI will work, but some features may be limited."
    echo "  To start API server: python backend/api_server.py"
fi

# Launch Streamlit
echo ""
echo "Starting Web UI..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Web UI will open in your browser"
echo "📍 URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start Streamlit
$PYTHON_CMD -m streamlit run streamlit_ui.py --server.headless true
