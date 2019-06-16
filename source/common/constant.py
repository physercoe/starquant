#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum
from ..api.ctp_constant import THOST_FTDC_D_Buy,THOST_FTDC_D_Sell,THOST_FTDC_PD_Long,THOST_FTDC_PD_Short,THOST_FTDC_PD_Net


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
  #10* data
    MSG_TYPE_TICK = 1000
    MSG_TYPE_TICK_L1 = 1001
    MSG_TYPE_TICK_L5 = 1002
    MSG_TYPE_TICK_L10 = 1003
    MSG_TYPE_TICK_L20 = 1004
    MSG_TYPE_BAR = 1010
    MSG_TYPE_BAR_1MIN = 1011
    MSG_TYPE_BAR_5MIN = 1012
    MSG_TYPE_BAR_15MIN = 1013
    MSG_TYPE_BAR_1HOUR = 1014
    MSG_TYPE_BAR_1DAY = 1015
    MSG_TYPE_BAR_1WEEK = 1016
    MSG_TYPE_BAR_1MON = 1017
    MSG_TYPE_STOCK_TICK = 1020
    MSG_TYPE_STOCK_BAR = 1021
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
  # 11* sys control
    MSG_TYPE_ENGINE_STATUS = 1101
    MSG_TYPE_ENGINE_START = 1111
    MSG_TYPE_ENGINE_STOP = 1112
    MSG_TYPE_ENGINE_RESET = 1113
    MSG_TYPE_ENGINE_CONNECT = 1120
    MSG_TYPE_ENGINE_DISCONNECT = 1121
    MSG_TYPE_SWITCH_TRADING_DAY = 1141
  # 12* strategy
    MSG_TYPE_STRATEGY_STATUS = 1200
    MSG_TYPE_STRATEGY_ADD = 1210
    MSG_TYPE_STRATEGY_INIT = 1211
    MSG_TYPE_STRATEGY_INIT_ALL = 1212
    MSG_TYPE_STRATEGY_START = 1213
    MSG_TYPE_STRATEGY_START_ALL = 1214    
    MSG_TYPE_STRATEGY_STOP = 1215
    MSG_TYPE_STRATEGY_STOP_ALL = 1216
    MSG_TYPE_STRATEGY_RESET = 1217
    MSG_TYPE_STRATEGY_RESET_ALL = 1218
    MSG_TYPE_STRATEGY_RELOAD = 1219    
    MSG_TYPE_STRATEGY_EDIT = 1220
    MSG_TYPE_STRATEGY_REMOVE = 1221
    MSG_TYPE_STRATEGY_REMOVE_DUPLICATE = 1222
    MSG_TYPE_STRATEGY_RTN_REMOVE = 1223
    MSG_TYPE_STRATEGY_GET_DATA = 1230
    MSG_TYPE_STRATEGY_RTN_DATA = 1231
    MSG_TYPE_STRATEGY_GET_CLASS_NAME = 1232
    MSG_TYPE_STRATEGY_RTN_CLASS_NAME = 1233
    MSG_TYPE_STRATEGY_GET_CLASS_PARAMETERS = 1234
    MSG_TYPE_STRATEGY_RTN_CLASS_PARAMETERS = 1235
    MSG_TYPE_STRATEGY_GET_PARAMETERS = 1234
    MSG_TYPE_STRATEGY_RTN_PARAMETERS = 1235    
  #  13*  task
    MSG_TYPE_TIMER = 1301 
    MSG_TYPE_TASK_START = 1310
    MSG_TYPE_TASK_STOP = 1311
  #  14*  recorder
    MSG_TYPE_RECORDER_STATUS = 1400
    MSG_TYPE_RECORDER_START = 1401 
    MSG_TYPE_RECORDER_STOP = 1402
    MSG_TYPE_RECORDER_RESET = 1403
    MSG_TYPE_RECORDER_RELOAD = 1404
    MSG_TYPE_RECORDER_GET_DATA = 1405
    MSG_TYPE_RECORDER_RTN_DATA = 1406
    MSG_TYPE_RECORDER_ADD_TICK = 1410
    MSG_TYPE_RECORDER_ADD_BAR = 1420
    MSG_TYPE_RECORDER_REMOVE_TICK = 1430
    MSG_TYPE_RECORDER_REMOVE_BAR = 1440
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
    MSG_TYPE_QRY_ORDER   = 2025
    MSG_TYPE_QRY_TRADE   = 2026
    MSG_TYPE_QRY_POSDETAIL   = 2027
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
    ENGINE_CONTROL = 1100
    STRATEGY_CONTROL = 1200
    TIMER = 1301
    RECORDER_CONTROL = 1400
    GENERAL_REQ = 2000
    SUBSCRIBE = 2001
    UNSUBSCIRBE = 2011
    QRY = 2020
    ORDER = 2031
    CANCEL = 2033
    ORDERSTATUS = 2052
    FILL = 2053
    ACCOUNT = 2054
    POSITION = 2051
    CONTRACT = 2055
    INFO = 3100
    ERROR = 3400
    BACKTEST_START = 9000
    BACKTEST_FINISH = 9001
    OPTIMIZATION_START = 9002
    OPTIMIZATION_FINISH = 9003
    BACKTEST_LOG = 9010

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
    LPT = 25    #local price condition touched 

