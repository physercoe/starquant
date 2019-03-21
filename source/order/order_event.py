#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .order_status import OrderStatus
from .order_flag import OrderFlag
from .order_type import OrderType
from ..event.event import *

class OrderEvent(Event):
    """
    Order event
    """
    
    def __init__(self):
        """
        Initialises order
        """
        self.event_type = EventType.ORDER
        self.server_order_id = -1
        self.client_order_id = -1
        self.broker_order_id = -1
        self.full_symbol =  ''
        self.order_type = OrderType.MKT
        self.order_flag = OrderFlag.OPEN
        self.order_status = OrderStatus.UNKNOWN
        self.limit_price = 0.0
        self.stop_price = 0.0
        self.order_size = 0         # short < 0, long > 0
        self.fill_price = 0.0
        self.fill_size = 0
        self.create_time = None
        self.fill_time = None
        self.cancel_time = None
        self.account = ''
        self.source = -1              # sid
        self.api = ''
        self.orderNo = ''        # used in tap 委托编码，服务器端唯一识别标志
        self.tag = ''             #用于其他区分标志

    def serialize(self):
        msg = ''
        if self.order_type == OrderType.MKT:
            msg = 'o' + '|' + str(self.account) + '|'+ str(self.source) + '|' + str(self.client_order_id) + '|' \
                  + str(OrderType.MKT.value) + '|' + self.full_symbol + '|' + str(self.order_size) + '|' + '0.0' +'|' \
                  + str(self.order_flag.value)  + '|' + self.tag
        elif self.order_type == OrderType.LMT:
            msg = 'o' + '|' + str(self.account) + '|' + str(self.source) + '|' + str(self.client_order_id) + '|' \
                  + str(OrderType.LMT.value)+ '|' + self.full_symbol + '|' + str(self.order_size) + '|' + str(self.limit_price) + '|' \
                  + str(self.order_flag.value) + '|' + self.tag
        elif self.order_type == OrderType.STP:
            msg = 'o' + '|' + str(self.account) + '|'+ str(self.source) + '|' + str(self.client_order_id) + '|' \
                  + str(OrderType.STP.value) + '|' + self.full_symbol + '|' + str(self.order_size) + '|' + '0.0' +'|' \
                  + str(self.order_flag.value)     + '|' + self.tag          
        elif self.order_type == OrderType.STPLMT:
            msg = 'o' + '|' + str(self.account) + '|' + str(self.source) + '|' + str(self.client_order_id) + '|' \
                  + str(OrderType.STPLMT.value)+ '|' + self.full_symbol + '|' + str(self.order_size) + '|' + str(self.stop_price) + '|' \
                  + str(self.order_flag.value) + '|' + self.tag
        else:
            print("unknown order type")            
        return msg