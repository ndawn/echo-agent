from abc import ABC, abstractmethod

from fastapi.websockets import WebSocket

from echo_agent.models import PyTunnelSession


class AsyncTunnelManager(ABC):
    channel = None

    @abstractmethod
    async def on_connect(self, websocket: WebSocket, session: PyTunnelSession) -> None:
        pass

    @abstractmethod
    async def on_receive(self, websocket: WebSocket, data: str) -> None:
        pass

    @abstractmethod
    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        pass
