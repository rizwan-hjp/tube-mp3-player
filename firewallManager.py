import flet as ft
import subprocess
import ctypes


class FirewallManager:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    # @staticmethod
    # def run_as_admin(cmd):
    #     if FirewallManager.is_admin():
    #         return subprocess.run(cmd, shell=True)
    #     else:
    #         ctypes.windll.shell32.ShellExecuteW(
    #             None, "runas", "cmd.exe", f"/c {cmd}", None, 1
    #         )

    @staticmethod
    def check_firewall_rule(app_name):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
                stdout=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,  # Suppress console
            )
            return app_name.lower() in result.stdout.lower()
        except Exception:
            return False

    @staticmethod
    def add_firewall_rule(app_name, app_path):
        try:
            # First check if already exists
            if FirewallManager.check_firewall_rule(app_name):
                return True
                
            # Try to add the rule
            cmd = (f'netsh advfirewall firewall add rule name="{app_name}" '
                f'dir=in action=allow program="{app_path}" enable=yes')
            result = FirewallManager.run_as_admin(cmd)
            
            # Wait a moment for the rule to be added
            import time
            time.sleep(1)
            
            # Verify the rule was actually added
            if FirewallManager.check_firewall_rule(app_name):
                return True
                
            # If we get here, the rule wasn't added successfully
            return False

        except Exception:
            return False

    @staticmethod
    def run_as_admin(cmd):
        try:
            if FirewallManager.is_admin():
                return subprocess.run(
                    cmd, 
                    shell=False, 
                    capture_output=True, 
                    text=True
                )
            else:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", "cmd.exe", f"/c {cmd}", None, 1
                )
                return None
        except Exception:
            return None