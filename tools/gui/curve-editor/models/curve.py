"""
Curve model providing linear interpolation between control points.

This module separates the data/model responsibilities from the Qt widget
implementation (see widgets/curve_widget.py).  The Curve class is intentionally
light‑weight and framework agnostic so it can be re-used or unit tested
independently.

Design notes:
- Control points are stored as a list of 2-item float lists: [[x, y], ...]
  (list of lists instead of tuples) to remain compatible with existing code
  that mutates the inner lists by re-assignment (e.g. replacing an element).
- Public API mirrors the previous in-widget implementation for drop‑in use.
- All methods include type hints and docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable


ControlPoint = list[float]  # [x, y]
ControlPoints = list[ControlPoint]  # collection alias


@dataclass
class Curve:
    """
    Represents a 2D curve defined by ordered control points and provides
    linear interpolation between those points.

    Attributes
    ----------
    x_max : float
        Maximum X axis value (domain upper bound).
    y_min : float
        Minimum Y axis value (range lower bound).
    y_max : float
        Maximum Y axis value (range upper bound).
    _cv_points : list[list[float]]
        Internal mutable list of control points. Each point is [x, y].
        Points are expected (but not strictly required) to be within the
        configured axis scales. They are kept sorted by X via build_curve().
    """

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

    # --------------------------------------------------------------------- #
    # Initialization / configuration
    # --------------------------------------------------------------------- #
    def __post_init__(self) -> None:
        """
        Normalize numeric types and ensure control points are sorted.
        """
        # Coerce to float explicitly (in case ints are passed)
        self.x_max = float(self.x_max)
        self.y_min = float(self.y_min)
        self.y_max = float(self.y_max)
        self.build_curve()

    def set_axis_scales(self, x_max: float, y_min: float, y_max: float) -> None:
        """
        Update axis scale values.

        Parameters
        ----------
        x_max : float
            New maximum X value.
        y_min : float
            New minimum Y value.
        y_max : float
            New maximum Y value (must be > y_min for meaningful interpolation).
        """
        self.x_max = float(x_max)
        self.y_min = float(y_min)
        self.y_max = float(y_max)

    # --------------------------------------------------------------------- #
    # Control point management
    # --------------------------------------------------------------------- #
    def get_cv_points(self) -> ControlPoints:
        """
        Return the current list of control points.

        Returns
        -------
        list[list[float]]
            The internal list (NOT a copy). Caller should treat it as read-only
            unless deliberately mutating. Widget code historically mutates it.
        """
        return self._cv_points

    def build_curve(self) -> None:
        """
        Sort control points by X coordinate (stable) to maintain correct
        linear interpolation behavior.
        """
        self._cv_points.sort(key=lambda v: v[0])

    def set_cv_value(self, index: int, x_value: float, y_value: float) -> None:
        """
        Update the control point at the specified index.

        Parameters
        ----------
        index : int
            Index of the control point to update.
        x_value : float
            New X coordinate.
        y_value : float
            New Y coordinate.
        """
        self._cv_points[index] = [float(x_value), float(y_value)]

    def add_cv_point(self, x_value: float, y_value: float) -> None:
        """
        Add a new control point and re-sort the curve.

        Parameters
        ----------
        x_value : float
            X coordinate of the new point.
        y_value : float
            Y coordinate of the new point.
        """
        self._cv_points.append([float(x_value), float(y_value)])
        self.build_curve()

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"Curve(x_max={self.x_max}, y_min={self.y_min}, y_max={self.y_max}, points={self._cv_points})"


__all__ = ["Curve", "ControlPoint", "ControlPoints"]
