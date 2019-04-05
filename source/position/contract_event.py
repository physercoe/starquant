#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..event.event import *

class ContractEvent(Event):
    """
    also serve as contract
    """
    def __init__(self):
        self.event_type = EventType.CONTRACT
        self.full_symbol = ''
        self.local_name = ''
        self.mininum_tick = 0.0
        self.mulitples = 1

    def deserialize(self, msg):
        v = msg.split('|')
        self.local_name = v[3]
        self.mininum_tick = float(v[4])
        self.mulitples = int(v[5])