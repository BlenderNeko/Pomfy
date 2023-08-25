from typing import Optional, Dict, Any, cast
import PySide6.QtCore
import PySide6.QtGui as QGui
from PySide6.QtWidgets import *

from gui import QNodeEditor
import os
import json

from gui.navigator import NavigatorWidget
from gui.workFolder import WorkFolder, MaybeSceneCollection
from node.factory.comfyFactory import ComfyFactory
from server import ComfyConnection
from style.socketStyle import SocketStyles


class NodeEditorWindow(QMainWindow):
    def __init__(self, args: Any) -> None:
        super().__init__()
        self.settings = self.initSettings()
        self.accelerate = not args.cpu
        self.connection = ComfyConnection()

        self.nodeFactory = ComfyFactory(SocketStyles())
        self.nodeFactory.loadNodeDefinitions(self.connection.getNodeDefs())

        self.workFolderLoc = self.getWorkFolderLoc()
        self.workFolder = WorkFolder(self.workFolderLoc, self.nodeFactory)
        self.initUI()

    def initUI(self) -> None:
        self.navigator = NavigatorWidget(self.workFolder)
        self.navigator.opened.connect(self.openNodes)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeNodes)
        self.splitter = QSplitter(self)
        self.splitter.insertWidget(0, self.navigator)
        self.splitter.insertWidget(1, self.tabs)
        self.setCentralWidget(self.splitter)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([300, 300])

        self.setWindowTitle("Pomfy node editor")

        menu = self.menuBar()
        fileMenu = menu.addMenu("File")

        saveAction = fileMenu.addAction("New")
        saveAction.triggered.connect(self.newNodeTree)

        saveAction = fileMenu.addAction("Save")
        saveAction.triggered.connect(self.saveNodes)
        # loadAction = fileMenu.addAction("Load")
        # sendAction = fileMenu.addAction("Send")

        # loadAction.triggered.connect(self.loadNodes)
        # sendAction.triggered.connect(self.sendPrompt)
        self.showMaximized()

    def openNodes(self, collection: MaybeSceneCollection, name: str) -> None:
        for i in range(self.tabs.count()):
            editor = cast(QNodeEditor, self.tabs.widget(i))
            if editor.sceneCollection == collection:
                self.tabs.setCurrentIndex(i)
                return
        editor = QNodeEditor(collection, accelerate=self.accelerate)
        ind_current = self.tabs.currentIndex()
        ind = self.tabs.insertTab(ind_current + 1, editor, collection.name)
        self.tabs.setCurrentIndex(ind)

    def closeNodes(self, index: int) -> None:
        editor = cast(QNodeEditor, self.tabs.widget(index))
        result: int = QMessageBox.StandardButton.Discard
        if editor.sceneCollection.hasChanges():
            msgBox = QMessageBox()
            msgBox.setText("Do you want to save your changes?")
            msgBox.setStandardButtons(
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )
            msgBox.setDefaultButton(QMessageBox.StandardButton.Save)
            result = msgBox.exec()
        if result == QMessageBox.StandardButton.Cancel:
            return
        self.tabs.removeTab(index)
        editor.sceneCollection.close(result == QMessageBox.StandardButton.Save)

    def closeEvent(self, event: QGui.QCloseEvent) -> None:
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
        return super().closeEvent(event)

    def getWorkFolderLoc(self) -> str:
        if "workFolder" not in self.settings:
            path = os.path.join(os.getcwd(), "workFolder")
            os.makedirs(path, exist_ok=True)
            self.settings["workFolder"] = path
        return self.settings["workFolder"]

    def initSettings(self) -> Dict[str, Any]:
        if not os.path.isfile("settings.json"):
            with open("settings.json", "w", encoding="utf-8") as f:
                f.write("{}")
            return {}

        with open("settings.json", "r") as f:
            settings: Dict[str, Any] = json.load(f)
        return settings

    def newNodeTree(self) -> None:
        self.navigator.newFile()

    def saveNodes(self) -> None:
        editor = cast(QNodeEditor, self.tabs.currentWidget())
        editor.sceneCollection.save()

    # def loadNodes(self) -> None:
    #    file = QFileDialog.getOpenFileName(
    #        self, "Load node tree", filter="Pomfy Node Tree (*.pnt)"
    #    )
    #    with open(file[0], "r") as f:
    #        saveString = f.readline()
    #    self.nodeEditorWidget.sceneCollection.fromJSON(saveString)

    # def sendPrompt(self) -> None:
    #    prompt = self.nodeEditorWidget.sceneCollection.prompt()
    #    result = self.connection.sendPrompt(prompt)
    #    print(result)
