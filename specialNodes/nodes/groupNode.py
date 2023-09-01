from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    TypeVar,
    Generic,
    cast,
    Callable,
    List,
    Generator,
    Tuple,
)
import PySide6.QtCore
import PySide6.QtGui

import PySide6.QtWidgets as QWgt
import PySide6.QtCore as QCor
import PySide6.QtGui as QGui
from nodeSlots.nodeSlot import NodeSlot
from specialNodes.nodes.expandableNode import ExpandableNode


if TYPE_CHECKING:
    from node.factory import ComfyFactory

from node import Node, NodeScene
from specialNodes.customNode import CustomNode, registerCustomNode


@registerCustomNode
class GroupIn(ExpandableNode, CustomNode):
    def __init__(
        self,
        nodeScene: NodeScene,
        nodeClass: str,
        isOutput: bool = False,
        description: str = "",
        title: str = "undefined",
    ) -> None:
        super().__init__(nodeScene, nodeClass, isOutput, description, title)

    @classmethod
    def getClassName(cls) -> str:
        return "GroupIn"

    @classmethod
    def getDisplayName(cls) -> str:
        return "Group Input"

    @classmethod
    def getCategory(cls) -> str | None:
        return "Layout"

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        assert factory.activeScene is not None
        node = cls(
            factory.activeScene,
            cls.getClassName(),
            description="group node input",
            title=cls.getDisplayName(),
        )
        node.addExpandableOutput()
        return node

    def generateSettings(self) -> List[Tuple[str, QWgt.QWidget]]:
        base_settings = super().generateSettings()
        self.lstWgt = MoveableList()
        self.lstWgt.setDragDropMode(QWgt.QListWidget.DragDropMode.InternalMove)
        self.lstWgt.reordered.connect(self.reorder)

        for slt in self.outputs[:-1]:
            item = QWgt.QListWidgetItem(self.lstWgt)
            Litem = ListItem(slt, item)
            Litem.requestDelete.connect(self.delete)
            item.setSizeHint(Litem.sizeHint())
            self.lstWgt.setItemWidget(item, Litem)
        items = base_settings + [("inputs", self.lstWgt)]
        return items

    # TODO: redo/undo

    def reorder(self, slots: List[NodeSlot]) -> None:
        for i, slot in enumerate(slots):
            if slot.ind != i:
                slot.ind = i
        self._outputs = slots + [self.outputs[-1]]
        self.grNode.updateSlots()
        for slot in slots:
            slot.socket.updateEdges()

    def delete(self, targetSlot: ListItem) -> None:
        self.removeOutputSlot(targetSlot.slot)
        ind = self.lstWgt.indexFromItem(targetSlot.item).row()
        self.lstWgt.removeItemWidget(targetSlot.item)
        self.lstWgt.model().removeRow(ind)
        for slot in self.outputs:
            slot.socket.updateEdges()


class MoveableList(QWgt.QListWidget):
    reordered = QCor.Signal(object)

    def dropEvent(self, event: QGui.QDropEvent) -> None:
        super().dropEvent(event)
        wgts = [self.itemWidget(self.item(i)) for i in range(self.count())]
        slots = [cast(ListItem, x).slot for x in wgts]
        self.reordered.emit(slots)


class ListItem(QWgt.QWidget):
    requestDelete = QCor.Signal(object)

    def __init__(
        self,
        slot: NodeSlot,
        item: QWgt.QListWidgetItem,
        parent: QWgt.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.slot = slot
        self.item = item
        layout = QWgt.QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        self.label = QWgt.QLabel(slot.name)
        self.edit = LabelEdit("")
        self.edit.hide()
        self.edit.abortEdit.connect(self.showLabel)
        self.edit.finishedEdit.connect(self.updatelabel)
        layout.addWidget(self.label, alignment=QCor.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.edit, alignment=QCor.Qt.AlignmentFlag.AlignLeft)
        # TODO: Icons ?
        close_icon = QWgt.QApplication.style().standardIcon(
            QWgt.QStyle.StandardPixmap.SP_TitleBarCloseButton
        )
        self.delBtn = QWgt.QPushButton(close_icon, "", self)
        self.delBtn.clicked.connect(self.onRequestDelete)
        layout.addWidget(self.delBtn, alignment=QCor.Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

    def onRequestDelete(self) -> None:
        self.requestDelete.emit(self)

    def showEdit(self) -> None:
        self.label.hide()
        self.edit.setText(self.label.text())
        self.edit.show()
        self.edit.setFocus()

    def showLabel(self) -> None:
        self.edit.setText(self.label.text())
        self.edit.hide()
        self.label.show()

    def updatelabel(self) -> None:
        self.label.setText(self.edit.text())
        self.slot.name = self.edit.text()
        self.showLabel()

    def mouseDoubleClickEvent(self, event: QGui.QMouseEvent) -> None:
        self.showEdit()
        return super().mouseDoubleClickEvent(event)


class LabelEdit(QWgt.QLineEdit):
    finishedEdit = QCor.Signal()
    abortEdit = QCor.Signal()

    def keyPressEvent(self, event: QGui.QKeyEvent) -> None:
        if (
            event.key() == QGui.Qt.Key.Key_Return
            or event.key() == QGui.Qt.Key.Key_Enter
        ):
            self.finishedEdit.emit()
        if event.key() == QGui.Qt.Key.Key_Escape:
            self.abortEdit.emit()
        return super().keyPressEvent(event)

    def focusOutEvent(self, event: QGui.QFocusEvent) -> None:
        self.finishedEdit.emit()
        return super().focusOutEvent(event)
