import asyncio
import threading
from typing import Callable

from cryptography.fernet import Fernet
from fastapi import WebSocket
from paramiko import AutoAddPolicy
from paramiko.channel import Channel
from paramiko.client import SSHClient
from starlette.websockets import WebSocketState

from echo_agent.config import Config
from echo_agent.models import PyTunnelSession
from echo_agent.tunnel import AsyncTunnelManager


config = Config()


class SSHTunnelManager(AsyncTunnelManager):
    channel: Channel

    async def on_connect(self, websocket: WebSocket, session: PyTunnelSession) -> None:
        client = SSHClient()

        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy)

        client.connect(
            hostname=str(session.credentials.host),
            port=session.port,
            username=session.credentials.username,
            password=Fernet(config.secret).decrypt(session.credentials.password).decode(),  # noqa
        )

        channel = client.invoke_shell('xterm')

        thread = threading.Thread(target=SSHTunnelManager._create_channel_to_websocket_tunnel_task(channel, websocket))
        thread.start()

        self.channel = channel

        await websocket.accept()

    async def on_receive(self, websocket: WebSocket, data: str) -> None:
        if self.channel.closed:
            return await websocket.close()

        self.channel.send(data.encode())

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if not self.channel.closed:
            self.channel.close()

    @staticmethod
    def _create_channel_to_websocket_tunnel_task(channel: Channel, websocket: WebSocket) -> Callable:
        async def _channel_to_websocket_tunnel():
            while not channel.closed:
                await asyncio.sleep(0.1)
                data = channel.recv(1024)

                if websocket.client_state == WebSocketState.DISCONNECTED:
                    return channel.close()

                await websocket.send_text(data.decode())

        def _channel_to_websocket_tunnel_runner():
            asyncio.run(_channel_to_websocket_tunnel())

        return _channel_to_websocket_tunnel_runner
