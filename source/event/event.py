#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
from enum import Enum


class MSG_TYPE(Enum):
    PYTHON_OBJ = 0
# 10 - 19 strategy
    MSG_TYPE_STRATEGY_START = 10
    MSG_TYPE_STRATEGY_END = 11
    MSG_TYPE_TRADE_ENGINE_LOGIN = 12
    MSG_TYPE_TRADE_ENGINE_ACK = 13 # 
    MSG_TYPE_STRATEGY_POS_SET = 14 # 
# 20 - 29 service
    MSG_TYPE_PAGED_START = 20
    MSG_TYPE_PAGED_END = 21
# 30 - 39 control
    MSG_TYPE_TRADE_ENGINE_OPEN = 30
    MSG_TYPE_TRADE_ENGINE_CLOSE = 31
    MSG_TYPE_MD_ENGINE_OPEN = 32
    MSG_TYPE_MD_ENGINE_CLOSE = 33
    MSG_TYPE_SWITCH_TRADING_DAY = 34
    MSG_TYPE_STRING_COMMAND = 35
# 50 - 89 utilities
    MSG_TYPE_TIME_TICK = 50
    MSG_TYPE_SUBSCRIBE_MARKET_DATA = 51
    MSG_TYPE_SUBSCRIBE_L2_MD = 52
    MSG_TYPE_SUBSCRIBE_INDEX = 53
    MSG_TYPE_SUBSCRIBE_ORDER_TRADE = 54
    MSG_TYPE_UNSUBSCRIBE = 55
    MSG_TYPE_ENGINE_STATUS = 60
# 90 - 99 memory alert
    MSG_TYPE_MEMORY_FROZEN = 90 # UNLESS SOME MEMORY UNLOCK NO MORE LOCKING		
#  100-199 market MSG
    MSG_TYPE_TICK_L1 = 100
    MSG_TYPE_TICK_L5 = 101
    MSG_TYPE_TICK_L10 = 102
    MSG_TYPE_TICK_L20 = 103
    MSG_TYPE_BAR_1MIN = 111
    MSG_TYPE_BAR_5MIN = 112
    MSG_TYPE_BAR_15MIN = 113
    MSG_TYPE_BAR_1HOUR = 114
    MSG_TYPE_BAR_1DAY = 115
    MSG_TYPE_BAR_1WEEK = 116
    MSG_TYPE_BAR_1MON = 117
    MSG_TYPE_Trade =160
    MSG_TYPE_Bid = 161
    MSG_TYPE_Ask = 162
    MSG_TYPE_Full = 163
    MSG_TYPE_BidPrice = 164
    MSG_TYPE_BidSize = 165
    MSG_TYPE_AskPrice = 166
    MSG_TYPE_AskSize = 167
    MSG_TYPE_TradePrice = 168
    MSG_TYPE_TradeSize = 169
    MSG_TYPE_OpenPrice = 170
    MSG_TYPE_HighPrice = 171
    MSG_TYPE_LowPrice = 172
    MSG_TYPE_ClosePrice = 173
    MSG_TYPE_Volume = 174
    MSG_TYPE_OpenInterest = 175
    MSG_TYPE_Hist =176
#  200-299 broker msg	
    MSG_TYPE_QRY_POS       = 201
    MSG_TYPE_RSP_POS       = 202
    MSG_TYPE_ORDER         = 204
    MSG_TYPE_RTN_ORDER     = 205
    MSG_TYPE_RTN_TRADE     = 206
    MSG_TYPE_ORDER_ACTION  = 207
    MSG_TYPE_QRY_ACCOUNT   = 208
    MSG_TYPE_RSP_ACCOUNT   = 209
    MSG_TYPE_QRY_CONTRACT   = 210
    MSG_TYPE_RSP_CONTRACT   = 211
    MSG_TYPE_CANCEL_ORDER = 212
    MSG_TYPE_CANCEL_ALL = 213			
#	300-399 general ,log etc msg
    MSG_TYPE_INFO   = 300
    MSG_TPPE_ERROR = 301
    MSG_TYPE_WARNING = 302
    MSG_TYPE_NOTIFY = 303
#  400-499 test msg
    MSG_TYPE_TEST = 400



class EventType(Enum):
    TICK = 100
    BAR = 111
    ORDER = 204
    FILL = 206
    CANCEL = 212
    ORDERSTATUS = 205
    ACCOUNT = 209
    POSITION = 202
    CONTRACT = 211
    HISTORICAL = 176
    TIMER = 303
    GENERAL = 300
    # request and qry event
    TRADE_ENGINE_OPEN = 30
    TRADE_ENGINE_CLOSE = 31
    MD_ENGINE_OPEN = 32
    MD_ENGINE_CLOSE = 33
    SUBSCRIBE = 51
    UNSUBSCIRBE = 55
    QRY_ACCOUNT = 208
    QRY_POS = 201
    QRY_CONTRACT = 210
    GENERAL_REQ = 500
















class Event(object):
    """
    Base Event class for event-driven system
    """
    @property
    def typename(self):
        return self.type.name

class GeneralEvent(Event):
    """
    General event: TODO seperate ErrorEvent
    """
    def __init__(self):
        self.event_type = EventType.GENERAL
        self.timestamp = ""
        self.content = ""

    def deserialize(self, msg):
        v = msg.split('|')
        self.content = msg
        self.timestamp = v[-1]


class GeneralReqEvent(Event):
    """
    General req event: 
    """
    def __init__(self):
        self.event_type = EventType.GENERAL_REQ
        self.timestamp = ""
        self.req = ""

    def serialize(self):
        return self.req