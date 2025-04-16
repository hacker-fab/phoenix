from typing import List, Tuple


def piecewise_linear_setpoint(current_time: float, profile: List[Tuple[float, float]]) -> float:
    """
    Given a list of (time, temperature) points sorted by time,
    returns the desired temperature at current_time using linear interpolation.
    """
    # If we're before the first point, return its temperature.
    if current_time <= profile[0][0]:
        return profile[0][1]
    # If we're beyond the last point, return its temperature.
    if current_time >= profile[-1][0]:
        return profile[-1][1]

    # Otherwise, find the two points that bracket current_time.
    for i in range(len(profile) - 1):
        t1, T1 = profile[i]
        t2, T2 = profile[i + 1]
        if t1 <= current_time <= t2:
            # Interpolate linearly between (t1, T1) and (t2, T2).
            fraction = (current_time - t1) / (t2 - t1)
            return T1 + fraction * (T2 - T1)

    # Fallback (should never happen if profile is well-formed).
    return profile[-1][1]


def validate_profile_rate(profile: List[Tuple[float, float]], max_rate: float, rate_unit: str = "deg/min") -> List[Tuple[int, float]]:
    """
    Check that the slope between consecutive points in the profile does not exceed the specified max rate.

    Parameters:
        profile: List of (time, temperature) pairs. Time is in seconds, temperature in °C.
        max_rate: Maximum allowed rate.
                  If rate_unit=="deg/min", then max_rate is in °C per minute.
                  If rate_unit=="deg/s", then max_rate is in °C per second.
        rate_unit: String specifying the unit of max_rate. Default is "deg/min".

    Returns:
        A list of violations. Each violation is a tuple: (index, computed_slope),
        where index is the starting index of the segment in the profile for which
        the absolute slope exceeds max_rate. If the list is empty, the profile is valid.
    """
    violations = []
    for i in range(len(profile) - 1):
        t1, T1 = profile[i]
        t2, T2 = profile[i + 1]
        dt = t2 - t1
        if dt <= 0:
            # Skip or raise an error if time is non-increasing.
            continue  # or: raise ValueError(f"Non-positive time difference at index {i}")
        dT = T2 - T1
        # Calculate slope in the desired unit.
        if rate_unit == "deg/min":
            # Convert deg/s to deg/min by multiplying by 60.
            slope = (dT / dt) * 60
        elif rate_unit == "deg/s":
            slope = dT / dt
        else:
            raise ValueError(f"Unknown rate_unit: {rate_unit}")

        if abs(slope) > max_rate:
            violations.append((i, slope))

    return violations
