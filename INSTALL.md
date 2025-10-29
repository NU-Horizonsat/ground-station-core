# Ground Station Core - Installation and Setup Guide

## Overview

Ground Station Core (GSC) is a comprehensive, open-source satellite tracking and communication system. Version 2.0 brings modern architecture with FastAPI backend, improved cross-platform support, and enhanced integrations.

## Features

- 🛰️ **Satellite Tracking**: Real-time satellite position tracking and pass prediction
- 📡 **SDR Integration**: Compatible with all common SDR hardware via SoapySDR
- 🎯 **Antenna Control**: Integrated rotator control for automated tracking
- 📊 **Telemetry Monitoring**: Real-time data visualization with InfluxDB and Grafana
- 🔧 **Command Uplink**: Send commands to satellites using CCSDS protocol
- 🌐 **REST API**: Modern FastAPI backend for flexible integration
- 🎨 **Modern UI**: Updated GUI with ttkbootstrap
- 🐳 **Docker Support**: Easy deployment with docker-compose
- 💻 **Cross-Platform**: Works on Windows and Linux

## System Requirements

### Minimum Requirements
- Python 3.8 or higher
- 4GB RAM
- 500MB disk space
- Internet connection (for TLE data and optional integrations)

### Optional Hardware
- SDR device (RTL-SDR, HackRF, USRP, LimeSDR, etc.) for transmission/reception
- Antenna rotator with serial interface (e.g., rot2prog compatible)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/NU-Horizonsat/ground-station-core.git
cd ground-station-core
```

### 2. Install Python Dependencies

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note**: Some packages (like cartopy and SoapySDR) require system-level dependencies. See detailed installation instructions below.

### 3. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your settings
# Set your ground station coordinates, email settings, etc.
```

### 4. Run the Application

#### Option A: Run Everything with Docker (Recommended)
```bash
docker-compose up -d
```

This starts:
- API Server on http://localhost:8000
- InfluxDB on http://localhost:8086
- Grafana on http://localhost:3000

#### Option B: Run Components Separately

**Start the API Server:**
```bash
python backend/api_server.py
```

**Start the UI:**
```bash
python ui.py
```

## Detailed Installation

### System Dependencies

#### Windows

1. **Install Python 3.8+** from https://www.python.org/downloads/

2. **Install Visual C++ Build Tools** (required for some Python packages):
   - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++"

3. **Optional: Install SoapySDR** for SDR support:
   ```powershell
   # Download PothosSDR bundle (includes SoapySDR)
   # https://downloads.myriadrf.org/builds/PothosSDR/
   ```

#### Linux (Ubuntu/Debian)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and development tools
sudo apt-get install -y python3 python3-pip python3-venv build-essential

# Install system dependencies for Python packages
sudo apt-get install -y \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    libusb-1.0-0-dev \
    pkg-config

# Optional: Install SoapySDR
sudo apt-get install -y soapysdr-tools python3-soapysdr

# Optional: Install SDR drivers
sudo apt-get install -y \
    rtl-sdr \
    hackrf \
    libhackrf-dev \
    soapysdr-module-rtlsdr \
    soapysdr-module-hackrf
```

#### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Install system dependencies
brew install geos proj

# Optional: Install SoapySDR
brew install soapysdr
```

### Python Virtual Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate.bat

