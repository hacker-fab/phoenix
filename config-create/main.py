from __future__ import annotations

import sys

import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as QtWidgets

# Import the existing curve widget so we can subclass it to add signals
from widgets.curve_widget import CurveWidget as BaseCurveWidget


class CurveWidget(BaseCurveWidget):
    """
    Thin subclass of the existing CurveWidget that emits signals whenever the
    set of control points changes or the selected point changes.

    We hook into _push_state (called after each logical modification) and
    _restore_state (used by undo/redo) to broadcast changes to outside
    components like the sidebar table.

    NOTE: We deliberately keep the parent widget logic untouched; only signal
    emission is added here to avoid editing the original file.
    """

    pointsChanged = QtCore.pyqtSignal()  # Emitted after points list changes
    selectionChanged = QtCore.pyqtSignal(int)  # Emitted with selected point index or -1

    def _push_state(self, action_name: str = "Unknown") -> None:  # type: ignore[override]
        super()._push_state(action_name)
        self.pointsChanged.emit()

    def _restore_state(self, state):  # type: ignore[override]
        super()._restore_state(state)
        self.pointsChanged.emit()

    def mousePressEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # type: ignore[override]
        super().mousePressEvent(a0)
        # After base handling, emit current selection
        selected_index = getattr(self, "_selected_point", None)
        if selected_index is None:
            self.selectionChanged.emit(-1)
        else:
            self.selectionChanged.emit(selected_index)

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # type: ignore[override]
        super().mouseDoubleClickEvent(a0)
        self.pointsChanged.emit()

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # type: ignore[override]
        pre_points = [p[:] for p in self.curve.get_cv_points()]
        super().mouseReleaseEvent(a0)
        post_points = self.curve.get_cv_points()
        if pre_points != post_points:
            self.pointsChanged.emit()


class PointsTable(QtWidgets.QTableWidget):
    """
    Table displaying control points:

    Columns:
        0 - Index (sorted order)
        1 - X position (editable)
        2 - Y position (editable)
        3 - ΔY from previous point (read only)
    """

    COL_INDEX = 0
    COL_X = 1
    COL_Y = 2
    COL_DY = 3

    headers = ["Idx", "X", "Y", "ΔY"]

    pointEdited = QtCore.pyqtSignal(int, float, float)  # row index (sorted), new x, new y

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(0, len(self.headers), parent)
        self.setHorizontalHeaderLabels(self.headers)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self._suppress_item_handler = False

        # Narrow index / delta columns
        self.setColumnWidth(self.COL_INDEX, 40)
        self.setColumnWidth(self.COL_DY, 60)

        self.itemChanged.connect(self._handle_item_changed)

    def populate(self, points: list[list[float]]) -> None:
        """
        Populate table with sorted points.
        """
        self._suppress_item_handler = True
        try:
            self.setRowCount(len(points))
            for row, (x, y) in enumerate(points):
                index_item = QtWidgets.QTableWidgetItem(str(row))
                index_item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                self.setItem(row, self.COL_INDEX, index_item)

                x_item = QtWidgets.QTableWidgetItem(self._format_float(x))
                x_item.setFlags(self._editable_flags())
                self.setItem(row, self.COL_X, x_item)

                y_item = QtWidgets.QTableWidgetItem(self._format_float(y))
                y_item.setFlags(self._editable_flags())
                self.setItem(row, self.COL_Y, y_item)

                dy_value = 0.0 if row == 0 else (y - points[row - 1][1])
                dy_item = QtWidgets.QTableWidgetItem(self._format_float(dy_value))
                dy_item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled)
                self.setItem(row, self.COL_DY, dy_item)
        finally:
            self._suppress_item_handler = False

    def select_point(self, sorted_index: int) -> None:
        """
        Select the table row corresponding to the given sorted index.
        """
        if 0 <= sorted_index < self.rowCount():
            self.setCurrentCell(sorted_index, self.COL_INDEX)

    def _editable_flags(self) -> QtCore.Qt.ItemFlag:
        return QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsEditable

    def _handle_item_changed(self, item: QtWidgets.QTableWidgetItem) -> None:
        if self._suppress_item_handler:
            return
        row = item.row()
        col = item.column()
        if col not in (self.COL_X, self.COL_Y):
            return

        # Parse current X / Y row data safely
        def parse_float(cell: QtWidgets.QTableWidgetItem) -> float | None:
            try:
                return float(cell.text())
            except Exception:
                return None

        x_item = self.item(row, self.COL_X)
        y_item = self.item(row, self.COL_Y)
        if x_item is None or y_item is None:
            return
        x_val = parse_float(x_item)
        y_val = parse_float(y_item)
        if x_val is None or y_val is None:
            return

        self.pointEdited.emit(row, x_val, y_val)

    @staticmethod
    def _format_float(v: float) -> str:
        if abs(v) >= 1000 or v.is_integer():
            return f"{v:.0f}"
        return f"{v:.2f}"


