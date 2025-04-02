import socket
import threading
import platform
import os
import socks
import random
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import pyfiglet

from colorama import Fore, Style
banner = pyfiglet.figlet_format("GHOST CYBER", font= "slant")
print(Fore.BLUE + banner + Style.RESET_ALL)
# Important Ports Dictionary (Make it globally accessible)
important_ports = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 
    110: "POP3", 143: "IMAP", 443: "HTTPS", 3389: "RDP"
}


def generate_random_mac():
    """Generate a random but valid MAC address"""
    mac = [random.choice([0x00, 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E]),  # unicast and locally administered MAC
           random.randint(0x00, 0xFF), random.randint(0x00, 0xFF), random.randint(0x00, 0xFF),
           random.randint(0x00, 0xFF), random.randint(0x00, 0xFF)]
    return ':'.join(map(lambda x: f"{x:02x}", mac))


def is_valid_mac(mac):
    """Check if the entered MAC is valid"""
    return re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac) is not None


def check_vmware():
    """Check if the system is a VMware VM"""
    try:
        with open("/sys/class/dmi/id/product_name", "r") as f:
            if "Vmware" in f.read():
                return True
    except FileNotFoundError:
        return False  # File not found, likely not a VM
    return False


def get_network_interface():
    """Get available network interfaces"""
    interfaces = os.listdir("/sys/class/net/")  # List all network interfaces
    return [iface for iface in interfaces if iface != "lo"]  # Exclude the loopback interface


def resolve_target(target):
    """Resolve domain names to IP addresses"""
    try:
        ip_address = socket.gethostbyname(target)  # Resolve domain to IP
        return ip_address
    except socket.gaierror:
        print(f"Invalid domain name or host: {target}")
        return None


def is_tor_installed():
    """Check if Tor is installed on the system"""
    if platform.system() == "Windows":
        result = subprocess.run(["where", "tor"], capture_output=True, text=True)
    else:
        result = subprocess.run(["which", "tor"], capture_output=True, text=True)
    return result.returncode == 0  # If return 0, Tor is installed


def install_tor():
    """Install and start Tor on the system"""
    os_type = platform.system()

    if os_type == "Linux":
        print("Installing Tor on Linux....")
        os.system("sudo apt update && sudo apt install tor -y")
        print("Tor installed successfully")
        print("Starting Tor service...")
        os.system("sudo systemctl start tor")
        print("Tor service started successfully")

    elif os_type == "Windows":
        print("Windows users must manually download and install Tor from https://www.torproject.org")
        input("Press enter after installing Tor and starting Tor browser")
    else:
        print("Unsupported OS, please install Tor manually from https://www.torproject.org")


def scan_port(target, port, service, use_tor):
    """Scan a specific port on the target"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15 if use_tor else 5)  # Set timeout based on whether Tor is used

        ip_target = resolve_target(target)
        if not ip_target:
            print(f"[!] Invalid target IP: {target}")
            return

        result = sock.connect_ex((ip_target, port))
        if result == 0:
            try:
                service_name = socket.getservbyport(port)
            except OSError:
                service_name = "Unknown service"

            # Use predefined names for important ports
            if port in important_ports:
                service_name = important_ports[port]

            print(f"[+] Port {port} ({service_name}) is **OPEN** on {target}")
        # Don't print anything for closed ports (only open ports will be shown)
    except Exception as e:
        print(f"[!] Error scanning port {port} on {target}: {e}")


def main():
    # MAC Spoofing Logic
    mac_spoofing = input("Do you want to spoof your MAC address? (yes/no):").strip().lower()
    if mac_spoofing == "yes" and platform.system() != "Linux":
        print("MAC spoofing only works on Linux, skipping MAC spoofing")
        mac_spoofing = "no"  # Disable spoofing if not on Linux

    if mac_spoofing == "yes":
        interfaces = get_network_interface()
        print("Available network interfaces:", interfaces)
        chosen_interface = input("Enter the interface you want to use for MAC spoofing (e.g., eth0, wlan0): ").strip()
        if chosen_interface not in interfaces:
            print("Invalid interface selected, exiting MAC spoofing")
            mac_spoofing = "no"  # Disable spoofing if invalid interface

    if mac_spoofing == "yes":
        while True:
            mac_option = input("Do you want to (1) Generate a random MAC or (2) Enter a MAC manually? (1/2): ").strip()
            if mac_option == "1":
                new_mac = generate_random_mac()
                print(f"Generated MAC address: {new_mac}")
                break
            elif mac_option == "2":
                new_mac = input("Enter the MAC address (format: XX:XX:XX:XX:XX:XX): ").strip()
                if is_valid_mac(new_mac):
                    print(f"Valid MAC address entered: {new_mac}")
                    break
                else:
                    print("Invalid MAC address entered")
                    retry = input("Do you want to re-enter manually (2) or generate a random MAC (1)? (1/2): ").strip()
                    if retry == "1":
                        new_mac = generate_random_mac()
                        print(f"Generated MAC address: {new_mac}")
                        break
                    elif retry != "2":
                        print("Invalid choice, exiting MAC spoofing")
                        mac_spoofing = "no"
                        break
            else:
                print("Invalid choice, please enter 1 or 2")

    # Tor Tunneling Logic
    use_tor = input("Do you want to tunnel the scan through Tor? (yes/no): ").strip().lower()

    if not is_tor_installed():
        print("Tor is not installed on your system")
        install_choice = input("Do you want to install Tor? (yes/no): ").strip().lower()
        if install_choice == "yes":
            install_tor()
        else:
            print("Tor is not installed, skipping Tor tunneling")
            use_tor = "no"

    if use_tor == "yes":
        print("Warning: Scanning through Tor will be much slower than a direct scan")
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket  # Route all traffic through the Tor proxy
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.connect(("check.torproject.org", 80))
            print("Tor is active! Your scan is now anonymous")
        except:
            print("Tor is not running, you are not anonymous")

    # Port Scanning Logic
    target = input("Enter the target IP Address:")
    print("\nChoose scanning option:")
    print("(1) Scan all ports (1-65535)")
    print("(2) Scan important ports only")
    print("(3) Scan a specific port")
    print("(4) Scan a range of ports")

    scan_choice = input("Enter your choice (1/2/3/4): ").strip()

    # Determine which ports to scan
    if scan_choice == "1":
        ports_to_scan = range(1, 65536)
    elif scan_choice == "2":
        ports_to_scan = important_ports.keys()
    elif scan_choice == "3":
        port = input("Enter the port to scan: ").strip()
        if port.isdigit() and 1 <= int(port) <= 65535:
            ports_to_scan = [int(port)]
        else:
            print("Invalid port number, scanning important ports only")
            ports_to_scan = important_ports.keys()
    elif scan_choice == "4":
        start_port = input("Enter the start port: ").strip()
        end_port = input("Enter the end port: ").strip()

        if start_port.isdigit() and end_port.isdigit():
            start_port, end_port = int(start_port), int(end_port)
            if 1 <= start_port <= end_port <= 65535:
                ports_to_scan = range(start_port, end_port + 1)
            else:
                print("Invalid port range, scanning important ports only")
                ports_to_scan = important_ports.keys()
        else:
            print("Invalid port range, scanning important ports only")
            ports_to_scan = important_ports.keys()
    else:
        print("Invalid choice, scanning important ports only")
        ports_to_scan = important_ports.keys()

    # Creating a thread pool for port scanning
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(lambda port: scan_port(target, port, important_ports.get(port, "Unknown"), use_tor), ports_to_scan)

    print("Scanning complete")


if __name__ == "__main__":
    main()
