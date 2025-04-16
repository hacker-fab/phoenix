from dataclasses import dataclass
import math
import matplotlib.pyplot as plt
from typing import List, Tuple

S_PER_MIN = 60  # Constant to convert per-second values to per-minute
N_RAMP_AVG = 10  # Number of values to average for ramp rate smoothing
N_DVAL_AVG = 10  # Number of values to average for derivative smoothing

class RampSoakPID:
    """
    PID controller with ramp limiting and integrator windup protection.
    
    Attributes:
        kp, ki, kd: PID gains.
        imax: Maximum absolute value for the integrator.
        ramp_up_limit, ramp_down_limit: Limits on the ramp rate (deg/min).
        crossover_distance: Distance for ramp transitions.
        debug: If True, prints detailed PID debug info.
    """
    def __init__(self, 
                 kp: float = 0.5, 
                 ki: float = 0.05, 
                 kd: float = 1.0, 
                 imax: float = 100.0,
                 ramp_up_limit: float = 30, 
                 ramp_down_limit: float = -30, 
                 crossover_distance: float = 10,
                 debug: bool = False) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.imax = imax
        self.ramp_up_limit = ramp_up_limit
        self.ramp_down_limit = ramp_down_limit
        self.crossover_distance = crossover_distance
        self.debug = debug

        # PID state variables
        self.error = 0.0
        self.p_val = 0.0
        self.i_val = 0.0
        self.d_val = 0.0
        self.current_val = 0.0
        self.target_val = 0.0

        # Instead of time tracking, we now only keep the previous measurement.
        self.prev_val: float | None = None

        # Ramp rate and smoothing
        self.ramp_rate = 0.0
        self.desired_ramp_rate = 0.0
        self.ramp_rate_avg = RunningAverage(N_RAMP_AVG)
        self.d_val_avg = RunningAverage(N_DVAL_AVG)

    def reset_pid(self) -> None:
        """Reset the time-dependent PID state."""
        self.prev_val = None
        self.error = 0.0
        self.i_val = 0.0
        self.ramp_rate = 0.0

    def set_target(self, target: float) -> None:
        """Set the desired target value (setpoint)."""
        self.target_val = target

    def debug_pid(self) -> None:
        """Print detailed debugging information about the PID state."""
        print(f"current: {self.current_val:.2f}, target: {self.target_val:.2f}, "
              f"ramp_rate: {self.ramp_rate:.2f}, desired_ramp_rate: {self.desired_ramp_rate:.2f}, "
              f"error: {self.error:.2f}, P: {self.p_val:.2f}, I: {self.i_val:.2f}, "
              f"D: {self.d_val_avg.average():.2f}, kp: {self.kp:.2f}, ki: {self.ki:.2f}, kd: {self.kd:.2f}")

    def pid_step(self, current_val: float, dt: float) -> float:
        """
        Compute the PID control output.
        
        Args:
            current_val: Measured process variable (e.g., temperature in °C).
            dt: Time difference (in seconds) since the last PID step.
            
        Returns:
            The PID control output.
        """
        self.current_val = current_val
        # If there's no previous value, initialize it.
        if self.prev_val is None:
            instantaneous_ramp = 0.0
        else:
            instantaneous_ramp = S_PER_MIN * (current_val - self.prev_val) / dt

        self.ramp_rate_avg.add(instantaneous_ramp)
        self.ramp_rate = self.ramp_rate_avg.average()
        self.prev_val = current_val

        prev_error = self.error

        # Ramp limiting logic based on whether the process is ramping up or down.
        if current_val < self.target_val:
            self.desired_ramp_rate = min(self.ramp_up_limit,
                                         self.ramp_up_limit * abs(self.target_val - current_val) / self.crossover_distance)
            self.error = self.desired_ramp_rate - self.ramp_rate
        elif current_val > self.target_val:
            self.desired_ramp_rate = max(self.ramp_down_limit,
                                         self.ramp_down_limit * abs(self.target_val - current_val) / self.crossover_distance)
            self.error = self.desired_ramp_rate - self.ramp_rate
        else:
            self.error = self.target_val - current_val

        # Compute PID contributions.
        self.p_val = self.kp * self.error
        self.i_val += self.ki * self.error * dt
        self.d_val = self.kd * (self.error - prev_error) / dt if dt > 0 else 0.0

        # Integrator windup protection.
        self.i_val = max(min(self.i_val, self.imax), -self.imax)

        if self.debug:
            self.debug_pid()

        self.d_val_avg.add(self.d_val)
        # Return the combined PID output.
        return self.p_val + self.i_val + self.d_val_avg.average()

def map_pid_to_pwm(pid_output: float, max_pwm: float = 100.0) -> float:
    """Map the PID output to a PWM percentage (0-100%)."""
    return 0.0 if pid_output < 0 else min(pid_output, max_pwm)

@dataclass
class HeatSimConfig:
    target: float               # Target temperature (°C)
    ambient: float              # Ambient temperature (°C)
    max_heating_rate: float     # Maximum heating rate (°C/s at 100% power)
    cooling_coeff: float        # Cooling coefficient

def simulate_tube_furnace(config: HeatSimConfig, sim_time, dt: float = 0.1) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
    """
    Simulate the temperature response of a tube furnace with PID control.
    
    Args:
        sim_time: Total simulation time (in seconds).
        dt: Time step for the simulation (in seconds).
    
    Returns:
        A tuple containing lists of simulation times, temperatures, PWM values,
        PID outputs, and computed ramp rates.
    """
    n_steps = int(sim_time / dt)

    times: List[float] = []
    temperatures: List[float] = []
    pwm_values: List[float] = []
    pid_outputs: List[float] = []
    ramp_rates: List[float] = []

    # Assume start temp = ambient temp
    temperature = config.ambient

    pid = RampSoakPID(kp=0.5, ki=0.05, kd=1.0, imax=100.0,
                      ramp_up_limit=30, ramp_down_limit=-30, crossover_distance=10,
                      debug=False)
    pid.set_target(config.target)
    pid.reset_pid()

    current_time = 0.0
    for _ in range(n_steps):
        output = pid.pid_step(temperature, dt)
        pwm = map_pid_to_pwm(output)
        # Simple model: heating is proportional to PWM, and cooling is proportional to the temperature excess over ambient.
        heating = (pwm / 100.0) * config.max_heating_rate
        cooling = config.cooling_coeff * (temperature - config.ambient)
        temperature += dt * (heating - cooling)
        
        times.append(current_time)
        temperatures.append(temperature)
        pwm_values.append(pwm)
        pid_outputs.append(output)
        ramp_rates.append(pid.ramp_rate)

        current_time += dt

    return times, temperatures, pwm_values, pid_outputs, ramp_rates

def main() -> None:
    times, temperatures, pwm_values, pid_outputs, ramp_rates = simulate_tube_furnace(
            config=HeatSimConfig(
                target=1000.0,
                ambient=25.0,
                max_heating_rate=2.0,
                cooling_coeff=0.01,
                ),
            sim_time=60*S_PER_MIN, 
            dt=0.1)

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
