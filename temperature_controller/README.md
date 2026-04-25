# Temperature Controller Support

This folder contains helper code to probe and control a Chinese temperature
controller that most likely speaks Modbus RTU over a serial connection.

## What to try first

1. Determine the physical serial interface:
   - If the device uses a DB9 connector, it may be RS-232 or RS-485.
   - Use USB-RS232 for RS-232 or USB-RS485 for RS-485.
2. Identify the serial port name:
   - Windows: `COM3`, `COM4`, etc.
   - Linux/macOS: `/dev/ttyUSB0`, `/dev/ttyUSB1`, etc.
3. Start with common Modbus settings:
   - `baudrate=9600`
   - `parity=N`
   - `stopbits=1`
   - `bytesize=8`
   - `unit=1`

## Files

- `controller.py`: generic Modbus RTU helper class for reading and writing registers.
- `probe.py`: command-line probe tool for serial settings and likely registers.
- `test_com3.py`: quick test script for COM3 with common settings.
- `GPT_chat1.pdf`: your imported chat log about the controller.
- `tController/`: Windows application folder provided by the company.

## Usage

From the `temperature_controller` folder:

```bash
python3 probe.py --list-ports
python3 probe.py --port COM3 --baud 9600 --parity N --stopbits 1 --bytesize 8 --unit 1
python3 probe.py --port COM3 --scan
python3 test_com3.py
```

For Windows, replace `/dev/ttyUSB0` with `COM3` or the actual COM port.

## What this does

- `probe.py` verifies whether your device responds to Modbus RTU on the port.
- It tries specific register reads so you can detect a working unit and address.
- `--scan` brute-forces all common serial settings (600 combinations, ~10 minutes).
- It does not assume any single exact register map, because the device model
  appears undocumented.

## Next steps

1. Run `python3 probe.py --list-ports`.
2. Run a simple probe with the most common settings.
3. If the serial link connects, use the returned register values to identify
   which registers hold temperature and setpoint.

If you want, I can now help you improve the script to test a specific register map
for your controller once we know the working port settings.
