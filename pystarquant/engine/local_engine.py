#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date, time
from time import time as ttime

from collections import defaultdict
import os
import json
from concurrent.futures import ThreadPoolExecutor
import traceback
import random
from typing import Any, Sequence, Type, Dict, List, Optional,Callable
from copy import copy

from pystarquant.common.constant import PRODUCT_VT2SQ
from pystarquant.common.utility import generate_full_symbol, extract_full_symbol, load_json, save_json
import pystarquant.common.sqglobal as SQGlobal
from pystarquant.engine.iengine import EventEngine,BaseLocalEngine
from pystarquant.gateway.gateway import BaseGateway
from pystarquant.strategy.strategy_base import StrategyBase




from pystarquant.common.constant import (
    EventType,
    Direction, 
    Offset, 
    Exchange,
    Interval,
    Status,
    EngineType,
    BacktestingMode, 
    STOPORDER_PREFIX, 
    StopOrderStatus,
    MSG_TYPE,
    OrderType,
)
from pystarquant.common.datastruct import (
    Event,
    OrderData, 
    TradeData, 
    BacktestTradeData,
    BarData, 
    TickData, 
    TBTBarData, 
    StopOrder, 
    ContractData,
    LogData,
    OrderRequest,
    VNHistoryRequest,
    VNCancelRequest,
    VNOrderRequest,
    VNSubscribeRequest
)
from pystarquant.data import database_manager
from pystarquant.trade.portfolio_manager import OffsetConverter


class LocalMainEngine:
    """
    Acts as the core of local Trader, manage all the local engines
    """

    def __init__(self, event_engine: EventEngine = None):
        """"""
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        # self.event_engine.start()

        self.gateways: Dict[str, BaseGateway] = {}
        self.engines: Dict[str, BaseLocalEngine] = {}
        # self.apps: Dict[str, BaseApp] = {}
        self.exchanges: List[Exchange] = []

        # os.chdir(TRADER_DIR)    # Change working directory
        self.init_engines()     # Initialize function engines

    def add_engine(self, engine_class: Any) -> "BaseLocalEngine":
        """
        Add function engine.
        """
        engine = engine_class(self, self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    def add_gateway(self, gateway_class: Type[BaseGateway]) -> BaseGateway:
        """
        Add gateway.
        """
        gateway = gateway_class(self.event_engine)
        self.gateways[gateway.gateway_name] = gateway

        # Add gateway supported exchanges into engine
        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    # def add_app(self, app_class: Type[BaseApp]) -> "BaseEngine":
    #     """
    #     Add app.
    #     """
    #     app = app_class()
    #     self.apps[app.app_name] = app

    #     engine = self.add_engine(app.engine_class)
    #     return engine

    def init_engines(self) -> None:
        """
        Init all engines.
        """
        # self.add_engine(LogEngine)
        # self.add_engine(OmsEngine)
        # self.add_engine(EmailEngine)
        pass

    def write_log(self, msg: str, source: str = "") -> None:
        """
        Put log event with specific message.
        """
        log = LogData(msg=msg, gateway_name=source)
        event = Event(EventType.INFO, log)
        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str) -> BaseGateway:
        """
        Return gateway object by name.
        """
        gateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(f"找不到底层接口：{gateway_name}")
        return gateway

    def get_engine(self, engine_name: str) -> "BaseEngine":
        """
        Return engine object by name.
        """
        engine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"找不到引擎：{engine_name}")
        return engine

    def get_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        """
        Get default setting dict of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self) -> List[str]:
        """
        Get all names of gatewasy added in main engine.
        """
        return list(self.gateways.keys())

    # def get_all_apps(self) -> List[BaseApp]:
    #     """
    #     Get all app objects.
    #     """
    #     return list(self.apps.values())

    def get_all_exchanges(self) -> List[Exchange]:
        """
        Get all exchanges.
        """
        return self.exchanges

    def connect(self, setting: dict, gateway_name: str) -> None:
        """
        Start connection of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)

    def subscribe(self, req: VNSubscribeRequest, gateway_name: str) -> None:
        """
        Subscribe tick data update of a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def send_order(self, req: VNOrderRequest, gateway_name: str) -> str:
        """
        Send new order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    def cancel_order(self, req: VNCancelRequest, gateway_name: str) -> None:
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def send_orders(self, reqs: Sequence[VNOrderRequest], gateway_name: str) -> List[str]:
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_orders(reqs)
        else:
            return ["" for req in reqs]

    def cancel_orders(self, reqs: Sequence[VNCancelRequest], gateway_name: str) -> None:
        """
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_orders(reqs)

    def query_history(self, req: VNHistoryRequest, gateway_name: str) -> Optional[List[BarData]]:
        """
        Send cancel order request to a specific gateway.
        """
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None

    def close(self) -> None:
        """
        Make sure every gateway and app is closed properly before
        programme exit.
        """
        # Stop event engine first to prevent new timer event.
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()




