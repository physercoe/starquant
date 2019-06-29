#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from logging import INFO
from typing import Any, Callable

from .constant import (EventType, MSG_TYPE, Exchange, Interval,
                       OrderType, Direction, Offset, Status, OrderFlag, OrderStatus, ACTIVE_STATUSES, StopOrderStatus,
                       DIRECTION_CTP2VT, ORDERFALG_2VT, ORDERSTATUS_2VT,
                       Product, OptionType, SYMBOL_TYPE,
                       OPTIONTYPE_CTP2VT, PRODUCT_CTP2VT, PRODUCT_VT2SQ, EXCHANGE_CTP2VT)
from ..api.ctp_constant import THOST_FTDC_PT_Net
from .utility import generate_full_symbol, extract_full_symbol, generate_vt_symbol


def retrieve_multiplier_from_full_symbol(symbol=""):
    return 1.0

# ################### Begin base class definitions##################


class Event(object):
    """
    Base Event class for event-driven system
    """

    def __init__(self,
                 type: EventType = EventType.HEADER,
                 data: Any = None,
                 des: str = '',
                 src: str = '',
                 msgtype: MSG_TYPE = MSG_TYPE.MSG_TYPE_BASE
                 ):

        self.event_type = type
        self.data = data
        self.destination = des
        self.source = src
        self.msg_type = msgtype

    @property
    def type(self):
        return self.event_type.name

    def serialize(self):
        msg = self.destination + '|' + self.source + \
            '|' + str(self.msg_type.value)
        if self.data:
            if type(self.data) == str:
                msg = msg + '|' + self.data
            else:
                try:
                    msg = msg + '|' + self.data.serialize()
                except Exception as e:
                    print(e)
                    pass
        return msg

    def deserialize(self, msg: str):
        v = msg.split('|', 3)
        try:
            self.destination = v[0]
            self.source = v[1]
            msg2type = MSG_TYPE(int(v[2]))
            if msg2type in [MSG_TYPE.MSG_TYPE_TICK, MSG_TYPE.MSG_TYPE_TICK_L1, MSG_TYPE.MSG_TYPE_TICK_L5]:
                self.event_type = EventType.TICK
                self.data = TickData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RTN_ORDER:
                self.event_type = EventType.ORDERSTATUS
                self.data = OrderData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RTN_TRADE:
                self.event_type = EventType.FILL
                self.data = TradeData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RSP_POS:
                self.event_type = EventType.POSITION
                self.data = PositionData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_BAR:
                self.event_type = EventType.BAR
                self.data = BarData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RSP_ACCOUNT:
                self.event_type = EventType.ACCOUNT
                self.data = AccountData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RSP_CONTRACT:
                self.event_type = EventType.CONTRACT
                self.data = ContractData(gateway_name=self.source)
                self.data.deserialize(v[3])
            elif v[2].startswith('11'):
                self.event_type = EventType.ENGINE_CONTROL
                self.msg_type = msg2type
                if len(v) > 3:
                    self.data = v[3]
            elif v[2].startswith('12'):
                self.event_type = EventType.STRATEGY_CONTROL
                self.msg_type = msg2type
                if len(v) > 3:
                    self.data = v[3]
            elif v[2].startswith('14'):
                self.event_type = EventType.RECORDER_CONTROL
                self.msg_type = msg2type
                if len(v) > 3:
                    self.data = v[3]
            elif v[2].startswith('3'):  # msg2type == MSG_TYPE.MSG_TYPE_INFO:
                self.event_type = EventType.INFO
                self.msg_type = msg2type
                self.data = LogData(gateway_name=self.source)
                self.data.deserialize(v[3])
            else:
                self.event_type = EventType.HEADER
                self.msg_type = msg2type
        except Exception as e:
            print(e)
            pass


@dataclass
class BaseData:
    """
    Any data object needs a gateway_name as source 
    and should inherit base data.
    """

    gateway_name: str = ''

    def serialize(self):
        pass

    def deserialize(self, msg):
        pass


