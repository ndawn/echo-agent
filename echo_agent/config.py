import os.path

import ujson


# DYNAMIC PARAMS:
# subnet
# token
# server_hostname
# agent_port
# db_url
# ports


DYNAMIC_CONFIG_FILE_PATH = 'config.json'


class Config:
    __instance: "Config" = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)

        return cls.__instance

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), DYNAMIC_CONFIG_FILE_PATH)) as dynamic:
            self.__dict__.update(ujson.load(dynamic))
