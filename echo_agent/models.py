from enum import Enum
from ipaddress import IPv4Address
from typing import Optional

from pydantic import BaseModel
from tortoise import Model, fields


class AuthMethodEnum(Enum):
    PASSWORD = 'password'
    PUBLIC_KEY = 'pubkey'


class HostCredentials(Model):
    owner_id = fields.IntField()
    host = fields.CharField(max_length=64)
    port = fields.IntField()
    username = fields.CharField(max_length=64, null=True)
    password = fields.BinaryField(null=True)
    public_key = fields.BinaryField(null=True)

    class Meta:
        unique_together = (('owner_id', 'host', 'port'),)


class TunnelSession(Model):
    sid = fields.CharField(max_length=64, unique=True)
    credentials = fields.ForeignKeyField('models.HostCredentials', on_delete=fields.CASCADE)
    port = fields.IntField()
    proto = fields.CharField(max_length=6)
    auth_method = fields.CharEnumField(AuthMethodEnum)
    username_required = fields.BooleanField()
    password_required = fields.BooleanField()


class PyHostCredentials(BaseModel):
    owner_id: int
    host: IPv4Address
    port: int
    username: str
    password: bytes
    public_key: bytes

    class Config:
        orm_mode = True


class PyTunnelSession(BaseModel):
    sid: str
    credentials: PyHostCredentials
    port: int
    proto: str
    auth_method: AuthMethodEnum
    username_required: bool
    password_required: bool

    class Config:
        orm_mode = True
        use_enum_values = True


class PyTunnelSessionCreateIn(BaseModel):
    user_access_token: str
    host: str
    port: int
    proto: str
    auth_method: AuthMethodEnum
    username: Optional[str]
    password: Optional[str]
    public_key: Optional[str]
    username_required: bool
    password_required: bool

    class Config:
        use_enum_values = True


class PyUser(BaseModel):
    pk: int
    username: str
    first_name: str
    last_name: str
