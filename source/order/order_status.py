#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

class OrderStatus(Enum):
    UNKNOWN = 0
    NEWBORN = 1              # in use
    PENDING_SUBMIT = 2
    SUBMITTED = 3           # in use
    ACKNOWLEDGED = 4
    QUEUED = 5        # in use
    PARTIALLY_FILLED = 6
    FILLED = 7              # in use
    PENDING_CANCEL = 8
    PENDING_MODIFY = 9
    CANCELED = 10
    LEFTDELETE =11
    SUSPENDED =12
    API_PENDING = 13
    API_CANCELLED = 14
    FAIL = 15
    DELETED = 16
    EFFECT = 17
    APPLY = 18
    ERROR = 19
    TRIG = 20
    EXCTRIG = 21

