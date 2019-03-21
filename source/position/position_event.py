#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..event.event import *
from .position import Position

class PositionEvent(Event):
    """
    position event
    """
    def __init__(self):
        """
        Initialises order
        """
        self.event_type = EventType.POSITION
        self.full_symbol = ''
        self.average_cost = 0.0
        self.size = 0
        self.pre_size = 0
        self.freezed_size = 0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.account = ''
        self.type = ''
        self.posno =''
        self.openorderNo = ''
        self.openapi = ''
        self.opensource = -1
        self.closeorderNo = ''
        self.closeapi = ''
        self.closesource = -1
        self.timestamp = ''


    def deserialize(self, msg):
        v = msg.split('|')
        self.type =v[1]     
        self.account = v[2]
        self.posno = v[3]
        self.openorderNo = v[4]
        self.openapi = v[5]
        self.opensource = int(v[6])
        self.closeorderNo = v[7]
        self.closeapi = v[8]
        self.closesource = int(v[9])        
        self.full_symbol = v[10]
        self.average_cost = float(v[11])
        self.size = int(v[12])
        self.pre_size = int(v[13])
        self.freezed_size = int(v[14])
        self.realized_pnl = float(v[15])
        self.unrealized_pnl = float(v[16])
        self.timestamp = v[17]

    def to_position(self):

        pos = Position(self.full_symbol, self.average_cost, 0)
        pos.account = self.account
        pos.posno =self.posno
        pos.openorderNo = self.openorderNo
        pos.openapi = self.openapi
        pos.opensource = self.opensource
        pos.closeorderNo = self.closeorderNo
        pos.closeapi = self.closeapi
        pos.closesource = self.closesource
        if self.size >= 0:
            pos.buy_quantity = self.size
        else:
            pos.sell_quantity = -1* self.size
        pos.size = pos.buy_quantity + pos.sell_quantity
        pos.realized_pnl = self.realized_pnl
        pos.unrealized_pnl = self.unrealized_pnl

        return pos
