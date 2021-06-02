import asyncio
import threading
from socket import socket as Socket  # noqa
from telnetlib import Telnet
from typing import Callable

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from echo_agent.models import PyTunnelSession
from echo_agent.tunnel import AsyncTunnelManager


class TelnetTunnelManager(AsyncTunnelManager):
    channel: Telnet

    async def on_connect(self, websocket: WebSocket, session: PyTunnelSession) -> None:
        client = Telnet()
        client.open(session.host, session.port)

        if session.username:
            client.write(f'{session.username}\n'.encode())

        if session.password:
            client.write(f'{session.password}\n'.encode())

        thread = threading.Thread(
            target=TelnetTunnelManager._create_channel_to_websocket_tunnel_task(client, websocket)
        )
        thread.start()

        self.channel = client

        await websocket.accept()

    async def on_receive(self, websocket: WebSocket, data: str) -> None:
        if getattr(self.channel.sock, '_closed', False):
            return await websocket.close()

        self.channel.write(data.encode())

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if not getattr(self.channel.sock, '_closed', False):
            self.channel.close()

    @staticmethod
    def _create_channel_to_websocket_tunnel_task(channel: Telnet, websocket: WebSocket) -> Callable:
        async def _channel_to_websocket_tunnel():
            while True:
                await asyncio.sleep(0.1)

                try:
                    data = channel.read_very_eager()

                    if websocket.client_state == WebSocketState.DISCONNECTED:
                        return channel.close()

                    await websocket.send_text(data.decode())
                except EOFError:
                    if websocket.client_state != WebSocketState.DISCONNECTED:
                        return await websocket.close()

        def _channel_to_websocket_tunnel_runner():
            asyncio.run(_channel_to_websocket_tunnel())

        return _channel_to_websocket_tunnel_runner
