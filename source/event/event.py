#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
from enum import Enum


class MSG_TYPE(Enum):
    MSG_TYPE_TICK_L1 = 1000
    MSG_TYPE_TICK_L5 = 1001
    MSG_TYPE_TICK_L10 = 1002
    MSG_TYPE_TICK_L20 = 1003
    MSG_TYPE_BAR_1MIN = 1011
    MSG_TYPE_BAR_5MIN = 1012
    MSG_TYPE_BAR_15MIN = 1013
    MSG_TYPE_BAR_1HOUR = 1014
    MSG_TYPE_BAR_1DAY = 1015
    MSG_TYPE_BAR_1WEEK = 1016
    MSG_TYPE_BAR_1MON = 1017	
    MSG_TYPE_Trade =1060
    MSG_TYPE_Bid = 1061
    MSG_TYPE_Ask = 1062
    MSG_TYPE_Full = 1063
    MSG_TYPE_BidPrice = 1064
    MSG_TYPE_BidSize = 1065
    MSG_TYPE_AskPrice = 1066
    MSG_TYPE_AskSize = 1067
    MSG_TYPE_TradePrice = 1068
    MSG_TYPE_TradeSize = 1069
    MSG_TYPE_OpenPrice = 1070
    MSG_TYPE_HighPrice = 1071
    MSG_TYPE_LowPrice = 1072
    MSG_TYPE_ClosePrice = 1073
    MSG_TYPE_Volume = 1074
    MSG_TYPE_OpenInterest = 1075
    MSG_TYPE_Hist =1076
# 	11* sys control
    MSG_TYPE_ENGINE_STATUS = 1101
    MSG_TYPE_ENGINE_START = 1111
    MSG_TYPE_ENGINE_STOP = 1112
    MSG_TYPE_ENGINE_CONNECT = 1120
    MSG_TYPE_ENGINE_DISCONNECT = 1121
    MSG_TYPE_SWITCH_TRADING_DAY = 1141
#  12* strategy
    MSG_TYPE_STRATEGY_START = 1210
    MSG_TYPE_STRATEGY_END = 1211
#  13*  tast
    MSG_TYPE_TIMER = 1301 
    MSG_TYPE_TASK_START = 1310
    MSG_TYPE_TASK_STOP = 1311
#  20* engine action
    # request
    MSG_TYPE_SUBSCRIBE_MARKET_DATA = 2001
    MSG_TYPE_SUBSCRIBE_L2_MD = 2002
    MSG_TYPE_SUBSCRIBE_INDEX = 2003
    MSG_TYPE_SUBSCRIBE_ORDER_TRADE = 2004
    MSG_TYPE_UNSUBSCRIBE = 2011
    MSG_TYPE_QRY_COMMODITY = 2021	
    MSG_TYPE_QRY_CONTRACT   = 2022
    MSG_TYPE_QRY_POS       = 2023
    MSG_TYPE_QRY_ACCOUNT   = 2024
    MSG_TYPE_ORDER         = 2031  #insert order
    MSG_TYPE_ORDER_ACTION  = 2032  #cancel order
    MSG_TYPE_CANCEL_ORDER = 2033
    MSG_TYPE_CANCEL_ALL = 2039
    #call back
    MSG_TYPE_RSP_POS       = 2051
    MSG_TYPE_RTN_ORDER     = 2052 #order status
    MSG_TYPE_RTN_TRADE     = 2053
    MSG_TYPE_RSP_ACCOUNT   = 2054
    MSG_TYPE_RSP_CONTRACT   = 2055
#	31*: info class msg mainly about sys
    MSG_TYPE_INFO   = 3100
    MSG_TYPE_INFO_ENGINE_MDCONNECTED = 3101
    MSG_TYPE_INFO_ENGINE_MDDISCONNECTED = 3102
    MSG_TYPE_INFO_ENGINE_TDCONNECTED = 3103
    MSG_TYPE_INFO_ENGINE_TDDISCONNECTED = 3104
    MSG_TYPE_INFO_HEARTBEAT_WARNING =3105
#	34*:error class msg
    MSG_TYPE_ERROR = 3400
    MSG_TYPE_ERROR_ENGINENOTCONNECTED = 3401
    MSG_TYPE_ERROR_SUBSCRIBE = 3402
    MSG_TYPE_ERROR_INSERTORDER = 3403
    MSG_TYPE_ERROR_CANCELORDER = 3404
    MSG_TYPE_ERROR_ORGANORDER = 3405 #order is not tracted by order manager
    MSG_TYPE_ERROR_QRY_ACC = 3406
    MSG_TYPE_ERROR_QRY_POS = 3407
    MSG_TYPE_ERROR_QRY_CONTRACT = 3408
    MSG_TYPE_ERROR_CONNECT = 3409  #login fail
    MSG_TYPE_ERROR_DISCONNECT = 3410
#  40*: test class msg
    MSG_TYPE_TEST = 4000



class EventType(Enum):
    TICK = 1000
    BAR = 1011
    HISTORICAL = 1076
    GENERAL_REQ = 1100
    ENGINE_CONNECT = 1120
    ENGINE_DISCONNECT = 1121
    TIMER = 1301
    SUBSCRIBE = 2001
    UNSUBSCIRBE = 2011
    QRY_CONTRACT = 2022
    QRY_POS = 2023
    QRY_ACCOUNT = 2024
    ORDER = 2031
    CANCEL = 2033
    ORDERSTATUS = 2052
    FILL = 2053
    ACCOUNT = 2054
    POSITION = 2051
    CONTRACT = 2055
    INFO = 3100
    ERROR = 3400


















class Event(object):
    """
    Base Event class for event-driven system
    """
    @property
    def typename(self):
        return self.type.name

class InfoEvent(Event):
    """
    General event: TODO seperate ErrorEvent
    """
    def __init__(self):
        self.event_type = EventType.INFO
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

class QryAccEvent(Event):
    """
    qry acc
    """
    def __init__(self):
        self.event_type = EventType.QRY_ACCOUNT
        self.source = 0
        self.api = ""
    def serialize(self):
        msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_QRY_ACCOUNT.value)
        return msg

class QryPosEvent(Event):
    """
    qry pos
    """
    def __init__(self):
        self.event_type = EventType.QRY_POS
        self.source = 0
        self.api = ""
    def serialize(self):
        msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_QRY_POS.value)
        return msg

class SubscribeEvent(Event):
    """
    qry acc
    """
    def __init__(self):
        self.event_type = EventType.SUBSCRIBE
        self.source = 0
        self.api = ""
        self.content = ""
    def serialize(self):
        msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_SUBSCRIBE_MARKET_DATA.value) + '|' + self.content
        return msg

