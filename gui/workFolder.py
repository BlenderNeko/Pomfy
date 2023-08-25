from typing import List, Tuple

import os
from glob import glob
import re

from node import SceneCollection
from node.factory.comfyFactory import ComfyFactory
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import QModelIndex


class MaybeSceneCollection:
    def __init__(self, path: str, factory: ComfyFactory) -> None:
        self.path = path
        self.factory = factory
        self._collection: SceneCollection | None = None
        pass

    @classmethod
    def create(cls, folder: str, factory: ComfyFactory) -> "MaybeSceneCollection":
        name = cls._makeNameUnique("nodeTree", folder)
        path = os.path.join(folder, f"{name}.pnt")
        obj = cls(path, factory)
        obj._collection = SceneCollection(factory)
        obj.save()
        return obj

    @property
    def collection(self) -> SceneCollection:
        if self._collection is None:
            self._collection = SceneCollection(self.factory)
            with open(self.path, "r") as f:
                self._collection.fromJSON(" ".join(f.readlines()))
            self._collection.undoStack.setClean()
        return self._collection

    @property
    def name(self) -> str:
        return os.path.splitext(os.path.basename(self.path))[0]

    @staticmethod
    def _getFiles(path: str) -> Tuple[List[str], List[int]]:
        names: List[str] = []
        counts: List[int] = []
        names = glob(os.path.join(path, "*.pnt"))
        names = [os.path.splitext(os.path.basename(x))[0] for x in names]
        splits = [re.split(r"\_(?=\d{3}\.pnt$)", x) for x in names]
        names, counts = zip(*[(x[0], int(x[1]) if len(x) > 1 else 0) for x in splits])
        return (names, counts)

    @classmethod
    def _makeNameUnique(cls, name: str, path: str) -> str:
        names, counts = cls._getFiles(path)
        taken = [(n, i) for n, i in zip(names, counts) if n == name]
        if len(taken) > 0:
            for j, (n, i) in enumerate(taken):
                if j != i and j != 0:
                    return f"{name}_{j:03}"
            return f"{name}_{len(taken):03}"
        return name

    def rename(self, name: str) -> str:
        name = self._makeNameUnique(name, os.path.split(self.path)[0])
        newPath = os.path.join(os.path.split(self.path)[0], f"{name}.pnt")
        os.rename(self.path, newPath)
        self.path = newPath
        return name

    def hasChanges(self) -> bool:
        if self._collection is None:
            return False
        return not self.collection.undoStack.isClean()

    def close(self, save: bool = True) -> None:
        if save:
            self.save()
        self._collection = None

    def save(self) -> None:
        if self._collection is not None:
            serialized = self._collection.toJSON()
            with open(self.path, "w") as f:
                f.write(serialized)
            self._collection.undoStack.setClean()


class SceneCollectionItem(QStandardItem):
    def __init__(self, collection: MaybeSceneCollection) -> None:
        self.collection = collection
        super().__init__(collection.name)


class WorkFolder:
    def __init__(self, folder: str, factory: ComfyFactory) -> None:
        self.workFolder = os.path.join(folder, "Pomfy workFolder")
        self.treeFolder = os.path.join(self.workFolder, "nodeTrees")
        self.factory = factory
        self.sceneCollections: List[MaybeSceneCollection] = []
        if not os.path.exists(self.workFolder):
            os.makedirs(self.workFolder)
            os.makedirs(self.treeFolder)
            # TODO: setup empty subgraph library
        treeFiles = glob(os.path.join(self.treeFolder, "*.pnt"))
        for f in treeFiles:
            obj = MaybeSceneCollection(f, factory)
            self.sceneCollections.append(obj)

        self.initModel()

    def initModel(self) -> None:
        self._model = QStandardItemModel()
        for col in self.sceneCollections:
            self._model.appendRow(SceneCollectionItem(col))
        self._model.itemChanged.connect(self.renameFile)

    def renameFile(self, item: SceneCollectionItem) -> None:
        name = item.collection.rename(item.text())
        blockState = self.model.blockSignals(True)
        item.setText(name)
        self.model.blockSignals(blockState)

    def newFile(self) -> QModelIndex:
        collection = MaybeSceneCollection.create(self.treeFolder, self.factory)
        self.sceneCollections.append(collection)
        colItem = SceneCollectionItem(collection)
        self._model.appendRow(colItem)
        return self._model.indexFromItem(colItem)

    @property
    def model(self) -> QStandardItemModel:
        return self._model
