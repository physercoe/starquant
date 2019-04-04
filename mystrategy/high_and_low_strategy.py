#!/usr/bin/env python
# -*- coding: utf-8 -*-
from source.strategy.strategy_base import StrategyBase
from source.order.order_event import OrderEvent
from source.order.order_type import OrderType
from source.order.order_flag import OrderFlag
from datetime import timedelta
from pandas import Timestamp
import numpy as np
class HighAndLowStrategy(StrategyBase):
    """
    high point sell and low point buy
    """
    def __init__(self, events_engine,order_manager,portfolio_manager,symbols=["SHFE F RB 1906"],
                start_time=Timestamp('1970-01-01'),end_time=Timestamp('1970-01-01'),
                act_period=3600,ordersize=30,buy_trig=20,sell_trig=20,close_trig=20):
        super(HighAndLowStrategy, self).__init__(events_engine,order_manager,portfolio_manager)
        """
        state:action indicator
        **trig:action conditon

        """
        self.id = 3
        self._portfolio_manager=portfolio_manager
        self.ticks = {}
        self.sign= {}
        self.high_point= {}
        self.low_point={}
        self.prices = {}
        self.sizeperorder = {}
        self.state = {}
        self.starttime = {} 
        self.endtime = {} 
        self.actperiod = {} 
        self.buytrig = {} 
        self.selltrig = {} 
        self.closetrig = {} 
        self.openprice = {}
        self.endprice = {}
        self.ordertime = {}
        self.firstpass = {}
        self.subactive = {}       
        self.symbols=symbols

        if symbols is not None:
            for sym in symbols:
                self.subactive[sym] =True
                self.ticks[sym] = 0
                self.sign[sym] = 1
                self.high_point[sym]= 0.0
                self.low_point[sym]=0.0
                self.prices[sym] = []
                self.sizeperorder[sym]= ordersize
                self.state[sym] = 0
                self.starttime[sym] = start_time
                self.endtime[sym] = end_time
                self.actperiod[sym] = act_period
                self.buytrig[sym] = buy_trig
                self.selltrig[sym] = sell_trig
                self.closetrig[sym] = close_trig
                self.openprice[sym] = 0.0
                self.endprice[sym] = 0.0
                self.ordertime[sym] = Timestamp('1970-01-01')
                self.firstpass[sym] = True
    def on_tick(self, k):
        #symbol = self.symbols[0]
        for sym in self.symbols:
            if (k.full_symbol == sym)  and self.subactive[sym] :

                if k.timestamp > self.starttime[sym] + timedelta(seconds=self.actperiod[sym]):
                    if self.firstpass[sym] :
                        self.firstpass[sym] = False
                        self.high_point[sym] = max(self.prices[sym])
                        self.low_point[sym]= min(self.prices[sym])
                        self.openprice[sym] = self.prices[sym][0]
                        self.endprice[sym] = self.prices[sym][len(self.prices[sym])-1]
                        deltaprice = max(self.high_point[sym]-self.openprice[sym],self.high_point[sym]-self.endprice[sym],self.openprice[sym]-self.low_point[sym],self.endprice[sym]-self.low_point[sym])
                        if (deltaprice <20):
                            self.subactive[sym]=False
                            print(sym,"has no high or low point, end")
                            #print(sym)
                            return
                    #print(k)
                    if (self.state[sym] == 0):# open aciton
                        if (k.price >= self.high_point[sym]):
                            """
                            when reach high point , short
                            """ 
                            o = OrderEvent()
                            o.full_symbol = sym
                            o.order_type = OrderType.MKT
                            o.order_flag = OrderFlag.OPEN
                            o.order_size = -1*self.sizeperorder[sym]
                            print(sym,'place order short')
                            #print(sym)
                            self.place_order(o)
                            self.ordertime[sym] = k.timestamp
                            self.state[sym] = -1
                            # if(self._portfolio_manager.positions[sym]):
                                # print("pos price = ",self._portfolio_manager.positions[sym].average_price)
        # self.average_price = average_price
        # self.size = size
        # self.realized_pnl = 0
        # self.unrealized_pnl = 0


                            return
                        elif (k.price <= self.low_point[sym]):
                            """
                            when reach low point , long
                            """                    
                            o = OrderEvent()
                            o.full_symbol = sym
                            o.order_type = OrderType.MKT
                            o.order_flag = OrderFlag.OPEN
                            o.order_size = 1*self.sizeperorder[sym]
                            if(sym in self._portfolio_manager.positions):
                                 print("pos price = ",self._portfolio_manager.positions[sym].average_price)
                            print(sym,'place order long')
                            #print(sym)
                            self.place_order(o)
                            self.ordertime[sym] = k.timestamp
                            self.state[sym] = 1
                            return
                    if (self.state[sym] == -1):#buy action to close 
                        closeaction = (k.price >= self.high_point[sym] + self.closetrig[sym]) \
                        or (k.price <= self.high_point[sym]-self.buytrig[sym]) \
                        or (k.timestamp > self.ordertime[sym] +timedelta(seconds=self.actperiod[sym])) \
                        or (k.timestamp >self.endtime[sym])
                        if (closeaction):
                            """
                            when reach close point , close
                            """ 
                            o = OrderEvent()
                            o.full_symbol = sym
                            o.order_type = OrderType.MKT
                            o.order_flag = OrderFlag.CLOSE
                            o.order_size = 1*self.sizeperorder[sym]
                            print(sym,'place order close short')
                            #print(sym)
                            self.place_order(o)
                            self.state[sym] = 0
                            self.firstpass[sym]=True
                            self.starttime[sym] = k.timestamp
                            self.prices[sym]=[]
                            return
                    if (self.state[sym] == 1):#sell action to close
                        closeaction = (k.price <= self.low_point[sym] - self.closetrig[sym]) \
                        or (k.price >= self.low_point[sym]+self.selltrig[sym]) \
                        or (k.timestamp > self.ordertime[sym] +timedelta(seconds=self.actperiod[sym])) \
                        or (k.timestamp >self.endtime[sym])

                        if (closeaction):
                            """
                            when reach close point , close
                            """ 
                            o = OrderEvent()
                            o.full_symbol = sym
                            o.order_type = OrderType.MKT
                            o.order_flag = OrderFlag.CLOSE
                            o.order_size = -1*self.sizeperorder[sym]
                            print(sym,'place order close long')
                            #print(sym)
                            if(sym in self._portfolio_manager.positions):
                                 print("pos price = ",self._portfolio_manager.positions[sym].average_price)
                            self.place_order(o)
                            self.state[sym] = 0
                            self.firstpass[sym]=True
                            self.starttime[sym] = k.timestamp
                            self.prices[sym]=[]
                            return
                else:
                    self.prices[sym].append(k.price)

