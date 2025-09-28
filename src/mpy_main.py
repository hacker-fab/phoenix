import time

from sim import simulate_profile, ThermalModel
from profile import validate_profile_rate, piecewise_linear_setpoint
from burst import BurstFire
from max31856 import Max31856
from pid import SimplePID

# MAX31856
PIN_CS = 46
PIN_MISO = 10 # SDO trace
PIN_MOSI = 9 # SDI trace
PIN_CLK = 11

# Burst
PIN_SSR = 5
AC_FREQ = 60
NUM_CYCLES = 20
DUTY = 0.5

DT_TARGET = 0.1

def main() -> None:
    # Define a sample piecewise linear profile:
    # (time_in_seconds, temperature_setpoint)
    heat_profile = [
        (0, 25), (100, 30), (200, 30),
    ]

    sim_time = 200.0  # simulate for 300 seconds (5 minutes)
    dt = 0.1

    # validate profile
    max_allowed_rate = 30.0  # °C per minute
    violations = validate_profile_rate(heat_profile, max_allowed_rate, rate_unit="deg/min")

    if violations:
        for index, slope in violations:
            print(f"Segment starting at index {index} has a slope of {slope:.2f} °C/min, which exceeds {max_allowed_rate} °C/min.")
    else:
        print("Profile is valid: all segments are within the allowed ramp rate.")

    # ------------- copied from test_sim.py --------------

    rate_limit = 30.0

    # 1) Profile validation
    violations = validate_profile_rate(heat_profile, rate_limit, rate_unit="deg/min")
    assert not violations, f"Profile rate violations: {violations}"

    # 2) Run simulation
    epoch = time.perf_counter()
    prev_t = 0
    max31856 = Max31856(PIN_CS, PIN_MISO, PIN_MOSI, PIN_CLK)
    pid = SimplePID()
    bf = BurstFire(output_pin_num=PIN_SSR, freq_hz=AC_FREQ, period_cycles=NUM_CYCLES, duty_percent=DUTY)


    while True:
        now = time.perf_counter() - epoch
        dt = now - prev_t
        prev_t = now

        goal = piecewise_linear_setpoint(now, heat_profile)
        temp = max31856.readThermocoupleTemp()
        output = pid.compute(goal, temp, dt)

        bf.set_duty(output)

        time.sleep(max(0.0, DT_TARGET - (time.perf_counter() - now)))

if __name__ == "__main__":
    main()
