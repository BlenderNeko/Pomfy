from typing import Any, Callable, List

import PySide6.QtCore as QCor
import PySide6.QtGui as QGui
import PySide6.QtGui
import PySide6.QtWidgets as QWgt


class _QLabel(QWgt.QLabel):
    hoverEnter = QCor.Signal(int)
    clicked = QCor.Signal(int)
    hoverLeave = QCor.Signal()

    def __init__(self, string: str, index: int, ele: Any):
        super().__init__(string)
        self.index = index
        self.content = ele

    def mouseReleaseEvent(self, ev: QGui.QMouseEvent) -> None:
        if self.contentsRect().contains(ev.pos()):
            self.clicked.emit(self.index)
        return super().mouseReleaseEvent(ev)

    def enterEvent(self, event: QGui.QEnterEvent) -> None:
        self.hoverEnter.emit(self.index)
        return super().enterEvent(event)

    def leaveEvent(self, event: QCor.QEvent) -> None:
        self.hoverLeave.emit()
        return super().leaveEvent(event)


# TODO: concurrency issues with filtering and hover events
class _QSearchableMenu(QWgt.QWidget):
    clicked = QCor.Signal(int)

    @property
    def selectedIndex(self) -> int:
        return self._filteredItems[self._selected].index

    def __init__(
        self,
        items: List[Any],
        renderFunction: Callable[[Any], str],
        filterFunction: Callable[[Any, str], bool],
        maxRows: int = 5,
        parent: QWgt.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._items = [
            _QLabel(renderFunction(ele), i, ele) for i, ele in enumerate(items)
        ]
        self._filterFunction = filterFunction
        self._filteredItems = self._items.copy()
        self._scrollPosition = 0
        self._selected = 0
        self._maxRows = maxRows
        self._itemCount = len(items)
        self._allowNormalScroll = False
        self._selection_color = QGui.QColor("#4251FF")
        self._accept_hover = True
        self._delayed_ind = -1
        self.initUI()
        self.setStyleSheet(
            f"_QLabel[selected=true]{{background-color : {self._selection_color.name()}}}"
        )
        self.update_selected(0, True)

    def initUI(self) -> None:
        self.setMaximumHeight(20 * self._maxRows)
        layout = QWgt.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        for item in self._items:
            item.setProperty("selected", False)
            item.setMaximumHeight(20)
            item.hoverEnter.connect(self.onHoverEnter)
            item.hoverLeave.connect(self.onHoverLeave)
            item.clicked.connect(self.onClicked)
            layout.addWidget(item)
            item.hide()
        # layout.insertStretch(-1, 1)
        for i in range(0, min(self._itemCount, self._maxRows)):
            self._items[i].show()

    def update_selected(self, ind: int, isSelected: bool) -> None:
        if ind < len(self._filteredItems):
            self._filteredItems[ind].setProperty("selected", isSelected)
            self.style().unpolish(self._filteredItems[ind])
            self.style().polish(self._filteredItems[ind])

    def setFilter(self, filter: Callable[[Any, str], bool]) -> None:
        self._filterFunction = filter
        self.filter("")

    def filter(self, filter_string: str) -> None:
        self._accept_hover = False
        self.update_selected(self._selected, False)
        self._filteredItems = []
        for ele in self._items:
            ele.hide()
            if self._filterFunction(ele.content, filter_string):
                self._filteredItems.append(ele)
        for i in range(0, min(len(self._filteredItems), self._maxRows)):
            self._filteredItems[i].show()
        self._scrollPosition = 0
        self._selected = 0
        self.update_selected(0, True)
        self._accept_hover = True
        if self._delayed_ind != -1:
            self.onHoverEnter(self._delayed_ind)

    def indToTop(self, ind: int) -> None:
        item_ind = -1
        for i, ele in enumerate(self._filteredItems):
            if ele.index == ind:
                item_ind = i
        if item_ind == -1:
            return
        self.update_selected(self._selected, False)
        top_ind = max(0, min(len(self._filteredItems) - self._maxRows, item_ind))
        for ele in self._filteredItems:
            ele.hide()
        for i in range(top_ind, min(top_ind + self._maxRows, len(self._filteredItems))):
            self._filteredItems[i].show()
        self._scrollPosition = ind
        self._selected = ind
        self.update_selected(ind, True)

    def onClicked(self, ind: int) -> None:
        self.clicked.emit(ind)

    def onHoverEnter(self, ind: int) -> None:
        if not self._accept_hover:
            self._delayed_ind = ind
            return
        self._allowNormalScroll = True
        self.update_selected(self._selected, False)

        new_index = 0
        for i, ele in enumerate(self._filteredItems):
            if ele.index == ind:
                new_index = i
                break
        self._selected = new_index

        self.update_selected(self._selected, True)
        self._delayed_ind = -1

    def onHoverLeave(self) -> None:
        self._allowNormalScroll = False

    def _setIndex(self, ind: int) -> None:
        if ind < 0 or ind >= len(self._filteredItems):
            return
        self.update_selected(self._selected, False)
        self.update_selected(ind, True)
        self._selected = ind

        if (
            self._selected < self._scrollPosition
            or self._selected >= self._scrollPosition + self._maxRows
        ):
            self._update_scroll()

    def scrollByInd(self, x: int) -> None:
        if self._allowNormalScroll:
            self._updateScrollPosition(x)

        x = 1 if x > 0 else -1
        if self._selected + x < 0 or self._selected + x >= len(self._filteredItems):
            return
        self._setIndex(self._selected + x)

    def _updateScrollPosition(self, delta: int) -> None:
        if delta > 0 and self._scrollPosition + delta + self._maxRows <= len(
            self._filteredItems
        ):
            for i in range(self._scrollPosition, self._scrollPosition + delta):
                self._filteredItems[i].hide()
            for i in range(
                self._scrollPosition + self._maxRows,
                self._scrollPosition + self._maxRows + delta,
            ):
                self._filteredItems[i].show()
            self._scrollPosition += delta
        elif delta < 0 and self._scrollPosition > 0:
            for i in range(
                self._scrollPosition + self._maxRows + delta,
                self._scrollPosition + self._maxRows,
            ):
                self._filteredItems[i].hide()
            for i in range(self._scrollPosition + delta, self._scrollPosition):
                self._filteredItems[i].show()
            self._scrollPosition += delta

    def _update_scroll(self) -> None:
        if self._selected < self._scrollPosition:
            delta = self._selected - self._scrollPosition
            self._updateScrollPosition(delta)
        elif self._selected >= self._scrollPosition + self._maxRows:
            delta = self._selected - (self._scrollPosition + self._maxRows - 1)
            self._updateScrollPosition(delta)


class QSearchableMenu(QWgt.QWidget):
    finished = QCor.Signal(int)
    abort = QCor.Signal()
    contentChanged = QCor.Signal()

    def __init__(
        self,
        items: List[Any],
        renderFunction: Callable[[Any], str],
        filterFunction: Callable[[Any, str], bool],
        maxRows: int = 5,
        parent: QWgt.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._maxRows = maxRows
        self._items = items
        self._renderFunction = renderFunction
        self._filterFunction = filterFunction
        self._hasFinished = False
        self.initUI()

    def initUI(self) -> None:
        self._layout = QWgt.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._filterBox = QWgt.QLineEdit()
        self._filterBox.setFixedWidth(300)
        self._filterBox.textChanged.connect(self._onFilterChange)
        self._list = _QSearchableMenu(
            self._items,
            self._renderFunction,
            self._filterFunction,
            maxRows=self._maxRows,
        )
        self._list.setFixedWidth(300)
        self._list.clicked.connect(self._onClick)
        self._layout.addWidget(self._filterBox)
        self._layout.addWidget(self._list)

    @property
    def items(self) -> List[Any]:
        return self._items

    def indToTop(self, ind: int) -> None:
        self._list.indToTop(ind)

    def setFilter(self, filter: Callable[[Any, str], bool]) -> None:
        self._filterFunction = filter
        self.clearText()
        self._list.setFilter(self._filterFunction)

    def clearText(self) -> None:
        self._filterBox.setText("")

    def _onClick(self, ind: int) -> None:
        self._finished(ind)
        self.close()

    def _finished(self, ind: int) -> None:
        self._hasFinished = True
        self.finished.emit(ind)

    def keyPressEvent(self, event: QGui.QKeyEvent) -> None:
        if (
            event.key() == QGui.Qt.Key.Key_Return
            or event.key() == QGui.Qt.Key.Key_Enter
        ):
            self._finished(self._list.selectedIndex)
            self.close()
        elif event.key() == QGui.Qt.Key.Key_Down:
            self._list.scrollByInd(1)
        elif event.key() == QGui.Qt.Key.Key_Up:
            self._list.scrollByInd(-1)
        super().keyPressEvent(event)

    def showEvent(self, event: QGui.QShowEvent) -> None:
        super().showEvent(event)
        self._filterBox.setFocus()

    def hideEvent(self, event: QGui.QHideEvent) -> None:
        super().hideEvent(event)
        if not self._hasFinished:
            self.abort.emit()
        self._hasFinished = False

    def wheelEvent(self, event: QGui.QWheelEvent) -> None:
        isDown = event.angleDelta().y() > 0
        delta = -1 if isDown else 1
        self._list.scrollByInd(delta)

    def _onFilterChange(self) -> None:
        self._list.filter(self._filterBox.text())
        self._list.adjustSize()
        self.adjustSize()
        self.contentChanged.emit()
