"""
FastAPI Backend Server for Ground Station Core
Provides REST API for satellite operations, telemetry, and command handling
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import ground station modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config import get_config, init_config
    from uplink import SatelliteUplink, SpacecraftID, CommandType
except ImportError as e:
    logging.warning(f"Could not import ground station modules: {e}")
    # Create stub for development
    class SatelliteUplink:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ground Station Core API",
    description="REST API for satellite ground station operations",
    version="2.0.0"
)

# CORS middleware for web UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
config = None
uplink = None
websocket_connections: List[WebSocket] = []
telemetry_data = {
    "battery": [],
    "temperature": [],
    "signal_strength": [],
    "timestamps": []
}


# Pydantic models for API
class GroundStationInfo(BaseModel):
    """Ground station information"""
    latitude: float
    longitude: float
    altitude: float = 0.0
    name: str = "Ground Station Core"
    status: str = "operational"


class SatelliteCommand(BaseModel):
    """Satellite command request"""
    spacecraft_id: int = Field(..., description="Spacecraft ID")
    command_type: int = Field(..., description="Command type code")
    data: Optional[str] = Field(None, description="Hex-encoded command data")
    modulation: str = Field("bpsk", description="Modulation scheme (bpsk/gmsk)")


class TelemetryPoint(BaseModel):
    """Single telemetry data point"""
    timestamp: datetime
    parameter: str
    value: float
    unit: str


class SatellitePass(BaseModel):
    """Satellite pass prediction"""
    satellite_name: str
    aos_time: datetime  # Acquisition of Signal
    los_time: datetime  # Loss of Signal
    max_elevation: float
    aos_azimuth: float
    max_azimuth: float
    los_azimuth: float


class RotatorPosition(BaseModel):
    """Antenna rotator position"""
    azimuth: float = Field(..., ge=0, le=360)
    elevation: float = Field(..., ge=0, le=90)


class SystemStatus(BaseModel):
    """Overall system status"""
    api_status: str = "running"
    uplink_enabled: bool = False
    rotator_connected: bool = False
    sdr_connected: bool = False
    influxdb_connected: bool = False
    last_command_time: Optional[datetime] = None
    active_passes: int = 0


# API Routes

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global config, uplink
    
    logger.info("Starting Ground Station Core API")
    
    try:
        # Initialize configuration
        config = init_config()
        logger.info(f"Configuration loaded: {config.config.latitude}, {config.config.longitude}")
        
        # Initialize uplink (optional - may not have SDR hardware)
        try:
            uplink = SatelliteUplink(
                frequency=config.config.sdr_center_freq,
                sample_rate=config.config.sdr_sample_rate,
                tx_gain=config.config.sdr_tx_gain,
                device_args=config.config.sdr_device_args
            )
            logger.info("Uplink system initialized")
        except Exception as e:
            logger.warning(f"Uplink not available: {e}")
            uplink = None
        
    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global uplink
    
    logger.info("Shutting down Ground Station Core API")
    
    if uplink:
        try:
            uplink.stop()
        except Exception as e:
            logger.error(f"Error stopping uplink: {e}")
    
    # Close all websocket connections
    for ws in websocket_connections:
        try:
            await ws.close()
        except:
            pass


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Ground Station Core API",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get overall system status"""
    return SystemStatus(
        api_status="running",
        uplink_enabled=uplink is not None,
        rotator_connected=False,  # TODO: Check actual rotator connection
        sdr_connected=uplink is not None,
        influxdb_connected=False,  # TODO: Check InfluxDB connection
        active_passes=0
    )


@app.get("/info", response_model=GroundStationInfo)
async def get_info():
    """Get ground station information"""
    if config:
        return GroundStationInfo(
            latitude=config.config.latitude,
            longitude=config.config.longitude,
            altitude=config.config.altitude,
            status="operational"
        )
    else:
        return GroundStationInfo(
            latitude=0.0,
            longitude=0.0,
            status="configuration_error"
        )


@app.post("/command/send")
async def send_command(cmd: SatelliteCommand, background_tasks: BackgroundTasks):
    """Send command to satellite"""
    if not uplink:
        raise HTTPException(status_code=503, detail="Uplink system not available")
    
    try:
        # Decode hex data if provided
        data = bytes.fromhex(cmd.data) if cmd.data else b''
        
        # Send command in background
        background_tasks.add_task(
            uplink.send_command,
            cmd.spacecraft_id,
            cmd.command_type,
            data,
            cmd.modulation
        )
        
        logger.info(f"Command queued: spacecraft={cmd.spacecraft_id}, type={cmd.command_type}")
        
        return {
            "status": "success",
            "message": "Command queued for transmission",
            "spacecraft_id": cmd.spacecraft_id,
            "command_type": cmd.command_type
        }
        
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/command/ping/{spacecraft_id}")
async def ping_satellite(spacecraft_id: int):
    """Send ping command to satellite"""
    if not uplink:
        raise HTTPException(status_code=503, detail="Uplink system not available")
    
    try:
        uplink.ping(spacecraft_id)
        return {
            "status": "success",
            "message": f"Ping sent to spacecraft {spacecraft_id}"
        }
    except Exception as e:
        logger.error(f"Error pinging satellite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/telemetry/latest")
