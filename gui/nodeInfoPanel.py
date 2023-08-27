from typing import Optional, List, Tuple, Callable
import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets as QWgt
import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets


class NodeInfoPanel(QWgt.QWidget):
    def __init__(self, parent: QWgt.QWidget | None = None) -> None:
        self.parentPanel = parent
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.layoutMain = QWgt.QVBoxLayout()
        self.layoutMain.addWidget(QWgt.QLabel("Node settings"))
        self.layoutForm = QWgt.QFormLayout()
        self.layoutMain.addLayout(self.layoutForm)
        self.setLayout(self.layoutMain)
        self.storedWidgets: List[QWgt.QWidget] = []

    def setContent(self, widgets: List[Tuple[str, QWgt.QWidget]]) -> None:
        for ind in range(self.layoutForm.rowCount()):
            self.layoutForm.removeRow(ind)
        self.storedWidgets = []
        for label, widget in widgets:
            self.storedWidgets.append(widget)
            self.layoutForm.addRow(label, widget)
            widget.show()
