#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date, time
from time import time as ttime
from typing import Union
from collections import defaultdict
from typing import Any, Callable
import multiprocessing
import traceback
import random
from itertools import product
from functools import lru_cache
import matplotlib.pyplot as plt
import numpy as np
from pandas import DataFrame
import pandas as pd
from deap import creator, base, tools, algorithms
# import ray


import pystarquant.common.sqglobal as SQGlobal

from pystarquant.common.constant import (
    Direction, Offset, Exchange,
    Interval, Status, EngineType,
    BacktestingMode, STOPORDER_PREFIX, StopOrderStatus
)
from pystarquant.common.datastruct import (
    OrderData, TradeData, BacktestTradeData,
    BarData, TickData, TBTBarData, StopOrder, ContractData
)
from pystarquant.common.utility import extract_full_symbol
from pystarquant.strategy.strategy_base import StrategyBase
from pystarquant.data import database_manager
from pystarquant.trade.portfolio_manager import PositionHolding


creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)


CtaTemplate = StrategyBase


class OptimizationSetting:
    """
    Setting for runnning optimization.
    """

    def __init__(self):
        """"""
        self.params = {}
        self.target_name = ""
        self.num_cpus = 1
        self.roll_period = 7
        self.use_roll = False

    def add_parameter(
        self, name: str, start: float, end: float = None, step: float = None
    ):
        """"""
        if not end and not step:
            self.params[name] = [start]
            return

        if start >= end:
            print("参数优化起始点必须小于终止点")
            return

        if step <= 0:
            print("参数优化步进必须大于0")
            return

        value = start
        value_list = []

        while value <= end:
            value_list.append(value)
            value += step

        self.params[name] = value_list

    def set_target(self, target_name: str):
        """"""
        self.target_name = target_name

    def generate_setting(self):
        """"""
        keys = self.params.keys()
        values = self.params.values()
        products = list(product(*values))

        settings = []
        for p in products:
            setting = dict(zip(keys, p))
            settings.append(setting)

        return settings    

    def set_num_cpus(self,n):
        self.num_cpus = n

    def set_roll_period(self,n):
        self.roll_period = n

    def set_use_roll(self,useroll):
        self.use_roll = useroll

    def generate_setting_ga(self):
        """"""
        settings_ga = []
        settings = self.generate_setting()
        for d in settings:
            param = [tuple(i) for i in d.items()]
            settings_ga.append(param)
        return settings_ga


