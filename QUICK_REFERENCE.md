# Ground Station Core v2.0 - Quick Reference

## 🚀 Quick Start Commands

### Windows
```powershell
.\start.ps1
```

### Linux/macOS
```bash
./start.sh
```

### Docker
```bash
docker-compose up -d
```

## 📍 Service URLs

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| API Server | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| InfluxDB | http://localhost:8086 | admin/adminpassword123 |
| Grafana | http://localhost:3000 | admin/admin |

## 🔧 Common Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy config template
cp .env.template .env

# Edit configuration
nano .env  # Linux/macOS
notepad .env  # Windows
```

### Running Services

```bash
# API Server only
python backend/api_server.py

# UI only
python ui.py

# Both with Docker
docker-compose up -d

# View Docker logs
docker-compose logs -f
```

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove data
docker-compose down -v

# Rebuild after changes
docker-compose up --build

# View logs
docker-compose logs -f [service-name]
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Configuration (create from .env.template) |
| `config.py` | Configuration management |
| `backend/api_server.py` | REST API server |
| `ui.py` | GUI application |
| `uplink.py` | Satellite uplink module |
| `api_client.py` | API client library |
| `command_handler.py` | Command utilities |

## 🔑 Environment Variables

### Required
```bash
GSC_LATITUDE=37.7749
GSC_LONGITUDE=-122.4194
GSC_ALTITUDE=50
```

### Optional
```bash
GSC_SDR_FREQ=437000000
GSC_SDR_TX_GAIN=70.0
ANT_SERIAL_PORT=COM3
INFLUXDB_TOKEN=your-token
EMAIL_SENDER=your-email@gmail.com
```

## 🐍 Python API Examples

### Connect to API
```python
from api_client import GroundStationAPIClient

client = GroundStationAPIClient("http://localhost:8000")
```

### Get Status
```python
status = client.get_status()
print(status)
```

### Send Command
```python
client.ping_satellite(spacecraft_id=1)
```

### Predict Passes
```python
passes = client.predict_passes(
    satellite="ISS",
    hours=24,
    min_elevation=10.0
)
```

### Get Telemetry
```python
data = client.get_latest_telemetry(limit=100)
```

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -ti:8000 | xargs kill -9
```

### Permission Denied (Serial Port - Linux)
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Dependencies Won't Install
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing again
pip install -r requirements.txt

# Or use conda
conda install -c conda-forge <package>
```

### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python version (needs 3.8+)
python --version
```

## 📊 Monitoring

### View API Logs
```bash
# Docker
docker-compose logs -f gsc-api

# Manual
# Check console output where api_server.py is running
```

### View InfluxDB Data
1. Open http://localhost:8086
2. Login with admin/adminpassword123
3. Navigate to Data Explorer

### Set Up Grafana Dashboard
1. Open http://localhost:3000
2. Login with admin/admin
3. Add Data Source → InfluxDB
4. Create dashboard with queries

## 🧪 Testing

### Test API Connection
```bash
curl http://localhost:8000
```

### Test API Endpoint
```bash
curl http://localhost:8000/status
```

### Python Test
```python
from api_client import GroundStationAPIClient
client = GroundStationAPIClient()
print("Connected!" if client.test_connection() else "Failed!")
```

## 📦 Package Management

### Update Dependencies
```bash
pip list --outdated
pip install --upgrade <package>
```

### Freeze Current Environment
```bash
pip freeze > requirements-frozen.txt
```

### Virtual Environment
```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Deactivate
deactivate
```

## 🔐 Security Notes

- Never commit `.env` file
- Use environment variables for secrets
- Change default Grafana/InfluxDB passwords
- Use HTTPS in production
- Restrict API access in production

## 📚 Documentation Links

- Installation: `INSTALL.md`
- Changes: `CHANGELOG.md`
- Summary: `MODERNIZATION_SUMMARY.md`
- API Docs: http://localhost:8000/docs
- Main README: `README.md`

## ⚡ Performance Tips

1. Use Docker for production
2. Enable InfluxDB for time-series data
3. Adjust log levels in production
4. Use connection pooling for API
5. Cache TLE data locally

## 🆘 Getting Help

1. Check `INSTALL.md` for detailed instructions
2. Review error logs
3. Check GitHub issues
4. Read API documentation
5. Review configuration in `.env`

---

**Keep this handy for quick reference! 📌**
