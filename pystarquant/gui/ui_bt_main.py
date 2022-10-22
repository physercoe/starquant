#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import gzip
import csv
from datetime import datetime, timedelta

from PyQt5 import QtCore, QtWidgets
# import pyqtgraph.console

from pystarquant.common.constant import CPU_NUMS,Interval, EventType,Direction,Offset
from pystarquant.common.datastruct import Event,BacktestTradeData
from pystarquant.engine.iengine import EventEngine

from pystarquant.engine.bactester import Backtester
from pystarquant.strategy.strategy_base import StrategyBase

from pystarquant.gui.ui_common import (
    FileTreeWidget,
    TextEditWidget,
    # WebWindow
)
from pystarquant.gui.ui_worker import (
    CsvLoaderWidget,
    DataDownloaderWidget,
)


from pystarquant.gui.ui_bt_setting import (
    BtContractManager,
    BacktestingSettingEditorWidget,
    OptimizationSettingEditorWidget,
    BacktestingDataViewSettingEditorWidget,
    BatchSettingTable
)
from pystarquant.gui.ui_bt_results import (
    BacktesterChart,
    TradesTable,
    DailyTable,
    OptimizationResultMonitorWidget,
    StatisticsMonitor,
    RiskStatisticsMonitor,
    TxnStatisticsMonitor,
    RatioStatisticsMonitor,

)
from pystarquant.gui.ui_bt_dataview import BTQuotesChart
import pystarquant.common.sqglobal as SQGlobal


CtaTemplate = StrategyBase

sys.path.insert(0, "../..")

