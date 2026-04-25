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

from serial import Serial, SerialException
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
# Use "COM3" if you know the exact port. Leave PORT = None to test every
# detected COM port from the IDE.
PORT = None
BAUDRATE = 9600
PARITY = 'N'
STOPBITS = 1
BYTESIZE = 8
UNIT = 1
TIMEOUT = 0.5

# IDE_SCAN_ALL_PORTS is the best first test when you see "No response" errors.
# It tries a small set of common settings across all detected COM ports.
IDE_SCAN_ALL_PORTS = True

# Keep this False for a focused scan. Set True only when you want to try many
# possible serial settings; it can take several minutes.
SCAN_SETTINGS = False

# Registers to try when SCAN_SETTINGS is False.
REGISTERS_TO_READ = [0, 1, 2, 3, 100, 101, 258, 259, 5000, 5004, 5005]

COMMON_BAUDRATES = [9600, 19200, 38400, 57600, 115200]
COMMON_PARITIES = ['N', 'E', 'O']
COMMON_STOPBITS = [1, 2]
COMMON_BYTESIZES = [7, 8]
COMMON_UNITS = [1, 2, 3, 4, 5, 10, 11, 20, 100, 247]
COMMON_REGISTERS = [0, 1, 2, 3, 4, 5, 10, 20, 100, 101, 102, 110, 111, 112, 200, 201, 256, 257, 258, 259, 5000, 5001, 5002, 5003, 5004, 5005]

# First-pass discovery settings. These are intentionally smaller than the full
# scan so the IDE run finishes in a reasonable time.
DISCOVERY_BAUDRATES = [9600, 19200, 38400]
DISCOVERY_PARITIES = ['N', 'E']
DISCOVERY_STOPBITS = [1]
DISCOVERY_BYTESIZES = [8]
DISCOVERY_UNITS = [1, 2, 10, 247]
DISCOVERY_REGISTERS = [0, 1, 2, 100, 101, 258, 259, 5000]
DISCOVERY_REGISTER_TYPES = ['holding', 'input']


def list_serial_ports():
    return [port.device for port in list_ports.comports()]


def list_serial_port_details():
    return list(list_ports.comports())


def choose_port(preferred_port=None):
    if preferred_port:
        return preferred_port

    ports = list_serial_ports()
    if not ports:
        return None

    logger.info(f"No port configured, using first detected port: {ports[0]}")
    return ports[0]


def print_ports():
    ports = list_serial_port_details()
    if not ports:
        logger.info('No serial ports found.')
        return

    logger.info('Available ports:')
    for port in ports:
        logger.info(f'  {port.device}: {port.description}')


def can_open_port(port):
    try:
        serial_port = Serial(port=port, timeout=0.1)
        serial_port.close()
        return True
    except SerialException as exc:
        logger.info(f"Skipping {port}: cannot open port ({exc})")
        return False


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
        timeout=TIMEOUT,
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


def read_register(controller, register_type, address):
    if register_type == 'holding':
        return controller.read_registers(address, count=1)
    if register_type == 'input':
        return controller.read_input_registers(address, count=1)
    raise ValueError(f"Unknown register type: {register_type}")


def scan_ports_for_replies(
    ports=None,
    registers=None,
    baudrates=None,
    parities=None,
    stopbits=None,
    bytesizes=None,
    units=None,
    register_types=None,
):
    ports = ports or list_serial_ports()
    registers = registers or DISCOVERY_REGISTERS
    baudrates = baudrates or DISCOVERY_BAUDRATES
    parities = parities or DISCOVERY_PARITIES
    stopbits = stopbits or DISCOVERY_STOPBITS
    bytesizes = bytesizes or DISCOVERY_BYTESIZES
    units = units or DISCOVERY_UNITS
    register_types = register_types or DISCOVERY_REGISTER_TYPES

    if not ports:
        logger.error("No serial ports found. Plug in the controller USB/RS485 adapter and run again.")
        return []

    total_settings = len(ports) * len(baudrates) * len(parities) * len(stopbits) * len(bytesizes) * len(units)
    logger.info("")
    logger.info("Discovery scan")
    logger.info(f"Ports: {ports}")
    logger.info(f"Serial settings to try: {total_settings}")
    logger.info(f"Registers: {registers}")
    logger.info("Only successful replies will be printed.")

    hits = []
    checked_settings = 0
    for port in ports:
        if not can_open_port(port):
            checked_settings += len(baudrates) * len(parities) * len(stopbits) * len(bytesizes) * len(units)
            continue

        for baud in baudrates:
            for parity in parities:
                for stop in stopbits:
                    for byte in bytesizes:
                        for unit in units:
                            checked_settings += 1
                            logger.info(
                                f"[{checked_settings}/{total_settings}] {port} @ {baud} {parity} {stop} {byte} unit {unit}"
                            )
                            controller = ModbusTemperatureController(
                                port=port,
                                baudrate=baud,
                                parity=parity,
                                stopbits=stop,
                                bytesize=byte,
                                unit=unit,
                                timeout=TIMEOUT,
                            )
                            try:
                                controller.connect()
                                for register_type in register_types:
                                    for address in registers:
                                        try:
                                            values = read_register(controller, register_type, address)
                                            hit = {
                                                'port': port,
                                                'baudrate': baud,
                                                'parity': parity,
                                                'stopbits': stop,
                                                'bytesize': byte,
                                                'unit': unit,
                                                'register_type': register_type,
                                                'address': address,
                                                'value': values[0],
                                            }
                                            hits.append(hit)
                                            logger.info(
                                                "HIT "
                                                f"{port} @ {baud} {parity} {stop} {byte} unit {unit} "
                                                f"{register_type} register {address} = {values[0]}"
                                            )
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                            finally:
                                controller.close()

    if hits:
        logger.info("")
        logger.info("Working replies found:")
        for hit in hits:
            logger.info(
                f"  {hit['port']} @ {hit['baudrate']} {hit['parity']} "
                f"{hit['stopbits']} {hit['bytesize']} unit {hit['unit']} "
                f"{hit['register_type']} register {hit['address']} = {hit['value']}"
            )
    else:
        logger.info("")
        logger.info("No Modbus replies found.")
        logger.info("Next checks:")
        logger.info("  1. Try the other listed COM ports in the vendor tController software.")
        logger.info("  2. Confirm RS485 A/B wires are not reversed.")
        logger.info("  3. Confirm the controller is powered and not already open in another app.")
        logger.info("  4. If tController connects, copy its port, baudrate, parity, and slave address here.")

    return hits


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
                            timeout=TIMEOUT,
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

    if IDE_SCAN_ALL_PORTS:
        ports = [PORT] if PORT else None
        scan_ports_for_replies(ports=ports)
        return

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
