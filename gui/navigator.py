from typing import Optional, cast
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from gui.workFolder import MaybeSceneCollection, WorkFolder, SceneCollectionItem


class NavigatorWidget(QWgt.QWidget):
    opened = QCor.Signal(MaybeSceneCollection, str)

    def __init__(
        self, workFolder: WorkFolder, parent: QWgt.QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.dirview = QWgt.QTreeView()
        self.workFolder = workFolder

        self.setLayout(QWgt.QHBoxLayout())
        self.layout().addWidget(self.dirview)
        self.dirview.setModel(workFolder.model)
        self.dirview.setHeaderHidden(True)
        self.dirview.setEditTriggers(QWgt.QAbstractItemView.EditTrigger.EditKeyPressed)
        self.dirview.doubleClicked.connect(self.openNodes)

    def openNodes(self, index: QCor.QModelIndex) -> None:
        target = cast(SceneCollectionItem, self.workFolder.model.itemFromIndex(index))
        self.opened.emit(target.collection, "root")

    def newFile(self) -> None:
        ind = self.workFolder.newFile()
        self.dirview.setCurrentIndex(ind)
        self.openNodes(ind)
        self.dirview.edit(ind)
