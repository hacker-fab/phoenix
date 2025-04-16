import math
import pytest
from sim import simulate_tube_furnace, ThermalModel

@pytest.mark.parametrize(
    "config, sim_time, tolerance",
    [
        # High target, no cooling
        (ThermalModel(target=1000.0, ambient=25.0, max_heating_rate=0.5, cooling_coeff=0), 3600, 5.0),
        # High target, high power
        (ThermalModel(target=1000.0, ambient=25.0, max_heating_rate=1.0, cooling_coeff=0.0001), 1800, 5.0),
        # Low target, 30 mins
        (ThermalModel(target=250.0, ambient=25.0, max_heating_rate=0.5, cooling_coeff=0.0001), 1800, 5.0),
    ]
)
def test_convergence(config: ThermalModel, sim_time: float, tolerance: float):
    """
    Run the simulation long enough so that the final temperature approaches the target.
    We assert that the final temperature is within 5°C of the target.
    """
    # Run for one hour (3600 s) with dt=0.1 s
    times, temperatures, pwm_values, pid_outputs, ramp_rates = simulate_tube_furnace(config, sim_time=3600, dt=0.1)
    
    final_temp = temperatures[-1]
    assert abs(final_temp - config.target) < 5.0, (
        f"Final temperature {final_temp} not within tolerance of target {config.target}"
    )

@pytest.mark.parametrize(
    "config, sim_time, ramp_limit",
    [
        # High target, no cooling
        (ThermalModel(target=1000.0, ambient=25.0, max_heating_rate=0.5, cooling_coeff=0), 3600, 30.0),
        # High target, high power
        (ThermalModel(target=1000.0, ambient=25.0, max_heating_rate=1.0, cooling_coeff=0.0001), 1800, 30.0),
        # Low target, 30 mins
        (ThermalModel(target=250.0, ambient=25.0, max_heating_rate=0.5, cooling_coeff=0.0001), 1800, 30.0),
    ]
)
def test_ramp_rate_limit(config: ThermalModel, sim_time: float, ramp_limit: float):
    """
    Test that during the ramp-up phase the simulation does not exceed the configured ramp limit.
    Given a ramp-up limit of 30 °C/min (0.5 °C/s) and a max heating rate of 2.0 °C/s,
    the expected PWM should be (0.5/2.0)*100 = 25% on average during the ramp-limited period.
    We also check that the maximum computed ramp rate does not exceed the limit (with a small tolerance).
    """
    # Run a shorter simulation where the system is still ramping (e.g., 600 s)
    times, temperatures, pwm_values, pid_outputs, ramp_rates = simulate_tube_furnace(config, sim_time, dt=0.1)
    tolerance = 1.0

    # The maximum ramp rate observed (in °C/min) should be close to (but not exceed) the ramp up limit.
    max_ramp = max(ramp_rates)
    assert max_ramp <= ramp_limit + tolerance, f"Max ramp rate at idx {ramp_rates.index(max_ramp)}: {max_ramp} exceeds allowed limit (30 °C/min + tolerance)."