# Website/App Usage Monitor

A desktop application built with Python and Tkinter that helps users track time spent on specific websites or applications. The program monitors the currently active window and logs usage, notifying users when their custom time limits are exceeded.
 
## Features

- ⏱ Track usage time for specified websites or apps
- 🔔 Get notified when time limits are reached 
- 📝 Daily usage logs with export option
- ➕ Add/edit/remove tracked items via GUI
- 💾 Data is saved persistently in JSON format
- 🧠 Works in the background using threading

## Technologies Used

- `Tkinter` – for the graphical user interface  
- `pywinctl` – to detect the currently active window  
- `plyer` – for cross-platform notifications  
- `json` & `datetime` – for data storage and time tracking  
- `threading` – to run the monitor in the background

## How to Use

1. **Add an item**  
   Enter a keyword (e.g., `youtube`, `chrome`) and a time limit in minutes.  
   The app will start tracking whenever the active window title contains the keyword.

2. **View usage**  
   The main list displays time used vs. time limit for each item.

3. **Edit or Remove**  
   Select an item in the list and click `Edit` or `Remove`.

4. **Export Logs**  
   Click `Export Logs` to save a usage report to `usage_log.txt`.

## File Structure

- `tracked_data.json` – Stores tracked sites/apps and their usage
- `usage_log.txt` – Optional exported log file

## Requirements

- Python 3.x
- Required libraries:
  ```bash
  pip install pywinctl plyer
  ```

## Notes

- Time is tracked based on active window title keywords (case-insensitive).
- Notifications are sent **once per session** when time limit is exceeded.
- Logs are grouped by date for each tracked site/app.

## License

This project is open-source and free to use.
