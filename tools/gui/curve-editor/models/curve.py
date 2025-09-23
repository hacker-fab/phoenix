from __future__ import annotations

from dataclasses import dataclass, field

# Lightweight curve data model (control points kept sorted by X).
ControlPoint = list[float]
ControlPoints = list[ControlPoint]


@dataclass
class Curve:
    x_max: float = 1400.0
    y_min: float = 25.0
    y_max: float = 1200.0
    _cv_points: ControlPoints = field(
        default_factory=lambda: [
            [0.0, 25.0],
            [200.0, 1100.0],
            [1200.0, 1100.0],
            [1400.0, 25.0],
        ]
    )

    def __post_init__(self) -> None:
        # Normalize numeric types then sort points
        self.x_max = float(self.x_max)
        self.y_min = float(self.y_min)
        self.y_max = float(self.y_max)
        self.build_curve()

    def set_axis_scales(self, x_max: float, y_min: float, y_max: float) -> None:
        self.x_max = float(x_max)
        self.y_min = float(y_min)
        self.y_max = float(y_max)

    def get_cv_points(self) -> ControlPoints:
        return self._cv_points  # Internal list (mutated by widget code)

    def build_curve(self) -> None:
        self._cv_points.sort(key=lambda v: v[0])

    def set_cv_value(self, index: int, x_value: float, y_value: float) -> None:
        self._cv_points[index] = [float(x_value), float(y_value)]

    def add_cv_point(self, x_value: float, y_value: float) -> None:
        self._cv_points.append([float(x_value), float(y_value)])
        self.build_curve()


__all__ = ["Curve", "ControlPoint", "ControlPoints"]
