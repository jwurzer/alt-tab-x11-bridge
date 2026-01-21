# AltTab X11 Bridge

For handling X11 windows (XQuartz) with AltTab on macOS

This Python script provides a **hack** for handling individual X11 windows specifically using the [AltTab app](https://alt-tab-macos.netlify.app).

The AltTab switcher on macOS typically sees all of X11/XQuartz as a single application instance, making it impossible to switch between individual X11 windows.

This script solves that issue:

1. It creates a lightweight, native Tkinter (Cocoa) "proxy" window for every active X11 window.
2. These native proxy windows are correctly detected and displayed by the AltTab application.
3. When you select a proxy window using AltTab, this script detects the switch and uses `wmctrl` to ensure the correct, underlying X11 window gets the actual focus.

## Features

* **Full AltTab Compatibility:** Makes individual X11 windows manageable via the AltTab application switcher.
* **Cocoa Proxy Windows:** Creates a unique native Tkinter window for each X11 window.
* **Bidirectional Focus Sync:**
  - Switching between proxy Tkinter windows automatically switches the focus in X11.
  - Switching back to the Python app from another external macOS app (like Firefox) automatically refocuses the last active X11 window using PID tracking and `osascript`.

## Prerequisites

This script is designed specifically for macOS and requires the following external command-line tools to be installed:

* **XQuartz:** The X11 server for macOS.
* **wmctrl:** A command-line tool to interact with EWMH/NetWM compatible X Window Managers.
* **osascript:** (Built-in to macOS) Used for AppleScript execution to monitor active applications.
* **AltTab App:** The primary target application for this bridge. You must have [AltTab](https://alt-tab-macos.netlify.app) installed and running.

## License

This project is dual licensed under the terms of **MIT license** and **zlib license** (choose whichever fits your needs best).


