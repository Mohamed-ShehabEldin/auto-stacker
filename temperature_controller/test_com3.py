#!/usr/bin/env python3
"""
Quick test script for the temperature controller on COM3.
Run this on the Windows PC with the device connected.
"""

try:
    from temperature_controller.controller import ModbusTemperatureController
except ImportError:
    from controller import ModbusTemperatureController

def test_connection(port='COM3', baudrate=9600, parity='N', stopbits=1, bytesize=8, unit=1):
    print(f"Testing {port} @ {baudrate} {parity} {stopbits} {bytesize} unit {unit}")
    controller = ModbusTemperatureController(
        port=port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        unit=unit,
    )
    try:
        controller.connect()
        print("Connected successfully!")
        # Try reading some registers
        for reg in [0, 1, 2, 100, 258, 259, 5000, 5004, 5005]:
            try:
                val = controller.read_registers(reg, count=1)
                print(f"Register {reg}: {val[0]}")
            except Exception as e:
                print(f"Register {reg}: FAILED - {e}")
        controller.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == '__main__':
    # Test common settings
    test_connection()
    test_connection(baudrate=19200)
    test_connection(baudrate=38400)
    test_connection(unit=2)
    test_connection(unit=10)
