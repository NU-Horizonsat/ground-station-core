#!/bin/bash
# Ground Station Core - Linux/macOS Startup Script
# This script starts the API server and UI

set -e

echo -e "\033[0;32mGround Station Core - Starting...\033[0m"
echo -e "\033[0;32m=================================\033[0m"
echo ""

# Check if Python is installed
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "\033[0;32m✓ Python found: $PYTHON_VERSION\033[0m"
else
    echo -e "\033[0;31m✗ Python 3 not found. Please install Python 3.8 or higher.\033[0m"
    exit 1
fi

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo -e "\033[0;32m✓ Virtual environment found\033[0m"
    echo -e "\033[0;36m  Activating virtual environment...\033[0m"
    source venv/bin/activate
else
    echo -e "\033[0;33m! Virtual environment not found. Creating...\033[0m"
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        echo -e "\033[0;32m✓ Virtual environment created\033[0m"
        source venv/bin/activate
        
        echo -e "\033[0;36m  Installing dependencies...\033[0m"
        pip install --upgrade pip
        pip install -r requirements.txt || {
            echo -e "\033[0;33m! Some dependencies may have failed to install\033[0m"
            echo -e "\033[0;33m  This is normal if SDR libraries are not available\033[0m"
        }
    else
        echo -e "\033[0;31m✗ Failed to create virtual environment\033[0m"
        exit 1
    fi
fi

echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "\033[0;33m! .env file not found\033[0m"
    if [ -f ".env.template" ]; then
        echo -e "\033[0;36m  Copying .env.template to .env...\033[0m"
        cp .env.template .env
        echo -e "\033[0;32m✓ Created .env file\033[0m"
        echo -e "\033[0;33m  Please edit .env with your settings before running again\033[0m"
        exit 0
    else
        echo -e "\033[0;33m  Running with default configuration\033[0m"
    fi
fi

echo ""
echo -e "\033[0;32mStarting services...\033[0m"
echo -e "\033[0;32m-------------------\033[0m"
echo ""

# Function to check if API server is running
check_api_server() {
    curl -s http://localhost:8000 > /dev/null 2>&1
    return $?
}

# Ask user what to start
echo -e "\033[0;36mWhat would you like to start?\033[0m"
echo -e "\033[1;37m1. API Server only\033[0m"
echo -e "\033[1;37m2. UI only (requires API server to be running)\033[0m"
echo -e "\033[1;37m3. Both API Server and UI\033[0m"
echo -e "\033[1;37m4. Exit\033[0m"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "\033[0;32mStarting API Server...\033[0m"
        echo -e "\033[0;36mAPI will be available at: http://localhost:8000\033[0m"
        echo -e "\033[0;36mAPI documentation at: http://localhost:8000/docs\033[0m"
        echo ""
        echo -e "\033[0;33mPress Ctrl+C to stop the server\033[0m"
        echo ""
        python3 backend/api_server.py
        ;;
    
    2)
        echo ""
        # Check if API server is running
        if check_api_server; then
            echo -e "\033[0;32m✓ API Server is running\033[0m"
        else
            echo -e "\033[0;33m! API Server is not running\033[0m"
            echo -e "\033[0;33m  Some features may not work properly\033[0m"
            echo -e "\033[0;33m  Start the API server in another terminal first\033[0m"
        fi
        
        echo ""
        echo -e "\033[0;32mStarting UI...\033[0m"
        python3 launch.py
        ;;
    
    3)
        echo ""
        echo -e "\033[0;32mStarting API Server in background...\033[0m"
        
        # Start API server in background
        python3 backend/api_server.py > /tmp/gsc-api.log 2>&1 &
        API_PID=$!
        
        echo -e "\033[0;32m✓ API Server started (PID: $API_PID)\033[0m"
        echo -e "\033[0;36m  Waiting for API to be ready...\033[0m"
        
        # Wait for API to be ready (max 10 seconds)
        timeout=10
        elapsed=0
        while ! check_api_server && [ $elapsed -lt $timeout ]; do
            sleep 1
            elapsed=$((elapsed + 1))
            echo -n "."
        done
        echo ""
        
        if check_api_server; then
            echo -e "\033[0;32m✓ API Server is ready\033[0m"
            echo -e "\033[0;36m  API: http://localhost:8000\033[0m"
            echo -e "\033[0;36m  Docs: http://localhost:8000/docs\033[0m"
        else
            echo -e "\033[0;33m! API Server may not be ready yet\033[0m"
            echo -e "\033[0;36m  Check logs: tail -f /tmp/gsc-api.log\033[0m"
        fi
        
        echo ""
        echo -e "\033[0;32mStarting UI...\033[0m"
        python3 launch.py
        
        # Clean up API server when UI closes
        echo ""
        echo -e "\033[0;33mStopping API Server...\033[0m"
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
        echo -e "\033[0;32m✓ API Server stopped\033[0m"
        ;;
    
    4)
        echo -e "\033[0;33mExiting...\033[0m"
        exit 0
        ;;
    
    *)
        echo -e "\033[0;31mInvalid choice. Exiting...\033[0m"
        exit 1
        ;;
esac

echo ""
echo -e "\033[0;32mGround Station Core stopped\033[0m"
