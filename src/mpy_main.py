from sim import simulate_profile, ThermalModel
from profile import validate_profile_rate


def main() -> None:
    # Define a sample piecewise linear profile:
    # (time_in_seconds, temperature_setpoint)
    heat_profile = [
        (0, 25), (100, 30), (200, 30),
    ]

    model = ThermalModel(
        ambient=25.0,
        max_heating_rate=2.0,  # °C/s at full power
        cooling_coeff=0.001,
    )

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
    tolerance = 1.0

    # 1) Profile validation
    violations = validate_profile_rate(heat_profile, rate_limit, rate_unit="deg/min")
    assert not violations, f"Profile rate violations: {violations}"

    # 2) Run simulation
    dt = 1
    _, temperatures, setpoints, _, _ = simulate_profile(
        heat_profile, model, sim_time, dt
    )

    # 3) Convergence assertion
    final_error = max(abs(a - b) for a, b in zip(temperatures, setpoints))
    assert final_error < tolerance, (
        f"Final temperature error {final_error:.1f}°C exceeds tolerance {tolerance}°C"
    )


if __name__ == "__main__":
    main()
