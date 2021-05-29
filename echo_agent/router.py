import asyncio
from secrets import token_urlsafe

from fastapi.background import BackgroundTasks
from fastapi.routing import APIRouter
from starlette.routing import WebSocketRoute

from echo_agent.endpoints import TunnelEndpoint
from echo_agent.models import PyTunnelSession, TunnelSession


router = APIRouter()

router.routes.append(WebSocketRoute('/tunnel', TunnelEndpoint))


async def delete_tunnel_session(sid: str):
    await asyncio.sleep(10)

    session = await TunnelSession.get_or_none(sid=sid)

    if session is not None:
        await session.delete()


@router.post('/tunnel/create', response_model=str)
async def create_tunnel_session(data: PyTunnelSession, background_tasks: BackgroundTasks) -> str:
    session = await TunnelSession.create(sid=token_urlsafe(48), **data.dict())
    background_tasks.add_task(delete_tunnel_session, session.sid)
    return session.sid
