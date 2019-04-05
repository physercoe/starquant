#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
from ..event.event import *
from ..position.position import Position
from .order_flag import OrderFlag
from ..util.util_func import retrieve_multiplier_from_full_symbol

class FillEvent(Event):
    """
    Fill event, with filled quantity/size and price
    """
    def __init__(self):
        """
        Initialises fill
        """
        self.event_type = EventType.FILL
        self.server_order_id = -1
        self.client_order_id = -1
        self.broker_order_id = -1
        self.orderNo = ''
        self.broker_fill_id = ''
        self.full_symbol = ''
        self.fill_time = ''
        self.fill_price = 0.0
        self.fill_size = 0     # size < 0 means short order is filled
        self.fill_flag = OrderFlag.OPEN
        self.fill_pnl = 0.0
        self.exchange = ''
        self.commission = 0.0
        self.account = ''
        self.source = -1
        self.api = 'none'

    def to_position(self):
        """
        if there is no existing position for this symbol, this fill will create a new position
        (otherwise it will be adjusted to exisitng position)
        """
        if self.fill_size > 0:
            average_price_including_commission = self.fill_price + self.commission \
                                                                     / retrieve_multiplier_from_full_symbol(self.full_symbol)
        else:
            average_price_including_commission = self.fill_price - self.commission \
                                                                     / retrieve_multiplier_from_full_symbol(self.full_symbol)

        new_position = Position(self.full_symbol, average_price_including_commission, self.fill_size)
        return new_position

    def deserialize(self, msg):
        v = msg.split('|')
        self.server_order_id = int(v[3])
        self.client_order_id = int(v[4])
        self.broker_order_id = int(v[5])
        self.orderNo = v[6]
        self.broker_fill_id = v[7]
        self.fill_time = v[8]
        self.full_symbol = v[9]
        self.fill_price = float(v[10])
        self.fill_size = int(v[11])
        self.fill_flag = OrderFlag(int(v[12]))
        self.commission = float(v[13])
        self.account = v[14]
        self.api = v[15]
        self.source = int(v[16])