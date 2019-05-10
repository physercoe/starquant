#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABC,ABCMeta, abstractmethod
from datetime import datetime
from typing import Any, Callable

from ..common.datastruct import *
from ..common.sqglobal import dotdict
from ..common.utility import virtual

class StrategyBase(metaclass=ABCMeta):
    """
    Base strategy class

    """
    # class id and name
    ID = -1
    NAME = "base"

    # for rqquant use
    context = dotdict()

    # parameters and variables,for vnpy use 
    author = ""
    parameters = []
    variables = []



    def __init__(self, 
        events_engine: Any, 
        strategy_name: str, 
        symbol: str,
        setting: dict):
        """
        initialize trategy
        :param symbols:
        :param events_engine:backtest_event_engine or live_event engine that provides queue_.put()
        """
        self.symbol = symbol
        self._events_engine = events_engine
        self.id = -1
        self.name = strategy_name

        self.active = False
        self.account = ''

        self.inited = False
        self.trading = False
        self.pos = 0

        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.update_setting(setting)

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
            "strategy_name": self.name,
            "symbol": self.symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data






    def set_capital(self, capital):
        self.capital = capital

    def set_symbols(self, symbols):
        self.symbols = symbols



    # used for trade engine run 
    def register_event(self):
        self._events_engine.register_handler(EventType.TICK, self.on_tick)
        self._events_engine.register_handler(EventType.BAR,self.on_bar)
        self._events_engine.register_handler(EventType.ORDERSTATUS, self.on_order_status)
        self._events_engine.register_handler(EventType.FILL, self.on_fill)
        self._events_engine.register_handler(EventType.POSITION, self.on_pos)
        self._events_engine.register_handler(EventType.ACCOUNT, self.on_acc)
        self._events_engine.register_handler(EventType.CONTRACT, self.on_contract)
        self._events_engine.register_handler(EventType.HISTORICAL, self.on_bar)
        self._events_engine.register_handler(EventType.INFO, self.on_info)
        self._events_engine.register_handler(EventType.GENERAL_REQ, self.on_req)


    def run(self):
        self.register_event()
        self._events_engine.id = self.id
        self._events_engine.start()

    #   event handlers

    @virtual 
    def on_init(self, params_dict=None):
        # self.inited = True

        # # set params
        # if params_dict is not None:
        #     for key, value in params_dict.items():
        #         try:
        #             self.__setattr__(key, value)
        #         except:
        #             pass
        pass
        
    @virtual 
    def on_start(self):
        self.active = True

    @virtual
    def on_stop(self):
        self.active = False

    @virtual
    def on_tick(self, event):
        """
        Respond to tick
        """
        pass
    @virtual
    def on_bar(self, event):
        """
        Respond to bar
        """
        pass

    @virtual
    def on_order_status(self,event):
        """
        on order acknowledged
        :return:
        """
        #raise NotImplementedError("Should implement on_order()")
        pass

    @virtual
    def on_cancel(self,event):
        """
        on order canceled
        :return:
        """
        pass

    @virtual
    def on_fill(self,event):
        """
        on order filled
        :return:
        """
        
        pass

    def on_trade(self,event):
        self.on_fill(event)

    @virtual
    def on_pos(self,event):
        pass
        
    @virtual
    def on_acc(self,event):
        pass

    @virtual
    def on_contract(self,event):
        pass

    @virtual
    def on_info(self,event):
        pass

    @virtual
    def on_req(self,event):
        pass

    @virtual
    def on_stop_order(self, stop_order):
        """
        Callback of stop order update.
        """
        pass


    def place_order(self, o):
        o.clientID = self.id         # identify source
        o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        if (self.active):
            self._events_engine.put(o)





    # wrapper function for easy use , rqquant's use  
    def buy_open(self,symbol,size,type='mkt',price = 0.0,api = 'CTP.TD'):
        o = OrderEvent()
        o.api = api
        o.full_symbol = symbol
        o.account = self.account
        o.order_flag = OrderFlag.OPEN
        o.order_size = size
        if type == 'mkt' :
            o.order_type = OrderType.MKT
        elif type =='lmt':
            o.order_type = OrderType.LMT
            o.limit_price = price
        else:
            print('order type unknown, using mkt !')
            o.order_type = OrderType.MKT
        #print('place order buy open')
        self.place_order(o)

    def buy_close(self,symbol,size,type='mkt',price = 0.0,closetoday = False, api = 'CTP.TD'):
        o = OrderEvent()
        o.api = api
        o.full_symbol = symbol
        o.account = self.account
        if closetoday:
            o.order_flag = OrderFlag.CLOSE_TODAY
        else:
            o.order_flag = OrderFlag.CLOSE
        o.order_size = size
        if type == 'mkt' :
            o.order_type = OrderType.MKT
        elif type =='lmt':
            o.order_type = OrderType.LMT
            o.limit_price = price
        elif type == 'stp':
            o.order_type = OrderType.STP
        elif type == 'stplmt':
            o.order_type = OrderType.STPLMT
            o.stop_price = price
        else:
            print('order type unknown, using mkt !')
            o.order_type = OrderType.MKT
        #print('place order buy close')
        self.place_order(o)

    def sell_open(self,symbol,size,type='mkt',price = 0.0,api = 'CTP.TD'):
        o = OrderEvent()
        o.api = api
        o.full_symbol = symbol
        o.account = self.account
        o.order_flag = OrderFlag.OPEN
        o.order_size = -1*abs(size)
        if type == 'mkt' :
            o.order_type = OrderType.MKT
        elif type =='lmt':
            o.order_type = OrderType.LMT
            o.limit_price = price
        else:
            print('order type unknown, using mkt !')
            o.order_type = OrderType.MKT
        #print('place order sell open')
        self.place_order(o)  

    def sell_close(self,symbol,size,type='mkt',price = 0.0,closetoday = False,api = 'CTP.TD'):
        o = OrderEvent()
        o.api = api
        o.full_symbol = symbol
        o.account = self.account
        if closetoday:
            o.order_flag = OrderFlag.CLOSE_TODAY
        else:
            o.order_flag = OrderFlag.CLOSE
        o.order_size = -1*abs(size)
        if type == 'mkt' :
            o.order_type = OrderType.MKT
        elif type =='lmt':
            o.order_type = OrderType.LMT
            o.limit_price = price
        elif type == 'stp':
            o.order_type = OrderType.STP
        elif type == 'stplmt':
            o.order_type = OrderType.STPLMT
            o.stop_price = price
        else:
            print('order type unknown, using mkt !')
            o.order_type = OrderType.MKT
        #print('place order sell close')
        self.place_order(o)       


    # vnpy's use  
    def buy(self, price: float, volume: float, stop: bool = False):
        """
        Send buy order to open a long position.
        """
        pass

    def sell(self, price: float, volume: float, stop: bool = False):
        """
        Send sell order to close a long position.
        """
        pass

    def short(self, price: float, volume: float, stop: bool = False):
        """
        Send short order to open as short position.
        """
        pass

    def cover(self, price: float, volume: float, stop: bool = False):
        """
        Send cover order to close a short position.
        """
        pass


    def cancel_order(self, oid):
        pass

    def cancel_all(self):
        """
        cancel all standing orders from this strategy id
        :return:
        """
        pass



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
        return self._events_engine.engine_type
        

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable = None,
    ):
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar
        pass
        self._events_engine.load_bar(self.symbol, days, interval, callback)

    def load_tick(self, days: int):
        """
        Load historical tick data for initializing strategy.
        """
        self._events_engine.load_tick(self.symbol, days, self.on_tick)
        pass


    def put_event(self):
        """
        Put an strategy data event for ui update.
        """
        # if self.inited:
        #     self.cta_engine.put_strategy_event(self)
        pass

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
        # if self.trading:
        #     self.cta_engine.sync_strategy_data(self)
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
OrderData = OrderStatusEvent

class TargetPosTemplate(CtaTemplate):
    """"""
    tick_add = 1

    last_tick = None
    last_bar = None
    target_pos = 0
    vt_orderids = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(TargetPosTemplate, self).__init__(
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