@dataclass
class TickData(BaseData):
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
    """

    symbol: str = ""
    exchange: Exchange = Exchange.SHFE
    datetime: datetime = datetime(2019, 1, 1)

    name: str = ""
    volume: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

# StarQuant unique field
    depth: int = 0
    open_interest: float = 0

    def __post_init__(self):
        """"""

        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.timestamp = Timestamp(self.datetime)
        self.full_symbol = generate_full_symbol(self.exchange, self.symbol)

    def deserialize(self, msg: str):
        try:
            v = msg.split('|')
            self.full_symbol = v[0]
            self.timestamp = pd.to_datetime(v[1])
            self.datetime = self.timestamp.to_pydatetime()
            self.symbol, self.exchange = extract_full_symbol(self.full_symbol)
            self.vt_symbol = generate_vt_symbol(self.symbol, self.exchange)
            self.last_price = float(v[2])
            self.volume = int(v[3])

            if (len(v) < 17):
                self.depth = 1
                self.bid_price_1 = float(v[4])
                self.bid_volume_1 = int(v[5])
                self.ask_price_1 = float(v[6])
                self.ask_volume_1 = int(v[7])
                self.open_interest = int(v[8])
                self.open_price = float(v[9])
                self.high_price = float(v[10])
                self.low_price = float(v[11])
                self.pre_close = float(v[12])
                self.limit_up = float(v[13])
                self.limit_down = float(v[14])
            else:
                self.depth = 5
                self.bid_price_1 = float(v[4])
                self.bid_volume_1 = int(v[5])
                self.ask_price_1 = float(v[6])
                self.ask_volume_1 = int(v[7])
                self.bid_price_2 = float(v[8])
                self.bid_volume_2 = int(v[9])
                self.ask_price_2 = float(v[10])
                self.ask_volume_2 = int(v[11])
                self.bid_price_3 = float(v[12])
                self.bid_volume_3 = int(v[13])
                self.ask_price_3 = float(v[14])
                self.ask_volume_3 = int(v[15])
                self.bid_price_4 = float(v[16])
                self.bid_volume_4 = int(v[17])
                self.ask_price_4 = float(v[18])
                self.ask_volume_4 = int(v[19])
                self.bid_price_5 = float(v[20])
                self.bid_volume_5 = int(v[21])
                self.ask_price_5 = float(v[22])
                self.ask_volume_5 = int(v[23])
                self.open_interest = int(v[24])
                self.open_price = float(v[25])
                self.high_price = float(v[26])
                self.low_price = float(v[27])
                self.pre_close = float(v[28])
                self.limit_up = float(v[29])
                self.limit_down = float(v[30])
        except Exception as e:
            print(e)
            pass


@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str = ''
    exchange: Exchange = Exchange.SHFE
    datetime: datetime = datetime(2019, 1, 1)

    interval: Interval = None
    volume: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    adj_close_price: float = 0.0
    open_interest: int = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.full_symbol = generate_full_symbol(self.exchange, self.symbol)
        self.bar_start_time = pd.Timestamp(self.datetime)


@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status 
    of a specific order.
    """

    symbol: str = ""
    exchange: Exchange = Exchange.SHFE
    orderid: str = ""

    type: OrderType = OrderType.LMT
    direction: Direction = Direction.LONG
    offset: Offset = Offset.NONE
    price: float = 0
    volume: int = 0
    traded: int = 0
    status: Status = Status.SUBMITTING
    time: str = ""

