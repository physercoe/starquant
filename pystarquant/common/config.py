#!/usr/bin/env python
# -*- coding: utf-8 -*-

from logging import CRITICAL
from pystarquant.common.utility import load_json

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

    "rqdata.username": "license",
    "rqdata.password": "RBLLJoAVKFjKQrK-MM4r75qvjX8wwH6fRtIi0hDABn5QTIJv1XBnML_X_-fnu9yZSGNSW-3YSoUT8LfPwD_zlf2aCNX7O8FRBHYdRsccBjTUz6hx9NIVsMC_eVBERQOhLxUz5d9jiDMjqJIuIttwLIXItSc97kAfYJVzAswA_sY=BaJrVG9_65BoZReydODhmsH3YzZmYcseFOb55ncPhLWF5o-5eh21urBtTAGY_Q9WBUMzy995gnqplTToA24TkQbMuOx8PSDKJnMBSPrUkHCT5PlRKV7HMwltXM5CC1L-VrJ0LdOyBVGo8Iac-wsaj_qXrdtv83wUj8ySHinI4SU=",

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
