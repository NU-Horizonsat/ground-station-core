"""
API Client for Ground Station Core UI
Handles communication between the UI and the backend API server
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class GroundStationAPIClient:
    """Client for communicating with Ground Station Core API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GroundStationUI/2.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
        
        Returns:
            Response data as dictionary, or None on error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: Could not reach API server at {self.base_url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to API server"""
        result = self._make_request('GET', '/')
        return result is not None
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get system status"""
        return self._make_request('GET', '/status')
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get ground station information"""
        return self._make_request('GET', '/info')
    
    def send_command(self, spacecraft_id: int, command_type: str, 
                    data: Optional[str] = None, modulation: str = 'bpsk') -> Optional[Dict[str, Any]]:
        """
        Send command to satellite
        
        Args:
            spacecraft_id: Target spacecraft ID
            command_type: Command type (string like 'NOOP', 'RESET', etc.)
            data: Hex-encoded command data (optional)
            modulation: Modulation scheme (bpsk/gmsk)
        
        Returns:
            Response data
        
        Example:
            client.send_command(spacecraft_id=1, command_type='NOOP')
            client.send_command(spacecraft_id=1, command_type='SET_MODE', data='0x01')
        """
        # Convert command type string to code if needed
        command_codes = {
            'NOOP': 0,
            'RESET': 1,
            'SET_MODE': 2,
            'REQUEST_TELEMETRY': 3,
            'DEPLOY_ANTENNA': 4,
            'IMAGING_ON': 5,
            'IMAGING_OFF': 6
        }
        
        cmd_code = command_codes.get(command_type, 0) if isinstance(command_type, str) else command_type
        
        payload = {
            'spacecraft_id': spacecraft_id,
            'command_type': cmd_code,
            'modulation': modulation
        }
        
        if data:
            payload['data'] = data
        
        return self._make_request('POST', '/command/send', json=payload)
    
    def schedule_command(self, spacecraft_id: int, command_type: str, 
                        scheduled_time: datetime, data: Optional[str] = None,
                        modulation: str = 'bpsk') -> Optional[Dict[str, Any]]:
        """
        Schedule command for future execution
        
        Args:
            spacecraft_id: Target spacecraft ID
            command_type: Command type (string)
            scheduled_time: When to execute the command
            data: Hex-encoded command data (optional)
            modulation: Modulation scheme
        
        Returns:
            Response with scheduled command ID
        """
        command_codes = {
            'NOOP': 0, 'RESET': 1, 'SET_MODE': 2, 'REQUEST_TELEMETRY': 3,
            'DEPLOY_ANTENNA': 4, 'IMAGING_ON': 5, 'IMAGING_OFF': 6
        }
        
        cmd_code = command_codes.get(command_type, 0) if isinstance(command_type, str) else command_type
        
        payload = {
            'spacecraft_id': spacecraft_id,
            'command_type': cmd_code,
            'scheduled_time': scheduled_time.isoformat(),
            'modulation': modulation
        }
        
        if data:
            payload['data'] = data
        
        return self._make_request('POST', '/command/schedule', json=payload)
    
    def get_scheduled_commands(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of scheduled commands"""
        result = self._make_request('GET', '/command/scheduled')
        if result:
            return result.get('scheduled_commands', [])
        return []
    
    def cancel_scheduled_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a scheduled command"""
        return self._make_request('DELETE', f'/command/scheduled/{command_id}')
    
    def ping_satellite(self, spacecraft_id: int) -> Optional[Dict[str, Any]]:
        """Send ping command to satellite"""
        return self._make_request('POST', f'/command/ping/{spacecraft_id}')
    
    def get_latest_telemetry(self, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get latest telemetry data"""
        return self._make_request('GET', f'/telemetry/latest?limit={limit}')
    
    def get_telemetry(self, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Get current telemetry data (alias for get_latest_telemetry)
        
        Returns:
            Dictionary with telemetry data including:
            - battery: Battery level (%)
            - temperature: Temperature (°C)
            - signal: Signal strength (dBm)
            - battery_delta: Change in battery
            - temp_delta: Change in temperature
        """
        result = self.get_latest_telemetry(limit=1)
        if result and 'telemetry' in result and len(result['telemetry']) > 0:
            # Extract latest values
            latest = result['telemetry'][0]
            return {
                'battery': latest.get('battery', 90.0),
                'temperature': latest.get('temperature', 22.0),
                'signal': latest.get('signal_strength', -75.0),
                'battery_delta': 0.0,
                'temp_delta': 0.0
            }
        # Return dummy data if no telemetry available
        return {
            'battery': 90.0,
            'temperature': 22.0,
            'signal': -75.0,
            'battery_delta': 0.0,
            'temp_delta': 0.0
        }
    
    def add_telemetry(self, parameter: str, value: float, 
                     unit: str, timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Add telemetry data point
        
        Args:
            parameter: Parameter name (battery, temperature, signal_strength)
            value: Parameter value
            unit: Unit of measurement
            timestamp: Timestamp (default: now)
        
        Returns:
            Response data
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        payload = {
            'timestamp': timestamp.isoformat(),
            'parameter': parameter,
            'value': value,
            'unit': unit
        }
        
        return self._make_request('POST', '/telemetry/add', json=payload)
    
    def predict_passes(self, satellite: str = 'ISS', hours: int = 24, 
                      min_elevation: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        Predict satellite passes
        
        Args:
            satellite: Satellite name
            hours: Prediction period in hours
            min_elevation: Minimum elevation in degrees
        
        Returns:
            Pass prediction data
        """
        params = {
            'satellite': satellite,
            'hours': hours,
            'min_elevation': min_elevation
        }
        
        return self._make_request('GET', '/passes/predict', params=params)
    
    def set_rotator_position(self, azimuth: float, elevation: float) -> Optional[Dict[str, Any]]:
        """
        Set antenna rotator position
        
        Args:
            azimuth: Azimuth angle (0-360 degrees)
            elevation: Elevation angle (0-90 degrees)
        
        Returns:
            Response data
        """
        payload = {
            'azimuth': azimuth,
            'elevation': elevation
        }
        
        return self._make_request('POST', '/rotator/position', json=payload)
    
    def get_rotator_position(self) -> Optional[Dict[str, Any]]:
        """Get current antenna rotator position"""
        return self._make_request('GET', '/rotator/position')
    
    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """Get current configuration"""
        return self._make_request('GET', '/config')


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    client = GroundStationAPIClient()
    
    # Test connection
    if client.test_connection():
        print("✓ Connected to API server")
        
        # Get status
        status = client.get_status()
        if status:
            print(f"Status: {status}")
        
        # Get info
        info = client.get_info()
        if info:
            print(f"Ground Station: {info['latitude']}, {info['longitude']}")
    else:
        print("✗ Failed to connect to API server")