# StarQuant unique field
    api: str = ""
    account: str = ""
    clientID: int = -1
    client_order_id: int = -1
    tag: str = ""

    full_symbol: str = ""
    flag: OrderFlag = OrderFlag.OPEN
    server_order_id: int = -1
    broker_order_id: int = -1
    orderNo: str = ""
    localNo: str = ""
    create_time: str = ""
    update_time: str = ""
    orders_status: OrderStatus = OrderStatus.SUBMITTED
    orderfield: Any = None

    def __post_init__(self):
        """"""
        if self.full_symbol:
            self.symbol, self.exchange = extract_full_symbol(self.full_symbol)
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.tag = str(self.type.value)

    def is_active(self):
        """
        Check if the order is active.
        """
        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

    def create_cancel_request(self):
        """
        Create cancel request object from order.
        """
        req = CancelRequest(
            clientID=self.clientID,
            client_order_id=self.client_order_id,
            server_order_id=self.server_order_id
        )
        return req

    def deserialize(self, msg: str):
        v = msg.split('|')
        try:
            self.api = v[0]
            self.account = v[1]
            self.clientID = int(v[2])
            self.client_order_id = int(v[3])
            self.tag = v[4]
            self.type = OrderType(int(v[4].split(':')[0]))
            self.full_symbol = v[5]
            self.symbol, self.exchange = extract_full_symbol(self.full_symbol)
            self.vt_symbol = generate_vt_symbol(self.symbol, self.exchange)
            self.price = float(v[6])
            self.volume = int(v[7])
            if self.volume < 0:
                self.direction = Direction.SHORT
                self.volume = -1 * self.volume
            self.traded = abs(int(v[8]))
            self.flag = OrderFlag(int(v[9]))
            self.offset = ORDERFALG_2VT[self.flag]
            self.server_order_id = int(v[10])
            self.broker_order_id = int(v[11])
            self.orderNo = v[12]
            self.localNo = v[13]
            self.orderid = self.localNo
            self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
            self.create_time = v[14]
            self.update_time = v[15]
            self.time = self.update_time
            self.order_status = OrderStatus(int(v[16]))
            self.status = ORDERSTATUS_2VT[self.order_status]
        except Exception as e:
            print(e)
            pass

    def serialize(self):
        msg = str(self.api
                  + '|' + self.account
                  + '|' + str(self.clientID)
                  + '|' + str(self.client_order_id)
                  + '|' + self.tag)
        if (self.orderfield):
            msg = msg + '|' + self.orderfield.serialize()
        return msg


@dataclass
class CtpOrderField(object):

    InstrumentID: str = ''
    OrderPriceType: str = ''
    Direction: str = ''
    CombOffsetFlag: str = ''
    CombHedgeFlag: str = ''
    LimitPrice: float = 0.0
    VolumeTotalOriginal: int = 0
    TimeCondition: str = ''
    GTDDate: str = ''
    VolumeCondition: str = ''
    MinVolume: int = 0
    ContingentCondition: str = ''
    StopPrice: float = 0.0
    ForceCloseReason: str = '0'
    IsAutoSuspend: int = 0
    UserForceClose: int = 0
    IsSwapOrder: int = 0
    BusinessUnit: str = ''
    CurrencyID: str = ''

    def serialize(self):
        msg = str(self.InstrumentID
                  + '|' + self.OrderPriceType
                  + '|' + self.Direction
                  + '|' + self.CombOffsetFlag
                  + '|' + self.CombHedgeFlag
                  + '|' + str(self.LimitPrice)
                  + '|' + str(self.VolumeTotalOriginal)
                  + '|' + self.TimeCondition
                  + '|' + self.GTDDate
                  + '|' + self.VolumeCondition
                  + '|' + str(self.MinVolume)
                  + '|' + self.ContingentCondition
                  + '|' + str(self.StopPrice)
                  + '|' + self.ForceCloseReason
                  + '|' + str(self.IsAutoSuspend)
                  + '|' + str(self.UserForceClose)
                  + '|' + str(self.IsSwapOrder)
                  + '|' + self.BusinessUnit
                  + '|' + self.CurrencyID)
        return msg


@dataclass
class PaperOrderField(object):

    order_type: OrderType = OrderType.MKT
    full_symbol: str = ''
    order_flag: OrderFlag = OrderFlag.OPEN
    limit_price: float = 0.0
    stop_price: float = 0.0
    order_size: int = 0

    def serialize(self):
        msg = str(str(self.order_type.value)
                  + '|' + self.full_symbol
                  + '|' + str(self.order_flag.value)
                  + '|' + str(self.order_size)
                  + '|' + str(self.limit_price)
                  + '|' + str(self.stop_price))
        return msg


