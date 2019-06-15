#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue, Empty
from threading import Thread
from nanomsg import Socket, PAIR, SUB, PUB, PUSH,SUB_SUBSCRIBE, AF_SP,SOL_SOCKET,RCVTIMEO
from datetime import datetime, timedelta,time
import os,sys
import yaml
from collections import defaultdict
from copy import copy
import traceback
import importlib
from typing import Any, Callable
from pathlib import Path

from ..api.ctp_constant import THOST_FTDC_PT_Net
from ..common.datastruct import *
from ..common.utility import *
from ..strategy.strategy_base import StrategyBase
from ..data.rqdata import rqdata_client
from ..data import database_manager
from ..trade.portfolio_manager import OffsetConverter
from ..engine.iengine import BaseEngine,EventEngine


class StrategyEngine(BaseEngine):
    """
    Send to and receive from msg  server ,used for strategy 
    """
    config_filename = "config_server.yaml"
    setting_filename = "cta_strategy_setting.json"
    data_filename = "cta_strategy_data.json"
# init    
    def __init__(self,configfile:str = '',id :int = 1):
        super(StrategyEngine, self).__init__(event_engine=EventEngine(10))
        """
        two sockets to send and recv msg
        """
        self.__active = False
        self.id = os.getpid()
        self.engine_type = EngineType.LIVE     
        self._recv_sock = Socket(SUB)
        self._send_sock = Socket(PUSH)
        self._handlers = defaultdict(list)
        if configfile:            
            self.config_filename = configfile
        filepath = Path.cwd().joinpath("etc/" + self.config_filename)
        with open(filepath, encoding='utf8') as fd:
            self._config = yaml.load(fd)
        self.ordercount = 0

        #  stragegy manage
        self.strategy_setting = {}  # strategy_name: dict
        self.strategy_data = {}     # strategy_name: dict

        self.classes = {}           # class_name: stategy_class        
        self.strategies = {}        # strategy_name: strategy

        # self.classes_id = {}     # class_id : strategy
        # self.strategies_id = {}     # strategy_ID: strategy


        self.symbol_strategy_map = defaultdict(
            list)                   # full_symbol: strategy list
        self.orderid_strategy_map = {}  # vt_orderid: strategy
        self.strategy_orderid_map = defaultdict(
            set)                    # strategy_name: client_order_id list

        self.stop_order_count = 0   # for generating stop_orderid
        self.stop_orders = {}       # stop_orderid: stop_order
        self.init_thread = None
        self.init_queue = Queue()

        # order,tick,position ,etc manage
        self.ticks = {}
        self.orders = {}               # clientorder id list
        self.trades = {}
        self.positions = {}
        self.accounts = {}
        self.contracts = {}
        self.active_orders = {}        # SQ id list

        self.rq_client = None
        self.rq_symbols = set()

        self.offset_converter = OffsetConverter(self)

        self.autoinited = False
        self.autostarted = False
        self.dayswitched = False

        self.init_engine()

# init functions 
    def init_engine(self):
        self.init_nng()
        self.init_rqdata()
        self.load_contract()
        self.load_strategy_class()
        self.load_strategy_setting()
        self.load_strategy_data()  
        self.register_event()

    def init_nng(self):
        self._recv_sock.set_string_option(SUB, SUB_SUBSCRIBE, '')  # receive msg start with all
        self._recv_sock.set_int_option(SOL_SOCKET,RCVTIMEO,100)
        self._recv_sock.connect(self._config['serverpub_url'])
        self._send_sock.connect(self._config['serverpull_url'])

    def init_rqdata(self):

        result = rqdata_client.init()
        if result:
            self.write_log("RQData数据接口初始化成功")
    
    def load_contract(self):
        contractfile = Path.cwd().joinpath("etc/ctpcontract.yaml")
        with open(contractfile, encoding='utf8') as fc: 
            contracts = yaml.load(fc)
        print('loading contracts, total number:',len(contracts))
        for sym, data in contracts.items():
            contract = ContractData(
                symbol=data["symbol"],
                exchange=Exchange(data["exchange"]),
                name=data["name"],
                product=PRODUCT_CTP2VT[str(data["product"])],
                size=data["size"],
                pricetick=data["pricetick"],
                net_position = True if str(data["positiontype"]) == THOST_FTDC_PT_Net else False,
                long_margin_ratio = data["long_margin_ratio"],
                short_margin_ratio = data["short_margin_ratio"],
                full_symbol = data["full_symbol"]
            )            
            # For option only
            if contract.product == Product.OPTION:
                contract.option_underlying = data["option_underlying"],
                contract.option_type = OPTIONTYPE_CTP2VT.get(str(data["option_type"]), None),
                contract.option_strike = data["option_strike"],
                contract.option_expiry = datetime.strptime(str(data["option_expiry"]), "%Y%m%d"),
            self.contracts[contract.full_symbol] = contract

    def register_event(self):
        """"""
        self.event_engine.register(EventType.TICK, self.process_tick_event)
        self.event_engine.register(EventType.ORDERSTATUS, self.process_orderstatus_event)
        self.event_engine.register(EventType.FILL, self.process_trade_event)
        self.event_engine.register(EventType.POSITION, self.process_position_event)
        self.event_engine.register(EventType.ACCOUNT, self.process_account_event)
        self.event_engine.register(EventType.CONTRACT, self.process_contract_event)        
        self.event_engine.register(EventType.STRATEGY_CONTROL,self.process_strategycontrol_event)
        self.event_engine.register(EventType.HEADER,self.process_general_event)
        self.event_engine.register(EventType.TIMER,self.process_timer_event)
