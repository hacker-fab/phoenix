import matplotlib.pyplot as plt
import sim

def main() -> None:
    # Run simulation and get extended debug data.
    (times,
     temperatures,
     pwm_values,
     pid_outputs,
     ramp_rates,
     errors,
     p_vals,
     i_vals,
     d_vals,
     desired_ramp_rates,
     instantaneous_ramp_rates,
     heating_values,
     cooling_values) = sim.simulate_tube_furnace(
        config=sim.ThermalModel(
            target=1000.0,
            ambient=25.0,
            max_heating_rate=1.0,
            cooling_coeff=0.0001,
        ),
        sim_time=60 * 60,
        dt=0.1,
    )

    # Window 1: Temperature and PWM over time.
    fig, ax1 = plt.subplots()
    ax1.plot(times, pwm_values, label="PWM", color="red")
    ax1.set_ylabel("PWM (fraction, 0-1)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")
    ax2 = ax1.twinx()
    ax2.plot(times, temperatures, label="Temperature (°C)", color="blue")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Temperature (°C)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    plt.title("Tube Furnace: Temperature and PWM")
    fig.tight_layout()
    plt.show()

    # Window 2: PID Output and Ramp Rate.
    fig, ax1 = plt.subplots()
    ax1.plot(times, pid_outputs, label="PID Output", color="purple")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("PID Output", color="purple")
    ax1.tick_params(axis="y", labelcolor="purple")
    ax2 = ax1.twinx()
    ax2.plot(times, ramp_rates, label="Ramp Rate (°C/min)", color="green")
    ax2.set_ylabel("Ramp Rate (°C/min)", color="green")
    ax2.tick_params(axis="y", labelcolor="green")
    plt.title("PID Output and Ramp Rate")
    fig.tight_layout()
    plt.show()

    # Window 3: PID Internals.
    fig, ax = plt.subplots()
    ax.plot(times, errors, label="Error", color="black")
    ax.plot(times, p_vals, label="P-term", color="blue")
    ax.plot(times, i_vals, label="I-term", color="green")
    ax.plot(times, d_vals, label="D-term (avg)", color="orange")
    ax.plot(times, desired_ramp_rates, label="Desired Ramp", color="purple")
    ax.plot(times, instantaneous_ramp_rates, label="Instantaneous Ramp", color="brown")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("PID Internal Values")
    ax.legend(loc='upper right')
    plt.title("PID Internal Debug Values")
    fig.tight_layout()
    plt.show()

    # Window 4: Physical Model Contributions.
    fig, ax = plt.subplots()
    ax.plot(times, heating_values, label="Heating", color="red")
    ax.plot(times, cooling_values, label="Cooling", color="cyan")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Heating/Cooling (°C/s)")
    ax.legend(loc='upper right')
    plt.title("Heating and Cooling Contributions")
    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
