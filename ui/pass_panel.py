import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Querybox
from datetime import datetime, timedelta
import threading
import time
import random

class PassPanel:
    """Panel for displaying and tracking satellite passes"""
    
    def __init__(self, notebook, api_client, on_log, config):
        self.notebook = notebook
        self.api_client = api_client
        self.log_message = on_log
        self.config = config  # Ground station location info
        
        # Satellite pass data
        self.passes = []
        
        self.create_panel()
    
    def create_panel(self):
        """Create the pass panel UI"""
        # Create the main frame
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Satellite Passes")
        
        # Top controls
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ground station info
        gs_frame = ttk.LabelFrame(control_frame, text="Ground Station Location", bootstyle=INFO)
        gs_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        ttk.Label(gs_frame, text=f"Latitude: {self.config['latitude']}°").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(gs_frame, text=f"Longitude: {self.config['longitude']}°").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(gs_frame, text="Elevation: 10m").pack(side=tk.LEFT, padx=10, pady=5)
        
        # Prediction controls
        pred_frame = ttk.LabelFrame(control_frame, text="Pass Prediction", bootstyle=PRIMARY)
        pred_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5, pady=5)
        
        ttk.Label(pred_frame, text="Satellite:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.satellite_var = ttk.Combobox(pred_frame, values=["All", "ISS (ZARYA)", "NOAA-19", "METEOR-M2"])
        self.satellite_var.pack(side=tk.LEFT, padx=5, pady=5)
        self.satellite_var.current(0)
        
        ttk.Label(pred_frame, text="Days:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.days_var = ttk.Spinbox(pred_frame, from_=1, to=30, width=3)
        self.days_var.pack(side=tk.LEFT, padx=5, pady=5)
        self.days_var.set("7")
        
        ttk.Button(pred_frame, text="Predict Passes", bootstyle=SUCCESS, 
                  command=self.calculate_passes).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Pass table
        pass_frame = ttk.LabelFrame(self.frame, text="Upcoming Satellite Passes", bootstyle=WARNING)
        pass_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for passes
        columns = ("aos", "los", "duration", "max_el", "direction", "satellite", "status")
        self.pass_tree = ttk.Treeview(pass_frame, columns=columns, show="headings")
        
        # Define headings
        self.pass_tree.heading("aos", text="AOS Time")
        self.pass_tree.heading("los", text="LOS Time")
        self.pass_tree.heading("duration", text="Duration")
        self.pass_tree.heading("max_el", text="Max Elev.")
        self.pass_tree.heading("direction", text="Direction")
        self.pass_tree.heading("satellite", text="Satellite")
        self.pass_tree.heading("status", text="Status")
        
        # Define columns
        self.pass_tree.column("aos", width=150)
        self.pass_tree.column("los", width=150)
        self.pass_tree.column("duration", width=80)
        self.pass_tree.column("max_el", width=80)
        self.pass_tree.column("direction", width=80)
        self.pass_tree.column("satellite", width=150)
        self.pass_tree.column("status", width=80)
        
        # Add scrollbar
        pass_scroll = ttk.Scrollbar(pass_frame, orient=tk.VERTICAL, command=self.pass_tree.yview)
        self.pass_tree.configure(yscrollcommand=pass_scroll.set)
        
        # Pack widgets
        self.pass_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pass_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(self.frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Schedule Auto-Tracking", 
                 bootstyle=INFO, command=self.schedule_tracking).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Export Pass List", 
                 bootstyle=WARNING, command=self.export_pass_list).pack(side=tk.LEFT, padx=5)
        
        # Load initial pass data
        self.calculate_passes()
    
    def calculate_passes(self):
        """Calculate satellite passes for the given number of days"""
        self.log_message("Calculating satellite passes...")
        satellite = self.satellite_var.get()
        days = int(self.days_var.get())
        
        # Clear existing data
        for item in self.pass_tree.get_children():
            self.pass_tree.delete(item)
        
        self.passes = []
        
        # Use a separate thread to avoid blocking the UI
        def calculation_thread():
            # This is a simulation - in a real application, this would use orbital mechanics
            # to calculate actual passes based on TLEs and ground station location
            
            # For demo purposes, generate some random passes
            satellites = ["ISS (ZARYA)", "NOAA-19", "METEOR-M2"]
            if satellite != "All":
                satellites = [satellite]
                
            now = datetime.now()
            for day in range(days):
                for sat in satellites:
                    # Generate 1-3 random passes per day per satellite
                    for _ in range(random.randint(1, 3)):
                        # Random time on this day
                        hour = random.randint(0, 23)
                        minute = random.randint(0, 59)
                        pass_date = now + timedelta(days=day)
                        aos_time = pass_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # Duration between 5 and 15 minutes
                        duration_minutes = random.randint(5, 15)
                        los_time = aos_time + timedelta(minutes=duration_minutes)
                        
                        # Max elevation between 5 and 85 degrees
                        max_el = random.randint(5, 85)
                        
                        # Direction
                        directions = ["N->S", "S->N", "E->W", "W->E"]
                        direction = random.choice(directions)
                        
                        # Status (all upcoming at this point)
                        status = "Upcoming"
                        
                        # Add to list
                        self.passes.append({
                            "aos": aos_time,
                            "los": los_time,
                            "duration": duration_minutes,
                            "max_el": max_el,
                            "direction": direction,
                            "satellite": sat,
                            "status": status
                        })
            
            # Sort by AOS time
            self.passes.sort(key=lambda x: x["aos"])
            
            # Update UI in thread-safe way
            self.notebook.after(0, self.update_pass_list)
        
        threading.Thread(target=calculation_thread, daemon=True).start()
    
    def update_pass_list(self):
        """Update the pass list treeview with the calculated passes"""
        # Clear existing items
        for item in self.pass_tree.get_children():
            self.pass_tree.delete(item)
        
        # Add passes to treeview
        for pass_data in self.passes:
            aos_str = pass_data["aos"].strftime("%Y-%m-%d %H:%M:%S")
            los_str = pass_data["los"].strftime("%Y-%m-%d %H:%M:%S")
            
            self.pass_tree.insert("", tk.END, values=(
                aos_str,
                los_str,
                f"{pass_data['duration']} min",
                f"{pass_data['max_el']}°",
                pass_data["direction"],
                pass_data["satellite"],
                pass_data["status"]
            ))
        
        self.log_message(f"Found {len(self.passes)} satellite passes for the next {self.days_var.get()} days")
    
    def schedule_tracking(self):
        """Schedule automatic tracking for selected pass"""
        selected = self.pass_tree.selection()
        if not selected:
            ttk.messagebox.showinfo("Selection Required", "Please select a pass to schedule tracking")
            return
            
        # Get pass information
        values = self.pass_tree.item(selected[0], "values")
        aos_time = values[0]
        satellite = values[5]
        
        # Confirm with user
        if ttk.messagebox.askyesno("Schedule Tracking", 
                                  f"Schedule automatic tracking for {satellite} starting at {aos_time}?"):
            self.log_message(f"Scheduled automatic tracking for {satellite} at {aos_time}")
    
    def export_pass_list(self):
        """Export the pass list to a file"""
        # In a real implementation, this would save to a file
        ttk.messagebox.showinfo("Export Pass List", 
                               "In a complete implementation, this would export the pass list to a file "
                               "in CSV or other format.")
        self.log_message("Pass list exported")