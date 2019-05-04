#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum



# ################        Begin consts  # ################  
class ESTATE(Enum):
    DISCONNECTED = 0         
    CONNECTING =1
    CONNECT_ACK = 2         
    AUTHENTICATING = 3
    AUTHENTICATE_ACK = 4      
    LOGINING = 5
    LOGIN_ACK = 6             
    LOGOUTING = 7
    STOP = 8 

class SYMBOL_TYPE(Enum):
    FULL = 0
    CTP = 1

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
    MSG_TYPE_ENGINE_RESET = 1113
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
    MSG_TYPE_ORDER         = 2030  #insert order
    MSG_TYPE_ORDER_PAPER = 2031
    MSG_TYPE_ORDER_CTP = 2032
    MSG_TYPE_ORDER_CTP_PARKED = 2033
    MSG_TYPE_ORDER_TAP = 2034
    MSG_TYPE_ORDER_XTP = 2035
    MSG_TYPE_ORDER_ACTION  = 2040  #cancel order
    MSG_TYPE_CANCEL_ORDER = 2041
    MSG_TYPE_CANCEL_ALL = 2042
    MSG_TYPE_ORDER_ACTION_CTP = 2043
    MSG_TYPE_ORDER_ACTION_TAP = 2044
    MSG_TYPE_ORDER_ACTION_XTP =2045
    #call back
    MSG_TYPE_RSP_POS       = 2500
    MSG_TYPE_RTN_ORDER     = 2510
    MSG_TYPE_RTN_ORDER_CTP     = 2511 
    MSG_TYPE_RTN_ORDER_TAP     = 2512
    MSG_TYPE_RTN_ORDER_XTP     = 2513
    MSG_TYPE_RTN_TRADE     = 2520
    MSG_TYPE_RTN_TRADE_CTP     = 2521
    MSG_TYPE_RTN_TRADE_TAP     = 2522
    MSG_TYPE_RTN_TRADE_XTP     = 2523
    MSG_TYPE_RSP_ACCOUNT   = 2530
    MSG_TYPE_RSP_CONTRACT   = 2540
    MSG_TYPE_RSP_COMMODITY   = 2541
#	31*: info class msg mainly about sys
    MSG_TYPE_INFO   = 3100
    MSG_TYPE_INFO_ENGINE_MDCONNECTED = 3101
    MSG_TYPE_INFO_ENGINE_MDDISCONNECTED = 3102
    MSG_TYPE_INFO_ENGINE_TDCONNECTED = 3103
    MSG_TYPE_INFO_ENGINE_TDDISCONNECTED = 3104
    MSG_TYPE_INFO_HEARTBEAT_WARNING =3105
    MSG_TYPE_INFO_ENGINE_STATUS = 3106
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
    MSG_TYPE_ERROR_NOACCOUNT = 3411
#  40*: test class msg
    MSG_TYPE_TEST = 4000
    MSG_TYPE_BASE = 9
class EventType(Enum):
    HEADER = 0
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

class OrderFlag(Enum):
    OPEN = 0              # in use
    CLOSE = 1
    CLOSE_TODAY = 2          # in use
    CLOSE_YESTERDAY = 3
    FORCECLOSE =4
    FORCEOFF = 5
    LOCALFORCECLOSE = 6        # in use

class OrderType(Enum):
    MKT = 0
    MKTC = 1    #market on close
    LMT = 2     #limit
    LMTC = 3
    PTM = 4        # peggedtomarket
    STP = 5       
    STPLMT = 6
    TRAIING_STOP = 7
    REL = 8           #relative
    VWAP = 9        # volumeweightedaverageprice
    TSL = 10            #trailingstoplimit
    VLT = 11           #volatility
    NONE = 12
    EMPTY = 13
    DEFAULT = 14
    SCALE = 15        
    MKTT =16           # market if touched
    LMTT =17           # limit if touched
    OPTE = 18         # used in tap opt exec
    OPTA = 19        # opt abandon
    REQQ = 20        #  request quot
    RSPQ = 21       # response quot
    SWAP = 22        # swap
    FAK = 23
    FOK = 24

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

class TickType(Enum):
    # same as msg_type
    Tick_L1 = 1000
    Tick_L5 = 1001
    Tick_L10 =1002
    Tick_L20 = 1003
    Bar_1min = 1011
    Bar_5min = 1012
    Bar_15min = 1013
    Bar_1h = 1014
    Bar_1d = 1015
    Bar_1w = 1016
    Bar_1m = 1017
    Trade = 1060		
    Bid = 1061
    Ask = 1062
    Full = 1063
    BidPrice = 1064
    BidSize = 1065
    AskPrice = 1066
    AskSize = 1067
    Price = 1068
    TradeSize = 1069
    OpenPrice = 1070
    HighPrice = 1071
    LowPrice = 1072
    ClosePrice = 1073
    Volume = 1074
    OpenInterest = 1075
    Bar = 1076

# ############################# vnpy 's data #########################

class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = "多"
    SHORT = "空"
    NET = "净"


class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"

class OptionType(Enum):
    """
    Option type.
    """
    CALL = "看涨期权"
    PUT = "看跌期权"

class Product(Enum):
    """
    Product class.
    """
    EQUITY = "股票"
    FUTURES = "期货"
    OPTION = "期权"
    INDEX = "指数"
    FOREX = "外汇"
    SPOT = "现货"
    ETF = "ETF"
    BOND = "债券"
    WARRANT = "权证"
    SPREAD = "价差"
    FUND = "基金"
class Exchange(Enum):
    """
    Exchange.
    """
    # Chinese
    CFFEX = "CFFEX"
    SHFE = "SHFE"
    CZCE = "CZCE"
    DCE = "DCE"
    INE = "INE"
    SSE = "SSE"
    SZSE = "SZSE"
    SGE = "SGE"

    # Global
    SMART = "SMART"
    NYMEX = "NYMEX"
    GLOBEX = "GLOBEX"
    IDEALPRO = "IDEALPRO"
    CME = "CME"
    ICE = "ICE"
    SEHK = "SEHK"
    HKFE = "HKFE"

    # CryptoCurrency
    BITMEX = "BITMEX"
    OKEX = "OKEX"
    HUOBI = "HUOBI"
    BITFINEX = "BITFINEX"


class Currency(Enum):
    """
    Currency.
    """
    USD = "USD"
    HKD = "HKD"
    CNY = "CNY"

class Interval(Enum):
    """
    Interval of bar data.
    """
    MINUTE = "1m"
    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"
class EngineType(Enum):
    LIVE = "实盘"
    BACKTESTING = "回测"


class BacktestingMode(Enum):
    BAR = 1
    TICK = 2
