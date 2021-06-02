from typing import Optional

from pydantic import BaseModel
from tortoise import Model, fields


class TunnelSession(Model):
    sid = fields.CharField(max_length=64, unique=True)
    host = fields.CharField(max_length=64)
    port = fields.IntField()
    proto = fields.CharField(max_length=6)
    username = fields.CharField(max_length=64, null=True)
    password = fields.CharField(max_length=64, null=True)


class PyTunnelSession(BaseModel):
    host: str
    port: int
    proto: str
    username: Optional[str]
    password: Optional[str]

    class Config:
        orm_mode = True
