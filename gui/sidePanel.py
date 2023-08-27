from typing import List
import PySide6.QtGui

import PySide6.QtWidgets as QWgt
import PySide6.QtGui as QGui
import PySide6.QtCore as QCor


class SidePanel(QWgt.QWidget):
    def __init__(self, parent: QWgt.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.widgets: List[QWgt.QWidget] = []
        self.setLayout(QWgt.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.activeInd: int = -1

    def addWidget(self, widget: QWgt.QWidget) -> None:
        self.widgets.append(widget)
        widget.hide()
        self.layout().addWidget(widget)

    def setActive(self, ind: int) -> None:
        if self.activeInd != -1:
            self.widgets[self.activeInd].hide()
        self.widgets[ind].show()
        self.adjustSize()
