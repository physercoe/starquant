#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys 
sys.path.append("..") 
from source.strategy.strategy_base import StrategyBase
from source.order.order_event import OrderEvent
from source.order.order_type import OrderType
from source.order.order_manager import OrderManager
from source.position.portfolio_manager import PortfolioManager
from source.event.trade_engine import TradeEngine
import os
import yaml
import datetime

"""
template for strategy run independantly, write its own event handler

"""
class ExampleStrategy(StrategyBase):
    def __init__(self, events_engine,order_manager,portfolio_manager):
        super(ExampleStrategy, self).__init__(events_engine,order_manager,portfolio_manager)
        self.id = 9999
  
    def on_tick(self, event):
        print(datetime.datetime.now(), ":examplestrategy receive tick, symbol = %s, price = %d",event.full_symbol, event.price)

#  main 
if __name__ == "__main__":
    config_server = None
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(path, '../etc/config_server.yaml')
        with open(os.path.expanduser(config_file), encoding='utf8') as fd:
            config_server = yaml.load(fd)
    except IOError:
        print("config_server.yaml is missing")
    config_client = None
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(path, '../etc/config_client.yaml')
        with open(os.path.expanduser(config_file), encoding='utf8') as fd:
            config_client = yaml.load(fd)
    except IOError:
        print("config_client.yaml is missing")


    tradeengine = TradeEngine(config_server)
    ordermanager = OrderManager()
    portfoliomanager = PortfolioManager(config_client['initial_cash'],config_server['tickers'])
    strategy = ExampleStrategy(tradeengine,ordermanager,portfoliomanager)
    strategy.register_event()
    tradeengine.start()

