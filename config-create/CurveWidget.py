# from __future__ import print_function

import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as QtWidgets


class Curve:
    """Interface to linear interpolation between control points"""

    def __init__(self, x_max=1400, y_min=25, y_max=1200):
        # Axis scale values
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        self._cv_points = [
            [0.0, 25.0],
            [200.0, 1100.0],
            [1200.0, 1100.0],
            [1400.0, 25.0],
        ]

        # Sort points by x coordinate for linear interpolation
        self.build_curve()

    def set_axis_scales(self, x_max, y_min, y_max):
        """Update axis scale values"""
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    def get_cv_points(self):
        """Returns a list of all controll points"""
        return self._cv_points

    def build_curve(self):
        """Sort control points by x coordinate for linear interpolation"""
        # Sort points by x coordinate for proper linear interpolation
        self._cv_points = sorted(self._cv_points, key=lambda v: v[0])

    def set_cv_value(self, index, x_value, y_value):
        """Updates the cv point at the given index"""
        self._cv_points[index] = [x_value, y_value]

    def add_cv_point(self, x_value, y_value):
        """Adds a new control point and rebuilds the curve"""
        self._cv_points.append([x_value, y_value])
        self.build_curve()

    def get_value(self, offset):
        """Returns the value using linear interpolation between control points.
        offset should be from 0 to 1, returns a value from 0 to 1."""
        if not self._cv_points:
            return 0.0

        # Ensure points are sorted by x coordinate
        sorted_points = sorted(self._cv_points, key=lambda v: v[0])

        # Handle edge cases
        if offset <= sorted_points[0][0]:
            return sorted_points[0][1]
        if offset >= sorted_points[-1][0]:
            return sorted_points[-1][1]

        # Find the two points to interpolate between
        for i in range(len(sorted_points) - 1):
            x1, y1 = sorted_points[i]
            x2, y2 = sorted_points[i + 1]

            if x1 <= offset <= x2:
                # Linear interpolation
                if x2 == x1:  # Avoid division by zero
                    return y1
                t = (offset - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)

        return 0.0