@dataclass
class TradeData(BaseData):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str = ""
    exchange: Exchange = Exchange.SHFE
    orderid: str = ""
    tradeid: str = ""
    direction: Direction = ""

    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    time: str = ""

# StarQuant field
    server_order_id: int = -1
    client_order_id: int = -1
    clientID: int = -1
    localNo: str = ""
    orderNo: str = ""
    full_symbol: str = ""
    fill_flag: OrderFlag = OrderFlag.OPEN
    commission: float = 0.0
    account: str = ""
    api: str = ""

    datetime: datetime = datetime(1990, 1, 1)

# Backtest use
    commission: float = 0.0
    slippage: float = 0.0
    turnover: float = 0.0
    long_pos: int = 0
    long_price: float = 0
    long_pnl: float = 0
    short_pos: int = 0
    short_price: float = 0
    short_pnl: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"

    def deserialize(self, msg: str):
        v = msg.split('|')
        try:
            self.server_order_id = int(v[0])
            self.client_order_id = int(v[1])
            self.clientID = int(v[2])
            self.localNo = v[3]
            self.orderid = self.localNo
            self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
            self.orderNo = v[4]
            self.tradeid = v[5]
            self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"
            self.time = v[6]
            self.full_symbol = v[7]
            self.symbol, self.exchange = extract_full_symbol(self.full_symbol)
            self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

            self.price = float(v[8])
            quantity = int(v[9])
            self.volume = abs(quantity)
            self.direction = Direction.LONG if quantity > 0 else Direction.SHORT
            self.fill_flag = OrderFlag(int(v[10]))
            self.offset = ORDERFALG_2VT[self.fill_flag]

            self.commission = float(v[11])
            self.account = v[12]
            self.api = v[13]
        except Exception as e:
            print(e)
            pass


@dataclass
class PositionData(BaseData):
    """
    Positon data is used for tracking each individual position holding.
    """

    symbol: str = ""
    exchange: Exchange = Exchange.SHFE
    direction: Direction = Direction.LONG

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0
# StarQuant field
    key: str = ""
    account: str = ""
    api: str = ""
    full_symbol: str = ""
    realized_pnl: float = 0
    timestamp: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid = f"{self.vt_symbol}.{self.direction}"

    def deserialize(self, msg: str):
        v = msg.split('|')
        try:
            self.key = v[0]
            self.account = v[1]
            self.api = v[2]
            self.full_symbol = v[3]
            self.symbol, self.exchange = extract_full_symbol(self.full_symbol)
            self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
            self.direction = DIRECTION_CTP2VT[v[4]]
            self.price = float(v[5])
            self.vt_positionid = f"{self.vt_symbol}.{self.direction}"
            self.volume = abs(int(v[6]))
            self.yd_volume = abs(int(v[7]))
            self.freezed_size = abs(int(v[8]))
            self.realized_pnl = float(v[9])
            self.pnl = float(v[10])
            self.timestamp = v[11]
        except Exception as e:
            print(e)
            pass


BacktestTradeData = TradeData


@dataclass
class AccountData(BaseData):
    """
    Account data contains information about balance, frozen and
    available.
    """

    accountid: str = ""

    balance: float = 0
    frozen: float = 0
# StarQuant field

    yd_balance: float = 0
    netliquid: float = 0
    commission: float = 0
    margin: float = 0
    closed_pnl: float = 0
    open_pnl: float = 0
    timestamp: str = ""

    def __post_init__(self):
        """"""
        self.available = self.balance - self.frozen
        self.vt_accountid = f"{self.gateway_name}.{self.accountid}"

    def deserialize(self, msg: str):
        v = msg.split('|')
        try:
            self.accountid = v[0]
            self.vt_accountid = f"{self.gateway_name}.{self.accountid}"
            self.yd_balance = float(v[1])
            self.netliquid = float(v[2])
            self.available = float(v[3])
            self.commission = float(v[4])
            self.margin = float(v[5])
            self.closed_pnl = float(v[6])
            self.open_pnl = float(v[7])
            self.balance = float(v[8])
            self.frozen = float(v[9])
            self.timestamp = v[10]
        except Exception as e:
            print(e)
            pass


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str = ''
    level: int = INFO
