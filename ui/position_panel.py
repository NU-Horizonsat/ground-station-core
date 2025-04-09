import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import threading
import time
import math
import random
import numpy as np

class PositionPanel:
    """Panel for tracking satellite position"""
    
    def __init__(self, notebook, api_client, on_log):
        self.notebook = notebook
        self.api_client = api_client
        self.log_message = on_log
        
        # Tracking status
        self.realtime_tracking = False
        self.tracking_thread = None
        self.tracking_active = False
        
        # TLE data
        self.tle_data = {
            "ISS (ZARYA)": [
                "1 25544U 98067A   25085.52489910  .00010561  00000+0  18891-3 0  9996",
                "2 25544  51.6455 207.8057 0005848 208.1539 256.4878 15.49418298436373"
            ],
            "NOAA-19": [
                "1 33591U 09005A   25085.30531260  .00000127  00000+0  92608-4 0  9994",
                "2 33591  99.1582 133.0342 0013284 318.7345  41.2952 14.12473618731283"
            ],
            "METEOR-M2": [
                "1 40069U 14037A   25085.38577574  .00000012  00000+0  11432-4 0  9999",
                "2 40069  98.7131 345.4104 0004596 204.0794 156.0261 14.20656179507517"
            ]
        }
        
        # Current satellite position
        self.sat_position = {
            "latitude": 0.0,
            "longitude": 0.0,
            "altitude": 0.0,
            "azimuth": 0.0,
            "elevation": 0.0,
            "range": 0.0,
            "velocity": 0.0
        }
        
        # Create the panel
        self.create_panel()
    
    def create_panel(self):
        """Create the position tracking panel UI"""
        # Create the main frame
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Satellite Position")
        
        # Split into top control panel and bottom map
        controls_frame = ttk.Frame(self.frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # TLE input
        tle_frame = ttk.LabelFrame(controls_frame, text="Satellite TLE Data", bootstyle=INFO)
        tle_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Label(tle_frame, text="Satellite:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.satellite_combo = ttk.Combobox(tle_frame, values=["ISS (ZARYA)", "NOAA-19", "METEOR-M2", "Custom..."])
        self.satellite_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.satellite_combo.current(0)
        self.satellite_combo.bind("<<ComboboxSelected>>", self.update_tle_data)
        
        ttk.Label(tle_frame, text="Line 1:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.tle_line1 = ttk.Entry(tle_frame, width=70)
        self.tle_line1.insert(0, self.tle_data["ISS (ZARYA)"][0])
        self.tle_line1.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(tle_frame, text="Line 2:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.tle_line2 = ttk.Entry(tle_frame, width=70)
        self.tle_line2.insert(0, self.tle_data["ISS (ZARYA)"][1])
        self.tle_line2.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Tracking controls
        track_frame = ttk.LabelFrame(controls_frame, text="Tracking Controls", bootstyle=WARNING)
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
        self.map_frame = ttk.LabelFrame(self.frame, text="Satellite Position Map", bootstyle=PRIMARY)
        self.map_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a simple world map using matplotlib
        self.fig = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Draw a basic world map (simplified for example)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Position info panel
        info_frame = ttk.LabelFrame(self.map_frame, text="Position Information", bootstyle=INFO)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Position info labels
        self.position_info_labels = {}
        
        position_info = [
            ("Latitude:", "0.0°"),
            ("Longitude:", "0.0°"),
            ("Altitude:", "0.0 km"),
            ("Azimuth:", "0.0°"),
            ("Elevation:", "0.0°"),
            ("Range:", "0.0 km"),
            ("Velocity:", "0.0 km/s"),
            ("Satellite:", "ISS"),
            ("Updated:", "Never")
        ]
        
        # Create a grid of labels
        for i, (label_text, value) in enumerate(position_info):
            row = i // 2
            col = i % 2
            
            label = ttk.Label(info_frame, text=label_text)
            label.grid(row=row, column=col*2, padx=5, pady=5, sticky=tk.W)
            
            value_label = ttk.Label(info_frame, text=value)
            value_label.grid(row=row, column=col*2+1, padx=5, pady=5, sticky=tk.W)
            
            # Store reference to the value label
            self.position_info_labels[label_text] = value_label
        
        # Create initial world map
        self.create_world_map()
        
        # Update position once to initialize
        self.update_satellite_position()
    
    def create_world_map(self):
        """Create a simplified world map"""
        self.ax.clear()
        
        # Draw simple world map
        self.ax.set_xlim(-180, 180)
        self.ax.set_ylim(-90, 90)
        self.ax.grid(True)
        self.ax.set_title("Satellite Position")
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")
        
        # Add country/continent outlines - simplified for example
        # In a real implementation, you would use cartopy or a similar library
        # to draw an actual map with proper projections
        
        # Draw equator
        self.ax.axhline(y=0, color='b', linestyle='-', alpha=0.3)
        
        # Draw prime meridian
        self.ax.axvline(x=0, color='b', linestyle='-', alpha=0.3)
        
        # Draw simplified continents (very approximate)
        # North America
        x = np.array([-130, -70, -50, -130, -130])
        y = np.array([15, 15, 70, 70, 15])
        self.ax.fill(x, y, alpha=0.3, color='green')
        
        # South America
        x = np.array([-80, -35, -70, -80, -80])
        y = np.array([10, -10, -60, 10, 10])
        self.ax.fill(x, y, alpha=0.3, color='green')
        
        # Europe and Africa
        x = np.array([-10, 40, 30, -20, -10, -10])
        y = np.array([35, 35, -30, -35, 10, 35])
        self.ax.fill(x, y, alpha=0.3, color='tan')
        
        # Asia
        x = np.array([25, 140, 130, 40, 25, 25])
        y = np.array([35, 35, 10, 10, 35, 35])
        self.ax.fill(x, y, alpha=0.3, color='yellow')
        
        # Australia
        x = np.array([115, 155, 155, 115, 115])
        y = np.array([-10, -10, -40, -40, -10])
        self.ax.fill(x, y, alpha=0.3, color='orange')
        
        self.canvas.draw()
    
    def update_tle_data(self, event=None):
        """Update TLE data based on selected satellite"""
        satellite = self.satellite_combo.get()
        
        if satellite != "Custom...":
            tle_data = self.tle_data.get(satellite, ["", ""])
            self.tle_line1.delete(0, tk.END)
            self.tle_line1.insert(0, tle_data[0])
            
            self.tle_line2.delete(0, tk.END)
            self.tle_line2.insert(0, tle_data[1])
            
            # Update position with new TLE
            self.update_satellite_position()
    
    def toggle_realtime_tracking(self):
        """Toggle real-time tracking on/off"""
        self.realtime_tracking = self.realtime_tracking_var.get()
        
        if self.realtime_tracking:
            self.log_message("Starting real-time satellite tracking")
            self.start_tracking_thread()
        else:
            self.log_message("Stopping real-time satellite tracking")
            self.stop_tracking_thread()
    
    def start_tracking_thread(self):
        """Start a thread for continuous tracking updates"""
        if self.tracking_active:
            return  # Already tracking
        
        self.tracking_active = True
        
        def tracking_thread():
            while self.tracking_active:
                self.update_satellite_position()
                time.sleep(1)  # Update every second
        
        self.tracking_thread = threading.Thread(target=tracking_thread, daemon=True)
        self.tracking_thread.start()
    
    def stop_tracking_thread(self):
        """Stop the tracking thread"""
        self.tracking_active = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
            self.tracking_thread = None
    
    def update_satellite_position(self):
        """Update the satellite position and map display"""
        # In a real implementation, this would use SGP4 or similar to compute
        # the actual satellite position from TLE data
        
        # For demo purposes, simulate a satellite position
        
        # Use a time-based simulation for more realistic animation
        time_base = time.time() / 100.0  # Slow down movement
        
        # Simulate a simple orbit
        lat = 50 * math.sin(time_base)
        lon = (time_base * 15) % 360 - 180
        
        altitude = 400.0 + 10 * math.sin(time_base * 5)
        
        # Update satellite position
        self.sat_position["latitude"] = lat
        self.sat_position["longitude"] = lon
        self.sat_position["altitude"] = altitude
        
        # Simulate ground station at 0,0 for azimuth/elevation calculation
        gs_lat = 37.7749
        gs_lon = -122.4194
        
        # Calculate distance and bearing (very rough approximation)
        lat1 = math.radians(gs_lat)
        lon1 = math.radians(gs_lon)
        lat2 = math.radians(lat)
        lon2 = math.radians(lon)
        
        # Rough distance calculation (not accounting for Earth's curvature or altitude)
        R = 6371.0  # Earth radius in km
        x = (lon2 - lon1) * math.cos(0.5 * (lat2 + lat1))
        y = lat2 - lat1
        d = R * math.sqrt(x*x + y*y)
        
        # Rough bearing calculation
        bearing = math.atan2(x, y)
        azimuth = (math.degrees(bearing) + 360) % 360
        
        # Rough elevation calculation
        elevation = math.degrees(math.atan2(altitude, d))
        
        # Update position data
        self.sat_position["azimuth"] = azimuth
        self.sat_position["elevation"] = elevation
        self.sat_position["range"] = math.sqrt(d*d + altitude*altitude)
        self.sat_position["velocity"] = 7.8  # ISS speed, roughly constant
        
        # Update the map
        self.update_map()
        
        # Update position info display
        self.update_position_display()
    
    def update_map(self):
        """Update the satellite position map"""
        # Clear previous plot
        self.ax.clear()
        
        # Redraw the map
        self.create_world_map()
        
        # Plot the current satellite position
        self.ax.plot(self.sat_position["longitude"], self.sat_position["latitude"], 'ro', markersize=8)
        
        # Show satellite name
        self.ax.text(self.sat_position["longitude"] + 5, self.sat_position["latitude"] + 5, 
                   self.satellite_combo.get(), fontsize=9)
        
        # Draw ground track if enabled
        if self.show_groundtrack_var.get():
            # Simulate an orbit track (simplified)
            t = time.time() / 100.0
            orbit_lons = []
            orbit_lats = []
            
            # Create points for one orbit
            for i in range(60):
                time_offset = t + i * 0.1
                orbit_lats.append(50 * math.sin(time_offset))
                orbit_lons.append((time_offset * 15) % 360 - 180)
            
            # Plot orbit
            self.ax.plot(orbit_lons, orbit_lats, 'b-', alpha=0.5)
        
        # Draw coverage area if enabled
        if self.show_coverage_var.get():
            # Simplified coverage circle (not accounting for Earth's curvature)
            coverage_radius = 20  # degrees
            coverage = plt.Circle((self.sat_position["longitude"], self.sat_position["latitude"]), 
                                coverage_radius, color='r', alpha=0.2)
            self.ax.add_patch(coverage)
        
        # Update the canvas
        self.canvas.draw()
    
    def update_position_display(self):
        """Update the position information display"""
        # Update text labels with current position data
        self.position_info_labels["Latitude:"].config(
            text=f"{self.sat_position['latitude']:.2f}°")
        
        self.position_info_labels["Longitude:"].config(
            text=f"{self.sat_position['longitude']:.2f}°")
        
        self.position_info_labels["Altitude:"].config(
            text=f"{self.sat_position['altitude']:.1f} km")
        
        self.position_info_labels["Azimuth:"].config(
            text=f"{self.sat_position['azimuth']:.1f}°")
        
        self.position_info_labels["Elevation:"].config(
            text=f"{self.sat_position['elevation']:.1f}°")
        
        self.position_info_labels["Range:"].config(
            text=f"{self.sat_position['range']:.1f} km")
        
        self.position_info_labels["Velocity:"].config(
            text=f"{self.sat_position['velocity']:.1f} km/s")
        
        self.position_info_labels["Satellite:"].config(
            text=f"{self.satellite_combo.get()}")
        
        self.position_info_labels["Updated:"].config(
            text=f"{datetime.now().strftime('%H:%M:%S')}")
    
    def shutdown(self):
        """Stop any active threads when shutting down"""
        self.stop_tracking_thread()