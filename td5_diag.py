import serial
import time
import sys

# === CONFIGURATION ===
COM_PORT = 'COM3'      # Your VAG409 cable
BAUDRATE = 10400
TIMEOUT = 1.0          # Serial timeout in seconds
LOGFILE = 'td5_log.txt'

# === GLOBALS ===
ser = None
log = None

def log_msg(msg):
    print(msg)
    if log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

# === KWP2000 Helper Functions ===
def checksum(data):
    return sum(data) % 256

def send_kwp(msg):
    """Send KWP2000 message with checksum."""
    full_msg = msg + [checksum(msg)]
    ser.write(bytes(full_msg))
    log_msg(f"TX: {full_msg}")

def read_kwp_response():
    time.sleep(0.1)
    resp = ser.read(64)
    if resp:
        data = list(resp)
        log_msg(f"RX: {data}")
        return data
    else:
        log_msg("RX: No response")
        return []

# === Protocol ===
def fast_init():
    log_msg("[INIT] Starting fast init sequence")
    ser.baudrate = 10400
    time.sleep(0.2)
    init_seq = [0x81, 0x13, 0xF1, 0x81]  # Target: 0x13 = ABS ECU (0x1C)
    send_kwp(init_seq)
    resp = read_kwp_response()
    return resp if resp else None

def scan_ecus():
    log_msg("[SCAN] Scanning ECUs from 0x10 to 0x3F...")
    for ecu_id in range(0x10, 0x40):
        try:
            send_kwp([0x81, ecu_id, 0xF1, 0x81])
            resp = read_kwp_response()
            if resp:
                log_msg(f"Found ECU at 0x{ecu_id:02X}: {resp}")
        except Exception as e:
            log_msg(f"Error at 0x{ecu_id:02X}: {e}")
            continue

# === ABS Functions ===
def connect_abs():
    log_msg("[ABS] Connecting to ABS ECU (0x1C)...")
    send_kwp([0x81, 0x1C, 0xF1, 0x81])
    return read_kwp_response()

def read_abs_dtc():
    log_msg("[ABS] Reading DTCs...")
    send_kwp([0x80, 0x1C, 0xF1, 0x21])  # Read DTC command
    return read_kwp_response()

def run_abs_actuators():
    log_msg("[ABS] Running actuator tests...")
    # Example test: output test command (you can add more later)
    send_kwp([0x80, 0x1C, 0xF1, 0x30])  # Start output test (example, may vary)
    return read_kwp_response()

# === Menu ===
def main_menu():
    while True:
        print("\n===== TD5 Diagnostic Tool =====")
        print("1. Scan for ECUs")
        print("2. Connect to ABS")
        print("3. Read ABS Fault Codes")
        print("4. Run ABS Actuator Tests")
        print("0. Exit")
        choice = input("> ")
        if choice == '1':
            scan_ecus()
        elif choice == '2':
            connect_abs()
        elif choice == '3':
            read_abs_dtc()
        elif choice == '4':
            run_abs_actuators()
        elif choice == '0':
            break
        else:
            print("Invalid option")

# === Main ===
if __name__ == '__main__':
    try:
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=TIMEOUT)
        log = open(LOGFILE, 'a')
        log_msg("=== TD5 DIAG SESSION STARTED ===")
        main_menu()
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if ser: ser.close()
        if log: log.close()
        print("Session ended.")
