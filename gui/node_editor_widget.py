from typing import Optional
import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets
from gui.nodeInfoPanel import NodeInfoPanel
from gui.sidePanel import SidePanel
from gui.view import QNodeGraphicsView

# from node_reroute import RerouteNode
from node import NodeScene
from PySide6.QtOpenGLWidgets import QOpenGLWidget

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from gui.workFolder import MaybeSceneCollection
from style.socketStyle import SocketStyles


class QNodeEditor(QWgt.QWidget):
    def __init__(
        self,
        sceneCollection: MaybeSceneCollection,
        accelerate: bool = True,
        parent: QWgt.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.sceneCollection = sceneCollection
        self.accelerate = accelerate
        self._initUI()

    def _initUI(self) -> None:
        # set layout
        self._layout = QWgt.QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # create view
        self.view = QNodeGraphicsView(self.sceneCollection.collection.activeScene)
        self.sideTabs = QWgt.QTabBar()
        self.sideTabs.setShape(QWgt.QTabBar.Shape.RoundedEast)
        self.sideTabs.setDrawBase(False)
        self.sideTabs.addTab("Prompt")
        self.sideTabs.addTab("Sub Trees")
        self.sideTabs.addTab("Node Settings")
        self.sideTabs.currentChanged.connect(self.tabChanged)

        self.sidePanel = SidePanel()
        self.nodeSettingsPanel = NodeInfoPanel(self.sidePanel)
        self.nodeSettingsPanel.setContent([])

        self.sidePanel.addWidget(self.nodeSettingsPanel)
        self.sidePanel.addWidget(self.nodeSettingsPanel)
        self.sidePanel.addWidget(self.nodeSettingsPanel)
        self.sidePanel.setActive(0)

        # OpenGl acceleration
        if self.accelerate:
            self.gl = QOpenGLWidget(self)
            format = self.gl.format()
            format.setVersion(4, 6)
            # format.setProfile(QGui.QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            format.setOption(
                QGui.QSurfaceFormat.FormatOption.DeprecatedFunctions, False
            )
            self.gl.setFormat(format)
            self.view.setViewport(self.gl)

        self._layout.addWidget(self.view)
        self._layout.addWidget(self.sideTabs)
        self._layout.setAlignment(self.sideTabs, QCor.Qt.AlignmentFlag.AlignTop)
        self.sidePanel.setParent(self)
        self.sidePanel.setFixedWidth(250)

        self.sidePanel.move(self.width() - self.sidePanel.width() - 10, 10)
        self.view.activeNodeChanged.connect(self.activeNodeChange)

    def resizeEvent(self, event: QGui.QResizeEvent) -> None:
        self.sidePanel.move(self.view.width() - self.sidePanel.width() - 10, 10)
        super().resizeEvent(event)

    def tabChanged(self, ind: int) -> None:
        self.sidePanel.setActive(ind)

    def activeNodeChange(self) -> None:
        node = self.view.activeNode
        print(node)
        if node is not None:
            self.nodeSettingsPanel.setContent(node.generateSettings())
        else:
            self.nodeSettingsPanel.setContent([])
        self.nodeSettingsPanel.adjustSize()
        self.sidePanel.adjustSize()
