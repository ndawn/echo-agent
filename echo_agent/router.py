import aiohttp
import asyncio
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from secrets import token_urlsafe

from fastapi.background import BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from starlette.routing import WebSocketRoute

from echo_agent.config import Config
from echo_agent.endpoints import TunnelEndpoint
from echo_agent.models import (
    AuthMethodEnum,
    HostCredentials,
    PyTunnelSessionCreateIn,
    PyUser,
    TunnelSession,
)


config = Config()

router = APIRouter()

router.routes.append(WebSocketRoute('/tunnel', TunnelEndpoint))


async def delete_tunnel_session(sid: str):
    await asyncio.sleep(10)

    session = await TunnelSession.get_or_none(sid=sid)

    if session is not None:
        await session.delete()


@router.post('/tunnel/create', response_model=str)
async def create_tunnel_session(data: PyTunnelSessionCreateIn, background_tasks: BackgroundTasks) -> str:
    print(data.dict())
    try:
        address = IPv4Address(data.host)
    except AddressValueError:
        raise HTTPException(status_code=400, detail='Address is not a valid IPv4 address')

    if address not in IPv4Network(config.subnet):  # noqa
        raise HTTPException(status_code=403, detail='Target device address is not in this agent\'s subnet')

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'http{"" if config.insecure else "s"}://{config.server_hostname}/api/account/',  # noqa
            headers={'Authorization': f'Bearer {data.user_access_token}'},
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=401, detail='Access token is invalid or expired')

            user = PyUser(**await response.json())

            host_credentials = await HostCredentials.get_or_none(
                owner_id=user.pk,
                host=data.host,
                port=data.port,
            )

            if host_credentials is None:
                await HostCredentials.create(owner_id=user.pk, host=data.host, port=data.port)
                raise HTTPException(status_code=401, detail='No credentials provided')

            if (
                (data.auth_method == AuthMethodEnum.PASSWORD and (
                    (host_credentials.username is None and data.username_required)
                    or (host_credentials.password is None and data.password_required)
                )) or (data.auth_method == AuthMethodEnum.PUBLIC_KEY and host_credentials.public_key is None)
            ):
                raise HTTPException(status_code=401, detail='No credentials provided')

            if data.auth_method == AuthMethodEnum.PASSWORD.value:
                if data.username_required:
                    host_credentials.username = data.username

                if data.password_required:
                    fernet = Fernet(config.secret.encode())  # noqa
                    host_credentials.password = fernet.encrypt(data.password.encode())
            elif data.auth_method == AuthMethodEnum.PUBLIC_KEY.value:
                host_credentials.public_key = data.public_key.encode()

            session = await TunnelSession.create(
                sid=token_urlsafe(48),
                credentials=host_credentials,
                port=data.port,
                proto=data.proto,
                auth_method=data.auth_method.value,
                username_required=data.username_required,
                password_requireed=data.password_required,
            )
            background_tasks.add_task(delete_tunnel_session, session.sid)
            return session.sid
