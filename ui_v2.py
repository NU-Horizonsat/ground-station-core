"""
Modernized Ground Station Core UI
Version 2.0 - With working satellite tracking, API integration, and proper error handling
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk as tkttk
import time
import threading
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Try importing optional dependencies with fallbacks
try:
    import ttkbootstrap as ttk
    from ttkbootstrap import Style
    from ttkbootstrap.constants import *
    HAS_TTKBOOTSTRAP = True
except ImportError:
    import tkinter.ttk as ttk
    HAS_TTKBOOTSTRAP = False
    # Define constants if ttkbootstrap not available
    PRIMARY = SUCCESS = INFO = WARNING = DANGER = DARK = "primary"

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from skyfield.api import load, wgs84, EarthSatellite
    from skyfield.timelib import Time
    HAS_SKYFIELD = True
except ImportError:
    HAS_SKYFIELD = False

# Try importing cartopy for world map
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Import our API client
try:
    from api_client import GroundStationAPIClient
    HAS_API_CLIENT = True
except ImportError:
    HAS_API_CLIENT = False
    
try:
    from config import get_config, init_config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class SatelliteGroundStationUI:
    """Main UI class for Ground Station Control"""
    
    def __init__(self, root):
        self.root = root
        
        # Initialize configuration
        if HAS_CONFIG:
            try:
                self.config = init_config()
                self.config_data = self.config.config
            except Exception as e:
                print(f"Warning: Could not load configuration: {e}")
                self.config = None
                self.config_data = None
        else:
            self.config = None
            self.config_data = None
        
        # Initialize API client
        if HAS_API_CLIENT:
            try:
                api_url = "http://localhost:8000"
                if self.config_data:
                    api_url = f"http://{self.config_data.api_host}:{self.config_data.api_port}"
                self.api_client = GroundStationAPIClient(api_url)
                self.api_connected = self.api_client.test_connection()
            except Exception as e:
                print(f"Warning: Could not connect to API: {e}")
                self.api_client = None
                self.api_connected = False
        else:
            self.api_client = None
            self.api_connected = False
        
        # Setup UI theme
        if HAS_TTKBOOTSTRAP:
            self.style = Style(theme="darkly")
        
        self.root.title("Ground Station Core v2.0")
        self.root.geometry("1400x900")
        
        # State variables
        self.connected = False
        self.telemetry_data = {"battery": [], "temperature": [], "signal": []}
        self.telemetry_times = []
        self.scheduled_commands = []
        self.realtime_tracking_active = False
        
        # Ground station selection (local vs AWS)
        self.ground_station_type = "local"  # "local" or "aws"
        self.aws_config = {
            "region": "us-west-2",
            "ground_station_id": "",
            "mission_profile_id": ""
        }
        
        # Satellite tracking
        self.current_satellite = None
        self.tle_line1 = ""
        self.tle_line2 = ""
        
        # Skyfield timescale (if available)
        if HAS_SKYFIELD:
            try:
                self.ts = load.timescale()
            except:
                self.ts = None
        else:
            self.ts = None
        
        # Create UI
        self.create_ui()
        
        # Start background tasks
        self.start_telemetry_updates()
        
        # Update status
        self.update_connection_status()
    
    def create_ui(self):
        """Create the main UI layout"""
        # Create menu bar
        self.create_menu_bar()
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_overview_tab()
        self.create_satellite_tracking_tab()
        self.create_pass_prediction_tab()
        self.create_command_tab()
        self.create_telemetry_tab()
        self.create_settings_tab()
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load TLE", command=self.load_tle_file)
        file_menu.add_command(label="Save Configuration", command=self.save_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Update TLE from Internet", command=self.update_tle_from_internet)
        tools_menu.add_command(label="Test API Connection", command=self.test_api_connection)
        tools_menu.add_command(label="Clear Telemetry Data", command=self.clear_telemetry)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_overview_tab(self):
        """Create overview/dashboard tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Overview")
        
        # Connection status
        status_frame = ttk.LabelFrame(frame, text="System Status", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Status grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.status_labels = {}
        statuses = [
            ("API Server:", "❓ Unknown"),
            ("SDR Status:", "❓ Unknown"),
            ("Rotator:", "❓ Unknown"),
            ("Satellite:", "❓ No satellite selected"),
        ]
        
        for i, (label_text, default_value) in enumerate(statuses):
            row, col = divmod(i, 2)
            ttk.Label(status_grid, text=label_text, font=("Arial", 10, "bold")).grid(
                row=row, column=col*2, padx=10, pady=5, sticky=tk.E)
            
            value_label = ttk.Label(status_grid, text=default_value)
            value_label.grid(row=row, column=col*2+1, padx=10, pady=5, sticky=tk.W)
            self.status_labels[label_text] = value_label
        
        # Quick actions
        actions_frame = ttk.LabelFrame(frame, text="Quick Actions", bootstyle=PRIMARY if HAS_TTKBOOTSTRAP else "")
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="🔄 Update Satellite Position", 
                  command=self.quick_update_position, bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📡 Calculate Next Pass", 
                  command=self.quick_calculate_pass, bootstyle=INFO if HAS_TTKBOOTSTRAP else "").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 View API Docs", 
                  command=self.open_api_docs, bootstyle=WARNING if HAS_TTKBOOTSTRAP else "").pack(side=tk.LEFT, padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(frame, text="Activity Log", bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_message("Ground Station Core v2.0 initialized")
        if self.api_connected:
            self.log_message("✓ Connected to API server")
        else:
            self.log_message("⚠ API server not available - some features disabled")
    
    def create_satellite_tracking_tab(self):
        """Create satellite tracking tab with working TLE calculations"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🛰️ Satellite Tracking")
        
        # Split into left controls and right visualization
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Controls
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Satellite selection
        sat_frame = ttk.LabelFrame(left_frame, text="Satellite Selection", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        sat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(sat_frame, text="Select Satellite:").pack(anchor=tk.W, padx=5, pady=5)
        
        self.satellite_combo = ttk.Combobox(sat_frame, values=[
            "ISS (ZARYA)",
            "NOAA 19",
            "NOAA 18",
            "METEOR-M2",
            "Custom TLE"
        ], state="readonly")
        self.satellite_combo.pack(fill=tk.X, padx=5, pady=5)
        self.satellite_combo.current(0)
        self.satellite_combo.bind("<<ComboboxSelected>>", self.on_satellite_selected)
        
        # TLE input
        tle_frame = ttk.LabelFrame(left_frame, text="TLE Data", bootstyle=WARNING if HAS_TTKBOOTSTRAP else "")
        tle_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(tle_frame, text="Line 1:").pack(anchor=tk.W, padx=5, pady=2)
        self.tle1_entry = ttk.Entry(tle_frame, width=70)
        self.tle1_entry.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(tle_frame, text="Line 2:").pack(anchor=tk.W, padx=5, pady=2)
        self.tle2_entry = ttk.Entry(tle_frame, width=70)
        self.tle2_entry.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(tle_frame, text="Load TLE", command=self.load_tle, 
                  bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "").pack(padx=5, pady=5)
        
        # Ground station location
        gs_frame = ttk.LabelFrame(left_frame, text="Ground Station", bootstyle=PRIMARY if HAS_TTKBOOTSTRAP else "")
        gs_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Load from config if available
        default_lat = self.config_data.latitude if self.config_data else 37.7749
        default_lon = self.config_data.longitude if self.config_data else -122.4194
        default_alt = self.config_data.altitude if self.config_data else 0
        
        ttk.Label(gs_frame, text="Latitude:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.gs_lat = ttk.Entry(gs_frame, width=15)
        self.gs_lat.insert(0, str(default_lat))
        self.gs_lat.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(gs_frame, text="Longitude:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.gs_lon = ttk.Entry(gs_frame, width=15)
        self.gs_lon.insert(0, str(default_lon))
        self.gs_lon.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(gs_frame, text="Altitude (m):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.gs_alt = ttk.Entry(gs_frame, width=15)
        self.gs_alt.insert(0, str(default_alt))
        self.gs_alt.grid(row=2, column=1, padx=5, pady=5)
        
        # Tracking controls
        track_frame = ttk.LabelFrame(left_frame, text="Tracking", bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "")
        track_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(track_frame, text="🎯 Update Position Now", command=self.update_satellite_position,
                  bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "").pack(fill=tk.X, padx=5, pady=5)
        
        self.realtime_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(track_frame, text="Real-time Tracking (update every 5s)", 
                       variable=self.realtime_var, command=self.toggle_realtime_tracking).pack(padx=5, pady=5)
        
        # Right panel - Position display
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # Current position
        pos_frame = ttk.LabelFrame(right_frame, text="Current Position", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.position_labels = {}
        position_data = [
            ("Latitude:", "---"),
            ("Longitude:", "---"),
            ("Altitude:", "---"),
            ("Azimuth:", "---"),
            ("Elevation:", "---"),
            ("Range:", "---"),
            ("Velocity:", "---"),
            ("Visibility:", "---"),
        ]
        
        for i, (label, default) in enumerate(position_data):
            row, col = divmod(i, 2)
            ttk.Label(pos_frame, text=label, font=("Arial", 9, "bold")).grid(
                row=row, column=col*2, padx=5, pady=3, sticky=tk.E)
            val_label = ttk.Label(pos_frame, text=default)
            val_label.grid(row=row, column=col*2+1, padx=5, pady=3, sticky=tk.W)
            self.position_labels[label] = val_label
        
        # Visualization area
        if HAS_MATPLOTLIB:
            viz_frame = ttk.LabelFrame(right_frame, text="World Map View", bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "")
            viz_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create figure with projection
            if HAS_CARTOPY:
                self.fig = Figure(figsize=(10, 6), dpi=100)
                self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
                self.ax.set_global()
                self.ax.add_feature(cfeature.LAND, facecolor='lightgray')
                self.ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
                self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
                self.ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.5)
                self.ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5)
                self.ax.set_title("Satellite Ground Track - World Map")
            else:
                # Fallback to simple plot
                self.fig = Figure(figsize=(10, 6), dpi=100)
                self.ax = self.fig.add_subplot(111)
                self.ax.set_xlabel("Longitude")
                self.ax.set_ylabel("Latitude")
                self.ax.set_title("Satellite Ground Track")
                self.ax.grid(True)
                self.ax.set_xlim(-180, 180)
                self.ax.set_ylim(-90, 90)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add toolbar frame
            toolbar_frame = ttk.Frame(viz_frame)
            toolbar_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(toolbar_frame, text="💡 Install cartopy for enhanced world map: pip install cartopy",
                     font=("Arial", 8)).pack(side=tk.LEFT) if not HAS_CARTOPY else None
        else:
            ttk.Label(right_frame, text="Install matplotlib for visualization:\npip install matplotlib",
                     font=("Arial", 12)).pack(expand=True)
        
        # Load default satellite
        self.on_satellite_selected(None)
    
    def create_pass_prediction_tab(self):
        """Create pass prediction tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔭 Pass Prediction")
        
        # Controls
        controls = ttk.LabelFrame(frame, text="Prediction Parameters", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        ctrl_grid = ttk.Frame(controls)
        ctrl_grid.pack(padx=10, pady=10)
        
        ttk.Label(ctrl_grid, text="Time Span (hours):").grid(row=0, column=0, padx=5, pady=5)
        self.pred_hours = ttk.Spinbox(ctrl_grid, from_=1, to=168, width=10)
        self.pred_hours.set(24)
        self.pred_hours.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(ctrl_grid, text="Min Elevation (°):").grid(row=0, column=2, padx=5, pady=5)
        self.min_elevation = ttk.Spinbox(ctrl_grid, from_=0, to=90, width=10)
        self.min_elevation.set(10)
        self.min_elevation.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(ctrl_grid, text="🔍 Calculate Passes", command=self.calculate_passes,
                  bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "").grid(row=0, column=4, padx=10, pady=5)
        
        # Results table
        results_frame = ttk.LabelFrame(frame, text="Upcoming Passes", bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ("aos", "los", "duration", "max_el", "aos_az", "los_az")
        self.pass_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        self.pass_tree.heading("aos", text="AOS Time")
        self.pass_tree.heading("los", text="LOS Time")
        self.pass_tree.heading("duration", text="Duration (min)")
        self.pass_tree.heading("max_el", text="Max Elevation")
        self.pass_tree.heading("aos_az", text="AOS Azimuth")
        self.pass_tree.heading("los_az", text="LOS Azimuth")
        
        self.pass_tree.column("aos", width=150)
        self.pass_tree.column("los", width=150)
        self.pass_tree.column("duration", width=100)
        self.pass_tree.column("max_el", width=100)
        self.pass_tree.column("aos_az", width=100)
        self.pass_tree.column("los_az", width=100)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.pass_tree.yview)
        self.pass_tree.configure(yscroll=scrollbar.set)
        
        self.pass_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Export button
        ttk.Button(frame, text="💾 Export to CSV", command=self.export_passes,
                  bootstyle=PRIMARY if HAS_TTKBOOTSTRAP else "").pack(pady=5)
    
    def create_command_tab(self):
        """Create command control tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📡 Commands")
        
        # Command selection
        cmd_frame = ttk.LabelFrame(frame, text="Send Command", bootstyle=WARNING if HAS_TTKBOOTSTRAP else "")
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)
        
        grid = ttk.Frame(cmd_frame)
        grid.pack(padx=10, pady=10)
        
        ttk.Label(grid, text="Spacecraft ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.spacecraft_id = ttk.Spinbox(grid, from_=1, to=255, width=10)
        self.spacecraft_id.set(1)
        self.spacecraft_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(grid, text="Command Type:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.command_type = ttk.Combobox(grid, values=[
            "0 - Ping",
            "1 - Reboot",
            "2 - Set Mode",
            "3 - Get Telemetry",
            "Custom"
        ], state="readonly", width=25)
        self.command_type.current(0)
        self.command_type.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(grid, text="Data (hex):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.command_data = ttk.Entry(grid, width=30)
        self.command_data.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(grid, text="Modulation:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.modulation = ttk.Combobox(grid, values=["bpsk", "gmsk"], state="readonly", width=10)
        self.modulation.current(0)
        self.modulation.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(grid, text="📤 Send Command", command=self.send_command,
                  bootstyle=DANGER if HAS_TTKBOOTSTRAP else "").grid(row=4, column=0, columnspan=2, pady=10)
        
        # Command history
        history_frame = ttk.LabelFrame(frame, text="Command History", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.command_history = scrolledtext.ScrolledText(history_frame, height=15, wrap=tk.WORD)
        self.command_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_telemetry_tab(self):
        """Create telemetry monitoring tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Telemetry")
        
        if HAS_MATPLOTLIB:
            # Create plots
            self.telemetry_fig = Figure(figsize=(12, 8), dpi=100)
            
            self.bat_ax = self.telemetry_fig.add_subplot(311)
            self.bat_ax.set_ylabel("Battery (V)")
            self.bat_ax.grid(True)
            
            self.temp_ax = self.telemetry_fig.add_subplot(312)
            self.temp_ax.set_ylabel("Temperature (°C)")
            self.temp_ax.grid(True)
            
            self.sig_ax = self.telemetry_fig.add_subplot(313)
            self.sig_ax.set_ylabel("Signal (dB)")
            self.sig_ax.set_xlabel("Time")
            self.sig_ax.grid(True)
            
            self.telemetry_fig.tight_layout()
            
            self.telemetry_canvas = FigureCanvasTkAgg(self.telemetry_fig, master=frame)
            self.telemetry_canvas.draw()
            self.telemetry_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(frame, text="Install matplotlib for telemetry plots:\npip install matplotlib",
                     font=("Arial", 12)).pack(expand=True)
    
    def create_settings_tab(self):
        """Create settings tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Settings")
        
        # Ground Station Type Selection
        gs_type_frame = ttk.LabelFrame(frame, text="Ground Station Selection", bootstyle=WARNING if HAS_TTKBOOTSTRAP else "")
        gs_type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        gs_grid = ttk.Frame(gs_type_frame)
        gs_grid.pack(padx=10, pady=10)
        
        ttk.Label(gs_grid, text="Command From:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.gs_type_var = tk.StringVar(value="local")
        ttk.Radiobutton(gs_grid, text="🏠 Local Ground Station", variable=self.gs_type_var, 
                       value="local", command=self.on_gs_type_changed).grid(row=0, column=1, padx=10, pady=5)
        ttk.Radiobutton(gs_grid, text="☁️ AWS Ground Station", variable=self.gs_type_var, 
                       value="aws", command=self.on_gs_type_changed).grid(row=0, column=2, padx=10, pady=5)
        
        self.gs_status_label = ttk.Label(gs_grid, text="Active: Local Ground Station", foreground="green")
        self.gs_status_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        # AWS Configuration (initially hidden)
        self.aws_config_frame = ttk.LabelFrame(frame, text="AWS Ground Station Configuration", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        
        aws_grid = ttk.Frame(self.aws_config_frame)
        aws_grid.pack(padx=10, pady=10)
        
        ttk.Label(aws_grid, text="AWS Region:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.aws_region_entry = ttk.Entry(aws_grid, width=30)
        self.aws_region_entry.insert(0, "us-west-2")
        self.aws_region_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(aws_grid, text="Ground Station ID:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.aws_gs_id_entry = ttk.Entry(aws_grid, width=30)
        self.aws_gs_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(aws_grid, text="Mission Profile ARN:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.aws_profile_entry = ttk.Entry(aws_grid, width=50)
        self.aws_profile_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Button(aws_grid, text="Test AWS Connection", command=self.test_aws_connection,
                  bootstyle=PRIMARY if HAS_TTKBOOTSTRAP else "").grid(row=3, column=0, columnspan=2, pady=10)
        
        # API settings
        api_frame = ttk.LabelFrame(frame, text="API Configuration", bootstyle=INFO if HAS_TTKBOOTSTRAP else "")
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        api_grid = ttk.Frame(api_frame)
        api_grid.pack(padx=10, pady=10)
        
        ttk.Label(api_grid, text="API URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.api_url_entry = ttk.Entry(api_grid, width=40)
        self.api_url_entry.insert(0, "http://localhost:8000")
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(api_grid, text="Test Connection", command=self.test_api_connection,
                  bootstyle=SUCCESS if HAS_TTKBOOTSTRAP else "").grid(row=0, column=2, padx=5, pady=5)
        
        # About
        about_frame = ttk.LabelFrame(frame, text="About", bootstyle=PRIMARY if HAS_TTKBOOTSTRAP else "")
        about_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        about_text = """
        Ground Station Core v2.0
        
        Modern satellite tracking and communication system
        
        Features:
        • Real-time satellite tracking with TLE data
        • Pass prediction and scheduling
        • Command uplink via SDR
        • Telemetry monitoring
        • REST API integration
        
        Required Libraries:
        ✓ Skyfield - Satellite position calculations
        ✓ Matplotlib - Data visualization  
        ✓ Requests - API communication
        ✓ NumPy - Numerical operations
        
        Optional:
        • SoapySDR - SDR hardware support
        • InfluxDB - Time series database
        • Grafana - Monitoring dashboards
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT)
        about_label.pack(padx=20, pady=20)
    
    # Satellite tracking methods
    
    def on_satellite_selected(self, event):
        """Handle satellite selection"""
        sat_name = self.satellite_combo.get()
        
        # Load default TLEs
        tle_data = {
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
        
        if sat_name in tle_data:
            line1, line2 = tle_data[sat_name]
            self.tle1_entry.delete(0, tk.END)
            self.tle1_entry.insert(0, line1)
            self.tle2_entry.delete(0, tk.END)
            self.tle2_entry.insert(0, line2)
            
            self.load_tle()
            self.log_message(f"Loaded TLE for {sat_name}")
    
    def load_tle(self):
        """Load TLE data and create satellite object"""
        line1 = self.tle1_entry.get().strip()
        line2 = self.tle2_entry.get().strip()
        
        if not line1 or not line2:
            messagebox.showerror("Error", "Please enter TLE data")
            return
        
        if not HAS_SKYFIELD:
            messagebox.showwarning("Skyfield Not Available", 
                                  "Skyfield library is required for satellite tracking.\n"
                                  "Install it with: pip install skyfield")
            return
        
        try:
            sat_name = self.satellite_combo.get()
            self.current_satellite = EarthSatellite(line1, line2, sat_name, self.ts)
            self.tle_line1 = line1
            self.tle_line2 = line2
            
            self.log_message(f"✓ Loaded satellite: {sat_name}")
            self.update_satellite_position()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load TLE: {str(e)}")
            self.log_message(f"✗ Failed to load TLE: {str(e)}")
    
    def update_satellite_position(self):
        """Calculate and display current satellite position"""
        if not self.current_satellite:
            messagebox.showinfo("Info", "Please load a satellite first")
            return
        
        if not HAS_SKYFIELD:
            return
        
        try:
            # Get ground station location
            lat = float(self.gs_lat.get())
            lon = float(self.gs_lon.get())
            alt = float(self.gs_alt.get())
            
            ground_station = wgs84.latlon(lat, lon, alt)
            
            # Get current time
            t = self.ts.now()
            
            # Calculate satellite position
            geocentric = self.current_satellite.at(t)
            subpoint = wgs84.subpoint(geocentric)
            
            # Calculate topocentric position (from ground station)
            difference = self.current_satellite - ground_station
            topocentric = difference.at(t)
            alt_deg, az_deg, distance = topocentric.altaz()
            
            # Update position labels
            self.position_labels["Latitude:"].config(
                text=f"{subpoint.latitude.degrees:.4f}°")
            self.position_labels["Longitude:"].config(
                text=f"{subpoint.longitude.degrees:.4f}°")
            self.position_labels["Altitude:"].config(
                text=f"{subpoint.elevation.km:.2f} km")
            self.position_labels["Azimuth:"].config(
                text=f"{az_deg.degrees:.2f}°")
            self.position_labels["Elevation:"].config(
                text=f"{alt_deg.degrees:.2f}°")
            self.position_labels["Range:"].config(
                text=f"{distance.km:.2f} km")
            
            # Calculate velocity
            velocity = self.current_satellite.at(t).velocity.km_per_s
            speed = (velocity[0]**2 + velocity[1]**2 + velocity[2]**2)**0.5
            self.position_labels["Velocity:"].config(
                text=f"{speed:.2f} km/s")
            
            # Visibility
            visibility = "Visible" if alt_deg.degrees > 0 else "Below horizon"
            self.position_labels["Visibility:"].config(text=visibility)
            
            # Update ground track visualization
            if HAS_MATPLOTLIB and HAS_NUMPY:
                self.update_ground_track()
            
            self.status_bar.config(text=f"Updated position at {datetime.now().strftime('%H:%M:%S')}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid ground station coordinates: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate position: {str(e)}")
            self.log_message(f"✗ Position calculation error: {str(e)}")
    
    def update_ground_track(self):
        """Update ground track visualization with world map"""
        if not self.current_satellite or not HAS_MATPLOTLIB or not HAS_NUMPY:
            return
        
        try:
            # Calculate ground track for next orbit (~90 minutes)
            t0 = self.ts.now()
            minutes = 100
            times = [t0.tt + (i / (minutes * 24 * 60)) for i in range(minutes)]
            
            lats = []
            lons = []
            
            for t_tt in times:
                t = self.ts.tt_jd(t_tt)
                geocentric = self.current_satellite.at(t)
                subpoint = wgs84.subpoint(geocentric)
                lats.append(subpoint.latitude.degrees)
                lons.append(subpoint.longitude.degrees)
            
            # Clear and redraw
            self.ax.clear()
            
            if HAS_CARTOPY:
                # Redraw map features
                self.ax.set_global()
                self.ax.add_feature(cfeature.LAND, facecolor='lightgray')
                self.ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
                self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
                self.ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.5)
                self.ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5)
                self.ax.set_title(f"Ground Track - {self.satellite_combo.get()}")
                
                # Plot ground track on map projection
                self.ax.plot(lons, lats, 'b-', linewidth=2, label="Ground Track",
                           transform=ccrs.PlateCarree())
                
                # Plot current position
                self.ax.plot(lons[0], lats[0], 'ro', markersize=10, label="Satellite",
                           transform=ccrs.PlateCarree(), zorder=10)
                
                # Plot ground station
                gs_lat = float(self.gs_lat.get())
                gs_lon = float(self.gs_lon.get())
                self.ax.plot(gs_lon, gs_lat, 'g^', markersize=15, label=f"GS ({self.ground_station_type.upper()})",
                           transform=ccrs.PlateCarree(), zorder=10)
                
                # Add visibility circle (simple approximation)
                # Draw horizon circle at satellite position
                circle_lons = [lons[0] + 15*np.cos(theta) for theta in np.linspace(0, 2*np.pi, 50)]
                circle_lats = [lats[0] + 15*np.sin(theta) for theta in np.linspace(0, 2*np.pi, 50)]
                self.ax.plot(circle_lons, circle_lats, 'r--', alpha=0.3, linewidth=1,
                           transform=ccrs.PlateCarree())
            else:
                # Simple 2D plot
                self.ax.set_xlabel("Longitude")
                self.ax.set_ylabel("Latitude")
                self.ax.set_title(f"Ground Track - {self.satellite_combo.get()}")
                self.ax.grid(True, alpha=0.3)
                self.ax.set_xlim(-180, 180)
                self.ax.set_ylim(-90, 90)
                
                # Plot ground track
                self.ax.plot(lons, lats, 'b-', linewidth=2, label="Ground Track")
                
                # Plot current position
                self.ax.plot(lons[0], lats[0], 'ro', markersize=10, label="Satellite")
                
                # Plot ground station
                gs_lat = float(self.gs_lat.get())
                gs_lon = float(self.gs_lon.get())
                self.ax.plot(gs_lon, gs_lat, 'g^', markersize=12, label=f"GS ({self.ground_station_type.upper()})")
            
            self.ax.legend(loc='upper right')
            self.canvas.draw()
            
        except Exception as e:
            self.log_message(f"Ground track update error: {str(e)}")
    
    def toggle_realtime_tracking(self):
        """Toggle real-time tracking"""
        if self.realtime_var.get():
            self.realtime_tracking_active = True
            self.start_realtime_tracking()
            self.log_message("Started real-time tracking")
        else:
            self.realtime_tracking_active = False
            self.log_message("Stopped real-time tracking")
    
    def start_realtime_tracking(self):
        """Start real-time tracking thread"""
        def tracking_loop():
            while self.realtime_tracking_active and self.realtime_var.get():
                try:
                    self.root.after(0, self.update_satellite_position)
                    time.sleep(5)  # Update every 5 seconds
                except:
                    break
        
        threading.Thread(target=tracking_loop, daemon=True).start()
    
    def calculate_passes(self):
        """Calculate upcoming satellite passes"""
        if not self.current_satellite:
            messagebox.showinfo("Info", "Please load a satellite first")
            return
        
        if not HAS_SKYFIELD:
            messagebox.showwarning("Skyfield Required", 
                                  "Install skyfield: pip install skyfield")
            return
        
        try:
            # Clear existing items
            for item in self.pass_tree.get_children():
                self.pass_tree.delete(item)
            
            # Get parameters
            hours = int(self.pred_hours.get())
            min_el = float(self.min_elevation.get())
            
            lat = float(self.gs_lat.get())
            lon = float(self.gs_lon.get())
            alt = float(self.gs_alt.get())
            
            ground_station = wgs84.latlon(lat, lon, alt)
            
            # Calculate passes
            t0 = self.ts.now()
            t1 = self.ts.tt_jd(t0.tt + hours / 24)
            
            t, events = self.current_satellite.find_events(
                ground_station, t0, t1, altitude_degrees=min_el)
            
            # Process events into passes
            passes = []
            current_pass = {}
            
            for ti, event in zip(t, events):
                if event == 0:  # AOS
                    current_pass = {'aos': ti}
                elif event == 1:  # Max elevation
                    current_pass['max'] = ti
                elif event == 2:  # LOS
                    current_pass['los'] = ti
                    passes.append(current_pass)
                    current_pass = {}
            
            # Display passes
            for pass_data in passes:
                if 'aos' not in pass_data or 'los' not in pass_data:
                    continue
                
                aos_time = pass_data['aos'].utc_datetime()
                los_time = pass_data['los'].utc_datetime()
                duration = (los_time - aos_time).total_seconds() / 60
                
                # Calculate azimuth at AOS and LOS
                difference = self.current_satellite - ground_station
                
                topo_aos = difference.at(pass_data['aos'])
                alt_aos, az_aos, _ = topo_aos.altaz()
                
                topo_los = difference.at(pass_data['los'])
                alt_los, az_los, _ = topo_los.altaz()
                
                # Max elevation
                if 'max' in pass_data:
                    topo_max = difference.at(pass_data['max'])
                    alt_max, _, _ = topo_max.altaz()
                    max_el = alt_max.degrees
                else:
                    max_el = min_el
                
                self.pass_tree.insert("", tk.END, values=(
                    aos_time.strftime("%Y-%m-%d %H:%M:%S"),
                    los_time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{duration:.1f}",
                    f"{max_el:.1f}°",
                    f"{az_aos.degrees:.1f}°",
                    f"{az_los.degrees:.1f}°"
                ))
            
            self.log_message(f"✓ Found {len(passes)} passes in next {hours} hours")
            self.status_bar.config(text=f"Found {len(passes)} passes")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate passes: {str(e)}")
            self.log_message(f"✗ Pass calculation error: {str(e)}")
    
    # Command methods
    
    def send_command(self):
        """Send command via API"""
        if not self.api_client or not self.api_connected:
            messagebox.showwarning("API Not Available", 
                                  "API server is not connected. Start the API server first.")
            return
        
        try:
            spacecraft_id = int(self.spacecraft_id.get())
            
            # Parse command type
            cmd_str = self.command_type.get()
            if cmd_str.startswith("Custom"):
                command_type = int(messagebox.askstring("Custom Command", "Enter command type code:") or "0")
            else:
                command_type = int(cmd_str.split("-")[0].strip())
            
            data = self.command_data.get().strip() or None
            modulation = self.modulation.get()
            
            # Send via API
            response = self.api_client.send_command(
                spacecraft_id=spacecraft_id,
                command_type=command_type,
                data=data,
                modulation=modulation
            )
            
            if response:
                msg = f"✓ Command sent: ID={spacecraft_id}, Type={command_type}"
                self.log_message(msg)
                self.command_history.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
                self.command_history.see(tk.END)
                messagebox.showinfo("Success", "Command sent successfully!")
            else:
                self.log_message("✗ Failed to send command")
                messagebox.showerror("Error", "Failed to send command")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {str(e)}")
            self.log_message(f"✗ Command error: {str(e)}")
    
    # Telemetry methods
    
    def start_telemetry_updates(self):
        """Start telemetry update thread"""
        def telemetry_loop():
            while True:
                try:
                    # Simulate telemetry (in real app, get from API)
                    import random
                    self.telemetry_data["battery"].append(random.uniform(11.5, 12.5))
                    self.telemetry_data["temperature"].append(random.uniform(15, 25))
                    self.telemetry_data["signal"].append(random.uniform(-100, -80))
                    self.telemetry_times.append(datetime.now())
                    
                    # Keep only last 100 points
                    for key in self.telemetry_data:
                        if len(self.telemetry_data[key]) > 100:
                            self.telemetry_data[key] = self.telemetry_data[key][-100:]
                    if len(self.telemetry_times) > 100:
                        self.telemetry_times = self.telemetry_times[-100:]
                    
                    # Update plots
                    self.root.after(0, self.update_telemetry_plots)
                    
                    time.sleep(2)
                except:
                    time.sleep(5)
        
        threading.Thread(target=telemetry_loop, daemon=True).start()
    
    def update_telemetry_plots(self):
        """Update telemetry plots"""
        if not HAS_MATPLOTLIB or not hasattr(self, 'telemetry_fig'):
            return
        
        try:
            # Clear plots
            self.bat_ax.clear()
            self.temp_ax.clear()
            self.sig_ax.clear()
            
            # Plot data
            if self.telemetry_times:
                times = [(t - self.telemetry_times[0]).total_seconds() for t in self.telemetry_times]
                
                self.bat_ax.plot(times, self.telemetry_data["battery"], 'b-')
                self.bat_ax.set_ylabel("Battery (V)")
                self.bat_ax.grid(True)
                
                self.temp_ax.plot(times, self.telemetry_data["temperature"], 'r-')
                self.temp_ax.set_ylabel("Temperature (°C)")
                self.temp_ax.grid(True)
                
                self.sig_ax.plot(times, self.telemetry_data["signal"], 'g-')
                self.sig_ax.set_ylabel("Signal (dB)")
                self.sig_ax.set_xlabel("Time (s)")
                self.sig_ax.grid(True)
            
            self.telemetry_canvas.draw()
        except:
            pass
    
    # Utility methods
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_connection_status(self):
        """Update connection status displays"""
        if self.api_connected:
            self.status_labels["API Server:"].config(text="✓ Connected")
        else:
            self.status_labels["API Server:"].config(text="✗ Not connected")
        
        # Check SDR status via API
        if self.api_client and self.api_connected:
            try:
                status = self.api_client.get_status()
                if status:
                    self.status_labels["SDR Status:"].config(
                        text="✓ Available" if status.get("sdr_connected") else "✗ Not available")
                    self.status_labels["Rotator:"].config(
                        text="✓ Connected" if status.get("rotator_connected") else "✗ Not connected")
            except:
                pass
        
        # Update satellite status
        if self.current_satellite:
            self.status_labels["Satellite:"].config(text=f"✓ {self.satellite_combo.get()}")
        else:
            self.status_labels["Satellite:"].config(text="❓ No satellite loaded")
    
    def test_api_connection(self):
        """Test API connection"""
        if not HAS_REQUESTS or not HAS_API_CLIENT:
            messagebox.showwarning("Libraries Missing", 
                                  "Install required libraries:\npip install requests")
            return
        
        try:
            api_url = self.api_url_entry.get()
            client = GroundStationAPIClient(api_url)
            
            if client.test_connection():
                self.api_client = client
                self.api_connected = True
                messagebox.showinfo("Success", f"Connected to API at {api_url}")
                self.log_message(f"✓ Connected to API: {api_url}")
                self.update_connection_status()
            else:
                self.api_connected = False
                messagebox.showerror("Error", f"Failed to connect to API at {api_url}")
                self.log_message(f"✗ Failed to connect to API: {api_url}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def on_gs_type_changed(self):
        """Handle ground station type change"""
        new_type = self.gs_type_var.get()
        self.ground_station_type = new_type
        
        if new_type == "aws":
            self.aws_config_frame.pack(fill=tk.X, padx=10, pady=10)
            self.gs_status_label.config(text="Active: AWS Ground Station", foreground="blue")
            self.log_message("🌐 Switched to AWS Ground Station")
        else:
            self.aws_config_frame.pack_forget()
            self.gs_status_label.config(text="Active: Local Ground Station", foreground="green")
            self.log_message("🏠 Switched to Local Ground Station")
        
        # Update ground track display
        if hasattr(self, 'current_satellite') and self.current_satellite:
            self.update_ground_track()
    
    def test_aws_connection(self):
        """Test AWS Ground Station connection"""
        try:
            # Check if boto3 is available
            import boto3
            
            region = self.aws_region_entry.get()
            gs_id = self.aws_gs_id_entry.get()
            
            if not region or not gs_id:
                messagebox.showwarning("Missing Configuration", 
                                      "Please enter AWS region and Ground Station ID")
                return
            
            # Try to create client
            client = boto3.client('groundstation', region_name=region)
            
            # Test connection by listing configs (or getting GS details)
            try:
                response = client.list_configs()
                messagebox.showinfo("AWS Connection", 
                                   f"✓ Successfully connected to AWS Ground Station in {region}\n"
                                   f"Found {len(response.get('configList', []))} configurations")
                self.log_message(f"✓ Connected to AWS Ground Station: {region}")
                
                # Store AWS config
                self.aws_config = {
                    "region": region,
                    "ground_station_id": gs_id,
                    "mission_profile_id": self.aws_profile_entry.get()
                }
            except Exception as e:
                messagebox.showerror("AWS Error", 
                                    f"Failed to connect to AWS Ground Station:\n{str(e)}\n\n"
                                    f"Check your AWS credentials and permissions.")
                self.log_message(f"✗ AWS connection failed: {str(e)}")
                
        except ImportError:
            messagebox.showwarning("Boto3 Not Installed", 
                                  "AWS Ground Station integration requires boto3.\n\n"
                                  "Install with: pip install boto3")
            self.log_message("✗ boto3 not installed - AWS features unavailable")
    
    def load_tle_file(self):
        """Load TLE from file"""
        filename = filedialog.askopenfilename(
            title="Select TLE File",
            filetypes=[("TLE files", "*.tle *.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    if len(lines) >= 2:
                        # Assume last two lines are TLE
                        self.tle1_entry.delete(0, tk.END)
                        self.tle1_entry.insert(0, lines[-2])
                        self.tle2_entry.delete(0, tk.END)
                        self.tle2_entry.insert(0, lines[-1])
                        self.load_tle()
                    else:
                        messagebox.showerror("Error", "Invalid TLE file format")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load TLE file: {str(e)}")
    
    def update_tle_from_internet(self):
        """Update TLE from internet sources"""
        if not HAS_REQUESTS:
            messagebox.showwarning("Requests Library Missing", 
                                  "Install requests library:\npip install requests")
            return
        
        messagebox.showinfo("TLE Update", 
                           "This feature would download TLE data from Celestrak or Space-Track.\n"
                           "Implement according to your preferred TLE source.")
    
    def save_configuration(self):
        """Save current configuration"""
        messagebox.showinfo("Save Configuration", 
                           "Configuration save feature - implement as needed")
    
    def export_passes(self):
        """Export pass predictions to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("AOS Time,LOS Time,Duration (min),Max Elevation,AOS Azimuth,LOS Azimuth\n")
                    for item in self.pass_tree.get_children():
                        values = self.pass_tree.item(item)['values']
                        f.write(','.join(str(v) for v in values) + '\n')
                
                messagebox.showinfo("Success", f"Passes exported to {filename}")
                self.log_message(f"✓ Exported passes to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def clear_telemetry(self):
        """Clear telemetry data"""
        self.telemetry_data = {"battery": [], "temperature": [], "signal": []}
        self.telemetry_times = []
        self.log_message("Telemetry data cleared")
    
    def quick_update_position(self):
        """Quick action: update satellite position"""
        if self.current_satellite:
            self.update_satellite_position()
        else:
            messagebox.showinfo("Info", "Please load a satellite first in the Satellite Tracking tab")
    
    def quick_calculate_pass(self):
        """Quick action: calculate next pass"""
        self.notebook.select(2)  # Switch to pass prediction tab
        if self.current_satellite:
            self.calculate_passes()
        else:
            messagebox.showinfo("Info", "Please load a satellite first")
    
    def open_api_docs(self):
        """Open API documentation in browser"""
        import webbrowser
        url = "http://localhost:8000/docs"
        if self.config_data:
            url = f"http://{self.config_data.api_host}:{self.config_data.api_port}/docs"
        webbrowser.open(url)
    
    def show_documentation(self):
        """Show documentation"""
        doc_path = Path("INSTALL.md")
        if doc_path.exists():
            import webbrowser
            webbrowser.open(str(doc_path.absolute()))
        else:
            messagebox.showinfo("Documentation", 
                               "See INSTALL.md and README.md for documentation")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Ground Station Core v2.0

Modern satellite tracking and communication system

Features:
• Real-time satellite tracking
• Pass prediction
• Command uplink
• Telemetry monitoring  
• REST API integration

© 2025 NU-Horizonsat
Licensed under terms in LICENSE file"""
        
        messagebox.showinfo("About Ground Station Core", about_text)


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Check dependencies
    missing = []
    if not HAS_SKYFIELD:
        missing.append("skyfield")
    if not HAS_MATPLOTLIB:
        missing.append("matplotlib")
    if not HAS_NUMPY:
        missing.append("numpy")
    if not HAS_REQUESTS:
        missing.append("requests")
    
    if missing:
        print("Warning: Some optional dependencies are missing:")
        for lib in missing:
            print(f"  - {lib}")
        print("\nInstall with: pip install " + " ".join(missing))
        print("\nSome features may be disabled.\n")
    
    app = SatelliteGroundStationUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
