#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
from enum import Enum
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from logging import INFO
from typing import Any, Callable

from .constant import *
from ..api.ctp_constant import THOST_FTDC_PT_Net
from .utility import generate_full_symbol,extract_full_symbol,generate_vt_symbol

def retrieve_multiplier_from_full_symbol(symbol = ""):
    return 1.0

# ################### Begin base class definitions##################
class Event(object):
    """
    Base Event class for event-driven system
    """
    def __init__(self,
        type:EventType = EventType.HEADER,
        data:Any = None,
        des:str = '',
        src:str = '',
        msgtype:MSG_TYPE = MSG_TYPE.MSG_TYPE_BASE
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
        msg = self.destination + '|' + self.source + '|' + str(self.msg_type.value)
        if self.data:
            if type(self.data) == str:
                msg = msg + '|' +self.data
            else:
                try:
                    msg = msg + '|' + self.data.serialize()
                except:
                    pass
        return msg

    def deserialize(self,msg:str):        
        v = msg.split('|',3)
        try:
            self.destination = v[0]
            self.source = v[1]
            msg2type = MSG_TYPE(int(v[2]))
            if msg2type in [MSG_TYPE.MSG_TYPE_TICK,MSG_TYPE.MSG_TYPE_TICK_L1,MSG_TYPE.MSG_TYPE_TICK_L5]:
                self.event_type = EventType.TICK
                self.data = TickData(gateway_name = self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RTN_ORDER:
                self.event_type = EventType.ORDERSTATUS
                self.data = OrderData(gateway_name = self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RTN_TRADE:
                self.event_type = EventType.FILL
                self.data = TradeData(gateway_name = self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RSP_POS:
                self.event_type = EventType.POSITION
                self.data = PositionData(gateway_name = self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_BAR:
                self.event_type = EventType.BAR
                self.data = BarData(gateway_name = self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RSP_ACCOUNT:
                self.event_type = EventType.ACCOUNT
                self.data = AccountData(gateway_name = self.source)
                self.data.deserialize(v[3])
            elif msg2type == MSG_TYPE.MSG_TYPE_RSP_CONTRACT:
                self.event_type = EventType.CONTRACT
                self.data = ContractData(gateway_name = self.source)
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
            elif v[2].startswith('3') :           #msg2type == MSG_TYPE.MSG_TYPE_INFO:
                self.event_type = EventType.INFO
                self.msg_type = msg2type
                self.data = LogData(gateway_name = self.source)
                self.data.deserialize(v[3])                    
            else:
                self.event_type = EventType.HEADER
                self.msg_type = msg2type
        except:
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
    def deserialize(self,msg):
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
    datetime: datetime = datetime(2019,1,1)

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
    depth :int = 0  
    open_interest:float = 0


    def __post_init__(self):
        """"""

        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.timestamp = Timestamp(self.datetime) 
        self.full_symbol = generate_full_symbol(self.exchange,self.symbol)

    
    def deserialize(self,msg:str):
        try:
            v = msg.split('|')
            self.full_symbol = v[0]  
            self.timestamp = pd.to_datetime(v[1])
            self.datetime = self.timestamp.to_pydatetime()
            self.symbol, self.exchange = extract_full_symbol(self.full_symbol)
            self.vt_symbol = generate_vt_symbol(self.symbol,self.exchange)
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
        except:
            pass


@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str = ''
    exchange: Exchange = Exchange.SHFE
    datetime: datetime = datetime(2019,1,1)

    interval: Interval = None
    volume: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0
    
    adj_close_price :float = 0.0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.full_symbol = generate_full_symbol(self.exchange,self.symbol)
        self.bar_start_time = pd.Timestamp(self.datetime)
    



@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status 
    of a specific order.
    """

    symbol: str =""
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
    api : str = ""
    account : str = ""
    clientID : int = -1
    client_order_id : int  = -1
    tag : str = ""
    
    full_symbol :str = ""
    flag : OrderFlag = OrderFlag.OPEN
    server_order_id : int = -1
    broker_order_id : int = -1
    orderNo : str = ""
    localNo : str = ""
    create_time : str = ""
    update_time : str = ""
    orders_status: OrderStatus = OrderStatus.SUBMITTED
    orderfield :Any = None

    def __post_init__(self):
        """"""
        if self.full_symbol:
            self.symbol,self.exchange = extract_full_symbol(self.full_symbol)
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
            clientID=self.clientID, client_order_id =self.client_order_id, server_order_id=self.server_order_id
        )
        return req
    def deserialize(self,msg:str):
        v = msg.split('|')
        try:
            self.api = v[0]
            self.account = v[1]
            self.clientID = int(v[2])
            self.client_order_id = int(v[3])
            self.tag = v[4]             
            self.type = OrderType(int(v[4].split(':')[0]))
            self.full_symbol =  v[5]
            self.symbol,self.exchange = extract_full_symbol(self.full_symbol)
            self.vt_symbol = generate_vt_symbol(self.symbol,self.exchange)
            self.price = float(v[6])
            self.volume = int(v[7])
            if self.volume <0:
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
        except:
            pass

    def serialize(self):
        msg = str( self.api 
            + '|' + self.account 
            + '|' + str(self.clientID)
            + '|' + str(self.client_order_id)
            + '|' + self.tag)
        if (self.orderfield):
            msg = msg + '|' + self.orderfield.serialize()
        return msg   
@dataclass
class CtpOrderField(object):

    InstrumentID :str = ''
    OrderPriceType :str = ''
    Direction :str = ''
    CombOffsetFlag:str = ''
    CombHedgeFlag : str = ''
    LimitPrice : float = 0.0
    VolumeTotalOriginal : int = 0
    TimeCondition :str = ''
    GTDDate :str = ''
    VolumeCondition :str = ''
    MinVolume :int = 0
    ContingentCondition :str = ''
    StopPrice :float = 0.0
    ForceCloseReason :str = '0'
    IsAutoSuspend :int = 0
    UserForceClose :int = 0
    IsSwapOrder :int = 0
    BusinessUnit :str = ''
    CurrencyID :str = ''

    def serialize(self):
        msg = str( self.InstrumentID  
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
            + '|' + self.CurrencyID )
        return msg 

@dataclass            
class PaperOrderField(object):

    order_type : OrderType = OrderType.MKT
    full_symbol :str = ''
    order_flag : OrderFlag = OrderFlag.OPEN
    limit_price :float = 0.0
    stop_price :float = 0.0
    order_size :int = 0

    def serialize(self):
        msg = str( str(self.order_type.value)  
            + '|' + self.full_symbol
            + '|' + str(self.order_flag.value)
            + '|' + str(self.order_size)
            + '|' + str(self.limit_price)
            + '|' + str(self.stop_price) )
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
    server_order_id : int  = -1
    client_order_id : int  = -1
    clientID : int = -1
    localNo : str = ""
    orderNo : str  = ""
    full_symbol : str = ""
    fill_flag : OrderFlag = OrderFlag.OPEN
    commission : float = 0.0
    account : str  = ""
    api :str  = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"
    
    def deserialize(self,msg:str):
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
            self.symbol,self.exchange = extract_full_symbol(self.full_symbol)
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
        except:
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
    key : str = ""
    account : str = ""
    api : str = ""
    full_symbol : str = ""
    realized_pnl : float = 0
    timestamp : str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid = f"{self.vt_symbol}.{self.direction}"

    def deserialize(self,msg:str):
        v = msg.split('|')
        try:
            self.key = v[0]
            self.account = v[1]
            self.api = v[2]
            self.full_symbol = v[3]
            self.symbol,self.exchange = extract_full_symbol(self.full_symbol)
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
        except:
            pass

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
    
    yd_balance : float = 0
    netliquid : float = 0
    commission : float = 0
    margin : float = 0
    closed_pnl : float = 0
    open_pnl : float = 0
    timestamp : str = ""

    def __post_init__(self):
        """"""
        self.available = self.balance - self.frozen
        self.vt_accountid = f"{self.gateway_name}.{self.accountid}"

    def deserialize(self,msg:str):
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
        except:
            pass


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str = ''
    level: int = INFO
# StarQuant field 
    timestamp :str = ''
    def __post_init__(self):
        """"""
        self.time = datetime.now()    

    def deserialize(self, msg:str):
        v = msg.split('|')
        try:
            self.msg = v[0]
            self.timestamp = v[1]
        except:
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
    full_symbol : str = ""
    long_margin_ratio :float = 0
    short_margin_ratio:float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

    def deserialize(self,msg:str):
        v = msg.split('|')
        try:
            self.symbol = v[0]
            self.exchange = EXCHANGE_CTP2VT[v[1]]
            self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
            self.name = v[2]
            self.product = PRODUCT_CTP2VT.get(v[3],None)
            st = PRODUCT_VT2SQ[self.product]
            self.full_symbol = generate_full_symbol(self.exchange,self.symbol,st)
            self.size = int(v[4])
            self.pricetick = float(v[5])
            if v[6] == THOST_FTDC_PT_Net:
                self.net_position = True
            self.long_margin_ratio = float(v[7])
            self.short_margin_ratio = float(v[8]) 
            if  self.product == Product.OPTION:
                self.option_underlying = v[9]
                self.option_type = OPTIONTYPE_CTP2VT.get(v[10], None)
                self.option_strike = float(v[11])
                self.option_expiry = datetime.strptime(v[12],"%Y%m%d")
        except:
            pass

# product = PRODUCT_CTP2VT.get(data["ProductClass"], None)
# if product:
# OPTIONTYPE_CTP2VT.get(data["OptionsType"], None),








class Position(object):
    def __init__(self, full_symbol, average_price=0, size=0, realized_pnl=0):
        """
        Position includes zero/closed security
        """
        ## TODO: add cumulative_commission, long_trades, short_trades, round_trip etc
        self.full_symbol = full_symbol
        # average price includes commission
        self.average_price = average_price
        self.avg_buy_price = 0
        self.avg_sell_price = 0
        self.size = size
        self.buy_quantity = 0            #多头仓位
        self.sell_quantity = 0           #空头仓位
        self.realized_pnl = 0          #平仓盈亏
        self.unrealized_pnl = 0        #浮盈
        self.buy_realized_pnl = 0
        self.sell_realized_pnl = 0
        self.buy_unrealized_pnl = 0
        self.sell_unrealized_pnl = 0
        self.last_realized_pnl =0 
        self.api = ''
        self.account = ''
        self.posno =''
        self.openorderNo = ''
        self.openapi = ''
        self.opensource = -1
        self.closeorderNo = ''
        self.closeapi = ''
        self.closesource = -1

    def mark_to_market(self, last_price):
        """
        given new market price, update the position
        """
        # if long or size > 0, pnl is positive if last_price > average_price
        # else if short or size < 0, pnl is positive if last_price < average_price
        self.buy_unrealized_pnl = (last_price - self.avg_buy_price) * self.buy_quantity \
                              * retrieve_multiplier_from_full_symbol(self.full_symbol)
        self.sell_unrealized_pnl = -1*(last_price - self.avg_sell_price) * self.sell_quantity \
                              * retrieve_multiplier_from_full_symbol(self.full_symbol)
        self.unrealized_pnl = self.buy_unrealized_pnl +self.sell_unrealized_pnl

    def on_fill(self, fill_event):
        """
        adjust average_price and size according to new fill/trade/transaction
        """
        if self.full_symbol != fill_event.full_symbol:
            print(
                "Position symbol %s and fill event symbol %s do not match. "
                % (self.full_symbol, fill_event.full_symbol)
            )
            return

        # if self.size > 0:        # existing long
        #     if fill_event.fill_size > 0:        # long more
        #         self.average_price = (self.average_price * self.size + fill_event.fill_price * fill_event.fill_size
        #                               + fill_event.commission / retrieve_multiplier_from_full_symbol(self.full_symbol)) \
        #                              / (self.size + fill_event.fill_size)
        #     else:        # flat long
        #         if abs(self.size) >= abs(fill_event.fill_size):   # stay long
        #             self.realized_pnl += (self.average_price - fill_event.fill_price) * fill_event.fill_size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #         else:   # flip to short
        #             self.realized_pnl += (fill_event.fill_price - self.average_price) * self.size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #             self.average_price = fill_event.fill_price
        # else:        # existing short
        #     if fill_event.fill_size < 0:         # short more
        #         self.average_price = (self.average_price * self.size + fill_event.fill_price * fill_event.fill_size
        #                               + fill_event.commission / retrieve_multiplier_from_full_symbol(self.full_symbol)) \
        #                              / (self.size + fill_event.fill_size)
        #     else:          # flat short
        #         if abs(self.size) >= abs(fill_event.fill_size):  # stay short
        #             self.realized_pnl += (self.average_price - fill_event.fill_price) * fill_event.fill_size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #         else:   # flip to long
        #             self.realized_pnl += (fill_event.fill_price - self.average_price) * self.size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #             self.average_price = fill_event.fill_price

        # self.size += fill_event.fill_size
        if fill_event.fill_size > 0 :
            if  fill_event.fill_flag == OrderFlag.OPEN :  # buy open
                self.avg_buy_price = (self.avg_buy_price * self.buy_quantity + fill_event.fill_price * fill_event.fill_size) \
                                    / (self.buy_quantity + fill_event.fill_size)
                self.buy_quantity += fill_event.fill_size
                print('开多仓 ：',fill_event.fill_price,fill_event.fill_size)
                print('当前多仓数量 ：', self.buy_quantity, '持仓价格',self.avg_buy_price)
            else:# buy close
                if self.sell_quantity >= fill_event.fill_size : 
                    tmp = (self.avg_sell_price - fill_event.fill_price) * fill_event.fill_size \
                                          * retrieve_multiplier_from_full_symbol(self.full_symbol)   
                    self.sell_realized_pnl += tmp                    
                    self.last_realized_pnl = tmp
                    print('平空仓盈亏：',tmp)
                    self.sell_quantity -= fill_event.fill_size
                else:  
                    print(" error: fill buy close size >sell postion size") 
        else:
            if  fill_event.fill_flag == OrderFlag.OPEN :  # sell open
                self.avg_sell_price = (self.avg_sell_price * self.sell_quantity - fill_event.fill_price * fill_event.fill_size) \
                                    / (self.sell_quantity - fill_event.fill_size)
                self.sell_quantity -= fill_event.fill_size
                print('开空仓 ：',fill_event.fill_price,fill_event.fill_size)
                print('当前空仓数量：',self.sell_quantity,'持仓价格''',self.avg_sell_price)               
            else: # sell close
                if self.buy_quantity >= abs(fill_event.fill_size) :
                    tmp =  (self.avg_buy_price - fill_event.fill_price) * fill_event.fill_size \
                                        * retrieve_multiplier_from_full_symbol(self.full_symbol) 
                    self.buy_realized_pnl += tmp
                    self.last_realized_pnl = tmp
                    print('平多仓盈亏：',tmp)
                    self.buy_quantity += fill_event.fill_size
                else:  
                    print(" error: fill sell close size >buy postion size")             
        self.realized_pnl = self.buy_realized_pnl + self.sell_realized_pnl

    def withdrawcash(self,ratio=1.0):
        tmp = self.realized_pnl*ratio
        self.realized_pnl =(1-ratio) * self.realized_pnl
        return tmp



class AccountEvent(Event):
    """
    also serve as account
    """
    def __init__(self):
        self.event_type = EventType.ACCOUNT
        self.account_id = ''
        self.preday_balance = 0.0
        self.balance = 0.0
        self.available = 0.0
        self.commission = 0.0
        self.margin = 0.0
        self.closed_pnl = 0.0
        self.open_pnl = 0.0
        self.timestamp = ''

    def deserialize(self, msg):
        v = msg.split('|')
        self.destination = v[0]
        self.source = v[1]
        self.account_id = v[3]
        self.preday_balance = float(v[4])
        self.balance = float(v[5])
        self.available = float(v[6])
        self.commission = float(v[7])
        self.margin = float(v[8])
        self.closed_pnl = float(v[9])
        self.open_pnl = float(v[10])        
        self.timestamp = v[11]
        
class ContractEvent(Event):
    """
    also serve as contract
    """
    def __init__(self):
        self.event_type = EventType.CONTRACT
        self.full_symbol = ''
        self.local_name = ''
        self.mininum_tick = 0.0
        self.mulitples = 1

    def deserialize(self, msg):
        v = msg.split('|')
        self.full_symbol = v[3]
        self.mininum_tick = float(v[4])
        self.mulitples = int(v[5])

class BarEvent(Event):
    """
    Bar event, aggregated from TickEvent
    """
    def __init__(self):
        """
        Initialises bar
        """
        self.event_type = EventType.BAR
        self.bar_start_time = pd.Timestamp('1970-01-01', tz='UTC')
        self.latestime = pd.Timestamp('1970-01-01', tz='UTC')
        self.interval = 86400       # 1day in secs = 24hrs * 60min * 60sec
        self.full_symbol = ''
        self.open_price = 0.0
        self.high_price = 0.0
        self.low_price = 0.0
        self.close_price = 0.0
        self.adj_close_price = 0.0
        self.volume = 0

    def bar_end_time(self):
        # To be consistent with (daily) bar backtest, bar_end_time is set to be bar_start_time
        return self.bar_start_time
        # return self.bar_start_time + pd.Timedelta(seconds=self.interval)

    def __str__(self):
        return "Time: %s, Symbol: %s, Interval: %s, " \
            "Open: %s, High: %s, Low: %s, Close: %s, " \
            "Adj Close: %s, Volume: %s" % (
                str(self.bar_start_time), str(self.full_symbol), str(self.interval),
                str(self.open_price), str(self.high_price), str(self.low_price),
                str(self.close_price), str(self.adj_close_price), str(self.volume)
            )

class TickEvent(Event):
    """
    Tick event
    """

    def __init__(self):
        """
        Initialises Tick
        """
        self.event_type = EventType.TICK
        self.tick_type = TickType.Trade

        self.timestamp = Timestamp('1970-01-01', tz='UTC')
        self.full_symbol = ''
        self.price = 0.0
        self.size = 0
        self.depth = 1

        self.bid_price_L1 = 0.0
        self.bid_size_L1 = 0
        self.ask_price_L1 = 0.0
        self.ask_size_L1 = 0
        self.bid_price_L2 = 0.0
        self.bid_size_L2 = 0
        self.ask_price_L2 = 0.0
        self.ask_size_L2 = 0
        self.bid_price_L3 = 0.0
        self.bid_size_L3 = 0
        self.ask_price_L3 = 0.0
        self.ask_size_L3 = 0
        self.bid_price_L4 = 0.0
        self.bid_size_L4 = 0
        self.ask_price_L4 = 0.0
        self.ask_size_L4 = 0
        self.bid_price_L5 = 0.0
        self.bid_size_L5 = 0
        self.ask_price_L5 = 0.0
        self.ask_size_L5 = 0

        self.open_interest = 0
        self.open = 0.0
        self.high = 0.0
        self.low = 0.0
        self.pre_close = 0.0
        self.upper_limit_price = 0.0
        self.lower_limit_price = 0.0
        self.totalq = 0.0
        self.position =0.0
        self.bors = ''
    def deserialize(self, msg):
        # print('begin deserial tick')
        try:
            v = msg.split('|')
            self.destination = v[0]
            self.source = v[1]
            self.tick_type = TickType(int(v[2]))
            # print('tick type',self.tick_type,self.tick_type == TickType.Tick_L1)
            self.full_symbol = v[3]
            #self.timestamp = time.mktime(time.strptime(v[1],'%Y-%m-%d %H:%M:%S.%f'))
            self.timestamp =pd.to_datetime(v[4])
            self.price = float(v[5])
            self.size = int(v[6])

            if (self.tick_type == TickType.Tick_L1):
                # print('tickl1 deserialize')
                self.depth = 1
                self.bid_price_L1 = float(v[7])
                self.bid_size_L1 = int(v[8])
                self.ask_price_L1 = float(v[9])
                self.ask_size_L1 = int(v[10])
                self.open_interest = int(v[11])
                self.open = float(v[12])
                self.high = float(v[13])
                self.low = float(v[14])
                self.pre_close = float(v[15])
                self.upper_limit_price = float(v[16])
                self.lower_limit_price = float(v[17])                
            elif (self.tick_type == TickType.Tick_L5):
                self.depth = 5
                self.bid_price_L1 = float(v[7])
                self.bid_size_L1 = int(v[8])
                self.ask_price_L1 = float(v[9])
                self.ask_size_L1 = int(v[10])
                self.bid_price_L2 = float(v[11])
                self.bid_size_L2 = int(v[12])
                self.ask_price_L2 = float(v[13])
                self.ask_size_L2 = int(v[14])
                self.bid_price_L3 = float(v[15])
                self.bid_size_L3 = int(v[16])
                self.ask_price_L3 = float(v[17])
                self.ask_size_L3 = int(v[18])
                self.bid_price_L4 = float(v[19])
                self.bid_size_L4 = int(v[20])
                self.ask_price_L4 = float(v[21])
                self.ask_size_L4 = int(v[22])
                self.bid_price_L5 = float(v[23])
                self.bid_size_L5 = int(v[24])
                self.ask_price_L5 = float(v[25])
                self.ask_size_L5 = int(v[26])
                self.open_interest = int(v[27])
                self.open = float(v[28])
                self.high = float(v[29])
                self.low = float(v[30])
                self.pre_close = float(v[31])
                self.upper_limit_price = float(v[32])
                self.lower_limit_price = float(v[33])
        except:
            pass

    def __str__(self):
        return "Time: %s, Ticker: %s, Type: %s,  Price: %s, Size %s" % (
            str(self.timestamp), str(self.full_symbol), (self.tick_type),
            str(self.price), str(self.size)
        )

class HistoricalEvent(Event):
    """
    Bar event, aggregated from TickEvent
    """
    def __init__(self):
        """
        Initialises bar
        """
        self.event_type = EventType.HISTORICAL
        self.bar_start_time = pd.Timestamp('1970-01-01', tz='UTC')
        self.interval = 86400       # 1day in secs = 24hrs * 60min * 60sec
        self.full_symbol = ''
        self.open_price = 0.0
        self.high_price = 0.0
        self.low_price = 0.0
        self.close_price = 0.0
        self.weighted_average_price = 0.0
        self.volume = 0
        self.count = 0           # number of trades in this bar

    def bar_end_time(self):
        # To be consistent with (daily) bar backtest, bar_end_time is set to be bar_start_time
        return self.bar_start_time
        # return self.bar_start_time + pd.Timedelta(seconds=self.interval)

    def __str__(self):
        return "Time: %s, Symbol: %s, Interval: %s, " \
            "Open: %s, High: %s, Low: %s, Close: %s, " \
            "Adj Close: %s, Volume: %s" % (
                str(self.bar_start_time), str(self.full_symbol), str(self.interval),
                str(self.open_price), str(self.high_price), str(self.low_price),
                str(self.close_price), str(self.weighted_average_price), str(self.volume)
            )

    def deserialize(self, msg):
        v = msg.split('|')
        self.full_symbol = v[1]
        self.bar_start_time = v[2]          # string
        self.open_price = float(v[3])
        self.high_price = float(v[4])
        self.low_price = float(v[5])
        self.close_price = float(v[6])
        self.volume = int(v[7])
        self.count = int(v[8])
        self.weighted_average_price = float(v[9])

class OrderEvent(Event):
    """
    Order event
    """
    
    def __init__(self):
        """
        Initialises order
        """
        self.event_type = EventType.ORDER
        self.msg_type = MSG_TYPE.MSG_TYPE_ORDER

        self.api = ''
        self.account = ''
        self.clientID = -1 
        self.client_order_id = -1
        self.tag = ''             #用于其他区分标志

        self.full_symbol =  ''
        self.price = 0.0
        self.quantity = 0
        self.flag_ = OrderFlag.OPEN
        self.server_order_id = -1
        self.broker_order_id = -1
        self.orderNo = ''        # used in tap 委托编码，服务器端唯一识别标志
        self.localNo = ''        # orderref
        self.create_time = None
        self.update_time = None
        self.order_status = OrderStatus.UNKNOWN

        self.orderfield = None
        
    def serialize(self):

        msg = str( self.destination  + '|' + self.source + '|' + str(self.msg_type.value)
            + '|' + self.api 
            + '|' + self.account 
            + '|' + str(self.clientID)
            + '|' + str(self.client_order_id)
            + '|' + self.tag)
        if (self.orderfield):
            msg = msg + '|' + self.orderfield.serialize()
        return msg

        # if self.order_type == OrderType.MKT:
        #     msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_ORDER.value) + '|' + str(self.account) + '|'+ str(self.client_order_id) + '|' \
        #           + str(OrderType.MKT.value) + '|' + self.full_symbol + '|' + str(self.order_size) + '|' + '0.0' +'|' \
        #           + str(self.order_flag.value)  + '|' + self.tag
        # elif self.order_type == OrderType.LMT:
        #     msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_ORDER.value) + '|' + str(self.account) + '|' + str(self.client_order_id) + '|' \
        #           + str(OrderType.LMT.value)+ '|' + self.full_symbol + '|' + str(self.order_size) + '|' + str(self.limit_price) + '|' \
        #           + str(self.order_flag.value) + '|' + self.tag
        # elif self.order_type == OrderType.STP:
        #     msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_ORDER.value) + '|' + str(self.account) + '|' + str(self.client_order_id) + '|' \
        #           + str(OrderType.STP.value) + '|' + self.full_symbol + '|' + str(self.order_size) + '|' + '0.0' +'|' \
        #           + str(self.order_flag.value)     + '|' + self.tag          
        # elif self.order_type == OrderType.STPLMT:
        #     msg = self.api + '|' + str(self.source) + '|' + str(MSG_TYPE.MSG_TYPE_ORDER.value) + '|' + str(self.account) + '|' + str(self.client_order_id) + '|' \
        #           + str(OrderType.STPLMT.value)+ '|' + self.full_symbol + '|' + str(self.order_size) + '|' + str(self.stop_price) + '|' \
        #           + str(self.order_flag.value) + '|' + self.tag
        # else:
        #     print("unknown order type")            
        # return msg

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

        self.api = ''
        self.account = ''
        self.clientID = -1 
        self.client_order_id = -1
        self.tag = ''             #用于其他区分标志

        self.full_symbol =  ''
        self.price = 0.0
        self.quantity = 0
        self.flag_ = OrderFlag.OPEN
        self.server_order_id = -1
        self.broker_order_id = -1
        self.orderNo = ''        # used in tap 委托编码，服务器端唯一识别标志
        self.localNo = ''        # orderref
        self.create_time = None
        self.update_time = None
        self.order_status = OrderStatus.UNKNOWN

    def deserialize(self, msg):
        v = msg.split('|')

        self.api = v[3]
        self.account = v[4]
        self.clientID = int(v[5])
        self.client_order_id = int(v[6])
        self.tag = v[7]             

        self.full_symbol =  v[8]
        self.price = float(v[9])
        self.quantity = int(v[10])
        self.flag_ = OrderFlag(int(v[11]))
        self.server_order_id = int(v[12])
        self.broker_order_id = int(v[13])
        self.orderNo = v[14]        
        self.localNo = v[15]        
        self.create_time = v[16]
        self.update_time = v[17]
        self.order_status = OrderStatus(int(v[18]))

    def to_order(self):
        o = OrderEvent()
        o.api =  self.api 
        o.account =  self.account 
        o.clientID = self.clientID  
        o.client_order_id = self.client_order_id
        o.tag = self.tag        

        o.full_symbol = self.full_symbol 
        o.price = self.price
        o.quantity = self.quantity 
        o.flag_ = self.flag_ 
        o.server_order_id = self.server_order_id 
        o.broker_order_id = self.broker_order_id
        o.orderNo = self.orderNo 
        o.localNo = self.localNo 
        o.create_time = self.create_time 
        o.update_time = self.update_time 
        o.order_status = self.order_status 

        return o

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
        self.clientID = -1
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
        self.api = 'none'   #appid 

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
        self.destination = v[0]
        self.source = v[1]
        self.server_order_id = int(v[3])
        self.client_order_id = int(v[4])
        self.clientID = int(v[5])
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


class PositionEvent(Event):
    """
    position event
    """
    def __init__(self):
        """
        Initialises order
        """
        self.event_type = EventType.POSITION
        self.key = ''
        self.account = ''
        self.api = ''        
        self.full_symbol = ''
        self.average_cost = 0.0
        self.size = 0
        self.pre_size = 0
        self.freezed_size = 0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.type = ''
        self.posno =''
        self.openorderNo = ''   
        self.openclientID = -1
        self.openapi = ''         
        self.closeorderNo = ''
        self.closeclientID = -1
        self.closeapi = ''
        self.timestamp = ''

    def deserialize(self, msg):
        v = msg.split('|')
        self.destination = v[0]
        self.source = v[1]
        self.key = v[3]
        self.account = v[4]
        self.api = v[5]
        self.full_symbol = v[6]
        self.average_cost = float(v[7])
        self.size = int(v[8])
        self.pre_size = int(v[9])
        self.freezed_size = int(v[10])
        self.realized_pnl = float(v[11])
        self.unrealized_pnl = float(v[12])
        self.timestamp = v[13]
        # self.type =v[13]     
        # self.posno = v[14]
        # self.openorderNo = v[15]
        # self.openapi = v[16]
        # self.openclientID = int(v[17])
        # self.closeorderNo = v[18]
        # self.closeclientID = int(v[19])        
        # self.closeapi = v[20]
        # self.timestamp = v[21]

    def to_position(self):

        pos = Position(self.full_symbol, self.average_cost, 0)
        pos.account = self.account
        pos.posno =self.posno
        pos.openorderNo = self.openorderNo
        pos.openapi = self.openapi
        pos.opensource = self.openclientID 
        pos.closeorderNo = self.closeorderNo
        pos.closeapi = self.closeapi
        pos.closesource = self.closeclientID
        if self.size >= 0:
            pos.buy_quantity = self.size
        else:
            pos.sell_quantity = -1* self.size
        pos.size = pos.buy_quantity + pos.sell_quantity
        pos.realized_pnl = self.realized_pnl
        pos.unrealized_pnl = self.unrealized_pnl

        return pos

class InfoEvent(Event):
    """
    General event: TODO seperate ErrorEvent
    """
    def __init__(self):
        self.event_type = EventType.INFO
        self.msg_type = MSG_TYPE.MSG_TYPE_INFO
        self.timestamp = ""
        self.content = ""

    def deserialize(self, msg):
        v = msg.split('|')
        self.destination = v[0]
        self.source = v[1]
        self.msg_type = MSG_TYPE(int(v[2]))
        
        self.content = "".join(v[3:-1])
        self.timestamp = v[-1]
class ErrorEvent(Event):
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
    def deserialize(self,msg):
        self.req = msg

# class QryAccEvent(Event):
#     """
#     qry acc
#     """
#     def __init__(self):
#         self.event_type = EventType.QRY_ACCOUNT

#     def serialize(self):
#         msg = self.destination + '|' + self.source + '|' + str(MSG_TYPE.MSG_TYPE_QRY_ACCOUNT.value)
#         return msg

# class QryPosEvent(Event):
#     """
#     qry pos
#     """
#     def __init__(self):
#         self.event_type = EventType.QRY_POS

#     def serialize(self):
#         msg = self.destination + '|' + self.source + '|' + str(MSG_TYPE.MSG_TYPE_QRY_POS.value)
#         return msg






















@dataclass
class QryContractRequest:
    """
    qry security
    """
    sym_type : SYMBOL_TYPE = SYMBOL_TYPE.FULL
    content : str = ''

    def serialize(self):
        msg = str(self.sym_type.value) + '|' + self.content
        return msg
@dataclass
class SubscribeRequest:
    """
    subscribe
    """
    sym_type : SYMBOL_TYPE = SYMBOL_TYPE.FULL
    content : str = ''    

    def serialize(self):
        msg = str(self.sym_type.value) + '|' + self.content
        return msg

@dataclass
class CancelRequest:
    """
    Request sending to specific gateway for canceling an existing order.
    """
    clientID : int = 0
    client_order_id : int = 0
    server_order_id : int = 0

    def serialize(self):
        msg = str(self.clientID) + '|' + str(self.client_order_id) + '|' + str(self.server_order_id)
        return msg        


OrderRequest = OrderData

# ############################# vnpy 's data #########################

# @dataclass
# class SubscribeRequest:
#     """
#     Request sending to specific gateway for subscribing tick data update.
#     """

#     symbol: str
#     exchange: Exchange

#     def __post_init__(self):
#         """"""
#         self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


# @dataclass
# class OrderRequest:
#     """
#     Request sending to specific gateway for creating a new order.
#     """
#     symbol: str
#     exchange: Exchange
#     direction: Direction
##     type: OrderType
#     volume: float
#     price: float = 0
#     offset: Offset = Offset.NONE

#     def __post_init__(self):
#         """"""
#         self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

#     def create_order_data(self, orderid: str, gateway_name: str):
#         """
#         Create order data from request.
#         """
#         order = OrderData(
#             symbol=self.symbol,
#             exchange=self.exchange,
#             orderid=orderid,
#             type=self.type,
#             direction=self.direction,
#             offset=self.offset,
#             price=self.price,
#             volume=self.volume,
#             gateway_name=gateway_name,
#         )
#         return order


# @dataclass
# class CancelRequest:
#     """
#     Request sending to specific gateway for canceling an existing order.
#     """

#     orderid: str
#     symbol: str
#     exchange: Exchange

#     def __post_init__(self):
#         """"""
#         self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
