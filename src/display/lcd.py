from machine import I2C, Pin
import utime

SDA_PIN = 12
SCL_PIN = 13
RST_PIN = 14
I2C_ADDR = 0x3C
FREQ = 400000


class LCD:
    """Basic I2C driver (ST7036) for NHD‑C0220BiZ 2-line LCD."""

    def __init__(self, addr=I2C_ADDR):
        self.i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=FREQ)
        self.addr = addr
        self.init_lcd()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x00, cmd]))

    def write_data(self, data):
        self.i2c.writeto(self.addr, bytearray([0x40, data]))

    def init_lcd(self):
        utime.sleep_ms(50)
        self.write_cmd(0x38)
        utime.sleep_ms(1)
        self.write_cmd(0x39)
        utime.sleep_ms(1)
        self.write_cmd(0x14)
        self.write_cmd(0x78)
        self.write_cmd(0x5E)
        utime.sleep_ms(200)
        self.write_cmd(0x6D)
        self.write_cmd(0x0C)
        self.write_cmd(0x01)
        utime.sleep_ms(2)
        self.write_cmd(0x06)

    def clear(self):
        self.write_cmd(0x01)
        utime.sleep_ms(2)

    def write(self, string, line=0):
        addr = 0x00 if line == 0 else 0x40
        self.write_cmd(0x80 | addr)
        for ch in string:
            self.write_data(ord(ch))