# event handler

    def process_timer_event(self,event):
        #auto init and start strategy at 8:57, 20:57
        nowtime = datetime.now().time()
        if (nowtime > time(hour=8, minute=55) ) and (nowtime < time(hour=8, minute=56)) and (not self.autoinited):
            for name, strategy in self.strategies.items():
                if strategy.autostart:
                    self.init_strategy(name)
            self.dayswitched = False
            self.autoinited = True
        if (nowtime > time(hour=20, minute=57) ) and (nowtime < time(hour=20, minute=58)) and (not self.autostarted):
            for name, strategy in self.strategies.items():
                if strategy.autostart:
                    self.start_strategy(name)        
            self.autostarted = True
            self.dayswitched = False

        # auto stop strategy at 14:57 and 22:57, 23:27, 00:27, 2:27 
        if (nowtime > time(hour=16, minute=0) ) and (nowtime < time(hour=16, minute=1)) and (not self.dayswitched):
            for name, strategy in self.strategies.items():
                if strategy.autostart:
                    self.reset_strategy(name)     
            self.dayswitched = True
            self.autostarted = False
            self.autoinited = False
        if (nowtime > time(hour=3, minute=0) ) and (nowtime < time(hour=3, minute=1)) and (not self.dayswitched):
            for name, strategy in self.strategies.items():
                if strategy.autostart:
                    self.reset_strategy(name)         
            self.dayswitched = True
            self.autostarted = False
            self.autoinited = False


    def process_general_event(self, event):
        for name, strategy in self.strategies.items():
            self.call_strategy_func(strategy, strategy.on_headermsg, event)
        pass

    def process_tick_event(self, event: Event):
        """"""
        tick = event.data

        strategies = self.symbol_strategy_map[tick.full_symbol]
        if not strategies:
            return
        # self.check_stop_order(tick)
        for strategy in strategies:
            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_tick, tick)
        self.ticks[tick.full_symbol] = tick

    def process_orderstatus_event(self, event: Event):
        """"""
        order = event.data

        self.offset_converter.update_order(order)

        if order.clientID != self.id:
            return

        self.orders[order.client_order_id] = order
        # If order is active, then update data in dict.
        if order.is_active():
            print('order is active')
            self.active_orders[order.client_order_id] = order
        # Otherwise, pop inactive order from in dict
        elif order.client_order_id in self.active_orders:
            self.active_orders.pop(order.client_order_id)  

        strategy = self.orderid_strategy_map.get(order.client_order_id, None)
        if not strategy:
            print(order.client_order_id, 'dont find strategy')
            return

        # Remove client_order_id if order is no longer active.
        client_order_ids = self.strategy_orderid_map[strategy.strategy_name]
        if (order.client_order_id in client_order_ids) and (not order.is_active()):
            print('rm inactive order in strategy order map')
            client_order_ids.remove(order.client_order_id)

        # For server stop order, call strategy on_stop_order function
        # if order.type == OrderType.STOP:
        #     so = StopOrder(
        #         full_symbol=order.full_symbol,
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

        
   

    def process_trade_event(self, event: Event):
        """"""
        trade = event.data

        self.offset_converter.update_trade(trade)

        if trade.clientID != self.id:
            return
        strategy = self.orderid_strategy_map.get(trade.client_order_id, None)
        if not strategy:
            return

        # if trade.direction == Direction.LONG:
        #     strategy.pos += trade.volume
        # else:
        #     strategy.pos -= trade.volume

        self.call_strategy_func(strategy, strategy.on_trade, trade)
        self.put_strategy_event(strategy)

        self.trades[trade.vt_tradeid] = trade
        #send qry pos to update position
        m = Event(type=EventType.QRY,
            des=event.source,
            src=str(self.id),
            msgtype=MSG_TYPE.MSG_TYPE_QRY_POS)
        self.put(m)

    def process_position_event(self, event: Event):
        """"""
        position = event.data

        self.offset_converter.update_position(position)

        self.positions[position.key] = position

    def process_account_event(self, event: Event):
        """"""
        account = event.data
        self.accounts[account.accountid] = account

    def process_contract_event(self, event: Event):
        """"""
        contract = event.data
        self.contracts[contract.full_symbol] = contract

    def process_strategycontrol_event(self,event:Event):
        msgtype = event.msg_type
        deslist = ['@*',str(self.id),'@'+str(self.id)]
        if (event.destination not in deslist ) :
            return
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_STATUS):
            m = Event(type=EventType.STRATEGY_CONTROL,
                des='@0',
                src=str(self.id),
                msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_STATUS
                )
            self._send_sock.send(m.serialize())
        # elif (event.destination not in deslist ) :
        #     return
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_ADD):
            v = event.data.split('|')
            classname = v[0]
            strname = v[1]
            fulsym = v[2]
            setting = json.loads(v[3])
            self.add_strategy(classname,strname,fulsym,setting)
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
            self.load_strategy_class(True)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_RESET):
            self.reset_strategy(event.data)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_RESET_ALL): 
            self.reset_all_strategies()
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_EDIT):
            v = event.data.split('|')
            setting = json.loads(v[1])
            self.edit_strategy(v[0],setting)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_REMOVE):
            if self.remove_strategy(event.data):
                m = Event(type=EventType.STRATEGY_CONTROL,
                data=event.data,
                des='@0',
                src=str(self.id),
                msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RTN_REMOVE
                )
                self._send_sock.send(m.serialize())
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_REMOVE_DUPLICATE):
            self.remove_strategy(event.data,True)
        elif (msgtype == MSG_TYPE.MSG_TYPE_STRATEGY_GET_DATA):
            # print('begin get data')
            if event.data:
                strategy = self.strategies.get(event.data,None)
                if strategy:
                    self.put_strategy_event(strategy)
            else : # get all strategy data
                for strategy in self.strategies.values():
                    self.put_strategy_event(strategy)
        

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
# strategy manage
    def add_strategy(
        self, class_name: str, strategy_name: str, full_symbol: str, setting: dict
    ):
        """
        Add a new strategy.
        """
        print("begin add strategy")
        if strategy_name in self.strategies:
            self.write_log(f"创建策略失败，存在重名{strategy_name}")
            return
        if class_name not in self.classes:
            self.write_log(f'strategy class[{class_name}] not exist, please check')
            return
        strategy_class = self.classes[class_name]

        strategy = strategy_class(self,strategy_name, full_symbol, setting)
        self.strategies[strategy_name] = strategy       

        # Add full_symbol to strategy map.
        strategies = self.symbol_strategy_map[full_symbol]
        strategies.append(strategy)
        # print("335 add strategy")
        # Update to setting file.
        self.update_strategy_setting(strategy_name, setting)

        self.put_strategy_event(strategy)
        print("end add strategy")
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
            contract = self.get_contract(strategy.full_symbol)
            if contract:
                m = Event(type=EventType.SUBSCRIBE,msgtype=MSG_TYPE.MSG_TYPE_SUBSCRIBE_MARKET_DATA)
                m.destination = "CTP.MD"
                m.source = str(self.id)
                req = SubscribeRequest()
                req.sym_type = SYMBOL_TYPE.CTP                
                req.content = contract.symbol
                m.data = req
                self._send_sock.send(m.serialize())
            else:
                self.write_log(f"行情订阅失败，找不到合约{strategy.full_symbol}", strategy)

            # qry pos and acc
            m = Event(type=EventType.QRY,msgtype=MSG_TYPE.MSG_TYPE_QRY_POS)
            m.destination = strategy.api + '.' + strategy.account
            m.source = str(self.id)
            self._send_sock.send(m.serialize())

            m = Event(type=EventType.QRY,msgtype=MSG_TYPE.MSG_TYPE_QRY_ACCOUNT)
            m.destination = strategy.api + '.' + strategy.account
            m.source = str(self.id)
            self._send_sock.send(m.serialize())

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
        self.cancel_all(strategy)

        # Update GUI
        self.put_strategy_event(strategy)
    def reset_strategy(self,strategy_name: str):
        "Reset a strategy"
        strategy = self.strategies[strategy_name]
        if not strategy.inited:
            return
        # stop first
        self.call_strategy_func(strategy, strategy.on_stop)
        strategy.trading = False
        self.cancel_all(strategy)
        # reset
        self.call_strategy_func(strategy,strategy.on_reset)
        strategy.inited = False

        self.put_strategy_event(strategy)

    def edit_strategy(self, strategy_name: str, setting: dict):
        """
        Edit parameters of a strategy.
        """
        strategy = self.strategies[strategy_name]
        strategy.update_setting(setting)

        self.update_strategy_setting(strategy_name, setting)
        self.put_strategy_event(strategy)

    def remove_strategy(self, strategy_name: str, duplicate:bool = False):
        """
        Remove a strategy.
        """
        print("begin remove")
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
            orderids = self.strategy_orderid_map.pop(strategy_name)

            # Remove vt_orderid strategy map
            for _orderid in orderids:
                if _orderid in self.orderid_strategy_map:
                    self.orderid_strategy_map.pop(_orderid)

        # Remove from strategies
        self.strategies.pop(strategy_name)
        print("end remove")
        return True

    def load_strategy_class(self,reload:bool=False):
        """
        Load strategy class from source code.
        """
        # app_path = Path(__file__).parent.parent
        # path1 = app_path.joinpath("cta_strategy", "strategies")
        # self.load_strategy_class_from_folder(
        #     path1, "vnpy.app.cta_strategy.strategies")

        path2 = Path.cwd().joinpath("mystrategy")
        self.load_strategy_class_from_folder(path2, "",reload)

    def load_strategy_class_from_folder(self, path: Path, module_name: str = "",reload:bool=False):
        """
        Load strategy class from certain folder.
        """
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".py"):
                    strategy_module_name = "mystrategy.".join(
                        [module_name, filename.replace(".py", "")])
                    self.load_strategy_class_from_module(strategy_module_name,reload)

    def load_strategy_class_from_module(self, module_name: str,reload:bool=False):
        """
        Load strategy class from module file.
        """
        try:
            module = importlib.import_module(module_name)
        # if reload delete old attribute
            if reload:
                for attr in dir(module):
                    if attr not in ('__name__','__file__'):
                        delattr(module,attr)
                importlib.reload(module)
            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate):
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

        self.strategy_data = load_json(self.data_filename)

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

    def reset_all_strategies(self):
        for strategy_name in self.strategies.keys():
            self.reset_strategy(strategy_name)

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
        # in order to save other engine's setting, should load again
        self.strategy_setting = load_json(self.setting_filename)
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
        # in order to save other engine's setting, should load again
        self.strategy_setting = load_json(self.setting_filename)
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
        sdata = {}
        sdata[strategy.strategy_name] = data
        # event = Event(EVENT_CTA_STRATEGY, data)
        # self.event_engine.put(event)
        msg = json.dumps(sdata)
        m = Event(type=EventType.STRATEGY_CONTROL,data=msg,des='@0',src=str(self.id),msgtype=MSG_TYPE.MSG_TYPE_STRATEGY_RTN_DATA)
        
        self._send_sock.send(m.serialize())

        # save_json(self.data_filename, sdata)
        