class CurveWidget(QtWidgets.QWidget):
    """This is a resizeable Widget which shows an editable curve which can
    be modified."""

    def __init__(self, parent):
        """Constructs the CurveWidget, we start with an initial curve"""
        super().__init__(parent)

        # Single curve
        self.curve = Curve()

        # Widget render constants
        self._cv_point_size = 6
        self._legend_border = 35
        self._control_bar_height = 40
        self._padding = 12

        # Currently dragged control point, format is:
        # (PointIndex, Drag-Offset (x,y))
        self._drag_point = None

        # Currently selected control point index
        self._selected_point = None

        # Create control widgets
        self._create_controls()

    def _create_controls(self):
        """Create the control widgets for axis scaling"""
        # X-axis max control
        self.x_max_label = QtWidgets.QLabel("X Max:")
        self.x_max_spinbox = QtWidgets.QSpinBox()
        self.x_max_spinbox.setRange(100, 10000)
        self.x_max_spinbox.setValue(1400)
        self.x_max_spinbox.valueChanged.connect(self._update_scales)

        # Y-axis min control
        self.y_min_label = QtWidgets.QLabel("Y Min:")
        self.y_min_spinbox = QtWidgets.QSpinBox()
        self.y_min_spinbox.setRange(0, 1000)
        self.y_min_spinbox.setValue(25)
        self.y_min_spinbox.valueChanged.connect(self._update_scales)

        # Y-axis max control
        self.y_max_label = QtWidgets.QLabel("Y Max:")
        self.y_max_spinbox = QtWidgets.QSpinBox()
        self.y_max_spinbox.setRange(100, 10000)
        self.y_max_spinbox.setValue(1200)
        self.y_max_spinbox.valueChanged.connect(self._update_scales)

    def _update_scales(self):
        """Update the curve axis scales when controls change"""
        x_max = self.x_max_spinbox.value()
        y_min = self.y_min_spinbox.value()
        y_max = self.y_max_spinbox.value()

        # Ensure y_max > y_min
        if y_max <= y_min:
            y_max = y_min + 100
            self.y_max_spinbox.setValue(y_max)

        self.curve.set_axis_scales(x_max, y_min, y_max)
        self.update()

    def paintEvent(self, e):
        """Internal QT paint event, draws the entire widget"""
        qp = QtGui.QPainter()
        qp.begin(self)
        self._draw(qp)
        qp.end()

    def mousePressEvent(self, QMouseEvent):
        """Internal mouse-press handler"""
        self._drag_point = None
        self._selected_point = None
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x()
        mouse_y = mouse_pos.y()

        for cv_index, (x, y) in enumerate(self.curve.get_cv_points()):
            point_x = self._get_x_value_for(x)
            point_y = self._get_y_value_for(y)

            # Check if mouse is close to this control point
            if abs(point_x - mouse_x) < self._cv_point_size + 4:
                if abs(point_y - mouse_y) < self._cv_point_size + 4:
                    # Store the offset from mouse to point center in screen coordinates
                    drag_x_offset = point_x - mouse_x
                    drag_y_offset = point_y - mouse_y
                    self._drag_point = (cv_index, (drag_x_offset, drag_y_offset))
                    self._selected_point = cv_index
                    break

        self.update()

    def mouseReleaseEvent(self, QMouseEvent):
        """Internal mouse-release handler"""
        self._drag_point = None

    def mouseDoubleClickEvent(self, QMouseEvent):
        """Internal mouse-double-click handler - adds new control point"""
        mouse_pos = QMouseEvent.pos()
        mouse_x = mouse_pos.x() - self._legend_border - self._padding
        mouse_y = mouse_pos.y() - self._padding

        # Convert to coordinate range using current axis scales
        local_x = max(0, min(self.curve.x_max, mouse_x / float(self.width() - self._legend_border - 2 * self._padding) * self.curve.x_max))
        local_y = max(
            self.curve.y_min,
            min(
                self.curve.y_max,
                (1 - mouse_y / float(self.height() - self._legend_border - self._control_bar_height - 2 * self._padding))
                * (self.curve.y_max - self.curve.y_min)
                + self.curve.y_min,
            ),
        )

        # Add new control point
        self.curve.add_cv_point(local_x, local_y)
        self.update()

    def mouseMoveEvent(self, QMouseEvent):
        """Internal mouse-move handler"""
        if self._drag_point is not None:
            # Get current mouse position in screen coordinates
            mouse_pos = QMouseEvent.pos()

            # Apply the drag offset to get the desired point position in screen coordinates
            point_screen_x = mouse_pos.x() + self._drag_point[1][0]
            point_screen_y = mouse_pos.y() + self._drag_point[1][1]

            # Convert from screen coordinates to graph coordinates
            graph_x = point_screen_x - self._legend_border - self._padding
            graph_y = point_screen_y - self._padding

            # Get graph dimensions
            graph_width = self.width() - self._legend_border - 2 * self._padding
            graph_height = self.height() - self._legend_border - self._control_bar_height - 2 * self._padding

            # Convert to data coordinates using current axis scales
            # X coordinate: normalize by graph width, then scale to x_max
            local_x = max(0, min(self.curve.x_max, graph_x / float(graph_width) * self.curve.x_max))

            # Y coordinate: flip Y axis (screen Y increases downward, data Y increases upward)
            # then normalize and scale to y range
            normalized_y = 1.0 - (graph_y / float(graph_height))
            local_y = max(self.curve.y_min, min(self.curve.y_max, normalized_y * (self.curve.y_max - self.curve.y_min) + self.curve.y_min))

            # Update the control point
            self.curve.set_cv_value(self._drag_point[0], local_x, local_y)

            # Rebuild curve and update display
            self.curve.build_curve()
            self.update()

    def _get_y_value_for(self, local_value):
        """Converts a value from y_min-y_max to canvas height"""
        y_range = self.curve.y_max - self.curve.y_min
        normalized_value = (local_value - self.curve.y_min) / y_range  # Normalize to 0-1
        normalized_value = max(0, min(1.0, 1.0 - normalized_value))  # Flip Y and clamp
        local_value = (
            normalized_value * (self.height() - self._legend_border - self._control_bar_height - 2 * self._padding) + self._padding
        )
        return local_value

    def _get_x_value_for(self, local_value):
        """Converts a value from 0-x_max to canvas width"""
        normalized_value = local_value / self.curve.x_max  # Normalize to 0-1
        normalized_value = max(0, min(1.0, normalized_value))
        local_value = normalized_value * (self.width() - self._legend_border - 2 * self._padding) + self._legend_border + self._padding
        return local_value

    def _draw(self, painter):
        """Internal method to draw the widget"""

        canvas_width = self.width() - self._legend_border - 2 * self._padding
        canvas_height = self.height() - self._legend_border - self._control_bar_height - 2 * self._padding

        # Draw field background
        palette = self.palette()
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Mid))
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Base))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        # Draw legend

        # Compute amount of horizontal / vertical lines
        num_vert_lines = 7  # Adjustable based on x_max
        line_spacing_x = (self.width() - self._legend_border - 2 * self._padding) / 7.0
        line_spacing_y = (self.height() - self._legend_border - self._control_bar_height - 2 * self._padding) / 10.0
        num_horiz_lines = 11  # Adjustable based on y range

        # Draw vertical lines
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Window))
        for i in range(num_vert_lines + 1):
            line_pos = i * line_spacing_x + self._legend_border + self._padding
            painter.drawLine(int(line_pos), self._padding, int(line_pos), canvas_height + self._padding)

        # Draw horizontal lines
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Window))
        for i in range(num_horiz_lines):
            line_pos = canvas_height - i * line_spacing_y + self._padding
            painter.drawLine(self._legend_border, int(line_pos), self.width(), int(line_pos))

        # Draw vertical legend labels (Y-axis values)
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Text))
        y_range = self.curve.y_max - self.curve.y_min
        for i in range(num_horiz_lines):
            line_pos = canvas_height - i * line_spacing_y + self._padding
            value = int(self.curve.y_min + (y_range * i / (num_horiz_lines - 1)))
            painter.drawText(6, int(line_pos + 3), str(value))

        # Draw horizontal legend labels (X-axis values)
        for i in range(num_vert_lines + 1):
            line_pos = i * line_spacing_x + self._legend_border + self._padding
            offpos_x = -14
            if i == 0:
                offpos_x = -2
            elif i == num_vert_lines:
                offpos_x = -33
            value = int(self.curve.x_max * i / num_vert_lines)
            painter.drawText(int(line_pos + offpos_x), canvas_height + self._padding + 18, str(value))

        # Draw control bar background
        control_bar_y = canvas_height + self._padding + 25
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Mid))
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Window))
        painter.drawRect(0, control_bar_y, self.width(), self._control_bar_height)

        # Position control widgets
        self._position_controls(control_bar_y)

        # Draw curve as straight lines between control points
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Text))
        cv_points = self.curve.get_cv_points()

        # Sort points by x coordinate for drawing
        sorted_points = sorted(cv_points, key=lambda v: v[0])

        # Draw lines between consecutive control points
        for i in range(len(sorted_points) - 1):
            x1, y1 = sorted_points[i]
            x2, y2 = sorted_points[i + 1]

            # Convert to screen coordinates
            screen_x1 = self._get_x_value_for(x1)
            screen_y1 = self._get_y_value_for(y1)
            screen_x2 = self._get_x_value_for(x2)
            screen_y2 = self._get_y_value_for(y2)

            painter.drawLine(int(screen_x1), int(screen_y1), int(screen_x2), int(screen_y2))

        # Draw the CV points of the curve
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Base))

        for cv_index, (x, y) in enumerate(self.curve.get_cv_points()):
            offs_x = self._get_x_value_for(x)
            offs_y = self._get_y_value_for(y)

            if self._selected_point == cv_index:
                painter.setPen(palette.color(QtGui.QPalette.ColorRole.Highlight))
            else:
                painter.setPen(palette.color(QtGui.QPalette.ColorRole.Dark))
            painter.drawRect(
                int(offs_x - self._cv_point_size), int(offs_y - self._cv_point_size), 2 * self._cv_point_size, 2 * self._cv_point_size
            )

    def _position_controls(self, y_pos):
        """Position the control widgets at the bottom"""
        x_offset = 10

        # X Max control
        self.x_max_label.setParent(self)
        self.x_max_label.move(x_offset, y_pos + 10)
        self.x_max_label.show()

        self.x_max_spinbox.setParent(self)
        self.x_max_spinbox.move(x_offset + 50, y_pos + 8)
        self.x_max_spinbox.resize(80, 25)
        self.x_max_spinbox.show()

        # Y Min control
        x_offset += 150
        self.y_min_label.setParent(self)
        self.y_min_label.move(x_offset, y_pos + 10)
        self.y_min_label.show()

        self.y_min_spinbox.setParent(self)
        self.y_min_spinbox.move(x_offset + 50, y_pos + 8)
        self.y_min_spinbox.resize(80, 25)
        self.y_min_spinbox.show()

        # Y Max control
        x_offset += 150
        self.y_max_label.setParent(self)
        self.y_max_label.move(x_offset, y_pos + 10)
        self.y_max_label.show()

        self.y_max_spinbox.setParent(self)
        self.y_max_spinbox.move(x_offset + 50, y_pos + 8)
        self.y_max_spinbox.resize(80, 25)
        self.y_max_spinbox.show()