class LocalCtaEngine(BaseLocalEngine):
    """"""

    engine_type = EngineType.LIVE  # live trading engine

    setting_filename = "cta_strategy_setting.json"
    data_filename = "cta_strategy_data.json"

    def __init__(self, main_engine: LocalMainEngine, event_engine: EventEngine):
        """"""
        super().__init__(
            main_engine, event_engine, "LocalCtaEngine")

        self.id = os.getpid()
        self.ordercount = 0


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

        self.init_executor = ThreadPoolExecutor(max_workers=1)


        self.vt_tradeids = set()    # for filtering duplicate trade

    #   oms management, put it here

        self.ticks = {}
        self.orders = {}               # vt_orderid list
        self.trades = {}
        self.positions = {}
        self.accounts = {}
        self.contracts = {}
        self.active_orders = {}        # id list







        # self.offset_converter = OffsetConverter(self.main_engine)
        self.offset_converter = OffsetConverter(self)

        self.init_engine()

    def init_engine(self):
        """
        """


        self.load_strategy()

        self.load_strategy_setting()
        self.load_strategy_data()
        self.register_event()
        self.write_log("local CTA策略引擎初始化成功")

        m = Event(type=EventType.STRATEGY_CONTROL,
                    des='@0',
                    src=str(self.id),
                    msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_STATUS
                    )
        self.event_engine.put(m)


    def close(self):
        """"""
        self.stop_all_strategies()

    def register_event(self):
        """"""
        self.event_engine.register(EventType.TICK, self.process_tick_event)
        self.event_engine.register(EventType.ORDERSTATUS, self.process_order_event)
        self.event_engine.register(EventType.FILL, self.process_trade_event)
        self.event_engine.register(EventType.POSITION, self.process_position_event)
        self.event_engine.register(
            EventType.ACCOUNT, self.process_account_event)
        self.event_engine.register(
            EventType.CONTRACT, self.process_contract_event)
        self.event_engine.register(EventType.GENERAL_REQ, self.process_general_event)

        self.event_engine.register(EventType.STRATEGY_CONTROL, self.process_strategycontrol_event)

        SQGlobal.livestrategyloader.write_log = self.write_log

    def load_strategy(self,reload: bool = False):
        if reload:
            SQGlobal.livestrategyloader.load_class(True)  
        
        self.classes =  SQGlobal.livestrategyloader.classes

    def process_tick_event(self, event: Event):
        """"""
        tick = event.data

        strategies = self.symbol_strategy_map[tick.full_symbol]
        if not strategies:
            return


        for strategy in strategies:
            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_tick, tick)
        
        self.ticks[tick.full_symbol] = tick

    def process_order_event(self, event: Event):
        """"""
        order = event.data

        self.offset_converter.update_order(order)



        strategy = self.orderid_strategy_map.get(order.vt_orderid, None)
        if not strategy:
            print(order.vt_orderid, 'dont find strategy')
            return
        # update original order in self.orders, since the original order keeps the sec_type info
        if order.vt_orderid not in self.orders:
            return
        ori_order = self.orders[order.vt_orderid]
        ori_order.traded = order.traded
        ori_order.status = order.status
        ori_order.create_time = order.create_time
        

        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

        # Remove vt_orderid if order is no longer active.
        vt_orderids = self.strategy_orderid_map[strategy.strategy_name]
        if order.vt_orderid in vt_orderids and not order.is_active():
            vt_orderids.remove(order.vt_orderid)

        # Call strategy on_order function
        self.call_strategy_func(strategy, strategy.on_order, order)

    def process_trade_event(self, event: Event):
        """"""
        trade = event.data

        # Filter duplicate trade push
        if trade.vt_tradeid in self.vt_tradeids:
            return
        self.vt_tradeids.add(trade.vt_tradeid)

        self.offset_converter.update_trade(trade)

        strategy = self.orderid_strategy_map.get(trade.vt_orderid, None)
        if not strategy:
            return

        # Update strategy pos before calling on_trade method
        if trade.direction == Direction.LONG:
            strategy.pos += trade.volume
        else:
            strategy.pos -= trade.volume

        self.call_strategy_func(strategy, strategy.on_trade, trade)

        self.trades[trade.vt_tradeid] = trade

        # Sync strategy variables to data file
        self.sync_strategy_data(strategy)

        # Update GUI
        self.put_strategy_event(strategy)

    def process_position_event(self, event: Event):
        """"""
        position = event.data

        self.offset_converter.update_position(position)
        # different from SQ
        # key = position.gateway_name + '.' + position.vt_positionid

        self.positions[position.key] = position

    def process_account_event(self, event: Event):
        """"""
        account = event.data
        self.accounts[account.accountid] = account

    def process_contract_event(self, event: Event):
        """"""
        contract = event.data
        st = PRODUCT_VT2SQ[contract.product]
        contract.full_symbol = generate_full_symbol(
            contract.exchange, contract.symbol, st)    
                
        self.contracts[contract.full_symbol] = contract

    def process_general_event(self,event: Event):
        msgtype = event.msg_type
        if msgtype == MSG_TYPE.MSG_TYPE_CANCEL_ORDER:
            order = event.data
            self.main_engine.cancel_order(order, order.gateway_name)

    def process_strategycontrol_event(self, event: Event):
        
        msgtype = event.msg_type
        deslist = ['@*', str(self.id), '@' + str(self.id)]
        # print('localcta msg:',event.msg_type,event.destination)
        if (event.destination not in deslist):
            return
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_STATUS):
            m = Event(type=EventType.STRATEGY_CONTROL,
                      des='@0',
                      src=str(self.id),
                      msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_STATUS
                      )
            self.event_engine.put(m)

        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_ADD):
            v = event.data.split('|')
            classname = v[0]
            strname = v[1]
            fulsym = v[2]
            setting = json.loads(v[3])
            self.add_strategy(classname, strname, fulsym, setting)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_INIT):
            self.init_strategy(event.data)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_INIT_ALL):
            self.init_all_strategies()
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_START):
            self.start_strategy(event.data)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_START_ALL):
            self.start_all_strategies()
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_STOP):
            self.stop_strategy(event.data)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_STOP_ALL):
            self.stop_all_strategies()
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_RELOAD):
            self.classes.clear()
            self.load_strategy(True)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_RESET):
            self.reset_strategy(event.data)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_RESET_ALL):
            self.reset_all_strategies()
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_EDIT):
            v = event.data.split('|')
            setting = json.loads(v[1])
            self.edit_strategy(v[0], setting)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_REMOVE):
            if self.remove_strategy(event.data):
                m = Event(type=EventType.STRATEGY_CONTROL,
                          data=event.data,
                          des='@0',
                          src=str(self.id),
                          msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RTN_REMOVE
                          )
                # self._send_sock.send(m.serialize())
                self.event_engine.put(m)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_REMOVE_DUPLICATE):
            self.remove_strategy(event.data, True)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_GET_DATA):
            # print('begin get data')
            if event.data:
                strategy = self.strategies.get(event.data, None)
                if strategy:
                    self.put_strategy_event(strategy)
            else:  # get all strategy data
                for strategy in self.strategies.values():
                    self.put_strategy_event(strategy)







    def reset_all_strategies(self):
        for strategy_name in self.strategies.keys():
            self.reset_strategy(strategy_name)




    def send_order(
        self,
        strategy: StrategyBase,
        original_req: OrderRequest,
        lock: bool = False,
        stop:bool = False
    ):
        """
        """
        # Convert with offset converter
        req_list = self.offset_converter.convert_order_request(
            original_req, lock)

        # Send Orders
        orderids = []

        for req in req_list:
            req.clientID = self.id
            req.client_order_id = self.ordercount
            self.ordercount += 1

            # Note: req.api should be same as gateway_name
            if not req.gateway_name:
                req.gateway_name = req.api
            _orderid = self.main_engine.send_order(
                req, req.gateway_name)
                # req, req.api)                

            # Check if sending order successful
            if not _orderid:
                continue
            req.orderid = _orderid

            

            self.offset_converter.update_order_request(req)

            # save order, using vt_orderid as unique id, "gateway+orderid"
            req.vt_orderid = f"{req.gateway_name}.{req.orderid}"
            self.orders[req.vt_orderid] = req
            


            # Save relationship between orderid and strategy.
            self.orderid_strategy_map[req.vt_orderid] = strategy
            self.strategy_orderid_map[strategy.strategy_name].add(
                req.vt_orderid)

            orderids.append(req.vt_orderid)

        return orderids


    # note: different from SQ 
    def cancel_order(self, strategy: StrategyBase, vt_orderid: str):
        """
        """

        order = self.get_order(vt_orderid)
        if not order:
            self.write_log(f"撤单失败，找不到委托{vt_orderid}", strategy)
            return

        # req = order.create_cancel_request()

        self.main_engine.cancel_order(order, order.gateway_name)

    def cancel_all(self, strategy: StrategyBase):
        """
        Cancel all active orders of a strategy.
        """
        vt_orderids = self.strategy_orderid_map[strategy.strategy_name]
        if not vt_orderids:
            return

        for vt_orderid in copy(vt_orderids):
            self.cancel_order(strategy, vt_orderid)

    def get_engine_type(self):
        """"""
        return self.engine_type

    def get_pricetick(self, strategy: StrategyBase):
        """
        Return contract pricetick data.
        """
        contract = self.get_contract(strategy.full_symbol)

        if contract:
            return contract.pricetick
        else:
            return None

    def load_bar(
        self,
        full_symbol: str,
        days: int,
        interval: Interval,
        callback: Callable[[BarData], None],
        datasource: str = 'DataBase'
    ):
        """"""

        tradedays = abs(days)
        weekday = datetime.now().weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        symbol, exchange = extract_full_symbol(full_symbol)
        end = datetime.now()
        start = end - timedelta(days=tradedays)

        # Query bars from RQData by default, if not found, load from database.
        # bars = self.query_bar_from_rq(symbol, exchange, interval, start, end)
        # if not bars:

        bars = database_manager.load_bar_data(
            full_symbol=full_symbol,
            interval=interval,
            start=start,
            end=end,
        )

        for bar in bars:
            callback(bar)


    def load_tick(self, full_symbol: str, days: int, callback: Callable, datasource: str = 'DataBase'):
        tradedays = abs(days)
        weekday = datetime.now().weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        # symbol, exchange = extract_full_symbol(full_symbol)
        end = datetime.now()
        start = end - timedelta(tradedays)

        ticks = database_manager.load_tick_data(full_symbol, start, end)

        for tick in ticks:
            callback(tick)


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
        self, class_name: str, strategy_name: str, full_symbol: str, setting: dict
    ):
        """
        Add a new strategy.
        """
        if strategy_name in self.strategies:
            self.write_log(f"创建策略失败，存在重名{strategy_name}")
            return

        strategy_class = self.classes.get(class_name, None)
        if not strategy_class:
            self.write_log(f"创建策略失败，找不到策略类{class_name}")
            return

        # if "." not in vt_symbol:
        #     self.write_log("创建策略失败，本地代码缺失交易所后缀")
        #     return

        # _, exchange_str = vt_symbol.split(".")
        # if exchange_str not in Exchange.__members__:
        #     self.write_log("创建策略失败，本地代码的交易所后缀不正确")
        #     return

        strategy = strategy_class(self, strategy_name, full_symbol, setting)
        self.strategies[strategy_name] = strategy

        # Add full_symbol to strategy map.
        strategies = self.symbol_strategy_map[full_symbol]
        strategies.append(strategy)

        # Update to setting file.
        self.update_strategy_setting(strategy_name, setting)

        self.put_strategy_event(strategy)

    def init_strategy(self, strategy_name: str):
        """
        Init a strategy.
        """
        self.init_executor.submit(self._init_strategy, strategy_name)

    def _init_strategy(self, strategy_name: str):
        """
        Init strategies in queue.
        """
        strategy = self.strategies[strategy_name]

        if strategy.inited:
            self.write_log(f"{strategy_name}已经完成初始化，禁止重复操作")
            return

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
        contract = self.get_contract(strategy.full_symbol)
        if contract:
            req = VNSubscribeRequest(
                symbol=contract.symbol, exchange=contract.exchange)
            self.main_engine.subscribe(req, contract.gateway_name)
        else:
            self.write_log(f"行情订阅失败，找不到合约{strategy.full_symbol}", strategy)

        # Put event to update init completed status.
        strategy.inited = True
        self.put_strategy_event(strategy)
        self.write_log(f"{strategy_name}初始化完成")

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
        self.cancel_all(strategy)

        # Sync strategy variables to data file
        self.sync_strategy_data(strategy)

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

    def remove_strategy(self, strategy_name: str,duplicate: bool = False):
        """
        Remove a strategy.
        """
        strategy = self.strategies[strategy_name]
        if strategy.trading:
            self.write_log(f"策略{strategy.strategy_name}移除失败，请先停止")
            return

        # Remove setting
        if not duplicate:
            self.remove_strategy_setting(strategy_name)

        # Remove from symbol strategy map
        strategies = self.symbol_strategy_map[strategy.full_symbol]
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

    def reset_strategy(self, strategy_name: str):
        "Reset a strategy"
        strategy = self.strategies[strategy_name]
        if not strategy.inited:
            return
        # stop first
        self.call_strategy_func(strategy, strategy.on_stop)
        strategy.trading = False
        self.cancel_all(strategy)
        # reset
        self.call_strategy_func(strategy, strategy.on_reset)
        strategy.inited = False

        self.put_strategy_event(strategy)    

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
                strategy_config["full_symbol"],
                strategy_config["setting"]
            )

    def update_strategy_setting(self, strategy_name: str, setting: dict):
        """
        Update setting file.
        """
        strategy = self.strategies[strategy_name]

        self.strategy_setting[strategy_name] = {
            "class_name": strategy.__class__.__name__,
            "full_symbol": strategy.full_symbol,
            "setting": setting,
        }
        save_json(self.setting_filename, self.strategy_setting)

    def remove_strategy_setting(self, strategy_name: str):
        """
        Update setting file.
        """
        if strategy_name not in self.strategy_setting:
            return
        self.strategy_setting = load_json(self.setting_filename)
        self.strategy_setting.pop(strategy_name)
        save_json(self.setting_filename, self.strategy_setting)

    def put_stop_order_event(self, stop_order: StopOrder):
        """
        Put an event to update stop order status.
        """
        # event = Event(EVENT_CTA_STOPORDER, stop_order)
        # self.event_engine.put(event)
        pass

    def put_strategy_event(self, strategy: StrategyBase):
        """
        Put an event to update strategy status.
        """
        data = strategy.get_data()

        sdata = {}
        sdata[strategy.strategy_name] = data
        msg = json.dumps(sdata)

        m = Event(type=EventType.STRATEGY_CONTROL, data=msg, des='@0', src=str(
            self.id), msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RTN_DATA)

        self.event_engine.put(m)

    def write_log(self, msg: str, strategy: StrategyBase = None):
        """
        Create cta engine log event.
        """
        if strategy:
            msg = f"{strategy.strategy_name}: {msg}"

        log = LogData(msg=msg, gateway_name="LocalCtaEngine")
        event = Event(type=EventType.INFO, data=log)
        self.event_engine.put(event)

    # oms 
    def get_tick(self, full_symbol):
        """
        Get latest market tick data by full_symbol.
        """
        return self.ticks.get(full_symbol, None)

    def get_order(self, orderid):
        """
        Get latest order data by orderid.
        """
        return self.orders.get(orderid, None)

    def get_trade(self, vt_tradeid):
        """
        Get trade data by vt_tradeid.
        """
        return self.trades.get(vt_tradeid, None)

    def get_position(self, key):
        """
        Get latest position data by vt_positionid.
        """
        return self.positions.get(key, None)

    def get_account(self, accountid):
        """
        Get latest account data by accountid.
        """
        return self.accounts.get(accountid, None)

    def get_contract(self, full_symbol):
        """
        Get contract data by full_symbol.
        """
        return self.contracts.get(full_symbol, None)

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

    def get_all_active_orders(self, full_symbol: str = ""):
        """
        Get all active orders by full_symbol.

        If full_symbol is empty, return all active orders.
        """
        if not full_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.full_symbol == full_symbol
            ]
            return active_orders

    def get_position_holding(self, acc: str, full_symbol: str):
        return self.offset_converter.get_position_holding(acc, full_symbol)

    def get_strategy_active_orderids(self, strategy_name: str):
        oidset = self.strategy_orderid_map[strategy_name]
        return oidset
