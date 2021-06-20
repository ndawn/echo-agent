import asyncio
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from secrets import token_urlsafe

from fastapi.background import BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.routing import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.routing import WebSocketRoute

from echo_agent.config import Config
from echo_agent.endpoints import TunnelEndpoint
from echo_agent.models import PyTunnelSession, TunnelSession


config = Config()

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

router.routes.append(WebSocketRoute('/tunnel', TunnelEndpoint))


async def delete_tunnel_session(sid: str):
    await asyncio.sleep(10)

    session = await TunnelSession.get_or_none(sid=sid)

    if session is not None:
        await session.delete()


@router.post('/tunnel/create', response_model=str)
@limiter.limit('5/minute')
async def create_tunnel_session(data: PyTunnelSession, background_tasks: BackgroundTasks, request: Request) -> str:
    try:
        address = IPv4Address(data.host)
    except AddressValueError:
        raise HTTPException(status_code=400, detail='Address is not a valid IPv4 address')

    if address not in IPv4Network(config.subnet):  # noqa
        raise HTTPException(status_code=403, detail='Target device address is not in this agent\'s subnet')

    session = await TunnelSession.create(sid=token_urlsafe(48), **data.dict())
    background_tasks.add_task(delete_tunnel_session, session.sid)
    return session.sid
