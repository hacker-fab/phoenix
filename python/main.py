import matplotlib.pyplot as plt
import sim


def main() -> None:
    times, temperatures, pwm_values, pid_outputs, ramp_rates = (
        sim.simulate_tube_furnace(
            config=sim.HeatSimConfig(
                target=1000.0,
                ambient=25.0,
                max_heating_rate=2.0,
                cooling_coeff=0.01,
            ),
            sim_time=60 * 60,
            dt=0.1,
        )
    )

    # Plot Temperature and PWM over time.
    fig, ax1 = plt.subplots()
    ax1.plot(times, temperatures, label="Temperature (°C)", color="blue")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Temperature (°C)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    ax2 = ax1.twinx()
    ax2.plot(times, pwm_values, label="PWM (%)", color="red")
    ax2.set_ylabel("PWM (%)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    plt.title("Tube Furnace Simulation")
    fig.tight_layout()
    plt.show()

    # Plot PID output and ramp rate.
    plt.figure()
    plt.plot(times, pid_outputs, label="PID Output")
    plt.plot(times, ramp_rates, label="Ramp Rate (°C/min)")
    plt.xlabel("Time (s)")
    plt.title("PID Output and Ramp Rate")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
