from machine import I2C, Pin
import utime

SDA_PIN = 12 #GPIO 12/ADC2_CH1, pin 18 on schematic
SCL_PIN = 13 #GPIO 13/ADC2_CH2, pin 19 on schematic
RST_PIN = 14 #GPIO 14, pin 20 on schematic
I2C_ADDR = 0x3C #60, can be found via i2c.scan()
FREQ = 400000 #400kHz, I2C Fast mode


class LCD:
    """Basic I2C driver (ST7036) for NHD‑C0220BiZ 2-line LCD."""
    def __init__(self, addr=I2C_ADDR):
        self.i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=FREQ)
        self.addr = addr
        self.init_lcd()

    def write_cmd(self, cmd):
        # control byte 0x00 for commands
        self.i2c.writeto(self.addr, bytearray([0x00, cmd]))

    def write_data(self, data):
        # control byte 0x40 for data
        self.i2c.writeto(self.addr, bytearray([0x40, data]))

    def init_lcd(self):
        utime.sleep_ms(50)
        # follow initialization sequence (from manufacturer sample/AN)  
        # example from NHD, p.13/15: https://newhavendisplay.com/content/specs/NHD-C0220BiZ-FSW-FBW-3V3M.pdf
        self.write_cmd(0x38)  # Function set: 8-bit, 2‑line
        utime.sleep_ms(1)
        self.write_cmd(0x39)  # extended instruction set
        utime.sleep_ms(1)
        self.write_cmd(0x14)  # internal OSC frequency
        self.write_cmd(0x78)  # contrast set – C5–C0
        self.write_cmd(0x5E)  # follower control
        utime.sleep_ms(200)
        self.write_cmd(0x6D)  # contrast set — C8–C6
        self.write_cmd(0x0C)  # display ON, cursor OFF, blink OFF
        self.write_cmd(0x01)  # clear display
        utime.sleep_ms(2)
        self.write_cmd(0x06)  # entry mode set (increment)

    def clear(self):
        self.write_cmd(0x01)
        utime.sleep_ms(2)

    def write(self, string, line=0):
        # move cursor to start of line
        # DDRAM address: 0x00 for first line, 0x40 for second
        addr = 0x00 if line == 0 else 0x40
        self.write_cmd(0x80 | addr)
        for ch in string:
            self.write_data(ord(ch))


def test():
    print("AS: LCD test started")
    rst = Pin(RST_PIN, Pin.OUT)
    rst.value(1)
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

    lcd = LCD()
    lcd.clear()
    line1_str = "Stage:1/8 Time:1m20s"
    line2_str = "Temp:850C Slop:20C/m"
    lcd.write(line1_str, line=0)
    lcd.write(line2_str, line=1)


if __name__ == "__main__":
    test()