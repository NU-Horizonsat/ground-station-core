import json
import requests
from urllib.parse import urljoin

class GroundStationClient:
    """Client for interacting with the ground station API"""
    def __init__(self, host="localhost", port=25565):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = 5  # seconds
        
    def connect(self):
        """Test connection to the ground station API"""
        try:
            response = self.get_status()
            if response[0]:
                return True, response[1]
            else:
                return False, "API returned error"
        except Exception as e:
            return False, str(e)
    
    def disconnect(self):
        """Clean up any resources"""
        # Nothing specific to do for a REST API client
        return True, "Disconnected"
    
    def _make_request(self, method, endpoint, data=None):
        """Make a request to the API"""
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method == "POST":
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            else:
                return False, f"Unsupported method: {method}"
            
            if response.status_code != 200:
                return False, f"API error: {response.status_code} {response.text}"
            
            return True, response.json()
        except requests.exceptions.ConnectionError:
            return False, "Connection error: Check if the server is running"
        except requests.exceptions.Timeout:
            return False, "Request timed out"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_status(self):
        """Get the status of the ground station"""
        return self._make_request("GET", "/status")
    
    def get_observation(self):
        """Get the current observation"""
        return self._make_request("GET", "/observation")
    
    def set_observation(self, observation_data):
        """Set up an observation"""
        return self._make_request("POST", "/observation", observation_data)
    
    def set_antenna_position(self, position_data):
        """Set the antenna position"""
        return self._make_request("POST", "/antenna", {"position": position_data})
    
    def start_calibration(self, azimuth=True, elevation=True):
        """Start antenna calibration"""
        calibration_data = {
            "calibration": {
                "azimuth": azimuth,
                "elevation": elevation
            }
        }
        return self._make_request("POST", "/calibration", calibration_data)