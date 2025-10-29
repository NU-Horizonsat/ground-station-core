"""
Configuration Management Module for Ground Station Core
Handles loading and managing configuration from files and environment variables
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class GroundStationConfig:
    """Ground station configuration settings"""
    
    # Ground station location
    latitude: float = 48.31237
    longitude: float = 7.44126
    altitude: float = 0.0  # meters above sea level
    
    # Rotator control (rotctld)
    azimuth_port: int = 8080
    elevation_port: int = 8081
    rotator_remote_addr: str = "127.0.0.1"
    
    # API and networking
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    request_port: int = 25565
    
    # Logging
    verbosity: int = 3
    log_file: str = "dump.log"
    log_level: str = "INFO"
    
    # GNU Radio
    gnuradio_config: str = ""
    gnuradio_flowgraph: str = ""
    
    # SDR settings
    sdr_center_freq: float = 437.0e6
    sdr_sample_rate: float = 2.0e6
    sdr_tx_gain: float = 70.0
    sdr_rx_gain: float = 40.0
    sdr_device_args: str = ""
    
    # InfluxDB settings
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "ground-station"
    influxdb_bucket: str = "satellite_telemetry"
    
    # Grafana settings
    grafana_url: str = "http://localhost:3000"
    grafana_port: int = 3000
    
    # Email notifications
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_sender: str = ""
    email_password: str = ""
    email_recipients: list = field(default_factory=list)
    
    # Results and data storage
    results_prefix: str = "results"
    
    # TLE data sources
    tle_sources: list = field(default_factory=lambda: [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle"
    ])
    
    # Paths
    config_dir: Path = field(default_factory=lambda: Path.home() / ".gsc")
    data_dir: Path = field(default_factory=lambda: Path.home() / ".gsc" / "data")


class ConfigManager:
    """Manages configuration loading and saving"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self.config = GroundStationConfig()
        self.config_file = config_file or self._find_config_file()
        
        if self.config_file:
            self.load_config(self.config_file)
        
        # Override with environment variables
        self.load_from_env()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations"""
        possible_paths = [
            Path("default.cfg"),
            Path("config.json"),
            Path("config.yaml"),
            Path.home() / ".gsc" / "config.json",
            Path.home() / ".gsc" / "config.yaml",
            Path("/etc/gsc/config.json"),
            Path("/etc/gsc/config.yaml"),
            Path("sample-default.cfg"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found configuration file: {path}")
                return str(path)
        
        logger.warning("No configuration file found, using defaults")
        return None
    
    def load_config(self, config_file: str) -> None:
        """
        Load configuration from file
        
        Args:
            config_file: Path to configuration file
        """
        path = Path(config_file)
        
        if not path.exists():
            logger.warning(f"Configuration file not found: {config_file}")
            return
        
        try:
            # Try parsing as different formats
            if path.suffix in ['.json']:
                with open(path, 'r') as f:
                    data = json.load(f)
            elif path.suffix in ['.yaml', '.yml']:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                # Try custom .cfg format (key = value)
                data = self._parse_cfg_file(path)
            
            # Update config with loaded data
            self._update_config(data)
            logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def _parse_cfg_file(self, path: Path) -> Dict[str, Any]:
        """Parse custom .cfg file format"""
        data = {}
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('//') or line.startswith('#'):
                    continue
                
                # Parse key = value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().rstrip(';')
                    
                    # Remove quotes
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    # Convert to appropriate type
                    try:
                        # Try as number
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        # Keep as string
                        pass
                    
                    # Convert hyphenated keys to snake_case
                    key = key.replace('-', '_')
                    data[key] = value
        
        return data
    
    def _update_config(self, data: Dict[str, Any]) -> None:
        """Update configuration with data from dictionary"""
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            'GSC_LATITUDE': 'latitude',
            'GSC_LONGITUDE': 'longitude',
            'GSC_ALTITUDE': 'altitude',
            'GSC_API_HOST': 'api_host',
            'GSC_API_PORT': 'api_port',
            'GSC_LOG_LEVEL': 'log_level',
            'GSC_SDR_FREQ': 'sdr_center_freq',
            'GSC_SDR_SAMPLE_RATE': 'sdr_sample_rate',
            'GSC_SDR_TX_GAIN': 'sdr_tx_gain',
            'GSC_SDR_RX_GAIN': 'sdr_rx_gain',
            'INFLUXDB_URL': 'influxdb_url',
            'INFLUXDB_TOKEN': 'influxdb_token',
            'INFLUXDB_ORG': 'influxdb_org',
            'INFLUXDB_BUCKET': 'influxdb_bucket',
            'EMAIL_SMTP_SERVER': 'email_smtp_server',
            'EMAIL_SMTP_PORT': 'email_smtp_port',
            'EMAIL_SENDER': 'email_sender',
            'EMAIL_PASSWORD': 'email_password',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert to appropriate type
                current_type = type(getattr(self.config, config_key))
                try:
                    if current_type == float:
                        value = float(value)
                    elif current_type == int:
                        value = int(value)
                    elif current_type == bool:
                        value = value.lower() in ('true', '1', 'yes')
                    
                    setattr(self.config, config_key, value)
                    logger.debug(f"Loaded {config_key} from environment")
                except Exception as e:
                    logger.warning(f"Error converting {env_var}: {e}")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        directories = [
            self.config.config_dir,
            self.config.data_dir,
            Path(self.config.results_prefix),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_config(self, output_file: Optional[str] = None) -> None:
        """
        Save current configuration to file
        
        Args:
            output_file: Path to output file (default: original config file)
        """
        output_file = output_file or self.config_file or "config.json"
        path = Path(output_file)
        
        # Convert config to dictionary
        config_dict = {
            key: getattr(self.config, key)
            for key in dir(self.config)
            if not key.startswith('_') and not callable(getattr(self.config, key))
        }
        
        # Convert Path objects to strings
        for key, value in config_dict.items():
            if isinstance(value, Path):
                config_dict[key] = str(value)
        
        try:
            if path.suffix == '.json':
                with open(path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            elif path.suffix in ['.yaml', '.yml']:
                with open(path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            
            logger.info(f"Saved configuration to {output_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            logger.warning(f"Unknown configuration key: {key}")


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> GroundStationConfig:
    """Get global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config


def init_config(config_file: Optional[str] = None) -> ConfigManager:
    """Initialize global configuration"""
    global _config_manager
    _config_manager = ConfigManager(config_file)
    return _config_manager


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    config_manager = ConfigManager()
    print(f"Latitude: {config_manager.config.latitude}")
    print(f"Longitude: {config_manager.config.longitude}")
    print(f"API Port: {config_manager.config.api_port}")
    
    # Save example configuration
    config_manager.save_config("config.json")
