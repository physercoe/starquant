#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABC, ABCMeta
from typing import Any, Callable
from copy import copy
from datetime import datetime

from pystarquant.common.constant import (
    Interval,
    OrderFlag, OrderType, Offset, Direction
)
from pystarquant.common.datastruct import (
    TickData, BarData,TBTBarData,
    OrderRequest, OrderData,
    CtpOrderField, PaperOrderField
)

from pystarquant.common.utility import extract_full_symbol, virtual,extract_product
from pystarquant.api.ctp_constant import (
    THOST_FTDC_D_Buy,
    THOST_FTDC_D_Sell,
    THOST_FTDC_OPT_LimitPrice,
    THOST_FTDC_OPT_AnyPrice,
    THOST_FTDC_OF_Open,
    THOST_FTDC_OF_Close,
    THOST_FTDC_HF_Speculation,
    THOST_FTDC_CC_Immediately,
    THOST_FTDC_TC_GFD,
    THOST_FTDC_VC_AV,
    THOST_FTDC_TC_IOC,
    THOST_FTDC_VC_CV
)


class StrategyBase(metaclass=ABCMeta):
    """
    Base strategy class

    """
    # class id and name
    ID = -1
    NAME = "base"

    # parameters and variables,for vnpy use
    author = ""
    account = ""
    api = "PAPER.TD"
    autostart = False
    parameters = ["api", "account"]
    variables = []

    def __init__(self,
                 strategy_engine: Any,
                 strategy_name: str,
                 full_symbol: str,
                 setting: dict):
        """
        initialize trategy
        :param
        :variables
        """
        self.full_symbol = full_symbol
        sym, ex = extract_full_symbol(self.full_symbol)
        self.symbol = sym
        self.strategy_engine = strategy_engine
        self.engine_id = self.strategy_engine.id
        self.strategy_name = strategy_name

        self.active = False

        self.inited = False
        self.trading = False
        self.pos = 0
        self.cost = 0
        self.last_tradetime = datetime(2020,1,1).strftime('%Y-%m-%d %H:%M:%S')

        self.long_pos = 0
        self.long_pos_frozen = 0
        self.short_pos = 0
        self.short_pos_frozen = 0
        self.long_price = 0.0
        self.short_price = 0.0
        
        # Copy a new variables list here to avoid duplicate insert when multiple 
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")
        self.variables.insert(3,"cost")
        self.variables.insert(4,"last_tradetime")

        self.update_setting(setting)
        self.add_functions()

    # used for optmization parameter filter
    def parameter_filter(self, setting):
        return True


    # used for roll optimization, result_values is list of (setting, balancedf)
    # should return one (setting, balancedf)
    def roll_choose(self, result_values: list, begindate, enddate):
        return result_values[0]



    def add_functions(self):
        self.get_position_holding = self.strategy_engine.get_position_holding
        self.get_account = self.strategy_engine.get_account
        self.get_order = self.strategy_engine.get_order
        self.get_tick = self.strategy_engine.get_tick
        self.get_trade = self.strategy_engine.get_trade
        self.get_position = self.strategy_engine.get_position
        self.get_contract = self.strategy_engine.get_contract
        self.get_all_active_orders = self.strategy_engine.get_all_active_orders

    def get_my_active_orderids(self):
        oidset = self.strategy_engine.get_strategy_active_orderids(
            self.strategy_name)
        return oidset

    def get_my_position_holding(self, full_symbol: str = ''):
        fullsym = full_symbol
        if not fullsym:
            fullsym = self.full_symbol
        holding = self.get_position_holding(self.account, fullsym)
        self.long_pos = holding.long_pos
        self.long_pos_frozen = holding.long_pos_frozen
        self.short_pos = holding.short_pos
        self.short_pos_frozen = holding.short_pos_frozen
        self.long_price = holding.long_price
        self.short_price = holding.short_price

    def update_setting(self, setting: dict):
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of strategy class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        strategy_parameters = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self):
        """
        Get strategy variables dict.
        """
        strategy_variables = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self):
        """
        Get strategy data.
        """
        strategy_data = {
            "engine_id": self.engine_id,
            "strategy_name": self.strategy_name,
            "full_symbol": self.full_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    @virtual
    def on_init(self, params_dict=None):
        pass

    @virtual
    def on_start(self):
        self.active = True

    @virtual
    def on_stop(self):
        self.active = False

    @virtual
    def on_reset(self):
        pass

    @virtual
    def on_tick(self, tick):
        """
        Respond to tick
        """
        pass

    @virtual
    def on_bar(self, bar):
        """
        Respond to bar
        """
        pass

    @virtual
    def on_order_status(self, order):
        """
        on order acknowledged
        :return:
        """
        #raise NotImplementedError("Should implement on_order()")
        pass

    @virtual
    def on_order(self, order):
        """
        on order 
        :return:
        """
        self.on_order_status(order)

    @virtual
    def on_cancel(self, event):
        """
        on order canceled
        :return:
        """
        pass

    @virtual
    def on_fill(self, trade):
        """
        on order filled
        :return:
        """

        pass

    def on_trade(self, trade):
        self.on_fill(trade)

    @virtual
    def on_pos(self, position):
        pass

    @virtual
    def on_acc(self, acc):
        pass

    @virtual
    def on_contract(self, contract):
        pass

    @virtual
    def on_info(self, info):
        pass

    @virtual
    def on_req(self, req):
        pass

    @virtual
    def on_headermsg(self, event):
        pass

    @virtual
    def on_stop_order(self, stop_order):
        """
        Callback of stop order update.
        """
        pass

    @virtual
    def on_finish(self):
        """
        Callback of backtest finish, i.e. before last data
        """
        pass

    def cancel_order(self, oid):
        if self.trading:
            self.strategy_engine.cancel_order(self, oid)


    def cancel_all(self,full_symbol:str = ''):
        """
        cancel all/specific full_symbol standing orders from this strategy 

        """
        if self.trading:
            self.strategy_engine.cancel_all(self,full_symbol)


# wrapper function for easy use ,
  # rqquant's use


    def buy_open(self, price: float, size: int, type='lmt', full_symbol:str = '',lock:bool = False, stop: bool = False):
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)
        if (type == 'mkt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_AnyPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.MKT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.MKT,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.MKT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'lmt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.LMT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == 'FUTU':             
                order = OrderRequest(
                    api="FUTU",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.LMT,
                    direction=Direction.LONG,
                    sec_type=extract_product(full_symbol),
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.LMT,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.LMT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fak'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FAK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FAK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FAK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fok'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_CV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FOK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FOK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FOK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        else:
            print('order type not supported!')
            return []
    def buy_close(self, price: float, size: int, type='lmt', full_symbol: str = '',lock:bool = False,stop: bool = False):
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)
        if (type == 'mkt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_AnyPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.MKT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.MKT,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.MKT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'lmt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.LMT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "FUTU":
                order = OrderRequest(
                    api="FUTU",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.LMT,
                    direction=Direction.LONG,
                    sec_type=extract_product(full_symbol),
                )
                return self.strategy_engine.send_order(self, order, lock)

            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.LMT,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.LMT,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fak'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FAK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FAK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FAK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fok'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Buy,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_CV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FOK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FOK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FOK,
                    direction=Direction.LONG,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        else:
            print('order type not supported!')
            return []

    def sell_open(self, price: float, size: int, type='lmt', full_symbol: str = '',lock:bool = False,stop: bool = False):
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)
        if (type == 'mkt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_AnyPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.MKT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.MKT,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.MKT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'lmt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.LMT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == 'FUTU':    
                order = OrderRequest(
                    api="FUTU",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.LMT,
                    direction=Direction.SHORT,
                    sec_type=extract_product(full_symbol)
                )
                return self.strategy_engine.send_order(self, order, lock)



            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.LMT,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.LMT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fak'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FAK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FAK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FAK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fok'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Open,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_CV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FOK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FOK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.OPEN,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.OPEN,
                    type=OrderType.FOK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        else:
            print('order type not supported!')
            return []

    def sell_close(self, price: float, size: int, type='lmt', full_symbol: str = '',lock:bool = False,stop: bool = False):
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)
        if (type == 'mkt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_AnyPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.MKT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.MKT,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.MKT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'lmt'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_GFD,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.LMT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == 'FUTU':
                order = OrderRequest(
                    api="FUTU",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.LMT,
                    direction=Direction.SHORT,
                    sec_type=extract_product(full_symbol),
                )
                return self.strategy_engine.send_order(self, order, lock)                
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.LMT,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.LMT,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fak'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_AV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FAK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FAK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FAK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        elif (type == 'fok'):
            if self.api == "CTP.TD":
                of = CtpOrderField(
                    InstrumentID=symbol,
                    OrderPriceType=THOST_FTDC_OPT_LimitPrice,
                    LimitPrice=price,
                    Direction=THOST_FTDC_D_Sell,
                    CombOffsetFlag=THOST_FTDC_OF_Close,
                    CombHedgeFlag=THOST_FTDC_HF_Speculation,
                    VolumeTotalOriginal=size,
                    TimeCondition=THOST_FTDC_TC_IOC,
                    VolumeCondition=THOST_FTDC_VC_CV,
                    MinVolume=1,
                    ContingentCondition=THOST_FTDC_CC_Immediately
                )
                order = OrderRequest(
                    api="CTP.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FOK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
            elif self.api == "PAPER.TD":
                of = PaperOrderField(
                    order_type=OrderType.FOK,
                    limit_price=price,
                    full_symbol=full_symbol,
                    order_flag=OrderFlag.CLOSE,
                    order_size=size * (-1)
                )
                order = OrderRequest(
                    api="PAPER.TD",
                    account=self.account,
                    symbol=symbol,
                    full_symbol=full_symbol,
                    price=price,
                    volume=size,
                    offset=Offset.CLOSE,
                    type=OrderType.FOK,
                    direction=Direction.SHORT,
                    orderfield=of
                )
                return self.strategy_engine.send_order(self, order, lock)
        else:
            print('order type not supported!')
            return []

  # vnpy's use

    def buy(self, price: float, volume: float, full_symbol: str = '',lock:bool = False,stop: bool = False):
        """
        Send buy order to open a long position.

        """
        #   only bactest use
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)   
        if stop:
            of = PaperOrderField(
                order_type=OrderType.LMT,
                limit_price=price,
                full_symbol=full_symbol,
                order_flag=OrderFlag.OPEN,
                order_size=volume
            )
            order = OrderRequest(
                api="PAPER.TD",
                account=self.account,
                symbol=symbol,
                full_symbol=full_symbol,
                price=price,
                volume=volume,
                offset=Offset.OPEN,
                type=OrderType.LMT,
                direction=Direction.LONG,
                orderfield=of
            )
            return self.strategy_engine.send_stop_order(self,order,lock)
        else:
            return self.buy_open(price, volume,'lmt',full_symbol,lock)

    def sell(self, price: float, volume: float, full_symbol: str = '',lock:bool = False,stop: bool = False):
        """
        Send sell order to close a long position.
        """
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)  
        if stop:
            of = PaperOrderField(
                order_type=OrderType.LMT,
                limit_price=price,
                full_symbol=full_symbol,
                order_flag=OrderFlag.CLOSE,
                order_size=volume * (-1)
            )
            order = OrderRequest(
                api="PAPER.TD",
                account=self.account,
                symbol=symbol,
                full_symbol=full_symbol,
                price=price,
                volume=volume,
                offset=Offset.CLOSE,
                type=OrderType.LMT,
                direction=Direction.SHORT,
                orderfield=of
            )
            return self.strategy_engine.send_stop_order(self, order,lock)
        else:
            return self.sell_close(price, volume,'lmt',full_symbol,lock)


    def short(self, price: float, volume: float, full_symbol: str = '',lock:bool = False,stop: bool = False):
        """
        Send short order to open as short position.
        """
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)       
        if stop:
            of = PaperOrderField(
                order_type=OrderType.LMT,
                limit_price=price,
                full_symbol=full_symbol,
                order_flag=OrderFlag.OPEN,
                order_size=volume * (-1)
            )
            order = OrderRequest(
                api="PAPER.TD",
                account=self.account,
                symbol=symbol,
                full_symbol=full_symbol,
                price=price,
                volume=volume,
                offset=Offset.OPEN,
                type=OrderType.LMT,
                direction=Direction.SHORT,
                orderfield=of
            )
            return self.strategy_engine.send_stop_order(self, order,lock)
        else:
            return self.sell_open(price, volume, 'lmt',full_symbol,lock)

    def cover(self, price: float, volume: float, full_symbol: str = '',lock:bool = False,stop: bool = False):
        """
        Send cover order to close a short position.
        """
        if not self.trading:
            return []
        if not full_symbol:
            full_symbol = self.full_symbol
        symbol, ex = extract_full_symbol(full_symbol)            
        if stop:
            of = PaperOrderField(
                order_type=OrderType.LMT,
                limit_price=price,
                full_symbol=full_symbol,
                order_flag=OrderFlag.CLOSE,
                order_size=volume
            )
            order = OrderRequest(
                api="PAPER.TD",
                account=self.account,
                symbol=symbol,
                full_symbol=full_symbol,
                price=price,
                volume=volume,
                offset=Offset.CLOSE,
                type=OrderType.LMT,
                direction=Direction.LONG,
                orderfield=of
            )
            return self.strategy_engine.send_stop_order(self, order, lock)
        else:
            return self.buy_close(price, volume, 'lmt', full_symbol,lock)

