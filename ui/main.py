#!/usr/bin/env python3
# filepath: c:\Users\chaud\Desktop\ground-station-core\ui\main.py
import os
import sys
import json
import tkinter as tk
import ttkbootstrap as ttk
from ui.main_window import MainWindow

def load_config():
    """Load configuration from JSON file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               "config", "settings.json")
    
    # Default configuration
    config = {
        "api": {
            "host": "localhost",
            "port": 25565
        },
        "ground_station": {
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        "influxdb": {
            "url": "http://localhost:8086",
            "token": "your_token_here",
            "org": "your_org",
            "bucket": "satellite_telemetry"
        },
        "paths": {
            "influxdb": r"C:\Program Files\InfluxDB\influxd.exe" 
                        if sys.platform == "win32" else "/usr/bin/influxd",
            "grafana": r"C:\Program Files\GrafanaLabs\grafana\bin\grafana-server.exe" 
                       if sys.platform == "win32" else "/usr/sbin/grafana-server"
        }
    }
    
    # Override with values from config file if it exists
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                loaded_config = json.load(f)
                # Update recursively
                def update_dict(d, u):
                    for k, v in u.items():
                        if isinstance(v, dict):
                            d[k] = update_dict(d.get(k, {}), v)
                        else:
                            d[k] = v
                    return d
                config = update_dict(config, loaded_config)
    except Exception as e:
        print(f"Error loading config: {e}")
    
    return config

def main():
    """Main entry point for the application"""
    # Load configuration
    config = load_config()
    
    # Create the main window
    root = ttk.Window(themename="darkly")
    root.title("Satellite Ground Station")
    root.geometry("1280x800")
    
    # Create and run the application
    app = MainWindow(root, config)
    
    # Handle window closing
    def on_closing():
        app.shutdown()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()