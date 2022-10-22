"""
Event-driven Bactester 
"""

import importlib
import traceback
from datetime import datetime, timedelta
from threading import Thread
from pathlib import Path
from copy import deepcopy
import os




from pystarquant.common.constant import Interval, EventType,Direction,Offset
from pystarquant.common.datastruct import Event,BacktestTradeData
from pystarquant.engine.iengine import EventEngine
from pystarquant.engine.backtest_engine import BacktestingEngine, BacktestingProEngine, OptimizationSetting
from pystarquant.strategy.strategy_base import StrategyBase,IndicatorBase
import pystarquant.common.sqglobal as SQGlobal


CtaTemplate = StrategyBase


class Backtester:
    """
    For running CTA strategy backtesting.
    """

    def __init__(self, event_engine: EventEngine = None):
        """"""
        super().__init__()
        if event_engine:
            self.event_engine = event_engine
        else:
            self.event_engine = None
        self.classes = {}
        self.backtesting_engine = None
        self.backtestingpro_engine = None
        self.virtualengine = None  #used to add,append,compare results
        self.thread = None

        # Backtesting reuslt
        self.result_df = None
        self.result_statistics = None
        self.result_trades = []
        self.result_dailys = []

        # Optimization result
        self.result_values = None



    def init_engine(self):
        """"""
        self.write_log("初始化回测引擎")

        self.backtesting_engine = BacktestingEngine()
        # Redirect log from backtesting engine outside.
        self.backtesting_engine.output = self.write_log

        self.backtestingpro_engine = BacktestingProEngine()
        self.backtestingpro_engine.output = self.write_log

        self.virtualengine = BacktestingProEngine()
        self.virtualengine.output = self.write_log

        self.write_log("回测引擎加载完成")

        # self.load_strategy_class()

        self.load_strategy()

        self.write_log("策略文件加载完成")

    def write_log(self, msg: str):
        """"""
        if self.event_engine:
            event = Event(type=EventType.BACKTEST_LOG)
            event.data = msg
            self.event_engine.put(event)
        else:
            print(str)


    def load_strategy(self,reload: bool = False):

        if reload:
            SQGlobal.strategyloader.load_class(True)

        self.classes =  SQGlobal.strategyloader.classes

    def get_strategy_class_names(self):
        """"""
        return list(self.classes.keys())

    def run_backtesting(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        setting: dict,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',
        interval: str = '1m',
    ):
        """"""
        self.result_df = None
        self.result_statistics = None

        engine = self.backtesting_engine
        engine.clear_data()

        engine.set_parameters(
            datasource=datasource,
            using_cursor=using_cursor,
            dbcollection=dbcollection,
            dbtype=dbtype,
            interval=interval,            
            full_symbol=full_symbol,
            start=start,
            end=end,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            capital=capital
        )

        strategy_class = self.classes[class_name]
        engine.add_strategy(
            strategy_class,
            setting
        )
        try:
            engine.load_data()
            success = engine.run_backtesting()
            if success:
                self.result_df = engine.calculate_result()
                self.result_statistics = engine.calculate_statistics(output=False)
                self.result_trades = engine.get_all_trades()
                self.result_dailys = engine.get_all_daily_results()

                # Put backtesting done event
                if self.event_engine:
                    event = Event(type=EventType.BACKTEST_FINISH)
                    self.event_engine.put(event)
        except:
            msg = f"回测触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg)
        # Clear thread object handler.
        self.thread = None

   

    def run_batch_bt(
        self,
        settinglist: dict,
        capital: int,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',
    ):
        """"""
        self.result_df = None
        self.result_statistics = None
        self.result_trades = []

        engine = self.backtesting_engine
        engine.clear_data()
        engine.clear_total_data()

        class_namelist = settinglist['strategy']
        stragegysettinglist = settinglist['parameter']
        fsmlist = settinglist['full_symbol']
        startlist = settinglist['start']
        endlist = settinglist['end']
        ratelist = settinglist['rate']
        slippagelist = settinglist['slippage']
        sizelist = settinglist['size']
        priceticklist = settinglist['pricetick']


        
        try:
            for i in range(len(fsmlist)):
                engine.clear_data()
                class_name = class_namelist[i]
                setting = eval(stragegysettinglist[i])
                strategy_class = self.classes[class_name]
                full_symbol = fsmlist[i]
                start = startlist[i]
                end = endlist[i]
                rate = float(ratelist[i])
                slippage = float(slippagelist[i])
                size = float(sizelist[i])
                pricetick = float(priceticklist[i])

                engine.set_parameters(
                    datasource=datasource,
                    using_cursor=using_cursor,
                    dbcollection=dbcollection,
                    dbtype=dbtype,
                    interval=interval,
                    full_symbol=full_symbol,
                    start=start,
                    end=end,
                    rate=rate,
                    slippage=slippage,
                    size=size,
                    pricetick=pricetick,
                    capital=capital
                )
                
                engine.add_strategy(
                    strategy_class,
                    setting
                )

                engine.load_data()
                success = engine.run_backtesting()
                if not success:
                    self.thread = None
                    return
                engine.calculate_result()

                self.result_trades.extend(engine.get_all_trades())
                engine.daily_results_dict[full_symbol] = deepcopy(engine.daily_results)


            self.result_df = engine.calculate_total_result()
            self.result_statistics = engine.calculate_statistics(df=self.result_df, output=False, trades=self.result_trades)

            self.result_dailys = list(engine.total_daily_results.values())

            # Put backtesting done event
            if self.event_engine:
                event = Event(type=EventType.BACKTEST_FINISH)
                self.event_engine.put(event)            
        except:
            msg = f"批量回测触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg)

        # Clear thread object handler.
        self.thread = None



    def run_batch_bt_mp(
        self,
        cpunums,
        settinglist: dict,
        capital: int,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',        
    ):
        """"""
        self.result_df = None
        self.result_statistics = None
        self.result_trades = []

        engine = self.backtesting_engine
        engine.clear_data()
        engine.clear_total_data()
        engine.set_parameters(capital=capital)

        try:
            resultslist = engine.run_mp_backtest(
                cpunums,
                self.classes,
                settinglist,
                capital,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                interval
                )
            num = 0
            for (full_symbol, daily_results,trades) in resultslist:
                num += 1
                # if full_symbol in engine.daily_results_dict:
                #     self.write_log("重复的合约全称，忽略")
                #     continue
                fullsym = full_symbol + '_' + str(num)
                self.result_trades.extend(trades)
                engine.daily_results_dict[fullsym] = daily_results
                engine.load_list_trades(trades)

            self.result_df = engine.calculate_total_result()
            self.result_statistics = engine.calculate_statistics(df=self.result_df, output=False, trades=self.result_trades)

            self.result_dailys = list(engine.total_daily_results.values())

            # Put backtesting done event
            if self.event_engine:
                event = Event(type=EventType.BACKTEST_FINISH)
                self.event_engine.put(event)  

        except:
            msg = f"多进程批量回测触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg)

        # Clear thread object handler.
        self.thread = None


    def run_batch_btpro_mp(
        self,
        cpunums,
        settinglist: dict,
        capital: int,
        contracts:dict = None,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_tbtbar_data',
        dbtype:str = 'TbtBar',
        interval: str = '1m',
    ):
        """"""
        self.result_df = None
        self.result_statistics = None
        self.result_trades = []

        engine = self.backtestingpro_engine
        engine.clear_data()
        engine.clear_batch_data()
        engine.set_parameters(capital=capital,contracts=contracts)

        try:
            resultslist = engine.run_mp_backtest_pro(
                cpunums,
                self.classes,
                settinglist,
                capital,
                contracts,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                interval
            )
            num = 0
            for (full_symbol, daily_results,trades) in resultslist:
                num += 1
                fullsym = full_symbol + '_' + str(num)
                # if full_symbol in engine.batch_daily_results_dict:
                #     self.write_log("重复的合约全称，忽略")
                #     continue
                self.result_trades.extend(trades)
                engine.batch_daily_results_dict[fullsym] = daily_results
                engine.load_list_trades(trades)

            self.result_df = engine.calculate_batch_result()
            self.result_statistics = engine.calculate_statistics(df=self.result_df, output=False, trades=self.result_trades)

            self.result_dailys = list(engine.batch_total_daily_results.values())

            # Put backtesting done event
            if self.event_engine:
                event = Event(type=EventType.BACKTEST_FINISH)
                self.event_engine.put(event)  

        except:
            msg = f"多进程批量pro回测触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg)

        # Clear thread object handler.
        self.thread = None



    def run_backtesting_pro(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        capital: int,
        setting: dict,
        contracts:dict = None,
        datasource: str = "DataBase", 
        using_cursor: bool = False,
        dbcollection:str = 'db_tbtbar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',         
    ):
        """"""
        self.result_df = None
        self.result_statistics = None
        self.result_trades = []

        engine = self.backtestingpro_engine
        engine.clear_data()
        try:
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
                contracts=contracts
            )

            strategy_class = self.classes[class_name]
            engine.add_strategy(
                strategy_class,
                setting
            )

            engine.load_data()
            success =  engine.run_backtesting()
            
            if not success:
                self.thread = None
                return
            self.result_df = engine.calculate_result()
            self.result_statistics = engine.calculate_statistics(output=False)
            self.result_trades = engine.get_all_trades()
            self.result_dailys = engine.get_all_daily_results()
            # Put backtesting done event
            if self.event_engine:
                event = Event(type=EventType.BACKTEST_FINISH)
                self.event_engine.put(event)

        except:
            msg = f"回测触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg)
        # Clear thread object handler.
        self.thread = None





    def start_backtesting(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        setting: dict,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m'
    ):        
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_backtesting,
            args=(
                class_name,
                full_symbol,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                setting,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                interval,
            )
        )
        self.thread.start()

        return True

    def start_batch_bt(
        self,
        btsettinglist: dict,
        capital: int,
        datasource: str = "DataBase", 
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False
        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_batch_bt,
            args=(
                btsettinglist,
                capital,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,        
                interval,
            )
        )
        self.thread.start()

        return True



    def start_batch_bt_mp(
        self,
        cpunums,
        btsettinglist: dict,
        capital: int,
        datasource: str = "DataBase",
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False
        self.write_log("开始多进程批量回测")
        self.thread = Thread(
            target=self.run_batch_bt_mp,
            args=(
                cpunums,
                btsettinglist,
                capital,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,        
                interval,
            )
        )
        self.thread.start()

        return True

    def start_batch_btpro_mp(
        self,
        cpunums,
        btsettinglist: dict,
        capital: int,
        contracts:dict = None,
        datasource: str = "DataBase",        
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False
        self.write_log("开始多进程批量pro回测")
        self.thread = Thread(
            target=self.run_batch_btpro_mp,
            args=(
                cpunums,
                btsettinglist,
                capital,
                contracts,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,        
                interval,
            )
        )
        self.thread.start()

        return True


    def start_backtesting_pro(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        capital: int,
        setting: dict,
        contracts:dict = None,
        datasource: str = "DataBase", 
        usingcursor:bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype:str = 'Bar',        
        interval: str = '1m',        
    ):        
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_backtesting_pro,
            args=(
                class_name,
                full_symbol,
                start,
                end,
                capital,
                setting,
                contracts,
                datasource,
                usingcursor,
                dbcollection,
                dbtype,        
                interval,
            )
        )
        self.thread.start()

        return True


    def get_result_df(self):
        """"""
        return self.result_df

    def get_result_statistics(self):
        """"""
        return self.result_statistics

    def get_result_values(self):
        """"""
        return self.result_values

    def get_result_trades(self):
        return self.result_trades

    def get_result_daily(self):
        return self.result_dailys

    def get_default_setting(self, class_name: str):
        """"""
        strategy_class = self.classes[class_name]
        return strategy_class.get_class_parameters()

    def run_optimization(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        optimization_setting: OptimizationSetting,
        use_ga: bool,
        datasource: str = 'DataBase',
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype: str = 'Bar',
        interval: str = '1m'    
    ):
        """"""
        if use_ga:
            self.write_log("开始遗传算法参数寻优")
        elif optimization_setting.use_roll:
            self.write_log("开始多进程滚动优化")
        else:
            self.write_log("开始多进程参数寻优")

        self.result_values = None

        engine = self.backtesting_engine
        engine.clear_data()
        try:
            engine.set_parameters(
                datasource=datasource,
                using_cursor=using_cursor,
                dbcollection=dbcollection,
                dbtype=dbtype,
                interval=interval,
                full_symbol=full_symbol,
                start=start,
                end=end,
                rate=rate,
                slippage=slippage,
                size=size,
                pricetick=pricetick,
                capital=capital
            )

            strategy_class = self.classes[class_name]
            engine.add_strategy(
                strategy_class,
                {}
            )

            if use_ga:
                self.result_values = engine.run_ga_optimization(
                    optimization_setting,
                    output=False,
                )
            elif optimization_setting.use_roll:
                self.result_values = engine.run_roll_optimization(
                    optimization_setting,
                )
            else:
                self.result_values = engine.run_optimization(
                    optimization_setting,
                    output=False,
                )
            self.write_log("参数优化完成")
            # Put optimization done event
            if self.event_engine:
                event = Event(type=EventType.OPTIMIZATION_FINISH)
                self.event_engine.put(event)
        except:
            msg = f"优化触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg) 

        # Clear thread object handler.
        self.thread = None

    def run_optimization_pro(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        capital: int,
        contracts: dict,
        optimization_setting: OptimizationSetting,
        use_ga: bool,
        datasource: str = 'DataBase',
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype: str = 'Bar',
        interval: str = '1m'        
    ):
        """"""
        if use_ga:
            self.write_log("开始遗传算法参数寻优")
        elif optimization_setting.use_roll:
            self.write_log("开始多进程滚动优化")
        else:
            self.write_log("开始多进程参数寻优")

        self.result_values = None

        engine = self.backtestingpro_engine
        engine.clear_data()

        try:
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
                contracts=contracts
            )

            strategy_class = self.classes[class_name]
            engine.add_strategy(
                strategy_class,
                {}
            )

            if use_ga:
                self.result_values = engine.run_ga_optimization(
                    optimization_setting,
                    output=False,
                )
            elif optimization_setting.use_roll:
                self.result_values = engine.run_roll_optimization(
                    optimization_setting,  
                )             
            else:
                self.result_values = engine.run_optimization(
                    optimization_setting,
                    output=False,
                )

            self.write_log("参数优化完成")

            # Put optimization done event
            if self.event_engine:
                event = Event(type=EventType.OPTIMIZATION_FINISH)
                self.event_engine.put(event)
        except:
            msg = f"优化触发异常结束：\n{traceback.format_exc()}"
            self.write_log(msg) 

        # Clear thread object handler.
        self.thread = None





    def start_optimization(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        optimization_setting: OptimizationSetting,
        use_ga: bool,
        datasource: str = 'DataBase',
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype: str = 'Bar',
        interval: str = '1m'
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_optimization,
            args=(
                class_name,
                full_symbol,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                optimization_setting,
                use_ga,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                interval
            )
        )
        self.thread.start()

        return True

    def start_optimization_pro(
        self,
        class_name: str,
        full_symbol: str,
        start: datetime,
        end: datetime,
        capital: int,
        contracts:dict,
        optimization_setting: OptimizationSetting,
        use_ga: bool,
        datasource: str = 'DataBase',
        using_cursor: bool = False,
        dbcollection:str = 'db_bar_data',
        dbtype: str = 'Bar',
        interval: str = '1m'
    ):
        if self.thread:
            self.write_log("已有任务在运行中，请等待完成")
            return False

        self.write_log("-" * 40)
        self.thread = Thread(
            target=self.run_optimization_pro,
            args=(
                class_name,
                full_symbol,
                start,
                end,
                capital,
                contracts,
                optimization_setting,
                use_ga,
                datasource,
                using_cursor,
                dbcollection,
                dbtype,
                interval                
            )
        )
        self.thread.start()

        return True    
