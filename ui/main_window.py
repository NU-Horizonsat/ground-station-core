import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from command_panel import CommandPanel
from telemetry_panel import TelemetryPanel
from schedule_panel import SchedulePanel
from pass_panel import PassPanel
from position_panel import PositionPanel
from services_panel import ServicesPanel
from gsclient import GroundStationClient

class MainWindow:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.connected = False
        
        # Initialize the API client
        self.api_client = GroundStationClient(
            host=config["api"]["host"],
            port=config["api"]["port"]
        )
        
        self.create_ui()
        
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
        
        # Connection controls
        self.create_connection_panel(left_frame)
        
        # Command panel
        self.command_panel = CommandPanel(
            parent=left_frame, 
            api_client=self.api_client,
            on_log=self.log_message
        )
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(right_frame, bootstyle=DARK)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add log panel
        self.create_log_panel()
        
        # Add telemetry panel
        self.telemetry_panel = TelemetryPanel(
            notebook=self.notebook,
            api_client=self.api_client,
            config=self.config["influxdb"]
        )
        
        # Add schedule panel
        self.schedule_panel = SchedulePanel(
            notebook=self.notebook,
            api_client=self.api_client,
            on_log=self.log_message
        )
        
        # Add pass tracking panel
        self.pass_panel = PassPanel(
            notebook=self.notebook,
            api_client=self.api_client,
            on_log=self.log_message,
            config=self.config["ground_station"]
        )
        
        # Add position tracking panel
        self.position_panel = PositionPanel(
            notebook=self.notebook,
            api_client=self.api_client,
            on_log=self.log_message
        )
        
        # Add services panel
        self.services_panel = ServicesPanel(
            notebook=self.notebook,
            config=self.config,
            on_log=self.log_message
        )
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_connection_panel(self, parent):
        conn_frame = ttk.LabelFrame(parent, text="Connection", bootstyle=INFO)
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
    
    def create_log_panel(self):
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Command Log")
        
        self.log_display = ttk.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def log_message(self, message):
        """Log a message to the log display"""
        self.log_display.insert(tk.END, f"{message}\n")
        self.log_display.see(tk.END)
        
    def connect(self):
        """Connect to ground station"""
        self.log_message("Connecting to ground station...")
        self.status_bar.config(text="Connecting...")
        
        # Use a thread to avoid blocking the UI
        def connection_thread():
            success, data = self.api_client.connect()
            if success:
                # Update UI in thread-safe way
                self.root.after(0, self.connection_success, data)
            else:
                # Show error in thread-safe way
                self.root.after(0, self.connection_failure, data)
        
        import threading
        threading.Thread(target=connection_thread, daemon=True).start()
    
    def connection_success(self, data):
        """Handle successful connection"""
        self.connected = True
        self.status_label.config(text="Status: Connected", bootstyle="inverse-success")
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.command_panel.enable_commands()
        self.status_bar.config(text="Connected to ground station")
        
        self.log_message("Connection established")
        self.log_message(f"Ground station status: {data}")
        
        # Start telemetry polling
        self.telemetry_panel.start_polling()
    
    def connection_failure(self, error_message):
        """Handle connection failure"""
        self.connected = False
        self.status_label.config(text="Status: Connection Failed", bootstyle="inverse-danger")
        self.status_bar.config(text=f"Connection failed: {error_message}")
        self.log_message(f"Connection failed: {error_message}")
        ttk.messagebox.showerror("Connection Failed", f"Could not connect to ground station:\n{error_message}")
    
    def disconnect(self):
        """Disconnect from ground station"""
        success, message = self.api_client.disconnect()
        
        self.connected = False
        self.status_label.config(text="Status: Disconnected", bootstyle="inverse-danger")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.command_panel.disable_commands()
        self.telemetry_panel.stop_polling()
        self.status_bar.config(text="Disconnected from ground station")
        self.log_message("Connection closed")
    
    def shutdown(self):
        """Perform cleanup before shutdown"""
        if self.connected:
            self.api_client.disconnect()
        
        # Stop all services
        self.services_panel.stop_all_services()