async def get_latest_telemetry(limit: int = 100):
    """Get latest telemetry data"""
    return {
        "battery": telemetry_data["battery"][-limit:],
        "temperature": telemetry_data["temperature"][-limit:],
        "signal_strength": telemetry_data["signal_strength"][-limit:],
        "timestamps": [t.isoformat() for t in telemetry_data["timestamps"][-limit:]]
    }


@app.post("/telemetry/add")
async def add_telemetry(data: TelemetryPoint):
    """Add telemetry data point"""
    try:
        # Store in memory
        if data.parameter == "battery":
            telemetry_data["battery"].append(data.value)
        elif data.parameter == "temperature":
            telemetry_data["temperature"].append(data.value)
        elif data.parameter == "signal_strength":
            telemetry_data["signal_strength"].append(data.value)
        
        telemetry_data["timestamps"].append(data.timestamp)
        
        # Limit stored data
        max_points = 1000
        for key in telemetry_data:
            if len(telemetry_data[key]) > max_points:
                telemetry_data[key] = telemetry_data[key][-max_points:]
        
        # Broadcast to websocket clients
        await broadcast_telemetry(data)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error adding telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/passes/predict")
async def predict_passes(
    satellite: str = "ISS",
    hours: int = 24,
    min_elevation: float = 10.0
):
    """Predict satellite passes"""
    # TODO: Implement actual pass prediction using skyfield or pyorbital
    
    return {
        "satellite": satellite,
        "ground_station": {
            "latitude": config.config.latitude if config else 0,
            "longitude": config.config.longitude if config else 0
        },
        "prediction_period_hours": hours,
        "min_elevation": min_elevation,
        "passes": [
            # Example pass data
            {
                "aos_time": "2025-10-28T12:00:00Z",
                "los_time": "2025-10-28T12:10:00Z",
                "max_elevation": 45.0,
                "aos_azimuth": 180.0,
                "max_azimuth": 270.0,
                "los_azimuth": 360.0
            }
        ]
    }


@app.post("/rotator/position")
async def set_rotator_position(position: RotatorPosition):
    """Set antenna rotator position"""
    # TODO: Implement actual rotator control
    logger.info(f"Rotator position requested: Az={position.azimuth}, El={position.elevation}")
    
    return {
        "status": "success",
        "azimuth": position.azimuth,
        "elevation": position.elevation
    }


@app.get("/rotator/position")
async def get_rotator_position():
    """Get current antenna rotator position"""
    # TODO: Implement actual rotator position reading
    return {
        "azimuth": 0.0,
        "elevation": 0.0
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


async def broadcast_telemetry(data: TelemetryPoint):
    """Broadcast telemetry to all connected websocket clients"""
    message = {
        "type": "telemetry",
        "timestamp": data.timestamp.isoformat(),
        "parameter": data.parameter,
        "value": data.value,
        "unit": data.unit
    }
    
    for ws in websocket_connections[:]:  # Copy list to avoid modification during iteration
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to websocket: {e}")
            websocket_connections.remove(ws)


@app.get("/config")
async def get_configuration():
    """Get current configuration"""
    if not config:
        raise HTTPException(status_code=503, detail="Configuration not loaded")
    
    return {
        "latitude": config.config.latitude,
        "longitude": config.config.longitude,
        "altitude": config.config.altitude,
        "api_port": config.config.api_port,
        "rotator": {
            "azimuth_port": config.config.azimuth_port,
            "elevation_port": config.config.elevation_port,
            "remote_addr": config.config.rotator_remote_addr
        },
        "sdr": {
            "center_freq": config.config.sdr_center_freq,
            "sample_rate": config.config.sdr_sample_rate,
            "tx_gain": config.config.sdr_tx_gain,
            "rx_gain": config.config.sdr_rx_gain
        }
    }


def main():
    """Run the API server"""
    # Load configuration to get port
    try:
        config = init_config()
        port = config.config.api_port
        host = config.config.api_host
    except:
        port = 8000
        host = "127.0.0.1"
    
    logger.info(f"Starting Ground Station Core API on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
