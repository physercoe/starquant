#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
dynamically load all strategies in the folder
'''
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
import importlib

strategy_list = {}
strategy_id = {}
path = os.path.abspath(os.path.dirname(__file__))

# loop over all the files in the path
for root, subdirs, files in os.walk(path):
    for name in files:
        # by default, all strategies should end with the word 'strategy'
        if 'strategy' in name and '.pyc' not in name:
            # add module prefix
            moduleName = 'mystrategy.' + name.replace('.py', '')
            # import module
            module = importlib.import_module(moduleName)
            # loop through all the objects in the module and look for the one with 'Strategy' keyword
            for k in dir(module):
                if ('Strategy' in k) and ('StrategyBase' not in k):
                    v = module.__getattribute__(k)
                    strategy_list[k] = v
                    strategy_id[v.ID] = v

def strategy_list_reload():
    strategy_list.clear()
    path = os.path.abspath(os.path.dirname(__file__))
# loop over all the files in the path
    for root, subdirs, files in os.walk(path):
        for name in files:
            # by default, all strategies should end with the word 'strategy'
            if 'strategy' in name and '.pyc' not in name:
                # add module prefix
                moduleName = 'mystrategy.' + name.replace('.py', '')
                # import module
                module = importlib.import_module(moduleName)
                # delete old attribute
                for attr in dir(module):
                    if attr not in ('__name__','__file__'):
                        delattr(module,attr)
                importlib.reload(module)
                # loop through all the objects in the module and look for the one with 'Strategy' keyword
                for k in dir(module):
                    if ('Strategy' in k) and ('StrategyBase' not in k):
                        v = module.__getattribute__(k)
                        strategy_list[k] = v


def startstrategy(name):
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

    strategyClass = strategy_list.get(name, None)
    if not strategyClass:
        print(u'can not find strategy：%s' % name)
    else:    
        tradeengine = TradeEngine(config_server)
        ordermanager = OrderManager()
        portfoliomanager = PortfolioManager(config_client['initial_cash'],config_server['tickers'])
        strategy = strategyClass(tradeengine,ordermanager,portfoliomanager)
        strategy.register_event()
        tradeengine.id = strategy.id
        tradeengine.start()

def startsid(sid):
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
    
    strategyClass = strategy_id.get(sid, None)
    if not strategyClass:
        print(u'can not find strategy id：%d' % sid)
    else:    
        tradeengine = TradeEngine(config_server)
        ordermanager = OrderManager()
        portfoliomanager = PortfolioManager(config_client['initial_cash'],config_server['tickers'])
        strategy = strategyClass(tradeengine,ordermanager,portfoliomanager)
        strategy.register_event()
        tradeengine.id = strategy.id
        tradeengine.start()        
