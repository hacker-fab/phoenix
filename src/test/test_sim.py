import os
import pytest
import matplotlib.pyplot as plt
import numpy as np

from sim import simulate_profile, ThermalModel
from profile import validate_profile_rate

# Ensure graphs/ directory exists
os.makedirs("graphs", exist_ok=True)

@pytest.mark.parametrize(
    "model, profile, rate_limit, sim_time, tolerance, test_index",
    [
        (
            ThermalModel(ambient=25.0, max_heating_rate=2.0, cooling_coeff=0.01),
            [(0, 25), (600, 100), (1200, 200)],
            30.0,
            1800.0,
            5.0,
            0,
        ),
        # you can add more cases here, incrementing test_index each time...
    ],
)
def test_profile_convergence_and_save_plots(
    model, profile, rate_limit, sim_time, tolerance, test_index
):
    """
    1) Validate that the piecewise‐linear profile obeys the ramp‐rate limit.
    2) Simulate following that profile.
    3) Assert convergence to the final setpoint.
    4) Save two debug plots under graphs/ as PNGs:
       - {index}_convergence_{temps}.png
       - {index}_slopes_{temps}.png
    """
    # 1) Profile validation
    violations = validate_profile_rate(profile, rate_limit, rate_unit="deg/min")
    assert not violations, f"Profile rate violations: {violations}"

    # 2) Run simulation
    dt = 0.1
    times, temperatures, setpoints, pwm_values, pid_outputs = simulate_profile(
        profile, model, sim_time, dt
    )

    # 3) Convergence assertion
    final_error = max(abs(a - b) for a, b in zip(temperatures, setpoints))
    assert final_error < tolerance, (
        f"Final temperature error {final_error:.1f}°C exceeds tolerance {tolerance}°C"
    )

    # Build a short description from the profile temperatures, e.g. "25-100-200"
    temps = [str(int(T)) for (_, T) in profile]
    description = "-".join(temps)

    # 4a) Plot & save temperature vs setpoint
    fig1, ax1 = plt.subplots()
    ax1.plot(times, temperatures, label="Simulated Temperature", color="blue")
    ax1.plot(times, setpoints,   label="Profile Setpoint",     color="orange", linestyle="--")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Temperature (°C)")
    ax1.set_title("Simulated Temperature vs. Profile Setpoint")
    ax1.legend()
    fname1 = f"graphs/{test_index}_convergence_{description}.png"
    fig1.savefig(fname1)
    plt.close(fig1)

    # 4b) Compute instantaneous slope and smooth
    raw_slopes = np.diff(temperatures) / dt * 60
    slope_times = times[1:]
    window_sec = 10.0
    window_len = max(1, int(window_sec / dt))
    kernel = np.ones(window_len) / window_len
    slopes = np.convolve(raw_slopes, kernel, mode="same")

    # Optional runtime check of simulated ramp rates
    max_slope = slopes.max()
    assert max_slope <= rate_limit + 1.0, (
        f"Simulated ramp rate {max_slope:.1f}°C/min exceeds limit {rate_limit}°C/min"
    )

    # Plot & save slope vs time
    fig2, ax2 = plt.subplots()
    ax2.plot(slope_times, slopes, label="Temp Slope (°C/min)", color="green")
    ax2.axhline(rate_limit, color="red", linestyle="--",
                label=f"Rate Limit ({rate_limit}°C/min)")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Slope (°C/min)")
    ax2.set_title("Rate of Temperature Change Over Time")
    ax2.legend()
    fname2 = f"graphs/{test_index}_slopes_{description}.png"
    fig2.savefig(fname2)
    plt.close(fig2)



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
