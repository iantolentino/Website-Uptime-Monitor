import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Dict
from models.tracked_item import TrackedItem


class MainWindow:
    """Main GUI window"""
    
    def __init__(self, data_manager, monitor):
        self.data_manager = data_manager
        self.monitor = monitor
        self.root = tk.Tk()
        self.root.title("Website/App Usage Monitor")
        self.root.geometry("600x550")
        
        # Apply modern styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self._setup_ui()
        self._update_list()
        
        # Bind cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _setup_ui(self):
        """Setup UI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Add New Item", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.name_entry = ttk.Entry(input_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Limit (minutes):").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.limit_entry = ttk.Entry(input_frame, width=10)
        self.limit_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(input_frame, text="Add", command=self._add_item).grid(row=0, column=4, padx=(10, 0))
        
        # List section
        list_frame = ttk.LabelFrame(main_frame, text="Tracked Items", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for better display
        columns = ('name', 'usage', 'limit', 'status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('name', text='Name')
        self.tree.heading('usage', text='Used (min)')
        self.tree.heading('limit', text='Limit (min)')
        self.tree.heading('status', text='Status')
        
        self.tree.column('name', width=200)
        self.tree.column('usage', width=100)
        self.tree.column('limit', width=100)
        self.tree.column('status', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button section
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Edit", command=self._edit_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=self._remove_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Logs", command=self._export_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=self._update_list).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Monitoring active applications...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _add_item(self):
        """Add new tracked item"""
        name = self.name_entry.get().strip()
        try:
            limit = int(self.limit_entry.get())
            if name:
                self.data_manager.add_item(name, limit)
                self._update_list()
                self.name_entry.delete(0, tk.END)
                self.limit_entry.delete(0, tk.END)
                self.status_var.set(f"Added '{name}' with {limit} minute limit")
            else:
                messagebox.showwarning("Invalid Input", "Please enter a name")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the limit")
            
    def _remove_item(self):
        """Remove selected item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            name = item['values'][0]
            if messagebox.askyesno("Confirm", f"Remove '{name}'?"):
                self.data_manager.remove_item(name)
                self._update_list()
                self.status_var.set(f"Removed '{name}'")
                
    def _edit_item(self):
        """Edit selected item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            name = item['values'][0]
            current_limit = item['values'][2]
            
            new_limit = simpledialog.askinteger(
                "Edit Limit", 
                f"New limit for '{name}' (minutes):",
                initialvalue=current_limit
            )
            
            if new_limit:
                self.data_manager.update_item(name, new_limit)
                self._update_list()
                self.status_var.set(f"Updated '{name}' limit to {new_limit} minutes")
                
    def _export_logs(self):
        """Export usage logs"""
        from config.settings import USAGE_LOG_FILE
        messagebox.showinfo(
            "Export Complete", 
            f"Logs exported to:\n{USAGE_LOG_FILE}\n{SESSION_LOG_FILE.parent}"
        )
        
    def _update_list(self):
        """Update the items list"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add items
        for item in self.data_manager.get_all_items().values():
            status = "Active" if item.is_active else "Idle"
            if item.limit_reached:
                status = "Limit Reached!"
                
            self.tree.insert('', tk.END, values=(
                item.name,
                item.used_minutes,
                item.limit_minutes,
                status
            ))
            
        # Update status
        active_count = sum(1 for item in self.data_manager.get_all_items().values() if item.is_active)
        self.status_var.set(f"Monitoring {len(self.data_manager.get_all_items())} items ({active_count} active)")
        
    def _on_closing(self):
        """Cleanup on window close"""
        self.monitor.stop()
        self.data_manager.save_data()
        self.root.destroy()
        
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


    def _update_list(self):
        """Update the items list"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add items
        items = self.data_manager.get_all_items()
        
        if not items:
            self.tree.insert('', tk.END, values=(
                "No apps tracked yet",
                "0",
                "0",
                "Open an app to auto-detect"
            ))
        else:
            for item in items.values():
                status = "🔴 Idle"
                if item.is_active:
                    status = "🟢 Active"
                if item.limit_reached:
                    status = "⚠️ Limit Reached!"
                    
                self.tree.insert('', tk.END, values=(
                    item.name,
                    item.used_minutes,
                    item.limit_minutes,
                    status
                ))
            
        # Update status
        active_count = sum(1 for item in items.values() if item.is_active)
        self.status_var.set(f"📊 Monitoring {len(items)} apps ({active_count} active)")