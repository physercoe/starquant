#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .order_status import OrderStatus
from ..event.event import *
from .order_event import OrderEvent
from .order_type import OrderType
from .order_flag import OrderFlag

class OrderStatusEvent(Event):
    """
    Order status event
    """
    def __init__(self):
        """
        order status contains order information because of open orders
        upon reconnect, open order event info will be received to recreate an order
        """
        self.event_type = EventType.ORDERSTATUS
        self.server_order_id = -1
        self.client_order_id = -1
        self.broker_order_id = -1
        self.full_symbol = ''
        self.order_size = 0
        self.order_flag = OrderFlag.OPEN
        self.limit_price = 0.0
        self.stop_price = 0.0
        self.fill_size = 0
        self.fill_price = 0.0
        self.create_time = ''
        self.cancel_time = ''
        self.account = ''
        self.source = -1
        self.api = ''
        self.tag = ''
        self.orderNo = ''
        self.order_status = OrderStatus.UNKNOWN
        self.timestamp = ''
        self.price = 0.0
        self.order_type = OrderType.MKT

    def deserialize(self, msg):
        v = msg.split('|')
        self.server_order_id = int(v[1])
        self.client_order_id = int(v[2])
        self.broker_order_id = int(v[3])
        self.full_symbol = v[4]
        self.order_size = int(v[5])
        self.order_flag = OrderFlag((int(v[6])))
        self.order_type = OrderType(int(v[7]))
        self.price = float(v[8])
        self.fill_size = int(v[9])
        self.fill_price = float(v[10])
        self.create_time = v[11]
        self.cancel_time = v[12]
        self.account = v[13]
        self.source = int(v[14])
        self.api = v[15]
        self.tag = v[16]
        self.orderNo = v[17]
        self.order_status = OrderStatus(int(v[18]))
        self.timestamp = v[19]

    def to_order(self):
        o = OrderEvent()
        o.server_order_id = self.server_order_id
        o.client_order_id = self.client_order_id
        o.broker_order_id = self.broker_order_id
        o.full_symbol = self.full_symbol
        o.order_type = self.order_type
        o.order_flag = self.order_flag
        o.order_status = self.order_status
        if (self.order_type == OrderType.LMT):
            o.limit_price = self.price
        elif (self.order_type == OrderType.STPLMT):
            o.stop_price = self.price
        o.order_size = self.order_size
        o.fill_price = self.fill_price
        o.fill_size = self.fill_size
        o.create_time = self.create_time
        o.fill_time = ''
        o.cancel_time = self.cancel_time
        o.account =  self.account
        o.source = self.source  # sid
        o.api = self.api
        o.tag = self.tag
        o.orderNo = self.orderNo

        return o