# end wrapper

    def write_log(self, msg: str):
        """
        Write a log message.
        """
        # if self.inited:
        #     self.cta_engine.write_log(msg, self)
        print(msg)
        pass

    def get_engine_type(self):
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        return self.strategy_engine.engine_type

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
        datasource='DataBase'
    ):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar
        self.strategy_engine.load_bar(
            self.full_symbol, days, interval, callback, datasource)

    def load_tbtbar(
        self,
        full_symbol,
        days: int,
        interval: Interval = Interval.MINUTE,
        bigmoney: int = 500000,
        callback: Callable = None,
        datasource='DataBase'
    ):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar
        self.strategy_engine.load_tbtbar(
            full_symbol, days, interval, bigmoney, callback, datasource)

    def load_tick(self, days: int, callback: Callable = None,datasource='DataBase'):
        """
        Load historical tick data for initializing strategy.
        """
        if not callback:
            callback = self.on_tick
        self.strategy_engine.load_tick(
            self.full_symbol, days, callback, datasource)


    def put_event(self):
        """
        Put an strategy data event for ui update.
        """
        if self.inited:
            self.strategy_engine.put_strategy_event(self)

    def send_email(self, msg):
        """
        Send email to default receiver.
        """
        # if self.inited:
        #     self.cta_engine.send_email(msg, self)
        pass

    def sync_data(self):
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            # print('begin syn data')
            self.strategy_engine.sync_strategy_data(self)
        pass


