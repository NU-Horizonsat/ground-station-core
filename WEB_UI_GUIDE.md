# Web UI Guide - Ground Station Core

## Overview

Ground Station Core now offers **two UI options**:

1. **Desktop UI** (`ui_v2.py`) - Traditional Tkinter application with world map
2. **Web UI** (`streamlit_ui.py`) - Modern browser-based interface

## Web UI (Streamlit)

### Features

✨ **Key Capabilities:**
- 🌐 **Browser-based** - Access from any device on your network
- 🗺️ **Interactive World Map** - Powered by Plotly for smooth pan/zoom
- 📊 **Real-time Updates** - Auto-refresh telemetry and tracking data
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- ☁️ **AWS Integration** - Switch between local and AWS Ground Station
- 🎨 **Modern UI** - Clean, intuitive interface with tabs

### Installation

Install web UI dependencies:

```powershell
pip install streamlit plotly pandas
```

### Running the Web UI

**Option 1: Direct Launch**
```powershell
streamlit run streamlit_ui.py
```

**Option 2: Custom Port**
```powershell
streamlit run streamlit_ui.py --server.port 8501
```

**Option 3: Network Access**
```powershell
streamlit run streamlit_ui.py --server.address 0.0.0.0
```

The web interface will open automatically in your default browser at:
```
http://localhost:8501
```

### Web UI Layout

#### Sidebar (Left)
- **Configuration Section**
  - Ground Station Selection (Local/AWS)
  - AWS Configuration (when AWS selected)
  - API Connection Settings
  - Ground Station Location
  - System Status

#### Main Tabs

**1. 📊 Overview**
- System status metrics
- Current satellite info
- Real-time clock
- Activity log

**2. 🗺️ Satellite Tracking**
- Satellite selector with preset TLEs
- TLE editor for custom satellites
- Interactive world map with:
  - Satellite ground track (blue line)
  - Current satellite position (red marker)
  - Ground station location (green triangle)
  - Natural Earth projection
- Real-time position data:
  - Latitude, Longitude, Altitude
  - Azimuth, Elevation, Range
  - Velocity
  - Visibility status

**3. 🔭 Pass Prediction**
- Time span selector (1-168 hours)
- Minimum elevation filter
- Calculate upcoming passes
- Interactive table with:
  - AOS/LOS times
  - Duration
  - Maximum elevation
  - AOS/LOS azimuths
- CSV export functionality

**4. 📡 Commands**
- Command type selector
- Spacecraft ID input
- JSON payload editor
- Send commands via API
- Activity logging

**5. 📈 Telemetry**
- Real-time telemetry metrics
- Auto-refresh toggle
- Historical charts (battery, temperature, signal)
- Interactive Plotly graphs

### Web UI Advantages

**vs Desktop UI:**
- ✅ No window management - runs in browser
- ✅ Better for remote access
- ✅ More responsive charts and maps
- ✅ Easier multi-user access
- ✅ Mobile-friendly
- ✅ Auto-save scroll positions

**When to Use Web UI:**
- Monitoring from multiple devices
- Remote ground station access
- Collaborative operations
- Mobile monitoring
- Better visualization needs

### Configuration

**Environment Variables** (optional):

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### Network Access

To access from other devices on your network:

1. Start with network binding:
   ```powershell
   streamlit run streamlit_ui.py --server.address 0.0.0.0
   ```

2. Find your IP address:
   ```powershell
   ipconfig
   ```

3. Access from other devices:
   ```
   http://<your-ip>:8501
   ```

### Security Considerations

⚠️ **Important for Production:**

1. **Authentication** - Streamlit doesn't include built-in auth
   - Use reverse proxy (nginx/Apache) with authentication
   - Deploy behind VPN
   - Use SSH tunneling for remote access

2. **HTTPS** - Enable SSL for production:
   ```toml
   [server]
   sslCertFile = "/path/to/cert.pem"
   sslKeyFile = "/path/to/key.pem"
   ```

3. **Firewall** - Limit port 8501 to trusted IPs

### Performance Tips

**Large Datasets:**
- Use `st.cache_data` for expensive calculations
- Limit ground track points for smoother rendering
- Adjust auto-refresh intervals

**Memory Management:**
- Clear old session state periodically
- Limit telemetry history length

### Troubleshooting

**Issue: Web UI won't start**
```
Solution: Check if port 8501 is already in use
netstat -ano | findstr :8501
```

**Issue: Map not rendering**
```
Solution: Ensure plotly is installed
pip install plotly
```

**Issue: Satellite tracking errors**
```
Solution: Install skyfield
pip install skyfield
```

**Issue: AWS features not working**
```
Solution: Install and configure boto3
pip install boto3
aws configure
```

## Desktop UI with World Map

