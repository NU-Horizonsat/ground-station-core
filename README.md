# Ground Station Core (GSC) v2.0

All-in-one open-source utility for SDR-based satellite tracking and communication. Everything you need to establish your own amateur or professional ground station.

![License](https://img.shields.io/badge/license-See%20LICENSE-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## 🚀 What's New in v2.0

- ✨ **Modern FastAPI Backend**: RESTful API for all ground station operations
- 🎨 **Improved UI**: Updated GUI with ttkbootstrap and better UX
- �️ **World Map Visualization**: Interactive world map with satellite ground tracks (Cartopy/Plotly)
- 🌐 **Web Interface**: Browser-based UI with Streamlit for remote access
- ☁️ **AWS Ground Station**: Hybrid local/cloud operations support
- �🐳 **Docker Support**: Easy deployment with docker-compose
- 💻 **Cross-Platform**: Full Windows, Linux, and macOS support
- 🔧 **Better Configuration**: Environment-based config management
- 📊 **Enhanced Integrations**: Seamless InfluxDB and Grafana integration
- 🛡️ **Improved Error Handling**: Graceful fallbacks and better error messages
- 📡 **Updated SDR Support**: Latest SoapySDR integration with fallback modes

## 📋 Features

### Core Capabilities
- [x] **Commercially proven** in real-world deployments
- [x] **SDR Compatible**: Works with all common SDR devices (RTL-SDR, HackRF, LimeSDR, USRP, etc.)
- [x] **Antenna Control**: Compatible with all common rotator controllers
- [x] **Autonomous Operation**: No internet connection required after initial setup
- [x] **Offline TLE Management**: Cache and manage satellite orbital elements locally

### Flexibility
- [x] **GNU Radio Integration**: Customize digital signal processing
- [x] **Pre/Post Pass Actions**: Automate actions before and after satellite passes
- [x] **Network Architecture**: Distributed operations via REST API
- [x] **Extensible**: Easy to add new features and integrations

### Monitoring & Control
- [x] **Real-time Status**: Live satellite position and telemetry
- [x] **Email Notifications**: Automated pass reports and alerts
- [x] **Time Series Database**: InfluxDB integration for telemetry storage
- [x] **Grafana Dashboards**: Beautiful visualization of satellite data
- [x] **REST API**: Programmatic access to all features

### Satellite Operations
- [x] **CCSDS Protocol**: Standard-compliant command uplink
- [x] **Doppler Compensation**: Automatic frequency correction
- [x] **Pass Prediction**: Calculate future satellite passes
- [x] **Command Scheduling**: Queue commands for automatic execution
- [x] **Modulation Support**: BPSK, GMSK, and more

## 🏗️ System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   UI (GUI)  │────▶│  FastAPI     │────▶│   SDR       │
│   Python    │     │  Backend     │     │   Hardware  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ├──────▶ InfluxDB (Telemetry)
                           │
                           ├──────▶ Rotator Control
                           │
                           └──────▶ GNU Radio
```

## 📦 Quick Start

### Prerequisites
- Python 3.8 or higher
- 4GB RAM recommended
- Optional: SDR hardware for transmission/reception
- Optional: Antenna rotator for automated tracking

### Installation

#### Windows
```powershell
# Clone repository
git clone https://github.com/NU-Horizonsat/ground-station-core.git
cd ground-station-core

# Run startup script (handles everything)
.\start.ps1
```

#### Linux/macOS
```bash
# Clone repository
git clone https://github.com/NU-Horizonsat/ground-station-core.git
cd ground-station-core

# Make script executable
chmod +x start.sh

# Run startup script
./start.sh
```

#### Docker (All Platforms)
```bash
# Start everything with Docker
docker-compose up -d

# Access services:
# - API: http://localhost:8000
# - Grafana: http://localhost:3000
# - InfluxDB: http://localhost:8086
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## 🎮 User Interfaces

Ground Station Core offers **three UI options**:

### 1. Desktop UI (ui_v2.py)
Traditional Tkinter application with world map visualization
```powershell
python ui_v2.py
```

### 2. Web UI (streamlit_ui.py) ⭐ NEW
Modern browser-based interface - **Recommended for operations**
```powershell
streamlit run streamlit_ui.py
# Opens at http://localhost:8501
```

### 3. API Only (backend/api_server.py)
Headless operation with REST API
```powershell
python backend/api_server.py
# API at http://localhost:8000
```

**See [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) for detailed UI comparison and usage**

## ☁️ AWS Ground Station Support

Switch between your local ground station and AWS Ground Station:
- Global coverage with 14+ AWS ground stations
- Managed infrastructure
- Seamless hybrid operations

**See [AWS_INTEGRATION.md](AWS_INTEGRATION.md) for setup guide**

## 📖 Documentation

- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **Web UI Guide**: [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) ⭐ NEW
- **AWS Integration**: [AWS_INTEGRATION.md](AWS_INTEGRATION.md) ⭐ NEW
- **UI Improvements**: [UI_IMPROVEMENTS.md](UI_IMPROVEMENTS.md)
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Configuration**: See `.env.template` for all settings
- **API Documentation**: http://localhost:8000/docs (when running)
- **Wiki**: https://github.com/NU-Horizonsat/ground-station-core/wiki

## 🧪 Tested With

### Satellites
- [x] NOAA weather satellites (APT)
- [x] ISS voice communications
- [x] CubeSats (BPSK, FSK modulation)
- [x] Amateur radio satellites

### SDR Hardware
- [x] RTL-SDR
- [x] HackRF One
- [x] LimeSDR
- [x] USRP B200/B210
- [x] Airspy

### Antenna Controllers
- [x] rot2prog compatible controllers
- [x] GS-232 protocol
- [x] Custom serial controllers

## 🎯 Usage Examples

### Track a Satellite
```python
from api_client import GroundStationAPIClient

client = GroundStationAPIClient()

# Get predicted passes
passes = client.predict_passes(
    satellite="ISS",
    hours=24,
    min_elevation=10.0
)

print(f"Found {len(passes['passes'])} passes")
```

### Send a Command
```python
# Send ping to spacecraft
response = client.ping_satellite(spacecraft_id=1)
print(response)

# Send custom command
response = client.send_command(
    spacecraft_id=1,
    command_type=42,
    data="0102030405",  # Hex data
    modulation="bpsk"
)
```

### Monitor Telemetry
```python
# Get latest telemetry
telemetry = client.get_latest_telemetry(limit=100)

# Add new telemetry point
client.add_telemetry(
    parameter="battery",
    value=12.5,
    unit="V"
)
```

## 🔧 Configuration

Key configuration options in `.env`:

```bash
# Ground Station Location
GSC_LATITUDE=37.7749
GSC_LONGITUDE=-122.4194
GSC_ALTITUDE=50

# SDR Settings
GSC_SDR_FREQ=437000000
GSC_SDR_SAMPLE_RATE=2000000
GSC_SDR_TX_GAIN=70.0

# Database
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-here
```

See `.env.template` for all available options.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8

# Run tests
pytest

# Format code
black *.py backend/*.py

# Lint
flake8 *.py backend/*.py
```

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original development by Stanislav Podolsky
- NU-Horizonsat team for continued development
- SoapySDR project for SDR abstraction
- Open source satellite tracking community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/NU-Horizonsat/ground-station-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NU-Horizonsat/ground-station-core/discussions)
- **Wiki**: [Project Wiki](https://github.com/NU-Horizonsat/ground-station-core/wiki)

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Made with ❤️ for the satellite tracking community**