# StarQuant field
    timestamp: str = ''

    def __post_init__(self):
        """"""
        self.time = datetime.now()

    def deserialize(self, msg: str):
        v = msg.split('|')
        try:
            self.msg = v[0]
            self.timestamp = v[1]
        except Exception as e:
            print(e)
            pass


@dataclass
class ContractData(BaseData):
    """
    Contract data contains basic information about each contract traded.
    """

    symbol: str = ""
    exchange: Exchange = Exchange.SHFE
    name: str = ""
    product: Product = Product.FUTURES
    size: int = 1
    pricetick: float = 0

    min_volume: float = 1           # minimum trading volume of the contract
    stop_supported: bool = False    # whether server supports stop order
    net_position: bool = False      # whether gateway uses net position volume

    option_strike: float = 0
    option_underlying: str = ""     # vt_symbol of underlying contract
    option_type: OptionType = None
    option_expiry: datetime = None

    # StarQuant field
    full_symbol: str = ""
    long_margin_ratio: float = 0
    short_margin_ratio: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

    def deserialize(self, msg: str):
        v = msg.split('|')
        try:
            self.symbol = v[0]
            self.exchange = EXCHANGE_CTP2VT[v[1]]
            self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
            self.name = v[2]
            self.product = PRODUCT_CTP2VT.get(v[3], None)
            st = PRODUCT_VT2SQ[self.product]
            self.full_symbol = generate_full_symbol(
                self.exchange, self.symbol, st)
            self.size = int(v[4])
            self.pricetick = float(v[5])
            if v[6] == THOST_FTDC_PT_Net:
                self.net_position = True
            self.long_margin_ratio = float(v[7])
            self.short_margin_ratio = float(v[8])
            if self.product == Product.OPTION:
                self.option_underlying = v[9]
                self.option_type = OPTIONTYPE_CTP2VT.get(v[10], None)
                self.option_strike = float(v[11])
                self.option_expiry = datetime.strptime(v[12], "%Y%m%d")
        except Exception as e:
            print(e)
            pass

# product = PRODUCT_CTP2VT.get(data["ProductClass"], None)
# if product:
# OPTIONTYPE_CTP2VT.get(data["OptionsType"], None),


@dataclass
class StopOrder:
    full_symbol: str
    direction: Direction
    offset: Offset
    price: float
    volume: float
    stop_orderid: str
    strategy_name: str
    lock: bool = False
    vt_orderids: list = field(default_factory=list)
    status: StopOrderStatus = StopOrderStatus.WAITING


@dataclass
class QryContractRequest:
    """
    qry security
    """
    sym_type: SYMBOL_TYPE = SYMBOL_TYPE.FULL
    content: str = ''

    def serialize(self):
        msg = str(self.sym_type.value) + '|' + self.content
        return msg


@dataclass
class SubscribeRequest:
    """
    subscribe
    """
    sym_type: SYMBOL_TYPE = SYMBOL_TYPE.FULL
    content: str = ''

    def serialize(self):
        msg = str(self.sym_type.value) + '|' + self.content
        return msg


@dataclass
class CancelRequest:
    """
    Request sending to specific gateway for canceling an existing order.
    """
    clientID: int = 0
    client_order_id: int = 0
    server_order_id: int = 0

    def serialize(self):
        msg = str(self.clientID) + '|' + str(self.client_order_id) + \
            '|' + str(self.server_order_id)
        return msg


OrderRequest = OrderData
CancelAllRequest = SubscribeRequest


@dataclass
class HistoryRequest:
    """
    Request sending to specific gateway for querying history data.
    """

    symbol: str
    exchange: Exchange
    start: datetime
    end: datetime = None
    interval: Interval = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
