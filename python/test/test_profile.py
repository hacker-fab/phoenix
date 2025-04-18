import pytest
from sim_profile import simulate_profile, ThermalModel
from profile import validate_profile_rate


# Test 1: Convergence with profile and rate limit checking
@pytest.mark.parametrize(
    "model, profile, rate_limit, sim_time, tolerance",
    [
        # Example that should pass:
        # The profile ramp from 25°C to 100°C in 600s and 100°C to 200°C in 600s has slopes:
        #   (100-25)/600*60 = 7.5 °C/min and (200-100)/600*60 = 10 °C/min,
        # both below the 30 °C/min limit.
        (
            ThermalModel(
                ambient=25.0,
                max_heating_rate=2.0,  # °C/s at full power
                cooling_coeff=0.01,
            ),
            [(0, 25), (600, 100), (1200, 200)],
            30.0,  # maximum allowed ramp rate in °C/min
            1800.0,  # simulate for 1800 seconds (30 mins)
            5.0,  # tolerance in °C for convergence
        ),
    ],
)
def test_profile_convergence_and_rate_limit(model, profile, rate_limit, sim_time, tolerance):
    """
    Test that the simulation following a given piecewise-linear profile:
      - Has a profile that does not exceed the ramp-rate limit.
      - Converges so that the final temperature is within tolerance of the final setpoint.
      - (Optionally) The observed simulation ramp rate is within the limit.
    """
    # First, validate the profile itself.
    violations = validate_profile_rate(profile, rate_limit, rate_unit="deg/min")
    assert len(violations) == 0, f"Profile violates the rate limit: {violations}"

    # Run the profile simulation.
    times, temperatures, setpoints, pwm_values, pid_outputs = simulate_profile(profile, model, sim_time, dt=0.1)

    # Check convergence at the final breakpoint.
    final_setpoint = setpoints[-1]
    final_temp = temperatures[-1]
    assert abs(final_temp - final_setpoint) < tolerance, (
        f"Final temperature {final_temp}°C differs from final setpoint {final_setpoint}°C by more than {tolerance}°C."
    )

    # (Optional) Check that the simulated ramp rates do not exceed the rate limit (with a small extra tolerance).
    max_simulated_ramp = max(abs((temperatures[i + 1] - temperatures[i]) / 0.1 * 60) for i in range(len(temperatures) - 1))
    assert max_simulated_ramp <= rate_limit + 1.0, (
        f"Simulated ramp rate {max_simulated_ramp:.2f}°C/min exceeds allowed limit of {rate_limit}°C/min (plus tolerance)."
    )


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
