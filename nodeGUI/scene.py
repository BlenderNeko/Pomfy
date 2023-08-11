from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from node import NodeScene

import math
import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt


class QNodeGraphicsScene(QWgt.QGraphicsScene):
    def __init__(
        self, nodeScene: NodeScene, parent: QWgt.QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.nodeScene = nodeScene
        self.background_color = QGui.QColor("#393939")
        self.grid_color_light = QGui.QColor("#2f2f2f")
        self.grid_color_dark = QGui.QColor("#292929")
        self.grid_size = 20

        self.grid_pen_l = QGui.QPen(self.grid_color_light)
        self.grid_pen_l.setWidth(1)
        self.grid_pen_d = QGui.QPen(self.grid_color_dark)
        self.grid_pen_d.setWidth(2)

        self.setBackgroundBrush(self.background_color)

    def setGrScene(self, width: int, height: int) -> None:
        self.setSceneRect(-width // 2, -height // 2, width, height)

    def drawBackground(
        self, painter: QGui.QPainter, rect: QCor.QRect | QCor.QRectF
    ) -> None:
        super().drawBackground(painter, rect)

        up = int(math.ceil(rect.top()))
        left = int(math.floor(rect.left()))
        down = int(math.floor(rect.bottom()))
        right = int(math.ceil(rect.right()))

        hlines = range(left - left % self.grid_size, right, self.grid_size)
        vlines = range(up - up % self.grid_size, down, self.grid_size)

        # draw light
        painter.setPen(self.grid_pen_l)
        painter.drawLines(
            [
                QCor.QLine(x, up, x, down)
                for x in hlines
                if x % (5 * self.grid_size) != 0
            ]
        )
        painter.drawLines(
            [
                QCor.QLine(left, x, right, x)
                for x in vlines
                if x % (5 * self.grid_size) != 0
            ]
        )

        # draw dark
        painter.setPen(self.grid_pen_d)
        painter.drawLines(
            [
                QCor.QLine(x, up, x, down)
                for x in hlines
                if x % (5 * self.grid_size) == 0
            ]
        )
        painter.drawLines(
            [
                QCor.QLine(left, x, right, x)
                for x in vlines
                if x % (5 * self.grid_size) == 0
            ]
        )
