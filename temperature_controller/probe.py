"""
Probe a Modbus RTU temperature controller to discover working serial settings
and useful candidate register addresses.

IDE use:
    Edit the SETTINGS section below, then click Run in your IDE.

Terminal use:
    python3 probe.py --port COM3 --baud 9600 --unit 1
    python3 probe.py --port /dev/ttyUSB0 --baud 9600 --unit 1 --registers 258 259
"""

import argparse
import logging
import sys

from serial.tools import list_ports

try:
    from .controller import ModbusTemperatureController
except ImportError:
    from controller import ModbusTemperatureController

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# =========================
# SETTINGS FOR IDE RUNNING
# =========================
#
# Most IDEs run this file without command-line arguments. Change these values,
# then click Run.
#
# Use "COM3" on your Windows machine unless Device Manager shows a different
# port. If you set PORT = None, the script will automatically use the first
# serial port it finds.
PORT = "COM3"
BAUDRATE = 9600
PARITY = 'N'
STOPBITS = 1
BYTESIZE = 8
UNIT = 1

# Keep this False for a quick register test. Set True only when you want to
# try many possible serial settings; it can take several minutes.
SCAN_SETTINGS = False

# Registers to try when SCAN_SETTINGS is False.
REGISTERS_TO_READ = [0, 1, 2, 3, 100, 101, 258, 259, 5000, 5004, 5005]

COMMON_BAUDRATES = [9600, 19200, 38400, 57600, 115200]
COMMON_PARITIES = ['N', 'E', 'O']
COMMON_STOPBITS = [1, 2]
COMMON_BYTESIZES = [7, 8]
COMMON_UNITS = [1, 2, 3, 4, 5, 10, 11, 20, 100, 247]
COMMON_REGISTERS = [0, 1, 2, 3, 4, 5, 10, 20, 100, 101, 102, 110, 111, 112, 200, 201, 256, 257, 258, 259, 5000, 5001, 5002, 5003, 5004, 5005]


def list_serial_ports():
    return [port.device for port in list_ports.comports()]


def choose_port(preferred_port=None):
    if preferred_port:
        return preferred_port

    ports = list_serial_ports()
    if not ports:
        return None

    logger.info(f"No port configured, using first detected port: {ports[0]}")
    return ports[0]


def print_ports():
    ports = list_serial_ports()
    if not ports:
        logger.info('No serial ports found.')
        return

    logger.info('Available ports:')
    for port in ports:
        logger.info(f'  {port}')


def probe_registers(port, baudrate, parity, stopbits, bytesize, unit, registers):
    logger.info(
        f"Probing {port} @ {baudrate} {parity} {stopbits} {bytesize} unit {unit} for registers: {registers}"
    )
    controller = ModbusTemperatureController(
        port=port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        unit=unit,
        timeout=1,
    )
    try:
        controller.connect()
    except Exception as exc:
        logger.error(f"Connection failed: {exc}")
        return

    for address in registers:
        try:
            registers_value = controller.read_registers(address, count=1)
            logger.info(f"OK  register {address}: {registers_value[0]}")
        except Exception as exc:
            logger.info(f"FAIL register {address}: {exc}")
    controller.close()


def scan_settings(port, registers, baudrates=None, parities=None, stopbits=None, bytesizes=None, units=None):
    baudrates = baudrates or COMMON_BAUDRATES
    parities = parities or COMMON_PARITIES
    stopbits = stopbits or COMMON_STOPBITS
    bytesizes = bytesizes or COMMON_BYTESIZES
    units = units or COMMON_UNITS

    logger.info(f"Scanning serial settings on {port}")
    total = len(baudrates) * len(parities) * len(stopbits) * len(bytesizes) * len(units)
    logger.info(f"Total combinations: {total}")
    count = 0
    for baud in baudrates:
        for parity in parities:
            for stop in stopbits:
                for byte in bytesizes:
                    for unit in units:
                        count += 1
                        if count % 100 == 0:
                            logger.info(f"Progress: {count}/{total}")
                        controller = ModbusTemperatureController(
                            port=port,
                            baudrate=baud,
                            parity=parity,
                            stopbits=stop,
                            bytesize=byte,
                            unit=unit,
                            timeout=1,
                        )
                        try:
                            controller.connect()
                            try:
                                response = controller.read_registers(registers[0], count=1)
                                logger.info(
                                    f"SUCCESS {baud} {parity} {stop} {byte} unit {unit}: register {registers[0]} -> {response[0]}"
                                )
                            except Exception as exc:
                                logger.debug(
                                    f"CONNECTED {baud} {parity} {stop} {byte} unit {unit} but read failed: {exc}"
                                )
                        except Exception as exc:
                            logger.debug(f"{baud} {parity} {stop} {byte} unit {unit} connect failed: {exc}")
                        finally:
                            controller.close()


def parse_args():
    parser = argparse.ArgumentParser(description='Probe a Modbus RTU temperature controller.')
    parser.add_argument('--port', required=False, help='Serial port name (COM3 or /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate')
    parser.add_argument('--parity', choices=['N', 'E', 'O'], default='N', help='Parity')
    parser.add_argument('--stopbits', type=int, choices=[1, 2], default=1, help='Stop bits')
    parser.add_argument('--bytesize', type=int, choices=[7, 8], default=8, help='Byte size')
    parser.add_argument('--unit', type=int, default=1, help='Modbus slave unit ID')
    parser.add_argument('--registers', type=int, nargs='+', default=[0, 1, 2, 3, 100, 101, 258, 259, 5000, 5004, 5005], help='Register addresses to read')
    parser.add_argument('--scan', action='store_true', help='Scan common baudrates, parities, and unit IDs')
    parser.add_argument('--list-ports', action='store_true', help='List available serial ports')
    return parser.parse_args()


def run_from_ide():
    logger.info("IDE run mode")
    print_ports()

    port = choose_port(PORT)
    if not port:
        logger.error("No serial port found. Plug in the controller USB/RS485 adapter and run again.")
        return

    if SCAN_SETTINGS:
        scan_settings(port, REGISTERS_TO_READ)
        return

    probe_registers(
        port=port,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=BYTESIZE,
        unit=UNIT,
        registers=REGISTERS_TO_READ,
    )


def run_from_terminal():
    args = parse_args()

    if args.list_ports:
        print_ports()
        return

    port = choose_port(args.port)
    if not port:
        logger.error("No serial port found. Use --list-ports after connecting the controller.")
        return

    if args.scan:
        scan_settings(port, args.registers)
        return

    probe_registers(
        port=port,
        baudrate=args.baud,
        parity=args.parity,
        stopbits=args.stopbits,
        bytesize=args.bytesize,
        unit=args.unit,
        registers=args.registers,
    )


def main():
    if len(sys.argv) == 1:
        run_from_ide()
    else:
        run_from_terminal()


if __name__ == '__main__':
    main()
