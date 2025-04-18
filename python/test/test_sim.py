import pytest
from sim import simulate_profile, ThermalModel
from profile import validate_profile_rate
import matplotlib.pyplot as plt
import numpy as np


@pytest.mark.parametrize(
    "model, profile, rate_limit, sim_time, tolerance",
    [
        # Profile from 25→100→200°C with gentle slopes well below 30°C/min.
        (
            ThermalModel(ambient=25.0, max_heating_rate=2.0, cooling_coeff=0.01),
            [(0, 25), (600, 100), (1200, 200)],
            30.0,    # maximum ramp rate, °C/min
            1800.0,  # simulate 30 minutes
            5.0      # °C tolerance at final setpoint
        ),
    ],
)
def test_conv_ramp(model, profile, rate_limit, sim_time, tolerance):
    # 1) Validate profile
    violations = validate_profile_rate(profile, rate_limit, rate_unit="deg/min")
    assert not violations, f"Profile rate violations: {violations}"

    # 2) Run simulation
    dt = 0.1
    times, temperatures, setpoints, pwm_values, pid_outputs = simulate_profile(profile, model, sim_time, dt)

    # 3) Assert convergence
    final_err = abs(temperatures[-1] - setpoints[-1])
    assert final_err < tolerance, f"Final temp error {final_err:.1f}°C exceeds tolerance {tolerance}°C"

    # 4a) Plot Temperature vs. Setpoint
    plt.figure()
    plt.plot(times, temperatures, label="Simulated Temperature", color="blue")
    plt.plot(times, setpoints,   label="Profile Setpoint",     color="orange", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Temperature (°C)")
    plt.title("Simulated Temperature vs. Profile Setpoint")
    plt.legend()
    plt.show()

    # 4b) Compute & Plot instantaneous slope (°C/min)
    raw_slopes = np.diff(temperatures) / dt * 60
    slope_times = times[1:]

    window_sec = 10.0                     # smooth over 10 seconds
    window_len = int(window_sec / dt)     # = 10 / 0.1 = 100 samples
    if window_len < 1:
        window_len = 1

    # Create the filter kernel and apply convolution:
    kernel = np.ones(window_len) / window_len
    slopes = np.convolve(raw_slopes, kernel, mode="same")

    # 5) Check that simulated ramp rates do not exceed the rate limit
    max_simulated_ramp = max(slopes)
    assert max_simulated_ramp <= rate_limit + 1.0, (
        f"Simulated ramp rate {max_simulated_ramp:.2f}°C/min exceeds allowed limit of {rate_limit}°C/min (plus tolerance)."
    )

    plt.figure()
    plt.plot(slope_times, slopes, label="Temp Slope (°C/min)", color="green")
    plt.axhline(rate_limit, color="red", linestyle="--", label=f"Rate Limit ({rate_limit}°C/min)")
    plt.xlabel("Time (s)")
    plt.ylabel("Slope (°C/min)")
    plt.title("Rate of Temperature Change Over Time")
    plt.legend()
    plt.show()



@pytest.mark.parametrize(
    "profile, max_rate, should_pass",
    [
        # This profile should pass: the slopes are gentle.
        (
            [(0, 25), (600, 100), (1200, 200)],
            30.0,  # max ramp rate in °C/min
            True,
        ),
        # This profile should fail: the first segment's slope is too high.
        (
            [(0, 25), (300, 200), (600, 500)],
            30.0,  # max ramp rate in °C/min
            False,
        ),
    ],
)
def test_validate_profile_rate(profile, max_rate, should_pass):
    """
    Test that validate_profile_rate returns the expected outcome.
    For a given profile and max_rate:
      - If should_pass is True, then there should be no violations.
      - If should_pass is False, then at least one violation should be returned.
    """
    violations = validate_profile_rate(profile, max_rate, rate_unit="deg/min")

    if should_pass:
        assert len(violations) == 0, f"Expected profile to pass, but got violations: {violations}"
    else:
        assert len(violations) > 0, "Expected profile to fail, but no violations were found."
