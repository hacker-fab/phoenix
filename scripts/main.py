from machine import Pin
import time

PIN1 = 7
PIN2 = 15
PIN3 = 16
 
led1 = Pin(PIN1, Pin.OUT)
led2 = Pin(PIN2, Pin.OUT)
led3 = Pin(PIN3, Pin.OUT)

for i in range(2):
    led1.value(1)
    led2.value(1)
    led3.value(1)
    time.sleep(0.5)
    led1.value(0)
    led2.value(0)
    led3.value(0)
    time.sleep(0.5)

