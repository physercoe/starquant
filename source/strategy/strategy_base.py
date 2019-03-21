#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from datetime import datetime

from ..order.order_event import OrderEvent
from ..order.order_type import OrderType
from ..order.order_flag import OrderFlag
class StrategyBase(metaclass=ABCMeta):
    """
    Base strategy class
    """
    def __init__(self, events_engine,order_manager,portfolio_manager):
        """
        initialize trategy
        :param symbols:
        :param events_engine:backtest_event_engine or live_event engine that provides queue_.put()
        """
        self.symbols = []
        self._events_engine = events_engine
        self._order_manager = order_manager
        self._portfolio_manager = portfolio_manager
        self.id = -1
        self.name = ''
        self.author = ''
        self.capital = 0.0
        self.initialized = False
        self.active = False
        self.account = ''
    def set_capital(self, capital):
        self.capital = capital

    def set_symbols(self, symbols):
        self.symbols = symbols

    def on_init(self, params_dict=None):
        self.initialized = True

        # set params
        if params_dict is not None:
            for key, value in params_dict.items():
                try:
                    self.__setattr__(key, value)
                except:
                    pass

    def on_start(self):
        self.active = True

    def on_stop(self):
        self.active = False

    def on_tick(self, event):
        """
        Respond to tick
        """
        pass

    def on_bar(self, event):
        """
        Respond to bar
        """
        pass

    def on_order_status(self):
        """
        on order acknowledged
        :return:
        """
        #raise NotImplementedError("Should implement on_order()")
        pass

    def on_cancel(self):
        """
        on order canceled
        :return:
        """
        pass

    def on_fill(self):
        """
        on order filled
        :return:
        """
        pass

    def place_order(self, o):
        o.source = self.id         # identify source
        o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        if (self.active):
            self._events_engine.put(o)
    # wrapper function for easy use   
    def buy_open(self,symbol,size,type='mkt',price = 0.0):
        o = OrderEvent()
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

    def buy_close(self,symbol,size,type='mkt',price = 0.0,closetoday = False):
        o = OrderEvent()
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

    def sell_open(self,symbol,size,type='mkt',price = 0.0):
        o = OrderEvent()
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

    def sell_close(self,symbol,size,type='mkt',price = 0.0,closetoday = False):
        o = OrderEvent()
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


    def cancel_order(self, oid):
        pass

    def cancel_all(self):
        """
        cancel all standing orders from this strategy id
        :return:
        """
        pass

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
