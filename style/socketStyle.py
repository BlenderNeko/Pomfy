from typing import Dict, Callable
import PySide6.QtGui as QGui
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF
from constants import SOCKET_RADIUS, SLOT_MIN_HEIGHT
import hashlib


class SocketColorProvider:
    @property
    def color(self) -> QGui.QColor:
        return self._color1

    @property
    def PrimaryBrush(self) -> QGui.QBrush:
        return self._brush1

    @property
    def SecondaryBrush(self) -> QGui.QBrush:
        return self._brush2

    @property
    def Pen(self) -> QGui.QPen | QGui.Qt.PenStyle:
        return self._pen

    def __init__(self, color: QGui.QColor) -> None:
        self._color1 = color
        self._color2 = color.darker(f=300)
        self._brush1 = QGui.QBrush(self._color1)
        self._brush2 = QGui.QBrush(self._color2)
        self._pen = QGui.Qt.PenStyle.NoPen

    def update(self) -> None:
        self._color2 = self.color.darker(f=300)
        self._brush2 = QGui.QBrush(self._color2)


class SocketPathProvider:
    @property
    def path1(self) -> QGui.QPainterPath:
        return self._path1

    @property
    def path2(self) -> QGui.QPainterPath:
        return self._path2

    def __init__(self, pathFunc: Callable[[float], QGui.QPainterPath]) -> None:
        self._pathFunc = pathFunc
        self._radius = SOCKET_RADIUS
        self.update()

    def update(self) -> None:
        self._path1 = self.createPath(self._radius)
        self._path2 = self.createPath(self._radius / 2)

    def setPathFunc(self, pathFunc: Callable[[float], QGui.QPainterPath]) -> None:
        self._path = pathFunc
        self.update()

    def createPath(self, radius: float) -> QPainterPath:
        return self._pathFunc(radius)


class SocketPainter:
    @property
    def primaryBrush(self) -> QGui.QBrush:
        return self._colorProvider.PrimaryBrush

    @property
    def secondaryBrush(self) -> QGui.QBrush:
        return self._colorProvider.SecondaryBrush

    def __init__(
        self,
        pathProvider: SocketPathProvider,
        colorProvider: SocketColorProvider,
        optional: bool,
    ) -> None:
        self._colorProvider = colorProvider
        self._pathProvider = pathProvider
        self._optional = optional
        self._radius = SOCKET_RADIUS  # let users pick this at some point
        self.update()

    def update(self) -> None:
        ...

    def getPath(self, radius: float) -> QPainterPath:
        return self._pathProvider.createPath(radius)

    def paint(
        self,
        painter: QGui.QPainter,
    ) -> None:
        painter.setPen(self._colorProvider.Pen)
        painter.setBrush(self._colorProvider.PrimaryBrush)
        painter.drawPath(self._pathProvider.path1)

        if self._optional:
            painter.setBrush(self._colorProvider.SecondaryBrush)
            painter.drawPath(self._pathProvider.path2)


def circle(radius: float) -> QPainterPath:
    socketPath = QPainterPath()
    socketPath.addEllipse(
        QPointF(SLOT_MIN_HEIGHT / 2, SLOT_MIN_HEIGHT / 2), radius, radius
    )
    return socketPath.simplified()


def diamond(radius: float) -> QPainterPath:
    socketPath = QPainterPath()
    centerPoint = QPointF(SLOT_MIN_HEIGHT / 2, SLOT_MIN_HEIGHT / 2)
    socketPath.addPolygon(
        [
            QPointF(0, radius) + centerPoint,
            QPointF(radius, 0) + centerPoint,
            QPointF(0, -radius) + centerPoint,
            QPointF(-radius, 0) + centerPoint,
        ]
    )
    return socketPath.simplified()


def square(radius: float) -> QPainterPath:
    socketPath = QPainterPath()
    socketPath.addRect(
        SLOT_MIN_HEIGHT / 2 - radius,
        SLOT_MIN_HEIGHT / 2 - radius,
        radius * 2,
        radius * 2,
    )
    return socketPath.simplified()


# TODO: extend to dynamically add styles, let users change them and save them to disk
class SocketStyles:
    def __init__(self) -> None:
        self._registeredPaths: Dict[str, SocketPathProvider] = {
            "node": SocketPathProvider(circle),
            "reroute": SocketPathProvider(diamond),
            "array": SocketPathProvider(square),
        }
        self._registeredTypes: Dict[str, SocketColorProvider] = {}
        self._default_colorProvider = SocketColorProvider(QGui.QColor("#808080"))
        self._default_pathProvider = self._registeredPaths["node"]

    def getSocketPainter(
        self, typeName: str, socketType: str, isOptional: bool = False
    ) -> SocketPainter:
        pathProvider = self._registeredPaths.get(socketType, self._default_pathProvider)
        if typeName in self._registeredTypes:
            colorProvider = self._registeredTypes[typeName]
        else:
            sha224 = hashlib.sha224(usedforsecurity=False)
            sha224.update(typeName.encode("utf-8"))
            hash = sha224.digest()
            hue = (
                float(int.from_bytes(hash[:2], byteorder="little", signed=False))
                / 0xFFFF
            )
            sat = (
                float(int.from_bytes(hash[2:3], byteorder="little", signed=False))
                / 0xFF
            )
            val = (
                float(int.from_bytes(hash[3:4], byteorder="little", signed=False))
                / 0xFF
            )
            hue = int(hue * 360)
            sat = int(sat * 100 + 155)
            val = int(val * 155 + 100)
            colorProvider = SocketColorProvider(QGui.QColor.fromHsv(hue, sat, val))
            self._registeredTypes[typeName] = colorProvider
        return SocketPainter(pathProvider, colorProvider, isOptional)
