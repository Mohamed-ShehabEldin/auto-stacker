#!/usr/bin/env python3
"""
Simple temperature controller test for IDE execution.
Just click Run in your IDE - no command-line args needed!
"""

try:
    from .controller import ModbusTemperatureController
except ImportError:
    from controller import ModbusTemperatureController

# ========== CONFIGURATION ==========
PORT = "COM3"
BAUDRATE = 9600
PARITY = 'N'
STOPBITS = 1
BYTESIZE = 8
UNIT = 1
TIMEOUT = 2

# Registers to test
TEST_REGISTERS = [0, 1, 2, 3, 4, 5, 100, 101, 102, 256, 257, 258, 259, 5000, 5004, 5005]

# ========== MAIN ==========
if __name__ == '__main__':
    print("=" * 60)
    print(f"Testing {PORT} @ {BAUDRATE} {PARITY} {STOPBITS} {BYTESIZE} unit {UNIT}")
    print("=" * 60)
    
    controller = ModbusTemperatureController(
        port=PORT,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=BYTESIZE,
        unit=UNIT,
        timeout=TIMEOUT,
    )
    
    try:
        print("\n[1] Attempting to connect...")
        controller.connect()
        print("[✓] Connected successfully!")
        
        print("\n[2] Testing registers...")
        for reg in TEST_REGISTERS:
            try:
                val = controller.read_registers(reg, count=1)
                print(f"    Register {reg:5d}: {val[0]:6d}")
            except Exception as e:
                print(f"    Register {reg:5d}: FAILED - {type(e).__name__}")
        
        controller.close()
        print("\n[✓] Test complete!")
        
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        print(f"   Make sure COM3 is connected and correct!")
