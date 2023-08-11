from server import ComfyConnection
from node.factory import ComfyFactory
from gui.view import QNodeGraphicsView

# from node_reroute import RerouteNode
from node import NodeScene
from PySide6.QtOpenGLWidgets import QOpenGLWidget

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from node import SceneCollection
from style.socketStyle import SocketStyles


class QNodeEditor(QWgt.QWidget):
    def __init__(self, parent: QWgt.QWidget | None = None) -> None:
        super().__init__(parent)
        self.connection = ComfyConnection()

        self._initUI()

        # self.initActions()

    def _initUI(self) -> None:
        # offset x, y, size x y

        # set layout
        self._layout = QWgt.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # create factory

        self.nodeFactory = ComfyFactory(SocketStyles())
        # with open("test.json", "r") as f:
        #    data = f.readlines()
        self.nodeFactory.loadNodeDefinitions(self.connection.getNodeDefs())

        # create scene
        self.sceneCollection = SceneCollection(self.nodeFactory)

        # create view
        self.gl = QOpenGLWidget(self)
        format = self.gl.format()
        format.setVersion(4, 6)
        self.gl.setFormat(format)

        self.view = QNodeGraphicsView(self.sceneCollection.activeScene)
        self.view.setViewport(self.gl)
        self._layout.addWidget(self.view)
