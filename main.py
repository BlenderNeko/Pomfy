from PySide6.QtWidgets import QApplication
import sys
from gui import NodeEditorWindow
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", action="store_true", help="Render node editor on cpu.")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    wnd = NodeEditorWindow(args)

    sys.exit(app.exec())
