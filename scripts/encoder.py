from machine import Pin, Timer
import time

# =========================
# GPIO Pin Definitions
# =========================

ENC_A_PIN = 18       # Rotary encoder pin A
ENC_B_PIN = 17       # Rotary encoder pin B
ENC_BTN_PIN = 4     # Rotary encoder pin SW, aka push-button
TIMER_ID = 0        # Timer ID used for button debounce

# =========================
# Rotary Encoder Class
# =========================

class RotaryEncoder:
    def __init__(self, pin_a, pin_b):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.position = 0
        self.prev_state = (self.pin_a.value() << 1) | self.pin_b.value()

        # Encoder transition lookup table (4-bit: prev<<2 | curr)
        self.transition_table = {
            0b0001: +1,
            0b0010: -1,
            0b0100: -1,
            0b0111: +1,
            0b1000: +1,
            0b1011: -1,
            0b1101: -1,
            0b1110: +1,
        }

        # Attach interrupts on both A and B
        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._handle_rotation)
        self.pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._handle_rotation)

    def _handle_rotation(self, pin):
        a = self.pin_a.value()
        b = self.pin_b.value()
        curr_state = (a << 1) | b
        transition = (self.prev_state << 2) | curr_state

        delta = self.transition_table.get(transition, 0)
        if delta:
            self.position += delta
            print("Position:", self.position)

        self.prev_state = curr_state

    def get_position(self):
        return self.position

# =========================
# Button Handler (IRQ + Debounce)
# =========================

class ButtonHandler:
    def __init__(self, pin, callback=None, timer_id=TIMER_ID, debounce_ms=50):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.debounce_timer = Timer(timer_id)
        self.callback = callback or self._default_callback
        self.debounce_ms = debounce_ms

        # Attach falling edge interrupt (button press)
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._irq_handler)

    def _irq_handler(self, pin):
        # Start debounce timer
        self.debounce_timer.init(
            mode=Timer.ONE_SHOT,
            period=self.debounce_ms,
            callback=self._debounce_callback
        )

    def _debounce_callback(self, timer):
        if self.pin.value() == 0:  # Still pressed
            self.callback()

    def _default_callback(self):
        print("Button pressed!")

# =========================
# Entry Point
# =========================

def test_run():
    print("Encoder test starting...")

    encoder = RotaryEncoder(ENC_A_PIN, ENC_B_PIN)
    button = ButtonHandler(ENC_BTN_PIN)

    try:
        while True:
            time.sleep(5)
            print("Idle...")
    except KeyboardInterrupt:
        print("Stopped by user")

if __name__ == '__main__':
    test_run()
