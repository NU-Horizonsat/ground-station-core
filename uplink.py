import time
import struct
import logging
import numpy as np
from enum import Enum, auto
from typing import List, Dict, Optional, Union, Tuple
import SoapySDR
from SoapySDR import SOAPY_SDR_TX, SOAPY_SDR_CF32

#!/usr/bin/env python3
"""
Satellite Uplink Module - Sends commands to satellites using SDR and CCSDS standards
"""


# Try to import SDR libraries
try:
    has_soapysdr = True
except ImportError:
    has_soapysdr = False
    logging.warning("SoapySDR not available. SDR transmission functionality limited.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CCSDS Constants
class SpacecraftID(Enum):
    """Enumeration of spacecraft IDs"""
    SPACECRAFT_A = 0x01
    SPACECRAFT_B = 0x02
    # Add more spacecraft IDs as needed

class CommandType(Enum):
    """Common satellite command types"""
    PING = auto()
    REBOOT = auto()
    SET_MODE = auto()
    GET_TELEMETRY = auto()
    DEPLOY_SOLAR_PANELS = auto()
    TRANSMIT_DATA = auto()
    # Add more command types as needed

class UplinkException(Exception):
    """Exception raised for errors in the uplink module."""
    pass

class CCSDSPacket:
    """
    CCSDS Space Packet Protocol implementation
    Based on CCSDS 133.0-B-2 specification
    """
    
    def __init__(self, spacecraft_id: int, command_type: int, data: bytes = b''):
        """
        Initialize a CCSDS packet
        
        Args:
            spacecraft_id: ID of the target spacecraft
            command_type: Type of command
            data: Command payload data
        """
        self.spacecraft_id = spacecraft_id
        self.command_type = command_type
        self.data = data
        self.sequence_count = 0  # Sequence counter for packets
    
    def set_sequence_count(self, count: int) -> None:
        """Set the sequence count for the packet"""
        self.sequence_count = count & 0x3FFF  # 14 bits
    
    def build(self) -> bytes:
        """
        Build CCSDS packet according to standard
        
        Returns:
            Bytes object containing the formatted CCSDS packet
        """
        # CCSDS Primary Header (6 bytes)
        version_type_shdr_apid = (0 << 13) | (1 << 12) | (1 << 11) | (self.spacecraft_id & 0x7FF)
        
        # Sequence Flags (2 bits) + Sequence Count (14 bits)
        sequence_fields = (1 << 14) | (self.sequence_count & 0x3FFF)
        
        # Packet Length (16 bits) - Length of secondary header + data - 1
        packet_length = len(self.data) + 2 - 1
        
        # Secondary Header (2 bytes)
        command_type_byte = self.command_type & 0xFF
        
        # Calculate checksum (simple XOR of all data bytes)
        checksum = command_type_byte
        for b in self.data:
            checksum ^= b
        
        # Assemble the packet
        header = struct.pack(">HHH", version_type_shdr_apid, sequence_fields, packet_length)
        secondary_header = struct.pack(">BB", command_type_byte, checksum)
        
        return header + secondary_header + self.data

class SDRTransmitter:
    """Interface for SDR transmission hardware"""
    
    def __init__(self, 
                 center_freq: float = 437.0e6,  # Default UHF frequency
                 sample_rate: float = 2e6,
                 tx_gain: float = 70.0,
                 device_args: str = ""):
        """
        Initialize SDR transmitter
        
        Args:
            center_freq: Center frequency in Hz
            sample_rate: Sample rate in samples/sec
            tx_gain: Transmit gain in dB
            device_args: Additional device arguments
        """
        self.center_freq = center_freq
        self.sample_rate = sample_rate
        self.tx_gain = tx_gain
        self.device_args = device_args
        self.sdr = None
        
    def setup(self) -> None:
        """Set up the SDR transmitter"""
        if not has_soapysdr:
            raise UplinkException("SoapySDR library not available")
        
        try:
            # Create SDR device instance
            self.sdr = SoapySDR.Device(self.device_args)
            
            # Configure transmitter
            self.sdr.setSampleRate(SOAPY_SDR_TX, 0, self.sample_rate)
            self.sdr.setFrequency(SOAPY_SDR_TX, 0, self.center_freq)
            self.sdr.setGain(SOAPY_SDR_TX, 0, self.tx_gain)
            
            logger.info(f"SDR initialized: {self.sdr.getHardwareInfo()}")
            logger.info(f"Frequency: {self.center_freq/1e6} MHz, Sample Rate: {self.sample_rate/1e6} MSps")
            
        except Exception as e:
            raise UplinkException(f"Failed to initialize SDR: {str(e)}")
    
    def close(self) -> None:
        """Close SDR device"""
        if self.sdr:
            self.sdr = None
            logger.info("SDR device closed")
    
    def transmit(self, samples: np.ndarray) -> None:
        """
        Transmit complex samples through SDR
        
        Args:
            samples: Complex baseband samples to transmit (numpy array)
        """
        if self.sdr is None:
            raise UplinkException("SDR not initialized. Call setup() first.")
        
        try:
            # Setup stream
            tx_stream = self.sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
            self.sdr.activateStream(tx_stream)
            
            # Transmit
            self.sdr.writeStream(tx_stream, [samples], len(samples))
            
            # Cleanup stream
            self.sdr.deactivateStream(tx_stream)
            self.sdr.closeStream(tx_stream)
            
            logger.info(f"Transmitted {len(samples)} samples")
            
        except Exception as e:
            raise UplinkException(f"Transmission failed: {str(e)}")

class SignalModulator:
    """Signal modulation for satellite uplink"""
    
    def __init__(self, sample_rate: float = 2e6):
        """
        Initialize modulator
        
        Args:
            sample_rate: Sample rate in samples/sec
        """
        self.sample_rate = sample_rate
    
    def bpsk_modulate(self, data: bytes, symbol_rate: float = 9600) -> np.ndarray:
        """
        Modulate data using Binary Phase Shift Keying (BPSK)
        
        Args:
            data: Bytes to modulate
            symbol_rate: Symbol rate in symbols/sec
        
        Returns:
            Complex baseband samples for transmission
        """
        # Convert bytes to bits
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        
        # NRZ encoding (0 -> -1, 1 -> 1)
        symbols = 2 * bits - 1
        
        # Upsample to sample_rate
        samples_per_symbol = int(self.sample_rate / symbol_rate)
        upsampled = np.repeat(symbols, samples_per_symbol)
        
        # Convert to complex baseband (real signal on I channel)
        complex_baseband = upsampled.astype(np.complex64)
        
        return complex_baseband
    
    def gmsk_modulate(self, data: bytes, symbol_rate: float = 9600, bt: float = 0.5) -> np.ndarray:
        """
        Modulate data using Gaussian Minimum Shift Keying (GMSK)
        
        Args:
            data: Bytes to modulate
            symbol_rate: Symbol rate in symbols/sec
            bt: Bandwidth-time product for Gaussian filter
        
        Returns:
            Complex baseband samples for transmission
        """
        # Convert bytes to bits
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        
        # NRZ encoding (0 -> -1, 1 -> 1)
        symbols = 2 * bits - 1
        
        # Upsample to sample_rate
        samples_per_symbol = int(self.sample_rate / symbol_rate)
        upsampled = np.repeat(symbols, samples_per_symbol)
        
        # For this example, creating a phase array and converting to complex
        phase = np.cumsum(upsampled) * np.pi/2 / samples_per_symbol
        complex_baseband = np.exp(1j * phase).astype(np.complex64)
        
        return complex_baseband

class SatelliteUplink:
    """Main class for satellite uplink operations"""
    
    def __init__(self, 
                 frequency: float = 437.0e6,
                 sample_rate: float = 2e6,
                 tx_gain: float = 70.0,
                 device_args: str = ""):
        """
        Initialize satellite uplink
        
        Args:
            frequency: Transmit frequency in Hz
            sample_rate: Sample rate in samples/sec
            tx_gain: Transmit gain in dB
            device_args: SDR device arguments
        """
        self.transmitter = SDRTransmitter(
            center_freq=frequency,
            sample_rate=sample_rate,
            tx_gain=tx_gain,
            device_args=device_args
        )
        self.modulator = SignalModulator(sample_rate=sample_rate)
        self.sequence_counter = 0
    
    def start(self) -> None:
        """Start the uplink system"""
        self.transmitter.setup()
        logger.info("Satellite uplink system started")
    
    def stop(self) -> None:
        """Stop the uplink system"""
        self.transmitter.close()
        logger.info("Satellite uplink system stopped")
    
    def send_command(self, 
                     spacecraft_id: Union[int, SpacecraftID], 
                     command_type: Union[int, CommandType], 
                     data: bytes = b'',
                     modulation: str = 'bpsk') -> None:
        """
        Send command to a satellite
        
        Args:
            spacecraft_id: Target spacecraft ID
            command_type: Command type
            data: Command data payload
            modulation: Modulation scheme ('bpsk' or 'gmsk')
        """
        # Convert enum to int if necessary
        if isinstance(spacecraft_id, SpacecraftID):
            spacecraft_id = spacecraft_id.value
        
        if isinstance(command_type, CommandType):
            command_type = command_type.value
        
        # Create CCSDS packet
        packet = CCSDSPacket(spacecraft_id, command_type, data)
        packet.set_sequence_count(self.sequence_counter)
        self.sequence_counter = (self.sequence_counter + 1) % 0x4000  # 14-bit counter
        
        # Build packet bytes
        packet_bytes = packet.build()
        
        # Modulate the packet
        if modulation.lower() == 'bpsk':
            samples = self.modulator.bpsk_modulate(packet_bytes)
        elif modulation.lower() == 'gmsk':
            samples = self.modulator.gmsk_modulate(packet_bytes)
        else:
            raise UplinkException(f"Unsupported modulation: {modulation}")
        
        # Transmit
        self.transmitter.transmit(samples)
        
        logger.info(f"Command sent to spacecraft {spacecraft_id}: "
                   f"type={command_type}, data_length={len(data)}")

    def ping(self, spacecraft_id: Union[int, SpacecraftID]) -> None:
        """Send ping command to satellite"""
        self.send_command(spacecraft_id, CommandType.PING)
    
    def reboot(self, spacecraft_id: Union[int, SpacecraftID]) -> None:
        """Send reboot command to satellite"""
        self.send_command(spacecraft_id, CommandType.REBOOT)
    
    def set_mode(self, 
                spacecraft_id: Union[int, SpacecraftID], 
                mode: int) -> None:
        """Set satellite operating mode"""
        mode_data = struct.pack(">B", mode)
        self.send_command(spacecraft_id, CommandType.SET_MODE, mode_data)
    
    def request_telemetry(self, spacecraft_id: Union[int, SpacecraftID]) -> None:
        """Request telemetry data from satellite"""
        self.send_command(spacecraft_id, CommandType.GET_TELEMETRY)

# Example usage
if __name__ == "__main__":
    # Example: Create uplink and send a command
    uplink = SatelliteUplink(frequency=437.5e6)
    
    try:
        uplink.start()
        
        # Send a ping command to spacecraft A
        uplink.ping(SpacecraftID.SPACECRAFT_A)
        
        # Custom command with data
        custom_data = b'\x01\x02\x03\x04'
        uplink.send_command(
            SpacecraftID.SPACECRAFT_A, 
            0x42,  # Custom command code
            custom_data
        )
        
    except Exception as e:
        logger.error(f"Error in uplink: {str(e)}")
        
    finally:
        uplink.stop()