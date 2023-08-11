from PySide6.QtWidgets import QApplication
import sys
from gui import NodeEditorWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)

    wnd = NodeEditorWindow()

    sys.exit(app.exec())