class Editor(QtWidgets.QMainWindow):
    """
    Main window hosting the curve editor and the sidebar table.
    """

    def __init__(self) -> None:
        super().__init__()
        self.resize(900, 520)
        self.setWindowTitle("Qt6 Curve Editor")

        # Central splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Sidebar (table)
        sidebar_container = QtWidgets.QWidget()
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(6, 6, 6, 6)
        sidebar_layout.setSpacing(4)

        header_label = QtWidgets.QLabel("Control Points")
        font = header_label.font()
        font.setBold(True)
        header_label.setFont(font)
        sidebar_layout.addWidget(header_label)

        self.table = PointsTable()
        sidebar_layout.addWidget(self.table, 1)

        # Buttons (optional)
        button_row = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Add Point")
        self.btn_remove = QtWidgets.QPushButton("Remove Selected")
        button_row.addWidget(self.btn_add)
        button_row.addWidget(self.btn_remove)
        sidebar_layout.addLayout(button_row)

        splitter.addWidget(sidebar_container)

        # Curve widget (right side)
        self.curve_widget: CurveWidget = CurveWidget(self)
        splitter.addWidget(self.curve_widget)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 640])

        # Connections
        self.curve_widget.pointsChanged.connect(self._refresh_table_from_curve)
        self.curve_widget.selectionChanged.connect(self._handle_curve_selection)
        self.table.pointEdited.connect(self._handle_table_edit)
        self.btn_add.clicked.connect(self._handle_add_point)
        self.btn_remove.clicked.connect(self._handle_remove_selected)

        # Initial population
        self._refresh_table_from_curve()

    # ------------------------------------------------------------------ #
    # Synchronization helpers
    # ------------------------------------------------------------------ #
    def _sorted_points(self) -> list[list[float]]:
        return sorted(self.curve_widget.curve.get_cv_points(), key=lambda p: p[0])

    def _refresh_table_from_curve(self) -> None:
        points = self._sorted_points()
        self.table.populate(points)

    def _handle_curve_selection(self, index: int) -> None:
        if index >= 0:
            # We need to locate selected point's position in sorted order
            sorted_pts = self._sorted_points()
            raw_point = self.curve_widget.curve.get_cv_points()[index]
            # Identify by (x,y) match (duplicate safety minimal point counts)
            for sorted_index, p in enumerate(sorted_pts):
                if p is raw_point or (p[0] == raw_point[0] and p[1] == raw_point[1]):
                    self.table.select_point(sorted_index)
                    break

    def _handle_table_edit(self, sorted_row: int, new_x: float, new_y: float) -> None:
        """
        Apply edited X/Y back to underlying curve.

        sorted_row: row index in sorted order (0..n-1)
        """
        points = self._sorted_points()
        if not (0 <= sorted_row < len(points)):
            return

        # Find the real underlying point reference. Since build_curve sorts in-place,
        # sorted order now matches internal order after modifications that push state.
        # To be safe, we re-sort internal list and then apply update by mapping index.
        self.curve_widget.curve.build_curve()
        internal_points = self.curve_widget.curve.get_cv_points()

        # Clamp within axis scales
        new_x_clamped = max(0.0, min(self.curve_widget.curve.x_max, new_x))
        new_y_clamped = max(self.curve_widget.curve.y_min, min(self.curve_widget.curve.y_max, new_y))

        self.curve_widget.curve.set_cv_value(sorted_row, new_x_clamped, new_y_clamped)
        self.curve_widget.curve.build_curve()
        self.curve_widget.update()
        # Use protected push_state to keep undo chain
        self.curve_widget._push_state("Edit point (table)")
        self.curve_widget.pointsChanged.emit()

    def _handle_add_point(self) -> None:
        """
        Add a point halfway between currently selected and next (or end).
        """
        sorted_pts = self._sorted_points()
        if not sorted_pts:
            self.curve_widget.curve.add_cv_point(0.0, self.curve_widget.curve.y_min)
            self.curve_widget._push_state("Add point (button)")
            self.curve_widget.pointsChanged.emit()
            return

        current_row = self.table.currentRow()
        if current_row < 0:
            # Add after last
            last_x, last_y = sorted_pts[-1]
            new_x = min(last_x + 50.0, self.curve_widget.curve.x_max)
            new_y = last_y
        else:
            if current_row == len(sorted_pts) - 1:
                # After last
                base_x, base_y = sorted_pts[current_row]
                new_x = min(base_x + 50.0, self.curve_widget.curve.x_max)
                new_y = base_y
            else:
                x1, y1 = sorted_pts[current_row]
                x2, y2 = sorted_pts[current_row + 1]
                new_x = x1 + (x2 - x1) / 2.0
                new_y = y1 + (y2 - y1) / 2.0

        self.curve_widget.curve.add_cv_point(new_x, new_y)
        self.curve_widget.update()
        self.curve_widget._push_state("Add point (button)")
        self.curve_widget.pointsChanged.emit()

    def _handle_remove_selected(self) -> None:
        """
        Remove selected point (in table sorted order) if more than one point exists.
        """
        row = self.table.currentRow()
        if row < 0:
            return
        internal_points = self.curve_widget.curve.get_cv_points()
        if len(internal_points) <= 1:
            return
        # Ensure internal order is sorted, then delete by index
        self.curve_widget.curve.build_curve()
        del internal_points[row]
        self.curve_widget.curve.build_curve()
        self.curve_widget.update()
        self.curve_widget._push_state("Delete point (button)")
        self.curve_widget.pointsChanged.emit()

    # ------------------------------------------------------------------ #
    # Close event / convenience
    # ------------------------------------------------------------------ #
    def closeEvent(self, a0: QtGui.QCloseEvent | None) -> None:  # type: ignore[override]
        super().closeEvent(a0)


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Qt6 Curve Editor")
    window = Editor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