# strategy functions 
  #get ,qry  
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
        full_symbol: str, 
        days: int, 
        interval: Interval,
        callback: Callable[[BarData], None],
        datasource:str='DataBase'
    ):
        """"""

        tradedays = abs(days)
        weekday = datetime.now().weekday()
        adddays = 2 if (days-weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        symbol, exchange = extract_full_symbol(full_symbol)
        end = datetime.now()  
        start = end - timedelta(tradedays)
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

    def load_tick(self, full_symbol: str, days: int, callback: Callable,datasource:str='DataBase'):   
        tradedays = abs(days)
        weekday = datetime.now().weekday()
        adddays = 2 if (days-weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        symbol, exchange = extract_full_symbol(full_symbol)
        end = datetime.now()  
        start = end - timedelta(tradedays)

        ticks = database_manager.load_tick_data(symbol,exchange,start,end)
        
        for tick in ticks:
            callback(tick)



    
    def get_tick(self, full_symbol):
        """
        Get latest market tick data by full_symbol.
        """
        return self.ticks.get(full_symbol, None)

    def get_order(self, orderid:int):
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

    def get_position_holding(self, acc:str, full_symbol:str):
        return self.offset_converter.get_position_holding(acc,full_symbol)

    def get_strategy_active_orderids(self,strategy_name:str):
        oidset = self.strategy_orderid_map[strategy_name]
        return oidset
 


  #order, cancel
    def send_order(
        self,
        strategy: StrategyBase,
        original_req: OrderRequest,
        lock: bool = False
    ):
        """
        Send a new order to server.
        """
        # Convert with offset converter
        req_list = self.offset_converter.convert_order_request(original_req, lock)

        # Send Orders
        orderids = []

        for req in req_list:
            req.clientID = self.id
            req.client_order_id = self.ordercount 
            self.ordercount += 1
            m = Event(type=EventType.ORDER,
                    data=req,
                    des=req.api + '.' + req.account, 
                    src=str(self.id)
                )
            if req.api == "CTP.TD":
                m.msg_type = MSG_TYPE.MSG_TYPE_ORDER_CTP
            elif req.api == "PAPER.TD":
                m.msg_type = MSG_TYPE.MSG_TYPE_ORDER_PAPER
            else:
                print("error:api not support!")
                return []
            msg = m.serialize()
            print(f'tradeclient {self.id} send msg: {msg}')
            self._send_sock.send(msg)
            orderids.append(req.client_order_id)
            self.offset_converter.update_order_request(req)
            # Save relationship between orderid and strategy.
            self.orderid_strategy_map[req.client_order_id] = strategy
            self.strategy_orderid_map[strategy.strategy_name].add(req.client_order_id)
        
        return orderids

    def cancel_order(self, strategy: StrategyBase, orderid: int):
        """
        Cancel existing order by orderid.
        """
        order = self.get_order(orderid)
        if not order:
            self.write_log(f"撤单失败，找不到委托{orderid}", strategy)
            return

        req = order.create_cancel_request()
        m = Event(type=EventType.CANCEL,            
            data=req,
            des=order.api + '.'+ order.account,
            src=str(self.id),
            msgtype=MSG_TYPE.MSG_TYPE_ORDER_ACTION
            )
        msg = m.serialize()
        print(f'tradeclient {self.id} send msg: {msg}')
        self._send_sock.send(msg)
    
    def cancel_all(self, strategy: StrategyBase):
        """
        Cancel all active orders of a strategy.
        """
        orderids = self.strategy_orderid_map[strategy.strategy_name]
        if not orderids:
            print(strategy.strategy_name,'has no active order')
            return

        for orderid in copy(orderids):
            print('cancel oid:',orderid)
            self.cancel_order(strategy, orderid)


    def send_testmsg(self):
        m = Event(des='CTP.MD',src=str(self.id),msgtype=MSG_TYPE.MSG_TYPE_TEST)
        msg = m.serialize()
        self._send_sock.send(msg)
        print(f'tradeclient {self.id} send msg: {msg}')

# start and stop    
    def start(self, timer=True):
        """
        start the dispatcher thread and begin to recv msg through nng
        """
        self.event_engine.start()
        print('tradeclient started ,pid = %d ' % os.getpid())
        self.__active = True
        while self.__active:
            try:
                msgin = self._recv_sock.recv(flags=0)
                msgin = msgin.decode("utf-8")
                if msgin is not None and msgin.index('|') > 0:
                    if msgin[0] == '@':
                        print('tradeclient(pid = %d) rec @ msg:'%(self.id), msgin,'at ', datetime.now())
                    if msgin[-1] == '\0':
                        msgin = msgin[:-1]
                    if msgin[-1] == '\x00':
                        msgin = msgin[:-1]
                    m = Event()
                    m.deserialize(msgin)
                    self.event_engine.put(m)
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
        # self.event_engine.register(type_,handler)
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