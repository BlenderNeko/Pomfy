import PySide6.QtWidgets as QWgt
import PySide6.QtCore as QCor
import PySide6.QtGui as QGui


class QSlotContentGraphicsItem(QWgt.QGraphicsItem):
    def __init__(self, parent: QWgt.QGraphicsItem | None = None) -> None:
        super().__init__(parent)

    def resize(self, width: float) -> None:
        raise NotImplementedError()


class QSlotContentProxyGraphicsItem(QSlotContentGraphicsItem):
    def __init__(
        self,
        content: QWgt.QWidget,
        width: float,
        height: float,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._width = width
        self._height = height
        self._content = content
        self.initUI()

    def initUI(self) -> None:
        self._proxy = QWgt.QGraphicsProxyWidget(self)
        self._content.resize(int(self._width), int(self._height))
        self._proxy.setWidget(self._content)
        self._proxy.prepareGeometryChange()
        self._proxy.setGeometry(0, 0, self._width, self._height)

    def resize(self, width: float) -> None:
        self._width = width
        self._proxy.prepareGeometryChange()
        self._proxy.setGeometry(0, 0, self._width, self._height)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = ...,
    ) -> None:
        pass

    def boundingRect(self) -> QCor.QRectF:
        return QCor.QRectF(0, 0, self._width, self._height)
