# Changelog

All notable changes to Ground Station Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-28

### 🎉 Major Release - Complete Modernization

This is a major update that modernizes the entire application architecture and improves cross-platform compatibility.

### Added

#### Backend & API
- **FastAPI REST API Server** (`backend/api_server.py`)
  - Modern REST API with automatic documentation
  - WebSocket support for real-time telemetry streaming
  - Background task processing for command execution
  - CORS middleware for web integration
  - Health checks and system status endpoints

- **API Client Library** (`api_client.py`)
  - Python client library for programmatic access
  - Type hints and comprehensive error handling
  - Session management and connection pooling

- **Configuration Management** (`config.py`)
  - Centralized configuration system
  - Support for multiple config file formats (JSON, YAML, custom .cfg)
  - Environment variable override support
  - Automatic directory creation
  - Type-safe configuration with dataclasses

#### Infrastructure
- **Docker Support**
  - `Dockerfile` for containerized deployment
  - `docker-compose.yml` with InfluxDB and Grafana
  - Production-ready configuration
  - Volume management for persistent data

- **Environment Configuration**
  - `.env.template` with all configuration options
  - Environment-based configuration
  - Secure credential management

#### Documentation
- **Comprehensive Installation Guide** (`INSTALL.md`)
  - Platform-specific instructions (Windows, Linux, macOS)
  - Detailed system requirements
  - Docker deployment guide
  - Troubleshooting section
  - API usage examples

- **Startup Scripts**
  - `start.ps1` for Windows with interactive menu
  - `start.sh` for Linux/macOS with colored output
  - Automatic virtual environment setup
  - Dependency installation
  - Service health checks

#### Dependencies
- **Complete requirements.txt**
  - All Python dependencies with version constraints
  - Optional dependencies clearly marked
  - Installation notes for system-level requirements

### Changed

#### Core Modules
- **uplink.py** - Satellite Uplink Module
  - Fixed SoapySDR import handling with proper fallback
  - Improved error messages and logging
  - Better exception handling throughout
  - Type hints for all functions
  - Graceful degradation when SDR hardware unavailable

- **command_handler.py** - Command Handler
  - Full cross-platform compatibility (Windows/Linux)
  - Environment variable configuration
  - Path handling with pathlib
  - Improved error handling in email notifications
  - Serial port auto-detection and simulation mode
  - Better logging and user feedback

- **ui.py** - User Interface
  - Ready for API integration (structure in place)
  - Improved error handling
  - Better configuration management

#### Configuration
- **default.cfg** format now supported by config.py
  - Backward compatible with existing configs
  - Can migrate to JSON/YAML if desired

### Improved

#### Error Handling
- Graceful fallback when SDR libraries unavailable
- Better error messages with actionable advice
- Proper exception hierarchies
- Logging throughout all modules

#### Cross-Platform Support
- Windows PowerShell scripts
- Linux/macOS bash scripts
- Platform-specific path handling
- Serial port configuration per platform

#### Developer Experience
- Type hints throughout codebase
- Comprehensive docstrings
- API documentation with FastAPI
- Clear project structure
- Development setup instructions

### Security
- Environment-based credential management
- No hardcoded passwords or tokens
- Secure email configuration
- CORS configuration for API

### Fixed
- SoapySDR import error that prevented module loading
- Hardcoded Linux paths in command_handler
- Email notification error handling
- Configuration file parsing issues
- Serial port error handling

### Dependencies

#### Required
- Python 3.8+
- numpy >= 1.21.0
- scipy >= 1.7.0
- fastapi >= 0.95.0
- uvicorn >= 0.20.0
- pydantic >= 2.0.0
- requests >= 2.28.0
- pyyaml >= 6.0
- python-dotenv >= 1.0.0

#### Optional
- SoapySDR (system-level install required for SDR)
- pyserial >= 3.5 (for rotator control)
- influxdb-client >= 1.36.0 (for telemetry storage)
- skyfield >= 1.42 (for pass prediction)
- matplotlib >= 3.5.0 (for visualization)
- cartopy >= 0.20.0 (for map display)

### Migration Guide

If upgrading from v1.x:

1. **Backup your configuration**
   ```bash
   cp default.cfg default.cfg.backup
   ```

2. **Install new dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file**
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

4. **Update paths**
   - Email config: Move to `~/.gsc/email.cfg` (Linux) or `%USERPROFILE%\.gsc\email.cfg` (Windows)
   - Results directory: Now configurable via `RESULTS_PREFIX` env var

5. **Start new services**
   ```bash
   # Option 1: Using startup scripts
   ./start.sh  # Linux/macOS
   .\start.ps1  # Windows
   
   # Option 2: Using Docker
   docker-compose up -d
   ```

### Breaking Changes

- Configuration file location now flexible (checks multiple locations)
- Email config file moved to `.gsc` directory in user home
- API server now required for full functionality
- Some module imports may need updates if used programmatically

### Known Issues

- cartopy requires system-level GEOS and PROJ libraries
- SoapySDR must be installed separately at system level
- Some Python packages may require Visual C++ Build Tools on Windows

### Roadmap for v2.1

- [ ] WebSocket telemetry client in UI
- [ ] Secure TLS/SSL for API
- [ ] User authentication system
- [ ] Advanced scheduling with recurring tasks
- [ ] Integration with Celestrak API for TLE updates
- [ ] Mobile app support via REST API
- [ ] Grafana dashboard templates
- [ ] Unit test coverage
- [ ] CI/CD pipeline

## [1.x] - Previous Versions

### Features from v1.x (Now Improved in v2.0)
- GNU Radio integration
- Rotator control
- Email notifications
- Pass scheduling
- SDR support
- Telemetry monitoring

---

## Version History

- **v2.0.0** (2025-10-28): Major modernization release
- **v1.x** (Previous): Original implementation

For detailed documentation, see [INSTALL.md](INSTALL.md) and the [GitHub Wiki](https://github.com/NU-Horizonsat/ground-station-core/wiki).
