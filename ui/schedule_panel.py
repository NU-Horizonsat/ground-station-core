import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, timedelta
import threading
import time
import json

class SchedulePanel:
    """Panel for scheduling commands to be executed at specific times"""
    
    def __init__(self, notebook, api_client, on_log):
        self.notebook = notebook
        self.api_client = api_client
        self.log_message = on_log
        
        # Store scheduled commands
        self.scheduled_commands = []
        self.command_checker_active = True
        
        self.create_panel()
        
        # Start the command checker
        self.check_scheduled_commands()
    
    def create_panel(self):
        """Create the schedule panel UI"""
        # Create the main frame
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Schedule Commands")
        
        # Split the frame into two sections
        left_panel = ttk.Frame(self.frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_panel = ttk.Frame(self.frame)
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

        # Add sample data for demonstration
        self.schedule_tree.insert("", tk.END, values=("1", "2025-03-27 08:00:00", "Telemetry Request", "Subsystem: Power", "Once", "Pending"))
        self.schedule_tree.insert("", tk.END, values=("2", "2025-03-27 12:30:00", "Attitude Adjustment", "Roll: 5°, Pitch: 0°, Yaw: 2°", "Daily", "Pending"))
    
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
            # In a real implementation, you would gather these from input fields
            parameters = "Roll: 5°, Pitch: 0°, Yaw: 2°"
        elif command == "Power Cycle":
            # Placeholder
            parameters = "Component: Radio, Delay: 5s"
        elif command == "Data Download":
            parameters = "Type: Telemetry Log, Period: Last Hour"
        elif command == "System Reset":
            parameters = "Type: Soft Reset"
            
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
    
    def edit_scheduled_command(self):
        """Edit the selected scheduled command"""
        selected = self.schedule_tree.selection()
        if not selected:
            return
            
        # Get the command values
        values = self.schedule_tree.item(selected[0], "values")
        cmd_id = values[0]
        
        # Show message
        ttk.messagebox.showinfo("Edit Command", 
                               f"Editing command #{cmd_id} is not fully implemented.\n\n"
                               f"In a complete implementation, this would open an editor dialog "
                               f"to modify the command parameters and execution time.")
        
        self.log_message(f"Edited scheduled command #{cmd_id}")
    
    def check_scheduled_commands(self):
        """Check for commands that need to be executed"""
        if not self.command_checker_active:
            return
            
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
        self.notebook.after(1000, self.check_scheduled_commands)
    
    def execute_scheduled_command(self, cmd):
        """Execute a scheduled command"""
        self.log_message(f"Executing scheduled command: {cmd['command']}")
        
        # In a real implementation, this would send the command to the satellite
        # For demonstration, we'll just log it
        self.log_message(f"Command executed: {cmd['command']} with parameters: {cmd['parameters']}")
    
    def reschedule_command(self, cmd, delta):
        """Reschedule a recurring command"""
        # Parse the current time
        current_time = datetime.strptime(cmd["time"], "%Y-%m-%d %H:%M:%S")
        
        # Calculate the new time
        new_time = current_time + delta
        new_time_str = new_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a new command entry
        new_cmd = cmd.copy()
        new_cmd["id"] = len(self.scheduled_commands) + 1
        new_cmd["time"] = new_time_str
        new_cmd["status"] = "Pending"
        
        # Add to the list of scheduled commands
        self.scheduled_commands.append(new_cmd)
        
        # Add to treeview
        self.schedule_tree.insert("", tk.END, values=(
            new_cmd["id"],
            new_cmd["time"],
            new_cmd["command"],
            new_cmd["parameters"],
            new_cmd["recurrence"],
            new_cmd["status"]
        ))
        
        self.log_message(f"Rescheduled {cmd['command']} for {new_time_str}")
    
    def shutdown(self):
        """Stop the command checker when shutting down"""
        self.command_checker_active = False