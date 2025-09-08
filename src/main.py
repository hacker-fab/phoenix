import matplotlib.pyplot as plt
from sim import simulate_profile, ThermalModel
from profile import validate_profile_rate


def main() -> None:
    # Define a sample piecewise linear profile:
    # (time_in_seconds, temperature_setpoint)
    heat_profile = [
        (0, 25.0),  # Start at 25 °C
        (300, 200),  # By t=300s, ramp to 200 °C
        (600, 500),  # Then ramp to 500 °C by t=600s
        (900, 800),  # Ramp to 800 °C by t=900s
        (1200, 1000),  # Finally ramp to 1000 °C by t=1200s
        (1400, 1000),
        (1500, 900),
        (1800, 900),
        (2000, 600),
    ]

    model = ThermalModel(
        ambient=25.0,
        max_heating_rate=2.0,  # °C/s at full power
        cooling_coeff=0.001,
    )

    sim_time = 3000.0  # simulate for 1800 seconds (30 minutes)
    dt = 0.1

    # validate profile
    max_allowed_rate = 30.0  # °C per minute
    violations = validate_profile_rate(heat_profile, max_allowed_rate, rate_unit="deg/min")

    if violations:
        for index, slope in violations:
            print(f"Segment starting at index {index} has a slope of {slope:.2f} °C/min, which exceeds {max_allowed_rate} °C/min.")
    else:
        print("Profile is valid: all segments are within the allowed ramp rate.")

    times, temperatures, setpoints, pwm_values, pid_outputs = simulate_profile(heat_profile, model, sim_time, dt)

    # Plot temperature vs. time and the setpoint
    plt.figure()
    plt.plot(times, temperatures, label="Temperature", color="blue")
    plt.plot(times, setpoints, label="Setpoint", color="orange", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Temperature (°C)")
    plt.title("Temperature vs. Setpoint")
    plt.legend()
    plt.show()

    # Plot PWM vs. time
    plt.figure()
    plt.plot(times, pwm_values, label="PWM", color="red")
    plt.xlabel("Time (s)")
    plt.ylabel("PWM [0..1]", color="red")
    plt.title("Heater PWM")
    plt.show()

    # Plot PID output vs. time
    plt.figure()
    plt.plot(times, pid_outputs, label="PID Output", color="purple")
    plt.xlabel("Time (s)")
    plt.ylabel("PID Output (unclamped)")
    plt.title("Raw PID Output")
    plt.show()


if __name__ == "__main__":
    main()
