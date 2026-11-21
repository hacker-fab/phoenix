import math
import sys

if sys.implementation.name == "micropython":
    from udataclasses import dataclass
else:
    from dataclasses import dataclass
from typing import List, Tuple

from pid import SimplePID
from profile import piecewise_linear_setpoint


# TODO udataclasses needs default attributes
@dataclass
class ThermalModel:
    ambient: float = 25.0           # Ambient temperature (°C)
    max_heating_rate: float = 0.0   # Max heating rate at 100% PWM (°C/s)
    cooling_coeff: float = 0.0      # Cooling coefficient


def clamp_pwm(output: float) -> float:
    """Convert an unbounded PID output into a PWM fraction [0..1]."""
    if output < 0:
        return 0.0
    elif output > 1.0:
        return 1.0
    else:
        return output


def simulate_profile(
    profile: List[Tuple[float, float]], model: ThermalModel, sim_time: float, dt: float = 0.1
) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
    """
    Simulate the furnace temperature using a piecewise linear setpoint profile
    and a basic PID control that drives PWM from 0..1.

    Returns:
        times: time in seconds
        temperatures: process temperature
        setpoints: piecewise linear setpoint at each step
        pwm_values: PWM fraction [0..1]
        pid_outputs: raw PID outputs before clamping
    """
    pid_controller = SimplePID(kp=0.5, ki=0.05, kd=1.0, imax=100.0)
    pid_controller.reset()

    # Start from ambient temperature
    temperature = model.ambient

    times = []
    temperatures = []
    setpoints = []
    pwm_values = []
    pid_outputs = []

    current_time = 0.0
    steps = int(sim_time / dt)

    for _ in range(steps):
        # 1) Retrieve the setpoint from the piecewise linear schedule
        setpoint = piecewise_linear_setpoint(current_time, profile)
        # 2) Let the PID compute its control output
        output = pid_controller.compute(setpoint, temperature, dt)
        # 3) Clamp output to [0..1] for PWM
        pwm = clamp_pwm(output)

        # 4) Integrate constant PWM heating and exponential cooling exactly
        # over one timestep. Euler integration can overshoot below ambient
        # when dt * cooling_coeff is large.
        heating = pwm * model.max_heating_rate
        if model.cooling_coeff:
            decay = math.exp(-model.cooling_coeff * dt)
            # expm1 avoids cancellation when cooling_coeff * dt is tiny.
            heating_integral = -math.expm1(-model.cooling_coeff * dt) / model.cooling_coeff
            temperature = (
                model.ambient
                + (temperature - model.ambient) * decay
                + heating * heating_integral
            )
        else:
            temperature += dt * heating

        # Store data
        times.append(current_time)
        temperatures.append(temperature)
        setpoints.append(setpoint)
        pwm_values.append(pwm)
        pid_outputs.append(output)

        current_time += dt

    return times, temperatures, setpoints, pwm_values, pid_outputs
