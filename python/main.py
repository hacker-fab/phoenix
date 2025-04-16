import matplotlib.pyplot as plt
import sim


def main() -> None:
    times, temperatures, pwm_values, pid_outputs, ramp_rates = (
        sim.simulate_tube_furnace(
            config=sim.ThermalModel(
                target=1000.0,
                ambient=25.0,
                max_heating_rate=0.5,
                cooling_coeff=0.0001,
            ),
            sim_time=60 * 60,
            dt=0.1,
        )
    )

    # Plot Temperature and PWM over time.
    fig, ax1 = plt.subplots()

    ax1.plot(times, pwm_values, label="PWM", color="red")
    ax1.set_ylabel("PWM (fraction, 0-1)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    ax2 = ax1.twinx()
    ax2.plot(times, temperatures, label="Temperature (°C)", color="blue")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Temperature (°C)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    plt.title("Tube Furnace Simulation")
    fig.tight_layout()
    plt.show()

    # Plot PID output and ramp rate with a second y-axis for ramp rate.
    fig, ax1 = plt.subplots()
    ax1.plot(times, ramp_rates, label="Ramp Rate (°C/min)", color="green")
    ax1.set_ylabel("Ramp Rate (°C/min)", color="green")
    ax1.tick_params(axis="y", labelcolor="green")

    ax2 = ax1.twinx()
    ax2.plot(times, pid_outputs, label="PID Output", color="purple")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("PID Output", color="purple")
    ax2.tick_params(axis="y", labelcolor="purple")

    plt.title("PID Output and Ramp Rate")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
