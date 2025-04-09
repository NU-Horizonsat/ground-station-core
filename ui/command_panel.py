import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import threading

class CommandPanel:
    """Panel for sending commands to the satellite"""
    
    def __init__(self, parent, api_client, on_log):
        self.parent = parent
        self.api_client = api_client
        self.log_message = on_log
        self.param_widgets = []
        
        self.create_panel()
        
    def create_panel(self):
        """Create the command panel UI elements"""
        # Command selection section
        cmd_frame = ttk.LabelFrame(self.parent, text="Command Selection", bootstyle=WARNING)
        cmd_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        
        ttk.Label(cmd_frame, text="Command Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cmd_type = ttk.Combobox(cmd_frame, values=[
            "Telemetry Request", 
            "Attitude Adjustment", 
            "Power Cycle", 
            "Data Download",
            "System Reset",
            "Antenna Calibration"
        ])
        self.cmd_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.cmd_type.current(0)
        self.cmd_type.bind("<<ComboboxSelected>>", self.update_parameters)
        
        # Parameters section
        self.param_frame = ttk.LabelFrame(cmd_frame, text="Parameters", bootstyle=INFO)
        self.param_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        # Will be populated by update_parameters()
        
        # Send command button
        self.send_btn = ttk.Button(cmd_frame, text="Send Command", bootstyle=SUCCESS,
                                  command=self.send_command, state=tk.DISABLED)
        self.send_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky=tk.EW)
        
        # Make rows and columns expandable
        cmd_frame.columnconfigure(1, weight=1)
        cmd_frame.rowconfigure(1, weight=1)
        
        # Initialize parameter display
        self.update_parameters()
    
    def enable_commands(self):
        """Enable command sending (called after connection)"""
        self.send_btn.config(state=tk.NORMAL)
    
    def disable_commands(self):
        """Disable command sending (called after disconnection)"""
        self.send_btn.config(state=tk.DISABLED)
    
    def update_parameters(self, event=None):
        """Update parameter fields based on selected command"""
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
            
        elif cmd == "Data Download":
            label = ttk.Label(self.param_frame, text="Data Type:")
            label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(label)
            
            data_type = ttk.Combobox(self.param_frame, values=["Telemetry Log", "Science Data", "Images", "System Log"])
            data_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
            data_type.current(0)
            self.param_widgets.append(data_type)
            
            time_label = ttk.Label(self.param_frame, text="Time Period:")
            time_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(time_label)
            
            time_period = ttk.Combobox(self.param_frame, values=["Last Hour", "Last Day", "Last Week", "All Available"])
            time_period.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
            time_period.current(0)
            self.param_widgets.append(time_period)
            
        elif cmd == "System Reset":
            label = ttk.Label(self.param_frame, text="Reset Type:")
            label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(label)
            
            reset_type = ttk.Combobox(self.param_frame, values=["Soft Reset", "Hard Reset", "Factory Reset"])
            reset_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
            reset_type.current(0)
            self.param_widgets.append(reset_type)
            
            confirm_label = ttk.Label(self.param_frame, text="Confirmation:")
            confirm_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(confirm_label)
            
            self.confirm_var = tk.BooleanVar(value=False)
            confirm_check = ttk.Checkbutton(self.param_frame, text="I confirm this action", 
                                          variable=self.confirm_var)
            confirm_check.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(confirm_check)
            
        elif cmd == "Antenna Calibration":
            label = ttk.Label(self.param_frame, text="Calibration Type:")
            label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(label)
            
            self.azimuth_var = tk.BooleanVar(value=True)
            azimuth_check = ttk.Checkbutton(self.param_frame, text="Azimuth", 
                                          variable=self.azimuth_var)
            azimuth_check.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(azimuth_check)
            
            self.elevation_var = tk.BooleanVar(value=True)
            elevation_check = ttk.Checkbutton(self.param_frame, text="Elevation", 
                                            variable=self.elevation_var)
            elevation_check.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            self.param_widgets.append(elevation_check)
            
        # Configure grid weights
        self.param_frame.columnconfigure(1, weight=1)
    
    def send_command(self):
        """Send command to the ground station"""
        command = self.cmd_type.get()
        self.log_message(f"Sending command: {command}")
        
        # Create command payload based on command type
        payload = self.create_command_payload(command)
        if not payload:
            return
        
        # Use thread for API call to keep UI responsive
        def command_thread():
            if command == "Telemetry Request":
                success, response = self.api_client.get_status()
            elif command == "Attitude Adjustment":
                success, response = self.api_client.set_antenna_position(payload)
            elif command == "Antenna Calibration":
                success, response = self.api_client.start_calibration(
                    azimuth=self.azimuth_var.get(), 
                    elevation=self.elevation_var.get()
                )
            elif command == "Power Cycle":
                # Placeholder - not directly mappable to current API
                success, response = True, "Command simulated (no direct API endpoint)"
            elif command == "Data Download":
                # Placeholder - not directly mappable to current API
                success, response = True, "Command simulated (no direct API endpoint)"
            elif command == "System Reset":
                # Placeholder - not directly mappable to current API
                if not self.confirm_var.get():
                    success, response = False, "Reset not confirmed - please check confirmation box"
                else:
                    success, response = True, "System reset command simulated (no direct API endpoint)"
            else:
                success, response = False, f"Unknown command: {command}"
            
            if success:
                self.command_success(command, response)
            else:
                self.command_failure(command, response)
        
        threading.Thread(target=command_thread, daemon=True).start()
    
    def create_command_payload(self, command):
        """Create the appropriate payload based on command type"""
        try:
            if command == "Telemetry Request":
                # No payload needed for status request
                return {}
                
            elif command == "Attitude Adjustment":
                # Get parameters from UI
                params = {}
                for widget in self.param_widgets:
                    if isinstance(widget, ttk.Entry):
                        # Find the label for this entry
                        label_text = ""
                        for w in self.param_widgets:
                            if isinstance(w, ttk.Label) and w.grid_info()["row"] == widget.grid_info()["row"]:
                                label_text = w.cget("text").replace(" (deg):", "").lower()
                                break
                        
                        if label_text:
                            try:
                                params[label_text] = float(widget.get())
                            except ValueError:
                                ttk.messagebox.showerror("Input Error", f"Invalid value for {label_text}")
                                return None
                
                # Create the antenna position payload
                return {
                    "antenna": {
                        "azimuth": params.get("roll", 0),  # Map roll to azimuth
                        "elevation": params.get("pitch", 0)  # Map pitch to elevation
                    }
                }
                
            elif command == "Power Cycle" or command == "Data Download" or command == "System Reset":
                # These commands don't map directly to REST API endpoints
                # For now, we'll return a placeholder payload
                return {"command": command.lower().replace(" ", "_")}
                
            # Add more command payload handlers as needed
            
            return {}
        
        except Exception as e:
            ttk.messagebox.showerror("Error", f"Failed to create command payload: {str(e)}")
            return None
    
    def command_success(self, command, response):
        """Handle successful command execution"""
        if isinstance(response, dict):
            response_text = json.dumps(response, indent=2)
        else:
            response_text = str(response)
        
        self.log_message(f"Command successful: {command}")
        self.log_message(f"Response: {response_text}")

    def command_failure(self, command, error_message):
        """Handle command execution failure"""
        self.log_message(f"Command failed: {command}")
        self.log_message(f"Error: {error_message}")
        ttk.messagebox.showerror("Command Failed", f"Error executing {command}:\n{error_message}")