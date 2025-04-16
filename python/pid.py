def clamp(value: float, lower: float, upper: float) -> float:
    return max(min(value, upper), lower)

class SimplePID:
    """
    A basic PID controller (no ramp-limiting).
    
    Attributes:
        kp, ki, kd: PID gains.
        imax: Maximum absolute value for the integrator (prevents windup).
        debug: If True, prints PID debug info each step.
    """

    def __init__(self, kp=0.5, ki=0.05, kd=1.0, imax=100.0, debug=False):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.imax = imax
        self.debug = debug
        
        self.error = 0.0
        self.prev_error = 0.0
        self.integral = 0.0

    def reset(self) -> None:
        """Reset integrator and error terms."""
        self.error = 0.0
        self.prev_error = 0.0
        self.integral = 0.0

    def compute(self, setpoint: float, measurement: float, dt: float) -> float:
        """
        Compute the PID output for the given setpoint and measurement.
        """
        self.error = setpoint - measurement
        self.integral += self.ki * self.error * dt
        self.integral = clamp(self.integral, -self.imax, self.imax)
        
        derivative = (self.error - self.prev_error) / dt if dt > 0 else 0.0
        
        p_term = self.kp * self.error
        i_term = self.integral
        d_term = self.kd * derivative
        
        output = p_term + i_term + d_term
        
        if self.debug:
            print(f"[PID DEBUG] error={self.error:.2f} p={p_term:.2f} i={i_term:.2f} d={d_term:.2f} out={output:.2f}")
        
        self.prev_error = self.error
        return output
