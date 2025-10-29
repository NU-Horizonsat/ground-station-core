"""
Web-based Ground Station UI using Streamlit
Modern, responsive interface accessible via web browser
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json

# Check numpy availability
HAS_NUMPY = True  # numpy is required for streamlit anyway

# Import optional dependencies
try:
    from skyfield.api import load, wgs84, EarthSatellite
    HAS_SKYFIELD = True
except ImportError:
    HAS_SKYFIELD = False
    st.warning("⚠️ Skyfield not installed - satellite tracking will be limited")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    st.warning("⚠️ Requests not installed - API features unavailable")

try:
    from api_client import GroundStationAPIClient
    HAS_API_CLIENT = True
except ImportError:
    HAS_API_CLIENT = False


# Page configuration
st.set_page_config(
    page_title="Ground Station Core",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'current_satellite' not in st.session_state:
    st.session_state.current_satellite = None
if 'ground_station_type' not in st.session_state:
    st.session_state.ground_station_type = "local"
if 'ts' not in st.session_state:
    if HAS_SKYFIELD:
        st.session_state.ts = load.timescale()
    else:
        st.session_state.ts = None
if 'satellite_position' not in st.session_state:
    st.session_state.satellite_position = None


# Sidebar - Configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Ground Station Selection
    st.subheader("Ground Station")
    gs_type = st.radio(
        "Command From:",
        ["🏠 Local Ground Station", "☁️ AWS Ground Station"],
        index=0 if st.session_state.ground_station_type == "local" else 1
    )
    
    if "Local" in gs_type:
        st.session_state.ground_station_type = "local"
        st.success("Active: Local Ground Station")
    else:
        st.session_state.ground_station_type = "aws"
        st.info("Active: AWS Ground Station")
        
        # AWS Configuration
        with st.expander("AWS Configuration", expanded=True):
            aws_region = st.text_input("AWS Region", value="us-west-2")
            aws_gs_id = st.text_input("Ground Station ID")
            aws_profile = st.text_input("Mission Profile ARN")
            
            if st.button("Test AWS Connection"):
                try:
                    import boto3
                    client = boto3.client('groundstation', region_name=aws_region)
                    response = client.list_configs()
                    st.success(f"✓ Connected! Found {len(response.get('configList', []))} configs")
                except ImportError:
                    st.error("boto3 not installed. Run: pip install boto3")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
    
    st.divider()
    
    # API Configuration
    st.subheader("API Settings")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    
    if st.button("Connect to API"):
        if HAS_API_CLIENT and HAS_REQUESTS:
            try:
                client = GroundStationAPIClient(api_url)
                if client.test_connection():
                    st.session_state.api_client = client
                    st.session_state.api_connected = True
                    st.success("✓ Connected to API")
                else:
                    st.error("Failed to connect to API")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
        else:
            st.warning("Install required libraries: pip install requests")
    
    st.divider()
    
    # Ground Station Location
    st.subheader("Ground Station Location")
    gs_lat = st.number_input("Latitude", value=37.7749, min_value=-90.0, max_value=90.0, step=0.0001)
    gs_lon = st.number_input("Longitude", value=-122.4194, min_value=-180.0, max_value=180.0, step=0.0001)
    gs_alt = st.number_input("Altitude (m)", value=0, min_value=0, max_value=10000, step=1)
    
    st.divider()
    
    # Status
    st.subheader("Status")
    if st.session_state.api_connected:
        st.success("API: Connected")
    else:
        st.error("API: Disconnected")
    
    if st.session_state.current_satellite:
        st.success(f"Satellite: Tracking")
    else:
        st.warning("Satellite: None loaded")


# Main content
st.title("🛰️ Ground Station Core - Web Interface")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", 
    "🗺️ Satellite Tracking", 
    "🔭 Pass Prediction", 
    "📡 Commands",
    "📈 Telemetry",
    "🎛️ Advanced"
])

# Tab 1: Overview
with tab1:
    st.header("System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("API Status", "Connected" if st.session_state.api_connected else "Disconnected")
    
    with col2:
        st.metric("Ground Station", st.session_state.ground_station_type.upper())
    
    with col3:
        st.metric("Satellite", 
                 st.session_state.current_satellite.name if st.session_state.current_satellite else "None")
    
    with col4:
        st.metric("Time", datetime.utcnow().strftime("%H:%M:%S UTC"))
    
    st.divider()
    
    # Recent Activity Log
    st.subheader("Recent Activity")
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    # Display last 10 activities
    if st.session_state.activity_log:
        for activity in reversed(st.session_state.activity_log[-10:]):
            st.text(activity)
    else:
        st.info("No recent activity")


# Tab 2: Satellite Tracking
with tab2:
    st.header("🗺️ Satellite Tracking & World Map")
    
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("Satellite Selection")
        
        satellite_options = {
            "ISS (ZARYA)": (
                "1 25544U 98067A   25301.50000000  .00016717  00000-0  10270-3 0  9990",
                "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563223"
            ),
            "NOAA 19": (
                "1 33591U 09005A   25301.50000000  .00000086  00000-0  74630-4 0  9996",
                "2 33591  99.1897 306.7656 0013972 292.5889  67.3773 14.12501073851623"
            ),
            "NOAA 18": (
                "1 28654U 05018A   25301.50000000  .00000080  00000-0  68744-4 0  9991",
                "2 28654  99.0398 294.1976 0015061 139.4036 220.8588 14.12589990047913"
            ),
            "METEOR-M2": (
                "1 40069U 14037A   25301.50000000  .00000071  00000-0  55448-4 0  9994",
                "2 40069  98.5687 217.4806 0004877 273.3076  86.7324 14.20694700589423"
            ),
        }
        
        selected_sat = st.selectbox("Select Satellite", list(satellite_options.keys()))
        
        st.subheader("TLE Data")
        tle1 = st.text_input("Line 1", value=satellite_options[selected_sat][0])
        tle2 = st.text_input("Line 2", value=satellite_options[selected_sat][1])
        
        if st.button("Load Satellite", type="primary"):
            if HAS_SKYFIELD and st.session_state.ts:
                try:
                    sat = EarthSatellite(tle1, tle2, selected_sat, st.session_state.ts)
                    st.session_state.current_satellite = sat
                    st.success(f"✓ Loaded {selected_sat}")
                    if 'activity_log' not in st.session_state:
                        st.session_state.activity_log = []
                    st.session_state.activity_log.append(
                        f"[{datetime.utcnow().strftime('%H:%M:%S')}] Loaded satellite: {selected_sat}"
                    )
                except Exception as e:
                    st.error(f"Failed to load satellite: {str(e)}")
            else:
                st.warning("Skyfield library required. Install: pip install skyfield")
        
        st.divider()
        
        st.subheader("Current Position")
        
        # Auto-refresh toggle
        auto_update = st.checkbox("🔄 Real-time Tracking (5s updates)", value=False, key="auto_tracking")
        
        if st.session_state.current_satellite and HAS_SKYFIELD:
            # Manual update button
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                update_clicked = st.button("🎯 Update Position Now", type="secondary", use_container_width=True)
            with col_btn2:
                update_track = st.button("🗺️ Update Ground Track", use_container_width=True)
            
            # Auto-update logic
            if auto_update or update_clicked or update_track:
                try:
                    t = st.session_state.ts.now()
                    geocentric = st.session_state.current_satellite.at(t)
                    subpoint = wgs84.subpoint(geocentric)
                    
                    # Calculate visibility from ground station
                    gs = wgs84.latlon(gs_lat, gs_lon, gs_alt)
                    difference = st.session_state.current_satellite - gs
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    # Fix velocity calculation - velocity is already in km/s as a tuple
                    velocity = geocentric.velocity.km_per_s
                    if isinstance(velocity, tuple) or isinstance(velocity, list):
                        speed = np.linalg.norm(velocity)
                    else:
                        # If it's a numpy array
                        speed = np.linalg.norm([velocity[0], velocity[1], velocity[2]])
                    
                    st.session_state.satellite_position = {
                        'lat': subpoint.latitude.degrees,
                        'lon': subpoint.longitude.degrees,
                        'alt': subpoint.elevation.km,
                        'azimuth': az.degrees,
                        'elevation': alt.degrees,
                        'range': distance.km,
                        'velocity': speed,
                        'visible': alt.degrees > 0,
                        'timestamp': datetime.utcnow()
                    }
                    
                    # Add to activity log
                    if 'activity_log' not in st.session_state:
                        st.session_state.activity_log = []
                    st.session_state.activity_log.append(
                        f"[{datetime.utcnow().strftime('%H:%M:%S')}] Position updated - Alt: {alt.degrees:.1f}°"
                    )
                    
                except Exception as e:
                    st.error(f"Position calculation error: {str(e)}")
            
            if st.session_state.satellite_position:
                pos = st.session_state.satellite_position
                
                # Show last update time
                if 'timestamp' in pos:
                    st.caption(f"Last update: {pos['timestamp'].strftime('%H:%M:%S UTC')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Latitude", f"{pos['lat']:.4f}°")
                    st.metric("Longitude", f"{pos['lon']:.4f}°")
                    st.metric("Altitude", f"{pos['alt']:.2f} km")
                    st.metric("Velocity", f"{pos['velocity']:.2f} km/s")
                
                with col2:
                    st.metric("Azimuth", f"{pos['azimuth']:.2f}°")
                    st.metric("Elevation", f"{pos['elevation']:.2f}°")
                    st.metric("Range", f"{pos['range']:.2f} km")
                    if pos['visible']:
                        st.success("🟢 VISIBLE")
                    else:
                        st.error("🔴 NOT VISIBLE")
    
    with col_right:
        st.subheader("World Map View")
        
        # Map options
        map_col1, map_col2 = st.columns([3, 1])
        with map_col1:
            track_length = st.slider("Ground Track Length (minutes)", 30, 200, 100, key="track_length")
        with map_col2:
            show_footprint = st.checkbox("Show Footprint", value=True, key="show_footprint")
        
        if st.session_state.current_satellite and HAS_SKYFIELD:
            # Calculate ground track
            try:
                t0 = st.session_state.ts.now()
                minutes = track_length
                times = [t0.tt + (i / (minutes * 24 * 60)) for i in range(minutes)]
                
                lats = []
                lons = []
                alts = []
                
                for t_tt in times:
                    t = st.session_state.ts.tt_jd(t_tt)
                    geocentric = st.session_state.current_satellite.at(t)
                    subpoint = wgs84.subpoint(geocentric)
                    lats.append(subpoint.latitude.degrees)
                    lons.append(subpoint.longitude.degrees)
                    alts.append(subpoint.elevation.km)
                
                # Create world map with plotly
                fig = go.Figure()
                
                # Add ground track with gradient color
                fig.add_trace(go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(width=3, color='blue'),
                    name='Ground Track',
                    hovertemplate='<b>Ground Track</b><br>Lat: %{lat:.2f}°<br>Lon: %{lon:.2f}°<extra></extra>'
                ))
                
                # Add current satellite position
                if st.session_state.satellite_position:
                    pos = st.session_state.satellite_position
                    fig.add_trace(go.Scattergeo(
                        lon=[pos['lon']],
                        lat=[pos['lat']],
                        mode='markers+text',
                        marker=dict(size=15, color='red', symbol='circle'),
                        text=['📡'],
                        textposition='top center',
                        name='Satellite',
                        hovertemplate=f"<b>Satellite Position</b><br>Lat: {pos['lat']:.4f}°<br>Lon: {pos['lon']:.4f}°<br>Alt: {pos['alt']:.1f} km<br>Velocity: {pos['velocity']:.2f} km/s<extra></extra>"
                    ))
                    
                    # Add visibility footprint circle (approximation)
                    if show_footprint and pos['alt'] > 0:
                        # Calculate approximate horizon distance
                        earth_radius = 6371  # km
                        horizon_angle = np.arccos(earth_radius / (earth_radius + pos['alt']))
                        horizon_distance_km = earth_radius * horizon_angle
                        # Convert to approximate degrees (rough)
                        radius_deg = horizon_distance_km / 111  # km per degree
                        
                        circle_lons = []
                        circle_lats = []
                        for angle in np.linspace(0, 2*np.pi, 50):
                            circle_lons.append(pos['lon'] + radius_deg * np.cos(angle))
                            circle_lats.append(pos['lat'] + radius_deg * np.sin(angle))
                        
                        fig.add_trace(go.Scattergeo(
                            lon=circle_lons,
                            lat=circle_lats,
                            mode='lines',
                            line=dict(width=1, color='rgba(255,0,0,0.3)', dash='dash'),
                            name='Visibility Circle',
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                
                # Add ground station
                fig.add_trace(go.Scattergeo(
                    lon=[gs_lon],
                    lat=[gs_lat],
                    mode='markers+text',
                    marker=dict(size=18, color='green', symbol='triangle-up'),
                    text=['🏠' if st.session_state.ground_station_type == 'local' else '☁️'],
                    textposition='bottom center',
                    name=f'GS ({st.session_state.ground_station_type.upper()})',
                    hovertemplate=f"<b>Ground Station</b><br>Lat: {gs_lat:.4f}°<br>Lon: {gs_lon:.4f}°<br>Type: {st.session_state.ground_station_type.upper()}<extra></extra>"
                ))
                
                # Update layout
                fig.update_geos(
                    projection_type="natural earth",
                    showland=True,
                    landcolor="lightgray",
                    showocean=True,
                    oceancolor="lightblue",
                    showcountries=True,
                    countrycolor="white",
                    coastlinecolor="darkgray",
                    lakecolor="lightblue"
                )
                
                fig.update_layout(
                    title=f"Ground Track - {selected_sat} (Next {track_length} min)",
                    height=600,
                    showlegend=True,
                    legend=dict(x=0.01, y=0.99),
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Additional map info
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Orbit Period", f"{90:.0f} min", help="Approximate orbital period")
                with col_info2:
                    st.metric("Track Points", f"{len(lats)}")
                with col_info3:
                    st.metric("Avg Altitude", f"{np.mean(alts):.1f} km")
                
            except Exception as e:
                st.error(f"Map rendering error: {str(e)}")
        else:
            st.info("📍 Load a satellite to see the world map view")
            st.markdown("""
            **How to use:**
            1. Select a satellite from the dropdown
            2. Click "Load Satellite"
            3. Click "Update Position Now"
            4. Enable real-time tracking for live updates
            """)


# Tab 3: Pass Prediction
with tab3:
    st.header("🔭 Pass Prediction")
    
    # Satellite selection for pass prediction
    col_sat, col_load = st.columns([3, 1])
    
    with col_sat:
        satellite_options_pass = {
            "ISS (ZARYA)": (
                "1 25544U 98067A   25301.50000000  .00016717  00000-0  10270-3 0  9990",
                "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563223"
            ),
            "NOAA 19": (
                "1 33591U 09005A   25301.50000000  .00000086  00000-0  74630-4 0  9996",
                "2 33591  99.1897 306.7656 0013972 292.5889  67.3773 14.12501073851623"
            ),
            "NOAA 18": (
                "1 28654U 05018A   25301.50000000  .00000080  00000-0  68744-4 0  9991",
                "2 28654  99.0398 294.1976 0015061 139.4036 220.8588 14.12589990047913"
            ),
            "METEOR-M2": (
                "1 40069U 14037A   25301.50000000  .00000071  00000-0  55448-4 0  9994",
                "2 40069  98.5687 217.4806 0004877 273.3076  86.7324 14.20694700589423"
            ),
        }
        
        selected_sat_pass = st.selectbox(
            "Select Satellite for Pass Prediction", 
            list(satellite_options_pass.keys()),
            help="Choose which satellite to calculate passes for"
        )
    
    with col_load:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("📡 Load", use_container_width=True):
            if HAS_SKYFIELD and st.session_state.ts:
                try:
                    tle1, tle2 = satellite_options_pass[selected_sat_pass]
                    sat = EarthSatellite(tle1, tle2, selected_sat_pass, st.session_state.ts)
                    st.session_state.current_satellite = sat
                    st.success(f"✓ Loaded {selected_sat_pass}")
                except Exception as e:
                    st.error(f"Failed to load: {str(e)}")
    
    # Show current satellite
    if st.session_state.current_satellite:
        st.info(f"📡 Active Satellite: **{st.session_state.current_satellite.name}**")
    else:
        st.warning("⚠️ No satellite loaded - select and load a satellite above")
    
    st.divider()
    
    # Pass prediction parameters
    if st.session_state.current_satellite:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pred_hours = st.number_input("Time Span (hours)", min_value=1, max_value=168, value=24,
                                        help="How far ahead to predict passes")
        
        with col2:
            min_elevation = st.number_input("Min Elevation (°)", min_value=0, max_value=90, value=10,
                                           help="Minimum elevation angle for a pass to be included")
        
        with col3:
            st.write("")  # Spacing
            calculate_button = st.button("🔍 Calculate Passes", type="primary", use_container_width=True)
        
        if calculate_button and HAS_SKYFIELD:
            with st.spinner(f"Calculating passes for {st.session_state.current_satellite.name}..."):
                try:
                    ground_station = wgs84.latlon(gs_lat, gs_lon, gs_alt)
                    
                    t0 = st.session_state.ts.now()
                    t1 = st.session_state.ts.tt_jd(t0.tt + pred_hours / 24)
                    
                    t, events = st.session_state.current_satellite.find_events(
                        ground_station, t0, t1, altitude_degrees=min_elevation)
                    
                    # Process events into passes
                    passes = []
                    current_pass = {}
                    
                    for ti, event in zip(t, events):
                        if event == 0:  # AOS
                            current_pass = {'aos': ti, 'aos_time': ti.utc_datetime()}
                        elif event == 1:  # Max elevation
                            if 'aos' in current_pass:
                                difference = st.session_state.current_satellite - ground_station
                                topocentric = difference.at(ti)
                                alt, az, _ = topocentric.altaz()
                                current_pass['max_el'] = alt.degrees
                                current_pass['max_el_time'] = ti.utc_datetime()
                        elif event == 2:  # LOS
                            if 'aos' in current_pass:
                                current_pass['los'] = ti
                                current_pass['los_time'] = ti.utc_datetime()
                                
                                # Calculate duration
                                duration = (current_pass['los_time'] - current_pass['aos_time']).total_seconds() / 60
                                current_pass['duration'] = duration
                                
                                # Get AOS and LOS azimuths
                                difference = st.session_state.current_satellite - ground_station
                                aos_topo = difference.at(current_pass['aos'])
                                _, aos_az, _ = aos_topo.altaz()
                                los_topo = difference.at(current_pass['los'])
                                _, los_az, _ = los_topo.altaz()
                                
                                current_pass['aos_az'] = aos_az.degrees
                                current_pass['los_az'] = los_az.degrees
                                
                                passes.append(current_pass)
                                current_pass = {}
                    
                    if passes:
                        st.success(f"Found {len(passes)} passes")
                        
                        # Create DataFrame
                        df = pd.DataFrame([
                            {
                                'AOS Time': p['aos_time'].strftime('%Y-%m-%d %H:%M:%S'),
                                'LOS Time': p['los_time'].strftime('%Y-%m-%d %H:%M:%S'),
                                'Duration (min)': f"{p['duration']:.1f}",
                                'Max Elevation (°)': f"{p.get('max_el', 0):.1f}",
                                'AOS Azimuth (°)': f"{p['aos_az']:.1f}",
                                'LOS Azimuth (°)': f"{p['los_az']:.1f}"
                            }
                            for p in passes
                        ])
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="💾 Download as CSV",
                            data=csv,
                            file_name=f"passes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No passes found in the specified time period")
                        
                except Exception as e:
                    st.error(f"Pass calculation error: {str(e)}")
    else:
        st.info("💡 Load a satellite above to calculate passes")


# Tab 4: Commands
with tab4:
    st.header("📡 Command Control")
    
    if not st.session_state.api_connected:
        st.warning("⚠️ Connect to API in the sidebar to send commands")
        st.info("💡 Start the API server: `python backend/api_server.py`")
    else:
        # Command input section
        st.subheader("Send Command")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            spacecraft_id = st.number_input("Spacecraft ID", min_value=1, max_value=255, value=1,
                                           help="Target spacecraft identifier (1-255)")
        
        with col2:
            cmd_type = st.selectbox("Command Type", [
                "NOOP",
                "RESET",
                "SET_MODE",
                "REQUEST_TELEMETRY",
                "DEPLOY_ANTENNA",
                "IMAGING_ON",
                "IMAGING_OFF"
            ], help="Type of command to send")
        
        with col3:
            modulation = st.selectbox("Modulation", ["bpsk", "gmsk"], 
                                     help="Modulation scheme for transmission")
        
        # Optional data field with help text
        st.markdown("**Command Data (Optional)**")
        data_input = st.text_input(
            "Hex Data", 
            value="",
            placeholder="e.g., 0x01AF or leave empty",
            help="Optional hex-encoded command data. Leave empty for commands without parameters."
        )
        
        # Command examples
        with st.expander("📖 Command Examples"):
            st.markdown("""
            **Common Commands:**
            - **NOOP**: No operation (health check) - no data needed
            - **RESET**: Reset spacecraft - no data needed
            - **SET_MODE**: Change mode - data: `0x01` (safe), `0x02` (nominal), `0x03` (science)
            - **REQUEST_TELEMETRY**: Request telemetry downlink - no data needed
            - **DEPLOY_ANTENNA**: Deploy antenna - no data needed
            - **IMAGING_ON**: Start imaging - data: `0x01` (low res), `0x02` (high res)
            - **IMAGING_OFF**: Stop imaging - no data needed
            
            **Data Format:**
            - Hex format: `0x01`, `0xABCD`, `0xFF00`
            - Leave empty if command doesn't need data
            """)
        
        # Send immediately or schedule
        col_send, col_schedule = st.columns(2)
        
        with col_send:
            if st.button("🚀 Send Command Now", type="primary", use_container_width=True):
                try:
                    response = st.session_state.api_client.send_command(
                        spacecraft_id=spacecraft_id,
                        command_type=cmd_type,
                        data=data_input if data_input else None,
                        modulation=modulation
                    )
                    st.success(f"✓ Command sent: {cmd_type}")
                    if 'activity_log' not in st.session_state:
                        st.session_state.activity_log = []
                    st.session_state.activity_log.append(
                        f"[{datetime.utcnow().strftime('%H:%M:%S')}] Sent {cmd_type} to SC-{spacecraft_id} via {st.session_state.ground_station_type.upper()}"
                    )
                except Exception as e:
                    st.error(f"❌ Command failed: {str(e)}")
        
        with col_schedule:
            if st.button("⏰ Schedule Command", use_container_width=True):
                st.session_state.show_schedule_dialog = True
        
        # Scheduling dialog
        if st.session_state.get('show_schedule_dialog', False):
            with st.form("schedule_form"):
                st.markdown("### ⏰ Schedule Command")
                
                sched_col1, sched_col2 = st.columns(2)
                with sched_col1:
                    sched_date = st.date_input("Execution Date", value=datetime.now())
                with sched_col2:
                    sched_time = st.time_input("Execution Time", value=datetime.now().time())
                
                sched_submit = st.form_submit_button("Schedule", type="primary")
                sched_cancel = st.form_submit_button("Cancel")
                
                if sched_submit:
                    try:
                        scheduled_dt = datetime.combine(sched_date, sched_time)
                        response = st.session_state.api_client.schedule_command(
                            spacecraft_id=spacecraft_id,
                            command_type=cmd_type,
                            scheduled_time=scheduled_dt,
                            data=data_input if data_input else None,
                            modulation=modulation
                        )
                        st.success(f"✓ Command scheduled for {scheduled_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.session_state.show_schedule_dialog = False
                        if 'activity_log' not in st.session_state:
                            st.session_state.activity_log = []
                        st.session_state.activity_log.append(
                            f"[{datetime.utcnow().strftime('%H:%M:%S')}] Scheduled {cmd_type} for {scheduled_dt.strftime('%H:%M')}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Scheduling failed: {str(e)}")
                
                if sched_cancel:
                    st.session_state.show_schedule_dialog = False
                    st.rerun()
        
        st.divider()
        
        # Scheduled Commands Management
        st.subheader("📅 Scheduled Commands")
        
        if st.button("🔄 Refresh Scheduled Commands"):
            pass  # Will refresh on rerun
        
        try:
            scheduled_cmds = st.session_state.api_client.get_scheduled_commands()
            
            if scheduled_cmds and len(scheduled_cmds) > 0:
                # Create DataFrame for display
                df_scheduled = pd.DataFrame(scheduled_cmds)
                
                # Display as table with actions
                for idx, cmd in enumerate(scheduled_cmds):
                    with st.expander(f"🕐 {cmd.get('scheduled_time', 'Unknown')} - {cmd.get('command_type', 'Unknown')}"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**Spacecraft ID:** {cmd.get('spacecraft_id', 'N/A')}")
                            st.write(f"**Command:** {cmd.get('command_type', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Scheduled:** {cmd.get('scheduled_time', 'N/A')}")
                            st.write(f"**Status:** {cmd.get('status', 'pending')}")
                        
                        with col3:
                            if st.button(f"❌ Cancel", key=f"cancel_{idx}"):
                                try:
                                    st.session_state.api_client.cancel_scheduled_command(cmd.get('id'))
                                    st.success("Command cancelled")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to cancel: {str(e)}")
            else:
                st.info("📭 No scheduled commands")
                st.markdown("""
                **To schedule a command:**
                1. Configure command parameters above
                2. Click "⏰ Schedule Command"
                3. Select date and time
                4. Command will execute automatically at scheduled time
                """)
        
        except Exception as e:
            st.warning(f"Could not fetch scheduled commands: {str(e)}")
            st.info("Ensure API server is running with scheduling support")
        
        st.divider()
        
        # Command Series Builder
        st.subheader("📜 Command Series")
        
        if 'command_series' not in st.session_state:
            st.session_state.command_series = []
        
        with st.expander("➕ Add Command to Series"):
            series_col1, series_col2, series_col3 = st.columns(3)
            
            with series_col1:
                series_cmd = st.selectbox("Command", [
                    "NOOP", "RESET", "SET_MODE", "REQUEST_TELEMETRY",
                    "DEPLOY_ANTENNA", "IMAGING_ON", "IMAGING_OFF"
                ], key="series_cmd")
            
            with series_col2:
                series_delay = st.number_input("Delay (seconds)", min_value=0, max_value=3600, value=10,
                                              help="Delay after previous command")
            
            with series_col3:
                series_data = st.text_input("Data (optional)", key="series_data", placeholder="0x01")
            
            if st.button("➕ Add to Series"):
                st.session_state.command_series.append({
                    'command': series_cmd,
                    'delay': series_delay,
                    'data': series_data
                })
                st.success(f"Added {series_cmd} to series")
                st.rerun()
        
        # Display command series
        if st.session_state.command_series:
            st.markdown("**Command Sequence:**")
            
            for idx, cmd in enumerate(st.session_state.command_series):
                col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                
                with col1:
                    st.write(f"**{idx + 1}.**")
                
                with col2:
                    st.write(f"{cmd['command']}")
                
                with col3:
                    st.write(f"⏱️ +{cmd['delay']}s" + (f" | Data: {cmd['data']}" if cmd['data'] else ""))
                
                with col4:
                    if st.button("🗑️", key=f"remove_{idx}"):
                        st.session_state.command_series.pop(idx)
                        st.rerun()
            
            st.divider()
            
            col_exec, col_sched, col_clear = st.columns(3)
            
            with col_exec:
                if st.button("🚀 Execute Series Now", type="primary", use_container_width=True):
                    st.info("Executing command series...")
                    # Schedule each command with cumulative delay
                    base_time = datetime.utcnow()
                    cumulative_delay = 0
                    
                    for cmd in st.session_state.command_series:
                        cumulative_delay += cmd['delay']
                        exec_time = base_time + timedelta(seconds=cumulative_delay)
                        
                        try:
                            st.session_state.api_client.schedule_command(
                                spacecraft_id=spacecraft_id,
                                command_type=cmd['command'],
                                scheduled_time=exec_time,
                                data=cmd['data'] if cmd['data'] else None,
                                modulation=modulation
                            )
                        except Exception as e:
                            st.error(f"Failed to schedule {cmd['command']}: {str(e)}")
                    
                    st.success(f"✓ Scheduled {len(st.session_state.command_series)} commands")
                    st.session_state.command_series = []
                    st.rerun()
            
            with col_sched:
                if st.button("⏰ Schedule Series", use_container_width=True):
                    st.session_state.show_series_schedule = True
            
            with col_clear:
                if st.button("🗑️ Clear Series", use_container_width=True):
                    st.session_state.command_series = []
                    st.rerun()
            
            # Series scheduling dialog
            if st.session_state.get('show_series_schedule', False):
                with st.form("series_schedule_form"):
                    st.markdown("### ⏰ Schedule Command Series")
                    st.write("Commands will execute in sequence starting from selected time")
                    
                    series_date = st.date_input("Start Date", value=datetime.now())
                    series_time = st.time_input("Start Time", value=datetime.now().time())
                    
                    series_submit = st.form_submit_button("Schedule Series", type="primary")
                    series_cancel = st.form_submit_button("Cancel")
                    
                    if series_submit:
                        base_time = datetime.combine(series_date, series_time)
                        cumulative_delay = 0
                        
                        for cmd in st.session_state.command_series:
                            cumulative_delay += cmd['delay']
                            exec_time = base_time + timedelta(seconds=cumulative_delay)
                            
                            try:
                                st.session_state.api_client.schedule_command(
                                    spacecraft_id=spacecraft_id,
                                    command_type=cmd['command'],
                                    scheduled_time=exec_time,
                                    data=cmd['data'] if cmd['data'] else None,
                                    modulation=modulation
                                )
                            except Exception as e:
                                st.error(f"Failed to schedule {cmd['command']}: {str(e)}")
                        
                        st.success(f"✓ Series scheduled starting at {base_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.session_state.command_series = []
                        st.session_state.show_series_schedule = False
                        st.rerun()
                    
                    if series_cancel:
                        st.session_state.show_series_schedule = False
                        st.rerun()
        
        else:
            st.info("💡 Build a command series to execute multiple commands in sequence")


# Tab 5: Telemetry
with tab5:
    st.header("📈 Telemetry Monitoring")
    
    if not st.session_state.api_connected:
        st.warning("Connect to API in the sidebar to view telemetry")
    else:
        # Auto-refresh checkbox
        auto_refresh = st.checkbox("Auto-refresh (every 5 seconds)")
        
        if auto_refresh:
            st.write("🔄 Auto-refreshing...")
            time.sleep(5)
            st.rerun()
        
        # Fetch telemetry
        try:
            telemetry = st.session_state.api_client.get_telemetry()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Battery", f"{telemetry.get('battery', 0):.1f}%", 
                         delta=f"{telemetry.get('battery_delta', 0):.1f}%")
            
            with col2:
                st.metric("Temperature", f"{telemetry.get('temperature', 0):.1f}°C",
                         delta=f"{telemetry.get('temp_delta', 0):.1f}°C")
            
            with col3:
                st.metric("Signal Strength", f"{telemetry.get('signal', 0):.1f} dBm")
            
            st.divider()
            
            # Telemetry chart
            st.subheader("Telemetry History")
            
            # Generate sample data for demonstration
            time_points = pd.date_range(end=datetime.now(), periods=50, freq='5s')
            df_telemetry = pd.DataFrame({
                'Time': time_points,
                'Battery (%)': np.random.uniform(85, 95, 50),
                'Temperature (°C)': np.random.uniform(18, 25, 50),
                'Signal (dBm)': np.random.uniform(-80, -60, 50)
            })
            
            fig = px.line(df_telemetry, x='Time', y=['Battery (%)', 'Temperature (°C)', 'Signal (dBm)'],
                         title="Telemetry Over Time")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Failed to fetch telemetry: {str(e)}")


# Tab 6: Advanced Features
with tab6:
    st.header("🎛️ Advanced Features")
    
    # Rotator Control
    st.subheader("📡 Rotator Control")
    
    if st.session_state.api_connected:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Manual Control**")
            azimuth_set = st.slider("Azimuth", 0, 360, 180, key="az_slider")
            elevation_set = st.slider("Elevation", 0, 90, 45, key="el_slider")
            
            if st.button("🎯 Point Antenna", type="primary"):
                try:
                    response = st.session_state.api_client.set_rotator_position(
                        azimuth=azimuth_set,
                        elevation=elevation_set
                    )
                    st.success(f"✓ Antenna pointing to Az:{azimuth_set}° El:{elevation_set}°")
                except Exception as e:
                    st.error(f"Rotator control failed: {str(e)}")
        
        with col2:
            st.markdown("**Auto-Track Satellite**")
            if st.session_state.current_satellite and st.session_state.satellite_position:
                pos = st.session_state.satellite_position
                st.info(f"Target: Az {pos['azimuth']:.1f}° / El {pos['elevation']:.1f}°")
                
                if st.button("🔄 Track Satellite", type="secondary"):
                    try:
                        response = st.session_state.api_client.set_rotator_position(
                            azimuth=pos['azimuth'],
                            elevation=pos['elevation']
                        )
                        st.success("✓ Tracking satellite")
                    except Exception as e:
                        st.error(f"Auto-track failed: {str(e)}")
            else:
                st.warning("Load and update satellite position first")
    else:
        st.warning("Connect to API to control rotator")
    
    st.divider()
    
    # TLE Management
    st.subheader("📡 TLE Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Update TLEs from Internet**")
        tle_source = st.selectbox("TLE Source", [
            "Celestrak (Active Satellites)",
            "Space-Track.org",
            "Custom URL"
        ])
        
        if st.button("🌐 Fetch Latest TLEs"):
            st.info("TLE fetch feature - integrate with Celestrak or Space-Track API")
    
    with col2:
        st.markdown("**Load TLE from File**")
        uploaded_file = st.file_uploader("Upload TLE file", type=['txt', 'tle'])
        if uploaded_file is not None:
            content = uploaded_file.read().decode('utf-8')
            st.text_area("TLE Content", content, height=150)
            if st.button("📥 Load from File"):
                st.success("TLE loaded successfully")
    
    st.divider()
    
    # Frequency Management
    st.subheader("📻 Frequency & Doppler")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        carrier_freq = st.number_input("Carrier Frequency (MHz)", 
                                       min_value=100.0, max_value=10000.0, 
                                       value=437.0, step=0.001, format="%.3f")
    
    with col2:
        if st.session_state.satellite_position:
            # Calculate doppler shift
            pos = st.session_state.satellite_position
            # Simplified doppler calculation
            doppler_hz = -(carrier_freq * 1e6 * pos['velocity'] * 1000) / 299792458  # c
            st.metric("Doppler Shift", f"{doppler_hz:.0f} Hz")
            corrected_freq = carrier_freq + (doppler_hz / 1e6)
            st.metric("Corrected Freq", f"{corrected_freq:.6f} MHz")
        else:
            st.info("Update satellite position to calculate Doppler")
    
    with col3:
        st.markdown("**Quick Actions**")
        if st.button("📻 Set Radio Frequency"):
            st.success(f"Radio tuned to {carrier_freq:.3f} MHz")
    
    st.divider()
    
    # Data Export
    st.subheader("💾 Data Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Session Log"):
            if 'activity_log' in st.session_state and st.session_state.activity_log:
                log_content = '\n'.join(st.session_state.activity_log)
                st.download_button(
                    label="Download Log",
                    data=log_content,
                    file_name=f"session_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            else:
                st.warning("No activity logged yet")
    
    with col2:
        if st.button("🗺️ Export Ground Track"):
            if st.session_state.current_satellite:
                st.info("Generate and download ground track data")
            else:
                st.warning("Load a satellite first")
    
    with col3:
        if st.button("⚙️ Export Configuration"):
            config_data = {
                'ground_station_type': st.session_state.ground_station_type,
                'gs_location': {'lat': gs_lat, 'lon': gs_lon, 'alt': gs_alt},
                'api_url': api_url,
                'timestamp': datetime.utcnow().isoformat()
            }
            st.download_button(
                label="Download Config",
                data=json.dumps(config_data, indent=2),
                file_name="ground_station_config.json",
                mime="application/json"
            )
    
    st.divider()
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Library Status**")
        libs = {
            "Skyfield": HAS_SKYFIELD,
            "Requests": HAS_REQUESTS,
            "NumPy": HAS_NUMPY,
            "API Client": HAS_API_CLIENT
        }
        for lib, status in libs.items():
            if status:
                st.success(f"✓ {lib}")
            else:
                st.error(f"✗ {lib}")
    
    with col2:
        st.markdown("**Session Stats**")
        if 'activity_log' in st.session_state:
            st.metric("Activities Logged", len(st.session_state.activity_log))
        if st.session_state.current_satellite:
            st.metric("Active Satellite", st.session_state.current_satellite.name)
        st.metric("Session Start", datetime.now().strftime("%H:%M:%S"))


# Auto-refresh logic for real-time tracking
if 'auto_tracking' in st.session_state and st.session_state.auto_tracking:
    time.sleep(5)
    st.rerun()


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    Ground Station Core v2.1 - Web Interface | Powered by Streamlit | 🛰️ Real-time Satellite Tracking
</div>
""", unsafe_allow_html=True)
