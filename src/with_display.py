import time

from display.lcd import LCD
from profile import validate_profile_rate, piecewise_linear_setpoint
from burst import BurstFire
from max31856 import Max31856
from pid import SimplePID

PIN_CS = 46
PIN_MISO = 10
PIN_MOSI = 9
PIN_CLK = 11

PIN_SSR = 5
AC_FREQ = 60
NUM_CYCLES = 20
DUTY = 0.5

DT_TARGET = 0.1
MS_TO_SEC = 1000


def main() -> None:
    heat_profile = [
        (0, 35),
        (300 * MS_TO_SEC, 60),
        (600 * MS_TO_SEC, 25),
    ]

    dt = 0.1
    max_allowed_rate = 30.0
    violations = validate_profile_rate(heat_profile, max_allowed_rate, rate_unit="deg/min")

    if violations:
        for index, slope in violations:
            print(f"Segment starting at index {index} has a slope of {slope:.2f} °C/min, which exceeds {max_allowed_rate} °C/min.")
        return
    else:
        print("Profile is valid: all segments are within the allowed ramp rate.")

    lcd = LCD()
    lcd.clear()

    rate_limit = 30.0
    violations = validate_profile_rate(heat_profile, rate_limit, rate_unit="deg/min")
    assert not violations, f"Profile rate violations: {violations}"

    epoch = time.ticks_ms()
    prev_t = 0
    max31856 = Max31856(PIN_CS, PIN_MISO, PIN_MOSI, PIN_CLK)
    pid = SimplePID()
    bf = BurstFire(output_pin_num=PIN_SSR, freq_hz=AC_FREQ, period_cycles=NUM_CYCLES, duty_percent=DUTY)

    while True:
        now = time.ticks_ms() - epoch
        dt = now - prev_t
        prev_t = now

        goal = piecewise_linear_setpoint(now, heat_profile)
        temp = max31856.readThermocoupleTemp()
        output = pid.compute(goal, temp, dt)

        print("goal:", goal, "temp:", temp)
        print("output:", output)
        bf.set_duty(output)

        # FIXME add slope and display the right thing.

        line1 = f"T: {now // 1000:4d}s Goal: {int(goal):3d}C"
        line2 = f"Cur: {int(temp):3d}C Pwr: {int(output * 100):2d}%"

        lcd.write(line1, line=0)
        lcd.write(line2, line=1)

        time.sleep(max(0.0, DT_TARGET - (time.ticks_ms() - now)))


if __name__ == "__main__":
    main()
