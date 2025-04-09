import os
import sys
import time
import subprocess
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
from tkinterweb import HtmlFrame

class ServicesPanel:
    def __init__(self, notebook, config, on_log):
        self.notebook = notebook
        self.config = config
        self.log_message = on_log
        
        # Service process tracking
        self.influxdb_process = None
        self.grafana_process = None
        self.service_check_active = True
        
        self.create_panel()
        
    def create_panel(self):
        # Create frame
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Services")
        
        # Create Grafana tab within services panel
        self.create_grafana_tab()
        
    def create_grafana_tab(self):
        """Create the Grafana dashboard tab"""
        grafana_frame = ttk.Frame(self.frame)
        grafana_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        self.influxdb_path.insert(0, self.config["paths"]["influxdb"])
        self.influxdb_path.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(config_frame, text="Browse", command=lambda: self.browse_file("influxdb")).grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Grafana Path:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.grafana_path = ttk.Entry(config_frame, width=40)
        self.grafana_path.insert(0, self.config["paths"]["grafana"])
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
    
    def browse_file(self, service_type):
        """Browse for executable file"""
        file_path = filedialog.askopenfilename(
            title=f"Select {service_type.capitalize()} Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")] if sys.platform == "win32" 
                     else [("All files", "*")]
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
        influxdb_running = self.is_service_running(self.influxdb_process, "influxd")
        if influxdb_running:
            self.influxdb_status.config(text="Running", bootstyle="inverse-success")
            self.start_influxdb_btn.config(state=tk.DISABLED)
            self.stop_influxdb_btn.config(state=tk.NORMAL)
        else:
            self.influxdb_status.config(text="Stopped", bootstyle="inverse-danger")
            self.start_influxdb_btn.config(state=tk.NORMAL)
            self.stop_influxdb_btn.config(state=tk.DISABLED)
            
        # Check Grafana
        grafana_running = self.is_service_running(self.grafana_process, "grafana-server")
        if grafana_running:
            self.grafana_status.config(text="Running", bootstyle="inverse-success")
            self.start_grafana_btn.config(state=tk.DISABLED)
            self.stop_grafana_btn.config(state=tk.NORMAL)
        else:
            self.grafana_status.config(text="Stopped", bootstyle="inverse-danger")
            self.start_grafana_btn.config(state=tk.NORMAL)
            self.stop_grafana_btn.config(state=tk.DISABLED)
        
        # Schedule next check
        self.notebook.after(5000, self.check_service_status)  # Check every 5 seconds
    
    def is_service_running(self, process, process_name):
        """Check if a service is running by process name"""
        # First check our own process
        if process and process.poll() is None:
            return True
            
        # On Windows, check using tasklist
        if sys.platform == "win32":
            proc = subprocess.Popen(["tasklist"], stdout=subprocess.PIPE)
            for line in proc.stdout:
                if process_name in str(line):
                    return True
        # On Unix, check using ps
        else:
            proc = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
            for line in proc.stdout:
                if process_name in str(line) and "grep" not in str(line):
                    return True
                    
        return False
    
    def start_influxdb(self):
        """Start the InfluxDB service"""
        if self.is_service_running(self.influxdb_process, "influxd"):
            return  # Already running
            
        try:
            # Get path from UI
            influxdb_path = self.influxdb_path.get()
            
            # Validate path exists
            if not os.path.exists(influxdb_path):
                ttk.messagebox.showerror("Error", f"InfluxDB executable not found at:\n{influxdb_path}")
                return
                
            # Start process
            self.log_message("Starting InfluxDB service...")
            
            # Create subprocess with appropriate flags based on platform
            if sys.platform == "win32":
                self.influxdb_process = subprocess.Popen([influxdb_path], 
                                                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.influxdb_process = subprocess.Popen([influxdb_path],
                                                    stdout=subprocess.DEVNULL,
                                                    stderr=subprocess.DEVNULL)
            
            # Update UI
            self.influxdb_status.config(text="Starting...", bootstyle="inverse-warning")
            self.notebook.after(5000, self.check_service_status)  # Check status after 5 seconds
            
        except Exception as e:
            ttk.messagebox.showerror("Error", f"Failed to start InfluxDB: {e}")
    
    def stop_influxdb(self):
        """Stop the InfluxDB service"""
        if not self.is_service_running(self.influxdb_process, "influxd"):
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
                # Try to kill the process by name
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/IM", "influxd.exe"], 
                                creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["killall", "influxd"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            
            # Update UI
            self.influxdb_status.config(text="Stopping...", bootstyle="inverse-warning")
            self.notebook.after(2000, self.check_service_status)  # Check status after 2 seconds
            
        except Exception as e:
            ttk.messagebox.showerror("Error", f"Failed to stop InfluxDB: {e}")
    
    def start_grafana(self):
        """Start the Grafana service"""
        if self.is_service_running(self.grafana_process, "grafana-server"):
            return  # Already running
            
        try:
            # Get path from UI
            grafana_path = self.grafana_path.get()
            
            # Validate path exists
            if not os.path.exists(grafana_path):
                ttk.messagebox.showerror("Error", f"Grafana executable not found at:\n{grafana_path}")
                return
                
            # Start process
            self.log_message("Starting Grafana service...")
            
            # Create subprocess with appropriate flags based on platform
            if sys.platform == "win32":
                self.grafana_process = subprocess.Popen([grafana_path], 
                                                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.grafana_process = subprocess.Popen([grafana_path],
                                                    stdout=subprocess.DEVNULL,
                                                    stderr=subprocess.DEVNULL)
            
            # Update UI
            self.grafana_status.config(text="Starting...", bootstyle="inverse-warning")
            self.notebook.after(5000, self.check_service_status)  # Check status after 5 seconds
            
        except Exception as e:
            ttk.messagebox.showerror("Error", f"Failed to start Grafana: {e}")
    
    def stop_grafana(self):
        """Stop the Grafana service"""
        if not self.is_service_running(self.grafana_process, "grafana-server"):
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
                # Try to kill the process by name
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/IM", "grafana-server.exe"], 
                                creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["killall", "grafana-server"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            
            # Update UI
            self.grafana_status.config(text="Stopping...", bootstyle="inverse-warning")
            self.notebook.after(2000, self.check_service_status)  # Check status after 2 seconds
            
        except Exception as e:
            ttk.messagebox.showerror("Error", f"Failed to stop Grafana: {e}")
    
    def stop_all_services(self):
        """Stop all services during shutdown"""
        self.service_check_active = False
        
        if self.influxdb_process and self.influxdb_process.poll() is None:
            self.influxdb_process.terminate()
            try:
                self.influxdb_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.influxdb_process.kill()
        
        if self.grafana_process and self.grafana_process.poll() is None:
            self.grafana_process.terminate()
            try:
                self.grafana_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.grafana_process.kill()