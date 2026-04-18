#pip uninstall pymodbus
#pip install pymodbus==2.5.3
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

class TemperatureController:
    def __init__(self, com="COM8"):
        self.com = com
        self.client = None
        self.connected = False
        self.connect()

    def connect(self):
        self.client = ModbusSerialClient(
            method='rtu',
            port=self.com,
            baudrate=9600,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1
        )
        self.connected = self.client.connect()

    def set_temperature(self, temp_celsius):
        if not self.connected:
            raise Exception("Could not connect to heat controller on COM port")

        self.client.write_register(address=0x010F, value=2, unit=1)

        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_16bit_uint(9999)
        builder.add_16bit_int(int(temp_celsius * 10))
        builder.add_16bit_uint(0)
        builder.add_16bit_uint(100)
        builder.add_16bit_uint(0)
        builder.add_16bit_int(int(temp_celsius * 10))
        builder.add_16bit_uint(0)
        builder.add_16bit_uint(100)
        payload = builder.to_registers()

        self.client.write_registers(address=0x5004, values=payload, unit=1)
        self.client.write_register(address=0x010F, value=0, unit=1)

    def get_temperature(self):
        if not self.connected:
            raise Exception("Could not connect to heat controller on COM port")
        result = self.client.read_holding_registers(address=258, count=1, unit=1)
        return result.registers[0] / 10.0

    def get_setpoint(self):
        if not self.connected:
            raise Exception("Could not connect to heat controller on COM port")
        result = self.client.read_holding_registers(address=0x5005, count=1, unit=1)
        val = result.registers[0]
        if val > 32767:
            val -= 65536
        return val / 10.0

    def close(self):
        if self.connected:
            self.client.close()
            self.connected = False

# === Usage ===
if __name__ == '__main__':
    temp_c = TemperatureController(com="COM8")
    temp_c.set_temperature(-45)
    print("Setpoint:", temp_c.get_setpoint(), "°C")
    print("Current:", temp_c.get_temperature(), "°C")
    temp_c.close()
