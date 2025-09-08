from machine import Pin

PIN1 = 7
PIN2 = 15
PIN3 = 16

led1 = Pin(PIN1, Pin.OUT)
led2 = Pin(PIN2, Pin.OUT)
led3 = Pin(PIN3, Pin.OUT)

led1.value(1)
led2.value(1)
led3.value(1)
