from typing import Any

import aiohttp
from fastapi import WebSocket
from starlette.endpoints import WebSocketEndpoint

from echo_agent.models import PyTunnelSession, TunnelSession
from echo_agent.tunnel import AsyncTunnelManager, ssh, telnet  # , vnc


class TunnelEndpoint(WebSocketEndpoint):
    encoding = 'text'

    tunnel_managers = {
        'ssh': ssh.SSHTunnelManager,
        'telnet': telnet.TelnetTunnelManager,
        # 'vnc': vnc.VNCTunnelManager,
    }

    manager: AsyncTunnelManager = None

    async def on_connect(self, websocket: WebSocket) -> None:
        sid = websocket.query_params.get('sid')

        if sid is None:
            return await websocket.close(4401)

        session = await TunnelSession.get_or_none(sid=sid).prefetch_related('credentials')

        if session is None:
            return await websocket.close(4401)

        session = PyTunnelSession.from_orm(session)

        if session.proto not in self.tunnel_managers:
            return await websocket.close(4400)

        self.manager = self.tunnel_managers[session.proto]()

        await self.manager.on_connect(websocket, session)

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        await self.manager.on_receive(websocket, data)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if self.manager is not None:
            await self.manager.on_disconnect(websocket, close_code)
