import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import pywinctl
import time
import json
import threading
from plyer import notification
import os
from datetime import datetime

DATA_FILE = "tracked_data.json"
LOG_FILE = "usage_log.txt"

# Load data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        tracked = json.load(f)
else:
    tracked = {}

# Ensure structure
for site in tracked:
    tracked[site].setdefault("used", 0)
    tracked[site].setdefault("log", {})
    tracked[site].setdefault("notified", False)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(tracked, f, indent=2)

def log_usage(site, seconds):
    today = datetime.now().strftime("%Y-%m-%d")
    tracked[site]["log"][today] = tracked[site]["log"].get(today, 0) + seconds

# GUI Setup
root = tk.Tk()
root.title("Website/App Usage Monitor")
root.geometry("500x500")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

site_entry = tk.Entry(frame, width=30)
site_entry.grid(row=0, column=0, padx=5)
time_entry = tk.Entry(frame, width=10)
time_entry.grid(row=0, column=1, padx=5)

def add_site():
    name = site_entry.get().strip().lower()
    try:
        limit = int(time_entry.get())
        if name:
            tracked[name] = {"limit": limit, "used": 0, "log": {}, "notified": False}
            update_list()
            save_data()
            site_entry.delete(0, tk.END)
            time_entry.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a number for the time limit.")

add_btn = tk.Button(frame, text="Add", command=add_site)
add_btn.grid(row=0, column=2, padx=5)

listbox = tk.Listbox(root, width=60)
listbox.pack(pady=10)

def update_list():
    listbox.delete(0, tk.END)
    for site, info in tracked.items():
        total_minutes = info["used"] // 60
        listbox.insert(tk.END, f"{site} - {total_minutes}m used / {info['limit']}m limit")

def remove_site():
    selection = listbox.curselection()
    if selection:
        site = list(tracked.keys())[selection[0]]
        if messagebox.askyesno("Confirm", f"Remove '{site}'?"):
            del tracked[site]
            save_data()
            update_list()

def edit_site():
    selection = listbox.curselection()
    if selection:
        site = list(tracked.keys())[selection[0]]
        new_limit = simpledialog.askinteger("Edit Limit", f"New limit for '{site}' (minutes):")
        if new_limit:
            tracked[site]["limit"] = new_limit
            tracked[site]["notified"] = False
            save_data()
            update_list()

def export_logs():
    with open(LOG_FILE, "w") as f:
        for site, info in tracked.items():
            f.write(f"{site}:\n")
            for date, seconds in info["log"].items():
                minutes = seconds // 60
                f.write(f"  {date}: {minutes} mins\n")
            f.write("\n")
    messagebox.showinfo("Exported", f"Logs saved to {LOG_FILE}")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Edit", command=edit_site).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Remove", command=remove_site).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Export Logs", command=export_logs).grid(row=0, column=2, padx=5)

def monitor():
    last_window = ""
    last_time = time.time()

    while True:
        time.sleep(1)
        try:
            win = pywinctl.getActiveWindow()
            title = win.title.lower() if win else ""
        except:
            title = ""

        now = time.time()
        elapsed = int(now - last_time)
        last_time = now

        for site in tracked:
            if site in title:
                tracked[site]["used"] += elapsed
                log_usage(site, elapsed)
                if tracked[site]["used"] // 60 >= tracked[site]["limit"]:
                    if not tracked[site]["notified"]:
                        notification.notify(
                            title="Time's up!",
                            message=f"You've used {site} for {tracked[site]['limit']} minutes.",
                            timeout=5
                        )
                        tracked[site]["notified"] = True
                break

        save_data()
        root.after(0, update_list)

# Start monitoring
threading.Thread(target=monitor, daemon=True).start()
update_list()
root.mainloop()
