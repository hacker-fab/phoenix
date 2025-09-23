from machine import Pin, Timer
import time

# === CONFIGURATION ===
relay_pin = Pin(5, Pin.OUT)    # SSR control pin
period_cycles = 20             # Number of AC cycles in a burst period
duty_percent = 75              # Power level (0 to 100%)

# === DERIVED VARIABLES ===
on_cycles = int(period_cycles * duty_percent / 100)
cycle_counter = 0              # Tracks where we are in the burst

# === 60Hz CLOCK TIMER ===
def on_60hz_tick(t):
    global cycle_counter

    # Determine if we're in ON or OFF portion of the burst
    if cycle_counter < on_cycles:
        relay_pin.value(1)  # Turn SSR ON
    else:
        relay_pin.value(0)  # Turn SSR OFF

    # Advance the cycle counter
    cycle_counter += 1
    if cycle_counter >= period_cycles:
        cycle_counter = 0

# === SETUP TIMER TO TICK AT 60Hz ===
# 1000 ms / 60 Hz = ~16.67ms per cycle
timer = Timer(1)
timer.init(freq=60, mode=Timer.PERIODIC, callback=on_60hz_tick)

# === MAIN LOOP ===
while True:
    # Do other stuff here, like update temperature or UI
    time.sleep(1)

