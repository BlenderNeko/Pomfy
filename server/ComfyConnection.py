import websockets.sync.client as client
import PySide6.QtCore as QCor
from typing import Any, Dict, List
import uuid
import json
import urllib.request as request
import urllib.parse as parse

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


class ComfyConnection:
    def __init__(self) -> None:
        self.threadpool = QCor.QThreadPool()
        self.threadpool.setMaxThreadCount(5)
        pass

    def getNodeDefs(self) -> str:
        req = request.Request(f"http://{server_address}/object_info")
        return request.urlopen(req).read()

    def sendPrompt(self, prompt: Dict[str, Any]) -> Any:
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode("utf-8")
        req = request.Request(f"http://{server_address}/prompt", data=data)
        response = json.loads(request.urlopen(req).read())
        worker = websocketWorker(response["prompt_id"])
        self.threadpool.start(worker)
        return


class websocketSignals(QCor.QObject):
    ...


class websocketWorker(QCor.QRunnable):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.promptId = args[0]

    @QCor.Slot()
    def run(self) -> None:
        try:
            with client.connect(
                f"ws://{server_address}/ws?clientId={client_id}"
            ) as webSocket:
                while True:
                    packet = webSocket.recv()
                    print(packet)
                    if isinstance(packet, str):
                        message = json.loads(packet)
                        if "type" in message and message["type"] == "executing":
                            data = message["data"]
                            if (
                                "node" in data
                                and data["node"] is None
                                and "prompt_id" in data
                                and data["prompt_id"] == self.promptId
                            ):
                                break
        except Exception as error:
            ...
        else:
            ...
        finally:
            ...