class CtaSignal(ABC):
    """"""

    def __init__(self):
        """"""
        self.signal_pos = 0

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        pass

    def set_signal_pos(self, pos):
        """"""
        self.signal_pos = pos

    def get_signal_pos(self):
        """"""
        return self.signal_pos


CtaTemplate = StrategyBase


class TargetPosTemplate(CtaTemplate):
    """"""
    tick_add = 1

    last_tick = None
    last_bar = None
    target_pos = 0
    vt_orderids = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.variables.append("target_pos")

    @virtual
    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.last_tick = tick

        if self.trading:
            self.trade()

    @virtual
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.last_bar = bar

    @virtual
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        vt_orderid = order.server_order_id

        if not order.is_active() and vt_orderid in self.vt_orderids:
            self.vt_orderids.remove(vt_orderid)

    def set_target_pos(self, target_pos):
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self):
        """"""
        self.cancel_all()

        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        # if self.get_engine_type() == EngineType.BACKTESTING:
        #     if pos_change > 0:
        #         vt_orderids = self.buy(long_price, abs(pos_change))
        #     else:
        #         vt_orderids = self.short(short_price, abs(pos_change))
        #     self.vt_orderids.extend(vt_orderids)

        # else:
        #     if self.vt_orderids:
        #         return

        #     if pos_change > 0:
        #         if self.pos < 0:
        #             if pos_change < abs(self.pos):
        #                 vt_orderids = self.cover(long_price, pos_change)
        #             else:
        #                 vt_orderids = self.cover(long_price, abs(self.pos))
        #         else:
        #             vt_orderids = self.buy(long_price, abs(pos_change))
        #     else:
        #         if self.pos > 0:
        #             if abs(pos_change) < self.pos:
        #                 vt_orderids = self.sell(short_price, abs(pos_change))
        #             else:
        #                 vt_orderids = self.sell(short_price, abs(self.pos))
        #         else:
        #             vt_orderids = self.short(short_price, abs(pos_change))
        #     self.vt_orderids.extend(vt_orderids)


