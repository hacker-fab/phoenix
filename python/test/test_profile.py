import pytest
from sim_profile import simulate_profile, ThermalModel

@pytest.mark.parametrize(
    "profile, sim_time, tolerance",
    [
        (
            [(0, 25), (300, 200), (600, 500), (900, 800), (1200, 1000)],
            1800,  # total simulation time in seconds
            10.0   # allowed tolerance in °C at each breakpoint
        ),
        (
            [(0, 25.0),  (300, 200), (600, 500), (900, 800), (1200, 1000),  (1400, 1000), (1500, 900), (1800, 900), (2000, 600), ],
            3600,
            10.0
        ),
    ],
)
def test_profile_breakpoints(profile, sim_time, tolerance):
    """
    Run the profile simulation and verify that at each profile breakpoint
    the simulation temperature is within the specified tolerance of the
    expected setpoint.
    """
    # Create a thermal model configuration.
    model = ThermalModel(
            ambient=25.0,
            max_heating_rate=2.0,  # °C/s at full power
            cooling_coeff=0.01
            )
    times, temperatures, setpoints, pwm_values, pid_outputs = simulate_profile(profile, model, sim_time, dt=0.1)

    # For each breakpoint in the profile, check that the simulation temperature
    # (at the time point closest to the breakpoint) is within tolerance.
    for expected_time, expected_temp in profile:
        # Find index of the simulation time closest to the breakpoint time.
        idx = min(range(len(times)), key=lambda i: abs(times[i] - expected_time))
        sim_time_at_idx = times[idx]
        sim_temp = temperatures[idx]
        assert abs(sim_temp - expected_temp) < tolerance, (
                f"At time {sim_time_at_idx:.1f}s, expected temperature {expected_temp:.1f}°C, "
                f"got {sim_temp:.1f}°C, which exceeds the tolerance of {tolerance}°C."
                )
