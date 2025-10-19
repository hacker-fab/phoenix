from machine import Pin, Timer
import time

class BurstFire:
    _DEFAULT_TIMER_ID = 0
    def __init__(self, output_pin_num, freq_hz=60, period_cycles=20, duty_percent=0.5):
        """
        Initialize burst fire control.
        
        :param output_pin_num: GPIO pin connected to SSR
        :param freq_hz: Mains frequency (default 60Hz)
        :param period_cycles: Number of AC cycles in a control period
        :param duty_percent: Initial power output (0.0 -> 1.0)
        """
        self.output_pin = Pin(output_pin_num, Pin.OUT)
        self.freq_hz = freq_hz
        self.period_cycles = period_cycles
        self.timer = Timer(self._DEFAULT_TIMER_ID)
        
        self.next_duty_percent = duty_percent
        self.duty_percent = duty_percent
        self.on_cycles = int(self.period_cycles * self.duty_percent)
        self.cycle_counter = 0

        self._start_timer()

    def _start_timer(self):
        """Start the periodic timer to simulate 60Hz zero-cross ticks."""
        self.timer.init(freq=self.freq_hz, mode=Timer.PERIODIC, callback=self._on_tick)

    def _on_tick(self, t):
        """Called every 1/freq_hz seconds to simulate AC cycle edges."""
        if self.cycle_counter < self.on_cycles:
            self.output_pin.value(1)  # SSR ON
        else:
            self.output_pin.value(0)  # SSR OFF

        self.cycle_counter += 1
        if self.cycle_counter >= self.period_cycles:
            self.cycle_counter = 0
            self._set_duty()

    def _set_duty(self):
        """
        Change power level.
        
        :param percent: Power output (0.0 -> 1.0)
        """
        self.duty_percent = self.next_duty_percent
        self.on_cycles = int(self.period_cycles * self.duty_percent)

    def set_duty(self, percent):
        assert 0.0 <= percent <= 1.0
        self.next_duty_percent = percent

    def stop(self):
        """Stops the output and disables the timer."""
        self.timer.deinit()
        self.output_pin.value(0)

    def start(self):
        """Restart the burst control."""
        self._start_timer()

if __name__ == "__main__":
    PIN_SSR = 5
    AC_FREQ = 60
    NUM_CYCLES = 20
    DUTY = 0.5
    bf = BurstFire(output_pin_num=PIN_SSR, freq_hz=AC_FREQ, period_cycles=NUM_CYCLES, duty_percent=DUTY)

    while True:
        time.sleep(1)