class BacktestingProEngine:
    """
    multiple instruments/products support
    """

    engine_type = EngineType.BACKTESTING
    gateway_name = "BACKTESTINGPRO"

    def __init__(self, contracts:dict = None):
        """"""
        self.id = 0

        self.full_symbol = "SSE T Any 0"
        self.symbol = "Any"
        self.exchange = Exchange("SSE")
        # self.rate = 0
        # self.slippage = 0
        # self.size = 1
        # self.pricetick = 0
        self.start = None
        self.end = None
        self.capital = 1_000_000
        self.mode = BacktestingMode.BAR
        self.tbtmode = False

        self.datasource = 'DataBase'
        self.using_cursor = True
        self.dbcollection = ''
        self.dbtype=  None
        self.interval = None
        


        self.db_usingcursor = False
        self.contract_dict = {}
        if contracts:
            self.contract_dict = contracts

        self.xrd_dict = defaultdict(dict) # used in xr,xd, sym-> xrd_dict(date->(xr,xd))

        self.holding_dict = {}
        self.strategy_class = None
        self.strategy = None
        self.tick = None   # last tick
        self.bar = None    # last bar
        self.datetime = None  # last datetime


        self.days = 0
        self.callback = None
        self.historybar_callback = None  # used in tick mode called by strategy load_bar
        self.historytick_callback = None  # used in tick mode called by strategy load_tick
        self.history_data = []
        self.history_data_startix = 0
        self.history_data_endix = 1
        self.history_bar = []  # used in tick mode called by strategy load_bar
        self.history_bar_startix = 0
        self.history_bar_endix = 0
        self.history_tick = []  # used in tick mode called by strategy load_tick
        self.history_tick_startix = 0
        self.history_tick_endix = 0
        self.order_count = 0

        self.stop_order_count = 0
        self.stop_orders_dict = defaultdict(dict)   # symbol -> orderid dict
        self.active_stop_orders_dict = defaultdict(dict)   # symbol -> orderid dict

        self.limit_order_count = 0
        self.limit_orders_dict = defaultdict(dict)  # symbol -> orderid dict
        self.active_limit_orders_dict = defaultdict(dict)
        self.strategy_orderid_map = defaultdict(set)
        self.orderid_symbol_map = {}

        self.trade_count = 0
        self.trades = {}

        self.logs = []

        self.daily_results_dict = defaultdict(dict)  # symbol -> dailyresult dict
        self.total_daily_results = {}
        self.daily_df = None

        self.batch_daily_results_dict = defaultdict(dict)  # for batch mode
        self.batch_total_daily_results = {}
        self.batch_daily_df = None

    def clear_data(self):
        """
        Clear all data of last backtesting.
        """
        self.strategy = None
        self.tick = None 
        self.bar = None 
        self.datetime = None
        self.holding_dict.clear()
        # self.contract_dict = None

        self.stop_order_count = 0
        self.stop_orders_dict.clear()
        self.active_stop_orders_dict.clear()

        self.limit_order_count = 0
        self.limit_orders_dict.clear()
        self.active_limit_orders_dict.clear()
        self.strategy_orderid_map.clear()

        self.trade_count = 0
        self.trades.clear()

        self.logs.clear()
        self.daily_results_dict.clear()

        self.total_daily_results.clear()
        self.daily_df = None

    def clear_batch_data(self):
        self.batch_daily_results_dict = {}
        self.batch_total_daily_results = {}
        self.batch_daily_df = None


        
    def load_list_trades(self,trades):
        for trade in trades:
            self.trades[self.trade_count] = trade
            self.trade_count += 1        



    def set_parameters(
        self,
        datasource='DataBase',
        using_cursor: bool =True,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',
        interval: str ='1m',  
        full_symbol: str = 'SHFE F RB 88',
        start: datetime = datetime(2019, 1,1),
        end: datetime = None,
        capital: int = 0,
        contracts:dict = None,
        mode: BacktestingMode = BacktestingMode.BAR
    ):
        """"""       
        self.mode = mode
        self.full_symbol = full_symbol
        self.symbol, self.exchange = extract_full_symbol(self.full_symbol)

        self.datasource = datasource
        self.dbcollection = dbcollection
        self.dbtype = dbtype
        self.using_cursor = using_cursor


        if dbtype.endswith('Bar'):
            self.mode = BacktestingMode.BAR
            self.interval = Interval(interval)
        else:
            self.mode = BacktestingMode.TICK
            self.interval = Interval.MINUTE


        # if interval == 'tick':
        #     self.interval = Interval.MINUTE
        #     self.mode = BacktestingMode.TICK
        # elif interval == 'tbtbar':
        #     self.interval = Interval.MINUTE
        #     self.mode = BacktestingMode.BAR
        #     self.tbtmode = True
        # else:
        #     self.interval = Interval(interval)

        if type(start) == date:
            self.start = datetime(start.year,start.month,start.day)
        else:
            self.start = start

        if capital:
            self.capital = capital

        if end:
            if type(end) == date:
                self.end = datetime(end.year,end.month,end.day)
            else:
                self.end = end
        else:
            self.end = datetime.now()

        
        if contracts:
            self.contract_dict = contracts
        

    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(
            self, strategy_class.__name__, self.full_symbol, setting
        )
        # redirect strategy write_log output
        self.strategy.write_log = self.output

    def load_data(self):
        """"""
        self.output(f"开始加载历史数据:{self.start}-{self.end}")

        if self.mode == BacktestingMode.BAR:
            if self.datasource == "DataBase":
                if self.dbtype == 'TbtBar':
                    if self.using_cursor:
                        load_tbtbar_data.cache_clear()
                    self.history_data = load_tbtbar_data(
                        self.full_symbol,
                        self.interval,
                        self.start,
                        self.end,
                        self.dbcollection,
                        self.using_cursor
                    ) 
                elif self.dbtype == 'Bar': 
                    if self.using_cursor:
                        load_bar_data.cache_clear()                                       
                    self.history_data = load_bar_data(
                        self.full_symbol,
                        self.interval,
                        self.start,
                        self.end, 
                        self.dbcollection,
                        (';' in self.full_symbol),
                        self.using_cursor
                    )
                if type(self.history_data) == list:                         
                    self.history_data_startix = 0
                    self.history_data_endix = len(self.history_data)
            elif self.datasource == "Memory":
                fullsyminterval = self.full_symbol + '-' + self.interval.value
                if self.dbtype == 'TbtBar':
                    totalbarlist = SQGlobal.history_tbtbar[fullsyminterval]
                elif self.dbtype == 'Bar':
                    totalbarlist = SQGlobal.history_bar[fullsyminterval]
                if not totalbarlist:
                    self.output('数据为空，请先读入')
                    return
                totalbars = len(totalbarlist)
                startix = totalbars - 1
                endix = 0
                for i in range(totalbars):
                    if totalbarlist[i].datetime < self.start:
                        continue
                    startix = i
                    break
                for i in reversed(range(totalbars)):
                    if totalbarlist[i].datetime > self.end:
                        continue
                    endix = i
                    break
                endix = min(endix + 1, totalbars)
                if endix < startix:
                    endix = startix
                self.history_data_startix = startix
                self.history_data_endix = endix
                self.history_data = totalbarlist
        else:
            if self.datasource == "DataBase":
                if self.using_cursor:
                    load_tick_data.cache_clear()             
                self.history_data = load_tick_data(
                    self.full_symbol,
                    self.start,
                    self.end, 
                    self.dbcollection,
                    (';' in self.full_symbol),
                    self.using_cursor
                )
                if type(self.history_data) == list: 
                    self.history_data_startix = 0
                    self.history_data_endix = len(self.history_data)
            elif self.datasource == "Memory":
                totalticklist = SQGlobal.history_tick[self.full_symbol]
                if not totalticklist:
                    self.output('数据为空，请先读入')
                    return
                totalticks = len(totalticklist)
                startix = totalticks - 1
                endix = 0
                for i in range(totalticks):
                    if totalticklist[i].datetime < self.start:
                        continue
                    startix = i
                    break
                for i in reversed(range(totalticks)):
                    if totalticklist[i].datetime > self.end:
                        continue
                    endix = i
                    break
                endix = min(endix + 1, totalticks)
                if endix < startix:
                    endix = startix                
                self.history_data = totalticklist
                self.history_data_startix = startix
                self.history_data_endix = endix
        if type(self.history_data) == list: 
            self.output(
                f"历史数据加载完成，数据量：{self.history_data_endix - self.history_data_startix - 1}")
        else:
            self.output("得到历史数据游标")
    def set_data(self, data):
        self.history_data = data
        self.history_data_startix = 0
        self.history_data_endix = len(self.history_data)

    def run_backtesting(self):
        """"""
        if not self.history_data or self.history_data_startix == self.history_data_endix:
            self.output('回测数据为空，直接结束回测')
            return True

        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        else:
            func = self.new_tick
        try:
            self.strategy.on_init()

            self.strategy.inited = True
            self.output("策略初始化完成")

            self.strategy.on_start()
            self.strategy.trading = True
            self.output("开始回放历史数据")
            totalcount = 0
            if type(self.history_data) == list:
                for data in self.history_data[self.history_data_startix:self.history_data_endix]:
                    func(data)
                    totalcount += 1
                #  deal last data alonely,for some backtest use, such as close all positon in batch mode
                # lastdata = self.history_data[-1]
                # func(lastdata)
                # totalcount += 1
            else:
                if self.mode == BacktestingMode.BAR:
                    if self.dbtype == 'TbtBar':  
                        for data in self.history_data:
                            btdata = TBTBarData(
                                full_symbol=data["full_symbol"],
                                datetime=data["datetime"],
                                interval=self.interval,
                                volume=data["volume"],
                                open_price=data["open_price"],
                                high_price=data["high_price"],
                                low_price=data["low_price"],
                                close_price=data["close_price"],
                                ask_totalqty=data["ask_totalqty"],
                                bid_totalqty=data["bid_totalqty"],
                                ask_totalmoney=data["ask_totalmoney"],
                                bid_totalmoney=data["bid_totalmoney"],
                                ask_bigmoney=data["ask_bigmoney"],
                                bid_bigmoney=data["bid_bigmoney"],
                                ask_bigleft=data["ask_bigleft"],
                                bid_bigleft=data["bid_bigleft"],
                                user_defined_1=data["user_defined_1"] if "user_defined_1" in data else 0.0
                                )
                            func(btdata)
                            totalcount += 1
                    elif self.dbtype == 'Bar':
                        for data in self.history_data:
                            btdata = BarData(
                                symbol=data["symbol"],
                                full_symbol=data["full_symbol"],
                                datetime=data["datetime"],
                                exchange=Exchange(data["exchange"]),
                                interval=self.interval,
                                volume=data["volume"],
                                open_interest=data["open_interest"],
                                open_price=data["open_price"],
                                high_price=data["high_price"],
                                low_price=data["low_price"],
                                close_price=data["close_price"]
                                )
                            func(btdata)
                            totalcount += 1
                else:
                    if self.dbtype == 'Tick':
                        for data in self.history_data:
                            btdata = TickData(
                                full_symbol=data["full_symbol"],
                                symbol=data["symbol"],
                                datetime=data["datetime"],
                                exchange=Exchange(data["exchange"]),
                                ask_price_1=data["ask_price_1"],
                                ask_volume_1=data["ask_volume_1"],
                                bid_price_1=data["bid_price_1"],
                                bid_volume_1=data["bid_volume_1"],
                                last_price=data["last_price"],
                                volume=data["volume"],
                                open_interest=data["open_interest"],
                                limit_up=data["limit_up"],
                                limit_down=data["limit_down"],
                                open_price=data["open_price"],
                                pre_close=data["pre_close"],
                                high_price=data["high_price"],
                                low_price=data["low_price"]
                                )
                            func(btdata)
                            totalcount += 1

            self.strategy.on_finish()

        except:            
            msg = f"回测异常:\n{traceback.format_exc()}"
            self.output(msg) 
            return False   
        self.output(f"总共{totalcount}个历史数据回放结束")
        return True

    def calculate_result(self):
        """"""
        self.output("开始计算逐日盯市盈亏")

        if not self.trades:
            self.output("成交记录为空，无法计算")
            self.daily_df = None
            return

        # Add trade data into daily reuslt.
        trades_daily_results = {}
        for trade in self.trades.values():
            sym = trade.full_symbol
            d = trade.datetime.date()
            t = trade.datetime.time()
            if t > time(hour=17, minute=0):
                if d.weekday() == 4:
                    d = d + timedelta(days=3)
                else:
                    d = d + timedelta(days=1)
            elif t < time(hour=8, minute=0):  # 周六凌晨算周一
                if d.weekday() == 5:
                    d = d + timedelta(days=2)
            daily_result = self.daily_results_dict[sym][d]            
            daily_result.add_trade(trade)
            trades_daily_result = trades_daily_results.setdefault(d, DailyResult(d,0))
            trades_daily_result.add_trade(trade)




        # Calculate each symbol's daily result by iteration .
        for sym, daily_results in self.daily_results_dict.items():
            pre_close = 0
            start_pos = 0
            pre_day = date(2000,1,1)
            contract  = self.contract_dict.setdefault(sym, ContractData(full_symbol=sym))
            xrddict = self.xrd_dict.get(sym, None)
            for tradeday, daily_result in daily_results.items():
                # 20200808 xr,xd
                if xrddict :
                    for xrddate, (xr,xd) in xrddict.items():
                        if pre_day < xrddate and tradeday >= xrddate: # xr,xd
                            pre_close -= xd
                            pre_close = pre_close *xr
                            break
                daily_result.calculate_pnl(
                    pre_close, start_pos, contract.size, contract.rate, contract.slippage
                )
                pre_close = daily_result.close_price
                start_pos = daily_result.end_pos
                pre_day = tradeday

        # Calculate margin used daily result by iteration .
        pre_margin = 0
        for _t, daily_result in sorted(trades_daily_results.items()):
            daily_result.calculate_margin(pre_margin, self.contract_dict)
            pre_margin = daily_result.margin


        # Calculate daily result by summation of symbols.
        total_daily_results = {}
        for daily_results in self.daily_results_dict.values():
            for datekey, dailyresult in daily_results.items():
                total_daily_result = total_daily_results.setdefault(datekey, DailyResult(datekey,0))
                total_daily_result.trade_count += dailyresult.trade_count
                total_daily_result.start_pos += dailyresult.start_pos
                total_daily_result.end_pos += dailyresult.end_pos
                total_daily_result.turnover += dailyresult.turnover
                total_daily_result.commission += dailyresult.commission
                total_daily_result.slippage += dailyresult.slippage
                total_daily_result.trading_pnl += dailyresult.trading_pnl
                total_daily_result.holding_pnl += dailyresult.holding_pnl
                total_daily_result.total_pnl += dailyresult.total_pnl
                total_daily_result.net_pnl += dailyresult.net_pnl

                trade_daily_result = trades_daily_results.get(datekey, DailyResult(datekey,0))
                total_daily_result.maxmargin = trade_daily_result.maxmargin

        self.total_daily_results = dict(sorted(total_daily_results.items()))
        # Generate dataframe
        results = defaultdict(list)

        for _t, daily_result in self.total_daily_results.items():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return self.daily_df

    def calculate_result_tbt(self):
        self.daily_results_dict.clear()

        self.output("开始计算逐日逐笔盈亏(忽略浮盈)")

        if not self.trades:
            self.output("成交记录为空，无法计算")
            self.daily_df = None
            return

        # Add trade data into daily reuslt.
        trades_daily_results = {}
        for trade in sorted(self.trades.values(), key=lambda x:x.datetime):
            sym = trade.full_symbol
            d = trade.datetime.date()
            t = trade.datetime.time()
            if t > time(hour=17, minute=0):
                if d.weekday() == 4:
                    d = d + timedelta(days=3)
                else:
                    d = d + timedelta(days=1)
            elif t < time(hour=8, minute=0):  # 周六凌晨算周一
                if d.weekday() == 5:
                    d = d + timedelta(days=2)
            daily_result = self.daily_results_dict[sym].setdefault(d,DailyResult(d, 0))
            daily_result.add_trade(trade)
            trades_daily_result = trades_daily_results.setdefault(d, DailyResult(d,0))
            trades_daily_result.add_trade(trade)



        # Calculate each symbol's daily result by iteration .
        for sym, daily_results in self.daily_results_dict.items():
            open_price = 0
            start_pos = 0
            contract  = self.contract_dict.setdefault(sym, ContractData(full_symbol=sym))
            for daily_result in daily_results.values():
                daily_result.calculate_pnltbt(
                    open_price, start_pos, contract.size, contract.rate, contract.slippage
                )
                open_price = daily_result.open_price
                start_pos = daily_result.end_pos

        # Calculate margin used daily result by iteration .
        pre_margin = 0
        for _t, daily_result in sorted(trades_daily_results.items()):
            daily_result.calculate_margin(pre_margin, self.contract_dict)
            pre_margin = daily_result.margin


        # Calculate daily result by summation of symbols.
        total_daily_results = {}
        for daily_results in self.daily_results_dict.values():
            for datekey, dailyresult in daily_results.items():
                total_daily_result = total_daily_results.setdefault(datekey, DailyResult(datekey,0))
                total_daily_result.trade_count += dailyresult.trade_count
                total_daily_result.start_pos += dailyresult.start_pos
                total_daily_result.end_pos += dailyresult.end_pos
                total_daily_result.turnover += dailyresult.turnover
                total_daily_result.commission += dailyresult.commission
                total_daily_result.slippage += dailyresult.slippage
                total_daily_result.trading_pnl += dailyresult.trading_pnl
                total_daily_result.holding_pnl += dailyresult.holding_pnl
                total_daily_result.total_pnl += dailyresult.total_pnl
                total_daily_result.net_pnl += dailyresult.net_pnl

                trade_daily_result = trades_daily_results.get(datekey, DailyResult(datekey,0))
                total_daily_result.maxmargin = trade_daily_result.maxmargin

        self.total_daily_results = dict(sorted(total_daily_results.items()))
        # Generate dataframe
        results = defaultdict(list)

        for _t, daily_result in self.total_daily_results.items():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日逐笔盈亏计算完成")
        return self.daily_df


    def calculate_batch_result(self):
        self.output("开始逐个批次逐个标的逐日盯市盈亏汇总")


        # Add trade data into daily reuslt.
        trades_daily_results = {}
        for trade in sorted(self.trades.values(), key=lambda x:x.datetime):
            d = trade.datetime.date()
            t = trade.datetime.time()
            if t > time(hour=17, minute=0):
                if d.weekday() == 4:
                    d = d + timedelta(days=3)
                else:
                    d = d + timedelta(days=1)
            elif t < time(hour=8, minute=0):  # 周六凌晨算周一
                if d.weekday() == 5:
                    d = d + timedelta(days=2)
            trades_daily_result = trades_daily_results.setdefault(d, DailyResult(d,0))
            trades_daily_result.add_trade(trade)

        # Calculate margin used daily result by iteration .
        pre_margin = 0
        for _t, daily_result in sorted(trades_daily_results.items()):
            daily_result.calculate_margin(pre_margin, self.contract_dict)
            pre_margin = daily_result.margin





        for daily_results in self.batch_daily_results_dict.values():# each total_daily_results in batch
            for datekey, dailyresult in daily_results.items():
                total_daily_result = self.batch_total_daily_results.setdefault(datekey, DailyResult(datekey,0))
                total_daily_result.trade_count += dailyresult.trade_count
                total_daily_result.start_pos += dailyresult.start_pos
                total_daily_result.end_pos += dailyresult.end_pos
                total_daily_result.turnover += dailyresult.turnover
                total_daily_result.commission += dailyresult.commission
                total_daily_result.slippage += dailyresult.slippage
                total_daily_result.trading_pnl += dailyresult.trading_pnl
                total_daily_result.holding_pnl += dailyresult.holding_pnl
                total_daily_result.total_pnl += dailyresult.total_pnl
                total_daily_result.net_pnl += dailyresult.net_pnl

                trade_daily_result = trades_daily_results.get(datekey, DailyResult(datekey,0))
                total_daily_result.maxmargin = trade_daily_result.maxmargin


        results = defaultdict(list)
        self.batch_total_daily_results = dict(sorted(self.batch_total_daily_results.items()))
        #按照key（时间）排序
        for _t, daily_result in self.batch_total_daily_results.items():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)
        if results:
            self.batch_total_daily_df = DataFrame.from_dict(results).set_index("date")

            self.output("逐个批次逐个标的盈亏加和统计完成")
            return self.batch_total_daily_df
        else:
            self.output("记录为空,无法计算")
            return


    def calculate_statistics(self, df: DataFrame = None, output=True, trades: list = None):
        """"""
        self.output("开始计算策略统计指标")

        if (df is None) or (df.empty):
            df = self.daily_df

        if df is None:
            # Set all statistics to 0 if no trade.
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            recent_drawdown = 0
            recent_ddpercent = 0
            max_drawdown_duration = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_turnover = 0
            return_std = 0
            sharpe_ratio = 0
            return_drawdown_ratio = 0
            winratio = 0
            winloss = 0
            profit_per_trade = 0
            long_count = 0
            short_count = 0
            long_profit = 0
            short_profit = 0
            long_profit_per_trade = 0
            short_profit_per_trade = 0
            longwinratio = 0
            longwinloss = 0
            shortwinratio = 0
            shortwinloss = 0

            maxmargin = 0
        else:
            # Calculate balance related time series data
            maxmargin = df['maxmargin'].max()

            df["balance"] = df["net_pnl"].cumsum() + self.capital
            minbalance = df["balance"].min()

            df["return"] = np.log(
                df["balance"] / df["balance"].shift(1)).fillna(0)


            df["highlevel"] = (
                df["balance"].rolling(
                    min_periods=1, window=len(df), center=False).max()
            )
            df["drawdown"] = df["balance"] - df["highlevel"]
            df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

            # Calculate statistics value
            start_date = df.index[0]
            end_date = df.index[-1]

            total_days = len(df)
            #TODO：对于读取过去成交记录计算指标情况下，只有成交对应的天数，少于交易日，不准确,先按照2/3自然日折算
            total_days_2 = int ( (end_date - start_date) / timedelta(days=1) * 2 / 3 )
            total_days = max(total_days, total_days_2)


            
            profit_days = len(df[df["net_pnl"] > 0])
            loss_days = len(df[df["net_pnl"] < 0])

            end_balance = df["balance"].iloc[-1]
            max_drawdown = df["drawdown"].min()
            max_ddpercent = df["ddpercent"].min()
            recent_drawdown = df["drawdown"].iloc[-1]
            recent_ddpercent = df["ddpercent"].iloc[-1]
            max_drawdown_end = df["drawdown"].idxmin()
            max_drawdown_start = df["balance"][:max_drawdown_end].argmax()
            max_drawdown_duration = (max_drawdown_end - max_drawdown_start).days


            total_net_pnl = df["net_pnl"].sum()
            daily_net_pnl = total_net_pnl / total_days

            total_commission = df["commission"].sum()
            daily_commission = total_commission / total_days

            total_slippage = df["slippage"].sum()
            daily_slippage = total_slippage / total_days

            total_turnover = df["turnover"].sum()
            daily_turnover = total_turnover / total_days

            total_trade_count = df["trade_count"].sum()
            daily_trade_count = total_trade_count / total_days

            total_return = (end_balance / self.capital - 1) * 100
            annual_return = total_return / total_days * 240

            if minbalance > 0:
                daily_return = df["return"].mean() * 100
            else:
                daily_return = 0.0

            if minbalance > 0:
                return_std = df["return"].std() * 100
            else:
                return_std = 0.0
            
            profit_per_trade = total_net_pnl / total_trade_count if total_trade_count else 0

            if return_std and minbalance > 0:
                sharpe_ratio = daily_return / return_std * np.sqrt(240)
            else:
                sharpe_ratio = 0
            if max_ddpercent:
                return_drawdown_ratio = -total_return / max_ddpercent
            else:
                return_drawdown_ratio = 0

            if total_turnover:
                return_turnover = total_net_pnl*10000 / total_turnover
            else:
                return_turnover = 0.0

            wincount = 0
            winmoney = 0
            losscount = 0
            lossmoney = 0
            longwincount = 0
            longwinmoney = 0
            longlosscount = 0
            longlossmoney = 0
            shortwincount = 0
            shortwinmoney = 0
            shortlosscount = 0
            shortlossmoney = 0

            long_count = 0
            short_count = 0
            long_profit = 0
            short_profit = 0
            long_profit_per_trade = 0
            short_profit_per_trade = 0


            if not trades:
                trades = self.trades.values()
            for trade in trades:
                netpnl = trade.long_pnl + trade.short_pnl - trade.slippage - trade.commission
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    long_count += 1
                    long_profit += netpnl
                elif trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    short_count += 1                    
                    short_profit += netpnl
                    if (netpnl) > 0:
                        wincount += 1
                        winmoney += netpnl
                        shortwincount += 1
                        shortwinmoney += netpnl
                    elif (netpnl) < 0:
                        losscount += 1
                        lossmoney += abs(netpnl)
                        shortlosscount += 1
                        shortlossmoney += abs(netpnl)
                elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    short_count += 1
                    short_profit += netpnl
                elif trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    long_count += 1
                    long_profit += netpnl
                    if (netpnl) > 0:
                        wincount += 1
                        winmoney += netpnl
                        longwincount += 1
                        longwinmoney += netpnl
                    elif (netpnl) < 0:
                        losscount += 1
                        lossmoney += abs(netpnl)
                        longlosscount += 1
                        longlossmoney += abs(netpnl)

            if long_count:
                long_profit_per_trade = long_profit / long_count
            else:
                long_profit_per_trade = 0
            if short_count:
                short_profit_per_trade = short_profit / short_count
            else:
                short_profit_per_trade = 0

            if (wincount + losscount):
                winratio = wincount / (wincount + losscount)
            else:
                winratio = 0.0
            if wincount and losscount and lossmoney:
                winloss = (winmoney / wincount) / (lossmoney / losscount)
            else:
                winloss = 0.0

            if (longwincount + longlosscount):
                longwinratio = longwincount / (longwincount + longlosscount)
            else:
                longwinratio = 0.0
            if longwincount and longlosscount and longlossmoney:
                longwinloss = (longwinmoney / longwincount) / (longlossmoney / longlosscount)
            else:
                longwinloss = 0.0

            if (shortwincount + shortlosscount):
                shortwinratio = shortwincount / (shortwincount + shortlosscount)
            else:
                shortwinratio = 0.0
            if shortwincount and shortlosscount and shortlossmoney:
                shortwinloss = (shortwinmoney / shortwincount) / (shortlossmoney / shortlosscount)
            else:
                shortwinloss = 0.0

        # Output
        if output:
            self.output("-" * 30)
            self.output(f"首个交易日：\t{start_date}")
            self.output(f"最后交易日：\t{end_date}")

            self.output(f"总交易日：\t{total_days}")
            self.output(f"盈利交易日：\t{profit_days}")
            self.output(f"亏损交易日：\t{loss_days}")

            self.output(f"起始资金：\t{self.capital:,.2f}")
            self.output(f"结束资金：\t{end_balance:,.2f}")

            self.output(f"总收益率：\t{total_return:,.2f}%")
            self.output(f"年化收益：\t{annual_return:,.2f}%")
            self.output(f"最大回撤: \t{max_drawdown:,.2f}")
            self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")

            self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
            self.output(f"总手续费：\t{total_commission:,.2f}")
            self.output(f"总滑点：\t{total_slippage:,.2f}")
            self.output(f"总成交金额：\t{total_turnover:,.2f}")
            self.output(f"总成交笔数：\t{total_trade_count}")

            self.output(f"日均盈亏：\t{daily_net_pnl:,.2f}")
            self.output(f"日均手续费：\t{daily_commission:,.2f}")
            self.output(f"日均滑点：\t{daily_slippage:,.2f}")
            self.output(f"日均成交金额：\t{daily_turnover:,.2f}")
            self.output(f"日均成交笔数：\t{daily_trade_count}")

            self.output(f"日均收益率：\t{daily_return:,.2f}%")
            self.output(f"收益标准差：\t{return_std:,.2f}%")
            self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
            self.output(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": self.capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "recent_drawdown": recent_drawdown,
            "recent_ddpercent": recent_ddpercent,
            "max_drawdown_duration": max_drawdown_duration,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_turnover":return_turnover,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
            "win_ratio": winratio,
            "win_loss": winloss,
            "long_win_ratio": longwinratio,
            "short_win_ratio": shortwinratio,
            "long_win_loss": longwinloss,
            "short_win_loss": shortwinloss,
            "profit_per_trade":profit_per_trade,
            "long_profit": long_profit,
            "short_profit": short_profit,
            "long_count":long_count,
            "short_count":short_count,
            "long_profit_per_trade":long_profit_per_trade,
            "short_profit_per_trade":short_profit_per_trade,
            "maxmargin":maxmargin,

        }

        return statistics


    def show_chart(self, df: DataFrame = None):
        """"""
        if not df:
            df = self.daily_df

        if df is None:
            return

        plt.figure(figsize=(10, 16))

        balance_plot = plt.subplot(4, 1, 1)
        balance_plot.set_title("Balance")
        df["balance"].plot(legend=True)

        drawdown_plot = plt.subplot(4, 1, 2)
        drawdown_plot.set_title("Drawdown")
        drawdown_plot.fill_between(range(len(df)), df["drawdown"].values)

        pnl_plot = plt.subplot(4, 1, 3)
        pnl_plot.set_title("Daily Pnl")
        df["net_pnl"].plot(kind="bar", legend=False, grid=False, xticks=[])

        distribution_plot = plt.subplot(4, 1, 4)
        distribution_plot.set_title("Daily Pnl Distribution")
        df["net_pnl"].hist(bins=50)

        plt.show()


    def run_mp_backtest_pro(
        self,
        cpunums,
        strategy_classes,
        settinglist: dict,
        capital: int,
        contracts:dict,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',
        interval: str = '1m'
    ):

        pool = multiprocessing.Pool(cpunums)
        results = []

        class_namelist = settinglist['strategy']
        stragegysettinglist = settinglist['parameter']
        fsmlist = settinglist['full_symbol']
        startlist = settinglist['start']
        endlist = settinglist['end']
        intervallist = settinglist['interval']

        for i in range(len(fsmlist)):
            class_name = class_namelist[i]
            setting = eval(stragegysettinglist[i])
            strategy_class = strategy_classes[class_name]
            full_symbol = fsmlist[i]
            start = startlist[i]
            end = endlist[i]
            dbinterval = intervallist[i]

            result = (pool.apply_async(mp_backtest_pro, (
                strategy_class,
                setting,
                full_symbol,
                start,
                end,
                capital,
                contracts,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                dbinterval
            )))
         
            results.append(result)

        pool.close()
        pool.join()

        result_values = [result.get() for result in results]
        return result_values


    def run_optimization(self, 
        optimization_setting: OptimizationSetting, 
        output=True, 
        ):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        target_name = optimization_setting.target_name
        num_cpus = optimization_setting.num_cpus

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        pool = multiprocessing.Pool(num_cpus)

        results = []
        # should use original interval info, since opt will use new engine to run backtesting
        # if self.tbtmode:
        #     interval = 'tbtbar'
        # elif self.mode == BacktestingMode.TICK:
        #     interval = 'tick'
        # else:
        #     interval = self.interval

        for setting in settings:
            if not self.strategy.parameter_filter(setting):
                continue
            result = (pool.apply_async(optimize_pro, (
                target_name,
                self.strategy_class,
                setting,
                self.full_symbol,
                self.start,
                self.end,
                self.capital,
                self.contract_dict,
                self.mode,
                self.datasource,
                self.using_cursor,
                self.dbcollection,
                self.dbtype,
                self.interval.value
            )))
            results.append(result)

        pool.close()
        pool.join()

        # Sort results and output
        result_values = [result.get() for result in results]
        result_values.sort(reverse=True, key=lambda result: result[1])

        if output:
            for value in result_values:
                msg = f"参数：{value[0]}, 目标：{value[1]}"
                self.output(msg)

        return result_values




    def run_roll_optimization(self, 
        optimization_setting: OptimizationSetting,
        ):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        rollperiod = optimization_setting.roll_period
        num_cpus = optimization_setting.num_cpus

        if not settings:
            self.output("滚动优化参数组合为空，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        pool = multiprocessing.Pool(num_cpus)

        results = []
        # should use original interval info, since opt will use new engine to run backtesting
        # if self.tbtmode:
        #     interval = 'tbtbar'
        # elif self.mode == BacktestingMode.TICK:
        #     interval = 'tick'
        # else:
        #     interval = self.interval

        for setting in settings:
            if not self.strategy.parameter_filter(setting):
                continue
            result = (pool.apply_async(roll_optimize_pro, (
                self.strategy_class,
                setting,
                self.full_symbol,
                self.start,
                self.end,
                self.capital,
                self.contract_dict,
                self.mode,
                self.datasource,
                self.using_cursor,
                self.dbcollection,
                self.dbtype,
                self.interval.value
            )))
            results.append(result)

        pool.close()
        pool.join()


        # Sort results and output
        result_values = [result.get() for result in results]
        roll_df = pd.Series()
        rollstartdate = self.start.date()
        rollenddate = self.end.date()
        rolldate = rollstartdate + timedelta(days=90)
        rollsettinglist = []
        rolldatelist = []
        while rolldate < rollenddate:
            tmpsetting, tmpdf = self.strategy.roll_choose(result_values,self.start.date(),rolldate)
            rollsettinglist.append(tmpsetting)
            rolldatelist.append(rollstartdate)
            nextrolldate = rolldate + timedelta(days=rollperiod)
            roll_df = roll_df.append(tmpdf[rollstartdate:nextrolldate])            
            rolldate = nextrolldate
            rollstartdate = rolldate + timedelta(days=1)



        return (rolldatelist,rollsettinglist, roll_df)











    def run_ga_optimization(self, 
        optimization_setting: OptimizationSetting, 
        population_size=100, 
        ngen_size=30, 
        output=True, 
        ):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting_ga()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return
        # Define parameter generation function
        def generate_parameter():
            """"""
            return random.choice(settings)

        def mutate_individual(individual, indpb):
            """"""
            size = len(individual)
            paramlist = generate_parameter()
            for i in range(size):
                if random.random() < indpb:
                    individual[i] = paramlist[i]
            return individual,

        # Create ga object function
        global ga_target_name
        global ga_strategy_class
        global ga_setting
        global ga_full_symbol
        global ga_start
        # global ga_rate
        # global ga_slippage
        # global ga_size
        # global ga_pricetick
        global ga_capital
        global ga_contracts
        global ga_end
        global ga_mode
        global ga_datasource
        global ga_using_cursor
        global ga_dbcollection
        global ga_dbtype
        global ga_interval

        ga_target_name = target_name
        ga_strategy_class = self.strategy_class
        ga_setting = settings[0]
        ga_full_symbol = self.full_symbol

        # if self.tbtmode:
        #     interval = 'tbtbar'
        # elif self.mode == BacktestingMode.TICK:
        #     interval = 'tick'
        # else:
        #     interval = self.interval


        ga_start = self.start
        # ga_rate = self.rate
        # ga_slippage = self.slippage
        # ga_size = self.size
        # ga_pricetick = self.pricetick
        ga_capital = self.capital
        ga_contracts = self.contract_dict
        ga_end = self.end
        ga_mode = self.mode
        ga_datasource = self.datasource
        ga_using_cursor = self.using_cursor
        ga_dbcollection = self.dbcollection
        ga_dbtype = self.dbtype
        ga_interval = self.interval.value

        # Set up genetic algorithem
        toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate,
                         creator.Individual, generate_parameter)
        toolbox.register("population", tools.initRepeat,
                         list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", mutate_individual, indpb=1)
        toolbox.register("evaluate", ga_optimize_pro)
        toolbox.register("select", tools.selNSGA2)

        total_size = len(settings)
        # number of individuals in each generation
        pop_size = population_size
        # number of children to produce at each generation
        lambda_ = pop_size
        # number of individuals to select for the next generation
        mu = int(pop_size * 0.8)

        cxpb = 0.95         # probability that an offspring is produced by crossover
        mutpb = 1 - cxpb    # probability that an offspring is produced by mutation
        ngen = ngen_size    # number of generation

        pop = toolbox.population(pop_size)
        hof = tools.ParetoFront()               # end result of pareto front

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        np.set_printoptions(suppress=True)
        stats.register("mean", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        # Multiprocessing is not supported yet.
        # pool = multiprocessing.Pool(multiprocessing.cpu_count())
        # toolbox.register("map", pool.map)

        # Run ga optimization
        self.output(f"参数优化空间：{total_size}")
        self.output(f"每代族群总数：{pop_size}")
        self.output(f"优良筛选个数：{mu}")
        self.output(f"迭代次数：{ngen}")
        self.output(f"交叉概率：{cxpb:.0%}")
        self.output(f"突变概率：{mutpb:.0%}")

        start = ttime()

        algorithms.eaMuPlusLambda(
            pop,
            toolbox,
            mu,
            lambda_,
            cxpb,
            mutpb,
            ngen,
            stats,
            halloffame=hof
        )

        end = ttime()
        cost = int((end - start))

        self.output(f"遗传算法优化完成，耗时{cost}秒")

        # Return result list
        results = []

        for parameter_values in hof:
            setting = dict(parameter_values)
            target_value = ga_optimize_pro(parameter_values)[0]
            results.append((setting, target_value, {}))

        return results

    def update_daily_close(self, symbol:str, price: float):
        """"""
        # 每天下午5点结算，晚上算另外一个交易日,周五算到下周一

        d = self.datetime.date()
        t = self.datetime.time()
        if t > time(hour=17, minute=0):
            if d.weekday() == 4:
                d = d + timedelta(days=3)
            else:
                d = d + timedelta(days=1)
        elif t < time(hour=8, minute=0):  # 周六凌晨算周一
            if d.weekday() == 5:
                d = d + timedelta(days=2)
        daily_results = self.daily_results_dict[symbol]
        contract = self.contract_dict.setdefault(symbol, ContractData(full_symbol=symbol))
        holding = self.holding_dict.setdefault(symbol,PositionHolding("PAPER", contract))
        daily_result = daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
            holding.last_price = price
        else:
            daily_results[d] = DailyResult(d, price)
            # 逐日盯市，改变持仓成本价格,需要用结算价（对商品期货是每日加权平均）
            # self.holding.long_price = self.holding.last_price
            # self.holding.short_price = self.holding.last_price
            holding.last_price = price

    def new_bar(self, bar: BarData):
        """"""
        self.bar = bar
        self.datetime = bar.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_bar(bar)

        self.update_daily_close(bar.full_symbol, bar.close_price)

    def new_tick(self, tick: TickData):
        """"""
        self.tick = tick
        self.datetime = tick.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_tick(tick)

        self.update_daily_close(tick.full_symbol, tick.last_price)

    def cross_limit_order(self):
        """
        Cross limit order with last bar/tick data.
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.low_price
            short_cross_price = self.bar.high_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
            symbol = self.bar.full_symbol
        else:
            long_cross_price = self.tick.ask_price_1
            short_cross_price = self.tick.bid_price_1
            long_best_price = long_cross_price
            short_best_price = short_cross_price
            symbol = self.tick.full_symbol

        rejectedoids = []
        active_limit_orders = self.active_limit_orders_dict[symbol]
        contract = self.contract_dict.setdefault(symbol, ContractData(full_symbol=symbol))
        holding = self.holding_dict.setdefault(symbol,PositionHolding("PAPER", contract))
        for order in list(active_limit_orders.values()):
            # Push order update with status "not traded" (pending).
            # if order.status == Status.SUBMITTING:
            #     order.status = Status.NOTTRADED
            #     self.strategy.on_order(order)

            # Check whether limit orders can be filled.
            long_cross = (
                order.direction == Direction.LONG
                and order.price >= long_cross_price
                and long_cross_price > 0
            )

            short_cross = (
                order.direction == Direction.SHORT
                and order.price <= short_cross_price
                and short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue

            if order.offset == Offset.CLOSE:
                noshortpos = (order.direction == Direction.LONG) and (
                    holding.short_pos < order.volume)
                nolongpos = (order.direction == Direction.SHORT) and (
                    holding.long_pos < order.volume)
                if nolongpos or noshortpos:
                    rejectedoids.append(order.client_order_id)
                    continue

            # Push order udpate with status "all traded" (filled).
            order.traded = order.volume
            order.status = Status.ALLTRADED
            self.strategy.on_order(order)

            active_limit_orders.pop(order.client_order_id, None)

            # Push trade update
            self.trade_count += 1

            if long_cross:
                trade_price = min(order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_best_price)
                pos_change = -order.volume

            turnover = trade_price * order.volume * contract.size
            commission = turnover * contract.rate
            slippage = order.volume * contract.size * contract.slippage

            trade = BacktestTradeData(
                full_symbol=order.full_symbol,  #symbol
                symbol=order.symbol,
                exchange=order.exchange,
                client_order_id=order.client_order_id,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                turnover=turnover,
                commission=commission,
                slippage=slippage,
                datetime=self.datetime,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            if trade.offset == Offset.CLOSE:  # 平仓不会影响持仓成本价格
                if trade.direction == Direction.LONG:
                    trade.short_pnl = trade.volume * \
                        (holding.short_price - trade.price) * contract.size
                else:
                    trade.long_pnl = trade.volume * \
                        (trade.price - holding.long_price) * contract.size
            holding.update_trade(trade)
            trade.long_pos = holding.long_pos
            trade.long_price = holding.long_price
            trade.short_pos = holding.short_pos
            trade.short_price = holding.short_price

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

            self.trades[trade.vt_tradeid] = trade

        for oid in rejectedoids:
            order = active_limit_orders.pop(oid)
            order.status = Status.REJECTED
            # Push update to strategy.
            self.strategy.on_order(order)

    def cross_stop_order(self):
        """
        Cross stop order with last bar/tick data.
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.high_price
            short_cross_price = self.bar.low_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
            symbol = self.bar.full_symbol
        else:
            long_cross_price = self.tick.last_price
            short_cross_price = self.tick.last_price
            long_best_price = long_cross_price
            short_best_price = short_cross_price
            symbol = self.tick.full_symbol

        rejectedoids = []
        active_stop_orders = self.active_stop_orders_dict[symbol]
        limit_orders = self.limit_orders_dict[symbol]
        contract = self.contract_dict.setdefault(symbol, ContractData(full_symbol=symbol))
        holding = self.holding_dict.setdefault(symbol,PositionHolding("PAPER", contract))
        for stop_order in list(active_stop_orders.values()):
            # Check whether stop order can be triggered.
            long_cross = (
                stop_order.direction == Direction.LONG
                and stop_order.price <= long_cross_price
            )

            short_cross = (
                stop_order.direction == Direction.SHORT
                and stop_order.price >= short_cross_price
            )

            if not long_cross and not short_cross:
                continue

            # close order must satisfy conditon that there are enough positions to close.
            if stop_order.offset == Offset.CLOSE:
                noshortpos = (stop_order.direction == Direction.LONG) and (
                    holding.short_pos < stop_order.volume)
                nolongpos = (stop_order.direction == Direction.SHORT) and (
                    holding.long_pos < stop_order.volume)
                if nolongpos or noshortpos:
                    rejectedoids.append(stop_order.client_order_id)
                    continue

            self.limit_order_count += 1
            stop_order.status = Status.ALLTRADED

            limit_orders[stop_order.client_order_id] = stop_order

            # Create trade data.
            if long_cross:
                trade_price = max(stop_order.price, long_best_price)
                pos_change = stop_order.volume
            else:
                trade_price = min(stop_order.price, short_best_price)
                pos_change = -stop_order.volume

            self.trade_count += 1

            turnover = trade_price * stop_order.volume * contract.size
            commission = turnover * contract.rate
            slippage = stop_order.volume * contract.size * contract.slippage

            trade = BacktestTradeData(
                full_symbol=stop_order.full_symbol,
                symbol=stop_order.symbol,
                exchange=stop_order.exchange,
                client_order_id=stop_order.client_order_id,
                tradeid=str(self.trade_count),
                direction=stop_order.direction,
                offset=stop_order.offset,
                price=trade_price,
                volume=stop_order.volume,
                turnover=turnover,
                commission=commission,
                slippage=slippage,
                datetime=self.datetime,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            if trade.offset == Offset.CLOSE:  # 平仓不会影响持仓成本价格
                if trade.direction == Direction.LONG:
                    trade.short_pnl = trade.volume * \
                        (holding.short_price - trade.price) * contract.size
                else:
                    trade.long_pnl = trade.volume * \
                        (trade.price - holding.long_price) * contract.size
            holding.update_trade(trade)
            trade.long_pos = holding.long_pos
            trade.long_price = holding.long_price
            trade.short_pos = holding.short_pos
            trade.short_price = holding.short_price

            self.trades[trade.vt_tradeid] = trade

            # Update stop order.

            active_stop_orders.pop(stop_order.client_order_id, None)

            # Push update to strategy.
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(stop_order)

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

        for oid in rejectedoids:
            stop_order = active_stop_orders.pop(oid)
            stop_order.status = Status.REJECTED
            self.limit_order_count += 1
            limit_orders[oid] = stop_order
            # Push update to strategy.
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(stop_order)

    def load_bar(
        self, 
        full_symbol: str, 
        days: int, 
        interval: Interval, 
        callback: Callable, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_bar_data'
    ):
        """
        called by strategy
        """
        # 以交易日为准，一星期内的时间补上周末二天，大于一周的时间暂不考虑补全额外的交易日
        tradedays = abs(days)
        weekday = self.start.weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        if self.datetime:
            end = self.datetime
        else:
            end = self.start
        start = end - timedelta(days=tradedays)
        if datasource == 'DataBase':
            self.history_bar = load_bar_data(
                full_symbol,
                interval,
                start,
                end,
                dbcollection,
                (';' in full_symbol)
            )
            self.history_bar_startix = 0
            self.history_bar_endix = len(self.history_bar)
        elif datasource == "Memory":
            startix = 0
            endix = 0
            fullsyminterval = full_symbol + '-' + interval.value
            totalbarlist = SQGlobal.history_bar[fullsyminterval]
            if not totalbarlist:
                self.output('load_bar数据为空，请先读入')
                return
            totalbars = len(totalbarlist)
            startix = totalbars - 1
            for i in range(totalbars):
                if totalbarlist[i].datetime < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalbars)):
                if totalbarlist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalbars)
            self.history_bar_startix = startix
            self.history_bar_endix = endix
            self.history_bar = totalbarlist

        self.historybar_callback = callback
        if self.historybar_callback:
            for data in self.history_bar[self.history_bar_startix:self.history_bar_endix]:
                self.historybar_callback(data)

    def load_tbtbar(
        self, 
        full_symbol: str, 
        days: int, 
        interval: Interval,
        callback: Callable, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_tbtbar_data'
    ):
        """
        called by strategy
        """
        # 以交易日为准，一星期内的时间补上周末二天，大于一周的时间暂不考虑补全额外的交易日
        tradedays = abs(days)
        weekday = self.start.weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        if self.datetime:
            end = self.datetime
        else:
            end = self.start
        start = end - timedelta(days=tradedays)

        if datasource == 'DataBase':
            self.history_bar = load_tbtbar_data(
                full_symbol,
                interval,
                start,
                end,
                dbcollection
            )
            self.history_bar_startix = 0
            self.history_bar_endix = len(self.history_bar)
        elif datasource == "Memory":
            startix = 0
            endix = 0
            fullsyminterval = full_symbol + '-' + interval.value
            totalbarlist = SQGlobal.history_tbtbar[fullsyminterval] 
            if not totalbarlist:
                self.output('load_tbtbar数据为空，请先读入')
                return
            totalbars = len(totalbarlist)
            startix = totalbars - 1
            for i in range(totalbars):
                if totalbarlist[i].datetime < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalbars)):
                if totalbarlist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalbars)
            self.history_bar_startix = startix
            self.history_bar_endix = endix
            self.history_bar = totalbarlist

        self.historybar_callback = callback
        if self.historybar_callback:
            for data in self.history_bar[self.history_bar_startix:self.history_bar_endix]:
                self.historybar_callback(data)

    def load_tick(self, 
        full_symbol: str, 
        days: int, 
        callback: Callable, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_tick_data'
        ):
        """
        called by strategy
        """
        tradedays = abs(days)
        weekday = self.start.weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        if self.datetime:
            end = self.datetime
        else:
            end = self.start
        start = end - timedelta(days=tradedays)

        if datasource == 'DataBase':
            self.history_tick = load_tick_data(
                full_symbol,
                start,
                end,
                dbcollection,
                (';' in full_symbol)
            )
            self.history_tick_startix = 0
            self.history_tick_endix = len(self.history_tick)

        elif datasource == 'Memory':
            startix = 0
            endix = 0
            totalticklist = SQGlobal.history_tick[full_symbol]
            if not totalticklist:
                self.output('load_tick数据为空，请先读入')
                return
            totalticks = len(totalticklist)
            startix = totalticks - 1
            for i in range(totalticks):
                if totalticklist[i].datetime < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalticks)):
                if totalticklist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalticks)
            self.history_tick_startix = startix
            self.history_tick_endix = endix
            self.history_tick = totalticklist

        self.historytick_callback = callback
        if self.historytick_callback:
            for data in self.history_tick[self.history_tick_startix:self.history_tick_endix]:
                self.historytick_callback(data)

    def send_order(
        self,
        strategy: CtaTemplate,
        req: OrderData,
        lock: bool = False,
        stop: bool = False
    ):
        """"""

        req.client_order_id = self.order_count
        req.time = self.datetime
        self.order_count += 1
        req.status = Status.NOTTRADED
        self.limit_order_count += 1
        self.strategy_orderid_map[strategy.strategy_name].add(
            req.client_order_id)
        self.orderid_symbol_map[req.client_order_id] = req.full_symbol
        self.active_limit_orders_dict[req.full_symbol][req.client_order_id] = req
        self.limit_orders_dict[req.full_symbol][req.client_order_id] = req

        return [req.client_order_id]

    def send_stop_order(
        self,
        strategy: CtaTemplate,
        req: OrderData,
        lock: bool = False
    ):
        """"""
        req.client_order_id = self.order_count
        req.time = self.datetime
        self.order_count += 1
        req.status = Status.NEWBORN
        self.stop_order_count += 1
        self.strategy_orderid_map[strategy.strategy_name].add(
            req.client_order_id)
        self.orderid_symbol_map[req.client_order_id] = req.full_symbol
        self.active_stop_orders_dict[req.full_symbol][req.client_order_id] = req
        self.stop_orders_dict[req.full_symbol][req.client_order_id] = req

        return [req.client_order_id]

    def cancel_order(self, strategy: CtaTemplate, orderid: int):
        """
        Cancel order by orderid.
        """
        symbol = self.orderid_symbol_map.get(orderid, None)
        if not symbol:
            return
        
        if orderid in self.active_limit_orders_dict[symbol]:
            order = self.active_limit_orders_dict[symbol].pop(orderid)
            order.status = Status.CANCELLED
            self.strategy.on_order(order)
        elif orderid in self.active_stop_orders_dict[symbol]:
            stop_order = self.active_stop_orders_dict[symbol].pop(orderid)
            stop_order.status = Status.CANCELLED
            self.strategy.on_stop_order(stop_order)

    def cancel_all(self, strategy: CtaTemplate, full_symbol: str = ''):
        """
        Cancel all orders, both limit and stop.
        """
        if full_symbol: # specific full_symbol
            lorderdict = self.active_limit_orders_dict[full_symbol]
            for orderid in list(lorderdict.keys()):
                order = lorderdict.pop(orderid)
                order.status = Status.CANCELLED
                self.strategy.on_order(order)
            
            storderdict =  self.active_stop_orders_dict[full_symbol]
            for orderid in list(storderdict.keys()):
                stop_order = storderdict.pop(orderid)
                stop_order.status = Status.CANCELLED
                self.strategy.on_stop_order(stop_order)                      
        
        else:  # all
            for orderdicts in self.active_limit_orders_dict.values():
                for orderid in list(orderdicts.keys()):
                    order = orderdicts.pop(orderid)
                    order.status = Status.CANCELLED
                    self.strategy.on_order(order)

            for orderdicts in self.active_stop_orders_dict.values():
                for orderid in list(orderdicts.keys()):
                    stop_order = orderdicts.pop(orderid)
                    stop_order.status = Status.CANCELLED
                    self.strategy.on_stop_order(stop_order)

    def write_log(self, msg: str, strategy: CtaTemplate = None):
        """
        Write log message.
        """
        msg = f"{self.datetime}\t{msg}"
        self.logs.append(msg)

    def send_email(self, msg: str, strategy: CtaTemplate = None):
        """
        Send email to default receiver.
        """
        pass

    def get_engine_type(self):
        """
        Return engine type.
        """
        return self.engine_type

    def put_strategy_event(self, strategy: CtaTemplate):
        """
        Put an event to update strategy status.
        """
        pass

    def output(self, msg):
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")

    def sync_strategy_data(self, strategy: CtaTemplate):
        pass

    def get_position_holding(self, acc: str, full_symbol: str):
        contract = self.contract_dict.setdefault(full_symbol, ContractData(full_symbol=full_symbol))
        holding = self.holding_dict.setdefault(full_symbol,PositionHolding("PAPER", contract))
        return holding

    def get_account(self, accountid):
        pass

    def get_order(self, orderid: int):
        symbol = self.orderid_symbol_map.get(orderid, None)
        if not symbol:
            return None
        if orderid in self.limit_orders_dict[symbol]:
            order = self.limit_orders_dict[symbol].get(orderid)
            return order
        if orderid in self.stop_orders_dict[symbol]:
            order = self.stop_orders_dict[symbol].get(orderid)
            return order

    def get_tick(self, full_symbol: str):
        pass

    def get_trade(self, vt_tradeid):
        return self.trades.get(vt_tradeid, None)

    def get_all_trades(self):
        return list(self.trades.values())

    def get_position(self, key):
        pass

    def get_contract(self, full_symbol):
        return self.contract_dict.setdefault(full_symbol, ContractData(full_symbol=full_symbol))


    def get_all_active_orders(self, full_symbol: str = ""):
        active_orders = []
        if full_symbol: # specific symbol
            lorders = self.active_limit_orders_dict[full_symbol]
            active_orders.extend(lorders.values())
            storders = self.active_stop_orders_dict[full_symbol]          
            active_orders.extend(storders.values())          
        else:  # all active orders
            for orders in self.active_limit_orders_dict.values():
                active_orders.extend(orders.values())
            for orders in self.active_stop_orders_dict.values():            
                active_orders.extend(orders.values())
        return active_orders


    def get_strategy_active_orderids(self, strategy_name: str):
        orderids = []
        for orders in self.active_limit_orders_dict.values():
            orderids.extend(orders.keys())
        active_orderids = set(orderids)
        return active_orderids

        # TODO: consider stoporder 
    def get_all_orders(self):
        """
        Return all limit order data of current backtesting result.
        """
        allorders = []
        for orders in self.limit_orders_dict.values():
            allorders.extend(orders.values())
        return allorders

    def get_all_daily_results(self):
        """
        Return all daily result data.
        """
        return list(self.total_daily_results.values())

    def get_daily_results(self, symbol: str):
        dailyresult = self.daily_results_dict.get(symbol, None)
        if dailyresult:
            return list(dailyresult.values())
        else:
            return []

