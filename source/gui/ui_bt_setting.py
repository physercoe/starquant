#!/usr/bin/env python
# -*- coding: utf-8 -*-

import source.common.sqglobal as sqglobal
import sys
import os

from PyQt5 import QtCore, QtWidgets, QtGui, Qt
import importlib
import traceback
from datetime import datetime, timedelta
from threading import Thread
from pathlib import Path

from source.common.constant import Interval, EventType
from source.common.datastruct import HistoryRequest, Event
from source.engine.iengine import EventEngine
from source.engine.backtest_engine import BacktestingEngine, OptimizationSetting
from source.strategy.strategy_base import StrategyBase
from source.gui.ui_basic import VerticalTabBar
from source.gui.ui_bt_resultsoverview import BacktesterChart
from source.gui.ui_bt_dataview import BTQuotesChart
from source.gui.ui_bt_txnview import TradesTable, DailyTable


CtaTemplate = StrategyBase

sys.path.insert(0, "../..")


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
        self.thread = None

        # Backtesting reuslt
        self.result_df = None
        self.result_statistics = None
        self.result_trades = []
        self.result_dailys = []

        # Optimization result
        self.result_values = None

        self.load_strategy_class()

    def init_engine(self):
        """"""
        self.write_log("初始化CTA回测引擎")

        self.backtesting_engine = BacktestingEngine()
        # Redirect log from backtesting engine outside.
        self.backtesting_engine.output = self.write_log

        self.write_log("回测引擎加载完成")

    def write_log(self, msg: str):
        """"""
        if self.event_engine:
            event = Event(type=EventType.BACKTEST_LOG)
            event.data = msg
            self.event_engine.put(event)
        else:
            print(str)

    def reload_strategy(self):
        self.classes.clear()
        self.load_strategy_class(True)

    def load_strategy_class(self, reload: bool = False):
        """
        Load strategy class from source code.
        """
        # app_path = Path(__file__).parent.parent
        # path1 = app_path.joinpath("cta_strategy", "strategies")
        # self.load_strategy_class_from_folder(
        #     path1, "vnpy.app.cta_strategy.strategies")

        path2 = Path.cwd().joinpath("teststrategy")
        self.load_strategy_class_from_folder(path2, "", reload)

    def load_strategy_class_from_folder(self, path: Path, module_name: str = "", reload: bool = False):
        """
        Load strategy class from certain folder.
        """
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".py"):
                    strategy_module_name = "teststrategy.".join(
                        [module_name, filename.replace(".py", "")])
                    self.load_strategy_class_from_module(
                        strategy_module_name, reload)

    def load_strategy_class_from_module(self, module_name: str, reload: bool = False):
        """
        Load strategy class from module file.
        """
        try:
            module = importlib.import_module(module_name)
        # if reload delete old attribute
            if reload:
                for attr in dir(module):
                    if attr not in ('__name__', '__file__'):
                        delattr(module, attr)
                importlib.reload(module)
            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"策略文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

    def get_strategy_class_names(self):
        """"""
        return list(self.classes.keys())

    def run_backtesting(
        self,
        class_name: str,
        full_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        setting: dict,
        datasource: str = "DataBase"
    ):
        """"""
        self.result_df = None
        self.result_statistics = None

        engine = self.backtesting_engine
        engine.clear_data()

        engine.set_parameters(
            full_symbol=full_symbol,
            interval=interval,
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

        engine.load_data(datasource)
        engine.run_backtesting()
        self.result_df = engine.calculate_result()
        self.result_statistics = engine.calculate_statistics(output=False)
        self.result_trades = engine.get_all_trades()
        self.result_dailys = engine.get_all_daily_results()
        # Clear thread object handler.
        self.thread = None

        # Put backtesting done event
        if self.event_engine:
            event = Event(type=EventType.BACKTEST_FINISH)
            self.event_engine.put(event)

    def start_backtesting(
        self,
        class_name: str,
        full_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        setting: dict,
        datasource: str = "DataBase"
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
                interval,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                setting,
                datasource
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
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        optimization_setting: OptimizationSetting,
        use_ga: bool,
        datasource: str = 'DataBase'
    ):
        """"""
        if use_ga:
            self.write_log("开始遗传算法参数优化")
        else:
            self.write_log("开始多进程参数优化")

        self.result_values = None

        engine = self.backtesting_engine
        engine.clear_data()

        engine.set_parameters(
            full_symbol=full_symbol,
            interval=interval,
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
                datasource=datasource
            )
        else:
            self.result_values = engine.run_optimization(
                optimization_setting,
                output=False,
                datasource=datasource
            )

        # Clear thread object handler.
        self.thread = None
        self.write_log("多进程参数优化完成")

        # Put optimization done event
        if self.event_engine:
            event = Event(type=EventType.OPTIMIZATION_FINISH)
            self.event_engine.put(event)

    def start_optimization(
        self,
        class_name: str,
        full_symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
        rate: float,
        slippage: float,
        size: int,
        pricetick: float,
        capital: int,
        optimization_setting: OptimizationSetting,
        use_ga: bool,
        datasource: str = 'DataBase'
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
                interval,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                optimization_setting,
                use_ga,
                datasource
            )
        )
        self.thread.start()

        return True


