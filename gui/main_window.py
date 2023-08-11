from typing import Optional
import PySide6.QtCore
from PySide6.QtWidgets import *

from gui import QNodeEditor


class NodeEditorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.initUI()

    def initUI(self) -> None:
        self.nodeEditorWidget = QNodeEditor(self)
        self.setCentralWidget(self.nodeEditorWidget)

        self.setGeometry(200, 200, 800, 600)
        self.setWindowTitle("Pomfy node editor")

        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        saveAction = fileMenu.addAction("Save")
        loadAction = fileMenu.addAction("Load")
        sendAction = fileMenu.addAction("Send")
        saveAction.triggered.connect(self.saveNodes)
        loadAction.triggered.connect(self.loadNodes)
        sendAction.triggered.connect(self.sendPrompt)
        self.nodeEditorWidget.sceneCollection
        self.show()

    def saveNodes(self) -> None:
        saveString = self.nodeEditorWidget.sceneCollection.toJSON()
        file = QFileDialog.getSaveFileName(
            self, "Save node tree", filter="Pomfy Node Tree (*.pnt)"
        )
        with open(file[0], "w") as f:
            f.write(saveString)

    def loadNodes(self) -> None:
        file = QFileDialog.getOpenFileName(
            self, "Load node tree", filter="Pomfy Node Tree (*.pnt)"
        )
        with open(file[0], "r") as f:
            saveString = f.readline()
        self.nodeEditorWidget.sceneCollection.fromJSON(saveString)

    def sendPrompt(self) -> None:
        prompt = self.nodeEditorWidget.sceneCollection.prompt()
        result = self.nodeEditorWidget.connection.sendPrompt(prompt)
        print(result)
