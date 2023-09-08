from typing import Optional
import socket


def colored(st, color: Optional[str], background=False):
    return (
        f"\u001b[{10*background+60*(color.upper() == color)+30+['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'].index(color.lower())}m{st}\u001b[0m"
        if color is not None
        else st
    )


def get_local_ip():
    try:
        # Create a dummy socket to connect to an external server
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use a public DNS server (Google's) to find the local IP
            # The connection is not actually established
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception as e:
        print(f"Error obtaining local IP: {e}")
        return None


def get_free_port():
    try:
        # Create a dummy socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Bind to an address with port 0
            s.bind(("", 0))
            # Get the assigned port and return it
            return s.getsockname()[1]
    except Exception as e:
        print(f"Error obtaining a free port: {e}")
        return None
