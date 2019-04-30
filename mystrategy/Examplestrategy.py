#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys 
import os
import yaml
import datetime
sys.path.append("..") 
from source.strategy.strategy_base import StrategyBase
from source.common.datastruct import *
from source.trade.order_manager import OrderManager
from source.trade.portfolio_manager import PortfolioManager
from source.engine.trade_engine import TradeEngine
import mystrategy 

"""
template for strategy run independantly, write its own event handler

"""
class ExampleStrategy(StrategyBase):
    ID = 9999
    name = "example"
    def __init__(self, events_engine,order_manager,portfolio_manager):
        super(ExampleStrategy, self).__init__(events_engine,order_manager,portfolio_manager)
        self.id = 9999
  
    def on_tick(self, event):
        if (self.active):
            print(datetime.datetime.now(), ":examplestrategy receive tick, symbol = %s, price = %d",event.full_symbol, event.price)

    def on_req(self,event):
        v = event.req.split('|')
        if ((v[0]!= '.') or (int(v[0][1:]) != self.id)):
            return 
        if v[2] == str(MSG_TYPE.MSG_TYPE_STRATEGY_START.value):
            self.on_start()
            print('strategy %d is active'%self.id)
        if v[2] == str(MSG_TYPE.MSG_TYPE_STRATEGY_END.value):
            self.on_stop()
            print('strategy %d is inactive'%self.id)
        
#  main 
if __name__ == "__main__":
    mystrategy.startstrategy("ExampleStrategy")

