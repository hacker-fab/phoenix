from __future__ import annotations

import copy
import sys
import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as QtWidgets
from typing import TypedDict

from models.curve import Curve

# Set to True to enable debug logging for state saves
DEBUG_UNDO = False


class Snapshot(TypedDict):
    cv_points: list[list[float]]
    x_max: float
    y_min: float
    y_max: float


class CurveWidget(QtWidgets.QWidget):
    """Resizable widget displaying an editable curve with undo/redo support."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.curve: Curve = Curve()
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # Widget render constants
        self._cv_point_size: int = 6
        self._legend_border: int = 35
        self._control_bar_height: int = 40
        self._help_bar_height: int = 22
        self._padding: int = 12

        # Drag / selection tracking
        self._drag_point: tuple[int, tuple[float, float]] | None = None  # (index, (offset_x, offset_y))
        self._selected_point: int | None = None
        self._pre_drag_points: list[list[float]] | None = None  # deep copy of points at drag start

        # Undo/Redo state history
        self._history: list[Snapshot] = []
        self._history_index: int = -1
        self._restoring_state: bool = False

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
    def _capture_state(self) -> Snapshot:
        """Return a deep copy snapshot of current logical state."""
        return Snapshot(
            cv_points=copy.deepcopy(self.curve._cv_points),
            x_max=self.curve.x_max,
            y_min=self.curve.y_min,
            y_max=self.curve.y_max,
        )

    def _states_equal(self, a: Snapshot, b: Snapshot) -> bool:
        return a["cv_points"] == b["cv_points"] and a["x_max"] == b["x_max"] and a["y_min"] == b["y_min"] and a["y_max"] == b["y_max"]

    def _push_state(self, action_name: str = "Unknown") -> None:
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

    def _undo(self) -> None:
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_state(self._history[self._history_index])
            self._update_window_title()
            if DEBUG_UNDO:
                print(f"UNDO DEBUG: undo -> index {self._history_index} / {len(self._history)}")

    def _redo(self) -> None:
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_state(self._history[self._history_index])
            self._update_window_title()
            if DEBUG_UNDO:
                print(f"UNDO DEBUG: redo -> index {self._history_index} / {len(self._history)}")

    def _restore_state(self, state: Snapshot) -> None:
        self._restoring_state = True
        try:
            self.curve._cv_points = copy.deepcopy(state["cv_points"])
            self.curve.x_max = state["x_max"]
            self.curve.y_min = state["y_min"]
            self.curve.y_max = state["y_max"]

            # Update spin boxes (will not push state due to flag)
            self.x_max_spinbox.setValue(int(state["x_max"]))
            self.y_min_spinbox.setValue(int(state["y_min"]))
            self.y_max_spinbox.setValue(int(state["y_max"]))

            self.curve.build_curve()
            self.update()
        finally:
            self._restoring_state = False

    # ------------------------------------------------------------------
    # UI / shortcuts
    # ------------------------------------------------------------------
    def _setup_shortcuts(self) -> None:
        self.undo_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Undo, self)
        self.undo_shortcut.activated.connect(self._undo)
        self.redo_shortcut: QtGui.QShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Redo, self)
        self.redo_shortcut.activated.connect(self._redo)

    def _update_window_title(self) -> None:
        # Keep window title simple; detailed instructions now live in bottom help bar.
        parent_window = self.window()
        if parent_window:
            parent_window.setWindowTitle("Qt6 Curve Editor")
        # Refresh help label text (in case platform-specific modifier differs).
        if hasattr(self, "help_label"):
            self.help_label.setText(self._build_help_text())

    def _build_help_text(self) -> str:
        mod = "Cmd" if sys.platform == "darwin" else "Ctrl"
        # We could reflect undo/redo availability dynamically, but for simplicity we always show them.
        return (
            f"Double-click: Add point  |  Right-click: Delete point  |  Delete: Remove selected  |  "
            f"{mod}+Z: Undo  |  {mod}+Shift+Z: Redo  |  Drag: Move point"
        )

    # ------------------------------------------------------------------
    # Context menu / point deletion
    # ------------------------------------------------------------------
    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        point_index = self._get_point_at_position(position)
        if point_index is None:
            return
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Delete Point")
        if delete_action:
            delete_action.triggered.connect(lambda: self._delete_point(point_index))
        menu.exec(self.mapToGlobal(position))

    def _get_point_at_position(self, position: QtCore.QPoint) -> int | None:
        mouse_x = position.x()
        mouse_y = position.y()
        for idx, (x, y) in enumerate(self.curve.get_cv_points()):
            px = self._get_x_value_for(x)
            py = self._get_y_value_for(y)
            if abs(px - mouse_x) < self._cv_point_size + 4 and abs(py - mouse_y) < self._cv_point_size + 4:
                return idx
        return None

    def _delete_point(self, point_index: int) -> None:
        if len(self.curve._cv_points) <= 1:
            return
        del self.curve._cv_points[point_index]
        if self._selected_point == point_index:
            self._selected_point = None
        elif self._selected_point is not None and self._selected_point > point_index:
            self._selected_point -= 1
        self.curve.build_curve()
        self.update()
        self._push_state(f"Delete point {point_index}")
        self._update_window_title()

    # ------------------------------------------------------------------
    # Axis scale controls
    # ------------------------------------------------------------------
    def _create_controls(self) -> None:
        self.x_max_label: QtWidgets.QLabel = QtWidgets.QLabel("X Max:")
        self.x_max_spinbox: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
        self.x_max_spinbox.setRange(100, 10000)
        self.x_max_spinbox.setValue(1400)
        self.x_max_spinbox.valueChanged.connect(self._update_scales)

        self.y_min_label: QtWidgets.QLabel = QtWidgets.QLabel("Y Min:")
        self.y_min_spinbox: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
        self.y_min_spinbox.setRange(0, 1000)
        self.y_min_spinbox.setValue(25)
        self.y_min_spinbox.valueChanged.connect(self._update_scales)

        self.y_max_label: QtWidgets.QLabel = QtWidgets.QLabel("Y Max:")
        self.y_max_spinbox: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
        self.y_max_spinbox.setRange(100, 10000)
        self.y_max_spinbox.setValue(1200)
        self.y_max_spinbox.valueChanged.connect(self._update_scales)

        # Copy Points button (copies points as (x1,y1),(x2,y2)...)
        self.copy_points_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Copy Points")
        self.copy_points_button.setToolTip("Copy points as (x1,y1),(x2,y2)")

        def _do_copy():
            pts = sorted(self.curve.get_cv_points(), key=lambda p: p[0])

            def fmt(v: float) -> str:
                return str(int(v)) if float(v).is_integer() else f"{v:.2f}"

            QtWidgets.QApplication.clipboard().setText(",".join(f"({fmt(x)},{fmt(y)})" for x, y in pts))

        self.copy_points_button.clicked.connect(_do_copy)

        # Help / instruction label (populated in _update_window_title)
        self.help_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self.help_label.setText(self._build_help_text())
        font = self.help_label.font()
        font.setPointSize(max(8, font.pointSize() - 1))
        self.help_label.setFont(font)
        self.help_label.setStyleSheet("color: gray;")

    def _update_scales(self) -> None:
        if self._restoring_state:
            return
        new_x = self.x_max_spinbox.value()
        new_ymin = self.y_min_spinbox.value()
        new_ymax = self.y_max_spinbox.value()
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
    def paintEvent(self, a0: QtGui.QPaintEvent | None) -> None:
        qp = QtGui.QPainter(self)
        self._draw(qp)

    def mousePressEvent(self, a0: QtGui.QMouseEvent | None) -> None:
        if a0 is None:
            return
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
                self._pre_drag_points = copy.deepcopy(self.curve._cv_points)
                break
        self.update()

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent | None) -> None:
        if a0 is None:
            return
        if self._drag_point is not None and self._pre_drag_points is not None:
            if self.curve._cv_points != self._pre_drag_points:
                # Defer sorting until drag end to avoid index changes during drag
                # that previously caused the actively moved point to switch and
                # appear as though points were deleted when crossing neighbors.
                self.curve.build_curve()
                self._push_state("Move point")
                self._update_window_title()
        self._drag_point = None
        self._pre_drag_points = None

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent | None) -> None:
        if a0 is None:
            return
        mouse_pos = a0.pos()
        mouse_x = mouse_pos.x() - self._legend_border - self._padding
        mouse_y = mouse_pos.y() - self._padding

        graph_width = self.width() - self._legend_border - 2 * self._padding
        graph_height = self.height() - self._legend_border - self._control_bar_height - self._help_bar_height - 2 * self._padding

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
        for _, existing_y in self.curve.get_cv_points():
            if abs(self._get_y_value_for(existing_y) - self._get_y_value_for(local_y)) <= self._cv_point_size * 2:
                local_y = existing_y
                break

        self.curve.add_cv_point(local_x, local_y)
        self.update()
        self._push_state("Add point")
        self._update_window_title()

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent | None) -> None:
        if a0 is None:
            return
        if self._drag_point is None:
            return
        idx, (ox, oy) = self._drag_point
        mouse_pos = a0.pos()

        point_screen_x = mouse_pos.x() + ox
        point_screen_y = mouse_pos.y() + oy

        graph_x = point_screen_x - self._legend_border - self._padding
        graph_y = point_screen_y - self._padding

        graph_width = self.width() - self._legend_border - 2 * self._padding
        graph_height = self.height() - self._legend_border - self._control_bar_height - self._help_bar_height - 2 * self._padding

        local_x = max(0, min(self.curve.x_max, graph_x / float(graph_width) * self.curve.x_max))
        normalized_y = 1.0 - (graph_y / float(graph_height))
        local_y = max(
            self.curve.y_min,
            min(
                self.curve.y_max,
                normalized_y * (self.curve.y_max - self.curve.y_min) + self.curve.y_min,
            ),
        )
        for other_idx, (_, existing_y) in enumerate(self.curve.get_cv_points()):
            if other_idx == idx:
                continue
            if abs(self._get_y_value_for(existing_y) - self._get_y_value_for(local_y)) <= self._cv_point_size * 2:
                local_y = existing_y
                break

        self.curve.set_cv_value(idx, local_x, local_y)
        # Do NOT sort here; sorting during drag changes indices and can
        # cause the dragged point reference to shift to another point.
        # We sort once on mouse release instead.
        self.update()

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def _get_y_value_for(self, local_value: float) -> float:
        y_range = self.curve.y_max - self.curve.y_min
        normalized_value = (local_value - self.curve.y_min) / y_range
        normalized_value = max(0.0, min(1.0, 1.0 - normalized_value))
        return (
            normalized_value * (self.height() - self._legend_border - self._control_bar_height - self._help_bar_height - 2 * self._padding)
            + self._padding
        )

    def _get_x_value_for(self, local_value: float) -> float:
        normalized_value = local_value / self.curve.x_max
        normalized_value = max(0.0, min(1.0, normalized_value))
        return normalized_value * (self.width() - self._legend_border - 2 * self._padding) + self._legend_border + self._padding

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _draw(self, painter: QtGui.QPainter) -> None:
        canvas_height = self.height() - self._legend_border - self._control_bar_height - self._help_bar_height - 2 * self._padding

        palette = self.palette()
        # Draw only the graph (plot) area background; leave rest transparent
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Mid))
        painter.setBrush(palette.color(QtGui.QPalette.ColorRole.Base))
        graph_width = self.width() - self._legend_border - 2 * self._padding
        painter.drawRect(self._legend_border, self._padding, graph_width, canvas_height)

        # Build grid positions at each 100 units (nearest hundred marks) plus end caps
        x_values: list[float] = []
        step = 100.0
        xv = 0.0
        while xv < self.curve.x_max:
            x_values.append(xv)
            xv += step
        if not x_values or x_values[-1] != self.curve.x_max:
            x_values.append(self.curve.x_max)
        # Y values from y_min upward every 100, include y_max
        y_values: list[float] = []
        yv = self.curve.y_min
        while yv < self.curve.y_max:
            y_values.append(yv)
            yv += step
        if not y_values or y_values[-1] != self.curve.y_max:
            y_values.append(self.curve.y_max)

        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Window))
        for xv in x_values:
            line_pos = (
                (xv / self.curve.x_max) * (self.width() - self._legend_border - 2 * self._padding) + self._legend_border + self._padding
            )
            painter.drawLine(int(line_pos), self._padding, int(line_pos), canvas_height + self._padding)

        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Window))
        for yv in y_values:
            py = self._get_y_value_for(yv)
            painter.drawLine(self._legend_border, int(py), self.width(), int(py))

        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Text))
        for yv in y_values:
            py = self._get_y_value_for(yv)
            painter.drawText(6, int(py + 3), str(int(yv)))

        for idx, xv in enumerate(x_values):
            line_pos = (
                (xv / self.curve.x_max) * (self.width() - self._legend_border - 2 * self._padding) + self._legend_border + self._padding
            )
            offpos_x = -14
            if idx == 0:
                offpos_x = -2
            elif idx == len(x_values) - 1:
                offpos_x = -33
            painter.drawText(int(line_pos + offpos_x), canvas_height + self._padding + 18, str(int(xv)))

        control_bar_y = canvas_height + self._padding + 25
        # Omit control bar background for a cleaner look
        painter.setPen(palette.color(QtGui.QPalette.ColorRole.Mid))
        # (Intentionally not drawing a rect for control bar background)

        self._position_controls(control_bar_y)

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
    def _position_controls(self, y_pos: int) -> None:
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

        # Copy Points button
        x_offset += 150
        self.copy_points_button.setParent(self)
        self.copy_points_button.move(x_offset, y_pos + 8)
        self.copy_points_button.resize(110, 25)
        self.copy_points_button.show()

        # Position help label in a separate bar below the control bar
        self.help_label.setParent(self)
        help_bar_y = y_pos + self._control_bar_height
        # Dynamically size and vertically center help label within the help bar
        label_height = max(12, self._help_bar_height - 6)
        self.help_label.resize(self.width() - 20, label_height)
        self.help_label.move(10, help_bar_y + (self._help_bar_height - label_height) // 2)
        self.help_label.show()

    def keyPressEvent(self, a0: QtGui.QKeyEvent | None) -> None:
        if a0 is None:
            return
        if a0.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace):
            if self._selected_point is not None:
                self._delete_point(self._selected_point)
                return
        super().keyPressEvent(a0)
