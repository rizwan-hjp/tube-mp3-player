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
            # Suppress console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Run the netsh command to list all firewall rules
            result = subprocess.run(
                ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
                stdout=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
            )
            
            # Process the output
            rules = result.stdout.splitlines()
            rule_count = 0
            allow_count = 0
            block_count = 0
            rule_found = False
            
            for line in rules:
                # Check if a new rule block starts
                if line.startswith("Rule Name:"):
                    if app_name.lower() in line.lower():
                        rule_found = True
                        rule_count += 1
                    else:
                        rule_found = False
                
                # If we are in the relevant rule block, check for action
                if rule_found and line.strip().startswith("Action:"):
                    action = line.split(":", 1)[-1].strip().lower()
                    if action == "allow":
                        allow_count += 1
                    elif action == "block":
                        block_count += 1
            
            # Return counts if any rules were found
            if block_count > 0:
                return False
            return rule_count > 0 and rule_count == allow_count
            
        except Exception as e:
            return f"Error: {str(e)}"



    @staticmethod
    def add_firewall_rule(app_name, app_path, rule_count):
        try:
            # Combine delete and add commands into a single batch command
            batch_cmd = (
                f'netsh advfirewall firewall delete rule name="{app_name}" & '
                f'netsh advfirewall firewall add rule name="{app_name}" '
                f'dir=in action=allow program="{app_path}" enable=yes'
            )
            
            # Run both commands in a single admin elevation
            FirewallManager.run_as_admin(batch_cmd)
            
            # Wait a moment for operations to complete
            import time
            time.sleep(0.5)
            
            # Verify the rule was added successfully
            if FirewallManager.check_firewall_rule(app_name):
                return True
            
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