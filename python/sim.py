from dataclasses import dataclass
from typing import List, Tuple

import pid

@dataclass
class ThermalModel:
    target: float               # Target temperature (°C)
    ambient: float              # Ambient temperature (°C)
    max_heating_rate: float     # Maximum heating rate (°C/s at 100% power)
    cooling_coeff: float        # Cooling coefficient

def simulate_tube_furnace(config: ThermalModel, sim_time, dt: float = 0.1) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
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

    rs = pid.RampSoak(kp=0.5, ki=0.05, kd=1.0, imax=100.0,
                      ramp_up_limit=30, ramp_down_limit=-30, crossover_distance=10,
                      debug=False)
    rs.set_target(config.target)
    rs.reset_pid()

    current_time = 0.0
    for _ in range(n_steps):
        output = rs.pid_step(temperature, dt)
        pwm = pid.to_pwm(output)
        # Simple model: heating is proportional to PWM, and cooling is proportional to the temperature excess over ambient.
        heating = (pwm / 100.0) * config.max_heating_rate
        cooling = config.cooling_coeff * (temperature - config.ambient)
        temperature += dt * (heating - cooling)
        
        times.append(current_time)
        temperatures.append(temperature)
        pwm_values.append(pwm)
        pid_outputs.append(output)
        ramp_rates.append(rs.ramp_rate)

        current_time += dt

    return times, temperatures, pwm_values, pid_outputs, ramp_rates