class BacktestingEngine:
    """"""

    engine_type = EngineType.BACKTESTING
    gateway_name = "BACKTESTING"

    def __init__(self):
        """"""
        self.id = 0
        self.full_symbol = ""
        self.symbol = ""
        self.exchange = None
        self.start = None
        self.end = None
        self.rate = 0
        self.slippage = 0
        self.size = 1
        self.pricetick = 0
        self.capital = 1_000_000
        self.mode = BacktestingMode.BAR
        self.tbtmode = False

        self.contract = None
        self.holding = None
        self.strategy_class = None
        self.strategy = None
        self.tick: TickData = None
        self.bar: BarData = None
        self.datetime = None

        self.datasource = 'DataBase'
        self.using_cursor = True
        self.dbcollection = ''
        self.dbtype=  None
        self.interval = None


        self.days = 0
        self.callback = None
        self.historybar_callback = None  # used in tick mode called by strategy load_bar
        self.historytick_callback = None  # used in tick mode called by strategy load_tick
        self.history_data = []
        self.history_data_startix = 0
        self.history_data_endix = 1
        self.history_bar = []  # used in tick mode called by strategy load_bar
        self.history_bar_startix = 0
        self.history_bar_endix = 0
        self.history_tick = []  # used in tick mode called by strategy load_tick
        self.history_tick_startix = 0
        self.history_tick_endix = 0
        self.order_count = 0

        self.stop_order_count = 0
        self.stop_orders = {}
        self.active_stop_orders = {}

        self.limit_order_count = 0
        self.limit_orders = {}
        self.active_limit_orders = {}
        self.strategy_orderid_map = defaultdict(set)

        self.trade_count = 0
        self.trades = {}

        self.logs = []

        self.daily_results = {}  # for lite mode
        self.daily_results_dict = defaultdict(dict)  # symbol -> dailyresult dict , for batch mode
        self.total_daily_results = {}  #for batch mode

        self.daily_df = None
        self.total_daily_df = None

    def clear_data(self):
        """
        Clear all data of last backtesting.
        """
        self.strategy = None
        self.tick = None
        self.bar = None
        self.datetime = None
        self.holding = None
        self.contract = None
        self.tbtmode = False

        self.stop_order_count = 0
        self.stop_orders.clear()
        self.active_stop_orders.clear()

        self.limit_order_count = 0
        self.limit_orders.clear()
        self.active_limit_orders.clear()
        self.strategy_orderid_map.clear()

        self.trade_count = 0
        self.trades.clear()

        self.logs.clear()
        self.daily_results.clear()

        self.daily_df = None
    
    def clear_total_data(self):
        self.total_daily_results.clear()
        self.daily_results_dict.clear()
        self.total_daily_df = None

    def load_list_trades(self,trades):
        for trade in trades:
            self.trades[self.trade_count] = trade
            self.trade_count += 1        

    def set_parameters(
        self,
        datasource='DataBase',
        using_cursor: bool =True,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',
        interval: str ='1m',        
        full_symbol: str = 'SHFE F RB 88',
        start: datetime = datetime(2019, 1,1),
        rate: float = 0.1,
        slippage: float = 0.1,
        size: float = 1.0,
        pricetick: float = 1.0,
        capital: int = 0,
        end: datetime = None,
        mode: BacktestingMode = BacktestingMode.BAR,
    ):
        """"""       
        self.mode = mode
        self.full_symbol = full_symbol
        self.datasource = datasource
        self.using_cursor = using_cursor
        self.dbcollection = dbcollection
        self.dbtype = dbtype


        if dbtype.endswith('Bar'):
            self.mode = BacktestingMode.BAR
            self.interval = Interval(interval)
        else:
            self.mode = BacktestingMode.TICK
            self.interval = Interval.MINUTE

        # if interval == 'tick':
        #     self.interval = Interval.MINUTE
        #     self.mode = BacktestingMode.TICK
        # elif interval == 'tbtbar':
        #     self.interval = Interval.MINUTE
        #     self.mode = BacktestingMode.BAR
        #     self.tbtmode = True
        # else:
        #     self.interval = Interval(interval)
        #     self.tbtmode = False
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.pricetick = pricetick
        if type(start) == date:
            self.start = datetime(start.year,start.month,start.day)
        else:
            self.start = start

        self.symbol, self.exchange = extract_full_symbol(self.full_symbol)

        if capital:
            self.capital = capital

        if end:
            if type(end) == date:
                self.end = datetime(end.year,end.month,end.day)
            else:
                self.end = end
        else:
            self.end = datetime.now()

        contract = ContractData(
            full_symbol=self.full_symbol,
            size=self.size,
            exchange=self.exchange,
            pricetick=self.pricetick
        )
        self.contract = contract
        self.holding = PositionHolding("PAPER", contract)

    def add_strategy(self, strategy_class: type, setting: dict):
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(
            self, strategy_class.__name__, self.full_symbol, setting
        )
        # redirect strategy write_log output
        self.strategy.write_log = self.output

    def load_data(self):
        """"""
        self.output("开始加载历史数据")

        if self.mode == BacktestingMode.BAR:
            if self.datasource == "DataBase":
                if self.dbtype == 'TbtBar':
                    if self.using_cursor:
                        load_tbtbar_data.cache_clear()
                    self.history_data = load_tbtbar_data(
                        self.full_symbol,
                        self.interval,
                        self.start,
                        self.end,
                        self.dbcollection,
                        self.using_cursor
                    )
                elif self.dbtype == 'Bar':
                    if self.using_cursor:
                        load_bar_data.cache_clear()
                    self.history_data = load_bar_data(
                        self.full_symbol,
                        self.interval,
                        self.start,
                        self.end, 
                        self.dbcollection,
                        True,
                        self.using_cursor
                    )
                if type(self.history_data) == list: 
                    self.history_data_startix = 0
                    self.history_data_endix = len(self.history_data)
            elif self.datasource == "Memory":
                # add interval to full symbol
                fullsyminterval = self.full_symbol + '-' + self.interval.value
                if self.dbtype == 'TbtBar':
                    totalbarlist = SQGlobal.history_tbtbar[fullsyminterval]
                elif self.dbtype == 'Bar':
                    totalbarlist = SQGlobal.history_bar[fullsyminterval]
                if not totalbarlist:
                    self.output('数据为空，请先读入')
                    return
                totalbars = len(totalbarlist)
                startix = totalbars - 1
                endix = 0
                for i in range(totalbars):
                    if totalbarlist[i].datetime < self.start:
                        continue
                    startix = i
                    break
                for i in reversed(range(totalbars)):
                    if totalbarlist[i].datetime > self.end:
                        continue
                    endix = i
                    break
                endix = min(endix + 1, totalbars)
                if endix < startix:
                    endix = startix
                self.history_data_startix = startix
                self.history_data_endix = endix
                self.history_data = totalbarlist
        else:
            if self.datasource == "DataBase":
                if self.using_cursor:
                    load_tick_data.cache_clear()
                self.history_data = load_tick_data(
                    self.full_symbol,
                    self.start,
                    self.end, 
                    self.dbcollection,
                    True,
                    self.using_cursor
                )
                if type(self.history_data) == list: 
                    self.history_data_startix = 0
                    self.history_data_endix = len(self.history_data)
            elif self.datasource == "Memory":
                totalticklist = SQGlobal.history_tick[self.full_symbol]
                if not totalticklist:
                    self.output('数据为空，请先读入')
                    return
                totalticks = len(totalticklist)
                startix = totalticks - 1
                endix = 0
                for i in range(totalticks):
                    if totalticklist[i].datetime < self.start:
                        continue
                    startix = i
                    break
                for i in reversed(range(totalticks)):
                    if totalticklist[i].datetime > self.end:
                        continue
                    endix = i
                    break
                endix = min(endix + 1, totalticks)
                if endix < startix:
                    endix = startix
                self.history_data = totalticklist
                self.history_data_startix = startix
                self.history_data_endix = endix

        if type(self.history_data) == list: 
            self.output(
                f"历史数据加载完成，数据量：{self.history_data_endix - self.history_data_startix - 1}")
        else:
            self.output("得到历史数据游标")


    def set_data(self, data):
        self.history_data = data
        self.history_data_startix = 0
        self.history_data_endix = len(self.history_data)


    def run_backtesting(self):
        """"""
        if not self.history_data or self.history_data_startix == self.history_data_endix:
            self.output('回测数据为空，直接结束回测')
            return True

        if self.mode == BacktestingMode.BAR:
            func = self.new_bar
        else:
            func = self.new_tick
        try:
            self.strategy.on_init()
            self.strategy.inited = True
            self.output("策略初始化完成")

            self.strategy.on_start()
            self.strategy.trading = True
            self.output("开始回放历史数据")

            totalcount = 0
            if type(self.history_data) == list:
                for data in self.history_data[self.history_data_startix:self.history_data_endix]:
                    func(data)
                    totalcount += 1
            else:
                if self.mode == BacktestingMode.BAR:
                    if self.dbtype == 'TbtBar':  
                        for data in self.history_data:
                            btdata = TBTBarData(
                                full_symbol=data["full_symbol"],
                                datetime=data["datetime"],
                                interval=self.interval,
                                volume=data["volume"],
                                open_price=data["open_price"],
                                high_price=data["high_price"],
                                low_price=data["low_price"],
                                close_price=data["close_price"],
                                ask_totalqty=data["ask_totalqty"],
                                bid_totalqty=data["bid_totalqty"],
                                ask_totalmoney=data["ask_totalmoney"],
                                bid_totalmoney=data["bid_totalmoney"],
                                ask_bigmoney=data["ask_bigmoney"],
                                bid_bigmoney=data["bid_bigmoney"],
                                ask_bigleft=data["ask_bigleft"],
                                bid_bigleft=data["bid_bigleft"],
                                user_defined_1=data['user_defined_1'] if "user_defined_1" in data else 0.0
                                )
                            func(btdata)
                            totalcount += 1
                    elif self.dbtype == 'Bar':
                        for data in self.history_data:
                            btdata = BarData(
                                symbol=data["symbol"],
                                full_symbol=data["full_symbol"],
                                datetime=data["datetime"],
                                exchange=Exchange(data["exchange"]),
                                interval=self.interval,
                                volume=data["volume"],
                                open_interest=data["open_interest"],
                                open_price=data["open_price"],
                                high_price=data["high_price"],
                                low_price=data["low_price"],
                                close_price=data["close_price"]
                                )
                            func(btdata)
                            totalcount += 1
                else:
                    if self.dbtype == 'Tick':
                        for data in self.history_data:
                            btdata = TickData(
                                full_symbol=data["full_symbol"],
                                symbol=data["symbol"],
                                datetime=data["datetime"],
                                exchange=Exchange(data["exchange"]),
                                ask_price_1=data["ask_price_1"],
                                ask_volume_1=data["ask_volume_1"],
                                bid_price_1=data["bid_price_1"],
                                bid_volume_1=data["bid_volume_1"],
                                last_price=data["last_price"],
                                volume=data["volume"],
                                open_interest=data["open_interest"],
                                limit_up=data["limit_up"],
                                limit_down=data["limit_down"],
                                open_price=data["open_price"],
                                pre_close=data["pre_close"],
                                high_price=data["high_price"],
                                low_price=data["low_price"]
                                )
                            func(btdata)
                            totalcount += 1

            self.strategy.on_finish()


        except:            
            msg = f"回测异常:\n{traceback.format_exc()}"
            self.output(msg) 
            return False   
        self.output(f"总共{totalcount}个历史数据回放结束")
        return True


    def calculate_result(self):
        """"""
        self.output("开始计算逐日盯市盈亏")

        if not self.trades:
            self.output("成交记录为空，无法计算")
            self.daily_df = None
            return None

        # Add trade data into daily reuslt.
        for trade in self.trades.values():
            d = trade.datetime.date()
            t = trade.datetime.time()
            if t > time(hour=17, minute=0):
                if d.weekday() == 4:
                    d = d + timedelta(days=3)
                else:
                    d = d + timedelta(days=1)
            elif t < time(hour=8, minute=0):  # 周六凌晨算周一
                if d.weekday() == 5:
                    d = d + timedelta(days=2)
            daily_result = self.daily_results[d]
            daily_result.add_trade(trade)



        # Calculate daily result by iteration.
        pre_close = 0
        start_pos = 0
        pre_margin = 0

        for daily_result in self.daily_results.values():
            daily_result.calculate_pnl(
                pre_close, start_pos, self.size, self.rate, self.slippage
            )

            pre_close = daily_result.close_price
            start_pos = daily_result.end_pos

            daily_result.calculate_margin(pre_margin)
            pre_margin = daily_result.margin

        # Generate dataframe
        results = defaultdict(list)

        for daily_result in self.daily_results.values():
            for key, value in daily_result.__dict__.items():
                results[key].append(value)

        self.daily_df = DataFrame.from_dict(results).set_index("date")

        self.output("逐日盯市盈亏计算完成")
        return self.daily_df

    def calculate_total_result(self):
        self.output("逐个标的逐日盯市盈亏统计")

        # Add trade data into daily reuslt.
        trades_daily_results = {}
        for trade in sorted(self.trades.values(), key=lambda x:x.datetime):
            d = trade.datetime.date()
            t = trade.datetime.time()
            if t > time(hour=17, minute=0):
                if d.weekday() == 4:
                    d = d + timedelta(days=3)
                else:
                    d = d + timedelta(days=1)
            elif t < time(hour=8, minute=0):  # 周六凌晨算周一
                if d.weekday() == 5:
                    d = d + timedelta(days=2)
            trades_daily_result = trades_daily_results.setdefault(d, DailyResult(d,0))
            trades_daily_result.add_trade(trade)

        # Calculate margin used daily result by iteration .
        pre_margin = 0
        for _t, daily_result in sorted(trades_daily_results.items()):
            daily_result.calculate_margin(pre_margin)
            pre_margin = daily_result.margin



        for daily_results in self.daily_results_dict.values():
            for datekey, dailyresult in daily_results.items():
                total_daily_result = self.total_daily_results.setdefault(datekey, DailyResult(datekey,0))
                total_daily_result.trade_count += dailyresult.trade_count
                total_daily_result.start_pos += dailyresult.start_pos
                total_daily_result.end_pos += dailyresult.end_pos
                total_daily_result.turnover += dailyresult.turnover
                total_daily_result.commission += dailyresult.commission
                total_daily_result.slippage += dailyresult.slippage
                total_daily_result.trading_pnl += dailyresult.trading_pnl
                total_daily_result.holding_pnl += dailyresult.holding_pnl
                total_daily_result.total_pnl += dailyresult.total_pnl
                total_daily_result.net_pnl += dailyresult.net_pnl

                trade_daily_result = trades_daily_results.get(datekey, DailyResult(datekey,0))
                total_daily_result.maxmargin = trade_daily_result.maxmargin

        results = defaultdict(list)

        #按照key（时间）排序
        for _t, daily_result in sorted(self.total_daily_results.items()):
            for key, value in daily_result.__dict__.items():
                results[key].append(value)
        if results:
            self.total_daily_df = DataFrame.from_dict(results).set_index("date")

            self.output("逐个标的盈亏加和统计完成")
            return self.total_daily_df
        else:
            self.output("记录为空,无法计算")
            return

    def calculate_statistics(self, df: DataFrame = None, output=True, trades: list = None):
        """"""
        self.output("开始计算策略统计指标")

        if (df is None) or (df.empty):
            df = self.daily_df

        if df is None:
            # Set all statistics to 0 if no trade.
            start_date = ""
            end_date = ""
            total_days = 0
            profit_days = 0
            loss_days = 0
            end_balance = 0
            max_drawdown = 0
            max_ddpercent = 0
            recent_drawdown = 0
            recent_ddpercent = 0
            max_drawdown_duration = 0
            total_net_pnl = 0
            daily_net_pnl = 0
            total_commission = 0
            daily_commission = 0
            total_slippage = 0
            daily_slippage = 0
            total_turnover = 0
            daily_turnover = 0
            total_trade_count = 0
            daily_trade_count = 0
            total_return = 0
            annual_return = 0
            daily_return = 0
            return_turnover = 0
            return_std = 0
            sharpe_ratio = 0
            return_drawdown_ratio = 0
            winratio = 0
            winloss = 0
            profit_per_trade = 0
            long_count = 0
            short_count = 0
            long_profit = 0
            short_profit = 0
            long_profit_per_trade = 0
            short_profit_per_trade = 0
            longwinratio = 0
            longwinloss = 0
            shortwinratio = 0
            shortwinloss = 0
            maxmargin = 0
        else:
            # Calculate balance related time series data
            maxmargin = df['maxmargin'].max()
            df["balance"] = df["net_pnl"].cumsum() + self.capital
            minbalance = df["balance"].min()
            
            df["return"] = np.log(
                df["balance"] / df["balance"].shift(1)).fillna(0)
            df["highlevel"] = (
                df["balance"].rolling(
                    min_periods=1, window=len(df), center=False).max()
            )
            df["drawdown"] = df["balance"] - df["highlevel"]
            df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

            # Calculate statistics value
            start_date = df.index[0]
            end_date = df.index[-1]

            total_days = len(df)
            # 先按自然日2/3折算
            total_days_2 = int ( (end_date - start_date) / timedelta(days=1) * 2 / 3 )
            total_days = max(total_days, total_days_2)

            profit_days = len(df[df["net_pnl"] > 0])
            loss_days = len(df[df["net_pnl"] < 0])

            end_balance = df["balance"].iloc[-1]
            max_drawdown = df["drawdown"].min()
            max_ddpercent = df["ddpercent"].min()
            recent_drawdown = df["drawdown"].iloc[-1]
            recent_ddpercent = df["ddpercent"].iloc[-1]

            # this method is the time to md
            # max_drawdown_end = df["drawdown"].idxmin()
            # max_drawdown_start = df["balance"][:max_drawdown_end].argmax()
            # max_drawdown_duration = (max_drawdown_end - max_drawdown_start).days

            # method to calculate mdd
            nodrawdown = np.where(df["drawdown"] ==0)[0]
            lastdd =    len(df) - np.where(df["drawdown"] ==0)[0][-1]         
            nodrawdown = np.diff(nodrawdown)
            max_drawdown_duration = max(np.max(nodrawdown),lastdd)
            # print('mdd',max_drawdown_duration)

            total_net_pnl = df["net_pnl"].sum()
            daily_net_pnl = total_net_pnl / total_days

            total_commission = df["commission"].sum()
            daily_commission = total_commission / total_days

            total_slippage = df["slippage"].sum()
            daily_slippage = total_slippage / total_days

            total_turnover = df["turnover"].sum()
            daily_turnover = total_turnover / total_days

            total_trade_count = df["trade_count"].sum()
            daily_trade_count = total_trade_count / total_days

            total_return = (end_balance / self.capital - 1) * 100
            annual_return = total_return / total_days * 240
       
            if minbalance > 0:
                daily_return = df["return"].mean() * 100
            else:
                daily_return = 0.0

            if minbalance > 0:
                return_std = df["return"].std() * 100
            else:
                return_std = 0.0
            
            profit_per_trade = total_net_pnl / total_trade_count if total_trade_count else 0

            if return_std and minbalance > 0:
                sharpe_ratio = daily_return / return_std * np.sqrt(240)
            else:
                sharpe_ratio = 0
            if max_ddpercent:
                return_drawdown_ratio = -total_return / max_ddpercent
            else:
                return_drawdown_ratio = 0


            if total_turnover:
                return_turnover = total_net_pnl*10000 / total_turnover
            else:
                return_turnover = 0.0




            wincount = 0
            winmoney = 0
            losscount = 0
            lossmoney = 0
            longwincount = 0
            longwinmoney = 0
            longlosscount = 0
            longlossmoney = 0
            shortwincount = 0
            shortwinmoney = 0
            shortlosscount = 0
            shortlossmoney = 0

            long_count = 0
            short_count = 0
            long_profit = 0
            short_profit = 0
            long_profit_per_trade = 0
            short_profit_per_trade = 0


            if not trades:
                trades = self.trades.values()
            for trade in trades:
                netpnl = trade.long_pnl + trade.short_pnl - trade.slippage - trade.commission
                if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                    long_count += 1
                    long_profit += netpnl
                elif trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                    short_count += 1                    
                    short_profit += netpnl
                    if (netpnl) > 0:
                        wincount += 1
                        winmoney += netpnl
                        shortwincount += 1
                        shortwinmoney += netpnl
                    elif (netpnl) < 0:
                        losscount += 1
                        lossmoney += abs(netpnl)
                        shortlosscount += 1
                        shortlossmoney += abs(netpnl)
                elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                    short_count += 1
                    short_profit += netpnl
                elif trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                    long_count += 1
                    long_profit += netpnl
                    if (netpnl) > 0:
                        wincount += 1
                        winmoney += netpnl
                        longwincount += 1
                        longwinmoney += netpnl
                    elif (netpnl) < 0:
                        losscount += 1
                        lossmoney += abs(netpnl)
                        longlosscount += 1
                        longlossmoney += abs(netpnl)

            if long_count:
                long_profit_per_trade = long_profit / long_count
            else:
                long_profit_per_trade = 0
            if short_count:
                short_profit_per_trade = short_profit / short_count
            else:
                short_profit_per_trade = 0

            if (wincount + losscount):
                winratio = wincount / (wincount + losscount)
            else:
                winratio = 0.0
            if wincount and losscount and lossmoney:
                winloss = (winmoney / wincount) / (lossmoney / losscount)
            else:
                winloss = 0.0

            if (longwincount + longlosscount):
                longwinratio = longwincount / (longwincount + longlosscount)
            else:
                longwinratio = 0.0
            if longwincount and longlosscount and longlossmoney:
                longwinloss = (longwinmoney / longwincount) / (longlossmoney / longlosscount)
            else:
                longwinloss = 0.0

            if (shortwincount + shortlosscount):
                shortwinratio = shortwincount / (shortwincount + shortlosscount)
            else:
                shortwinratio = 0.0
            if shortwincount and shortlosscount and shortlossmoney:
                shortwinloss = (shortwinmoney / shortwincount) / (shortlossmoney / shortlosscount)
            else:
                shortwinloss = 0.0

        # Output
        if output:
            self.output("-" * 30)
            self.output(f"首个交易日：\t{start_date}")
            self.output(f"最后交易日：\t{end_date}")

            self.output(f"总交易日：\t{total_days}")
            self.output(f"盈利交易日：\t{profit_days}")
            self.output(f"亏损交易日：\t{loss_days}")

            self.output(f"起始资金：\t{self.capital:,.2f}")
            self.output(f"结束资金：\t{end_balance:,.2f}")

            self.output(f"总收益率：\t{total_return:,.2f}%")
            self.output(f"年化收益：\t{annual_return:,.2f}%")
            self.output(f"最大回撤: \t{max_drawdown:,.2f}")
            self.output(f"百分比最大回撤: {max_ddpercent:,.2f}%")

            self.output(f"总盈亏：\t{total_net_pnl:,.2f}")
            self.output(f"总手续费：\t{total_commission:,.2f}")
            self.output(f"总滑点：\t{total_slippage:,.2f}")
            self.output(f"总成交金额：\t{total_turnover:,.2f}")
            self.output(f"总成交笔数：\t{total_trade_count}")

            self.output(f"日均盈亏：\t{daily_net_pnl:,.2f}")
            self.output(f"日均手续费：\t{daily_commission:,.2f}")
            self.output(f"日均滑点：\t{daily_slippage:,.2f}")
            self.output(f"日均成交金额：\t{daily_turnover:,.2f}")
            self.output(f"日均成交笔数：\t{daily_trade_count}")

            self.output(f"日均收益率：\t{daily_return:,.2f}%")
            self.output(f"收益标准差：\t{return_std:,.2f}%")
            self.output(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
            self.output(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

        statistics = {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "profit_days": profit_days,
            "loss_days": loss_days,
            "capital": self.capital,
            "end_balance": end_balance,
            "max_drawdown": max_drawdown,
            "max_ddpercent": max_ddpercent,
            "recent_drawdown": recent_drawdown,
            "recent_ddpercent": recent_ddpercent,
            "max_drawdown_duration": max_drawdown_duration,
            "total_net_pnl": total_net_pnl,
            "daily_net_pnl": daily_net_pnl,
            "total_commission": total_commission,
            "daily_commission": daily_commission,
            "total_slippage": total_slippage,
            "daily_slippage": daily_slippage,
            "total_turnover": total_turnover,
            "daily_turnover": daily_turnover,
            "total_trade_count": total_trade_count,
            "daily_trade_count": daily_trade_count,
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_return": daily_return,
            "return_turnover":return_turnover,
            "return_std": return_std,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
            "win_ratio": winratio,
            "win_loss": winloss,
            "long_win_ratio": longwinratio,
            "short_win_ratio": shortwinratio,
            "long_win_loss": longwinloss,
            "short_win_loss": shortwinloss,
            "profit_per_trade":profit_per_trade,
            "long_profit": long_profit,
            "short_profit": short_profit,
            "long_count":long_count,
            "short_count":short_count,
            "long_profit_per_trade":long_profit_per_trade,
            "short_profit_per_trade":short_profit_per_trade,
            "maxmargin":maxmargin,

        }

        return statistics

    def show_chart(self, df: DataFrame = None):
        """"""
        if not df:
            df = self.daily_df

        if df is None:
            return

        plt.figure(figsize=(10, 16))

        balance_plot = plt.subplot(4, 1, 1)
        balance_plot.set_title("Balance")
        df["balance"].plot(legend=True)

        drawdown_plot = plt.subplot(4, 1, 2)
        drawdown_plot.set_title("Drawdown")
        drawdown_plot.fill_between(range(len(df)), df["drawdown"].values)

        pnl_plot = plt.subplot(4, 1, 3)
        pnl_plot.set_title("Daily Pnl")
        df["net_pnl"].plot(kind="bar", legend=False, grid=False, xticks=[])

        distribution_plot = plt.subplot(4, 1, 4)
        distribution_plot.set_title("Daily Pnl Distribution")
        df["net_pnl"].hist(bins=50)

        plt.show()

    def run_optimization(self, 
        optimization_setting: OptimizationSetting, 
        output=True, 
        ):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        target_name = optimization_setting.target_name
        num_cpus = optimization_setting.num_cpus

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        pool = multiprocessing.Pool(num_cpus)

        # should use original interval info, since opt will use new engine to run backtesting
        # if self.tbtmode:
        #     interval = 'tbtbar'
        # elif self.mode == BacktestingMode.TICK:
        #     interval = 'tick'
        # else:
        #     interval = self.interval


        results = []
        for setting in settings:
            if not self.strategy.parameter_filter(setting):
                continue
            result = (pool.apply_async(optimize, (
            # result = optimize_remote.remote (
                target_name,
                self.strategy_class,
                setting,
                self.full_symbol,
                self.start,
                self.rate,
                self.slippage,
                self.size,
                self.pricetick,
                self.capital,
                self.end,
                self.mode,
                self.datasource,
                self.using_cursor,
                self.dbcollection,
                self.dbtype,
                self.interval.value
            )))
            # )         
            results.append(result)

        pool.close()
        pool.join()

        result_values = [result.get() for result in results]
        # result_values = [ray.get(result) for result in results]

        # Sort results and output
        result_values.sort(reverse=True, key=lambda result: result[1])

        if output:
            for value in result_values:
                msg = f"参数：{value[0]}, 目标：{value[1]}"
                self.output(msg)

        return result_values


    def run_roll_optimization(self, 
        optimization_setting: OptimizationSetting, 
        ):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting()
        num_cpus = optimization_setting.num_cpus
        rollperiod = optimization_setting.roll_period
        if not settings:
            self.output("滚动优化参数组合为空，请检查")
            return

        # Use multiprocessing pool for running backtesting with different setting
        pool = multiprocessing.Pool(num_cpus)


        # should use original interval info, since opt will use new engine to run backtesting
        # if self.tbtmode:
        #     interval = 'tbtbar'
        # elif self.mode == BacktestingMode.TICK:
        #     interval = 'tick'
        # else:
        #     interval = self.interval



        results = []
        for setting in settings:
            if not self.strategy.parameter_filter(setting):
                continue
            result = (pool.apply_async(roll_optimize, (
                self.strategy_class,
                setting,
                self.full_symbol,
                self.start,
                self.rate,
                self.slippage,
                self.size,
                self.pricetick,
                self.capital,
                self.end,
                self.mode,
                self.datasource,
                self.using_cursor,
                self.dbcollection,
                self.dbtype,
                self.interval.value
            )))         
            results.append(result)
        pool.close()
        pool.join()



        # Sort results and output
        result_values = [result.get() for result in results]
        roll_df = pd.Series()
        rollstartdate = self.start.date()
        rollenddate = self.end.date()
        rolldate = rollstartdate + timedelta(days=90)
        rollsettinglist = []
        rolldatelist = []
        while rolldate < rollenddate:
            tmpsetting, tmpdf = self.strategy.roll_choose(result_values,self.start.date(),rolldate)
            rollsettinglist.append(tmpsetting)
            rolldatelist.append(rollstartdate)
            nextrolldate = rolldate + timedelta(days=rollperiod)
            roll_df = roll_df.append(tmpdf[rollstartdate:nextrolldate])            
            rolldate = nextrolldate
            rollstartdate = rolldate + timedelta(days=1)



        return (rolldatelist,rollsettinglist, roll_df)









    def run_mp_backtest(
        self,
        cpunums,
        strategy_classes,
        settinglist: dict,
        capital: int,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',        
        ):

        pool = multiprocessing.Pool(cpunums)
        results = []

        class_namelist = settinglist['strategy']
        stragegysettinglist = settinglist['parameter']
        fsmlist = settinglist['full_symbol']
        startlist = settinglist['start']
        endlist = settinglist['end']
        ratelist = settinglist['rate']
        slippagelist = settinglist['slippage']
        sizelist = settinglist['size']
        priceticklist = settinglist['pricetick']
        intervallist = settinglist['interval']

        for i in range(len(fsmlist)):
            class_name = class_namelist[i]
            setting = eval(stragegysettinglist[i])
            strategy_class = strategy_classes[class_name]
            full_symbol = fsmlist[i]
            start = startlist[i]
            end = endlist[i]
            rate = float(ratelist[i])
            slippage = float(slippagelist[i])
            size = float(sizelist[i])
            pricetick = float(priceticklist[i])
            dbinterval = intervallist[i]

            result = (pool.apply_async(mp_backtest, (
                strategy_class,
                setting,
                full_symbol,
                start,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                end,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                dbinterval,
            )))
         
            results.append(result)

        pool.close()
        pool.join()

        result_values = [result.get() for result in results]
        return result_values



    def run_ga_optimization(self, 
        optimization_setting: OptimizationSetting, 
        population_size=100, 
        ngen_size=30, 
        output=True, 
    ):
        """"""
        # Get optimization setting and target
        settings = optimization_setting.generate_setting_ga()
        target_name = optimization_setting.target_name

        if not settings:
            self.output("优化参数组合为空，请检查")
            return

        if not target_name:
            self.output("优化目标未设置，请检查")
            return

        # Define parameter generation function
        def generate_parameter():
            """"""
            return random.choice(settings)

        def mutate_individual(individual, indpb):
            """"""
            size = len(individual)
            paramlist = generate_parameter()
            for i in range(size):
                if random.random() < indpb:
                    individual[i] = paramlist[i]
            return individual,

        # Create ga object function
        global ga_target_name
        global ga_strategy_class
        global ga_setting
        global ga_full_symbol
        global ga_start
        global ga_rate
        global ga_slippage
        global ga_size
        global ga_pricetick
        global ga_capital
        global ga_end
        global ga_mode
        global ga_datasource
        global ga_using_cursor
        global ga_dbcollection
        global ga_dbtype
        global ga_interval

        ga_target_name = target_name
        ga_strategy_class = self.strategy_class
        ga_setting = settings[0]
        ga_full_symbol = self.full_symbol

        # if self.tbtmode:
        #     interval = 'tbtbar'
        # elif self.mode == BacktestingMode.TICK:
        #     interval = 'tick'
        # else:
        #     interval = self.interval


        ga_start = self.start
        ga_rate = self.rate
        ga_slippage = self.slippage
        ga_size = self.size
        ga_pricetick = self.pricetick        
        ga_capital = self.capital
        ga_end = self.end
        ga_mode = self.mode
        ga_datasource = self.datasource
        ga_using_cursor = self.using_cursor
        ga_dbcollection = self.dbcollection
        ga_dbtype = self.dbtype
        ga_interval = self.interval.value


        # Set up genetic algorithem
        toolbox = base.Toolbox()
        toolbox.register("individual", tools.initIterate,
                         creator.Individual, generate_parameter)
        toolbox.register("population", tools.initRepeat,
                         list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", mutate_individual, indpb=1)
        toolbox.register("evaluate", ga_optimize)
        toolbox.register("select", tools.selNSGA2)

        total_size = len(settings)
        # number of individuals in each generation
        pop_size = population_size
        # number of children to produce at each generation
        lambda_ = pop_size
        # number of individuals to select for the next generation
        mu = int(pop_size * 0.8)

        cxpb = 0.95         # probability that an offspring is produced by crossover
        mutpb = 1 - cxpb    # probability that an offspring is produced by mutation
        ngen = ngen_size    # number of generation

        pop = toolbox.population(pop_size)
        hof = tools.ParetoFront()               # end result of pareto front

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        np.set_printoptions(suppress=True)
        stats.register("mean", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)

        # Multiprocessing is not supported yet.
        # pool = multiprocessing.Pool(multiprocessing.cpu_count())
        # toolbox.register("map", pool.map)

        # Run ga optimization
        self.output(f"参数优化空间：{total_size}")
        self.output(f"每代族群总数：{pop_size}")
        self.output(f"优良筛选个数：{mu}")
        self.output(f"迭代次数：{ngen}")
        self.output(f"交叉概率：{cxpb:.0%}")
        self.output(f"突变概率：{mutpb:.0%}")

        start = ttime()

        algorithms.eaMuPlusLambda(
            pop,
            toolbox,
            mu,
            lambda_,
            cxpb,
            mutpb,
            ngen,
            stats,
            halloffame=hof
        )

        end = ttime()
        cost = int((end - start))

        self.output(f"遗传算法优化完成，耗时{cost}秒")

        # Return result list
        results = []

        for parameter_values in hof:
            setting = dict(parameter_values)
            target_value = ga_optimize(parameter_values)[0]
            results.append((setting, target_value, {}))

        return results

    def update_daily_close(self, price: float):
        """"""
        # 每天下午5点结算，晚上算另外一个交易日,周五算到下周一

        d = self.datetime.date()
        t = self.datetime.time()
        if t > time(hour=17, minute=0):
            if d.weekday() == 4:
                d = d + timedelta(days=3)
            else:
                d = d + timedelta(days=1)
        elif t < time(hour=8, minute=0):  # 周六凌晨算周一
            if d.weekday() == 5:
                d = d + timedelta(days=2)
        daily_result = self.daily_results.get(d, None)
        if daily_result:
            daily_result.close_price = price
            self.holding.last_price = price
        else:
            self.daily_results[d] = DailyResult(d, price)
            # 逐日盯市，改变持仓成本价格,需要用结算价（对商品期货是每日加权平均）
            # self.holding.long_price = self.holding.last_price
            # self.holding.short_price = self.holding.last_price
            self.holding.last_price = price

    def new_bar(self, bar: BarData):
        """"""
        self.bar = bar
        self.datetime = bar.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_bar(bar)

        self.update_daily_close(bar.close_price)

    def new_tick(self, tick: TickData):
        """"""
        self.tick = tick
        self.datetime = tick.datetime

        self.cross_limit_order()
        self.cross_stop_order()
        self.strategy.on_tick(tick)

        self.update_daily_close(tick.last_price)

    def cross_limit_order(self):
        """
        Cross limit order with last bar/tick data.
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.low_price
            short_cross_price = self.bar.high_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.ask_price_1
            short_cross_price = self.tick.bid_price_1
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        rejectedoids = []

        for order in list(self.active_limit_orders.values()):
            # Push order update with status "not traded" (pending).
            # if order.status == Status.SUBMITTING:
            #     order.status = Status.NOTTRADED
            #     self.strategy.on_order(order)

            # Check whether limit orders can be filled.
            long_cross = (
                order.direction == Direction.LONG
                and order.price >= long_cross_price
                and long_cross_price > 0
            )

            short_cross = (
                order.direction == Direction.SHORT
                and order.price <= short_cross_price
                and short_cross_price > 0
            )

            if not long_cross and not short_cross:
                continue

            if order.offset == Offset.CLOSE:
                noshortpos = (order.direction == Direction.LONG) and (
                    self.holding.short_pos < order.volume)
                nolongpos = (order.direction == Direction.SHORT) and (
                    self.holding.long_pos < order.volume)
                if nolongpos or noshortpos:
                    rejectedoids.append(order.client_order_id)
                    continue

            # Push order udpate with status "all traded" (filled).
            order.traded = order.volume
            order.status = Status.ALLTRADED
            self.strategy.on_order(order)

            self.active_limit_orders.pop(order.client_order_id)

            # Push trade update
            self.trade_count += 1

            if long_cross:
                trade_price = min(order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = max(order.price, short_best_price)
                pos_change = -order.volume

            turnover = trade_price * order.volume * self.size
            commission = turnover * self.rate
            slippage = order.volume * self.size * self.slippage

            trade = BacktestTradeData(
                full_symbol=order.full_symbol,
                symbol=order.symbol,
                exchange=order.exchange,
                client_order_id=order.client_order_id,
                tradeid=str(self.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                turnover=turnover,
                commission=commission,
                slippage=slippage,
                datetime=self.datetime,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            if trade.offset == Offset.CLOSE:  # 平仓不会影响持仓成本价格
                if trade.direction == Direction.LONG:
                    trade.short_pnl = trade.volume * \
                        (self.holding.short_price - trade.price) * self.size
                else:
                    trade.long_pnl = trade.volume * \
                        (trade.price - self.holding.long_price) * self.size
            self.holding.update_trade(trade)
            trade.long_pos = self.holding.long_pos
            trade.long_price = self.holding.long_price
            trade.short_pos = self.holding.short_pos
            trade.short_price = self.holding.short_price

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

            self.trades[trade.vt_tradeid] = trade

        for oid in rejectedoids:
            order = self.active_limit_orders.pop(oid)
            order.status = Status.REJECTED
            # Push update to strategy.
            self.strategy.on_order(order)

    def cross_stop_order(self):
        """
        Cross stop order with last bar/tick data.
        """
        if self.mode == BacktestingMode.BAR:
            long_cross_price = self.bar.high_price
            short_cross_price = self.bar.low_price
            long_best_price = self.bar.open_price
            short_best_price = self.bar.open_price
        else:
            long_cross_price = self.tick.last_price
            short_cross_price = self.tick.last_price
            long_best_price = long_cross_price
            short_best_price = short_cross_price

        rejectedoids = []

        for stop_order in list(self.active_stop_orders.values()):
            # Check whether stop order can be triggered.
            long_cross = (
                stop_order.direction == Direction.LONG
                and stop_order.price <= long_cross_price
            )

            short_cross = (
                stop_order.direction == Direction.SHORT
                and stop_order.price >= short_cross_price
            )

            if not long_cross and not short_cross:
                continue

            # close order must satisfy conditon that there are enough positions to close.
            if stop_order.offset == Offset.CLOSE:
                noshortpos = (stop_order.direction == Direction.LONG) and (
                    self.holding.short_pos < stop_order.volume)
                nolongpos = (stop_order.direction == Direction.SHORT) and (
                    self.holding.long_pos < stop_order.volume)
                if nolongpos or noshortpos:
                    rejectedoids.append(stop_order.client_order_id)
                    continue

            self.limit_order_count += 1
            stop_order.status = Status.ALLTRADED

            self.limit_orders[stop_order.client_order_id] = stop_order

            # Create trade data.
            if long_cross:
                trade_price = max(stop_order.price, long_best_price)
                pos_change = stop_order.volume
            else:
                trade_price = min(stop_order.price, short_best_price)
                pos_change = -stop_order.volume

            self.trade_count += 1

            turnover = trade_price * stop_order.volume * self.size
            commission = turnover * self.rate
            slippage = stop_order.volume * self.size * self.slippage

            trade = BacktestTradeData(
                full_symbol=stop_order.full_symbol,
                symbol=stop_order.symbol,
                exchange=stop_order.exchange,
                client_order_id=stop_order.client_order_id,
                tradeid=str(self.trade_count),
                direction=stop_order.direction,
                offset=stop_order.offset,
                price=trade_price,
                volume=stop_order.volume,
                turnover=turnover,
                commission=commission,
                slippage=slippage,
                datetime=self.datetime,
                time=self.datetime.strftime("%H:%M:%S"),
                gateway_name=self.gateway_name,
            )
            if trade.offset == Offset.CLOSE:  # 平仓不会影响持仓成本价格
                if trade.direction == Direction.LONG:
                    trade.short_pnl = trade.volume * \
                        (self.holding.short_price - trade.price) * self.size
                else:
                    trade.long_pnl = trade.volume * \
                        (trade.price - self.holding.long_price) * self.size
            self.holding.update_trade(trade)
            trade.long_pos = self.holding.long_pos
            trade.long_price = self.holding.long_price
            trade.short_pos = self.holding.short_pos
            trade.short_price = self.holding.short_price

            self.trades[trade.vt_tradeid] = trade

            # Update stop order.

            self.active_stop_orders.pop(stop_order.client_order_id, None)

            # Push update to strategy.
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(stop_order)

            self.strategy.pos += pos_change
            self.strategy.on_trade(trade)

        for oid in rejectedoids:
            stop_order = self.active_stop_orders.pop(oid)
            stop_order.status = Status.REJECTED
            self.limit_order_count += 1
            self.limit_orders[oid] = stop_order
            # Push update to strategy.
            self.strategy.on_stop_order(stop_order)
            self.strategy.on_order(stop_order)

    def load_bar(self, 
        full_symbol: str, 
        days: int, 
        interval: Interval, 
        callback: Callable, 
        datasource: str = 'DataBase',
        dbcollection: str = 'db_bar_data'
    ):
        """
        called by strategy
        """
        # 以交易日为准，一星期内的时间补上周末二天，大于一周的时间暂不考虑补全额外的交易日
        tradedays = abs(days)
        weekday = self.start.weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        start = self.start - timedelta(days=tradedays)
        end = self.start
        if datasource == 'DataBase':
            self.history_bar = load_bar_data(
                full_symbol,
                interval,
                start,
                end, 
                dbcollection,
                True
            )
            self.history_bar_startix = 0
            self.history_bar_endix = len(self.history_bar)
        elif datasource == "Memory":
            startix = 0
            endix = 0
            fullsyminterval = full_symbol + '-' + interval.value
            totalbarlist = SQGlobal.history_bar[fullsyminterval]
            if not totalbarlist:
                self.output('load_bar数据为空，请先读入')
                return
            totalbars = len(totalbarlist)
            startix = totalbars - 1
            for i in range(totalbars):
                if totalbarlist[i].datetime < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalbars)):
                if totalbarlist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalbars)
            self.history_bar_startix = startix
            self.history_bar_endix = endix
            self.history_bar = totalbarlist

        self.historybar_callback = callback
        if self.historybar_callback:
            for data in self.history_bar[self.history_bar_startix:self.history_bar_endix]:
                self.historybar_callback(data)

        # self.days = days
        # self.callback = callback

    def load_tbtbar(
        self, 
        full_symbol: str,
        days: int, 
        interval: Interval,
        callback: Callable, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_tbtbar_data'
    ):
        """
        called by strategy
        """
        # 以交易日为准，一星期内的时间补上周末二天，大于一周的时间暂不考虑补全额外的交易日
        tradedays = abs(days)
        weekday = self.start.weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        start = self.start - timedelta(days=tradedays)
        end = self.start
        if datasource == 'DataBase':
            self.history_bar = load_tbtbar_data(
                full_symbol,
                interval,
                start,
                end,
                dbcollection
            )
            self.history_bar_startix = 0
            self.history_bar_endix = len(self.history_bar)
        elif datasource == "Memory":
            startix = 0
            endix = 0
            fullsyminterval  = full_symbol + '-' + interval.value
            totalbarlist = SQGlobal.history_tbtbar[fullsyminterval]  
            if not totalbarlist:
                self.output('load_tbtbar数据为空，请先读入')
                return
            totalbars = len(totalbarlist)
            startix = totalbars - 1
            for i in range(totalbars):
                if totalbarlist[i].datetime < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalbars)):
                if totalbarlist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalbars)
            self.history_bar_startix = startix
            self.history_bar_endix = endix
            self.history_bar = totalbarlist

        self.historybar_callback = callback
        if self.historybar_callback:
            for data in self.history_bar[self.history_bar_startix:self.history_bar_endix]:
                self.historybar_callback(data)






    def load_tick(self, 
        full_symbol: str, 
        days: int, 
        callback: Callable, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_tick_data'
    ):
        """
        called by strategy
        """
        tradedays = abs(days)
        weekday = self.start.weekday()
        adddays = 2 if (days - weekday > 0) else 0
        if weekday == 6:
            tradedays = days + 1
        else:
            tradedays = days + adddays

        start = self.start - timedelta(days=tradedays)
        end = self.start
        if datasource == 'DataBase':
            self.history_tick = load_tick_data(
                full_symbol,
                start,
                end,
                dbcollection,
                True
            )
            self.history_tick_startix = 0
            self.history_tick_endix = len(self.history_tick)

        elif datasource == 'Memory':
            startix = 0
            endix = 0
            totalticklist = SQGlobal.history_tick[full_symbol]
            if not totalticklist:
                self.output('load_tick数据为空，请先读入')
                return
            totalticks = len(totalticklist)
            startix = totalticks - 1
            for i in range(totalticks):
                if totalticklist[i].datetime < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalticks)):
                if totalticklist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalticks)
            self.history_tick_startix = startix
            self.history_tick_endix = endix
            self.history_tick = totalticklist

        self.historytick_callback = callback
        if self.historytick_callback:
            for data in self.history_tick[self.history_tick_startix:self.history_tick_endix]:
                self.historytick_callback(data)


    def send_order(
        self,
        strategy: CtaTemplate,
        req: OrderData,
        lock: bool = False,
        stop: bool = False
    ):
        """"""

        req.client_order_id = self.order_count
        req.time = self.datetime   # here time used as datetime
        self.order_count += 1
        req.status = Status.NOTTRADED
        self.limit_order_count += 1
        self.strategy_orderid_map[strategy.strategy_name].add(
            req.client_order_id)
        self.active_limit_orders[req.client_order_id] = req
        self.limit_orders[req.client_order_id] = req

        return [req.client_order_id]

    def send_stop_order(
        self,
        strategy: CtaTemplate,
        req: OrderData, 
        lock: bool = False
    ):
        """"""
        req.client_order_id = self.order_count
        req.time = self.datetime
        self.order_count += 1
        req.status = Status.NEWBORN
        self.stop_order_count += 1
        self.strategy_orderid_map[strategy.strategy_name].add(
            req.client_order_id)
        self.active_stop_orders[req.client_order_id] = req
        self.stop_orders[req.client_order_id] = req

        return [req.client_order_id]

    def cancel_order(self, strategy: CtaTemplate, orderid: int):
        """
        Cancel order by orderid.
        """
        if orderid in self.active_limit_orders:
            order = self.active_limit_orders.pop(orderid)
            order.status = Status.CANCELLED
            self.strategy.on_order(order)
        elif orderid in self.active_stop_orders:
            stop_order = self.active_stop_orders.pop(orderid)
            stop_order.status = Status.CANCELLED
            self.strategy.on_stop_order(stop_order)

    def cancel_all(self, strategy: CtaTemplate, full_symbol: str = ''):
        """
        Cancel all orders, both limit and stop.
        """
        orderids = list(self.active_limit_orders.keys())
        for orderid in orderids:
            order = self.active_limit_orders.pop(orderid)
            order.status = Status.CANCELLED
            self.strategy.on_order(order)

        stop_orderids = list(self.active_stop_orders.keys())
        for orderid in stop_orderids:
            stop_order = self.active_stop_orders.pop(orderid)
            stop_order.status = Status.CANCELLED
            self.strategy.on_stop_order(stop_order)

    def write_log(self, msg: str, strategy: CtaTemplate = None):
        """
        Write log message.
        """
        msg = f"{self.datetime}\t{msg}"
        self.logs.append(msg)

    def send_email(self, msg: str, strategy: CtaTemplate = None):
        """
        Send email to default receiver.
        """
        pass

    def get_engine_type(self):
        """
        Return engine type.
        """
        return self.engine_type

    def put_strategy_event(self, strategy: CtaTemplate):
        """
        Put an event to update strategy status.
        """
        pass

    def output(self, msg):
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")

    def sync_strategy_data(self, strategy: CtaTemplate):
        pass

    def get_position_holding(self, acc: str, full_symbol: str):
        return self.holding

    def get_account(self, accountid):
        pass

    def get_order(self, orderid: int):
        if orderid in self.limit_orders:
            order = self.limit_orders.get(orderid)
            return order
        if orderid in self.stop_orders:
            order = self.stop_orders.get(orderid)
            return order

    def get_tick(self, full_symbol: str):
        pass

    def get_trade(self, vt_tradeid):
        return self.trades.get(vt_tradeid, None)

    def get_all_trades(self):
        return list(self.trades.values())

    def get_position(self, key):
        pass

    def get_contract(self, full_symbol):
        return self.contract

    def get_all_active_orders(self, full_symbol: str = ""):
        active_orders = list(self.active_limit_orders.values())
        active_orders.extend(self.active_stop_orders.values())
        return active_orders

    def get_strategy_active_orderids(self, strategy_name: str):
        active_orderids = set(self.active_limit_orders.keys())
        return active_orderids

    def get_all_orders(self):
        """
        Return all limit order data of current backtesting result.
        """
        return list(self.limit_orders.values())

    def get_all_daily_results(self):
        """
        Return all daily result data.
        """
        return list(self.daily_results.values())


class DailyResult:
    """"""

    def __init__(self, date: date, close_price: float):
        """"""
        self.date = date
        self.close_price = close_price
        self.pre_close = 0

        # 20200808:  start_pos' s date,  for xd,xr use  
        self.pre_date = date

        self.open_price = 0

        self.trades = []
        self.trade_count = 0

        self.start_pos = 0
        self.end_pos = 0

        self.turnover = 0
        self.commission = 0
        self.slippage = 0

        self.trading_pnl = 0
        self.holding_pnl = 0
        self.total_pnl = 0
        self.net_pnl = 0

        self.margin = 0
        self.maxmargin = 0

    def add_trade(self, trade: Union[TradeData, BacktestTradeData]):
        """"""
        self.trades.append(trade)



    def calculate_margin(
        self,
        pre_margin: float,
        contracts:dict = None,
    ):
        """"""
        self.margin = pre_margin
        self.maxmargin = max(self.maxmargin, self.margin)

        for trade in self.trades:
            if not contracts:
                contract = ContractData(full_symbol=trade.full_symbol)
            else:
                contract = contracts.get(trade.full_symbol, ContractData(full_symbol=trade.full_symbol))

            if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                self.margin += trade.turnover *contract.long_margin_ratio
            elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                self.margin += trade.turnover *contract.short_margin_ratio
            elif trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                self.margin -= (trade.turnover *contract.short_margin_ratio + trade.short_pnl)                
            elif trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                self.margin -= (trade.turnover * contract.long_margin_ratio - trade.long_pnl)

            self.maxmargin = max(self.maxmargin, self.margin)


    def calculate_pnl(
        self,
        pre_close: float,
        start_pos: float,
        size: int,
        rate: float,
        slippage: float,
    ):
        """"""
        self.pre_close = pre_close

        # Holding pnl is the pnl from holding position at day start
        self.start_pos = start_pos
        self.end_pos = start_pos
        self.holding_pnl = self.start_pos * \
            (self.close_price - self.pre_close) * size

        # Trading pnl is the pnl from new trade during the day
        self.trade_count = len(self.trades)

        for trade in self.trades:
            if trade.direction == Direction.LONG:
                pos_change = trade.volume
            else:
                pos_change = -trade.volume

            turnover = trade.price * trade.volume * size

            self.trading_pnl += pos_change * \
                (self.close_price - trade.price) * size
            self.end_pos += pos_change
            self.turnover += turnover
            self.commission += turnover * rate
            self.slippage += trade.volume * size * slippage

        # Net pnl takes account of commission and slippage cost
        self.total_pnl = self.trading_pnl + self.holding_pnl
        self.net_pnl = self.total_pnl - self.commission - self.slippage


    def calculate_pnltbt(
        self,
        pre_price: float,
        start_pos: float,
        size: int,
        rate: float,
        slippage: float,
    ):
        """"""
        self.open_price = pre_price

        # Holding pnl is ignored since no close price info
        self.start_pos = start_pos
        self.end_pos = start_pos
        self.holding_pnl = 0

        # Trading pnl is the pnl closed by trade
        self.trade_count = len(self.trades)

        for trade in self.trades:
            if trade.turnover:
                tsize = trade.turnover / trade.price / trade.volume
            else:
                tsize = size

            if trade.direction == Direction.LONG:
                pos_change = trade.volume
                beginpos =  self.end_pos
                self.end_pos += pos_change

                if beginpos >= 0: #净增多仓
                    self.open_price = (beginpos * self.open_price + trade.price * trade.volume) / self.end_pos 
                elif beginpos < 0 and self.end_pos <= 0:  # 平空
                    self.trading_pnl += pos_change * (self.open_price - trade.price) * tsize

                else:  #平空，开多
                    self.trading_pnl += -1*beginpos * \
                        (self.open_price - trade.price) * tsize
                    self.open_price = trade.price
            else:
                pos_change = -trade.volume
                beginpos =  self.end_pos
                self.end_pos += pos_change

                if beginpos <= 0: #净增空仓
                    self.open_price = (beginpos * self.open_price - trade.price * trade.volume) / self.end_pos
                elif beginpos >0 and self.end_pos >=0:  # 平多
                    self.trading_pnl += pos_change * (self.open_price - trade.price) * tsize
                else:  # 平多，开空
                    self.trading_pnl += -1*beginpos * \
                        (self.open_price - trade.price) * tsize                    
                    self.open_price = trade.price
            if trade.turnover:
                turnover = trade.turnover
            else:
                turnover = trade.price * trade.volume * tsize
            self.turnover += turnover
            if trade.commission:
                self.commission += trade.commission
            else:
                self.commission += turnover * rate
            if trade.slippage:
                self.slippage += trade.slippage
            else:
                self.slippage += trade.volume * tsize * slippage

        # Net pnl takes account of commission and slippage cost
        self.total_pnl = self.trading_pnl + self.holding_pnl
        self.net_pnl = self.total_pnl - self.commission - self.slippage


#TODO: using ray to do distributed optimazation and backtest
# @ray.remote(max_calls=1)
def optimize_remote(
    target_name: str,
    strategy_class: CtaTemplate,
    setting: dict,
    full_symbol: str,
    start: datetime,
    rate: float,
    slippage: float,
    size: float,
    pricetick: float,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    datasource: str = "DataBase", 
    using_cursor: bool = False,
    dbcollection:str = 'db_bar_data',
    dbtype:str = 'Bar',
    interval: str = '1m'
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,
        full_symbol=full_symbol,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    statistics = engine.calculate_statistics(output=False)

    target_value = statistics[target_name]
    return (setting, target_value, statistics)


def optimize(
    target_name: str,
    strategy_class: CtaTemplate,
    setting: dict,
    full_symbol: str,
    start: datetime,
    rate: float,
    slippage: float,
    size: float,
    pricetick: float,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    datasource: str = "DataBase", 
    using_cursor: bool = False,
    dbcollection:str = 'db_bar_data',
    dbtype:str = 'Bar',
    interval: str = '1m'
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,
        full_symbol=full_symbol,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    statistics = engine.calculate_statistics(output=False)

    target_value = statistics[target_name]
    return (setting, target_value, statistics)


def roll_optimize(
    strategy_class: CtaTemplate,
    setting: dict,
    full_symbol: str,
    start: datetime,
    rate: float,
    slippage: float,
    size: float,
    pricetick: float,
    capital: int,
    end: datetime,
    mode: BacktestingMode,
    datasource: str = "DataBase", 
    using_cursor: bool = False,
    dbcollection:str = 'db_bar_data',
    dbtype:str = 'Bar',
    interval: str = '1m'
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,        
        full_symbol=full_symbol,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
        mode=mode
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    # balance = df["net_pnl"].cumsum() + capital

    return (setting, df)




def mp_backtest(
    strategy_class,
    setting,
    full_symbol,
    start,
    rate,
    slippage,
    size,
    pricetick,
    capital,
    end,
    datasource,
    using_cursor,
    dbcollection,
    dbtype,
    interval    
):

    engine = BacktestingEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,
        full_symbol=full_symbol,
        start=start,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        end=end,
    )

    engine.add_strategy(
        strategy_class,
        setting
    )
    engine.load_data()
    success = engine.run_backtesting()
    if not success:
        return (full_symbol,{},[])
    engine.calculate_result()

    trades = engine.get_all_trades()
    dailyresults = engine.daily_results

    return (full_symbol,dailyresults,trades)


def mp_backtest_pro(
    strategy_class,
    setting,
    full_symbol,
    start,
    end,
    capital,
    contracts,
    datasource,
    using_cursor,
    dbcollection,
    dbtype,
    interval    
):
    engine = BacktestingProEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,
        full_symbol=full_symbol,
        start=start,
        end=end,
        capital=capital,
        contracts=contracts,
     )

    engine.add_strategy(
        strategy_class,
        setting
    )
    engine.load_data()
    success = engine.run_backtesting()
    if not success:
        return (full_symbol,{},[])
    engine.calculate_result()

    trades = engine.get_all_trades()
    dailyresults = engine.total_daily_results

    return (full_symbol,dailyresults,trades)




def optimize_pro(
    target_name: str,
    strategy_class: CtaTemplate,
    setting: dict,
    full_symbol: str,
    start: datetime,
    end: datetime,
    capital: int,
    contracts:dict,
    mode: BacktestingMode,
    datasource: str = "DataBase", 
    using_cursor: bool = False,
    dbcollection:str = 'db_bar_data',
    dbtype: str = 'Bar',
    interval: str = '1m'
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingProEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,        
        full_symbol=full_symbol,
        start=start,
        end=end,        
        capital=capital,
        contracts=contracts,
        mode=mode
    )

    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    statistics = engine.calculate_statistics(output=False)

    target_value = statistics[target_name]
    return (setting, target_value, statistics)




def roll_optimize_pro(
    strategy_class: CtaTemplate,
    setting: dict,
    full_symbol: str,
    start: datetime,
    end: datetime,
    capital: int,
    contracts:dict,
    mode: BacktestingMode,
    datasource: str = "DataBase", 
    using_cursor: bool = False,
    dbcollection:str = 'db_bar_data',
    dbtype: str = 'Bar',
    interval: str = '1m'
):
    """
    Function for running in multiprocessing.pool
    """
    engine = BacktestingProEngine()

    engine.set_parameters(
        datasource=datasource,
        using_cursor=using_cursor,
        dbcollection=dbcollection,
        dbtype=dbtype,
        interval=interval,
        full_symbol=full_symbol,
        start=start,
        end=end,        
        capital=capital,
        contracts=contracts,
        mode=mode
    )


    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()

    return (setting, df)





@lru_cache(maxsize=1048576)
def _ga_optimize(parameter_values: tuple):
    """"""
    setting = dict(parameter_values)

    result = optimize(
        ga_target_name,
        ga_strategy_class,
        setting,
        ga_full_symbol,
        ga_start,
        ga_rate,
        ga_slippage,
        ga_size,
        ga_pricetick,
        ga_capital,
        ga_end,
        ga_mode,
        ga_datasource,
        ga_using_cursor,
        ga_dbcollection,
        ga_dbtype,
        ga_interval,
    )
    return (result[1],)

@lru_cache(maxsize=1048576)
def _ga_optimize_pro(parameter_values: tuple):
    """"""
    setting = dict(parameter_values)

    result = optimize_pro(
        ga_target_name,
        ga_strategy_class,
        setting,
        ga_full_symbol,
        ga_start,
        ga_end,
        ga_capital,
        ga_contracts,
        ga_mode,
        ga_datasource,
        ga_using_cursor,
        ga_dbcollection,
        ga_dbtype,
        ga_interval,
    )
    return (result[1],)

def ga_optimize(parameter_values: list):
    """"""
    return _ga_optimize(tuple(parameter_values))

def ga_optimize_pro(parameter_values: list):
    """"""
    return _ga_optimize_pro(tuple(parameter_values))

@lru_cache(maxsize=1048576)
def load_bar_data(
    full_symbol: str,
    interval: Interval,
    start: datetime,
    end: datetime,
    collectionname:str ='db_bar_data',
    using_in: bool = False,
    using_cursor: bool = False
):
    """"""
    return database_manager.load_bar_data(
        full_symbol, interval, start, end, collectionname, using_in,using_cursor
    )

@lru_cache(maxsize=1048576)
def load_tbtbar_data(
    full_symbol: str,
    interval: Interval,
    start: datetime,
    end: datetime,
    collectionname: str='db_tbtbar_data',
    using_cursor: bool = False
):
    """"""
    return database_manager.load_tbtbar_data(
        full_symbol, interval, start, end,collectionname,using_cursor
    )






@lru_cache(maxsize=1048576)
def load_tick_data(
    full_symbol: str,
    start: datetime,
    end: datetime,
    collectionname:str ='db_tick_data',
    using_in: bool = False,
    using_cursor: bool = False
):
    """"""
    return database_manager.load_tick_data(
        full_symbol, start, end, collectionname,using_in,using_cursor
    )


# GA related global value
ga_end = None
ga_mode = None
ga_target_name = None
ga_strategy_class = None
ga_setting = None
ga_full_symbol = None
ga_start = None
ga_rate = None
ga_slippage = None
ga_size = None
ga_pricetick = None
ga_capital = None
ga_datasource = None
ga_contracts = None
ga_using_cursor = None
ga_dbcollection = None
ga_dbtype = None
ga_interval = None
