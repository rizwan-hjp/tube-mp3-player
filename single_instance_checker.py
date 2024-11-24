import socket
import sys
import win32gui
import win32con

class SingleInstanceChecker:
    def __init__(self, app_title, port=12345):
        self.app_title = app_title
        self.port = port

    def find_and_focus_window(self):
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if self.app_title in window_title:
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if windows:
            hwnd = windows[0]
            if win32gui.IsIconic(hwnd):  # If minimized
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        return False

    def check_already_running(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', self.port))
            sock.listen(1)
            return False, sock  # App is not running
        except socket.error:
            return True, None   # App is already running

    def prevent_multiple_instances(self):
        is_running, sock = self.check_already_running()
        
        if is_running:
            # Try to focus existing window
            if self.find_and_focus_window():
                sys.exit()
            else:
                # If window not found but port is in use
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Already Running", "Application is already running!")
                root.destroy()
                sys.exit()
                
        return sock  # Return sock to keep it from being garbage collected