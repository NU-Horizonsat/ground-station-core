import tkinter as tk
from tkinter import scrolledtext
import time
import threading
import requests
import json
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
from tkinterweb import HtmlFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from influxdb_client import InfluxDBClient, Point, WritePrecision

class SatelliteGroundStationUI:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(theme="darkly")  # Modern dark theme
        self.root.title("Satellite Ground Station")
        self.root.geometry("1280x800")
        self.connected = False
        self.telemetry_data = {"battery": [], "temperature": [], "signal": []}
        self.telemetry_times = []
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
        
        # Grafana dashboard tab
        grafana_frame = ttk.Frame(self.notebook)
        self.notebook.add(grafana_frame, text="Grafana Dashboard")
        
        # Instructions for Grafana setup
        ttk.Label(grafana_frame, text="Note: To view Grafana dashboard, make sure Grafana is running at the URL below",
                 bootstyle=INFO).pack(pady=5)
        
        # Frame for Grafana dashboard (using tkinterweb)
        self.grafana_view = HtmlFrame(grafana_frame)
        self.grafana_url = "http://localhost:3000/d/satellite/satellite-telemetry"  # Replace with your dashboard URL
        self.grafana_view.load_website(self.grafana_url)
        self.grafana_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Refresh button for Grafana
        ttk.Button(grafana_frame, text="Refresh Dashboard", 
                  bootstyle=INFO, command=lambda: self.grafana_view.load_website(self.grafana_url)).pack(pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize parameter display
        self.update_parameters()
        
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

def main():
    root = ttk.Window()
    app = SatelliteGroundStationUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()