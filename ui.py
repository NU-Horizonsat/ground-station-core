import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import time
import threading
import requests
import json
import os
import subprocess
from datetime import datetime, timedelta
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Querybox
from PIL import Image, ImageTk
from tkinterweb import HtmlFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from influxdb_client import InfluxDBClient, Point, WritePrecision
import random  # For simulation
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class SatelliteGroundStationUI:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(theme="darkly")  # Modern dark theme
        self.root.title("Satellite Ground Station")
        self.root.geometry("1280x800")
        self.connected = False
        self.telemetry_data = {"battery": [], "temperature": [], "signal": []}
        self.telemetry_times = []
        self.scheduled_commands = []  # Store scheduled commands
        
        # Service process tracking
        self.influxdb_process = None
        self.grafana_process = None
        self.service_check_active = True
        
        self.create_ui()
        
        # InfluxDB configuration (for Grafana)
        self.influxdb_url = "http://localhost:8086"
        self.influxdb_token = "your_token_here"  # Replace with your token
        self.influxdb_org = "your_org"  # Replace with your org
        self.influxdb_bucket = "satellite_telemetry"
        
    def create_ui(self):
        # Create main frame with two panels
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for command controls
        left_frame = ttk.LabelFrame(main_frame, text="Command Center", bootstyle=PRIMARY)
        main_frame.add(left_frame, weight=1)
        
        # Right panel for data display
        right_frame = ttk.LabelFrame(main_frame, text="Satellite Data", bootstyle=SUCCESS)
        main_frame.add(right_frame, weight=2)
        
        # Create connection controls
        conn_frame = ttk.LabelFrame(left_frame, text="Connection", bootstyle=INFO)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", 
                                     bootstyle=SUCCESS, command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", 
                                         bootstyle=DANGER, command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.status_label = ttk.Label(conn_frame, text="Status: Disconnected", 
                                      bootstyle="inverse-danger")
        self.status_label.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Command selection section
        cmd_frame = ttk.LabelFrame(left_frame, text="Command Selection", bootstyle=WARNING)
        cmd_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        ttk.Label(cmd_frame, text="Command Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cmd_type = ttk.Combobox(cmd_frame, values=[
            "Telemetry Request", 
            "Attitude Adjustment", 
            "Power Cycle", 
            "Data Download",
            "System Reset"
        ])
        self.cmd_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.cmd_type.current(0)
        self.cmd_type.bind("<<ComboboxSelected>>", self.update_parameters)
        
        # Parameters section
        self.param_frame = ttk.LabelFrame(cmd_frame, text="Parameters", bootstyle=INFO)
        self.param_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        # Will be populated by update_parameters()
        self.param_widgets = []
        
        # Send command button
        self.send_btn = ttk.Button(cmd_frame, text="Send Command", bootstyle=SUCCESS,
                                 command=self.send_command, state=tk.DISABLED)
        self.send_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky=tk.EW)
        
        # Make rows and columns expandable
        cmd_frame.columnconfigure(1, weight=1)
        cmd_frame.rowconfigure(1, weight=1)
        
        # Create data display with notebook tabs
        self.notebook = ttk.Notebook(right_frame, bootstyle=DARK)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Telemetry data tab
        telemetry_frame = ttk.Frame(self.notebook)
        self.notebook.add(telemetry_frame, text="Telemetry")
        
        self.telemetry_display = scrolledtext.ScrolledText(telemetry_frame, wrap=tk.WORD)
        self.telemetry_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Command log tab
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Command Log")
        
        self.log_display = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization tab
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="Visualization")
        
        # Create a figure for the plots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(10, 8))
        self.fig.tight_layout(pad=3.0)
        
        # Create canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add Grafana dashboard tab
        self.create_grafana_tab()
        
        # Instructions for Grafana setup
        # ttk.Label(grafana_frame, text="Note: To view Grafana dashboard, make sure Grafana is running at the URL below",
        #          bootstyle=INFO).pack(pady=5)
        
        # Frame for Grafana dashboard (using tkinterweb)
        # self.grafana_view = HtmlFrame(grafana_frame)
        # self.grafana_url = "http://localhost:3000/d/satellite/satellite-telemetry"  # Replace with your dashboard URL
        # self.grafana_view.load_website(self.grafana_url)
        # self.grafana_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # # Refresh button for Grafana
        # ttk.Button(grafana_frame, text="Refresh Dashboard", 
        #           bootstyle=INFO, command=lambda: self.grafana_view.load_website(self.grafana_url)).pack(pady=5)
        
        # Add Command Scheduling tab
        self.create_schedule_tab()
        
        # Add Pass Times tab
        self.create_pass_times_tab()
        
        # Add Satellite Position tab
        self.create_position_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize parameter display
        self.update_parameters()
        
        # Start command execution checker
        self.check_scheduled_commands()
        
    def create_schedule_tab(self):
        """Create the command scheduling tab"""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="Schedule Commands")
        
        # Split the frame into two sections
        left_panel = ttk.Frame(schedule_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_panel = ttk.Frame(schedule_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Command selection section (left panel)
        cmd_frame = ttk.LabelFrame(left_panel, text="Schedule New Command", bootstyle=WARNING)
        cmd_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        ttk.Label(cmd_frame, text="Command Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.schedule_cmd_type = ttk.Combobox(cmd_frame, values=[
            "Telemetry Request", 
            "Attitude Adjustment", 
            "Power Cycle", 
            "Data Download",
            "System Reset"
        ])
        self.schedule_cmd_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.schedule_cmd_type.current(0)
        
        # Parameters frame
        self.schedule_param_frame = ttk.LabelFrame(cmd_frame, text="Parameters", bootstyle=INFO)
        self.schedule_param_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        # Default parameter (subsystem selector for telemetry)
        self.schedule_subsystem_label = ttk.Label(self.schedule_param_frame, text="Subsystem:")
        self.schedule_subsystem_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.schedule_subsystem = ttk.Combobox(self.schedule_param_frame, values=["Power", "Thermal", "Comms", "Payload", "ADCS"])
        self.schedule_subsystem.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.schedule_subsystem.current(0)
        
        # Date and time selection
        ttk.Label(cmd_frame, text="Execution Date:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.schedule_date = ttk.DateEntry(cmd_frame)
        self.schedule_date.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(cmd_frame, text="Execution Time:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        time_frame = ttk.Frame(cmd_frame)
        time_frame.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        self.schedule_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.schedule_hour.pack(side=tk.LEFT, padx=2)
        self.schedule_hour.set("12")
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        self.schedule_minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.schedule_minute.pack(side=tk.LEFT, padx=2)
        self.schedule_minute.set("00")
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        self.schedule_second = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.schedule_second.pack(side=tk.LEFT, padx=2)
        self.schedule_second.set("00")
        
        # Recurrence options
        ttk.Label(cmd_frame, text="Recurrence:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.schedule_recurrence = ttk.Combobox(cmd_frame, values=["Once", "Daily", "Weekly"])
        self.schedule_recurrence.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        self.schedule_recurrence.current(0)
        
        # Add to schedule button
        ttk.Button(cmd_frame, text="Add to Schedule", 
                  bootstyle=SUCCESS, command=self.add_scheduled_command).grid(
                      row=5, column=0, columnspan=2, padx=5, pady=10, sticky=tk.EW)
        
        # Configure grid weights
        cmd_frame.columnconfigure(1, weight=1)
        cmd_frame.rowconfigure(1, weight=1)
        
        # Scheduled commands list (right panel)
        list_frame = ttk.LabelFrame(right_panel, text="Scheduled Commands", bootstyle=PRIMARY)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for scheduled commands
        columns = ("id", "time", "command", "parameters", "recurrence", "status")
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define headings
        self.schedule_tree.heading("id", text="ID")
        self.schedule_tree.heading("time", text="Execution Time")
        self.schedule_tree.heading("command", text="Command")
        self.schedule_tree.heading("parameters", text="Parameters")
        self.schedule_tree.heading("recurrence", text="Recurrence")
        self.schedule_tree.heading("status", text="Status")
        
        # Define columns
        self.schedule_tree.column("id", width=40)
        self.schedule_tree.column("time", width=150)
        self.schedule_tree.column("command", width=120)
        self.schedule_tree.column("parameters", width=180)
        self.schedule_tree.column("recurrence", width=80)
        self.schedule_tree.column("status", width=80)
        
        # Add scrollbar
        schedule_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=schedule_scroll.set)
        
        # Pack widgets
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        schedule_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons for managing scheduled commands
        btn_frame = ttk.Frame(right_panel)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Remove Selected", 
                  bootstyle=DANGER, command=self.remove_scheduled_command).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Edit Selected", 
                  bootstyle=WARNING, command=self.edit_scheduled_command).pack(side=tk.LEFT, padx=5)

        # Add sample data
        self.schedule_tree.insert("", tk.END, values=("1", "2025-03-27 08:00:00", "Telemetry Request", "Subsystem: Power", "Once", "Pending"))
        self.schedule_tree.insert("", tk.END, values=("2", "2025-03-27 12:30:00", "Attitude Adjustment", "Roll: 5°, Pitch: 0°, Yaw: 2°", "Daily", "Pending"))

    def create_pass_times_tab(self):
        """Create the satellite pass times tab"""
        pass_frame = ttk.Frame(self.notebook)
        self.notebook.add(pass_frame, text="Pass Times")
        
        # Controls frame
        controls_frame = ttk.Frame(pass_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Ground Station:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # Ground station coordinates
        coord_frame = ttk.Frame(controls_frame)
        coord_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(coord_frame, text="Lat:").grid(row=0, column=0)
        self.lat_entry = ttk.Entry(coord_frame, width=10)
        self.lat_entry.insert(0, "37.7749")  # Example: San Francisco
        self.lat_entry.grid(row=0, column=1, padx=2)
        
        ttk.Label(coord_frame, text="Lon:").grid(row=0, column=2, padx=(10,0))
        self.lon_entry = ttk.Entry(coord_frame, width=10)
        self.lon_entry.insert(0, "-122.4194")  # Example: San Francisco
        self.lon_entry.grid(row=0, column=3, padx=2)
        
        # Minimum elevation filter
        ttk.Label(controls_frame, text="Min Elevation:").pack(side=tk.LEFT, padx=(20,5), pady=5)
        self.elev_spinbox = ttk.Spinbox(controls_frame, from_=0, to=90, width=5)
        self.elev_spinbox.set("10")  # 10 degrees default
        self.elev_spinbox.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Label(controls_frame, text="degrees").pack(side=tk.LEFT, padx=0, pady=5)
        
        # Date range
        ttk.Label(controls_frame, text="Date Range:").pack(side=tk.LEFT, padx=(20,5), pady=5)
        self.start_date = ttk.DateEntry(controls_frame)
        self.start_date.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(controls_frame, text="to").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.end_date = ttk.DateEntry(controls_frame)
        self.end_date.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Satellite selection
        ttk.Label(controls_frame, text="Satellite:").pack(side=tk.LEFT, padx=(20,5), pady=5)
        self.pass_satellite = ttk.Combobox(controls_frame, values=["ISS (ZARYA)", "NOAA-19", "METEOR-M2"])
        self.pass_satellite.pack(side=tk.LEFT, padx=5, pady=5)
        self.pass_satellite.current(0)
        
        # Calculate button
        ttk.Button(controls_frame, text="Calculate Passes", 
                  bootstyle=SUCCESS, command=self.calculate_passes).pack(side=tk.LEFT, padx=20, pady=5)
        
        # Pass list
        list_frame = ttk.LabelFrame(pass_frame, text="Upcoming Passes")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for pass times
        columns = ("aos", "los", "max_elev", "duration", "direction", "satellite")
        self.pass_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define headings
        self.pass_tree.heading("aos", text="AOS Time")
        self.pass_tree.heading("los", text="LOS Time")
        self.pass_tree.heading("max_elev", text="Max Elevation")
        self.pass_tree.heading("duration", text="Duration")
        self.pass_tree.heading("direction", text="Direction")
        self.pass_tree.heading("satellite", text="Satellite")
        
        # Define columns
        self.pass_tree.column("aos", width=150)
        self.pass_tree.column("los", width=150)
        self.pass_tree.column("max_elev", width=100)
        self.pass_tree.column("duration", width=100)
        self.pass_tree.column("direction", width=100)
        self.pass_tree.column("satellite", width=100)
        
        # Add scrollbar
        pass_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.pass_tree.yview)
        self.pass_tree.configure(yscrollcommand=pass_scroll.set)
        
        # Pack widgets
        self.pass_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pass_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(pass_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Schedule Auto-Tracking", 
                 bootstyle=INFO, command=self.schedule_tracking).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Export Pass List", 
                 bootstyle=WARNING, command=self.export_pass_list).pack(side=tk.LEFT, padx=5)

    def create_position_tab(self):
        """Create the satellite position tracking tab"""
        position_frame = ttk.Frame(self.notebook)
        self.notebook.add(position_frame, text="Satellite Position")
        
        # Split into top control panel and bottom map
        controls_frame = ttk.Frame(position_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # TLE input
        tle_frame = ttk.LabelFrame(controls_frame, text="Satellite TLE Data")
        tle_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Label(tle_frame, text="Satellite:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.satellite_combo = ttk.Combobox(tle_frame, values=["ISS (ZARYA)", "NOAA-19", "METEOR-M2", "Custom..."])
        self.satellite_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.satellite_combo.current(0)
        self.satellite_combo.bind("<<ComboboxSelected>>", self.update_tle_data)
        
        ttk.Label(tle_frame, text="Line 1:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.tle_line1 = ttk.Entry(tle_frame, width=70)
        self.tle_line1.insert(0, "1 25544U 98067A   25085.52489910  .00010561  00000+0  18891-3 0  9996")
        self.tle_line1.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(tle_frame, text="Line 2:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.tle_line2 = ttk.Entry(tle_frame, width=70)
        self.tle_line2.insert(0, "2 25544  51.6455 207.8057 0005848 208.1539 256.4878 15.49418298436373")
        self.tle_line2.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Tracking controls
        track_frame = ttk.LabelFrame(controls_frame, text="Tracking Controls")
        track_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Button(track_frame, text="Update Position", 
                bootstyle=SUCCESS, command=self.update_satellite_position).pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        self.realtime_tracking_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(track_frame, text="Real-time tracking", 
                    variable=self.realtime_tracking_var, 
                    command=self.toggle_realtime_tracking).pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.show_groundtrack_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(track_frame, text="Show ground track", 
                    variable=self.show_groundtrack_var,
                    command=self.update_satellite_position).pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.show_coverage_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(track_frame, text="Show coverage area", 
                    variable=self.show_coverage_var,
                    command=self.update_satellite_position).pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        # Map display
        self.map_frame = ttk.LabelFrame(position_frame, text="Satellite Position Map")
        self.map_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a figure for the world map with Cartopy projection
        self.map_fig = Figure(figsize=(10, 6))
        # Use PlateCarree projection which is standard for world maps
        self.map_ax = self.map_fig.add_subplot(111, projection=ccrs.PlateCarree())
        
        # Create the world map
        self.create_realistic_world_map()
        
        # Create canvas for the map
        self.map_canvas = FigureCanvasTkAgg(self.map_fig, master=self.map_frame)
        self.map_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Orbital information panel
        info_frame = ttk.LabelFrame(position_frame, text="Orbital Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid of information labels
        info_labels = [
            ("Latitude:", "0.00° N"), ("Longitude:", "0.00° E"),
            ("Altitude:", "408.05 km"), ("Velocity:", "27,576 km/h"),
            ("Period:", "92.9 min"), ("Inclination:", "51.64°"),
            ("Phase:", "Ascending"), ("Next Pass:", "2025-03-26 18:42:30")
        ]
        
        # Store the value labels for updating
        self.position_info_labels = {}
        
        # Create the grid of information
        for i, (label_text, value_text) in enumerate(info_labels):
            row, col = divmod(i, 4)
            ttk.Label(info_frame, text=label_text, font=("Arial", 10, "bold")).grid(
                row=row, column=col*2, padx=5, pady=5, sticky=tk.E)
            
            value_label = ttk.Label(info_frame, text=value_text)
            value_label.grid(row=row, column=col*2+1, padx=5, pady=5, sticky=tk.W)
            
            # Store reference to the value label
            self.position_info_labels[label_text] = value_label

    def create_realistic_world_map(self):
        """Create a realistic world map using Cartopy"""
        # Clear the axis
        self.map_ax.clear()
        
        # Set global extent
        self.map_ax.set_global()
        
        # Add natural Earth features
        self.map_ax.add_feature(cfeature.LAND, facecolor='lightgreen', alpha=0.5)
        self.map_ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.5)
        self.map_ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        self.map_ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=':')
        self.map_ax.add_feature(cfeature.LAKES, alpha=0.5)
        self.map_ax.add_feature(cfeature.RIVERS, linewidth=0.5, alpha=0.5)
        
        # Add a grid
        self.map_ax.gridlines(draw_labels=True, linewidth=0.2, color='gray', alpha=0.5, linestyle=':')
        
        # Set limits (in Plate Carree, longitude is -180 to 180, latitude is -90 to 90)
        self.map_ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())
        
        # Set title
        self.map_ax.set_title('Satellite Position')
        
        # Update the figure
        self.map_fig.tight_layout()
    
    def update_parameters(self, event=None):
        # Clear existing parameter widgets
        for widget in self.param_widgets:
            widget.destroy()
        self.param_widgets = []
        
        # Add appropriate parameter fields based on selected command
        cmd = self.cmd_type.get()
        
        if cmd == "Telemetry Request":
            label = ttk.Label(self.param_frame, text="Subsystem:")
            label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(label)
            
            subsystem = ttk.Combobox(self.param_frame, values=["Power", "Thermal", "Comms", "Payload", "ADCS"])
            subsystem.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
            subsystem.current(0)
            self.param_widgets.append(subsystem)
            
        elif cmd == "Attitude Adjustment":
            params = [("Roll (deg):", "0.0"), ("Pitch (deg):", "0.0"), ("Yaw (deg):", "0.0")]
            for i, (label_text, default) in enumerate(params):
                label = ttk.Label(self.param_frame, text=label_text)
                label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
                self.param_widgets.append(label)
                
                entry = ttk.Entry(self.param_frame)
                entry.insert(0, default)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self.param_widgets.append(entry)
                
        elif cmd == "Power Cycle":
            label = ttk.Label(self.param_frame, text="Component:")
            label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(label)
            
            component = ttk.Combobox(self.param_frame, values=["Radio", "Camera", "Experiment 1", "Experiment 2"])
            component.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
            component.current(0)
            self.param_widgets.append(component)
            
            delay_label = ttk.Label(self.param_frame, text="Delay (sec):")
            delay_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(delay_label)
            
            delay_entry = ttk.Entry(self.param_frame)
            delay_entry.insert(0, "5")
            delay_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
            self.param_widgets.append(delay_entry)
            
        # Configure grid weights
        self.param_frame.columnconfigure(1, weight=1)
            
    def connect(self):
        self.log_message("Connecting to satellite...")
        
        # Simulate connection process
        def connection_process():
            time.sleep(2)  # Simulate connection time
            self.root.after(0, self.connection_success)
            
        threading.Thread(target=connection_process, daemon=True).start()
        self.status_bar.config(text="Connecting...")
        
    def connection_success(self):
        self.connected = True
        self.status_label.config(text="Status: Connected", bootstyle="inverse-success")
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="Connected to satellite")
        self.log_message("Connection established")
        
        # Clear previous data
        self.telemetry_data = {"battery": [], "temperature": [], "signal": []}
        self.telemetry_times = []
        
        # Start simulated telemetry
        self.start_telemetry_simulation()
        
    def disconnect(self):
        self.connected = False
        self.status_label.config(text="Status: Disconnected", bootstyle="inverse-danger")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.status_bar.config(text="Disconnected from satellite")
        self.log_message("Connection closed")
        
    def send_command(self):
        command = self.cmd_type.get()
        self.log_message(f"Sending command: {command}")
        self.status_bar.config(text=f"Command sent: {command}")
        
        # Simulate command acknowledgement
        def command_ack():
            time.sleep(1)
            self.root.after(0, lambda: self.log_message(f"Command acknowledged: {command}"))
            
        threading.Thread(target=command_ack, daemon=True).start()
        
    def log_message(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_display.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_display.see(tk.END)
        
    def start_telemetry_simulation(self):
        def telemetry_thread():
            try:
                # Try to create an InfluxDB client (will work if InfluxDB is configured)
                client = InfluxDBClient(url=self.influxdb_url, token=self.influxdb_token, org=self.influxdb_org)
                write_api = client.write_api()
                influxdb_available = True
            except Exception as e:
                print(f"InfluxDB connection error: {e}")
                influxdb_available = False
            
            while self.connected:
                # Generate simulated telemetry
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                battery = 90 + (hash(timestamp) % 10)
                temp = 20 + (hash(timestamp) % 5)
                signal = -50 - (hash(timestamp) % 20)
                
                # Save data for visualization
                self.telemetry_times.append(timestamp)
                self.telemetry_data["battery"].append(battery)
                self.telemetry_data["temperature"].append(temp)
                self.telemetry_data["signal"].append(signal)
                
                # Keep only the last 50 data points
                if len(self.telemetry_times) > 50:
                    self.telemetry_times.pop(0)
                    self.telemetry_data["battery"].pop(0)
                    self.telemetry_data["temperature"].pop(0)
                    self.telemetry_data["signal"].pop(0)
                
                # Update plots
                self.update_plots()
                
                telemetry_text = f"[{timestamp}] Battery: {battery}%, Temperature: {temp}°C, Signal: {signal} dBm"
                
                # Send data to InfluxDB if available
                if influxdb_available:
                    try:
                        point = Point("satellite_telemetry") \
                            .tag("satellite", "sat1") \
                            .field("battery", float(battery)) \
                            .field("temperature", float(temp)) \
                            .field("signal", float(signal)) \
                            .time(datetime.utcnow(), WritePrecision.NS)
                        
                        write_api.write(bucket=self.influxdb_bucket, record=point)
                    except Exception as e:
                        print(f"Error writing to InfluxDB: {e}")
                
                # Update UI in thread-safe way
                self.root.after(0, lambda t=telemetry_text: self.update_telemetry(t))
                time.sleep(2)
                
        threading.Thread(target=telemetry_thread, daemon=True).start()
    
    def update_plots(self):
        # Don't update if no data or not connected
        if not self.telemetry_times or not self.connected:
            return
            
        try:
            # Clear all axes
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            
            # Plot battery level
            self.ax1.plot(range(len(self.telemetry_times)), self.telemetry_data["battery"], 'g-')
            self.ax1.set_ylabel('Battery (%)')
            self.ax1.set_title('Battery Level')
            self.ax1.set_ylim([0, 100])
            self.ax1.grid(True)
            
            # Plot temperature
            self.ax2.plot(range(len(self.telemetry_times)), self.telemetry_data["temperature"], 'r-')
            self.ax2.set_ylabel('Temperature (°C)')
            self.ax2.set_title('Satellite Temperature')
            self.ax2.grid(True)
            
            # Plot signal strength
            self.ax3.plot(range(len(self.telemetry_times)), self.telemetry_data["signal"], 'b-')
            self.ax3.set_ylabel('Signal (dBm)')
            self.ax3.set_title('Signal Strength')
            self.ax3.set_xlabel('Time (samples)')
            self.ax3.grid(True)
            
            # Update the figure
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error updating plots: {e}")
        
    def update_telemetry(self, data):
        self.telemetry_display.insert(tk.END, data + "\n")
        self.telemetry_display.see(tk.END)
        
    def add_scheduled_command(self):
        """Add a new command to the schedule"""
        # Get command details
        command = self.schedule_cmd_type.get()
        date_str = self.schedule_date.entry.get()
        time_str = f"{self.schedule_hour.get()}:{self.schedule_minute.get()}:{self.schedule_second.get()}"
        datetime_str = f"{date_str} {time_str}"
        recurrence = self.schedule_recurrence.get()
        
        # Get parameters based on command type
        parameters = ""
        if command == "Telemetry Request":
            parameters = f"Subsystem: {self.schedule_subsystem.get()}"
        elif command == "Attitude Adjustment":
            # Placeholder - in a real implementation, you would gather these from input fields
            parameters = "Roll: 5°, Pitch: 0°, Yaw: 2°"
        elif command == "Power Cycle":
            # Placeholder
            parameters = "Component: Radio, Delay: 5s"
            
        # Generate a unique ID
        cmd_id = len(self.scheduled_commands) + 1
            
        # Add to treeview
        self.schedule_tree.insert("", tk.END, values=(cmd_id, datetime_str, command, parameters, recurrence, "Pending"))
        
        # Store command details for execution
        self.scheduled_commands.append({
            "id": cmd_id,
            "time": datetime_str,
            "command": command,
            "parameters": parameters,
            "recurrence": recurrence,
            "status": "Pending"
        })
        
        self.log_message(f"Scheduled {command} for {datetime_str}")
        self.status_bar.config(text=f"Command scheduled: {command} at {datetime_str}")
        
    def remove_scheduled_command(self):
        """Remove the selected scheduled command"""
        selected = self.schedule_tree.selection()
        if not selected:
            return
            
        # Get the command ID
        cmd_id = self.schedule_tree.item(selected[0], "values")[0]
        
        # Remove from treeview
        self.schedule_tree.delete(selected[0])
        
        # Remove from scheduled commands list
        self.scheduled_commands = [cmd for cmd in self.scheduled_commands if str(cmd["id"]) != str(cmd_id)]
        
        self.log_message(f"Removed scheduled command #{cmd_id}")
        self.status_bar.config(text=f"Scheduled command #{cmd_id} removed")
    
    def edit_scheduled_command(self):
        """Edit the selected scheduled command"""
        selected = self.schedule_tree.selection()
        if not selected:
            return
            
        # Get the command values
        values = self.schedule_tree.item(selected[0], "values")
        cmd_id = values[0]
        
        # Show message
        messagebox.showinfo("Edit Command", 
                           f"Editing command #{cmd_id} is not fully implemented.\n\n"
                           f"In a complete implementation, this would open an editor dialog "
                           f"to modify the command parameters and execution time.")
        
        self.log_message(f"Edited scheduled command #{cmd_id}")
    
    def check_scheduled_commands(self):
        """Check for commands that need to be executed"""
        current_time = datetime.now()
        
        # Check each scheduled command
        for cmd in self.scheduled_commands:
            if cmd["status"] == "Pending":
                try:
                    # Parse the scheduled time
                    cmd_time = datetime.strptime(cmd["time"], "%Y-%m-%d %H:%M:%S")
                    
                    # If it's time to execute
                    if current_time >= cmd_time:
                        # Execute the command
                        self.execute_scheduled_command(cmd)
                        
                        # Update status
                        cmd["status"] = "Executed"
                        
                        # Update treeview
                        for item in self.schedule_tree.get_children():
                            if self.schedule_tree.item(item, "values")[0] == str(cmd["id"]):
                                values = list(self.schedule_tree.item(item, "values"))
                                values[5] = "Executed"  # Update status
                                self.schedule_tree.item(item, values=values)
                                break
                                
                        # If recurring, schedule the next occurrence
                        if cmd["recurrence"] == "Daily":
                            self.reschedule_command(cmd, timedelta(days=1))
                        elif cmd["recurrence"] == "Weekly":
                            self.reschedule_command(cmd, timedelta(weeks=1))
                except Exception as e:
                    print(f"Error checking scheduled command: {e}")
        
        # Check again in 1 second
        self.root.after(1000, self.check_scheduled_commands)
        
    def execute_scheduled_command(self, cmd):
        """Execute a scheduled command"""
        self.log_message(f"Executing scheduled command: {cmd['command']}")
        
        # In a real implementation, this would send the command to the satellite
        # For demonstration, we'll just log it
        self.log_message(f"Command executed: {cmd['command']} with parameters: {cmd['parameters']}")
        
    def reschedule_command(self, cmd, delta):
        """Reschedule a recurring command"""
        # Parse the old time
        old_time = datetime.strptime(cmd["time"], "%Y-%m-%d %H:%M:%S")
        
        # Calculate the new time
        new_time = old_time + delta
        new_time_str = new_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a new command
        new_cmd = cmd.copy()
        new_cmd["id"] = len(self.scheduled_commands) + 1
        new_cmd["time"] = new_time_str
        new_cmd["status"] = "Pending"
        
        # Add to scheduled commands
        self.scheduled_commands.append(new_cmd)
        
        # Add to treeview
        self.schedule_tree.insert("", tk.END, values=(
            new_cmd["id"], new_cmd["time"], new_cmd["command"], 
            new_cmd["parameters"], new_cmd["recurrence"], new_cmd["status"]
        ))
        
        self.log_message(f"Rescheduled {cmd['command']} for {new_time_str}")
    
    def calculate_passes(self):
        """Calculate satellite passes for the specified time range"""
        # Get inputs
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            min_elev = float(self.elev_spinbox.get())
            satellite = self.pass_satellite.get()
            
            # Clear existing pass data
            for item in self.pass_tree.get_children():
                self.pass_tree.delete(item)
                
            # Simulate calculating passes
            self.status_bar.config(text=f"Calculating passes for {satellite}...")
            
            # In a real implementation, this would use orbital mechanics calculations
            # For demonstration, we'll generate random passes
            self.generate_simulated_passes(satellite)
            
            self.log_message(f"Calculated passes for {satellite} from ground station at {lat}, {lon}")
            self.status_bar.config(text=f"Calculated passes for {satellite}")
            
        except ValueError as e:
            messagebox.showerror("Input Error", "Please check your latitude and longitude values")
    
    def generate_simulated_passes(self, satellite):
        """Generate simulated pass times for demonstration"""
        # Get the date range
        try:
            start_date = datetime.strptime(self.start_date.entry.get(), "%m/%d/%y")
            end_date = datetime.strptime(self.end_date.entry.get(), "%m/%d/%y")
            
            # Ensure end date is after start date
            if end_date <= start_date:
                end_date = start_date + timedelta(days=7)
                
            # Number of days in the range
            days = (end_date - start_date).days
            
            # Generate 1-2 passes per day
            current_date = start_date
            for _ in range(days):
                # Number of passes for this day
                num_passes = random.randint(1, 2)
                
                for _ in range(num_passes):
                    # Random time of day
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    
                    # AOS time
                    aos_time = current_date.replace(hour=hour, minute=minute)
                    
                    # Duration between 8 and 15 minutes
                    duration_minutes = random.randint(8, 15)
                    duration_seconds = random.randint(0, 59)
                    
                    # LOS time
                    los_time = aos_time + timedelta(minutes=duration_minutes, seconds=duration_seconds)
                    
                    # Max elevation between 15 and 85 degrees
                    max_elev = random.randint(15, 85)
                    
                    # Direction
                    direction = random.choice(["N to S", "S to N"])
                    
                    # Format strings
                    aos_str = aos_time.strftime("%Y-%m-%d %H:%M:%S")
                    los_str = los_time.strftime("%Y-%m-%d %H:%M:%S")
                    duration_str = f"{duration_minutes}m {duration_seconds}s"
                    
                    # Add to treeview
                    self.pass_tree.insert("", tk.END, values=(
                        aos_str, los_str, f"{max_elev}°", 
                        duration_str, direction, satellite
                    ))
                
                # Next day
                current_date += timedelta(days=1)
                
        except Exception as e:
            print(f"Error generating passes: {e}")
    
    def schedule_tracking(self):
        """Schedule automatic tracking for selected pass"""
        selected = self.pass_tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a pass to schedule tracking")
            return
            
        # Get pass information
        values = self.pass_tree.item(selected[0], "values")
        aos_time = values[0]
        satellite = values[5]
        
        # Confirm with user
        if messagebox.askyesno("Schedule Tracking", 
                              f"Schedule automatic tracking for {satellite} starting at {aos_time}?"):
            self.log_message(f"Scheduled automatic tracking for {satellite} at {aos_time}")
            self.status_bar.config(text=f"Tracking scheduled for {satellite}")
    
    def export_pass_list(self):
        """Export the pass list to a file"""
        # In a real implementation, this would save to a file
        messagebox.showinfo("Export Pass List", 
                           "In a complete implementation, this would export the pass list to a file "
                           "in CSV or other format.")
        self.log_message("Pass list exported")
    
    def update_satellite_position(self):
        """Update the satellite position on the map"""
        # In a real implementation, this would calculate the actual position
        # based on TLE data and current time
        
        # Clear and redraw the world map
        self.create_realistic_world_map()
        
        # Generate a simulated position (convert to the -180 to 180 longitude range for cartopy)
        lat = random.uniform(-80, 80)
        lon = random.uniform(-180, 180)
        
        # Plot the satellite position
        self.map_ax.plot(lon, lat, 'ro', markersize=8, transform=ccrs.PlateCarree())
        
        # Draw ground track if enabled
        if self.show_groundtrack_var.get():
            # Simplified ground track (would be calculated from orbit in real implementation)
            # Generate points along a track that wraps around the Earth
            num_points = 20
            track_lons = []
            track_lats = []
            
            for i in range(num_points):
                # Create a track that crosses the date line properly
                track_lons.append(lon + (i - num_points//2) * 18)
                track_lats.append(lat + 5 * np.sin(i / (num_points-1) * 2 * np.pi))
                
            self.map_ax.plot(track_lons, track_lats, 'r--', linewidth=1.5, transform=ccrs.PlateCarree())
        
        # Draw coverage area if enabled
        if self.show_coverage_var.get():
            # Create a proper circle in the Plate Carree projection
            coverage_radius = 20  # degrees
            
            # In a real implementation, this would be calculated based on satellite altitude
            # and field of view of instruments
            
            # Add a circle using the Circle patch
            circle = Circle((lon, lat), coverage_radius, color='r', fill=False, alpha=0.7, 
                        transform=ccrs.PlateCarree())
            self.map_ax.add_patch(circle)
        
        # Update the map
        self.map_canvas.draw()
        
        # Update orbital information
        self.update_orbital_info(lat, lon)
        
        satellite = self.satellite_combo.get()
        self.status_bar.config(text=f"Updated position for {satellite}")
    
    def update_orbital_info(self, lat, lon):
        """Update the orbital information labels"""
        # In a real implementation, these would be calculated from orbit parameters
        
        # Direction (N/S)
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        
        # Update labels
        self.position_info_labels["Latitude:"].config(text=f"{abs(lat):.2f}° {lat_dir}")
        self.position_info_labels["Longitude:"].config(text=f"{abs(lon):.2f}° {lon_dir}")
        
        # These values would be calculated in a real implementation
        altitude = random.uniform(400, 420)
        velocity = random.uniform(27500, 27600)
        period = random.uniform(92.5, 93.5)
        inclination = random.uniform(51.5, 51.7)
        
        # Phase is ascending when moving northward, descending when moving southward
        phase = "Ascending" if random.choice([True, False]) else "Descending"
        
        # Next pass time (would be calculated from orbit)
        next_pass = (datetime.now() + timedelta(hours=random.randint(2, 12))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Update the rest of the information
        self.position_info_labels["Altitude:"].config(text=f"{altitude:.2f} km")
        self.position_info_labels["Velocity:"].config(text=f"{velocity:.0f} km/h")
        self.position_info_labels["Period:"].config(text=f"{period:.1f} min")
        self.position_info_labels["Inclination:"].config(text=f"{inclination:.2f}°")
        self.position_info_labels["Phase:"].config(text=f"{phase}")
        self.position_info_labels["Next Pass:"].config(text=f"{next_pass}")
    
    def toggle_realtime_tracking(self):
        """Toggle real-time satellite tracking"""
        if self.realtime_tracking_var.get():
            # Start real-time tracking
            self.start_realtime_tracking()
            self.log_message("Started real-time tracking")
            self.status_bar.config(text="Real-time tracking enabled")
        else:
            # Stop real-time tracking
            self.stop_realtime_tracking()
            self.log_message("Stopped real-time tracking")
            self.status_bar.config(text="Real-time tracking disabled")
    
    def start_realtime_tracking(self):
        """Start real-time satellite tracking"""
        self.realtime_tracking_active = True
        
        def tracking_thread():
            while self.realtime_tracking_active and self.realtime_tracking_var.get():
                # Update position every 2 seconds
                self.root.after(0, self.update_satellite_position)
                time.sleep(2)
                
        threading.Thread(target=tracking_thread, daemon=True).start()
    
    def stop_realtime_tracking(self):
        """Stop real-time satellite tracking"""
        self.realtime_tracking_active = False
    
    def update_tle_data(self, event=None):
        """Update TLE data based on selected satellite"""
        satellite = self.satellite_combo.get()
        
        # In a real implementation, this would load actual TLE data
        # Here we just have example TLEs for demonstration
        if satellite == "ISS (ZARYA)":
            self.tle_line1.delete(0, tk.END)
            self.tle_line1.insert(0, "1 25544U 98067A   25085.52489910  .00010561  00000+0  18891-3 0  9996")
            self.tle_line2.delete(0, tk.END)
            self.tle_line2.insert(0, "2 25544  51.6455 207.8057 0005848 208.1539 256.4878 15.49418298436373")
        elif satellite == "NOAA-19":
            self.tle_line1.delete(0, tk.END)
            self.tle_line1.insert(0, "1 33591U 09005A   25085.51612874  .00000075  00000+0  65128-4 0  9992")
            self.tle_line2.delete(0, tk.END)
            self.tle_line2.insert(0, "2 33591  99.1932 157.6232 0013815 197.4586 162.6126 14.12500935826138")
        elif satellite == "METEOR-M2":
            self.tle_line1.delete(0, tk.END)
            self.tle_line1.insert(0, "1 40069U 14037A   25085.52553907  .00000041  00000+0  42912-4 0  9990")
            self.tle_line2.delete(0, tk.END)
            self.tle_line2.insert(0, "2 40069  98.5564 204.9266 0006121 102.2088 257.9815 14.20651977503457")
            
        # Update the satellite position
        self.update_satellite_position()

    def browse_file(self, service_type):
        """Browse for executable file"""
        file_path = filedialog.askopenfilename(
            title=f"Select {service_type.capitalize()} Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if file_path:
            if service_type == "influxdb":
                self.influxdb_path.delete(0, tk.END)
                self.influxdb_path.insert(0, file_path)
            elif service_type == "grafana":
                self.grafana_path.delete(0, tk.END)
                self.grafana_path.insert(0, file_path)
    
    def check_service_status(self):
        """Check if InfluxDB and Grafana are running"""
        if not self.service_check_active:
            return
            
        # Check InfluxDB
        influxdb_running = self.is_service_running(self.influxdb_process, "influxd.exe")
        if influxdb_running:
            self.influxdb_status.config(text="Running", bootstyle="inverse-success")
            self.start_influxdb_btn.config(state=tk.DISABLED)
            self.stop_influxdb_btn.config(state=tk.NORMAL)
        else:
            self.influxdb_status.config(text="Stopped", bootstyle="inverse-danger")
            self.start_influxdb_btn.config(state=tk.NORMAL)
            self.stop_influxdb_btn.config(state=tk.DISABLED)
            
        # Check Grafana
        grafana_running = self.is_service_running(self.grafana_process, "grafana-server.exe")
        if grafana_running:
            self.grafana_status.config(text="Running", bootstyle="inverse-success")
            self.start_grafana_btn.config(state=tk.DISABLED)
            self.stop_grafana_btn.config(state=tk.NORMAL)
        else:
            self.grafana_status.config(text="Stopped", bootstyle="inverse-danger")
            self.start_grafana_btn.config(state=tk.NORMAL)
            self.stop_grafana_btn.config(state=tk.DISABLED)
        
        # Schedule next check
        self.root.after(5000, self.check_service_status)  # Check every 5 seconds
    
    def is_service_running(self, process, process_name):
        """Check if a service is running by process name"""
        # First check if we have a process object and it's still running
        if process and process.poll() is None:
            return True
            
        # If not, check if the process is running elsewhere (like as a Windows service)
        try:
            # Use Windows tasklist command to check for running processes
            result = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {process_name}"], 
                                   capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return process_name.lower() in result.stdout.lower()
        except Exception as e:
            print(f"Error checking service status: {e}")
            return False
        
        # Update the Grafana dashboard tab method
    def create_grafana_tab(self):
        """Create the Grafana dashboard tab"""
        grafana_frame = ttk.Frame(self.notebook)
        self.notebook.add(grafana_frame, text="Grafana Dashboard")
        
        # Top panel for controls
        controls_frame = ttk.Frame(grafana_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Service control panel
        service_frame = ttk.LabelFrame(controls_frame, text="Service Controls")
        service_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # InfluxDB controls
        influx_frame = ttk.Frame(service_frame)
        influx_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(influx_frame, text="InfluxDB:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.influxdb_status = ttk.Label(influx_frame, text="Stopped", bootstyle="inverse-danger")
        self.influxdb_status.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.start_influxdb_btn = ttk.Button(influx_frame, text="Start InfluxDB", 
                                           bootstyle=SUCCESS, command=self.start_influxdb)
        self.start_influxdb_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_influxdb_btn = ttk.Button(influx_frame, text="Stop InfluxDB", 
                                          bootstyle=DANGER, command=self.stop_influxdb,
                                          state=tk.DISABLED)
        self.stop_influxdb_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Grafana controls
        grafana_control_frame = ttk.Frame(service_frame)
        grafana_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(grafana_control_frame, text="Grafana:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.grafana_status = ttk.Label(grafana_control_frame, text="Stopped", bootstyle="inverse-danger")
        self.grafana_status.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.start_grafana_btn = ttk.Button(grafana_control_frame, text="Start Grafana", 
                                          bootstyle=SUCCESS, command=self.start_grafana)
        self.start_grafana_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_grafana_btn = ttk.Button(grafana_control_frame, text="Stop Grafana", 
                                         bootstyle=DANGER, command=self.stop_grafana,
                                         state=tk.DISABLED)
        self.stop_grafana_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Configuration settings
        config_frame = ttk.LabelFrame(controls_frame, text="Configuration")
        config_frame.pack(side=tk.RIGHT, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(config_frame, text="InfluxDB Path:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.influxdb_path = ttk.Entry(config_frame, width=40)
        self.influxdb_path.insert(0, r"C:\Program Files\InfluxDB\influxd.exe")
        self.influxdb_path.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(config_frame, text="Browse", command=lambda: self.browse_file("influxdb")).grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Grafana Path:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.grafana_path = ttk.Entry(config_frame, width=40)
        self.grafana_path.insert(0, r"C:\Program Files\GrafanaLabs\grafana\bin\grafana-server.exe")
        self.grafana_path.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(config_frame, text="Browse", command=lambda: self.browse_file("grafana")).grid(row=1, column=2, padx=5, pady=2)
        
        # Instructions for Grafana setup
        ttk.Label(grafana_frame, text="Note: To view Grafana dashboard, make sure InfluxDB and Grafana are running",
                 bootstyle=INFO).pack(pady=5)
        
        # Frame for Grafana dashboard (using tkinterweb)
        self.grafana_view = HtmlFrame(grafana_frame)
        self.grafana_url = "http://localhost:3000/d/satellite/satellite-telemetry"  # Replace with your dashboard URL
        self.grafana_view.load_website(self.grafana_url)
        self.grafana_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Refresh button for Grafana
        ttk.Button(grafana_frame, text="Refresh Dashboard", 
                  bootstyle=INFO, command=lambda: self.grafana_view.load_website(self.grafana_url)).pack(pady=5)
        
        # Start checking the status of services
        self.check_service_status()
    
    def start_influxdb(self):
        """Start the InfluxDB service"""
        if self.is_service_running(self.influxdb_process, "influxd.exe"):
            return  # Already running
            
        try:
            # Get path from UI
            influxdb_path = self.influxdb_path.get()
            
            # Validate path exists
            if not os.path.exists(influxdb_path):
                messagebox.showerror("Error", f"InfluxDB executable not found at:\n{influxdb_path}")
                return
                
            # Start process
            self.log_message("Starting InfluxDB service...")
            self.influxdb_process = subprocess.Popen([influxdb_path], 
                                                    creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Update UI
            self.influxdb_status.config(text="Starting...", bootstyle="inverse-warning")
            self.root.after(5000, self.check_service_status)  # Check status after 5 seconds
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start InfluxDB: {e}")
    
    def stop_influxdb(self):
        """Stop the InfluxDB service"""
        if not self.is_service_running(self.influxdb_process, "influxd.exe"):
            return  # Not running
            
        try:
            # Try to stop our process if we started it
            if self.influxdb_process and self.influxdb_process.poll() is None:
                self.log_message("Stopping InfluxDB service...")
                self.influxdb_process.terminate()
                
                # Wait for termination with timeout
                try:
                    self.influxdb_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.influxdb_process.kill()  # Force kill if not terminated
                    
                self.influxdb_process = None
            else:
                # Try to kill the process by name (if it was started elsewhere)
                subprocess.run(["taskkill", "/F", "/IM", "influxd.exe"], 
                              creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Update UI
            self.influxdb_status.config(text="Stopping...", bootstyle="inverse-warning")
            self.root.after(2000, self.check_service_status)  # Check status after 2 seconds
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop InfluxDB: {e}")
    
    def start_grafana(self):
        """Start the Grafana service"""
        if self.is_service_running(self.grafana_process, "grafana-server.exe"):
            return  # Already running
            
        try:
            # Get path from UI
            grafana_path = self.grafana_path.get()
            
            # Validate path exists
            if not os.path.exists(grafana_path):
                messagebox.showerror("Error", f"Grafana executable not found at:\n{grafana_path}")
                return
                
            # Start process
            self.log_message("Starting Grafana service...")
            
            # Get the directory of the grafana-server.exe file
            grafana_dir = os.path.dirname(grafana_path)
            
            # Start the process in its directory to ensure it finds its configuration
            self.grafana_process = subprocess.Popen([grafana_path], 
                                                    cwd=grafana_dir,
                                                    creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Update UI
            self.grafana_status.config(text="Starting...", bootstyle="inverse-warning")
            self.root.after(5000, self.check_service_status)  # Check status after 5 seconds
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Grafana: {e}")
    
    def stop_grafana(self):
        """Stop the Grafana service"""
        if not self.is_service_running(self.grafana_process, "grafana-server.exe"):
            return  # Not running
            
        try:
            # Try to stop our process if we started it
            if self.grafana_process and self.grafana_process.poll() is None:
                self.log_message("Stopping Grafana service...")
                self.grafana_process.terminate()
                
                # Wait for termination with timeout
                try:
                    self.grafana_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.grafana_process.kill()  # Force kill if not terminated
                    
                self.grafana_process = None
            else:
                # Try to kill the process by name (if it was started elsewhere)
                subprocess.run(["taskkill", "/F", "/IM", "grafana-server.exe"], 
                              creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Update UI
            self.grafana_status.config(text="Stopping...", bootstyle="inverse-warning")
            self.root.after(2000, self.check_service_status)  # Check status after 2 seconds
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop Grafana: {e}")

def main():
    root = ttk.Window()
    app = SatelliteGroundStationUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()