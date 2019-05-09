#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue, Empty
from threading import Thread
from nanomsg import Socket, PAIR, SUB, PUB, PUSH,SUB_SUBSCRIBE, AF_SP,SOL_SOCKET,RCVTIMEO
from datetime import datetime, timedelta
import os
from collections import defaultdict
from copy import copy
from pathlib import Path
import traceback
import importlib
from typing import Any, Callable

from ..common.datastruct import *
from ..common.utility import *
from ..strategy.strategy_base import StrategyBase
from ..data.rqdata import rqdata_client
from ..data import database_manager
from ..trade.portfolio_manager import OffsetConverter
from ..engine.iengine import BaseEngine
class TradeEngine(BaseEngine):
    """
    Send to and receive from msg  server ,used for strategy 
    """
    setting_filename = "cta_strategy_setting.json"
    data_filename = "cta_strategy_data.json"

    def __init__(self,config:dict):
        super(TradeEngine, self).__init__()
        """
        two sockets to send and recv msg
        """
        self.__active = False
        self.id = 0
        self.engine_type = EngineType.LIVE     
        self._recv_sock = Socket(SUB)
        self._send_sock = Socket(PUSH)
        self._config = config
        self._handlers = defaultdict(list)

#  stragegy manage
        self.strategy_setting = {}  # strategy_name: dict
        self.strategy_data = {}     # strategy_name: dict

        self.classes = {}           # class_name: stategy_class
        self.strategies = {}        # strategy_name: strategy

        self.symbol_strategy_map = defaultdict(
            list)                   # vt_symbol: strategy list
        self.orderid_strategy_map = {}  # vt_orderid: strategy
        self.strategy_orderid_map = defaultdict(
            set)                    # strategy_name: orderid list

        self.stop_order_count = 0   # for generating stop_orderid
        self.stop_orders = {}       # stop_orderid: stop_order
        self.init_thread = None
        self.init_queue = Queue()

