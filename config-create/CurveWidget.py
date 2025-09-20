# from __future__ import print_function

import copy
import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as QtWidgets

# Set to True to enable debug logging for state saves
DEBUG_UNDO = False


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

        sorted_points = sorted(self._cv_points, key=lambda v: v[0])

        if offset <= sorted_points[0][0]:
            return sorted_points[0][1]
        if offset >= sorted_points[-1][0]:
            return sorted_points[-1][1]

        for i in range(len(sorted_points) - 1):
            x1, y1 = sorted_points[i]
            x2, y2 = sorted_points[i + 1]
            if x1 <= offset <= x2:
                if x2 == x1:
                    return y1
                t = (offset - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)

        return 0.0


class CurveWidget(QtWidgets.QWidget):
    """Resizeable widget displaying an editable curve with undo/redo support."""

    def __init__(self, parent):
        super().__init__(parent)

        self.curve = Curve()
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # Widget render constants
        self._cv_point_size = 6
        self._legend_border = 35
        self._control_bar_height = 40
        self._padding = 12

        # Drag / selection tracking
        self._drag_point = None  # (index, (offset_x, offset_y))
        self._selected_point = None
        self._pre_drag_points = None  # deep copy of points at drag start

        # Undo/Redo state history
        self._history = []
        self._history_index = -1
        self._restoring_state = False

        # Build UI
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._create_controls()
        self._setup_shortcuts()

        # Save initial state AFTER widget is ready
        self._push_state("Initial")
        self._update_window_title()

    # ------------------------------------------------------------------
    # Undo/Redo infrastructure
    # ------------------------------------------------------------------
    def _capture_state(self):
        """Return a deep copy snapshot of current logical state."""
        return {
            "cv_points": copy.deepcopy(self.curve._cv_points),
            "x_max": self.curve.x_max,
            "y_min": self.curve.y_min,
            "y_max": self.curve.y_max,
        }

    def _states_equal(self, a, b):
        return a["cv_points"] == b["cv_points"] and a["x_max"] == b["x_max"] and a["y_min"] == b["y_min"] and a["y_max"] == b["y_max"]

    def _push_state(self, action_name="Unknown"):
        """Record current state AFTER a modification."""
        current = self._capture_state()
        # Truncate redo branch if we are not at the end
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]
        # Avoid duplicates
        if self._history and self._states_equal(current, self._history[-1]):
            if DEBUG_UNDO:
                print(f"UNDO DEBUG: skip duplicate after '{action_name}'")
            return
        self._history.append(current)
        self._history_index = len(self._history) - 1
        if DEBUG_UNDO:
            print(f"UNDO DEBUG: push '{action_name}' -> index {self._history_index} / {len(self._history)}")

    # Backwards compatibility (legacy code/tests may call _save_state before modifying)
    def _save_state(self, action_name="Unknown"):
        """Deprecated: kept for backward compatibility.
        Unlike legacy behavior we now snapshot current state (post-mod)."""
        self._push_state(action_name)

    def _undo(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_state(self._history[self._history_index])
            self._update_window_title()
            if DEBUG_UNDO:
                print(f"UNDO DEBUG: undo -> index {self._history_index} / {len(self._history)}")

    def _redo(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_state(self._history[self._history_index])
            self._update_window_title()
            if DEBUG_UNDO:
                print(f"UNDO DEBUG: redo -> index {self._history_index} / {len(self._history)}")

    def _restore_state(self, state):
        self._restoring_state = True
        try:
            self.curve._cv_points = copy.deepcopy(state["cv_points"])
            self.curve.x_max = state["x_max"]
            self.curve.y_min = state["y_min"]
            self.curve.y_max = state["y_max"]

            # Update spin boxes (will not push state due to flag)
            self.x_max_spinbox.setValue(state["x_max"])
            self.y_min_spinbox.setValue(state["y_min"])
            self.y_max_spinbox.setValue(state["y_max"])

            self.curve.build_curve()
            self.update()
        finally:
            self._restoring_state = False

    # ------------------------------------------------------------------
    # UI / shortcuts
    # ------------------------------------------------------------------
    def _setup_shortcuts(self):
        self.undo_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Undo, self)
        self.undo_shortcut.activated.connect(self._undo)
        self.redo_shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Redo, self)
        self.redo_shortcut.activated.connect(self._redo)

    def _update_window_title(self):
        parent_window = self.window()
        if not parent_window:
            return
        base_title = "Qt6 Curve Editor"
        undo_available = self._history_index > 0
        redo_available = self._history_index < len(self._history) - 1
        status_parts = []
        if undo_available:
            status_parts.append("Ctrl+Z: Undo")
        if redo_available:
            status_parts.append("Ctrl+Shift+Z: Redo")
        if status_parts:
            title = f"{base_title} - {' | '.join(status_parts)} | Right-click to delete points | Delete: Remove selected point"
        else:
            title = f"{base_title} - Right-click to delete points | Delete: Remove selected point"
        parent_window.setWindowTitle(title)

    # ------------------------------------------------------------------
    # Context menu / point deletion
    # ------------------------------------------------------------------
    def _show_context_menu(self, position):
        point_index = self._get_point_at_position(position)
        if point_index is None:
            return
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Delete Point")
        if delete_action:
            delete_action.triggered.connect(lambda: self._delete_point(point_index))
        menu.exec(self.mapToGlobal(position))

    def _get_point_at_position(self, position):
        mouse_x = position.x()
        mouse_y = position.y()
        for idx, (x, y) in enumerate(self.curve.get_cv_points()):
            px = self._get_x_value_for(x)
            py = self._get_y_value_for(y)
            if abs(px - mouse_x) < self._cv_point_size + 4 and abs(py - mouse_y) < self._cv_point_size + 4:
                return idx
        return None

    def _delete_point(self, point_index):
        if len(self.curve._cv_points) <= 1:
            return
        # Perform mutation first
        del self.curve._cv_points[point_index]
        if self._selected_point == point_index:
            self._selected_point = None
        elif self._selected_point is not None and self._selected_point > point_index:
            self._selected_point -= 1
        self.curve.build_curve()
        self.update()
        # Save state AFTER deletion
        self._push_state(f"Delete point {point_index}")
        self._update_window_title()

    # ------------------------------------------------------------------
    # Axis scale controls
    # ------------------------------------------------------------------
    def _create_controls(self):
        self.x_max_label = QtWidgets.QLabel("X Max:")
        self.x_max_spinbox = QtWidgets.QSpinBox()
        self.x_max_spinbox.setRange(100, 10000)
        self.x_max_spinbox.setValue(1400)
        self.x_max_spinbox.valueChanged.connect(self._update_scales)

        self.y_min_label = QtWidgets.QLabel("Y Min:")
        self.y_min_spinbox = QtWidgets.QSpinBox()
        self.y_min_spinbox.setRange(0, 1000)
        self.y_min_spinbox.setValue(25)
        self.y_min_spinbox.valueChanged.connect(self._update_scales)

        self.y_max_label = QtWidgets.QLabel("Y Max:")
        self.y_max_spinbox = QtWidgets.QSpinBox()
        self.y_max_spinbox.setRange(100, 10000)
        self.y_max_spinbox.setValue(1200)
        self.y_max_spinbox.valueChanged.connect(self._update_scales)

    def _update_scales(self):
        if self._restoring_state:
            return
        new_x = self.x_max_spinbox.value()
        new_ymin = self.y_min_spinbox.value()
        new_ymax = self.y_max_spinbox.value()
        # Enforce invariant
        if new_ymax <= new_ymin:
            new_ymax = new_ymin + 1
            self.y_max_spinbox.setValue(new_ymax)
        changed = new_x != self.curve.x_max or new_ymin != self.curve.y_min or new_ymax != self.curve.y_max
        self.curve.set_axis_scales(new_x, new_ymin, new_ymax)
        if changed:
            self._push_state("Axis scale change")
        self.update()
        self._update_window_title()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def paintEvent(self, a0):
        qp = QtGui.QPainter()
        qp.begin(self)
        self._draw(qp)
        qp.end()

    def mousePressEvent(self, a0):
        self.setFocus()
        self._drag_point = None
        self._pre_drag_points = None
        self._selected_point = None

        mouse_pos = a0.pos()
        mx = mouse_pos.x()
        my = mouse_pos.y()

        for idx, (x, y) in enumerate(self.curve.get_cv_points()):
            px = self._get_x_value_for(x)
            py = self._get_y_value_for(y)
            if abs(px - mx) < self._cv_point_size + 4 and abs(py - my) < self._cv_point_size + 4:
                self._drag_point = (idx, (px - mx, py - my))
                self._selected_point = idx
                # record original points for later comparison (drag end)
                self._pre_drag_points = copy.deepcopy(self.curve._cv_points)
                break
        self.update()

    def mouseReleaseEvent(self, a0):
        # Save state after drag if something actually moved
        if self._drag_point is not None and self._pre_drag_points is not None:
            if self.curve._cv_points != self._pre_drag_points:
                self._push_state("Move point")
                self._update_window_title()
        self._drag_point = None
        self._pre_drag_points = None

    def mouseDoubleClickEvent(self, a0):
        mouse_pos = a0.pos()
        mouse_x = mouse_pos.x() - self._legend_border - self._padding
        mouse_y = mouse_pos.y() - self._padding

        graph_width = self.width() - self._legend_border - 2 * self._padding
        graph_height = self.height() - self._legend_border - self._control_bar_height - 2 * self._padding

        local_x = max(
            0,
            min(
                self.curve.x_max,
                mouse_x / float(graph_width) * self.curve.x_max,
            ),
        )
        local_y = max(
            self.curve.y_min,
            min(
                self.curve.y_max,
                (1 - mouse_y / float(graph_height)) * (self.curve.y_max - self.curve.y_min) + self.curve.y_min,
            ),
        )
        # Snap new point's Y to existing point Y values if close (screen-space)
        for _, existing_y in self.curve.get_cv_points():
            if abs(self._get_y_value_for(existing_y) - self._get_y_value_for(local_y)) <= self._cv_point_size * 2:
                local_y = existing_y
                break

        # Perform modification first
        self.curve.add_cv_point(local_x, local_y)
        self.update()
        # Save state AFTER adding
        self._push_state("Add point")
        self._update_window_title()

    def mouseMoveEvent(self, a0):
        if self._drag_point is None:
            return
        idx, (ox, oy) = self._drag_point
        mouse_pos = a0.pos()

        # Screen position for point (apply stored offset)
        point_screen_x = mouse_pos.x() + ox
        point_screen_y = mouse_pos.y() + oy

        graph_x = point_screen_x - self._legend_border - self._padding
        graph_y = point_screen_y - self._padding

        graph_width = self.width() - self._legend_border - 2 * self._padding
        graph_height = self.height() - self._legend_border - self._control_bar_height - 2 * self._padding

        local_x = max(0, min(self.curve.x_max, graph_x / float(graph_width) * self.curve.x_max))
        normalized_y = 1.0 - (graph_y / float(graph_height))
        local_y = max(
            self.curve.y_min,
            min(
                self.curve.y_max,
                normalized_y * (self.curve.y_max - self.curve.y_min) + self.curve.y_min,
            ),
        )
        # Snap dragged point's Y to other points if close (exclude itself)
        for other_idx, (_, existing_y) in enumerate(self.curve.get_cv_points()):
            if other_idx == idx:
                continue
            if abs(self._get_y_value_for(existing_y) - self._get_y_value_for(local_y)) <= self._cv_point_size * 2:
                local_y = existing_y
                break

        self.curve.set_cv_value(idx, local_x, local_y)
        self.curve.build_curve()
        self.update()

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def _get_y_value_for(self, local_value):
        y_range = self.curve.y_max - self.curve.y_min
        normalized_value = (local_value - self.curve.y_min) / y_range
        normalized_value = max(0, min(1.0, 1.0 - normalized_value))
        return normalized_value * (self.height() - self._legend_border - self._control_bar_height - 2 * self._padding) + self._padding

    def _get_x_value_for(self, local_value):
        normalized_value = local_value / self.curve.x_max
        normalized_value = max(0, min(1.0, normalized_value))
        return normalized_value * (self.width() - self._legend_border - 2 * self._padding) + self._legend_border + self._padding

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _draw(self, painter):
        canvas_width = self.width() - self._legend_border - 2 * self._padding
        canvas_height = self.height() - self._legend_border - self._control_bar_height - 2 * self._padding

        palette = self.palette()
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Mid))
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Base))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        # Grid lines
        num_vert_lines = 7
        line_spacing_x = (self.width() - self._legend_border - 2 * self._padding) / 7.0
        line_spacing_y = (self.height() - self._legend_border - self._control_bar_height - 2 * self._padding) / 10.0
        num_horiz_lines = 11

        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Window))
        for i in range(num_vert_lines + 1):
            line_pos = i * line_spacing_x + self._legend_border + self._padding
            painter.drawLine(int(line_pos), self._padding, int(line_pos), canvas_height + self._padding)

        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Window))
        for i in range(num_horiz_lines):
            line_pos = canvas_height - i * line_spacing_y + self._padding
            painter.drawLine(self._legend_border, int(line_pos), self.width(), int(line_pos))

        # Y axis labels
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Text))
        y_range = self.curve.y_max - self.curve.y_min
        for i in range(num_horiz_lines):
            line_pos = canvas_height - i * line_spacing_y + self._padding
            value = int(self.curve.y_min + (y_range * i / (num_horiz_lines - 1)))
            painter.drawText(6, int(line_pos + 3), str(value))

        # X axis labels
        for i in range(num_vert_lines + 1):
            line_pos = i * line_spacing_x + self._legend_border + self._padding
            offpos_x = -14
            if i == 0:
                offpos_x = -2
            elif i == num_vert_lines:
                offpos_x = -33
            value = int(self.curve.x_max * i / num_vert_lines)
            painter.drawText(
                int(line_pos + offpos_x),
                canvas_height + self._padding + 18,
                str(value),
            )

        # Control bar background
        control_bar_y = canvas_height + self._padding + 25
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Mid))
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Window))
        painter.drawRect(0, control_bar_y, self.width(), self._control_bar_height)

        self._position_controls(control_bar_y)

        # Curve lines
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Text))
        sorted_points = sorted(self.curve.get_cv_points(), key=lambda v: v[0])
        for i in range(len(sorted_points) - 1):
            x1, y1 = sorted_points[i]
            x2, y2 = sorted_points[i + 1]
            painter.drawLine(
                int(self._get_x_value_for(x1)),
                int(self._get_y_value_for(y1)),
                int(self._get_x_value_for(x2)),
                int(self._get_y_value_for(y2)),
            )

        # Points
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Base))
        for idx, (x, y) in enumerate(self.curve.get_cv_points()):
            offs_x = self._get_x_value_for(x)
            offs_y = self._get_y_value_for(y)
            if self._selected_point == idx:
                painter.setPen(palette.color(QtGui.QPalette.ColorRole.Highlight))
            else:
                painter.setPen(palette.color(QtGui.QPalette.ColorRole.Dark))
            painter.drawRect(
                int(offs_x - self._cv_point_size),
                int(offs_y - self._cv_point_size),
                2 * self._cv_point_size,
                2 * self._cv_point_size,
            )

    # ------------------------------------------------------------------
    # Control positioning
    # ------------------------------------------------------------------
    def _position_controls(self, y_pos):
        x_offset = 10
        self.x_max_label.setParent(self)
        self.x_max_label.move(x_offset, y_pos + 10)
        self.x_max_label.show()

        self.x_max_spinbox.setParent(self)
        self.x_max_spinbox.move(x_offset + 50, y_pos + 8)
        self.x_max_spinbox.resize(80, 25)
        self.x_max_spinbox.show()

        x_offset += 150
        self.y_min_label.setParent(self)
        self.y_min_label.move(x_offset, y_pos + 10)
        self.y_min_label.show()

        self.y_min_spinbox.setParent(self)
        self.y_min_spinbox.move(x_offset + 50, y_pos + 8)
        self.y_min_spinbox.resize(80, 25)
        self.y_min_spinbox.show()

        x_offset += 150
        self.y_max_label.setParent(self)
        self.y_max_label.move(x_offset, y_pos + 10)
        self.y_max_label.show()

        self.y_max_spinbox.setParent(self)
        self.y_max_spinbox.move(x_offset + 50, y_pos + 8)
        self.y_max_spinbox.resize(80, 25)
        self.y_max_spinbox.show()

    def keyPressEvent(self, a0):
        # Allow deleting the currently selected point with Delete or Backspace
        if a0 is None:
            return
        if a0.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace):
            if self._selected_point is not None:
                self._delete_point(self._selected_point)
                return
        super().keyPressEvent(a0)
