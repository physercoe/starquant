#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum
from datetime import date
from collections import defaultdict

import psutil
CPU_NUMS = psutil.cpu_count(logical=False)


from pystarquant.api.ctp_constant import (
    THOST_FTDC_D_Buy,
    THOST_FTDC_D_Sell,
    THOST_FTDC_PD_Long,
    THOST_FTDC_PD_Short,
    THOST_FTDC_PD_Net
)


# ################        Begin consts  # ################
class ESTATE(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
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
    XTP = 2


class MSG_TYPE(Enum):
    # 10* data
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
    MSG_TYPE_STOCK_TickByTickTrade = 1031
    MSG_TYPE_STOCK_TickByTickEntrust = 1032
    MSG_TYPE_Trade = 1060
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
    MSG_TYPE_Hist = 1076
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
    MSG_TYPE_STRATEGY_WATCH = 1201
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
    MSG_TYPE_UNSUBSCRIBE_ORDER_TRADE = 2012
    MSG_TYPE_QRY_COMMODITY = 2021
    MSG_TYPE_QRY_CONTRACT = 2022
    MSG_TYPE_QRY_POS = 2023
    MSG_TYPE_QRY_ACCOUNT = 2024
    MSG_TYPE_QRY_ORDER = 2025
    MSG_TYPE_QRY_TRADE = 2026
    MSG_TYPE_QRY_POSDETAIL = 2027
    MSG_TYPE_ORDER = 2030  # insert order
    MSG_TYPE_ORDER_PAPER = 2031
    MSG_TYPE_ORDER_CTP = 2032
    MSG_TYPE_ORDER_CTP_PARKED = 2033
    MSG_TYPE_ORDER_TAP = 2034
    MSG_TYPE_ORDER_XTP = 2035
    MSG_TYPE_ORDER_ACTION = 2040  # cancel order
    MSG_TYPE_CANCEL_ORDER = 2041
    MSG_TYPE_CANCEL_ALL = 2042
    MSG_TYPE_ORDER_ACTION_CTP = 2043
    MSG_TYPE_ORDER_ACTION_TAP = 2044
    MSG_TYPE_ORDER_ACTION_XTP = 2045
    # call back
    MSG_TYPE_RSP_POS = 2500
    MSG_TYPE_RTN_ORDER = 2510
    MSG_TYPE_RTN_ORDER_CTP = 2511
    MSG_TYPE_RTN_ORDER_TAP = 2512
    MSG_TYPE_RTN_ORDER_XTP = 2513
    MSG_TYPE_RTN_TRADE = 2520
    MSG_TYPE_RTN_TRADE_CTP = 2521
    MSG_TYPE_RTN_TRADE_TAP = 2522
    MSG_TYPE_RTN_TRADE_XTP = 2523
    MSG_TYPE_RSP_ACCOUNT = 2530
    MSG_TYPE_RSP_CONTRACT = 2540
    MSG_TYPE_RSP_COMMODITY = 2541
    #	31*: info class msg mainly about sys
    MSG_TYPE_INFO = 3100
    MSG_TYPE_INFO_ENGINE_MDCONNECTED = 3101
    MSG_TYPE_INFO_ENGINE_MDDISCONNECTED = 3102
    MSG_TYPE_INFO_ENGINE_TDCONNECTED = 3103
    MSG_TYPE_INFO_ENGINE_TDDISCONNECTED = 3104
    MSG_TYPE_INFO_HEARTBEAT_WARNING = 3105
    MSG_TYPE_INFO_ENGINE_STATUS = 3106
  #	34*:error class msg
    MSG_TYPE_ERROR = 3400
    MSG_TYPE_ERROR_ENGINENOTCONNECTED = 3401
    MSG_TYPE_ERROR_SUBSCRIBE = 3402
    MSG_TYPE_ERROR_INSERTORDER = 3403
    MSG_TYPE_ERROR_CANCELORDER = 3404
    MSG_TYPE_ERROR_ORGANORDER = 3405  # order is not tracted by order manager
    MSG_TYPE_ERROR_QRY_ACC = 3406
    MSG_TYPE_ERROR_QRY_POS = 3407
    MSG_TYPE_ERROR_QRY_CONTRACT = 3408
    MSG_TYPE_ERROR_CONNECT = 3409  # login fail
    MSG_TYPE_ERROR_DISCONNECT = 3410
    MSG_TYPE_ERROR_NOACCOUNT = 3411
  #  40*: test class msg
    MSG_TYPE_TEST = 4000
    MSG_TYPE_BASE = 9


class EventType(Enum):
    HEADER = 0
    TICK = 1000
    BAR = 1011
    TBTENTRUST = 1030
    TBTTRADE = 1031
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
    DATALOAD_LOG = 9101
    DATALOAD_STRAT = 9102
    DATALOAD_FINISH = 9103
    DATADOWNLOAD_LOG = 9104
    DATADOWNLOAD_STRAT = 9105
    DATADOWNLOAD_FINISH = 9106
    ANALYSIS_LOG = 9200
    ANALYSIS_STRAT = 9201
    ANALYSIS_FINISH = 9202
    ANALYSIS_CORRLOG = 9203
    ANALYSIS_CORRSTART = 9204
    ANALYSIS_CORRFINISH = 9205
    VECTORBT_LOG = 9400
    VECTORBT_START = 9401
    VECTORBT_FINISH = 9402
    VECTORBT_OPTLOG = 9403
    VECTORBT_OPTSTART = 9404
    VECTORBT_OPTFINISH = 9405
    VECTORBT_ROLLLOG = 9406
    VECTORBT_ROLLSTART = 9407
    VECTORBT_ROLLFINISH = 9408

class OrderFlag(Enum):
    OPEN = 0              # in use
    CLOSE = 1
    CLOSE_TODAY = 2          # in use
    CLOSE_YESTERDAY = 3
    FORCECLOSE = 4
    FORCEOFF = 5
    LOCALFORCECLOSE = 6        # in use


class OrderType(Enum):
    MKT = 0
    MKTC = 1  # market on close
    LMT = 2  # limit
    LMTC = 3
    PTM = 4        # peggedtomarket
    STP = 5
    STPLMT = 6
    TRAIING_STOP = 7
    REL = 8  # relative
    VWAP = 9        # volumeweightedaverageprice
    TSL = 10  # trailingstoplimit
    VLT = 11  # volatility
    NONE = 12
    EMPTY = 13
    DEFAULT = 14
    SCALE = 15
    MKTT = 16           # market if touched
    LMTT = 17           # limit if touched
    OPTE = 18         # used in tap opt exec
    OPTA = 19        # opt abandon
    REQQ = 20  # request quot
    RSPQ = 21       # response quot
    SWAP = 22        # swap
    FAK = 23
    FOK = 24
    LPT = 25  # local price condition touched


OT2STR = {
    OrderType.MKT: '市价',
    OrderType.LMT: '限价',
    OrderType.STP: '市价止损',
    OrderType.STPLMT: '限价止损',
    OrderType.FAK: 'FAK',
    OrderType.FOK: 'FOK',
    OrderType.LPT: '本地条件单',
    OrderType.DEFAULT: '未知'
}

class OrderType_VN(Enum):
    """
    Order type.
    """
    LIMIT = "限价"
    MARKET = "市价"
    STOP = "STOP"
    FAK = "FAK"
    FOK = "FOK"
    RFQ = "询价"

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
    LEFTDELETE = 11
    SUSPENDED = 12
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
    Tick_L10 = 1002
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
    OrderFlag.OPEN: Offset.OPEN,
    OrderFlag.CLOSE: Offset.CLOSE,
    OrderFlag.CLOSE_TODAY: Offset.CLOSETODAY,
    OrderFlag.CLOSE_YESTERDAY: Offset.CLOSEYESTERDAY,
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

ACTIVE_STATUSES = set([Status.NEWBORN, Status.SUBMITTING,
                       Status.NOTTRADED, Status.PARTTRADED, Status.UNKNOWN])


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
    TECH_STOCK = "科创"


PRODUCT_CTP2VT = {
    '1': Product.FUTURES,
    '2': Product.OPTION,
    '3': Product.SPREAD,
    '5': Product.SPOT
}

PRODUCT_VT2SQ = {
    Product.EQUITY: "T",
    Product.FUTURES: "F",
    Product.OPTION: "O",
    Product.INDEX: "Z",
    Product.FOREX: "X",
    Product.SPOT: "P",
    Product.ETF: "e",
    Product.BOND: "B",
    Product.WARRANT: "W",
    Product.SPREAD: "S",
    Product.FUND: "J",
    Product.TECH_STOCK:"t"
}

PRODUCT_SQ2VT = {v: k for k, v in PRODUCT_VT2SQ.items()}

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
    DERIBIT = "DERIBIT"


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



Holidays = [
    date(2010,2,12),date(2010,4,2),date(2010,4,30), date(2010,9,21), date(2010,9,30), date(2010,12,31),
    date(2011,2,1),date(2011,4,1),date(2011,4,29),date(2011,6,3), date(2011,9,9), date(2011,9,30), date(2011,12,30),
    date(2012,1,20),date(2012,3,30),date(2012,4,27), date(2012,6,21), date(2012,9,28), date(2012,12,31),
    date(2013,2,8),date(2013,4,3),date(2013,4,26),date(2013,6,7), date(2013,9,18), date(2013,9,27), date(2013,12,31),
    date(2014,1,30),date(2014,4,4),date(2014,4,30),date(2014,5,30), date(2014,9,5), date(2014,9,30), date(2014,12,31),
    date(2015,2,17),date(2015,4,3),date(2015,4,30), date(2015,6,19),date(2015,9,2),date(2015,9,25), date(2015,9,30), date(2015,12,31),
    date(2016,2,5),date(2016,4,1),date(2016,4,29),date(2016,6,8), date(2016,9,14),date(2016,9,30),date(2016,12,30),
    date(2017,1,26),date(2017,3,31),date(2017,4,28),date(2017,5,26),date(2017,9,29),date(2017,12,29),
    date(2018,2,9),date(2018,4,4), date(2018,9,21), date(2018,9,28), date(2018,12,28),
    date(2019,4,4), date(2019,2,1), date(2019,4,4), date(2019,4,30),date(2019,6,6), date(2019,8,21),date(2019,9,12), date(2019,9,30)    
]


RB_switch_days = [date(2010, 3, 8), date(2010,7,20), date(2010, 10, 13), 
    date(2011, 2, 9), date(2011, 8, 5), date(2011, 11, 2), 
    date(2012, 3, 1), date(2012, 7, 11), date(2012, 10, 22), 
    date(2013, 2, 18), date(2013, 7, 3),  date(2013, 10, 30), 
    date(2014, 3, 4), date(2014, 7, 7), date(2014, 10, 20), 
    date(2015, 3, 11), date(2015, 7, 20),date(2015, 11, 4),
    date(2016, 3, 11), date(2016, 8, 17), date(2016, 11, 25), 
    date(2017, 3, 22), date(2017, 8, 8),date(2017, 11, 9),
    date(2018, 3, 27), date(2018, 8, 17), date(2018, 11, 28), 
    date(2019, 3, 29), date(2019, 8, 21)
]

TA_switch_days = [

    date(2010, 1, 21), date(2010, 3, 26), date(2010, 7, 28), date(2010, 11, 1), 
    date(2011, 3, 24), date(2011, 7, 4), date(2011, 11, 21), 
    date(2012, 3, 14), date(2012, 7, 11), date(2012, 11, 5), 
    date(2013, 2, 21), date(2013, 7, 11), date(2013, 12, 4), 
    date(2014, 3, 13), date(2014, 8, 6), date(2014, 11, 25), 
    date(2015, 3, 30), date(2015, 8, 5),date(2015, 11, 24),
    date(2016, 3, 30), date(2016, 8, 4), date(2016, 11, 17), 
    date(2017, 4, 7), date(2017, 8, 7),date(2017, 11, 22),
    date(2018, 3, 28), date(2018, 8, 6), date(2018, 11, 30), 
    date(2019, 4, 8), date(2019, 8, 14)
]

MA_switch_days = [
    date(2015, 4, 16), date(2015, 7, 27), date(2015, 11, 27), 
    date(2016, 4, 8), date(2016, 8, 9), date(2016, 12, 1), 
    date(2017, 4, 6), date(2017, 8, 4), date(2017, 12, 8), 
    date(2018, 4, 11), date(2018, 8, 8), date(2018, 12, 12), 
    date(2019, 4, 12), date(2019, 8, 15),
]

I_switch_days = [
    date(2013, 10, 18), 
    date(2014, 2, 28), date(2014, 7, 22), date(2014, 10, 22), 
    date(2015, 3, 6), date(2015, 7, 21), date(2015, 11, 23), 
    date(2016, 3, 18), date(2016, 8, 10), date(2016, 11, 25), 
    date(2017, 3, 22), date(2017, 7, 31), date(2017, 11, 22), 
    date(2018, 4, 3), date(2018, 8, 7), date(2018, 11, 29), 
    date(2019, 4, 8), date(2019, 7, 31),
]

CU_switch_days =[
    date(2010, 1, 19), date(2010, 2, 24), date(2010, 3, 26), date(2010, 4, 28), date(2010, 5, 27), date(2010, 6, 29), 
    date(2010, 7, 28), date(2010, 8, 24), date(2010, 10, 8), date(2010, 10, 27), date(2010, 11, 19), date(2010, 12, 31), 
    date(2011, 2, 1), date(2011, 3, 15), date(2011, 4, 25), date(2011, 5, 24), date(2011, 6, 27), date(2011, 7, 22), date(2011, 8, 16), 
    date(2011, 9, 16), date(2011, 10, 19), date(2011, 11, 17), date(2011, 12, 15), date(2012, 1, 17), date(2012, 2, 10), 
    date(2012, 3, 6), date(2012, 4, 5), date(2012, 4, 27), date(2012, 5, 17), date(2012, 6, 20), date(2012, 7, 19), 
    date(2012, 8, 14), date(2012, 9, 17), date(2012, 10, 26), date(2012, 11, 26), date(2012, 12, 25), date(2013, 1, 25), 
    date(2013, 2, 26), date(2013, 3, 18), date(2013, 4, 3), date(2013, 5, 2), date(2013, 6, 6), date(2013, 6, 26), date(2013, 6, 27), 
    date(2013, 7, 8), date(2013, 8, 16), date(2013, 10, 9), date(2013, 11, 18), date(2013, 12, 20), date(2014, 1, 15), date(2014, 2, 20), 
    date(2014, 3, 11), date(2014, 4, 2), date(2014, 5, 14), date(2014, 6, 26), date(2014, 7, 31), date(2014, 9, 1), date(2014, 9, 24), 
    date(2014, 10, 17), date(2014, 11, 26), date(2014, 12, 18), date(2015, 1, 23), date(2015, 2, 25), date(2015, 3, 23), 
    date(2015, 4, 27), date(2015, 5, 26), date(2015, 6, 26), date(2015, 7, 24), date(2015, 8, 27), date(2015, 9, 25),
    date(2015, 10, 29), date(2015, 11, 26), date(2015, 12, 29), date(2016, 1, 29), date(2016, 2, 29), date(2016, 3, 29),
    date(2016, 4, 26), date(2016, 5, 27), date(2016, 6, 28), date(2016, 8, 1), date(2016, 9, 2), date(2016, 9, 28), 
    date(2016, 10, 31), date(2016, 11, 28), date(2016, 12, 28), date(2017, 2, 10), date(2017, 3, 9), date(2017, 4, 12), 
    date(2017, 5, 9), date(2017, 6, 1), date(2017, 7, 3), date(2017, 7, 31), date(2017, 9, 6), date(2017, 9, 29), date(2017, 11, 7),
    date(2017, 12, 5), date(2017, 12, 28), date(2018, 2, 5), date(2018, 3, 1), date(2018, 4, 13), date(2018, 5, 9), date(2018, 6, 6), 
    date(2018, 7, 9), date(2018, 8, 9), date(2018, 9, 5), date(2018, 10, 22), date(2018, 11, 6), date(2018, 11, 30), date(2019, 1, 2),
    date(2019, 2, 15), date(2019, 3, 5), date(2019, 4, 18), date(2019, 5, 10), date(2019, 6, 11), date(2019, 7, 9), date(2019, 8, 9),
    date(2019, 9, 9),
]

ZN_switch_days = [
    date(2010, 1, 19), date(2010, 2, 24), date(2010, 3, 29), date(2010, 5, 5), date(2010, 5, 27), date(2010, 6, 28), 
    date(2010, 7, 26), date(2010, 8, 13), date(2010, 9, 10), date(2010, 10, 21), date(2010, 11, 18), date(2010, 12, 30), 
    date(2011, 2, 10), date(2011, 3, 17), date(2011, 4, 25), date(2011, 5, 25), date(2011, 6, 23), date(2011, 7, 18), 
    date(2011, 8, 15), date(2011, 9, 21), date(2011, 10, 19), date(2011, 11, 18), date(2011, 12, 15), date(2012, 1, 16), 
    date(2012, 2, 14), date(2012, 3, 8), date(2012, 4, 6), date(2012, 5, 8), date(2012, 5, 28), date(2012, 6, 25), 
    date(2012, 7, 23), date(2012, 8, 16), date(2012, 9, 20), date(2012, 11, 5), date(2012, 12, 7), date(2013, 1, 7), 
    date(2013, 1, 29), date(2013, 3, 6), date(2013, 4, 3), date(2013, 5, 2), date(2013, 5, 22), date(2013, 6, 20), 
    date(2013, 6, 26), date(2013, 6, 27), date(2013, 7, 30), date(2013, 8, 20), date(2013, 10, 10), date(2013, 11, 15), 
    date(2013, 12, 17), date(2014, 1, 16), date(2014, 2, 21), date(2014, 3, 19), date(2014, 4, 17), date(2014, 5, 28), 
    date(2014, 6, 20), date(2014, 7, 22), date(2014, 8, 27), date(2014, 9, 23), date(2014, 10, 29), date(2014, 11, 28), 
    date(2014, 12, 25), date(2015, 1, 26), date(2015, 2, 25), date(2015, 3, 24), date(2015, 4, 23), date(2015, 5, 25), 
    date(2015, 6, 25), date(2015, 7, 29), date(2015, 8, 31), date(2015, 9, 25), date(2015, 10, 30), date(2015, 11, 26), 
    date(2015, 12, 30), date(2016, 2, 2), date(2016, 3, 1), date(2016, 3, 29), date(2016, 4, 29), date(2016, 6, 1), 
    date(2016, 6, 29), date(2016, 7, 28), date(2016, 8, 30), date(2016, 10, 10), date(2016, 10, 31), date(2016, 11, 29), 
    date(2016, 12, 28), date(2017, 2, 13), date(2017, 3, 3), date(2017, 4, 7), date(2017, 5, 8), date(2017, 6, 7), 
    date(2017, 7, 6), date(2017, 8, 4), date(2017, 9, 5), date(2017, 10, 10), date(2017, 11, 2), date(2017, 12, 4), 
    date(2018, 1, 4), date(2018, 2, 6), date(2018, 3, 2), date(2018, 4, 3), date(2018, 5, 3), date(2018, 6, 7), date(2018, 7, 10),
    date(2018, 8, 7), date(2018, 9, 11), date(2018, 10, 19), date(2018, 11, 2), date(2018, 11, 30), date(2019, 1, 7), 
    date(2019, 2, 15), date(2019, 3, 7), date(2019, 4, 11), date(2019, 5, 9), date(2019, 6, 12), date(2019, 7, 5), 
    date(2019, 8, 7), date(2019, 9, 6),
]

NI_switch_days = [
    date(2015, 5, 28), date(2015, 8, 14), date(2015, 12, 15), date(2016, 4, 8), date(2016, 8, 1), 
    date(2016, 11, 25), date(2017, 3, 31), date(2017, 8, 3), date(2017, 11, 13), date(2018, 3, 29), date(2018, 6, 4),
    date(2018, 8, 6), date(2018, 10, 11), date(2018, 12, 6), date(2019, 4, 9), date(2019, 5, 7), date(2019, 6, 10), 
    date(2019, 7, 8), date(2019, 7, 17), date(2019, 8, 29)
 ]

AG_switch_days = [
    date(2012, 7, 24), date(2012, 11, 1), 
    date(2013, 5, 7), date(2013, 11, 26), 
    date(2014, 5, 12), date(2014, 11, 5), 
    date(2015, 5, 6), date(2015, 11, 17), 
    date(2016, 5, 9), date(2016, 11, 10), 
    date(2017, 5, 10), date(2017, 11, 21), 
    date(2018, 5, 3), date(2018, 11, 2), 
    date(2019, 5, 8)
]



SR_switch_days =[
    date(2010, 8, 18), date(2010, 11, 1), 
    date(2011, 6, 14), date(2011, 9, 19), date(2011, 12, 28), 
    date(2012, 5, 28), date(2012, 10, 26), 
    date(2013, 1, 23), date(2013, 6, 28), date(2013, 11, 11), 
    date(2014, 2, 21), date(2014, 6, 18), date(2014, 11, 11), 
    date(2015, 2, 13), date(2015, 6, 24), date(2015, 11, 17), 
    date(2016, 3, 1), date(2016, 7, 21), date(2016, 12, 7), 
    date(2017, 3, 30), date(2017, 7, 17), date(2017, 12, 13), 
    date(2018, 3, 29), date(2018, 7, 30), date(2018, 11, 12), 
    date(2019, 3, 19), date(2019, 7, 26)
]

J_switch_days = [
    date(2011, 8, 22), date(2011, 12, 8), 
    date(2012, 4, 13), date(2012, 7, 17), date(2012, 10, 24),
    date(2013, 2, 6),                       date(2013, 10, 29), 

    date(2015, 3, 27), date(2015, 8, 11), date(2015, 11, 25), 
                        date(2016, 8, 15), date(2016, 12, 2), 
    date(2017, 3, 31), date(2017, 8, 2), date(2017, 11, 29),
    date(2018, 4, 10), date(2018, 8, 7), date(2018, 12, 5), 
    date(2019, 4, 4), date(2019, 8, 6)
]

JM_switch_days = [
    date(2013, 3, 22), date(2013, 7, 1), date(2013, 11, 4), 
    date(2014, 3, 13), date(2014, 7, 23), date(2014, 11, 18), 
    date(2015, 3, 30), date(2015, 8, 10), date(2015, 11, 24), 
    date(2016, 3, 31), date(2016, 8, 15), date(2016, 11, 29),
    date(2017, 3, 30), date(2017, 8, 3), date(2017, 11, 30), 
    date(2018, 4, 11), date(2018, 8, 8), date(2018, 12, 12), 
    date(2019, 4, 9), date(2019, 8, 16)
]

JD_switch_days = [
    date(2013, 11, 8), 
    date(2014, 3, 17), date(2014, 7, 29), date(2014, 11, 28), 
    date(2015, 4, 1), date(2015, 8, 3), date(2015, 11, 26), 
    date(2016, 3, 24), date(2016, 7, 29), date(2016, 11, 29), 
    date(2017, 4, 12), date(2017, 8, 2), date(2017, 11, 30), 
    date(2018, 4, 9), date(2018, 8, 6), date(2018, 12, 7), 
    date(2019, 4, 4), date(2019, 8, 5)
]


BU_switch_days = [
    date(2014, 2, 14), date(2014, 5, 21), date(2014, 9, 12), date(2014, 12, 10), 
    date(2015, 6, 2), date(2015, 8, 24), date(2015, 11, 25), date(2015, 12, 21),
    date(2016, 4, 11), date(2016, 8, 2), date(2016, 11, 10),
    date(2017, 4, 25), date(2017, 8, 2), date(2017, 11, 21), 
    date(2018, 5, 3), date(2018, 11, 22), 
    date(2019, 4, 30),date(2019, 11, 28)
]



FG_switch_days = [
    date(2012, 12, 3), 
    date(2013, 1, 29), date(2013, 10, 30), 
    date(2014, 3, 17), date(2014, 7, 10), date(2014, 11, 14), 
    date(2015, 4, 7),                     date(2015, 12, 1), 
    date(2016, 4, 6), date(2016, 8, 11), date(2016, 12, 2), 
    date(2017, 4, 11), date(2017, 8, 9), date(2017, 11, 28), 
    date(2018, 4, 10), date(2018, 8, 8), date(2018, 12, 12), 
    date(2019, 4, 11), date(2019, 8, 9)
]


CF_switch_days = [
    date(2010, 1, 12), date(2010, 3, 23), date(2010, 9, 3), 
    date(2011, 6, 13), date(2011, 8, 12), 
    date(2012, 2, 8), date(2012, 6, 4), date(2012, 11, 5), 
    date(2013, 1, 30), date(2013, 6, 13), date(2013, 10, 15), 
    date(2014, 3, 20), date(2014, 11, 14), 
    date(2015, 3, 20), date(2015, 7, 2), date(2015, 10, 26), 
    date(2016, 2, 4), date(2016, 6, 20), date(2016, 11, 22), 
    date(2017, 3, 31), date(2017, 8, 2), date(2017, 11, 28), 
    date(2018, 3, 23), date(2018, 5, 14), date(2018, 11, 22), 
    date(2019, 4, 3), date(2019, 8, 8)
]

P_switch_days = [
    date(2010, 1, 11), date(2010, 9, 13), date(2010, 11, 4), 
    date(2011, 4, 11), date(2011, 7, 19), 
    date(2012, 1, 18), date(2012, 6, 6), date(2012, 10, 24), 
    date(2013, 2, 8), date(2013, 6, 14), date(2013, 11, 4), 
    date(2014, 2, 26), date(2014, 6, 16), 
    date(2015, 3, 9), date(2015, 6, 4), date(2015, 11, 26), 
    date(2016, 3, 15), date(2016, 7, 7), date(2016, 11, 23), 
    date(2017, 3, 10), date(2017, 7, 11), date(2017, 11, 21), 
    date(2018, 3, 21), date(2018, 7, 20), date(2018, 12, 3), 
    date(2019, 4, 9), date(2019, 8, 5)
]

PP_switch_days = [
    date(2014, 3, 3), date(2014, 7, 30), date(2014, 11, 24), 
    date(2015, 3, 13), date(2015, 8, 3), date(2015, 11, 25), 
    date(2016, 3, 29), date(2016, 8, 15), date(2016, 11, 30), 
    date(2017, 4, 10), date(2017, 8, 8), date(2017, 11, 30), 
    date(2018, 4, 9), date(2018, 8, 6), date(2018, 12, 5), 
    date(2019, 4, 4), date(2019, 8, 1)
]

L_switch_days = [
    date(2010, 1, 11), date(2010, 2, 5), date(2010, 3, 26), date(2010, 7, 30), date(2010, 11, 10), 
    date(2011, 3, 28), date(2011, 7, 18), date(2011, 11, 9), 
    date(2012, 3, 15), date(2012, 7, 16), date(2012, 11, 1), 
    date(2013, 2, 7), date(2013, 7, 3), date(2013, 11, 14), 
    date(2014, 3, 6), date(2014, 7, 23), date(2014, 11, 28), 
    date(2015, 3, 18), date(2015, 8, 3), date(2015, 11, 26), 
    date(2016, 3, 24), date(2016, 7, 25), date(2016, 11, 28), 
    date(2017, 4, 6), date(2017, 7, 31), date(2017, 11, 28), 
    date(2018, 4, 4), date(2018, 7, 31), date(2018, 11, 16), 
    date(2019, 4, 1), date(2019, 8, 2)
]

Y_switch_days = [
    date(2010, 1, 11), date(2010, 2, 5), date(2010, 4, 23), date(2010, 8, 6), date(2010, 10, 26), 
    date(2011, 4, 11), date(2011, 7, 12), date(2011, 12, 15), 
    date(2012, 5, 29), date(2012, 10, 15), 
    date(2013, 1, 22), date(2013, 6, 24), date(2013, 10, 17), 
    date(2014, 2, 25), date(2014, 6, 5), date(2014, 10, 31), 
    date(2015, 3, 3), date(2015, 6, 16), date(2015, 11, 18), 
    date(2016, 3, 8), date(2016, 7, 5), date(2016, 11, 23), 
    date(2017, 3, 20), date(2017, 7, 28), date(2017, 11, 30), 
    date(2018, 3, 23), date(2018, 7, 27), date(2018, 12, 3), 
    date(2019, 4, 2), date(2019, 8, 1)
]

IF_switch_days = []

RU_switch_days = [
    date(2010, 6, 21), date(2010, 6, 23), date(2010, 7, 29), date(2010, 9, 13), date(2010, 10, 25), 
    date(2011, 3, 16), date(2011, 7, 4), date(2011, 11, 15), 
    date(2012, 4, 5), date(2012, 7, 20), date(2012, 11, 1), 
    date(2013, 2, 18), date(2013, 6, 27), date(2013, 11, 4), 
    date(2014, 2, 28), date(2014, 7, 24), date(2014, 11, 20), 
    date(2015, 3, 2), date(2015, 7, 16), date(2015, 11, 24), 
    date(2016, 3, 17), date(2016, 8, 3), date(2016, 11, 22), 
    date(2017, 3, 24), date(2017, 8, 2), date(2017, 11, 28), 
    date(2018, 3, 29), date(2018, 8, 7), date(2018, 11, 30), 
    date(2019, 3, 25), date(2019, 8, 8)
]



SwitchDays = defaultdict(list)

SwitchDays['SHFE F RB 88'] = RB_switch_days
SwitchDays['SHFE F CU 88'] = CU_switch_days
SwitchDays['SHFE F ZN 88'] = ZN_switch_days
SwitchDays['SHFE F NI 88'] = NI_switch_days
SwitchDays['SHFE F BU 88'] = BU_switch_days
SwitchDays['SHFE F AG 88'] = AG_switch_days
SwitchDays['SHFE F RU 88'] = RU_switch_days
# FU, SC, HC, AU,


SwitchDays['CZCE F TA 88'] = TA_switch_days
SwitchDays['CZCE F MA 88'] = MA_switch_days
SwitchDays['CZCE F SR 88'] = SR_switch_days
SwitchDays['CZCE F FG 88'] = FG_switch_days
SwitchDays['CZCE F CF 88'] = CF_switch_days

# RM, SM,AP,CJ



SwitchDays['DCE F I 88'] = I_switch_days
SwitchDays['DCE F J 88'] = J_switch_days
SwitchDays['DCE F JM 88'] = JM_switch_days
SwitchDays['DCE F JD 88'] = JD_switch_days
SwitchDays['DCE F P 88'] = P_switch_days
SwitchDays['DCE F PP 88'] = PP_switch_days
SwitchDays['DCE F L 88'] = L_switch_days
SwitchDays['DCE F Y 88'] = Y_switch_days
#V, M, B, C, A,  EB, EG



SwitchDays['CFFEX F IF 88'] = IF_switch_days










RB88TupleList = [
    ('RB1101',date(2010,7,20),date(2010,10,13) ),
    ('RB1105',date(2010,10,14),date(2011,2,9) ),
    ('RB1110',date(2011,2,10),date(2011,8,4) ),
    ('RB1201',date(2011,8,5),date(2011,11,2) ),
    ('RB1205',date(2011,11,3),date(2012,3,1) ),
    ('RB1210',date(2012,3,2),date(2012,7,11) ),
    ('RB1301',date(2012,7,12),date(2012,10,22) ),
    ('RB1305',date(2012,10,23),date(2013,2,18) ),
    ('RB1310',date(2013,2,19),date(2013,7,3) ),
    ('RB1401',date(2013,7,4),date(2013,10,30) ),
    ('RB1405',date(2013,10,31),date(2014,3,4) ),
    ('RB1410',date(2014,3,5),date(2014,7,7) ),
    ('RB1501',date(2014,7,8),date(2014,10,20) ),
    ('RB1505',date(2014,10,21),date(2015,3,11) ),
    ('RB1510',date(2015,3,12),date(2015,7,20) ),
    ('RB1601',date(2015,7,21),date(2015,11,4) ),
    ('RB1605',date(2015,11,5),date(2016,3,11) ),
    ('RB1610',date(2016,3,12),date(2016,8,17) ),
    ('RB1701',date(2016,8,18),date(2016,11,25) ),
    ('RB1705',date(2016,11,26),date(2017,3,22) ),
    ('RB1710',date(2017,3,23),date(2017,8,8) ),
    ('RB1801',date(2017,8,9),date(2017,11,9) ),
    ('RB1805',date(2017,11,10),date(2018,3,27) ),
    ('RB1810',date(2018,3,28),date(2018,8,17) ),
    ('RB1901',date(2018,8,18),date(2018,11,28) ),
    ('RB1905',date(2018,11,29),date(2019,3,29) ),
    ('RB1910',date(2019,3,30),date(2019,8,21) ),
    ('RB2001',date(2019,8,22),date(2019,11,30) ),
]


TA88TupleList = [
    ('TA1003',date(2010,1,1),date(2010,1,21) ),
    ('TA1005',date(2010,1,22),date(2010,3,26) ),
    ('TA1009',date(2010,3,27),date(2010,7,28) ),
    ('TA1101',date(2010,7,29),date(2010,11,1) ),
    ('TA1105',date(2010,11,2),date(2011,3,24) ),
    ('TA1109',date(2011,3,25),date(2011,7,4) ),
    ('TA1201',date(2011,7,5),date(2011,11,21) ),
    ('TA1205',date(2011,11,22),date(2012,3,14) ),
    ('TA1209',date(2012,3,15),date(2012,7,11) ),
    ('TA1301',date(2012,7,12),date(2012,11,5) ),
    ('TA1305',date(2012,11,6),date(2013,2,21) ),
    ('TA1309',date(2013,2,22),date(2013,7,11) ),
    ('TA1401',date(2013,7,12),date(2013,12,4) ),
    ('TA1405',date(2013,12,5),date(2014,3,13) ),
    ('TA1409',date(2014,3,14),date(2014,8,6) ),
    ('TA1501',date(2014,8,7),date(2014,11,25) ),
    ('TA1505',date(2014,11,26),date(2015,3,30) ),
    ('TA1509',date(2015,3,31),date(2015,8,5) ),
    ('TA1601',date(2015,8,6),date(2015,11,24) ),
    ('TA1605',date(2015,11,25),date(2016,3,30) ),
    ('TA1609',date(2016,3,31),date(2016,8,4) ),
    ('TA1701',date(2016,8,5),date(2016,11,17) ),
    ('TA1705',date(2016,11,18),date(2017,4,7) ),
    ('TA1709',date(2017,4,8),date(2017,8,7) ),
    ('TA1801',date(2017,8,8),date(2017,11,22) ),
    ('TA1805',date(2017,11,23),date(2018,3,28) ),
    ('TA1809',date(2018,3,29),date(2018,8,6) ),
    ('TA1901',date(2018,8,7),date(2018,11,30) ),
    ('TA1905',date(2018,12,1),date(2019,4,8) ),
    ('TA1909',date(2019,4,9),date(2019,8,14) ),
    ('TA2001',date(2019,8,15),date(2019,11,30) ),
]

MA88TupleList = [
    ('MA1509',date(2015,4,17),date(2015,7,27) ),
    ('MA1601',date(2015,7,28),date(2015,11,27) ),
    ('MA1605',date(2015,11,28),date(2016,4,8) ),
    ('MA1609',date(2016,4,9),date(2016,8,9) ),
    ('MA1701',date(2016,8,10),date(2016,12,1) ),
    ('MA1705',date(2016,12,2),date(2017,4,6) ),
    ('MA1709',date(2017,4,7),date(2017,8,4) ),
    ('MA1801',date(2017,8,5),date(2017,12,8) ),
    ('MA1805',date(2017,12,9),date(2018,4,11) ),
    ('MA1809',date(2018,4,12),date(2018,8,8) ),
    ('MA1901',date(2018,8,9),date(2018,12,12) ),
    ('MA1905',date(2018,12,13),date(2019,4,12) ),
    ('MA1909',date(2019,4,13),date(2019,8,15) ),
    ('MA2001',date(2019,8,16),date(2019,11,30) ),
]



I88TupleList = [
    ('I1405',date(2013,10,19),date(2014,2,28) ),
    ('I1409',date(2014,3,1),date(2014,7,22) ),
    ('I1501',date(2014,7,23),date(2014,10,22) ),
    ('I1505',date(2014,10,23),date(2015,3,6) ),
    ('I1509',date(2015,3,7),date(2015,7,21) ),
    ('I1601',date(2015,7,22),date(2015,11,23) ),
    ('I1605',date(2015,11,24),date(2016,3,18) ),
    ('I1609',date(2016,3,19),date(2016,8,10) ),
    ('I1701',date(2016,8,11),date(2016,11,25) ),
    ('I1705',date(2016,11,26),date(2017,3,22) ),
    ('I1709',date(2017,3,23),date(2017,7,31) ),
    ('I1801',date(2017,8,1),date(2017,11,22) ),
    ('I1805',date(2017,11,23),date(2018,4,3) ),
    ('I1809',date(2018,4,4),date(2018,8,7) ),
    ('I1901',date(2018,8,8),date(2018,11,29) ),
    ('I1905',date(2018,11,30),date(2019,4,8) ),
    ('I1909',date(2019,4,9),date(2019,7,31) ),
    ('I2001',date(2019,8,1),date(2019,11,30) ),
]

JM88TupleList = [
    ('JM1309',date(2013, 3, 23),date(2013, 7, 1) ),
    ('JM1401',date(2013, 7, 2),date(2013, 11, 4) ),
    ('JM1405',date(2013,11,5),date(2014, 3, 13) ),
    ('JM1409',date(2014,3,14),date(2014, 7, 23) ),
    ('JM1501',date(2014,7,24),date(2014, 11, 18) ),
    ('JM1505',date(2014,11,19),date(2015, 3, 30) ),
    ('JM1509',date(2015,3,31),date(2015, 8, 10) ),
    ('JM1601',date(2015,8,11),date(2015, 11, 24) ),
    ('JM1605',date(2015,11,25),date(2016, 3, 31)),
    ('JM1609',date(2016,4,1),date(2016, 8, 15) ),
    ('JM1701',date(2016,8,16),date(2016, 11, 29) ),
    ('JM1705',date(2016,11,30),date(2017, 3, 30) ),
    ('JM1709',date(2017,3,31),date(2017, 8, 3) ),
    ('JM1801',date(2017,8,4),date(2017, 11, 30) ),
    ('JM1805',date(2017,12,1),date(2018, 4, 11) ),
    ('JM1809',date(2018,4,12),date(2018, 8, 8) ),
    ('JM1901',date(2018,8,9),date(2018, 12, 12) ),
    ('JM1905',date(2018,12,13),date(2019, 4, 9) ),
    ('JM1909',date(2019,4,10),date(2019, 8, 16) ),
    ('JM2001',date(2019,8,17),date(2019,11,30) ),
]

J88TupleList = [
    ('J1201', date(2011, 8, 23), date(2011, 12, 8)),
    ('J1205', date(2011, 12, 9), date(2012, 4, 13)), 
    ('J1209', date(2012, 4, 14), date(2012, 7, 17)), 
    ('J1301', date(2012, 7, 18), date(2012, 10, 24)), 
    ('J1305', date(2012, 10, 25), date(2013, 2, 6)), 
    ('J1401', date(2013, 2, 7), date(2013, 10, 29)),  # need correct 
    ('J1501', date(2013, 10, 30), date(2015, 3, 27)),  # need correct 
    ('J1601', date(2015, 3, 28), date(2015, 8, 11)), 
    ('J1605', date(2015, 8, 12), date(2015, 11, 25)), 
    ('J1609', date(2015, 11, 26), date(2016, 8, 15)), 
    ('J1701', date(2016, 8, 16), date(2016, 12, 2)), 
    ('J1705', date(2016, 12, 3), date(2017, 3, 31)), 
    ('J1709', date(2017, 4, 1), date(2017, 8, 2)), 
    ('J1801', date(2017, 8, 3), date(2017, 11, 29)), 
    ('J1805', date(2017, 11, 30), date(2018, 4, 10)), 
    ('J1809', date(2018, 4, 11), date(2018, 8, 7)), 
    ('J1901', date(2018, 8, 8), date(2018, 12, 5)), 
    ('J1905', date(2018, 12, 6), date(2019, 4, 4)), 
    ('J1909', date(2019, 4, 5), date(2019, 8, 6)),

]

JD88TupleList = [
    ('JD1405', date(2013, 11, 9), date(2014, 3, 17)), 
    ('JD1409', date(2014, 3, 18), date(2014, 7, 29)), 
    ('JD1501', date(2014, 7, 30), date(2014, 11, 28)), 
    ('JD1505', date(2014, 11, 29), date(2015, 4, 1)), 
    ('JD1509', date(2015, 4, 2), date(2015, 8, 3)), 
    ('JD1601', date(2015, 8, 4), date(2015, 11, 26)), 
    ('JD1605', date(2015, 11, 27), date(2016, 3, 24)), 
    ('JD1609', date(2016, 3, 25), date(2016, 7, 29)), 
    ('JD1701', date(2016, 7, 30), date(2016, 11, 29)), 
    ('JD1705', date(2016, 11, 30), date(2017, 4, 12)), 
    ('JD1709', date(2017, 4, 13), date(2017, 8, 2)), 
    ('JD1801', date(2017, 8, 3), date(2017, 11, 30)), 
    ('JD1805', date(2017, 12, 1), date(2018, 4, 9)), 
    ('JD1809', date(2018, 4, 10), date(2018, 8, 6)), 
    ('JD1901', date(2018, 8, 7), date(2018, 12, 7)), 
    ('JD1905', date(2018, 12, 8), date(2019, 4, 4)), 
    ('JD1909', date(2019, 4, 5), date(2019, 8, 5))
]

AG88TupleList = [
    ('AG1212', date(2012, 7, 25), date(2012, 11, 1)),
    ('AG1306', date(2012, 11, 2), date(2013, 5, 7)), 
    ('AG1312', date(2013, 5, 8), date(2013, 11, 26)), 
    ('AG1406', date(2013, 11, 27), date(2014, 5, 12)), 
    ('AG1412', date(2014, 5, 13), date(2014, 11, 5)), 
    ('AG1506', date(2014, 11, 6), date(2015, 5, 6)), 
    ('AG1512', date(2015, 5, 7), date(2015, 11, 17)), 
    ('AG1606', date(2015, 11, 18), date(2016, 5, 9)), 
    ('AG1612', date(2016, 5, 10), date(2016, 11, 10)), 
    ('AG1706', date(2016, 11, 11), date(2017, 5, 10)), 
    ('AG1712', date(2017, 5, 11), date(2017, 11, 21)), 
    ('AG1806', date(2017, 11, 22), date(2018, 5, 3)), 
    ('AG1812', date(2018, 5, 4), date(2018, 11, 2)), 
    ('AG1906', date(2018, 11, 3), date(2019, 5, 8)),
    ('AG1912', date(2018, 5, 9), date(2019, 12, 2))   # need correct 
]



SR88TupleList = [
    ('SR1105', date(2010, 8, 19), date(2010, 11, 1)),
    ('SR1109', date(2010, 11, 2), date(2011, 6, 14)), 
    ('SR1201', date(2011, 6, 15), date(2011, 9, 19)), 
    ('SR1205', date(2011, 9, 20), date(2011, 12, 28)), 
    ('SR1209', date(2011, 12, 29), date(2012, 5, 28)), 
    ('SR1301', date(2012, 5, 29), date(2012, 10, 26)), 
    ('SR1305', date(2012, 10, 27), date(2013, 1, 23)), 
    ('SR1309', date(2013, 1, 24), date(2013, 6, 28)), 
    ('SR1401', date(2013, 6, 29), date(2013, 11, 11)), 
    ('SR1405', date(2013, 11, 12), date(2014, 2, 21)), 
    ('SR1409', date(2014, 2, 22), date(2014, 6, 18)), 
    ('SR1501', date(2014, 6, 19), date(2014, 11, 11)), 
    ('SR1505', date(2014, 11, 12), date(2015, 2, 13)), 
    ('SR1509', date(2015, 2, 14), date(2015, 6, 24)), 
    ('SR1601', date(2015, 6, 25), date(2015, 11, 17)), 
    ('SR1605', date(2015, 11, 18), date(2016, 3, 1)), 
    ('SR1609', date(2016, 3, 2), date(2016, 7, 21)), 
    ('SR1701', date(2016, 7, 22), date(2016, 12, 7)), 
    ('SR1705', date(2016, 12, 8), date(2017, 3, 30)), 
    ('SR1709', date(2017, 3, 31), date(2017, 7, 17)), 
    ('SR1801', date(2017, 7, 18), date(2017, 12, 13)), 
    ('SR1805', date(2017, 12, 14), date(2018, 3, 29)), 
    ('SR1809', date(2018, 3, 30), date(2018, 7, 30)), 
    ('SR1901', date(2018, 7, 31), date(2018, 11, 12)), 
    ('SR1905', date(2018, 11, 13), date(2019, 3, 19)), 
    ('SR1909', date(2019, 3, 20), date(2019, 7, 26)),

]

JD88TupleList = [
    ('JD1405', date(2013, 11, 9), date(2014, 3, 17)),
    ('JD1409', date(2014, 3, 18), date(2014, 7, 29)), 
    ('JD1501', date(2014, 7, 30), date(2014, 11, 28)), 
    ('JD1505', date(2014, 11, 29), date(2015, 4, 1)), 
    ('JD1509', date(2015, 4, 2), date(2015, 8, 3)), 
    ('JD1601', date(2015, 8, 4), date(2015, 11, 26)), 
    ('JD1605', date(2015, 11, 27), date(2016, 3, 24)), 
    ('JD1609', date(2016, 3, 25), date(2016, 7, 29)), 
    ('JD1701', date(2016, 7, 30), date(2016, 11, 29)), 
    ('JD1705', date(2016, 11, 30), date(2017, 4, 12)), 
    ('JD1709', date(2017, 4, 13), date(2017, 8, 2)), 
    ('JD1801', date(2017, 8, 3), date(2017, 11, 30)), 
    ('JD1805', date(2017, 12, 1), date(2018, 4, 9)), 
    ('JD1809', date(2018, 4, 10), date(2018, 8, 6)), 
    ('JD1901', date(2018, 8, 7), date(2018, 12, 7)), 
    ('JD1905', date(2018, 12, 8), date(2019, 4, 4)), 
    ('JD1909', date(2019, 4, 5), date(2019, 8, 5))

]


BU88TupleList = [
    ('BU1406', date(2014, 2, 15), date(2014, 5, 21)), 
    ('BU1410', date(2014, 5, 22), date(2014, 9, 12)), 
    ('BU1412', date(2014, 9, 13), date(2014, 12, 10)),   # need correct...
    ('BU1506', date(2014, 12, 11), date(2015, 6, 2)), 
    ('BU1510', date(2015, 6, 3), date(2015, 8, 24)), 
    ('BU1512', date(2015, 8, 25), date(2015, 11, 25)), 
    ('BU1602', date(2015, 11, 26), date(2015, 12, 21)), 
    ('BU1606', date(2015, 12, 22), date(2016, 4, 11)), 
    ('BU1609', date(2016, 4, 12), date(2016, 8, 2)), 
    ('BU1612', date(2016, 8, 3), date(2016, 11, 10)), 
    ('BU1706', date(2016, 11, 11), date(2017, 4, 25)), 
    ('BU1709', date(2017, 4, 26), date(2017, 8, 2)), 
    ('BU1712', date(2017, 8, 3), date(2017, 11, 21)), 
    ('BU1806', date(2017, 11, 22), date(2018, 5, 3)), 
    ('BU1812', date(2018, 5, 4), date(2018, 11, 22)), 
    ('BU1906', date(2018, 11, 23), date(2019, 4, 30)), 
    ('BU1912', date(2019, 5, 1), date(2019, 11, 28))

]


FG88TupleList = [
    ('FG1401', date(2012, 12, 4), date(2013, 1, 29)), 
    ('FG1405', date(2013, 1, 30), date(2013, 10, 30)), 
    ('FG1409', date(2013, 10, 31), date(2014, 3, 17)), 
    ('FG1501', date(2014, 3, 18), date(2014, 7, 10)), # need correct
    ('FG1505', date(2014, 7, 11), date(2014, 11, 14)), 
    ('FG1509', date(2014, 11, 15), date(2015, 4, 7)), 
    ('FG1601', date(2015, 4, 8), date(2015, 12, 1)), 
    ('FG1605', date(2015, 12, 2), date(2016, 4, 6)), 
    ('FG1609', date(2016, 4, 7), date(2016, 8, 11)), 
    ('FG1701', date(2016, 8, 12), date(2016, 12, 2)), 
    ('FG1705', date(2016, 12, 3), date(2017, 4, 11)), 
    ('FG1709', date(2017, 4, 12), date(2017, 8, 9)), 
    ('FG1801', date(2017, 8, 10), date(2017, 11, 28)), 
    ('FG1805', date(2017, 11, 29), date(2018, 4, 10)), 
    ('FG1809', date(2018, 4, 11), date(2018, 8, 8)), 
    ('FG1901', date(2018, 8, 9), date(2018, 12, 12)), 
    ('FG1905', date(2018, 12, 13), date(2019, 4, 11)), 
    ('FG1909', date(2019, 4, 12), date(2019, 8, 9))
]


CF88TupleList = [
    ('CF1101', date(2010, 1, 13), date(2010, 3, 23)),  #need correct
    ('CF1105', date(2010, 3, 24), date(2010, 9, 3)),
    ('CF1109', date(2010, 9, 4), date(2011, 6, 13)), 
    ('CF1201', date(2011, 6, 14), date(2011, 8, 12)),
    ('CF1205', date(2011, 8, 13), date(2012, 2, 8)), 
    ('CF1209', date(2012, 2, 9), date(2012, 6, 4)), 
    ('CF1301', date(2012, 6, 5), date(2012, 11, 5)), 
    ('CF1305', date(2012, 11, 6), date(2013, 1, 30)), 
    ('CF1309', date(2013, 1, 31), date(2013, 6, 13)), 
    ('CF1401', date(2013, 6, 14), date(2013, 10, 15)), 
    ('CF1405', date(2013, 10, 16), date(2014, 3, 20)), 
    ('CF1501', date(2014, 3, 21), date(2014, 11, 14)), 
    ('CF1505', date(2014, 11, 15), date(2015, 3, 20)), 
    ('CF1509', date(2015, 3, 21), date(2015, 7, 2)), 
    ('CF1512', date(2015, 7, 3), date(2015, 10, 26)), 
    ('CF1601', date(2015, 10, 27), date(2016, 2, 4)), 
    ('CF1609', date(2016, 2, 5), date(2016, 6, 20)), 
    ('CF1701', date(2016, 6, 21), date(2016, 11, 22)), 
    ('CF1705', date(2016, 11, 23), date(2017, 3, 31)), 
    ('CF1709', date(2017, 4, 1), date(2017, 8, 2)), 
    ('CF1801', date(2017, 8, 3), date(2017, 11, 28)), 
    ('CF1805', date(2017, 11, 29), date(2018, 3, 23)), 
    ('CF1809', date(2018, 3, 24), date(2018, 5, 14)), 
    ('CF1901', date(2018, 5, 15), date(2018, 11, 22)), 
    ('CF1905', date(2018, 11, 23), date(2019, 4, 3)), 
    ('CF1909', date(2019, 4, 4), date(2019, 8, 8))
]


P88TupleList = [
    ('P1111', date(2010, 1, 12), date(2010, 9, 13)), #need correct
    ('P1101', date(2010, 9, 14), date(2010, 11, 4)), 
    ('P1105', date(2010, 11, 5), date(2011, 4, 11)), 
    ('P1109', date(2011, 4, 12), date(2011, 7, 19)), 
    ('P1205', date(2011, 7, 20), date(2012, 1, 18)), 
    ('P1209', date(2012, 1, 19), date(2012, 6, 6)), 
    ('P1301', date(2012, 6, 7), date(2012, 10, 24)), 
    ('P1305', date(2012, 10, 25), date(2013, 2, 8)), 
    ('P1309', date(2013, 2, 9), date(2013, 6, 14)), 
    ('P1401', date(2013, 6, 15), date(2013, 11, 4)), 
    ('P1405', date(2013, 11, 5), date(2014, 2, 26)), 
    ('P1501', date(2014, 2, 27), date(2014, 6, 16)), 
    ('P1505', date(2014, 6, 17), date(2015, 3, 9)), 
    ('P1509', date(2015, 3, 10), date(2015, 6, 4)), 
    ('P1601', date(2015, 6, 5), date(2015, 11, 26)), 
    ('P1605', date(2015, 11, 27), date(2016, 3, 15)), 
    ('P1609', date(2016, 3, 16), date(2016, 7, 7)), 
    ('P1701', date(2016, 7, 8), date(2016, 11, 23)), 
    ('P1705', date(2016, 11, 24), date(2017, 3, 10)), 
    ('P1709', date(2017, 3, 11), date(2017, 7, 11)), 
    ('P1801', date(2017, 7, 12), date(2017, 11, 21)), 
    ('P1805', date(2017, 11, 22), date(2018, 3, 21)), 
    ('P1809', date(2018, 3, 22), date(2018, 7, 20)), 
    ('P1901', date(2018, 7, 21), date(2018, 12, 3)), 
    ('P1905', date(2018, 12, 4), date(2019, 4, 9)), 
    ('P1909', date(2019, 4, 10), date(2019, 8, 5))

]

PP88TupleList = [
    ('PP1409', date(2014, 3, 4), date(2014, 7, 30)), 
    ('PP1501', date(2014, 7, 31), date(2014, 11, 24)), 
    ('PP1505', date(2014, 11, 25), date(2015, 3, 13)), 
    ('PP1509', date(2015, 3, 14), date(2015, 8, 3)), 
    ('PP1601', date(2015, 8, 4), date(2015, 11, 25)), 
    ('PP1605', date(2015, 11, 26), date(2016, 3, 29)), 
    ('PP1609', date(2016, 3, 30), date(2016, 8, 15)), 
    ('PP1701', date(2016, 8, 16), date(2016, 11, 30)), 
    ('PP1705', date(2016, 12, 1), date(2017, 4, 10)), 
    ('PP1709', date(2017, 4, 11), date(2017, 8, 8)), 
    ('PP1801', date(2017, 8, 9), date(2017, 11, 30)), 
    ('PP1805', date(2017, 12, 1), date(2018, 4, 9)), 
    ('PP1809', date(2018, 4, 10), date(2018, 8, 6)), 
    ('PP1901', date(2018, 8, 7), date(2018, 12, 5)), 
    ('PP1905', date(2018, 12, 6), date(2019, 4, 4)), 
    ('PP1909', date(2019, 4, 5), date(2019, 8, 1))
    
]

L88TupleList = [
    ('L1003', date(2010, 1, 12), date(2010, 2, 5)), 
    ('L1005', date(2010, 2, 6), date(2010, 3, 26)), 
    ('L1009', date(2010, 3, 27), date(2010, 7, 30)), 
    ('L1101', date(2010, 7, 31), date(2010, 11, 10)), 
    ('L1105', date(2010, 11, 11), date(2011, 3, 28)), 
    ('L1109', date(2011, 3, 29), date(2011, 7, 18)), 
    ('L1201', date(2011, 7, 19), date(2011, 11, 9)), 
    ('L1205', date(2011, 11, 10), date(2012, 3, 15)), 
    ('L1209', date(2012, 3, 16), date(2012, 7, 16)), 
    ('L1301', date(2012, 7, 17), date(2012, 11, 1)), 
    ('L1305', date(2012, 11, 2), date(2013, 2, 7)), 
    ('L1309', date(2013, 2, 8), date(2013, 7, 3)), 
    ('L1401', date(2013, 7, 4), date(2013, 11, 14)), 
    ('L1405', date(2013, 11, 15), date(2014, 3, 6)), 
    ('L1409', date(2014, 3, 7), date(2014, 7, 23)), 
    ('L1501', date(2014, 7, 24), date(2014, 11, 28)),
    ('L1505', date(2014, 11, 29), date(2015, 3, 18)), 
    ('L1509', date(2015, 3, 19), date(2015, 8, 3)), 
    ('L1601', date(2015, 8, 4), date(2015, 11, 26)), 
    ('L1605', date(2015, 11, 27), date(2016, 3, 24)), 
    ('L1609', date(2016, 3, 25), date(2016, 7, 25)), 
    ('L1701', date(2016, 7, 26), date(2016, 11, 28)), 
    ('L1705', date(2016, 11, 29), date(2017, 4, 6)), 
    ('L1709', date(2017, 4, 7), date(2017, 7, 31)), 
    ('L1801', date(2017, 8, 1), date(2017, 11, 28)), 
    ('L1805', date(2017, 11, 29), date(2018, 4, 4)), 
    ('L1809', date(2018, 4, 5), date(2018, 7, 31)), 
    ('L1901', date(2018, 8, 1), date(2018, 11, 16)), 
    ('L1905', date(2018, 11, 17), date(2019, 4, 1)), 
    ('L1909', date(2019, 4, 2), date(2019, 8, 2))

]

Y88TupleList = [
    ('Y1001', date(2010, 1, 12), date(2010, 2, 5)), 
    ('Y1005', date(2010, 2, 6), date(2010, 4, 23)), 
    ('Y1009', date(2010, 4, 24), date(2010, 8, 6)), 
    ('Y1101', date(2010, 8, 7), date(2010, 10, 26)), 
    ('Y1105', date(2010, 10, 27), date(2011, 4, 11)), 
    ('Y1109', date(2011, 4, 12), date(2011, 7, 12)), 
    ('Y1201', date(2011, 7, 13), date(2011, 12, 15)), 
    ('Y1209', date(2011, 12, 16), date(2012, 5, 29)), 
    ('Y1301', date(2012, 5, 30), date(2012, 10, 15)), 
    ('Y1305', date(2012, 10, 16), date(2013, 1, 22)), 
    ('Y1309', date(2013, 1, 23), date(2013, 6, 24)), 
    ('Y1401', date(2013, 6, 25), date(2013, 10, 17)), 
    ('Y1405', date(2013, 10, 18), date(2014, 2, 25)), 
    ('Y1409', date(2014, 2, 26), date(2014, 6, 5)), 
    ('Y1501', date(2014, 6, 6), date(2014, 10, 31)), 
    ('Y1505', date(2014, 11, 1), date(2015, 3, 3)), 
    ('Y1509', date(2015, 3, 4), date(2015, 6, 16)), 
    ('Y1601', date(2015, 6, 17), date(2015, 11, 18)), 
    ('Y1605', date(2015, 11, 19), date(2016, 3, 8)), 
    ('Y1609', date(2016, 3, 9), date(2016, 7, 5)), 
    ('Y1701', date(2016, 7, 6), date(2016, 11, 23)), 
    ('Y1705', date(2016, 11, 24), date(2017, 3, 20)), 
    ('Y1709', date(2017, 3, 21), date(2017, 7, 28)), 
    ('Y1801', date(2017, 7, 29), date(2017, 11, 30)), 
    ('Y1805', date(2017, 12, 1), date(2018, 3, 23)), 
    ('Y1809', date(2018, 3, 24), date(2018, 7, 27)), 
    ('Y1901', date(2018, 7, 28), date(2018, 12, 3)), 
    ('Y1905', date(2018, 12, 4), date(2019, 4, 2)), 
    ('Y1909', date(2019, 4, 3), date(2019, 8, 1))
]

RU88TupleList = [
    ('RU1009', date(2010, 6, 22), date(2010, 6, 23)),  #need correct
    ('RU1009', date(2010, 6, 24), date(2010, 7, 29)), 
    ('RU1011', date(2010, 7, 30), date(2010, 9, 13)), 
    ('RU1101', date(2010, 9, 14), date(2010, 10, 25)), 
    ('RU1105', date(2010, 10, 26), date(2011, 3, 16)), 
    ('RU1109', date(2011, 3, 17), date(2011, 7, 4)), 
    ('RU1201', date(2011, 7, 5), date(2011, 11, 15)), 
    ('RU1205', date(2011, 11, 16), date(2012, 4, 5)), 
    ('RU1209', date(2012, 4, 6), date(2012, 7, 20)), 
    ('RU1301', date(2012, 7, 21), date(2012, 11, 1)), 
    ('RU1305', date(2012, 11, 2), date(2013, 2, 18)), 
    ('RU1309', date(2013, 2, 19), date(2013, 6, 27)), 
    ('RU1401', date(2013, 6, 28), date(2013, 11, 4)), 
    ('RU1405', date(2013, 11, 5), date(2014, 2, 28)), 
    ('RU1409', date(2014, 3, 1), date(2014, 7, 24)), 
    ('RU1501', date(2014, 7, 25), date(2014, 11, 20)), 
    ('RU1505', date(2014, 11, 21), date(2015, 3, 2)), 
    ('RU1509', date(2015, 3, 3), date(2015, 7, 16)), 
    ('RU1601', date(2015, 7, 17), date(2015, 11, 24)), 
    ('RU1605', date(2015, 11, 25), date(2016, 3, 17)), 
    ('RU1609', date(2016, 3, 18), date(2016, 8, 3)), 
    ('RU1701', date(2016, 8, 4), date(2016, 11, 22)), 
    ('RU1705', date(2016, 11, 23), date(2017, 3, 24)), 
    ('RU1709', date(2017, 3, 25), date(2017, 8, 2)), 
    ('RU1801', date(2017, 8, 3), date(2017, 11, 28)), 
    ('RU1805', date(2017, 11, 29), date(2018, 3, 29)), 
    ('RU1809', date(2018, 3, 30), date(2018, 8, 7)), 
    ('RU1901', date(2018, 8, 8), date(2018, 11, 30)), 
    ('RU1905', date(2018, 12, 1), date(2019, 3, 25)), 
    ('RU1909', date(2019, 3, 26), date(2019, 8, 8))

]

DominantDict = {}
DominantDict['SHFE F RB 88'] = RB88TupleList
DominantDict['SHFE F RU 88'] = RU88TupleList
DominantDict['SHFE F BU 88'] = BU88TupleList
DominantDict['SHFE F AG 88'] = AG88TupleList

DominantDict['DCE F I 88'] = TA88TupleList
DominantDict['DCE F J 88'] = J88TupleList
DominantDict['DCE F JM 88'] = JM88TupleList
DominantDict['DCE F P 88'] = P88TupleList
DominantDict['DCE F PP 88'] = PP88TupleList
DominantDict['DCE F L 88'] = L88TupleList
DominantDict['DCE F Y 88'] = Y88TupleList
DominantDict['DCE F JD 88'] = JD88TupleList

DominantDict['CZCE F TA 88'] = TA88TupleList
DominantDict['CZCE F MA 88'] = MA88TupleList
DominantDict['CZCE F SR 88'] = SR88TupleList
DominantDict['CZCE F CF 88'] = CF88TupleList
DominantDict['CZCE F FG 88'] = FG88TupleList