# Activate (Linux/macOS)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt
```

### Configuration

#### 1. Ground Station Location

Edit `.env`:
```bash
GSC_LATITUDE=37.7749      # Your latitude
GSC_LONGITUDE=-122.4194   # Your longitude
GSC_ALTITUDE=50           # Altitude in meters
```

#### 2. Email Notifications (Optional)

Create `~/.gsc/email.cfg` (Linux) or `C:\Users\<YourName>\.gsc\email.cfg` (Windows):
```
your-email@gmail.com
your-app-password
```

**Note**: For Gmail, you need to create an App Password: https://support.google.com/accounts/answer/185833

#### 3. Serial Port for Rotator (Optional)

Windows: `COM3` (or appropriate COM port)
Linux: `/dev/ttyUSB0` (or `/dev/ttyACM0`)

Set in `.env`:
```bash
ANT_SERIAL_PORT=COM3  # Windows
# or
ANT_SERIAL_PORT=/dev/ttyUSB0  # Linux
```

## Running the System

### Development Mode

1. **Start API Server**:
   ```bash
   python backend/api_server.py
   ```

2. **In another terminal, start the UI**:
   ```bash
   python ui.py
   ```

3. **Access Services**:
   - API Documentation: http://localhost:8000/docs
   - Ground Station UI: Launches automatically

### Production Mode with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

#### Access Services:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **InfluxDB**: http://localhost:8086 (admin/adminpassword123)
- **Grafana**: http://localhost:3000 (admin/admin)

## Usage

### Tracking a Satellite

1. Open the UI
2. Go to "Satellite Position" tab
3. Select satellite from dropdown or enter TLE data
4. Click "Update Position" or enable "Real-time tracking"

### Predicting Passes

1. Go to "Pass Times" tab
2. Enter your location coordinates
3. Set minimum elevation (10° recommended)
4. Select satellite
5. Click "Calculate Passes"

### Sending Commands

1. Ensure API server is running and SDR is connected
2. Go to "Command Control" tab
3. Select command type
4. Fill in parameters
5. Click "Send Command"

### Scheduling Commands

1. Go to "Schedule" tab
2. Select command and parameters
3. Set execution time
4. Click "Add to Schedule"

### Monitoring Telemetry

1. **Via UI**: "Telemetry" tab shows real-time graphs
2. **Via Grafana**: 
   - Open http://localhost:3000
   - Default credentials: admin/admin
   - Add InfluxDB as data source
   - Create dashboards for your telemetry

## API Usage

The REST API can be accessed programmatically:

```python
from api_client import GroundStationAPIClient

# Create client
client = GroundStationAPIClient("http://localhost:8000")

# Get system status
status = client.get_status()
print(status)

# Send ping to satellite
response = client.ping_satellite(spacecraft_id=1)
print(response)

# Get telemetry
telemetry = client.get_latest_telemetry(limit=50)
print(telemetry)
```

See `api_client.py` for full API reference.

## Troubleshooting

### API Server Won't Start
- Check if port 8000 is already in use
- Verify Python dependencies are installed
- Check logs for configuration errors

### SDR Not Detected
- Install SoapySDR and appropriate drivers
- Run `SoapySDRUtil --find` to list devices
- Check USB permissions (Linux: add user to `plugdev` group)

### Serial Port Access Denied (Linux)
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Docker Issues
```bash
# Reset Docker environment
docker-compose down -v
docker-compose up --build
```

## Development

### Project Structure
```
ground-station-core/
├── backend/           # FastAPI backend
│   └── api_server.py
├── src/              # C/C++ core modules
├── grc/              # GNU Radio flowgraphs
├── config.py         # Configuration management
├── uplink.py         # Satellite uplink module
├── ui.py             # GUI application
├── api_client.py     # API client library
├── command_handler.py # Command handler utilities
├── requirements.txt  # Python dependencies
├── docker-compose.yml
└── Dockerfile
```

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black *.py backend/*.py

# Lint
flake8 *.py backend/*.py
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

See LICENSE file for details.

## Support

- **Issues**: https://github.com/NU-Horizonsat/ground-station-core/issues
- **Wiki**: https://github.com/NU-Horizonsat/ground-station-core/wiki
- **Discussions**: https://github.com/NU-Horizonsat/ground-station-core/discussions

## Acknowledgments

- Original GSC development by Stanislav Podolsky
- Uses SoapySDR for SDR abstraction
- Orbital mechanics via Skyfield and PyEphem
- Visualization with Matplotlib and Cartopy
