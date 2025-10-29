"""
AWS Ground Station Integration Module
Handles AWS Ground Station API interactions for satellite contact scheduling
"""

import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AWSGroundStationConfig:
    """AWS Ground Station configuration"""
    region: str
    ground_station_id: str
    mission_profile_arn: str
    satellite_arn: Optional[str] = None
    dataflow_endpoint_group_arn: Optional[str] = None


@dataclass
class Contact:
    """Satellite contact information"""
    contact_id: str
    satellite_arn: str
    ground_station: str
    start_time: datetime
    end_time: datetime
    maximum_elevation: float
    status: str
    tags: Optional[Dict[str, str]] = None


class AWSGroundStationClient:
    """
    Client for AWS Ground Station operations
    Handles contact scheduling, reservation management, and data retrieval
    """
    
    def __init__(self, config: AWSGroundStationConfig):
        """
        Initialize AWS Ground Station client
        
        Args:
            config: AWS Ground Station configuration
        """
        self.config = config
        self.client = boto3.client('groundstation', region_name=config.region)
        self.s3_client = boto3.client('s3', region_name=config.region)
        
    def list_ground_stations(self) -> List[Dict[str, Any]]:
        """
        List available AWS Ground Stations
        
        Returns:
            List of ground station information
        """
        try:
            response = self.client.list_ground_stations()
            stations = response.get('groundStationList', [])
            logger.info(f"Found {len(stations)} ground stations")
            return stations
        except Exception as e:
            logger.error(f"Failed to list ground stations: {str(e)}")
            raise
    
    def get_ground_station_details(self, gs_id: str) -> Dict[str, Any]:
        """
        Get details for a specific ground station
        
        Args:
            gs_id: Ground station ID
            
        Returns:
            Ground station details
        """
        try:
            response = self.client.get_ground_station(groundStationId=gs_id)
            return response
        except Exception as e:
            logger.error(f"Failed to get ground station details: {str(e)}")
            raise
    
    def list_contacts(self, 
                     start_time: datetime,
                     end_time: datetime,
                     status_filter: Optional[List[str]] = None) -> List[Contact]:
        """
        List satellite contacts in time range
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            status_filter: Optional list of contact statuses to filter by
            
        Returns:
            List of Contact objects
        """
        try:
            params = {
                'startTime': start_time,
                'endTime': end_time
            }
            
            if status_filter:
                params['statusList'] = status_filter
            
            response = self.client.list_contacts(**params)
            
            contacts = []
            for contact_data in response.get('contactList', []):
                contact = Contact(
                    contact_id=contact_data['contactId'],
                    satellite_arn=contact_data['satelliteArn'],
                    ground_station=contact_data['groundStation'],
                    start_time=contact_data['startTime'],
                    end_time=contact_data['endTime'],
                    maximum_elevation=contact_data.get('maximumElevation', {}).get('value', 0),
                    status=contact_data['contactStatus'],
                    tags=contact_data.get('tags', {})
                )
                contacts.append(contact)
            
            logger.info(f"Found {len(contacts)} contacts")
            return contacts
            
        except Exception as e:
            logger.error(f"Failed to list contacts: {str(e)}")
            raise
    
    def reserve_contact(self,
                       mission_profile_arn: str,
                       satellite_arn: str,
                       start_time: datetime,
                       end_time: datetime,
                       ground_station: str,
                       tags: Optional[Dict[str, str]] = None) -> str:
        """
        Reserve a satellite contact
        
        Args:
            mission_profile_arn: ARN of the mission profile
            satellite_arn: ARN of the satellite
            start_time: Contact start time
            end_time: Contact end time
            ground_station: Ground station ID
            tags: Optional tags for the contact
            
        Returns:
            Contact ID of reserved contact
        """
        try:
            params = {
                'missionProfileArn': mission_profile_arn,
                'satelliteArn': satellite_arn,
                'startTime': start_time,
                'endTime': end_time,
                'groundStation': ground_station
            }
            
            if tags:
                params['tags'] = tags
            
            response = self.client.reserve_contact(**params)
            contact_id = response['contactId']
            
            logger.info(f"Reserved contact: {contact_id}")
            return contact_id
            
        except Exception as e:
            logger.error(f"Failed to reserve contact: {str(e)}")
            raise
    
    def cancel_contact(self, contact_id: str) -> bool:
        """
        Cancel a reserved contact
        
        Args:
            contact_id: ID of contact to cancel
            
        Returns:
            True if successful
        """
        try:
            self.client.cancel_contact(contactId=contact_id)
            logger.info(f"Cancelled contact: {contact_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel contact: {str(e)}")
            raise
    
    def get_contact_details(self, contact_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a contact
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact details
        """
        try:
            response = self.client.describe_contact(contactId=contact_id)
            return response
        except Exception as e:
            logger.error(f"Failed to get contact details: {str(e)}")
            raise
    
    def list_mission_profiles(self) -> List[Dict[str, Any]]:
        """
        List available mission profiles
        
        Returns:
            List of mission profile information
        """
        try:
            response = self.client.list_mission_profiles()
            profiles = response.get('missionProfileList', [])
            logger.info(f"Found {len(profiles)} mission profiles")
            return profiles
        except Exception as e:
            logger.error(f"Failed to list mission profiles: {str(e)}")
            raise
    
    def get_mission_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Get mission profile details
        
        Args:
            profile_id: Mission profile ID
            
        Returns:
            Mission profile details
        """
        try:
            response = self.client.get_mission_profile(missionProfileId=profile_id)
            return response
        except Exception as e:
            logger.error(f"Failed to get mission profile: {str(e)}")
            raise
    
    def list_configs(self, config_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List configuration objects
        
        Args:
            config_type: Optional filter by configuration type
                       (antenna-downlink, antenna-uplink, dataflow-endpoint, etc.)
        
        Returns:
            List of configuration objects
        """
        try:
            params = {}
            if config_type:
                params['configType'] = config_type
                
            response = self.client.list_configs(**params)
            configs = response.get('configList', [])
            logger.info(f"Found {len(configs)} configs")
            return configs
        except Exception as e:
            logger.error(f"Failed to list configs: {str(e)}")
            raise
    
    def download_contact_data(self, 
                             contact_id: str,
                             s3_bucket: str,
                             local_path: str) -> bool:
        """
        Download contact data from S3
        
        Args:
            contact_id: Contact ID
            s3_bucket: S3 bucket name
            local_path: Local path to save data
            
        Returns:
            True if successful
        """
        try:
            # List objects in S3 bucket with contact ID prefix
            prefix = f"contacts/{contact_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=s3_bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.warning(f"No data found for contact {contact_id}")
                return False
            
            # Download each file
            import os
            for obj in response['Contents']:
                key = obj['Key']
                filename = os.path.join(local_path, os.path.basename(key))
                
                logger.info(f"Downloading {key} to {filename}")
                self.s3_client.download_file(s3_bucket, key, filename)
            
            logger.info(f"Downloaded {len(response['Contents'])} files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download contact data: {str(e)}")
            raise
    
    def get_satellite_ephemeris(self,
                               satellite_arn: str,
                               start_time: datetime,
                               end_time: datetime) -> Dict[str, Any]:
        """
        Get satellite ephemeris data (TLE or other orbital elements)
        
        Args:
            satellite_arn: Satellite ARN
            start_time: Start time
            end_time: End time
            
        Returns:
            Ephemeris data
        """
        try:
            response = self.client.get_satellite(satelliteId=satellite_arn.split('/')[-1])
            return response
        except Exception as e:
            logger.error(f"Failed to get satellite ephemeris: {str(e)}")
            raise


class AWSGroundStationManager:
    """
    High-level manager for AWS Ground Station operations
    Provides simplified interface for common tasks
    """
    
    def __init__(self, config: AWSGroundStationConfig):
        self.client = AWSGroundStationClient(config)
        self.config = config
    
    def find_available_passes(self,
                             satellite_arn: str,
                             duration_hours: int = 24,
                             min_elevation: float = 10.0) -> List[Contact]:
        """
        Find available satellite passes
        
        Args:
            satellite_arn: Satellite ARN
            duration_hours: How many hours ahead to search
            min_elevation: Minimum elevation angle
            
        Returns:
            List of available contacts
        """
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=duration_hours)
        
        # List all contacts (available and reserved)
        contacts = self.client.list_contacts(start_time, end_time)
        
        # Filter by elevation and availability
        available = [
            c for c in contacts 
            if c.maximum_elevation >= min_elevation and c.status == 'AVAILABLE'
        ]
        
        logger.info(f"Found {len(available)} available passes")
        return available
    
    def schedule_pass(self,
                     satellite_arn: str,
                     start_time: datetime,
                     end_time: datetime,
                     tags: Optional[Dict[str, str]] = None) -> str:
        """
        Schedule a satellite pass
        
        Args:
            satellite_arn: Satellite ARN
            start_time: Pass start time
            end_time: Pass end time
            tags: Optional tags
            
        Returns:
            Contact ID
        """
        return self.client.reserve_contact(
            mission_profile_arn=self.config.mission_profile_arn,
            satellite_arn=satellite_arn,
            start_time=start_time,
            end_time=end_time,
            ground_station=self.config.ground_station_id,
            tags=tags
        )
    
    def get_upcoming_passes(self, hours_ahead: int = 24) -> List[Contact]:
        """
        Get all upcoming scheduled passes
        
        Args:
            hours_ahead: How many hours ahead to look
            
        Returns:
            List of scheduled contacts
        """
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=hours_ahead)
        
        return self.client.list_contacts(
            start_time, 
            end_time,
            status_filter=['SCHEDULED', 'EXECUTING']
        )
    
    def cancel_pass(self, contact_id: str) -> bool:
        """
        Cancel a scheduled pass
        
        Args:
            contact_id: Contact ID to cancel
            
        Returns:
            True if successful
        """
        return self.client.cancel_contact(contact_id)
    
    def get_pass_status(self, contact_id: str) -> Dict[str, Any]:
        """
        Get status of a scheduled pass
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Pass status and details
        """
        return self.client.get_contact_details(contact_id)
    
    def export_pass_schedule(self, hours_ahead: int = 24) -> str:
        """
        Export pass schedule to JSON
        
        Args:
            hours_ahead: How many hours ahead to include
            
        Returns:
            JSON string of pass schedule
        """
        passes = self.get_upcoming_passes(hours_ahead)
        
        schedule = []
        for p in passes:
            schedule.append({
                'contact_id': p.contact_id,
                'satellite': p.satellite_arn,
                'ground_station': p.ground_station,
                'start': p.start_time.isoformat(),
                'end': p.end_time.isoformat(),
                'max_elevation': p.maximum_elevation,
                'status': p.status
            })
        
        return json.dumps(schedule, indent=2)


# Utility functions

def create_aws_client(region: str, 
                     ground_station_id: str, 
                     mission_profile_arn: str) -> AWSGroundStationManager:
    """
    Factory function to create AWS Ground Station manager
    
    Args:
        region: AWS region
        ground_station_id: Ground station ID
        mission_profile_arn: Mission profile ARN
        
    Returns:
        AWSGroundStationManager instance
    """
    config = AWSGroundStationConfig(
        region=region,
        ground_station_id=ground_station_id,
        mission_profile_arn=mission_profile_arn
    )
    return AWSGroundStationManager(config)


def test_aws_connection(region: str) -> bool:
    """
    Test AWS Ground Station connection
    
    Args:
        region: AWS region
        
    Returns:
        True if connection successful
    """
    try:
        client = boto3.client('groundstation', region_name=region)
        client.list_ground_stations()
        return True
    except Exception as e:
        logger.error(f"AWS connection test failed: {str(e)}")
        return False
