from machine import I2C, Pin
import time
from enum import Enum

LCD_RESET = 14

I2C_ADDR = 60
CONTROL = 0x00
DATA = 0x00
LINE2 = 0xC0

class CtrlContinue(Enum):
    LAST_CTRL = 0
    MORE_CTRL = 1

class CtrlType(Enum):
    INSTRUCTION = 0
    DATA = 1

class ControlByte():
    def __init__(self, co, rs):
        self.co = co 
        self.rs = rs
    def to_byte(self):
        return (self.co.value << 7) | (self.rs.value << 6)


lcd_reset = Pin(LCD_RESET, Pin.OUT)

lcd_reset.value(0)
time.sleep(0.005)
lcd_reset.value(1)

i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=250_000)

# scan
print(i2c.scan())

# def write_data(data):
#     stuff = bytearray([my_ctrl, data])
#     print(stuff)
#     i2c.writeto(I2C_ADDR, stuff)

# write data
my_ctrl = ControlByte(co=CtrlContinue.MORE_CTRL, rs=CtrlType.DATA)

text = "HELLO"
data = text.encode('ascii')[:20]

sequence = bytearray([my_ctrl, data])
i2c.writeto(I2C_ADDR, sequence)

print("write done")
