from typing import List


class RunningAverage:
    """A simple running average calculator."""

    def __init__(self, size: int):
        self.size = size
        self.values: List[float] = []

    def add(self, value: float) -> None:
        self.values.append(value)
        if len(self.values) > self.size:
            self.values.pop(0)

    def average(self) -> float:
        return sum(self.values) / len(self.values) if self.values else 0.0

    def clear(self) -> None:
        self.values.clear()
