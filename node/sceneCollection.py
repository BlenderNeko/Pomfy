from typing import List, Dict, Any
from undo import NTM
from node.factory import ComfyFactory
from server import ComfyPromptManager
from node import NodeScene
from PySide6.QtGui import QUndoStack
import json


class SceneCollection:
    def __init__(self, nodeFactory: ComfyFactory) -> None:
        self.scenes: List[NodeScene] = []

        self.undoStack = QUndoStack()
        self.ntm = NTM(self.undoStack)
        self.nodeFactory = nodeFactory
        self.rootScene = NodeScene(self)
        self.activeScene = self.rootScene
        self.nodeFactory.activeScene = self.activeScene

    # TODO: scene identifiers
    def toJSON(self) -> str:
        state: Dict[str, Any] = {}
        # TODO: scenes should be ordered by group node dependency
        state["scenes"] = [s.saveState() for s in self.scenes]
        state["rootScene"] = self.rootScene.saveState()
        return json.dumps(state)

    def fromJSON(self, jsonData: str) -> None:
        state = json.loads(jsonData)
        for s in state["scenes"]:
            # TODO: should check for duplicate scenes
            nodeScene = NodeScene(self)
            self.nodeFactory.activeScene = nodeScene
            nodeScene.loadState(s, self.nodeFactory)
            self.scenes.append(nodeScene)
        self.nodeFactory.activeScene = self.rootScene
        self.rootScene.loadState(state["rootScene"], self.nodeFactory)

    def prompt(self) -> Dict[str, Any]:
        promptManager = ComfyPromptManager()
        scenes = [self.rootScene] + self.scenes
        promptDict = promptManager.execute(scenes)
        return promptDict
