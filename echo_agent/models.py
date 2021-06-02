from pydantic import BaseModel
from tortoise import Model, fields


class TunnelSession(Model):
    sid = fields.CharField(max_length=64, unique=True)
    host = fields.CharField(max_length=64)
    port = fields.IntField()
    proto = fields.CharField(max_length=6)
    username = fields.CharField(max_length=64)
    password = fields.CharField(max_length=64)


class PyTunnelSession(BaseModel):
    host: str
    port: int
    proto: str
    username: str
    password: str

    class Config:
        orm_mode = True
