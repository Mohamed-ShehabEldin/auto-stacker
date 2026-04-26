"""
Generic Modbus RTU helper for Chinese temperature controllers.
This library is written to help you probe the serial bus and read/write
registers before you know the exact register map for your controller.
"""

import logging

from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ConnectionException

logger = logging.getLogger(__name__)

class ModbusTemperatureController:
    def __init__(
        self,
        port,
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1,
        unit=1,
    ):
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.unit = unit
        self.client = ModbusSerialClient(
            method='rtu',
            port=self.port,
            baudrate=self.baudrate,
            parity=self.parity,
            stopbits=self.stopbits,
            bytesize=self.bytesize,
            timeout=self.timeout,
        )
        self.connected = False

    def connect(self):
        if not self.connected:
            self.connected = self.client.connect()
            if not self.connected:
                raise ConnectionError(
                    f"Could not connect to {self.port} at {self.baudrate} {self.parity} "
                    f"unit {self.unit}"
                )
        return self.connected

    def close(self):
        try:
            self.client.close()
        finally:
            self.connected = False

    def read_registers(self, address, count=1, unit=None):
        if not self.connected:
            self.connect()
        unit = self.unit if unit is None else unit
        response = self.client.read_holding_registers(address=address, count=count, unit=unit)
        if response is None:
            raise IOError(f"Timeout or no response for register {address} unit {unit}")
        if hasattr(response, 'isError') and response.isError():
            raise IOError(f"Modbus error reading register {address} unit {unit}: {response}")
        return response.registers

    def read_holding_register_block(self, address, count, unit=None):
        return self.read_registers(address=address, count=count, unit=unit)

    def read_input_registers(self, address, count=1, unit=None):
        if not self.connected:
            self.connect()
        unit = self.unit if unit is None else unit
        response = self.client.read_input_registers(address=address, count=count, unit=unit)
        if response is None:
            raise IOError(f"Timeout or no response for input register {address} unit {unit}")
        if hasattr(response, 'isError') and response.isError():
            raise IOError(f"Modbus error reading input register {address} unit {unit}: {response}")
        return response.registers

    def read_input_register_block(self, address, count, unit=None):
        return self.read_input_registers(address=address, count=count, unit=unit)

    def write_register(self, address, value, unit=None):
        if not self.connected:
            self.connect()
        unit = self.unit if unit is None else unit
        response = self.client.write_register(address=address, value=value, unit=unit)
        if response is None:
            raise IOError(f"Timeout or no response writing register {address} unit {unit}")
        if hasattr(response, 'isError') and response.isError():
            raise IOError(f"Modbus error writing register {address} unit {unit}: {response}")
        return response

    def read_coils(self, address, count=1, unit=None):
        if not self.connected:
            self.connect()
        unit = self.unit if unit is None else unit
        response = self.client.read_coils(address=address, count=count, unit=unit)
        if response is None:
            raise IOError(f"Timeout or no response for coil {address} unit {unit}")
        if hasattr(response, 'isError') and response.isError():
            raise IOError(f"Modbus error reading coil {address} unit {unit}: {response}")
        return response.bits[:count]

    def read_discrete_inputs(self, address, count=1, unit=None):
        if not self.connected:
            self.connect()
        unit = self.unit if unit is None else unit
        response = self.client.read_discrete_inputs(address=address, count=count, unit=unit)
        if response is None:
            raise IOError(f"Timeout or no response for discrete input {address} unit {unit}")
        if hasattr(response, 'isError') and response.isError():
            raise IOError(f"Modbus error reading discrete input {address} unit {unit}: {response}")
        return response.bits[:count]

    def read_temperature(self, address, scaling=10.0, signed=True, unit=None):
        registers = self.read_registers(address, count=1, unit=unit)
        value = registers[0]
        if signed and value > 0x7FFF:
            value -= 0x10000
        return value / scaling

    def set_register_value(self, address, value, unit=None):
        return self.write_register(address=address, value=value, unit=unit)

    def __repr__(self):
        return (
            f"<ModbusTemperatureController port={self.port} baudrate={self.baudrate} "
            f"parity={self.parity} stopbits={self.stopbits} bytesize={self.bytesize} "
            f"unit={self.unit} connected={self.connected}>"
        )