class BacktesterManager(QtWidgets.QWidget):
    """"""

    signal_log = QtCore.pyqtSignal(Event)
    signal_backtesting_finished = QtCore.pyqtSignal(Event)
    signal_optimization_finished = QtCore.pyqtSignal(Event)

    def __init__(self, event_engine: EventEngine):
        """"""
        super().__init__()

        self.event_engine = event_engine
        self.backtester_engine = Backtester(event_engine=self.event_engine)

        self.class_names = []
        self.settings = {}

        self.target_display = ""

        self.init_strategy_settings()
        self.init_ui()
        self.register_event()
        self.backtester_engine.init_engine()

    def init_strategy_settings(self):
        """"""
        self.class_names = self.backtester_engine.get_strategy_class_names()

        for class_name in self.class_names:
            setting = self.backtester_engine.get_default_setting(class_name)
            self.settings[class_name] = setting

    def init_ui(self):
        """"""
        self.setWindowTitle("CTA回测")

        # Setting Part
        self.class_combo = QtWidgets.QComboBox()
        self.class_combo.addItems(self.class_names)
        policy = self.class_combo.sizePolicy()
        policy.setHorizontalStretch(1)
        self.class_combo.setSizePolicy(policy)

        self.data_source = QtWidgets.QComboBox()
        self.data_source.addItems(['Memory', 'DataBase'])
        loaddatafile_btn = QtWidgets.QPushButton("内存数据情况")
        loaddatafile_btn.clicked.connect(self.load_data_file)

        cleardata_btn = QtWidgets.QPushButton("清空内存")
        cleardata_btn.clicked.connect(self.clear_data)

        self.symbol_line = QtWidgets.QLineEdit("SHFE F RB 1910")
        self.symbol_line.setMaximumWidth(160)
        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItem('tick')
        for inteval in Interval:
            self.interval_combo.addItem(inteval.value)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=1 * 365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(
                start_dt.year,
                start_dt.month,
                start_dt.day
            )
        )
        self.end_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate.currentDate()
        )

        self.rate_line = QtWidgets.QLineEdit("0.0002")
        self.slippage_line = QtWidgets.QLineEdit("0")
        self.size_line = QtWidgets.QLineEdit("10")
        self.pricetick_line = QtWidgets.QLineEdit("1")
        self.capital_line = QtWidgets.QLineEdit("1000000")
        # self.capital_line.setMaximumWidth(150)
        self.margin_line = QtWidgets.QLineEdit("0.1")

        reload_button = QtWidgets.QPushButton("重新加载")
        reload_button.clicked.connect(self.reload_strategy)

        backtesting_button = QtWidgets.QPushButton("开始回测")
        backtesting_button.clicked.connect(self.start_backtesting)

        datashow_button = QtWidgets.QPushButton("行情展示")
        datashow_button.clicked.connect(self.show_data)

        optimization_button = QtWidgets.QPushButton("参数优化")
        optimization_button.clicked.connect(self.start_optimization)

        self.result_button = QtWidgets.QPushButton("优化结果")
        self.result_button.clicked.connect(self.show_optimization_result)
        self.result_button.setEnabled(False)

        for button in [
            backtesting_button,
            optimization_button,
            datashow_button,
            self.result_button
        ]:
            button.setFixedHeight(button.sizeHint().height() * 2)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(QtWidgets.QLabel('交易策略'))
        hbox1.addWidget(self.class_combo)
        hbox1.addWidget(reload_button)

        hbox11 = QtWidgets.QHBoxLayout()
        hbox11.addWidget(QtWidgets.QLabel('数据来源'))
        hbox11.addWidget(self.data_source)
        hbox11.addWidget(loaddatafile_btn)
        hbox11.addWidget(cleardata_btn)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(QtWidgets.QLabel('合约全称'))
        hbox2.addWidget(self.symbol_line)
        hbox2.addWidget(QtWidgets.QLabel('时间尺度'))
        hbox2.addWidget(self.interval_combo)

        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(QtWidgets.QLabel('开始日期'))
        hbox3.addWidget(self.start_date_edit)
        hbox3.addWidget(QtWidgets.QLabel('结束日期'))
        hbox3.addWidget(self.end_date_edit)

        hbox4 = QtWidgets.QHBoxLayout()
        hbox4.addWidget(QtWidgets.QLabel('手续费率'))
        hbox4.addWidget(self.rate_line)
        hbox4.addWidget(QtWidgets.QLabel('交易滑点'))
        hbox4.addWidget(self.slippage_line)

        hbox5 = QtWidgets.QHBoxLayout()
        hbox5.addWidget(QtWidgets.QLabel('合约乘数'))
        hbox5.addWidget(self.size_line)
        hbox5.addWidget(QtWidgets.QLabel('价格跳动'))
        hbox5.addWidget(self.pricetick_line)

        hbox52 = QtWidgets.QHBoxLayout()
        hbox52.addWidget(QtWidgets.QLabel('保证金率'))
        hbox52.addWidget(self.margin_line)
        hbox52.addWidget(QtWidgets.QLabel('回测资金'))
        hbox52.addWidget(self.capital_line)

        hbox6 = QtWidgets.QHBoxLayout()
        hbox6.addWidget(backtesting_button)
        hbox6.addWidget(datashow_button)

        hbox7 = QtWidgets.QHBoxLayout()
        hbox7.addWidget(optimization_button)
        hbox7.addWidget(self.result_button)

        # Result part
        self.statistics_monitor = StatisticsMonitor()
        self.txnstatics_monitor = TxnStatisticsMonitor()

        hbox8 = QtWidgets.QHBoxLayout()
        hbox8.addWidget(self.statistics_monitor)
        hbox8.addWidget(self.txnstatics_monitor)

        self.log_monitor = QtWidgets.QTextEdit()
        policy = self.log_monitor.sizePolicy()
        policy.setVerticalStretch(1)
        self.log_monitor.setSizePolicy(policy)
        # self.log_monitor.setMaximumHeight(400)
        form = QtWidgets.QFormLayout()
        label1 = QtWidgets.QLabel('回测参数设置')
        label1.setAlignment(QtCore.Qt.AlignCenter)
        form.addWidget(label1)
        form.addRow(hbox1)
        form.addRow(hbox11)
        form.addRow(hbox2)
        form.addRow(hbox3)
        form.addRow(hbox4)
        form.addRow(hbox5)
        form.addRow(hbox52)
        form.addRow(hbox6)
        form.addRow(hbox7)
        label2 = QtWidgets.QLabel('回测结果总览')
        label2.setAlignment(QtCore.Qt.AlignCenter)
        form.addWidget(label2)
        form.addRow(hbox8)
        label3 = QtWidgets.QLabel('回测日志')
        label3.setAlignment(QtCore.Qt.AlignCenter)
        form.addWidget(label3)
        form.addRow(self.log_monitor)

        bt_setting = QtWidgets.QWidget()
        bt_setting.setLayout(form)
        bt_setting.setMinimumWidth(400)
        self.bt_setting = bt_setting

        self.overviewchart = BacktesterChart()
        self.overviewchart.setMinimumWidth(1000)
        self.overviewchart.setMinimumHeight(1200)

        self.scrolltop = QtWidgets.QScrollArea()
        self.scrolltop.setWidget(self.overviewchart)
        self.scrolltop.setWidgetResizable(True)

        # self.posviewchart = BtPosViewWidget()
        self.txnviewtable = TradesTable()
        self.txnviewtable.tradesig.connect(self.show_trade)
        self.dailytable = DailyTable()
        # TradesTable

        bt_topmiddle = QtWidgets.QTabWidget()
        # bt_topmiddle.setTabBar(VerticalTabBar(bt_topmiddle))
        bt_topmiddle.setTabPosition(QtWidgets.QTabWidget.West)
        bt_topmiddle.addTab(self.scrolltop, '盈亏情况')
        bt_topmiddle.addTab(self.txnviewtable, '成交明细')
        bt_topmiddle.addTab(self.dailytable, '每日明细')
        # bt_topmiddle.addTab(self.posviewchart, '持仓')
        self.bt_topmiddle = bt_topmiddle
    #  bottom middle:  data

        self.bt_bottommiddle = QtWidgets.QTabWidget()
        self.bt_bottommiddle.setTabsClosable(True)
        self.bt_bottommiddle.setMovable(True)

        self.bt_bottommiddle.tabCloseRequested.connect(
            self.bt_bottommiddle.removeTab)
        self.bt_bottommiddle.setTabPosition(QtWidgets.QTabWidget.West)
        # self.dataviewchart = BTQuotesChart()
        # self.bt_bottommiddle.addTab(self.dataviewchart, '历史行情')

    # --------------------------------

        bt_splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        bt_splitter1.addWidget(bt_topmiddle)
        bt_splitter1.addWidget(self.bt_bottommiddle)
        bt_splitter1.setSizes([500, 500])

        bt_splitter3 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        bt_splitter3.addWidget(bt_setting)
        bt_splitter3.addWidget(bt_splitter1)
        bt_splitter3.setSizes([300, 1200])

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(bt_splitter3)
        self.setLayout(hbox)

    def register_event(self):
        """"""
        self.signal_log.connect(self.process_log_event)
        self.signal_backtesting_finished.connect(
            self.process_backtesting_finished_event)
        self.signal_optimization_finished.connect(
            self.process_optimization_finished_event)

        self.event_engine.register(
            EventType.BACKTEST_LOG, self.signal_log.emit)
        self.event_engine.register(
            EventType.OPTIMIZATION_FINISH, self.signal_optimization_finished.emit)
        self.event_engine.register(
            EventType.BACKTEST_FINISH, self.signal_backtesting_finished.emit)

    def process_log_event(self, event: Event):
        """"""
        msg = event.data
        self.write_log(msg)

    def write_log(self, msg):
        """"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp}\t{msg}"
        self.log_monitor.append(msg)

    def process_backtesting_finished_event(self, event: Event):
        """"""
        statistics = self.backtester_engine.get_result_statistics()
        self.statistics_monitor.set_data(statistics)
        self.txnstatics_monitor.set_data(statistics)

        df = self.backtester_engine.get_result_df()
        self.overviewchart.set_data(df)
        trades = self.backtester_engine.get_result_trades()
        self.txnviewtable.set_data(trades)
        dailyresults = self.backtester_engine.get_result_daily()
        self.dailytable.set_data(dailyresults)

    def process_optimization_finished_event(self, event: Event):
        """"""
        self.write_log("请点击[优化结果]按钮查看")
        self.result_button.setEnabled(True)

    def clear_data(self):
        full_sym = self.symbol_line.text()
        if self.interval_combo.currentText() == 'tick':
            msg = f"will clear Tick data {full_sym} , continue?"
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', msg,
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return
            sqglobal.history_tick[full_sym].clear()
        elif self.interval_combo.currentText() == '1m':
            msg = f"will clear Bar(1m) data {full_sym} , continue?"
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', msg,
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return
            sqglobal.history_bar[full_sym].clear()

    def load_data_file(self):
        if not self.data_source.currentText() == 'Memory':
            return

        full_sym = self.symbol_line.text()
        if self.interval_combo.currentText() == 'tick':
            if sqglobal.history_tick[full_sym]:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'already has data in memory!', QtWidgets.QMessageBox.Ok)
                return
            QtWidgets.QMessageBox().information(None, 'Info',
                                                'Please load data to from Tools/Data loader!', QtWidgets.QMessageBox.Ok)
            return
        elif self.interval_combo.currentText() == '1m':
            if sqglobal.history_bar[full_sym]:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'already has data in memory!', QtWidgets.QMessageBox.Ok)
                return
            QtWidgets.QMessageBox().information(None, 'Info',
                                                'Please load data to from Tools/Data loader!', QtWidgets.QMessageBox.Ok)
            return
        QtWidgets.QMessageBox().information(
            None, 'Info', 'not implemented yet!', QtWidgets.QMessageBox.Ok)

    def reload_strategy(self):
        self.class_names.clear()
        self.settings.clear()
        self.backtester_engine.reload_strategy()
        self.init_strategy_settings()
        self.class_combo.clear()
        self.class_combo.addItems(self.class_names)

    def start_backtesting(self):
        """"""
        class_name = self.class_combo.currentText()
        full_symbol = self.symbol_line.text()
        interval = self.interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        rate = float(self.rate_line.text())
        slippage = float(self.slippage_line.text())
        size = float(self.size_line.text())
        pricetick = float(self.pricetick_line.text())
        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()

        if end <= start:
            QtWidgets.QMessageBox().information(None, 'Error',
                                                'End date should later than start date!', QtWidgets.QMessageBox.Ok)
            return
        if (end - start) > timedelta(days=90) and interval == 'tick':
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return

        old_setting = self.settings[class_name]
        dialog = BacktestingSettingEditor(class_name, old_setting)
        i = dialog.exec()
        if i != dialog.Accepted:
            return

        new_setting = dialog.get_setting()
        self.settings[class_name] = new_setting

        result = self.backtester_engine.start_backtesting(
            class_name,
            full_symbol,
            interval,
            start,
            end,
            rate,
            slippage,
            size,
            pricetick,
            capital,
            new_setting,
            datasource
        )

        if result:
            self.statistics_monitor.clear_data()
            self.txnstatics_monitor.clear_data()
            self.overviewchart.clear_data()

    def start_optimization(self):
        """"""
        class_name = self.class_combo.currentText()
        full_symbol = self.symbol_line.text()
        interval = self.interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        rate = float(self.rate_line.text())
        slippage = float(self.slippage_line.text())
        size = float(self.size_line.text())
        pricetick = float(self.pricetick_line.text())
        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()

        if (end - start) > timedelta(days=90) and interval == 'tick':
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return

        parameters = self.settings[class_name]
        dialog = OptimizationSettingEditor(class_name, parameters)
        i = dialog.exec()
        if i != dialog.Accepted:
            return

        optimization_setting, use_ga = dialog.get_setting()
        self.target_display = dialog.target_display

        self.backtester_engine.start_optimization(
            class_name,
            full_symbol,
            interval,
            start,
            end,
            rate,
            slippage,
            size,
            pricetick,
            capital,
            optimization_setting,
            use_ga,
            datasource
        )

        self.result_button.setEnabled(False)

    def show_optimization_result(self):
        """"""
        result_values = self.backtester_engine.get_result_values()

        dialog = OptimizationResultMonitor(
            result_values,
            self.target_display
        )
        dialog.exec_()

    def show_data(self):

        full_symbol = self.symbol_line.text()
        interval = self.interval_combo.currentText()
        datasource = self.data_source.currentText()

        if interval == 'tick':
            interval = '1m'
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        trades = self.backtester_engine.get_result_trades()
        addtrade = bool(trades) and full_symbol == trades[0].full_symbol
        if (end - start) > timedelta(days=60) and interval == '1m':
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return
        for i in range(self.bt_bottommiddle.count()):
            if self.bt_bottommiddle.tabText(i) == full_symbol:
                widget = self.bt_bottommiddle.widget(i)
                widget.reset(full_symbol, start, end,
                             Interval(interval), datasource)
                if addtrade:
                    widget.add_trades(trades)
                    widget.show_text_signals()
                return
        dataviewchart = BTQuotesChart()
        dataviewchart.reset(full_symbol, start, end,
                            Interval(interval), datasource)
        if addtrade:
            dataviewchart.add_trades(trades)
            dataviewchart.show_text_signals()
        self.bt_bottommiddle.addTab(dataviewchart, full_symbol)

    def show_trade(self, trade):
        full_symbol = trade.full_symbol
        tradetime = trade.datetime

        adddaysstart = 2
        if tradetime.date().weekday() == 0:
            adddaysstart = 4
        elif tradetime.date().weekday() == 1:
            adddaysstart = 3
        start = tradetime - timedelta(days=adddaysstart)

        adddaysend = 1
        if tradetime.date().weekday() == 4:
            adddaysend = 3
        end = tradetime + timedelta(days=adddaysend)

        datasource = self.data_source.currentText()
        trades = self.backtester_engine.get_result_trades()
        for i in range(self.bt_bottommiddle.count()):
            if self.bt_bottommiddle.tabText(i) == full_symbol:
                widget = self.bt_bottommiddle.widget(i)
                widget.reset(full_symbol, start.date(),
                             end.date(), Interval.MINUTE, datasource)
                widget.add_trades(trades)
                widget.show_text_signals()
                return
        dataviewchart = BTQuotesChart()
        dataviewchart.reset(full_symbol, start.date(),
                            end.date(), Interval.MINUTE, datasource)
        dataviewchart.add_trades(trades)
        dataviewchart.show_text_signals()
        self.bt_bottommiddle.addTab(dataviewchart, full_symbol)

    def show(self):
        """"""
        self.showMaximized()


class BacktestingSettingEditor(QtWidgets.QDialog):
    """
    For creating new strategy and editing strategy parameters.
    """

    def __init__(
        self, class_name: str, parameters: dict
    ):
        """"""
        super(BacktestingSettingEditor, self).__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle(f"策略参数配置：{self.class_name}")
        button_text = "确定"
        parameters = self.parameters

        for name, value in parameters.items():
            type_ = type(value)

            edit = QtWidgets.QLineEdit(str(value))
            if type_ is int:
                validator = QtGui.QIntValidator()
                edit.setValidator(validator)
            elif type_ is float:
                validator = QtGui.QDoubleValidator()
                edit.setValidator(validator)

            form.addRow(f"{name} {type_}", edit)

            self.edits[name] = (edit, type_)

        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        form.addRow(button)

        self.setLayout(form)

    def get_setting(self):
        """"""
        setting = {}

        for name, tp in self.edits.items():
            edit, type_ = tp
            value_text = edit.text()

            if type_ == bool:
                if value_text == "True":
                    value = True
                else:
                    value = False
            else:
                value = type_(value_text)

            setting[name] = value

        return setting


class OptimizationSettingEditor(QtWidgets.QDialog):
    """
    For setting up parameters for optimization.
    """
    DISPLAY_NAME_MAP = {
        "总收益率": "total_return",
        "夏普比率": "sharpe_ratio",
        "收益回撤比": "return_drawdown_ratio",
        "日均盈亏": "daily_net_pnl"
    }

    def __init__(
        self, class_name: str, parameters: dict
    ):
        """"""
        super().__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.optimization_setting = None
        self.use_ga = False

        self.init_ui()

    def init_ui(self):
        """"""
        QLabel = QtWidgets.QLabel

        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItems(list(self.DISPLAY_NAME_MAP.keys()))

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QLabel("目标"), 0, 0)
        grid.addWidget(self.target_combo, 0, 1, 1, 3)
        grid.addWidget(QLabel("参数"), 1, 0)
        grid.addWidget(QLabel("开始"), 1, 1)
        grid.addWidget(QLabel("步进"), 1, 2)
        grid.addWidget(QLabel("结束"), 1, 3)

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle(f"优化参数配置：{self.class_name}")

        validator = QtGui.QDoubleValidator()
        row = 2

        for name, value in self.parameters.items():
            type_ = type(value)
            if type_ not in [int, float]:
                continue

            start_edit = QtWidgets.QLineEdit(str(value))
            step_edit = QtWidgets.QLineEdit(str(1))
            end_edit = QtWidgets.QLineEdit(str(value))

            for edit in [start_edit, step_edit, end_edit]:
                edit.setValidator(validator)

            grid.addWidget(QLabel(name), row, 0)
            grid.addWidget(start_edit, row, 1)
            grid.addWidget(step_edit, row, 2)
            grid.addWidget(end_edit, row, 3)

            self.edits[name] = {
                "type": type_,
                "start": start_edit,
                "step": step_edit,
                "end": end_edit
            }

            row += 1

        parallel_button = QtWidgets.QPushButton("多进程优化")
        parallel_button.clicked.connect(self.generate_parallel_setting)
        grid.addWidget(parallel_button, row, 0, 1, 4)

        row += 1
        ga_button = QtWidgets.QPushButton("遗传算法优化")
        ga_button.clicked.connect(self.generate_ga_setting)
        grid.addWidget(ga_button, row, 0, 1, 4)

        self.setLayout(grid)

    def generate_ga_setting(self):
        """"""
        self.use_ga = True
        self.generate_setting()

    def generate_parallel_setting(self):
        """"""
        self.use_ga = False
        self.generate_setting()

    def generate_setting(self):
        """"""
        self.optimization_setting = OptimizationSetting()

        self.target_display = self.target_combo.currentText()
        target_name = self.DISPLAY_NAME_MAP[self.target_display]
        self.optimization_setting.set_target(target_name)

        for name, d in self.edits.items():
            type_ = d["type"]
            start_value = type_(d["start"].text())
            step_value = type_(d["step"].text())
            end_value = type_(d["end"].text())

            if start_value == end_value:
                self.optimization_setting.add_parameter(name, start_value)
            else:
                self.optimization_setting.add_parameter(
                    name,
                    start_value,
                    end_value,
                    step_value
                )

        self.accept()

    def get_setting(self):
        """"""
        return self.optimization_setting, self.use_ga


class OptimizationResultMonitor(QtWidgets.QDialog):
    """
    For viewing optimization result.
    """

    def __init__(
        self, result_values: list, target_display: str
    ):
        """"""
        super().__init__()

        self.result_values = result_values
        self.target_display = target_display

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("参数优化结果")
        self.resize(1100, 500)

        table = QtWidgets.QTableWidget()

        table.setColumnCount(2)
        table.setRowCount(len(self.result_values))
        table.setHorizontalHeaderLabels(["参数", self.target_display])
        table.setEditTriggers(table.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )

        for n, tp in enumerate(self.result_values):
            setting, target_value, _ = tp
            setting_cell = QtWidgets.QTableWidgetItem(str(setting))
            target_cell = QtWidgets.QTableWidgetItem(str(target_value))

            setting_cell.setTextAlignment(QtCore.Qt.AlignCenter)
            target_cell.setTextAlignment(QtCore.Qt.AlignCenter)

            table.setItem(n, 0, setting_cell)
            table.setItem(n, 1, target_cell)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(table)

        self.setLayout(vbox)


class StatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "capital": "起始资金",
        "end_balance": "结束资金",

        "total_net_pnl": "总盈亏",
        "total_return": "总收益率",
        "annual_return": "年化收益",
        "daily_net_pnl": "日均盈亏",
        "daily_return": "日均收益率",

        "max_drawdown": "最大回撤",
        "max_ddpercent": "百分比最大回撤",

        "return_std": "收益标准差",
        "sharpe_ratio": "夏普比率",
        "return_drawdown_ratio": "收益回撤比",
        "win_ratio": "胜率",
        "win_loss": "盈亏比"
    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setRowCount(len(self.KEY_NAME_MAP))
        self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        self.setColumnCount(1)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)

        for row, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            self.setItem(row, 0, cell)
            self.cells[key] = cell
        self.setMinimumHeight(450)
        # self.setFixedWidth(200)

    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):
        """"""
        data["capital"] = f"{data['capital']:,.2f}"
        data["end_balance"] = f"{data['end_balance']:,.2f}"
        data["total_return"] = f"{data['total_return']:,.2f}%"
        data["annual_return"] = f"{data['annual_return']:,.2f}%"
        data["max_drawdown"] = f"{data['max_drawdown']:,.2f}"
        data["max_ddpercent"] = f"{data['max_ddpercent']:,.2f}%"
        data["total_net_pnl"] = f"{data['total_net_pnl']:,.2f}"

        data["daily_net_pnl"] = f"{data['daily_net_pnl']:,.2f}"
        data["daily_return"] = f"{data['daily_return']:,.2f}%"
        data["return_std"] = f"{data['return_std']:,.2f}%"
        data["sharpe_ratio"] = f"{data['sharpe_ratio']:,.2f}"
        data["return_drawdown_ratio"] = f"{data['return_drawdown_ratio']:,.2f}"
        data["win_ratio"] = f"{data['win_ratio']:,.2f}"
        data["win_loss"] = f"{data['win_loss']:,.2f}"
        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))


class TxnStatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "start_date": "首个交易日",
        "end_date": "最后交易日",

        "total_days": "总交易日数",
        "profit_days": "盈利交易日数",
        "loss_days": "亏损交易日数",


        "total_commission": "总手续费",
        "total_slippage": "总滑点",
        "total_turnover": "总成交额",
        "total_trade_count": "总成交笔数",

        "daily_commission": "日均手续费",
        "daily_slippage": "日均滑点",
        "daily_turnover": "日均成交额",
        "daily_trade_count": "日均成交笔数",
    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setRowCount(len(self.KEY_NAME_MAP))
        self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        self.setColumnCount(1)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)

        for row, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            self.setItem(row, 0, cell)
            self.cells[key] = cell
        self.setMinimumHeight(450)
        # self.setFixedWidth(200)

    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):
        """"""

        data["total_commission"] = f"{data['total_commission']:,.2f}"
        data["total_slippage"] = f"{data['total_slippage']:,.2f}"
        data["total_turnover"] = f"{data['total_turnover']:,.2f}"
        data["daily_commission"] = f"{data['daily_commission']:,.2f}"
        data["daily_slippage"] = f"{data['daily_slippage']:,.2f}"
        data["daily_turnover"] = f"{data['daily_turnover']:,.2f}"
        data["daily_trade_count"] = f"{data['daily_trade_count']:,.2f}"

        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))
