#!/usr/bin/env python
# -*- coding: utf-8 -*-


def retrieve_multiplier_from_full_symbol(full_symbol):
    return 1.0
def marginrate(full_symbol):
    return 0.1


from logging import CRITICAL

from .utility import load_json

SETTINGS = {
    "font.family": "Arial",
    "font.size": 12,

    "log.active": True,
    "log.level": CRITICAL,
    "log.console": True,
    "log.file": True,

    "email.server": "smtp.qq.com",
    "email.port": 465,
    "email.username": "",
    "email.password": "",
    "email.sender": "",
    "email.receiver": "",

    "rqdata.username": "",
    "rqdata.password": "",

    "database.driver": "mongodb",  # see database.Driver
    "database.database": "findata",  # for sqlite, use this as filepath
    "database.host": "localhost",
    "database.port": 27017,
    "database.user": "",
    "database.password": "",
    "database.authentication_source": "",  # for mongodb
}

# Load global setting from json file.
SETTING_FILENAME = "sq_setting.json"
SETTINGS.update(load_json(SETTING_FILENAME))


def get_settings(prefix: str = ""):
    prefix_length = len(prefix)
    return {k[prefix_length:]: v for k, v in SETTINGS.items() if k.startswith(prefix)}
