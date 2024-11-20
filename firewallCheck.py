import psutil
import socket

class FirewallCheck:
    def __init__(self, port):
        self.port = port

    def is_app_listening_on_port(self):
        """Check if an application is listening on the specified port."""
        # Iterate over all network connections to find any listening on the specified port
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr.port == self.port:
                return True
        return False

    def check_firewall_status(self):
        """Check if the port is open and listening, indicating possible firewall allowance."""
        # Check if the application is listening on the specified port
        return self.is_app_listening_on_port()


# Example Usage
if __name__ == "__main__":
    port = 8000
    firewall_checker = FirewallCheck(port)
    if firewall_checker.check_firewall_status():
        print(f"App is likely allowed through the firewall on port {port}.")
    else:
        print(f"App is not listening on port {port}. It might not be allowed through the firewall.")
