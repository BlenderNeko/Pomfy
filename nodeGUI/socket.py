from __future__ import annotations
from typing import TYPE_CHECKING

from style.socketStyle import SocketPainter

if TYPE_CHECKING:
    from node import NodeSocket

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath


from constants import (
    SLOT_MIN_HEIGHT,
    SOCKET_PADDING,
    SOCKET_RADIUS,
)


class GrNodeSocket(QWgt.QGraphicsItem):
    @property
    def nodeSocket(self) -> NodeSocket:
        return self._nodeSocket

    @property
    def color(self) -> QGui.QColor:
        return self.socketPainter.primaryBrush.color()

    def __init__(
        self,
        nodeSocket: NodeSocket,
        socketPainter: SocketPainter,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._nodeSocket = nodeSocket
        self.setAcceptHoverEvents(True)
        self.socketPainter = socketPainter
        self._highlightBrush = QGui.QBrush(QGui.QColor("#80ecc546"))
        self.updatePaint()

    def boundingRect(self) -> QCor.QRectF:
        return QCor.QRectF(
            SLOT_MIN_HEIGHT / 2 - SOCKET_RADIUS - SOCKET_PADDING,
            SLOT_MIN_HEIGHT / 2 - SOCKET_RADIUS - SOCKET_PADDING,
            SOCKET_RADIUS * 2 + SOCKET_PADDING * 2,
            SOCKET_RADIUS * 2 + SOCKET_PADDING * 2,
        )

    def centerPos(self) -> QPointF:
        return self.scenePos() + QPointF(SLOT_MIN_HEIGHT / 2, SLOT_MIN_HEIGHT / 2)

    def updatePaint(self) -> None:
        socketHighlight = QPainterPath()
        socketHighlight.addEllipse(
            QPointF(SLOT_MIN_HEIGHT / 2, SLOT_MIN_HEIGHT / 2), 10, 10
        )
        self._socketHighlightPath = socketHighlight.simplified()

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        self.socketPainter.paint(painter)

        if self.nodeSocket.active:
            painter.setBrush(self._highlightBrush)
            painter.drawPath(self._socketHighlightPath)

    def mousePressEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        event.accept()
        # return super().mousePressEvent(event)