The enhanced desktop UI (`ui_v2.py`) now includes:

### New Features

**🗺️ World Map Visualization**
- Cartopy integration for real geographic projection
- Satellite ground track overlay
- Ground station marker
- Current satellite position
- Visibility circle

**☁️ AWS Ground Station Switching**
- Radio button selector in Settings tab
- AWS configuration panel
- Connection testing
- Ground station type indicator on map

### Installation (Desktop)

```powershell
# Basic (without world map)
pip install matplotlib skyfield numpy

# With world map (requires system libraries)
pip install cartopy

# Note: Cartopy requires GEOS and PROJ libraries
# Windows: Use conda
conda install cartopy

# Or use simple 2D fallback (no cartopy needed)
```

### Using the World Map

1. **Load a Satellite**
   - Go to "Satellite Tracking" tab
   - Select satellite from dropdown (or enter custom TLE)
   - Click "Load TLE"

2. **View on Map**
   - Map shows:
     - 🔵 Blue line: Ground track (next ~100 minutes)
     - 🔴 Red dot: Current satellite position
     - 🟢 Green triangle: Ground station location
     - ⭕ Red dashed circle: Visibility footprint

3. **Update Position**
   - Click "Update Position Now" for manual update
   - Enable "Real-time Tracking" for auto-updates every 5 seconds

### Ground Station Switching

**In Settings Tab:**

1. **Select Ground Station Type:**
   - 🏠 **Local Ground Station** - Your own hardware
   - ☁️ **AWS Ground Station** - Amazon's network

2. **Configure AWS (if selected):**
   - Enter AWS Region (e.g., us-west-2)
   - Enter Ground Station ID
   - Enter Mission Profile ARN
   - Click "Test AWS Connection"

3. **Active Indicator:**
   - Shows current active ground station
   - Updates map legend
   - Routes commands accordingly

### Map Features

**With Cartopy (Enhanced):**
- Natural Earth projection
- Country borders
- Ocean/land coloring
- Proper geodesic calculations
- Labeled gridlines

**Without Cartopy (Fallback):**
- Simple 2D lat/lon plot
- Grid lines
- All tracking features work
- Lighter weight

### Keyboard Shortcuts (Desktop)

- `F5` - Refresh position
- `Ctrl+S` - Save configuration
- `Ctrl+Q` - Quit application

## Comparison Table

| Feature | Desktop UI | Web UI |
|---------|-----------|--------|
| World Map | ✅ Cartopy/Matplotlib | ✅ Plotly Interactive |
| Satellite Tracking | ✅ | ✅ |
| Pass Prediction | ✅ | ✅ |
| Command Sending | ✅ | ✅ |
| Telemetry | ✅ Charts | ✅ Real-time Charts |
| AWS Switching | ✅ | ✅ |
| Remote Access | ❌ | ✅ Easy |
| Mobile Support | ❌ | ✅ Responsive |
| Installation | Complex (cartopy) | Simple (pip) |
| Performance | Native | Browser-based |
| Multi-user | ❌ | ✅ |
| Offline Mode | ✅ | ⚠️ Needs server |

## Best Practices

### Development/Testing
- Use **Desktop UI** for quick local testing
- Simpler to debug
- Direct Python execution

### Operations/Monitoring
- Use **Web UI** for operations
- Better for team coordination
- Remote monitoring
- Mobile access

### Production Deployment
- Run both simultaneously:
  ```powershell
  # Terminal 1: API Server
  python backend/api_server.py
  
  # Terminal 2: Web UI
  streamlit run streamlit_ui.py
  
  # Terminal 3: Desktop UI (optional)
  python ui_v2.py
  ```

## Integration with Backend

Both UIs connect to the same FastAPI backend:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Desktop UI │─────▶│              │◀─────│   Web UI    │
│  (ui_v2.py) │ HTTP │ API Server   │ HTTP │(streamlit)  │
└─────────────┘      │ (port 8000)  │      └─────────────┘
                     │              │
                     │  ├─ Local GS │
                     │  └─ AWS GS   │
                     └──────────────┘
```

Both UIs can:
- Share the same API endpoint
- Switch between local/AWS ground stations
- Operate simultaneously
- View same telemetry data

## Next Steps

1. **Try the Web UI**: `streamlit run streamlit_ui.py`
2. **Configure AWS**: Follow AWS Integration guide
3. **Customize Maps**: Adjust ground track length, colors
4. **Set Up Remote Access**: Configure for network access
5. **Monitor Operations**: Use whichever UI fits your workflow

## Support

- **Desktop UI Issues**: Check matplotlib/cartopy installation
- **Web UI Issues**: Check streamlit/plotly installation
- **AWS Issues**: Verify boto3 and AWS credentials
- **API Connection**: Ensure backend is running on port 8000