class BacktesterManager(QtWidgets.QWidget):
    """"""

    signal_log = QtCore.pyqtSignal(Event)
    signal_backtesting_finished = QtCore.pyqtSignal(Event)
    signal_optimization_finished = QtCore.pyqtSignal(Event)
    signal_ana_finished = QtCore.pyqtSignal(Event)
    signal_corr_finished = QtCore.pyqtSignal(Event)
    signal_vecbt_finished = QtCore.pyqtSignal(Event)
    signal_vecroll_finished = QtCore.pyqtSignal(Event)

    def __init__(self, event_engine: EventEngine):
        """"""
        super().__init__()

        self.event_engine = event_engine
        self.backtester_engine = Backtester(event_engine=self.event_engine)

        self.bt_contract_manager = BtContractManager()

        self.class_names = []
        self.settings = {}

        self.target_display = ""
        self.use_roll = False

        self.init_ui()
        self.register_event()
        self.backtester_engine.init_engine()
        self.load_strategy()

    def load_strategy(self,reload: bool = False):

        """"""
        if reload:
            SQGlobal.strategyloader.load_class(True)

        self.backtester_engine.load_strategy()

        self.classes =  SQGlobal.strategyloader.classes
        self.settings = SQGlobal.strategyloader.settings

        self.class_names = list(self.classes.keys())
        self.class_combo.clear()
        self.class_combo.addItems(self.class_names)

        cn = self.class_combo.currentText()
        cs = self.settings.get(cn,{})
        self.strategysetting.set_paras(cn,cs)
        self.optisetting.set_paras(cn,cs)


    def change_strategy_setting(self,cn):
        cs = self.settings.get(cn,{})
        self.strategysetting.set_paras(cn,cs)
        self.optisetting.set_paras(cn,cs)

    def init_ui(self):
        """"""
        self.setWindowTitle("回测引擎")

        # Setting Part
        self.class_combo = QtWidgets.QComboBox()
        self.class_combo.currentTextChanged.connect(self.change_strategy_setting)

        policy = self.class_combo.sizePolicy()
        policy.setHorizontalStretch(1)
        self.class_combo.setSizePolicy(policy)

        self.data_source = QtWidgets.QComboBox()
        self.data_source.addItems(['DataBase','Memory'])
        self.dbusingcursor = QtWidgets.QCheckBox()
        self.dbusingcursor.setChecked(True)
        self.dbusingcursor.setToolTip("数据库是否采用游标回放数据")
        loaddatafile_btn = QtWidgets.QPushButton("内存数据情况")
        loaddatafile_btn.clicked.connect(self.load_data_file)

        cleardata_btn = QtWidgets.QPushButton("清空内存")
        cleardata_btn.clicked.connect(self.clear_data)

        self.db_collection_edit = QtWidgets.QLineEdit('db_bar_data') # 表名
        self.db_type_combo = QtWidgets.QComboBox()    # 字段类型
        self.db_type_combo.addItems(['Bar','Tick','TbtBar'])
        self.db_interval_combo =  QtWidgets.QComboBox()  #字段参数
        for interval in Interval:
            self.db_interval_combo.addItem(interval.value)

        self.btmode = QtWidgets.QComboBox()
        self.btmode.addItems(['lite', 'pro'])
        self.contract_widget = QtWidgets.QStackedWidget()
        litebtwidget =  QtWidgets.QFrame()
        liteform = QtWidgets.QFormLayout()
        probtwidget = QtWidgets.QFrame()
        proform = QtWidgets.QFormLayout()

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=1 * 365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(
                start_dt.year,
                start_dt.month,
                start_dt.day
            )
        )
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate.currentDate()
        )
        self.end_date_edit.setCalendarPopup(True)


        self.symbol_line = QtWidgets.QLineEdit("SHFE F RB 88")
        self.symbol_line.setFixedWidth(160)
        self.symbol_line_pro = QtWidgets.QLineEdit("SZSE T Any 00")

        self.rate_line = QtWidgets.QLineEdit("0.0002")
        self.slippage_line = QtWidgets.QLineEdit("0")
        self.size_line = QtWidgets.QLineEdit("10")
        self.pricetick_line = QtWidgets.QLineEdit("1")
        self.capital_line = QtWidgets.QLineEdit("10000")
        # self.capital_line.setMaximumWidth(150)
        self.margin_line = QtWidgets.QLineEdit("0.1")

        reload_button = QtWidgets.QPushButton("重新加载")
        reload_button.clicked.connect(lambda:self.load_strategy(True))

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(QtWidgets.QLabel('交易策略'))
        hbox1.addWidget(self.class_combo)
        hbox1.addWidget(reload_button)

        hbox11 = QtWidgets.QHBoxLayout()
        hbox11.addWidget(QtWidgets.QLabel('数据来源'))
        hbox11.addWidget(self.data_source)
        hbox11.addWidget(QtWidgets.QLabel('游标'))
        hbox11.addWidget(self.dbusingcursor)
        hbox11.addWidget(loaddatafile_btn)
        hbox11.addWidget(cleardata_btn)

        hbox12 = QtWidgets.QHBoxLayout()
        hbox12.addWidget(QtWidgets.QLabel('DB表名') )
        hbox12.addWidget(self.db_collection_edit)
        hbox12.addWidget(QtWidgets.QLabel('字段类型'))
        hbox12.addWidget(self.db_type_combo)




        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(QtWidgets.QLabel('回测模式'))
        hbox2.addWidget(self.btmode)
        hbox2.addWidget(QtWidgets.QLabel('时间尺度'))
        hbox2.addWidget(self.db_interval_combo)
        hbox2.addWidget(QtWidgets.QLabel('资金'))
        hbox2.addWidget(self.capital_line)

        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(QtWidgets.QLabel('开始日期'))
        hbox3.addWidget(self.start_date_edit)
        hbox3.addWidget(QtWidgets.QLabel('结束日期'))
        hbox3.addWidget(self.end_date_edit)



        self.batchmode = QtWidgets.QCheckBox("批量回测")
        self.btcpus = QtWidgets.QSpinBox()
        self.btcpus.setFixedWidth(45)
        self.btcpus.setToolTip('cpu数目')
        self.btcpus.setSingleStep(1)
        self.btcpus.setRange(1, CPU_NUMS)
        self.btcpus.setValue(CPU_NUMS)
        self.batchadd = QtWidgets.QPushButton("添加")
        self.batchedit = QtWidgets.QPushButton("查看/编辑")
        self.batchtable = BatchSettingTable()
        self.batchadd.clicked.connect(self.batchaddsetting)
        self.batchedit.clicked.connect(self.batchtable.show)


        hbox52 = QtWidgets.QHBoxLayout()
        hbox52.addWidget(QtWidgets.QLabel('合约全称'))
        hbox52.addWidget(self.symbol_line)
        hbox52.addWidget(QtWidgets.QLabel('保证金率'))
        hbox52.addWidget(self.margin_line)

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

        hbox31 = QtWidgets.QHBoxLayout()
        hbox31.addWidget(self.batchmode)
        hbox31.addWidget(self.btcpus)
        hbox31.addWidget(self.batchadd)
        hbox31.addWidget(self.batchedit)

        liteform.addRow(hbox52)
        liteform.addRow(hbox4)
        liteform.addRow(hbox5)
        # liteform.addRow(hbox31)
        litebtwidget.setLayout(liteform)
        litebtwidget.setContentsMargins(0, 0, 0, 0)
        self.contract_widget.addWidget(litebtwidget)
        
        editcontract_btn = QtWidgets.QPushButton("回测合约参数设置")
        editcontract_btn.clicked.connect(self.bt_contract_manager.show)
        self.num_combination = QtWidgets.QSpinBox()
        self.num_combination.setFixedWidth(45)
        self.num_combination.setToolTip('组合分析数目')
        self.num_combination.setSingleStep(1)
        self.num_combination.setRange(1, 4)
        self.num_combination.setValue(2)

        proform.addRow('回测数据名称', self.symbol_line_pro)
        proform.addRow(editcontract_btn)

        probtwidget.setLayout(proform)
        probtwidget.setContentsMargins(0, 0, 0, 0)        
        self.contract_widget.addWidget(probtwidget)

        self.contract_widget.setCurrentIndex(0)
        self.btmode.currentIndexChanged.connect(self.set_btwidget)


        self.settingwidget = QtWidgets.QTabWidget()

        self.strategysetting = BacktestingSettingEditorWidget()
        self.strategysetting.startbutton.clicked.connect(self.start_backtesting)
        self.strategysetting.savebtn.clicked.connect(self.save_btsetting)
        self.strategysetting.load_button.clicked.connect(self.load_result)

        self.optisetting = OptimizationSettingEditorWidget()
        self.optisetting.opt_mode.connect(self.start_optimization)


        self.dataview = BacktestingDataViewSettingEditorWidget()
        self.dataview.showdatabtn.clicked.connect(self.show_data)
        self.dataview.sig_indicator.connect(self.show_indicator)
        self.fileview = FileTreeWidget()
        # syncronize
        self.symbol_line.textChanged.connect(self.dataview.symbol_line.setText)
        self.data_source.currentIndexChanged.connect(self.dataview.data_source.setCurrentIndex)
        self.db_interval_combo.currentIndexChanged.connect(self.dataview.db_interval_combo.setCurrentIndex)
        self.db_type_combo.currentIndexChanged.connect(self.dataview.db_type_combo.setCurrentIndex)
        self.db_collection_edit.textChanged.connect(self.dataview.db_collection_edit.setText)


        self.settingwidget.addTab(self.strategysetting,'策略设置')
        self.settingwidget.addTab(self.optisetting,'参数优化')
        self.settingwidget.addTab(self.dataview,'行情展示')
        self.settingwidget.addTab(CsvLoaderWidget(self.event_engine),'数据导入')
        self.settingwidget.addTab(DataDownloaderWidget(),'数据下载')
        self.settingwidget.addTab(self.fileview,'文件编辑')

        scrollsetting = QtWidgets.QScrollArea()
        scrollsetting.setWidget(self.settingwidget)
        scrollsetting.setWidgetResizable(True)




        # Result part
        self.riskstatics_monitor = RiskStatisticsMonitor()
        self.statistics_monitor = StatisticsMonitor()
        self.txnstatics_monitor = TxnStatisticsMonitor()
        self.ratiostatics_monitor = RatioStatisticsMonitor()


        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setFontPointSize(12)
        policy = self.log_monitor.sizePolicy()
        policy.setVerticalStretch(1)
        self.log_monitor.setSizePolicy(policy)


    #左侧总布局:回测参数设置，回测结果总览，回测日志

        form = QtWidgets.QFormLayout()

        form.addRow(hbox1)
        form.addRow(hbox11)
        form.addRow(hbox12)
        form.addRow(hbox3)
        form.addRow(hbox2)
        form.addRow(hbox31)
        form.addWidget(self.contract_widget)

        bt_setting = QtWidgets.QWidget()
        bt_setting.setLayout(form)
        bt_setting.setMinimumWidth(400)
        self.bt_setting = bt_setting

    # --------------------bt results charts, tables-----------------------------
        self.overviewchart = BacktesterChart()
        self.overviewchart.setMinimumWidth(900)
        self.overviewchart.setMinimumHeight(1600)

        self.scrolltop = QtWidgets.QScrollArea()
        self.scrolltop.setWidget(self.overviewchart)
        self.scrolltop.setWidgetResizable(True)


        
        # self.posviewchart = BtPosViewWidget()
        self.txnviewtable = TradesTable()
        self.txnviewtable.tradesig.connect(self.show_trade)
        self.dailytable = DailyTable()



 


        bt_overview = QtWidgets.QWidget()
        vbox8 = QtWidgets.QVBoxLayout()
        vbox8.addWidget(QtWidgets.QLabel('收益情况'))
        vbox8.addWidget(self.statistics_monitor)
        vbox8.addWidget(QtWidgets.QLabel('风险回撤'))
        vbox8.addWidget(self.riskstatics_monitor)
        vbox8.addWidget(QtWidgets.QLabel('交易统计'))
        vbox8.addWidget(self.txnstatics_monitor)
        vbox8.addWidget(QtWidgets.QLabel('盈亏比例'))
        vbox8.addWidget(self.ratiostatics_monitor)
        vbox8.addStretch()
        bt_overview.setLayout(vbox8)

        scrolloverview = QtWidgets.QScrollArea()
        scrolloverview.setWidget(bt_overview)
        scrolloverview.setWidgetResizable(True)        

        bt_results = QtWidgets.QTabWidget()
        # bt_results.setTabPosition(QtWidgets.QTabWidget.West)
        bt_results.addTab(self.log_monitor, '系统日志')
        bt_results.addTab(scrolloverview, '指标总览')
        bt_results.addTab(self.scrolltop, '事件驱动盈亏曲线')
        # bt_results.addTab(self.txnviewtable, '成交明细')
        # bt_results.addTab(self.dailytable, '每日明细')

        
        self.bt_results = bt_results

    #  ------------bt data view widgets---------------

        self.bt_dataviews = QtWidgets.QTabWidget()
        self.bt_dataviews.setTabsClosable(True)
        self.bt_dataviews.setMovable(True)

        self.bt_dataviews.tabCloseRequested.connect(
            self.bt_dataviews.removeTab)
        self.bt_dataviews.setTabPosition(QtWidgets.QTabWidget.West)


    # -----------------optimazation results----------------------------------

        self.bt_opt = QtWidgets.QTabWidget()
        self.grid_opt = OptimizationResultMonitorWidget()


        self.bt_opt.addTab(self.txnviewtable, '成交明细')
        self.bt_opt.addTab(self.dailytable, '每日明细')
        self.bt_opt.addTab(self.grid_opt,'网格寻参结果')



    # ----------------- tools--------------------------------


        self.fileeditor = TextEditWidget() 

        self.bt_opt.addTab(self.fileeditor,'Editor')
        # self.bt_tools.addTab(EmbTerminal(),'Terminal')

    # --------------------------------layout--------------------

        bt_splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        bt_splitter1.addWidget(self.bt_setting)
        bt_splitter1.addWidget(scrollsetting)
        bt_splitter1.setSizes([500, 500])

        bt_splitter2 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        bt_splitter2.addWidget(self.bt_results)
        bt_splitter2.addWidget(self.bt_dataviews)
        bt_splitter2.setSizes([400, 800])

        # bt_splitter3 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        # bt_splitter3.addWidget(self.bt_opt)
        # bt_splitter3.addWidget(self.bt_tools)
        # bt_splitter3.setSizes([500, 500])


        bt_splitter4 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        bt_splitter4.addWidget(bt_splitter1)
        bt_splitter4.addWidget(bt_splitter2)
        # bt_splitter4.addWidget(bt_splitter3)
        bt_splitter4.addWidget(self.bt_opt)        
        bt_splitter4.setSizes([300, 1100,500])

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(bt_splitter4)
        self.setLayout(hbox)


    def set_btwidget(self, index):
        if self.btmode.currentText() == 'lite':
            self.contract_widget.setCurrentIndex(0)
        else:
            self.contract_widget.setCurrentIndex(1)

    def register_event(self):
        """"""
        SQGlobal.strategyloader.write_log = self.write_log
        SQGlobal.factorloader.write_log = self.write_log
        SQGlobal.indicatorloader.write_log = self.write_log
        SQGlobal.modelloader.write_log = self.write_log


        self.signal_log.connect(self.process_log_event)
        self.signal_backtesting_finished.connect(
            self.process_backtesting_finished_event)
        self.signal_optimization_finished.connect(
            self.process_optimization_finished_event)

        self.signal_ana_finished.connect(self.process_analysis_finished_event)
        self.signal_corr_finished.connect(self.process_corr_finished_event)
        self.signal_vecbt_finished.connect(self.process_vecbt_finished_event)
        self.signal_vecroll_finished.connect(self.process_vecroll_finished_event)

        #  !!!!!!  only signal can be  used by other thread, eg event_engine

        self.event_engine.register(
            EventType.BACKTEST_LOG, self.signal_log.emit)
        self.event_engine.register(
            EventType.DATALOAD_LOG, self.signal_log.emit)
        self.event_engine.register(
            EventType.ANALYSIS_LOG, self.signal_log.emit)

        self.event_engine.register(
            EventType.OPTIMIZATION_FINISH, self.signal_optimization_finished.emit)
        self.event_engine.register(
            EventType.BACKTEST_FINISH, self.signal_backtesting_finished.emit)
        
        self.event_engine.register(
            EventType.ANALYSIS_FINISH, self.signal_ana_finished.emit)

        self.event_engine.register(
            EventType.ANALYSIS_CORRFINISH, self.signal_corr_finished.emit)

        self.event_engine.register(
            EventType.VECTORBT_FINISH, self.signal_vecbt_finished.emit)
        self.event_engine.register(
            EventType.VECTORBT_ROLLFINISH, self.signal_vecroll_finished.emit)


        # internal signals,TODO:move all internal signals here
        self.fileview.signal_filepath.connect(self.fileeditor.open_file)

       

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
        self.write_log("回测结束")
        statistics = self.backtester_engine.get_result_statistics()
        self.riskstatics_monitor.set_data(statistics)
        self.statistics_monitor.set_data(statistics)
        self.txnstatics_monitor.set_data(statistics)
        self.ratiostatics_monitor.set_data(statistics)

        df = self.backtester_engine.get_result_df()
        self.overviewchart.set_data(df)
        trades = self.backtester_engine.get_result_trades()
        self.txnviewtable.set_data(trades)
        self.overviewchart.set_trade(trades)
        dailyresults = self.backtester_engine.get_result_daily()
        self.dailytable.set_data(dailyresults)

        self.bt_results.setCurrentWidget(self.scrolltop)


        engine = self.backtester_engine.virtualengine
        engine.clear_data()
        engine.clear_batch_data()
        engine.tbtmode = False

    def process_optimization_finished_event(self, event: Event):
        """"""
        self.write_log("优化结束")
        self.show_optimization_result()

        # self.result_button.setEnabled(True)

    def process_analysis_finished_event(self, event: Event):
        self.write_log("因子统计分析结束")



    def process_corr_finished_event(self,event: Event):
        self.write_log("因子相关分析结束")

    def process_vecbt_finished_event(self,event: Event):
        self.write_log("向量回测结束")


    def process_vecroll_finished_event(self,event: Event):
        self.write_log("向量滚动回测结束")

    def show_vecbt_graph(self,index):
        pass

    def show_vecroll_graph(self):
        pass

    def load_result(self):
        self.strategysetting.load_setting()
        file_path = self.strategysetting.file_name
        loadmode = self.strategysetting.mode
        if not file_path:
            return
        suffix = file_path.split('.')[-1]
        trades = []
        if suffix == 'csv':
            with open(file_path, "rt") as f:
                trades = self.load_result_handle(f)
        elif suffix == 'csv.gz':
            with gzip.open(file_path, 'rt') as f:
                trades = self.load_result_handle(f)
        if not trades:
            return

        capital = float(self.capital_line.text())
        contracts = self.bt_contract_manager.contracts

        engine = self.backtester_engine.virtualengine
        # TODO: 区分显示的曲线对应的交易数据，只在最新曲线对应的成交数据上叠加新的成交，方法是回测完清空virtual engine
        if loadmode == 'new':
            engine.clear_data()
            engine.clear_batch_data()
            engine.tbtmode = False
            enginelite = self.backtester_engine.backtesting_engine
            enginelite.clear_data()
            enginepro = self.backtester_engine.backtestingpro_engine
            enginepro.clear_data()
        elif loadmode == 'append' and not engine.tbtmode:  # only append once
            engine.tbtmode = True
            if self.btmode.currentText() == 'lite':
                enginelite = self.backtester_engine.backtesting_engine
                tradeslite = enginelite.get_all_trades()
                engine.load_list_trades(tradeslite)
            else:
                enginepro = self.backtester_engine.backtestingpro_engine
                tradespro = enginepro.get_all_trades()
                engine.load_list_trades(tradespro)


        engine.load_list_trades(trades)
        engine.set_parameters(capital=capital,contracts=contracts)

        alltrades = engine.get_all_trades()
        df = engine.calculate_result_tbt()
        dailyresults = engine.get_all_daily_results()

        statistics = engine.calculate_statistics(df=df, output=False, trades=alltrades)

        self.overviewchart.set_data(df)

        self.riskstatics_monitor.set_data(statistics)
        self.statistics_monitor.set_data(statistics)
        self.txnstatics_monitor.set_data(statistics)
        self.ratiostatics_monitor.set_data(statistics)

        self.txnviewtable.set_data(alltrades)
        self.overviewchart.set_trade(alltrades)
        self.dailytable.set_data(dailyresults)


    def load_result_handle(self, f):
        reader = csv.DictReader(f)
        trades = []
        try:
            head = reader.fieldnames
            if 'long_pnl' in head:
                for item in reader:
                    dt = datetime.strptime(
                            item['datetime'], '%Y.%m.%d %H:%M:%S')

                    trade = BacktestTradeData(
                        full_symbol=item['full_symbol'],
                        direction=Direction(item['direction']),
                        offset=Offset(item['offset']),
                        price=float(item['price']),
                        volume=float(item['volume']),
                        datetime=dt,
                        turnover=float(item['turnover']),
                        commission=float(item['commission']),
                        slippage=float(item['slippage']),
                        long_pos=float(item['long_pos']),
                        long_price=float(item['long_price']),
                        long_pnl=float(item['long_pnl']),
                        short_pos=float(item['short_pos']),
                        short_price=float(item['short_price']),
                        short_pnl=float(item['short_pnl']),
                    )
                    trades.append(trade)            
            else:
                for item in reader:
                    dt = datetime.strptime(
                            item['datetime'], '%Y.%m.%d %H:%M:%S')

                    trade = BacktestTradeData(
                        full_symbol=item['full_symbol'],
                        direction=Direction(item['direction']),
                        offset=Offset(item['offset']),
                        price=float(item['price']),
                        volume=float(item['volume']),
                        datetime=dt,
                    )
                    trades.append(trade)
        except Exception as e:
            msg = "Load Results error: {0}".format(str(e.args[0]))
            self.write_log(msg)
            return []

        return trades



    def clear_data(self):
        if self.btmode.currentText() == 'lite':
            full_sym = self.symbol_line.text()
        else:
            full_sym = self.symbol_line_pro.text()
            
        if self.db_type_combo.currentText() == 'Tick':
            msg = f"will clear Tick data {full_sym} , continue?"
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', msg,
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return
            SQGlobal.history_tick[full_sym].clear()
        elif self.db_type_combo.currentText() == 'TbtBar':
            msg = f"will clear TbtBar(1m) data {full_sym} , continue?"
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', msg,
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return
            fullsyminterval = full_sym + '-' + self.db_interval_combo.currentText()
            SQGlobal.history_tbtbar[fullsyminterval].clear()
        elif self.db_type_combo.currentText() == 'Bar':
            msg = f"will clear Bar(1m) data {full_sym} , continue?"
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', msg,
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return
            fullsyminterval = full_sym + '-' + self.db_interval_combo.currentText()
            SQGlobal.history_bar[fullsyminterval].clear()

    def load_data_file(self):
        if not self.data_source.currentText() == 'Memory':
            return
        if self.btmode.currentText() == 'lite':
            full_sym = self.symbol_line.text()
        else:
            full_sym = self.symbol_line_pro.text()

        if self.db_type_combo.currentText() == 'Tick':
            if SQGlobal.history_tick[full_sym]:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'already has data in memory!', QtWidgets.QMessageBox.Ok)
                return
            QtWidgets.QMessageBox().information(None, 'Info',
                                                'Please load data to from Tools/Data loader!', QtWidgets.QMessageBox.Ok)
            return
        elif self.db_type_combo.currentText() == 'TbtBar':
            fullsyminterval = full_sym + '-' + self.db_interval_combo.currentText()
            if SQGlobal.history_tbtbar[fullsyminterval]:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'already has data in memory!', QtWidgets.QMessageBox.Ok)
                return
            QtWidgets.QMessageBox().information(None, 'Info',
                                                'Please load data to from Tools/Data loader!', QtWidgets.QMessageBox.Ok)
            return
        elif self.db_type_combo.currentText() == 'Bar':
            fullsyminterval = full_sym + '-' + self.db_interval_combo.currentText()
            if SQGlobal.history_bar[fullsyminterval]:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'already has data in memory!', QtWidgets.QMessageBox.Ok)
                return
            QtWidgets.QMessageBox().information(None, 'Info',
                                                'Please load data to from Tools/Data loader!', QtWidgets.QMessageBox.Ok)
            return
        QtWidgets.QMessageBox().information(
            None, 'Info', 'not implemented yet!', QtWidgets.QMessageBox.Ok)


    def batchaddsetting(self):
        class_name = self.class_combo.currentText()
        old_setting = self.settings[class_name]
        new_setting = self.strategysetting.get_setting()
        self.settings[class_name] = new_setting

        if self.btmode.currentText() == 'lite':
            full_symbol = self.symbol_line.text()
        elif self.btmode.currentText() == 'pro':
            full_symbol = self.symbol_line_pro.text()

        db_interval = self.db_interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()

        margin = self.margin_line.text()
        rate = self.rate_line.text()
        slippage = self.slippage_line.text()
        size = self.size_line.text()
        pricetick = self.pricetick_line.text()

        setting = {
            'strategy':class_name,
            'parameter':str(new_setting),
            'full_symbol': full_symbol,
            'interval':db_interval,
            'start': start, 
            'end': end,
            'margin':margin,
            'rate':rate,
            'slippage':slippage,
            'size':size,
            'pricetick':pricetick
        }
        self.batchtable.add_data(setting)


    def save_btsetting(self):
        class_name = self.class_combo.currentText()
        full_symbol = self.symbol_line.text()
        db_interval = self.db_interval_combo.currentText()
        db_collection = self.db_collection_edit.text()
        db_type = self.db_type_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()
        usingcursor = self.dbusingcursor.isChecked()

        new_setting = self.strategysetting.get_setting()

        if self.btmode.currentText() == 'pro':
            full_symbol = self.symbol_line_pro.text()
            settingtosave = {}
            settingtosave['mode'] = 'pro'
            settingtosave['strategy'] = class_name
            settingtosave['full_symbol'] = full_symbol
            settingtosave['start'] = start.strftime('%Y-%m-%d')
            settingtosave['end'] = end.strftime('%Y-%m-%d')
            settingtosave['capital'] = capital
            settingtosave['datasource'] = datasource
            settingtosave['usingcursor'] = usingcursor
            settingtosave['parameter'] = new_setting
            settingtosave['dbcollection'] = db_collection
            settingtosave['dbtype'] = db_type
            settingtosave['interval'] = db_interval            
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "保存回测设置", "", "JSON(*.json)")
            if not path:
                return
            with open(path, "w") as f:
                json.dump(settingtosave, f, indent=4)
            return
        else:
            rate = float(self.rate_line.text())
            slippage = float(self.slippage_line.text())
            size = float(self.size_line.text())
            pricetick = float(self.pricetick_line.text())


            settingtosave = {}
            settingtosave['mode'] = 'lite'
            settingtosave['strategy'] = class_name
            settingtosave['full_symbol'] = full_symbol
            settingtosave['start'] = start.strftime('%Y-%m-%d')
            settingtosave['end'] = end.strftime('%Y-%m-%d')
            settingtosave['rate'] = rate
            settingtosave['slippage'] = slippage
            settingtosave['size'] = size
            settingtosave['pricetick'] = pricetick
            settingtosave['capital'] = capital
            settingtosave['datasource'] = datasource
            settingtosave['dbcollection'] = db_collection
            settingtosave['dbtype'] = db_type
            settingtosave['interval'] = db_interval
            settingtosave['usingcursor'] = usingcursor
            settingtosave['parameter'] = new_setting

            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "保存回测设置", "", "JSON(*.json)")
            if not path:
                return
            with open(path, "w") as f:
                json.dump(settingtosave, f, indent=4)
            return


    def start_backtesting(self):
        """"""
        if self.btmode.currentText() == 'pro':
            if self.batchmode.isChecked():
                mbox = QtWidgets.QMessageBox().question(None, 'Confirm', 'Start Batch Backtest Pro?',
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                if mbox == QtWidgets.QMessageBox.No:
                    return      
                self.start_batch_btpro()
            else:
                self.start_pro_bt()
        else: 
            if self.batchmode.isChecked():
                mbox = QtWidgets.QMessageBox().question(None, 'Confirm', 'Start Batch backtest?',
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                if mbox == QtWidgets.QMessageBox.No:
                    return             
                self.start_batch_bt()
            else:
                class_name = self.class_combo.currentText()
                full_symbol = self.symbol_line.text()
                db_interval = self.db_interval_combo.currentText()
                db_collection = self.db_collection_edit.text()
                db_type = self.db_type_combo.currentText()

                start = self.start_date_edit.date().toPyDate()
                end = self.end_date_edit.date().toPyDate()
                rate = float(self.rate_line.text())
                slippage = float(self.slippage_line.text())
                size = float(self.size_line.text())
                pricetick = float(self.pricetick_line.text())
                capital = float(self.capital_line.text())
                datasource = self.data_source.currentText()
                usingcursor = self.dbusingcursor.isChecked()

                if end <= start:
                    QtWidgets.QMessageBox().information(None, 'Error',
                                                        'End date should later than start date!', QtWidgets.QMessageBox.Ok)
                    return
                if (end - start) > timedelta(days=90) and db_type.endswith('Tick'):
                    mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                    if mbox == QtWidgets.QMessageBox.No:
                        return

                old_setting = self.settings[class_name]
                new_setting = self.strategysetting.get_setting()

                self.settings[class_name] = new_setting

                result = self.backtester_engine.start_backtesting(
                    class_name,
                    full_symbol,
                    start,
                    end,
                    rate,
                    slippage,
                    size,
                    pricetick,
                    capital,
                    new_setting,
                    datasource,
                    usingcursor,
                    db_collection,
                    db_type,
                    db_interval,
                )

                if result:
                    self.riskstatics_monitor.clear_data()
                    self.statistics_monitor.clear_data()
                    self.txnstatics_monitor.clear_data()
                    self.ratiostatics_monitor.clear_data()
                    self.overviewchart.clear_data()
                    self.txnviewtable.set_data([])
                    self.dailytable.set_data([])

    


    def start_pro_bt(self):
        contracts = self.bt_contract_manager.contracts
        class_name = self.class_combo.currentText()
        full_symbol = self.symbol_line_pro.text()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()
        usingcursor = self.dbusingcursor.isChecked()
        db_interval = self.db_interval_combo.currentText()
        db_collection = self.db_collection_edit.text()
        db_type = self.db_type_combo.currentText()

        if end <= start:
            QtWidgets.QMessageBox().information(None, 'Error',
                                                'End date should later than start date!', QtWidgets.QMessageBox.Ok)
            return
        if (end - start) > timedelta(days=90) and db_type.endswith('Tick'):
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return

        old_setting = self.settings[class_name]
        new_setting = self.strategysetting.get_setting()
        self.settings[class_name] = new_setting


        result = self.backtester_engine.start_backtesting_pro(
            class_name,
            full_symbol,
            start,
            end,
            capital,
            new_setting,
            contracts,
            datasource,
            usingcursor,
            db_collection,
            db_type,
            db_interval
        )

        if result:
            self.riskstatics_monitor.clear_data()
            self.statistics_monitor.clear_data()
            self.txnstatics_monitor.clear_data()
            self.ratiostatics_monitor.clear_data()
            self.overviewchart.clear_data()
            self.txnviewtable.set_data([])
            self.dailytable.set_data([])

    def start_batch_bt(self):
        batchsettinglist = self.batchtable.get_data()
        # class_name = self.class_combo.currentText()

        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()
        usingcursor = self.dbusingcursor.isChecked()

        db_interval = self.db_interval_combo.currentText()
        db_collection = self.db_collection_edit.text()
        db_type = self.db_type_combo.currentText()


        cpunums = self.btcpus.value()

        result = self.backtester_engine.start_batch_bt_mp(
            cpunums,
            batchsettinglist,
            capital,
            datasource,
            usingcursor,
            db_collection,
            db_type,
            db_interval
        )

        if result:
            self.riskstatics_monitor.clear_data()
            self.statistics_monitor.clear_data()
            self.txnstatics_monitor.clear_data()
            self.ratiostatics_monitor.clear_data()
            self.overviewchart.clear_data()
            self.txnviewtable.set_data([])
            self.dailytable.set_data([])

    def start_batch_btpro(self):
        contracts = self.bt_contract_manager.contracts

        batchsettinglist = self.batchtable.get_data()
        # class_name = self.class_combo.currentText()

        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()
        usingcursor = self.dbusingcursor.isChecked()
        db_interval = self.db_interval_combo.currentText()
        db_collection = self.db_collection_edit.text()
        db_type = self.db_type_combo.currentText()


        cpunums = self.btcpus.value()

        result = self.backtester_engine.start_batch_btpro_mp(
            cpunums,
            batchsettinglist,
            capital,
            contracts,
            datasource,
            usingcursor,
            db_collection,
            db_type,
            db_interval
        )

        if result:
            self.riskstatics_monitor.clear_data()
            self.statistics_monitor.clear_data()
            self.txnstatics_monitor.clear_data()
            self.ratiostatics_monitor.clear_data()
            self.overviewchart.clear_data()
            self.txnviewtable.set_data([])
            self.dailytable.set_data([])


    def start_optimization(self,optmode='grid'):
        """"""
        class_name = self.class_combo.currentText()
        full_symbol = self.symbol_line.text()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        rate = float(self.rate_line.text())
        slippage = float(self.slippage_line.text())
        size = float(self.size_line.text())
        pricetick = float(self.pricetick_line.text())
        capital = float(self.capital_line.text())
        datasource = self.data_source.currentText()
        bt_mode = self.btmode.currentText()
        contracts = self.bt_contract_manager.contracts
        usingcursor = self.dbusingcursor.isChecked()
        db_interval = self.db_interval_combo.currentText()
        db_collection = self.db_collection_edit.text()
        db_type = self.db_type_combo.currentText()


        if (end - start) > timedelta(days=90) and db_type.endswith('Tick'):
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return

        # parameters = self.settings[class_name]
        # self.optisetting.set_paras(class_name, parameters)

        # dialog = OptimizationSettingEditor(class_name, parameters)
        # i = dialog.exec()
        # if i != dialog.Accepted:
        #     return

        optimization_setting, use_ga = self.optisetting.get_setting()
        self.target_display = self.optisetting.target_display
        self.use_roll = optimization_setting.use_roll

        if bt_mode == 'lite':
            self.backtester_engine.start_optimization(
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
                usingcursor,
                db_collection,
                db_type,
                db_interval
            )
            
        elif bt_mode == 'pro':
            full_symbol = self.symbol_line_pro.text()
            self.backtester_engine.start_optimization_pro(
                class_name,
                full_symbol,
                start,
                end,
                capital,
                contracts,
                optimization_setting,
                use_ga,
                datasource,
                usingcursor,
                db_collection,
                db_type,
                db_interval
            )

        # self.result_button.setEnabled(False)

    def show_optimization_result(self):
        """"""


        result_values = self.backtester_engine.get_result_values()
        
        if self.use_roll:
            rolldf = result_values[2]
            engine = self.backtester_engine.virtualengine
            capital = float(self.capital_line.text())
            engine.set_parameters(capital=capital)

            statistics = engine.calculate_statistics(df=rolldf, output=False)
            self.overviewchart.set_data(rolldf)
            self.riskstatics_monitor.set_data(statistics)
            self.statistics_monitor.set_data(statistics)
            self.txnstatics_monitor.set_data(statistics)
            self.ratiostatics_monitor.set_data(statistics)
            self.bt_opt.setCurrentIndex(1)

        else:

            self.grid_opt.set_data(result_values,self.target_display)
            self.bt_opt.setCurrentIndex(0)


    def show_data(self):
        dv = self.dataview

        db_interval = dv.db_interval_combo.currentText()
        db_collection = dv.db_collection_edit.text()
        db_type = dv.db_type_combo.currentText()
        full_symbol = dv.symbol_line.text()
        datasource = dv.data_source.currentText()
        start = dv.start_date_edit.dateTime().toPyDateTime()
        end = dv.end_date_edit.dateTime().toPyDateTime()
        trades = self.backtester_engine.get_result_trades()
        addtrade = bool(trades) and full_symbol == trades[0].full_symbol
        combo_setting = dv.get_setting()
        tabsymbol = (db_type + '-' + db_interval + '-' + full_symbol)

        if end <= start :
            QtWidgets.QMessageBox().information(
                None, 'Info', 'End time should later than start time!', QtWidgets.QMessageBox.Ok)
            return

        istoomanydata =  (  (end - start) > timedelta(days=60) and db_interval == '1m' ) \
             or  (end - start > timedelta(minutes=2880) and db_type == 'Tick')

        if istoomanydata:
            mbox = QtWidgets.QMessageBox().question(None, 'Warning', 'Two many data will slow system performance, continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if mbox == QtWidgets.QMessageBox.No:
                return

        for i in range(self.bt_dataviews.count()):
            if self.bt_dataviews.tabText(i) == tabsymbol:
                widget = self.bt_dataviews.widget(i)
                widget.reset(combo_setting, start, end,
                            Interval(db_interval), datasource,db_collection)
                if addtrade:
                    widget.add_trades(trades)
                    widget.show_text_signals()
                return

        dataviewchart = BTQuotesChart(db_type)    
        dataviewchart.reset(combo_setting, start, end, Interval(db_interval), datasource,db_collection)
        if addtrade:
            dataviewchart.add_trades(trades)
            dataviewchart.show_text_signals()
        self.bt_dataviews.addTab(dataviewchart, tabsymbol)


    def start_analysis(self):
        pass

    def start_vecbt(self):
        pass

    def start_vecbt_interday(self):
        pass


    def start_corr(self):
        pass


    def start_vecroll(self):
        pass












    def show_indicator(self,indicator):
        dv = self.dataview        
        db_type = dv.db_type_combo.currentText()
        db_interval = dv.db_interval_combo.currentText()
        full_symbol = dv.symbol_line.text()

        tabsymbol = (db_type + '-' + db_interval + '-' + full_symbol)


        for i in range(self.bt_dataviews.count()):
            if self.bt_dataviews.tabText(i) == tabsymbol:
                widget = self.bt_dataviews.widget(i)
                widget.set_indicator(indicator)
                return    

        QtWidgets.QMessageBox().information(
            None, 'Info', '请先加载相应行情!', QtWidgets.QMessageBox.Ok)
        return


    def show_trade(self, trade):
        dv = self.dataview

        db_interval = dv.db_interval_combo.currentText()
        db_collection = dv.db_collection_edit.text()
        datasource = dv.data_source.currentText()

        full_symbol = trade.full_symbol
        tradetime = trade.datetime        
        db_type = self.db_type_combo.currentText()
        tabsymbol = (db_type + '-' + db_interval + '-' + full_symbol)
        combosym = ([(full_symbol,0)],'+')

        #default is bar/1min ,which show 2days before and after
        adddaysstart = 5
        if tradetime.date().weekday() == 0:
            adddaysstart = 6
        elif tradetime.date().weekday() == 1:
            adddaysstart = 7
        if db_interval == 'd':
            adddaysstart = 60
        elif db_interval == '1h': 
            adddaysstart = 15
        start = tradetime - timedelta(days=adddaysstart)

        adddaysend = 5
        if tradetime.date().weekday() == 4:
            adddaysend = 7

        if db_interval == 'd':
            adddaysend = 30
        elif db_interval == '1h': 
            adddaysend = 10

        end = tradetime + timedelta(days=adddaysend)

        # for tick, 10min before and after
        if db_type == 'Tick':
            start = tradetime - timedelta(minutes=10)
            end = tradetime + timedelta(minutes=10)

        trades = self.backtester_engine.get_result_trades()
        for i in range(self.bt_dataviews.count()):
            if self.bt_dataviews.tabText(i) == tabsymbol:
                widget = self.bt_dataviews.widget(i)
                widget.reset(combosym, start,
                             end, Interval(db_interval), datasource,db_collection)
                widget.add_trades(trades)
                widget.show_text_signals()
                return

        dataviewchart = BTQuotesChart(db_type)
        dataviewchart.reset(combosym, start,
                            end, Interval(db_interval), datasource,db_collection)
        dataviewchart.add_trades(trades)
        dataviewchart.show_text_signals()

        self.bt_dataviews.addTab(dataviewchart, tabsymbol)

        


    def show(self):
        """"""
        self.showMaximized()