# order,tick,position ,etc manage
        self.ticks = {}
        self.orders = {}
        self.trades = {}
        self.positions = {}
        self.accounts = {}
        self.contracts = {}

        self.active_orders = {}



        self.rq_client = None
        self.rq_symbols = set()

        self.offset_converter = OffsetConverter(self)

        self.init_engine()


    def init_engine(self):
        self.init_nng()
        self.init_rqdata()
        self.load_strategy_class()
        self.load_strategy_setting()
        self.load_strategy_data()  
        self.register_event()


    def init_rqdata(self):

        result = rqdata_client.init()
        if result:
            self.write_log("RQData数据接口初始化成功")

    def register_event(self):
        """"""
        self.event_engine.register(EventType.TICK, self.process_tick_event)
        self.event_engine.register(EventType.ORDERSTATUS, self.process_order_event)
        self.event_engine.register(EventType.FILL, self.process_trade_event)
        self.event_engine.register(EventType.POSITION, self.process_position_event)
        self.event_engine.register(EventType.ACCOUNT, self.process_account_event)
        self.event_engine.register(EventType.CONTRACT, self.process_contract_event)        


    def process_tick_event(self, event: Event):
        """"""
        tick = event

        strategies = self.symbol_strategy_map[tick.full_symbol]
        if not strategies:
            return
        # self.check_stop_order(tick)
        for strategy in strategies:
            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_tick, tick)
        self.ticks[tick.full_symbol] = tick

    def process_order_event(self, event: Event):
        """"""
        order = event
        
        self.offset_converter.update_order(order)

        strategy = self.orderid_strategy_map.get(order.vt_orderid, None)
        if not strategy:
            return

        # Remove vt_orderid if order is no longer active.
        vt_orderids = self.strategy_orderid_map[strategy.strategy_name]
        if order.vt_orderid in vt_orderids and not order.is_active():
            vt_orderids.remove(order.vt_orderid)

        # For server stop order, call strategy on_stop_order function
        # if order.type == OrderType.STOP:
        #     so = StopOrder(
        #         vt_symbol=order.vt_symbol,
        #         direction=order.direction,
        #         offset=order.offset,
        #         price=order.price,
        #         volume=order.volume,
        #         stop_orderid=order.vt_orderid,
        #         strategy_name=strategy.strategy_name,
        #         status=STOP_STATUS_MAP[order.status],
        #         vt_orderid=order.vt_orderid,
        #     )
        #     self.call_strategy_func(strategy, strategy.on_stop_order, so)  

        # Call strategy on_order function
        self.call_strategy_func(strategy, strategy.on_order, order)

        
        self.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)     

    def process_trade_event(self, event: Event):
        """"""
        trade = event

        self.offset_converter.update_trade(trade)

        strategy = self.orderid_strategy_map.get(trade.vt_orderid, None)
        if not strategy:
            return

        # if trade.direction == Direction.LONG:
        #     strategy.pos += trade.volume
        # else:
        #     strategy.pos -= trade.volume

        self.call_strategy_func(strategy, strategy.on_trade, trade)
        self.put_strategy_event(strategy)

        self.trades[trade.vt_tradeid] = trade


    def process_position_event(self, event: Event):
        """"""
        position = event

        self.offset_converter.update_position(position)

        self.positions[position.vt_positionid] = position

    def process_account_event(self, event: Event):
        """"""
        account = event
        self.accounts[account.vt_accountid] = account

    def process_contract_event(self, event: Event):
        """"""
        contract = event
        self.contracts[contract.vt_symbol] = contract

    def call_strategy_func(
        self, strategy: StrategyBase, func: Callable, params: Any = None
    ):
        """
        Call function of a strategy and catch any exception raised.
        """
        try:
            if params:
                func(params)
            else:
                func()
        except Exception:
            strategy.trading = False
            strategy.inited = False

            msg = f"触发异常已停止\n{traceback.format_exc()}"
            self.write_log(msg, strategy)

    def add_strategy(
        self, class_name: str, strategy_name: str, vt_symbol: str, setting: dict
    ):
        """
        Add a new strategy.
        """
        if strategy_name in self.strategies:
            self.write_log(f"创建策略失败，存在重名{strategy_name}")
            return

        strategy_class = self.classes[class_name]

        strategy = strategy_class(self, strategy_name, vt_symbol, setting)
        self.strategies[strategy_name] = strategy

        # Add vt_symbol to strategy map.
        strategies = self.symbol_strategy_map[vt_symbol]
        strategies.append(strategy)

        # Update to setting file.
        self.update_strategy_setting(strategy_name, setting)

        self.put_strategy_event(strategy)

    def init_strategy(self, strategy_name: str):
        """
        Init a strategy.
        """ 
        self.init_queue.put(strategy_name)

        if not self.init_thread:
            self.init_thread = Thread(target=self._init_strategy)
            self.init_thread.start()

    def _init_strategy(self):
        """
        Init strategies in queue.
        """
        while not self.init_queue.empty():
            strategy_name = self.init_queue.get()
            strategy = self.strategies[strategy_name]

            if strategy.inited:
                self.write_log(f"{strategy_name}已经完成初始化，禁止重复操作")
                continue

            self.write_log(f"{strategy_name}开始执行初始化")

            # Call on_init function of strategy
            self.call_strategy_func(strategy, strategy.on_init)

            # Restore strategy data(variables)
            data = self.strategy_data.get(strategy_name, None)
            if data:
                for name in strategy.variables:
                    value = data.get(name, None)
                    if value:
                        setattr(strategy, name, value)

            # Subscribe market data
            contract = self.get_contract(strategy.vt_symbol)
            if contract:
                req = SubscribeEvent()
                req.destination = contract.gateway_name
                req.source = "0"                
                req.content = strategy.symbol
                self.put(req)
            else:
                self.write_log(f"行情订阅失败，找不到合约{strategy.vt_symbol}", strategy)

            # Put event to update init completed status.
            strategy.inited = True
            self.put_strategy_event(strategy)
            self.write_log(f"{strategy_name}初始化完成")
        
        self.init_thread = None

    def start_strategy(self, strategy_name: str):
        """
        Start a strategy.
        """
        strategy = self.strategies[strategy_name]
        if not strategy.inited:
            self.write_log(f"策略{strategy.strategy_name}启动失败，请先初始化")
            return

        if strategy.trading:
            self.write_log(f"{strategy_name}已经启动，请勿重复操作")
            return

        self.call_strategy_func(strategy, strategy.on_start)
        strategy.trading = True

        self.put_strategy_event(strategy)

    def stop_strategy(self, strategy_name: str):
        """
        Stop a strategy.
        """
        strategy = self.strategies[strategy_name]
        if not strategy.trading:
            return

        # Call on_stop function of the strategy
        self.call_strategy_func(strategy, strategy.on_stop)

        # Change trading status of strategy to False
        strategy.trading = False

        # Cancel all orders of the strategy
        # self.cancel_all(strategy)

        # Update GUI
        self.put_strategy_event(strategy)

    def edit_strategy(self, strategy_name: str, setting: dict):
        """
        Edit parameters of a strategy.
        """
        strategy = self.strategies[strategy_name]
        strategy.update_setting(setting)

        self.update_strategy_setting(strategy_name, setting)
        self.put_strategy_event(strategy)

    def remove_strategy(self, strategy_name: str):
        """
        Remove a strategy.
        """
        strategy = self.strategies[strategy_name]
        if strategy.trading:
            self.write_log(f"策略{strategy.strategy_name}移除失败，请先停止")
            return

        # Remove setting
        self.remove_strategy_setting(strategy_name)

        # Remove from symbol strategy map
        strategies = self.symbol_strategy_map[strategy.vt_symbol]
        strategies.remove(strategy)

        # Remove from active orderid map
        if strategy_name in self.strategy_orderid_map:
            vt_orderids = self.strategy_orderid_map.pop(strategy_name)

            # Remove vt_orderid strategy map
            for vt_orderid in vt_orderids:
                if vt_orderid in self.orderid_strategy_map:
                    self.orderid_strategy_map.pop(vt_orderid)

        # Remove from strategies
        self.strategies.pop(strategy_name)

        return True

    def load_strategy_class(self):
        """
        Load strategy class from source code.
        """
        path1 = Path(__file__).parent.joinpath("")
        self.load_strategy_class_from_folder(
            path1, "mystrategy")

        path2 = Path.cwd().joinpath("")
        self.load_strategy_class_from_folder(path2, "mystrategy")

    def load_strategy_class_from_folder(self, path: Path, module_name: str = ""):
        """
        Load strategy class from certain folder.
        """
        for dirpath, dirnames, filenames in os.walk(str(path)):
            for filename in filenames:
                if filename.endswith(".py"):
                    strategy_module_name = ".".join(
                        [module_name, filename.replace(".py", "")])
                    self.load_strategy_class_from_module(strategy_module_name)

    def load_strategy_class_from_module(self, module_name: str):
        """
        Load strategy class from module file.
        """
        try:
            module = importlib.import_module(module_name)

            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, StrategyBase) and value is not StrategyBase):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

    def load_strategy_data(self):
        """
        Load strategy data from json file.
        """
        self.strategy_data = load_json(self.data_filename)

    def sync_strategy_data(self, strategy: StrategyBase):
        """
        Sync strategy data into json file.
        """
        data = strategy.get_variables()
        data.pop("inited")      # Strategy status (inited, trading) should not be synced.
        data.pop("trading")

        self.strategy_data[strategy.strategy_name] = data
        save_json(self.data_filename, self.strategy_data)

    def get_all_strategy_class_names(self):
        """
        Return names of strategy classes loaded.
        """
        return list(self.classes.keys())

    def get_strategy_class_parameters(self, class_name: str):
        """
        Get default parameters of a strategy class.
        """
        strategy_class = self.classes[class_name]

        parameters = {}
        for name in strategy_class.parameters:
            parameters[name] = getattr(strategy_class, name)

        return parameters

    def get_strategy_parameters(self, strategy_name):
        """
        Get parameters of a strategy.
        """
        strategy = self.strategies[strategy_name]
        return strategy.get_parameters()

    def init_all_strategies(self):
        """
        """
        for strategy_name in self.strategies.keys():
            self.init_strategy(strategy_name)

    def start_all_strategies(self):
        """
        """
        for strategy_name in self.strategies.keys():
            self.start_strategy(strategy_name)

    def stop_all_strategies(self):
        """
        """
        for strategy_name in self.strategies.keys():
            self.stop_strategy(strategy_name)

    def load_strategy_setting(self):
        """
        Load setting file.
        """
        self.strategy_setting = load_json(self.setting_filename)

        for strategy_name, strategy_config in self.strategy_setting.items():
            self.add_strategy(
                strategy_config["class_name"], 
                strategy_name,
                strategy_config["vt_symbol"], 
                strategy_config["setting"]
            )

    def update_strategy_setting(self, strategy_name: str, setting: dict):
        """
        Update setting file.
        """
        strategy = self.strategies[strategy_name]

        self.strategy_setting[strategy_name] = {
            "class_name": strategy.__class__.__name__,
            "vt_symbol": strategy.vt_symbol,
            "setting": setting,
        }
        save_json(self.setting_filename, self.strategy_setting)

    def remove_strategy_setting(self, strategy_name: str):
        """
        Update setting file.
        """
        if strategy_name not in self.strategy_setting:
            return

        self.strategy_setting.pop(strategy_name)
        save_json(self.setting_filename, self.strategy_setting)

    # def put_stop_order_event(self, stop_order: StopOrder):
    #     """
    #     Put an event to update stop order status.
    #     """
    #     event = Event(EVENT_CTA_STOPORDER, stop_order)
    #     self.event_engine.put(event)

    def put_strategy_event(self, strategy: StrategyBase):
        """
        Put an event to update strategy status.
        """
        data = strategy.get_data()
        # event = Event(EVENT_CTA_STRATEGY, data)
        # self.event_engine.put(event)
        pass






    def init_nng(self):
        self._recv_sock.set_string_option(SUB, SUB_SUBSCRIBE, '')  # receive msg start with all
        self._recv_sock.set_int_option(SOL_SOCKET,RCVTIMEO,100)
        self._recv_sock.connect(self._config['serverpub_url'])
        self._send_sock.connect(self._config['serverpull_url'])
    #------------------------------------ public functions -----------------------------#
    
    def query_bar_from_rq(
        self, symbol: str, exchange: Exchange, interval: Interval, start: datetime, end: datetime
    ):
        """
        Query bar data from RQData.
        """
        data = rqdata_client.query_bar(
            symbol, exchange, interval, start, end
        )
        return data   
    
    
    def load_bar(
        self, 
        vt_symbol: str, 
        days: int, 
        interval: Interval,
        callback: Callable[[BarData], None]
    ):
        """"""
        symbol, exchange = extract_vt_symbol(vt_symbol)
        end = datetime.now()
        start = end - timedelta(days)

        # Query bars from RQData by default, if not found, load from database.
        bars = self.query_bar_from_rq(symbol, exchange, interval, start, end)
        if not bars:
            bars = database_manager.load_bar_data(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start=start,
                end=end,
            )

        for bar in bars:
            callback(bar)
    
    
    
    def get_tick(self, vt_symbol):
        """
        Get latest market tick data by vt_symbol.
        """
        return self.ticks.get(vt_symbol, None)

    def get_order(self, vt_orderid):
        """
        Get latest order data by vt_orderid.
        """
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid):
        """
        Get trade data by vt_tradeid.
        """
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid):
        """
        Get latest position data by vt_positionid.
        """
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid):
        """
        Get latest account data by vt_accountid.
        """
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol):
        """
        Get contract data by vt_symbol.
        """
        return self.contracts.get(vt_symbol, None)

    def get_all_ticks(self):
        """
        Get all tick data.
        """
        return list(self.ticks.values())

    def get_all_orders(self):
        """
        Get all order data.
        """
        return list(self.orders.values())

    def get_all_trades(self):
        """
        Get all trade data.
        """
        return list(self.trades.values())

    def get_all_positions(self):
        """
        Get all position data.
        """
        return list(self.positions.values())

    def get_all_accounts(self):
        """
        Get all account data.
        """
        return list(self.accounts.values())

    def get_all_contracts(self):
        """
        Get all contract data.
        """
        return list(self.contracts.values())

    def get_all_active_orders(self, vt_symbol: str = ""):
        """
        Get all active orders by vt_symbol.

        If vt_symbol is empty, return all active orders.
        """
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders    
    


    
    
    def start(self, timer=True):
        """
        start the dispatcher thread and begin to recv msg through nng
        """
        self.event_engine.start()
        print('tradeclient started ,pid = %d ' % os.getpid())
        self.__active = True
        # print(self._config['serverpub_url'])
        while self.__active:
            try:
                msgin = self._recv_sock.recv(flags=0)
                msgin = msgin.decode("utf-8")
                if msgin is not None and msgin.index('|') > 0:
                    print('tradeclient(id = %d) rec server msg:'%(self.id), msgin,'at ', datetime.now())
                    if msgin[-1] == '\0':
                        msgin = msgin[:-1]
                    if msgin[-1] == '\x00':
                        msgin = msgin[:-1]
                    # v = msgin.split('|')
                    # msg2type = MSG_TYPE(int(v[2]))
                    # if msg2type == MSG_TYPE.MSG_TYPE_TICK_L1:
                    #     m = TickEvent()
                    #     m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_RTN_ORDER:
                    #    m = OrderStatusEvent()
                    #    m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_RTN_TRADE:
                    #     m = FillEvent()
                    #     m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_RSP_POS:
                    #     m = PositionEvent()
                    #     m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_Hist:
                    #     m = HistoricalEvent()
                    #     m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_RSP_ACCOUNT:
                    #     m = AccountEvent()
                    #     m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_RSP_CONTRACT:
                    #     m = ContractEvent()
                    #     m.deserialize(msgin)
                    # elif msg2type == MSG_TYPE.MSG_TYPE_INFO:
                    #     m = InfoEvent()
                    #     m.deserialize(msgin)
                    # else:
                    #     m = GeneralReqEvent() 
                    #     m.deserialize(msgin)
                    #     pass
                    m = Event()
                    m.deserialize(msgin)
                    self.event_engine.put(m)
                    # if m.event_type in self._handlers:
                    #     [handler(m) for handler in self._handlers[m.event_type]]
            except Exception as e:
                pass
                #print("TradeEngineError {0}".format(str(e.args[0])).encode("utf-8"))
 
    def stop(self):
        """
        stop 
        """
        self.__active = False
        self.event_engine.stop()

    def put(self, event):
        """
        send event msg,TODO:check the event
        """
        # 
        self._send_sock.send(event.serialize(),flags=1)

    def register_handler(self, type_, handler):
        """
        register handler/subscriber
        """
        # handlerList = self._handlers[type_]

        # if handler not in handlerList:
        #     self._handlers[type_].append(handler)
        #     #handlerList.append(handler)
        pass

    def unregister_handler(self, type_, handler):
        """
        unregister handler/subscriber
        """
        # handlerList = self._handlers[type_]

        # if handler in handlerList:
        #     self._handlers.remove(handler)

        # if not handlerList:
        #     del self._handlers[type_]
        pass

    def write_log(self, msg: str, strategy: StrategyBase = None):
        """
        Create engine log event.
        """
        # if strategy:
        #     msg = f"{strategy.strategy_name}: {msg}"

        # log = LogData(msg=msg, gateway_name="CtaStrategy")
        # event = Event(type=EVENT_CTA_LOG, data=log)
        # self.event_engine.put(event)  
        print(msg)      

    # -------------------------------- end of public functions -----------------------------#