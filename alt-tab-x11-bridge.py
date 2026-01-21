import subprocess
import time
import tkinter as tk
from functools import partial
import os # Needed to get the process ID of the script

# Dictionary to map X11 Window IDs (str) to Tkinter Toplevel instances
active_cocoa_windows = {}
root = tk.Tk()
root.withdraw() # Hide the main (empty) Tkinter root window

# Get the script's own Process ID (PID)
OWN_PID = os.getpid()
print(f"My Python script has PID: {OWN_PID}")

# Global variable to track the last active macOS app PID
last_active_os_pid = None

# Global variable to track the last focused X11 window ID
last_active_window_id = None

def get_active_app_pid():
    """Queries macOS for the Process ID (PID) of the currently active application."""
    # AppleScript command: 'tell app "System Events" to get unix id of first process whose frontmost is true'
    cmd = ["osascript", "-e", 'tell app "System Events" to get unix id of first process whose frontmost is true']
    try:
        pid_str = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        return int(pid_str)
    except subprocess.CalledProcessError:
        return None
    except ValueError: # if osascript does not return a number
        return None
    except FileNotFoundError:
        print("Error: 'osascript' not found. This functionality only works on macOS.")
        return None

def get_current_window_info():
    """Calls wmctrl -l and returns a dictionary of {ID: Title}."""
    try:
        output = subprocess.check_output(["wmctrl", "-l"], stderr=subprocess.STDOUT, text=True)
        lines = output.strip().splitlines()
        window_info = {}
        for line in lines:
            if line:
                # Split the line: ID, Desktop, Machine, Title
                parts = line.split(None, 3)
                if len(parts) == 4:
                    # Correction: Use correct indices to get string values (parts[0] and parts[3])
                    window_id = parts[0]
                    window_title = parts[3]
                    window_info[window_id] = window_title
        return window_info
    except FileNotFoundError:
        print("Error: 'wmctrl' command not found. Please install this.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing wmctrl: {e.output}")
        exit(1)

def set_x11_focus(window_id, event=None):
    global last_active_window_id
    """Sets focus to the X11 window using its ID and wmctrl."""
    print(f"[FOCUS REQUEST] Focusing X11-ID: {window_id}")
    if (window_id is None):
        print("window id is None!")
        return
    # Update the last active window ID for external app switching logic
    last_active_window_id = window_id
    try:
        # wmctrl -i -a <ID> is the standard method
        subprocess.run(["wmctrl", "-i", "-a", window_id], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Optional: Bring XQuartz to the foreground at the macOS app level
        subprocess.run(["osascript", "-e", 'tell application "XQuartz" to activate'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except subprocess.CalledProcessError as e:
        print(f"Error setting focus for {window_id}: {e}")

def update_windows_status(previous_info, current_info):
    """Checks for changes and updates the Cocoa (Tkinter) GUI."""
    current_ids = set(current_info.keys())
    previous_ids = set(previous_info.keys())

    added_windows_ids = current_ids - previous_ids
    closed_windows_ids = previous_ids - current_ids

    for window_id in added_windows_ids:
        title = current_info[window_id]
        print(f"[NEW X11] ID: {window_id} Title: '{title}'. Creating Cocoa window.")
        create_cocoa_window(window_id, title)

    for window_id in closed_windows_ids:
        print(f"[CLOSED X11] ID: {window_id}. Destroying Cocoa window.")
        destroy_cocoa_window(window_id)

    return current_info

def create_cocoa_window(window_id, title):
    """Creates a new Tkinter Toplevel window with a focus binding."""
    if window_id not in active_cocoa_windows:
        toplevel = tk.Toplevel(root)
        toplevel.title(f"X11 Monitor: {title}")
        toplevel.geometry("300x100")

        label = tk.Label(toplevel, text=f"Monitoring X11 Window:\n{title}", padx=10, pady=10)
        label.pack()

        active_cocoa_windows[window_id] = toplevel

        # Binding for internal focus change within the Python app
        toplevel.bind("<FocusIn>", partial(set_x11_focus, window_id))

        toplevel.protocol("WM_DELETE_WINDOW", lambda id=window_id: destroy_cocoa_window(id))


def destroy_cocoa_window(window_id):
    """Destroys the Tkinter window and removes it from tracking."""
    if window_id in active_cocoa_windows:
        window = active_cocoa_windows.pop(window_id)
        window.destroy()

def main_loop():
    """The main monitoring loop that checks periodically."""
    global previous_window_info, last_active_os_pid

    # --- NEW LOGIC: Detect OS-level app switch using PID ---
    current_app_pid = get_active_app_pid()

    if current_app_pid is not None and current_app_pid != last_active_os_pid:
        
        # Check if the active PID matches our own PID
        if current_app_pid == OWN_PID:
            print(f"[SYSTEM EVENT] My PID ({OWN_PID}) is now active! Switch from external app detected.")
            # Restore focus to the last known X11 window
            if (last_active_window_id is not None):
                set_x11_focus(last_active_window_id, None)
            else:
                print("last active window id is None!")
        
        last_active_os_pid = current_app_pid
    # ----------------------------------------------------------------

    current_window_info = get_current_window_info()
    previous_window_info = update_windows_status(previous_window_info, current_window_info)

    # Schedule the next check in 500ms (check faster for better responsiveness)
    root.after(500, main_loop)

if __name__ == "__main__":
    print("Starting bidirectional window monitor with OS app activity check (PID-based).")
    print("Ensure XQuartz and wmctrl are installed.")

    previous_window_info = get_current_window_info()
    for window_id, title in previous_window_info.items():
        create_cocoa_window(window_id, title)

    # Set timer for faster detection (500ms)
    root.after(500, main_loop)
    root.mainloop()

