from machine import I2C, Pin
import time

LCD_RESET = 14

I2C_ADDR = 0x78
COM = 0x00
DATA = 0x00
LINE2 = 0xC0

lcd_reset = Pin(LCD_RESET, Pin.OUT)

lcd_reset.value(0)
time.sleep(0.005)
lcd_reset.value(1)

i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=250_000)

# scan
print(i2c.scan())

# def write_data(data):
#     i2c.writeto(I2C_ADDR, bytearray([DATA, data]))

text = "hello"
print(bytearray([DATA, text[0]]))
for c in text.encode('ascii')[:20]:
    print(bytearray([DATA, c]))
    # write_data(c)