class Strategies(StrategyBase):
    """
    Strategies is a collection of strategy
    Usage e.g.: strategy = Strategies(strategyA, DisplayStrategy())
    """

    def __init__(self, *strategies):
        self._strategies_collection = strategies

    def on_tick(self, event):
        for strategy in self._strategies_collection:
            strategy.on_tick(event)


class IndicatorBase(metaclass=ABCMeta):
    """
    Base Indicator class, here parameters is used for calculte function

    """
    parameters = []
    primary = False


    
    def __init__(self):
        self.datas = []


    def set_data(self, datas:list = None):
        if datas:
            self.datas = datas        

    def update_setting(self, setting: dict):
        """
        Update indicator parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of indicator class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        indicator_parameters = {}
        for name in self.parameters:
            indicator_parameters[name] = getattr(self, name)
        return indicator_parameters

    @virtual
    def calculate(self):
        """
        calculate indicator, should return tuple of list, the element of the tuple will show in one chart
        for example: 
            vols = [bar.volume for bar in self.datas]
            return vols, 
        """
        pass

import inspect
import pandas as pd
class FactorBase(metaclass=ABCMeta):
    """
    Base Factor class, here parameters is used for fomulate function

    """
    parameters = []
    factor_name = ""
    def __init__(self):
        self.data = pd.DataFrame()

    def set_data(self, datas:pd.DataFrame = None):
        self.data = datas        

    def update_setting(self, setting: dict):
        """
        Update indicator parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of indicator class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        indicator_parameters = {}
        for name in self.parameters:
            indicator_parameters[name] = getattr(self, name)
        return indicator_parameters

    @virtual
    def formula(self):
        """
        """
        pass

    def form_info(self):
        return inspect.getsource(self.formula)
    
    def info(self):
        info = ""
        info = info + "factor_name:\n"
        info = info +self.factor_name+"\n"
        info = info +"\n"
        info = info + "formula:\n"
        info = info +self.form_info()+"\n"
        info = info +"\n"
        info = info + "params:\n"
        for key in self.parameters:
            info = info+"$"+key+":"+str(getattr(self, key))+"\n"
        return info
        
    def __repr__(self):
        return self.info()
    
    def __str__(self):
        return self.info()

class ModelBase(metaclass=ABCMeta):
    """
    Base predictive model class, here parameters is used for fomulate function

    """
    parameters = []
    model_name = ""

    def __init__(self):
        self.data = pd.DataFrame()
        self.model = None

    def set_data(self, datas:pd.DataFrame = None):
        self.data = datas        

    def update_setting(self, setting: dict):
        """
        Update indicator parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls):
        """
        Get default parameters dict of indicator class.
        """
        class_parameters = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self):
        """
        Get strategy parameters dict.
        """
        indicator_parameters = {}
        for name in self.parameters:
            indicator_parameters[name] = getattr(self, name)
        return indicator_parameters

    @virtual
    def predict(self,data):
        """
        """
        pass

    @virtual
    def fit(self,samplex,sampley):
        """
        """
        pass

    @virtual
    def gen_signals(self,data):
        pass

    @virtual
    def select(self,stats):
        pass


    @virtual
    def filter(self,data):
        pass