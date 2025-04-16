from running_average import RunningAverage

S_PER_MIN = 60  # Constant to convert per-second values to per-minute
N_RAMP_AVG = 10  # Number of values to average for ramp rate smoothing
N_DVAL_AVG = 10  # Number of values to average for derivative smoothing


def to_pwm(pid_output: float) -> float:
    """Map the PID output to a PWM percentage (0-100%)."""
    return 0.0 if pid_output < 0 else min(pid_output, 1.0)


class RampSoak:
    """
    PID controller with ramp limiting and integrator windup protection.

    Attributes:
        kp, ki, kd: PID gains.
        imax: Maximum absolute value for the integrator.
        ramp_up_limit, ramp_down_limit: Limits on the ramp rate (deg/min).
        crossover_distance: Distance for ramp transitions.
        debug: If True, prints detailed PID debug info.
    """
    def __init__(
        self,
        kp: float = 0.5,
        ki: float = 0.05,
        kd: float = 1.0,
        imax: float = 100.0,
        ramp_up_limit: float = 30,
        ramp_down_limit: float = -30,
        crossover_distance: float = 10,
        debug: bool = False,
    ) -> None:
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
        self.instantaneous_ramp = 0.0  # New: instantaneous ramp rate (°C/min) before averaging
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
        print(
            f"current: {self.current_val:.2f}, target: {self.target_val:.2f}, "
            f"ramp_rate: {self.ramp_rate:.2f}, desired_ramp_rate: {self.desired_ramp_rate:.2f}, "
            f"error: {self.error:.2f}, P: {self.p_val:.2f}, I: {self.i_val:.2f}, "
            f"D: {self.d_val_avg.average():.2f}, kp: {self.kp:.2f}, ki: {self.ki:.2f}, kd: {self.kd:.2f}"
        )

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
        # Calculate instantaneous ramp rate (°C/min)
        if self.prev_val is None:
            self.instantaneous_ramp = 0.0
        else:
            self.instantaneous_ramp = S_PER_MIN * (current_val - self.prev_val) / dt

        self.ramp_rate_avg.add(self.instantaneous_ramp)
        self.ramp_rate = self.ramp_rate_avg.average()
        self.prev_val = current_val

        prev_error = self.error

        # Ramp limiting logic
        if current_val < self.target_val:
            self.desired_ramp_rate = min(
                self.ramp_up_limit,
                self.ramp_up_limit * abs(self.target_val - current_val) / self.crossover_distance,
            )
            self.error = self.desired_ramp_rate - self.ramp_rate
        elif current_val > self.target_val:
            self.desired_ramp_rate = max(
                self.ramp_down_limit,
                self.ramp_down_limit * abs(self.target_val - current_val) / self.crossover_distance,
            )
            self.error = self.desired_ramp_rate - self.ramp_rate
        else:
            self.error = self.target_val - current_val

        self.p_val = self.kp * self.error
        self.i_val += self.ki * self.error * dt
        self.d_val = self.kd * (self.error - prev_error) / dt if dt > 0 else 0.0

        self.i_val = max(min(self.i_val, self.imax), -self.imax)

        if self.debug:
            self.debug_pid()

        self.d_val_avg.add(self.d_val)
        return self.p_val + self.i_val + self.d_val_avg.average()