OT2STR = {
    OrderType.MKT:'市价',
    OrderType.LMT:'限价',
    OrderType.STP:'市价止损',
    OrderType.STPLMT:'限价止损',
    OrderType.FAK:'FAK',
    OrderType.FOK:'FOK',
    OrderType.LPT:'本地条件单',
    OrderType.DEFAULT:'未知'
}
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

DIRECTION_VT2CTP = {
    Direction.LONG: THOST_FTDC_D_Buy, 
    Direction.SHORT: THOST_FTDC_D_Sell,
    Direction.NET: THOST_FTDC_PD_Net
}
DIRECTION_CTP2VT = {v: k for k, v in DIRECTION_VT2CTP.items()}
DIRECTION_CTP2VT[THOST_FTDC_PD_Long] = Direction.LONG
DIRECTION_CTP2VT[THOST_FTDC_PD_Short] = Direction.SHORT


class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"

ORDERFALG_2VT = {
    OrderFlag.OPEN:Offset.OPEN, 
    OrderFlag.CLOSE:Offset.CLOSE,
    OrderFlag.CLOSE_TODAY:Offset.CLOSETODAY,
    OrderFlag.CLOSE_YESTERDAY:Offset.CLOSEYESTERDAY,
}
OFFSET_VT2ORDERFLAG = {v: k for k, v in ORDERFALG_2VT.items()}

class OptionType(Enum):
    """
    Option type.
    """
    CALL = "看涨期权"
    PUT = "看跌期权"

OPTIONTYPE_CTP2VT = {
    '1': OptionType.CALL,
    '2': OptionType.PUT
}

class Status(Enum):
    """
    Order status.
    """
    NEWBORN = "等待提交"
    SUBMITTING = "提交中"
    NOTTRADED = "未成交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"
    UNKNOWN = "未知"

ORDERSTATUS_2VT = {
    OrderStatus.SUBMITTED: Status.SUBMITTING,
    OrderStatus.NEWBORN: Status.NEWBORN,
    OrderStatus.UNKNOWN: Status.UNKNOWN,
    OrderStatus.ACKNOWLEDGED: Status.NOTTRADED,
    OrderStatus.PARTIALLY_FILLED: Status.PARTTRADED,
    OrderStatus.FILLED: Status.ALLTRADED,
    OrderStatus.CANCELED: Status.CANCELLED,
    OrderStatus.ERROR: Status.REJECTED
}

ACTIVE_STATUSES = set([Status.NEWBORN,Status.SUBMITTING, Status.NOTTRADED,Status.PARTTRADED,Status.UNKNOWN])
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


PRODUCT_CTP2VT = {
    '1': Product.FUTURES,
    '2': Product.OPTION,
    '3': Product.SPREAD,
    '5': Product.SPOT
}

PRODUCT_VT2SQ = {
    Product.EQUITY : "T",
    Product.FUTURES : "F",
    Product.OPTION : "O",
    Product.INDEX : "Z",
    Product.FOREX : "X",
    Product.SPOT : "P",
    Product.ETF : "e",
    Product.BOND : "B",
    Product.WARRANT : "W",
    Product.SPREAD : "S",
    Product.FUND : "J"
}


class Exchange(Enum):
    """
    Exchange.
    """
    # Chinese
    SHFE = "SHFE"
    CZCE = "CZCE"
    DCE = "DCE"
    CFFEX = "CFFEX"
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


EXCHANGE_CTP2VT = {
    "CFFEX": Exchange.CFFEX,
    "SHFE": Exchange.SHFE,
    "CZCE": Exchange.CZCE,
    "DCE": Exchange.DCE,
    "INE": Exchange.INE
}
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

class StopOrderStatus(Enum):
    WAITING = "等待中"
    CANCELLED = "已撤销"
    TRIGGERED = "已触发"

STOPORDER_PREFIX = "STOP"