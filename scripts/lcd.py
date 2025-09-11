from machine import I2C, Pin
import time

LCD_RESET = 14

lcd_reset = Pin(LCD_RESET, Pin.OUT)

lcd_reset.value(0)
time.sleep(0.005)
lcd_reset.value(1)

i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=250_000)
print(i2c.scan())
