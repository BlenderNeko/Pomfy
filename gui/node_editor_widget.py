from server import ComfyConnection
from node.factory import ComfyFactory
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
        self._layout = QWgt.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # create view
        self.view = QNodeGraphicsView(self.sceneCollection.collection.activeScene)

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
