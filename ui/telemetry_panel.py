import time
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from influxdb_client import InfluxDBClient, Point, WritePrecision
from datetime import datetime

class TelemetryPanel:
    def __init__(self, notebook, api_client, config):
        self.notebook = notebook
        self.api_client = api_client
        self.influxdb_url = config["url"]
        self.influxdb_token = config["token"]
        self.influxdb_org = config["org"]
        self.influxdb_bucket = config["bucket"]
        
        # Data storage
        self.telemetry_times = []
        self.telemetry_data = {"battery": [], "temperature": [], "signal": []}
        
        # Control flag for polling thread
        self.polling_active = False
        self.polling_thread = None
        
        self.create_panel()
    
    def create_panel(self):
        # Create frame
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Telemetry")
        
        # Split into two sections
        left_panel = ttk.Frame(self.frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_panel = ttk.Frame(self.frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Telemetry display (left)
        self.telemetry_display = ttk.ScrolledText(left_panel, wrap=tk.WORD)
        self.telemetry_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visualization (right)
        # Create a figure for the plots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(6, 8))
        self.fig.tight_layout(pad=3.0)
        
        # Create canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_telemetry(self, data):
        """Update the telemetry display with new data"""
        self.telemetry_display.insert(tk.END, data + "\n")
        self.telemetry_display.see(tk.END)
    
    def update_plots(self):
        """Update the plots with current data"""
        # Clear the axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        # Plot the data
        self.ax1.plot(self.telemetry_times, self.telemetry_data["battery"])
        self.ax1.set_ylabel("Battery (%)")
        self.ax1.set_title("Battery Level")
        self.ax1.grid(True)
        
        self.ax2.plot(self.telemetry_times, self.telemetry_data["temperature"])
        self.ax2.set_ylabel("Temperature (°C)")
        self.ax2.set_title("Temperature")
        self.ax2.grid(True)
        
        self.ax3.plot(self.telemetry_times, self.telemetry_data["signal"])
        self.ax3.set_ylabel("Signal (dBm)")
        self.ax3.set_title("Signal Strength")
        self.ax3.set_xlabel("Time")
        self.ax3.grid(True)
        
        # Adjust x-axis labels
        for ax in [self.ax1, self.ax2, self.ax3]:
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        
        # Update the canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def update_telemetry_from_response(self, response):
        """Update telemetry displays and data structures from API response"""
        try:
            # Extract relevant values - adjust based on actual API response structure
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract values from the response - adjust these paths based on actual API response
            battery = response.get("battery", {}).get("percentage", 90)  # Default to 90 if not found
            temp = response.get("temperature", 20)  # Default to 20 if not found
            signal = response.get("signal", {}).get("strength", -60)  # Default to -60 if not found
            
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
            
            # Update telemetry text display
            telemetry_text = f"[{timestamp}] Battery: {battery}%, Temperature: {temp}°C, Signal: {signal} dBm"
            self.update_telemetry(telemetry_text)
            
            # Write to InfluxDB if possible
            try:
                client = InfluxDBClient(url=self.influxdb_url, token=self.influxdb_token, org=self.influxdb_org)
                write_api = client.write_api()
                
                point = Point("satellite_telemetry") \
                    .tag("satellite", "sat1") \
                    .field("battery", float(battery)) \
                    .field("temperature", float(temp)) \
                    .field("signal", float(signal)) \
                    .time(datetime.utcnow(), WritePrecision.NS)
                
                write_api.write(bucket=self.influxdb_bucket, record=point)
            except Exception as e:
                print(f"Error writing to InfluxDB: {e}")
                
        except Exception as e:
            print(f"Error updating telemetry: {e}")
    
    def start_polling(self):
        """Start polling for telemetry data from the backend"""
        if self.polling_active:
            return
        
        self.polling_active = True
        
        def telemetry_thread():
            poll_interval = 2  # seconds
            
            while self.polling_active:
                # Poll for status data
                success, response = self.api_client.get_status()
                
                if success and isinstance(response, dict):
                    # Extract telemetry from the response
                    self.notebook.after(0, self.update_telemetry_from_response, response)
                
                time.sleep(poll_interval)
        
        self.polling_thread = threading.Thread(target=telemetry_thread, daemon=True)
        self.polling_thread.start()
    
    def stop_polling(self):
        """Stop polling for telemetry data"""
        self.polling_active = False
        if self.polling_thread:
            self.polling_thread.join(timeout=1.0)
            self.polling_thread = None