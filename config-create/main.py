import sys
import PyQt6.QtCore as QtCore

# Removed unused PyQt6.QtGui import
import PyQt6.QtWidgets as QtWidgets

from widgets.curve_widget import CurveWidget


class Editor(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.resize(580, 480)
        self.setWindowTitle("Qt6 Curve Editor")

        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Create curve widget
        self.curve_widget: CurveWidget = CurveWidget(self)
        layout.addWidget(self.curve_widget)

        # Ensure the curve widget can receive focus for keyboard shortcuts
        self.curve_widget.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.curve_widget.setFocus()


def main() -> int:
    """Main function with proper error handling"""
    try:
        app = QtWidgets.QApplication(sys.argv)
        app.setApplicationName("Qt6 Curve Editor")

        editor = Editor()
        editor.show()

        return app.exec()
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
