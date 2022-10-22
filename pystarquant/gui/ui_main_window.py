#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue
from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import datetime
# import requests
# import itchat

import pyqtgraph.console

# from source.trade.order_manager import OrderManager
from pystarquant.common.constant import EventType
from pystarquant.trade.risk_manager import PassThroughRiskManager
from pystarquant.engine.iengine import EventEngine
from pystarquant.common.client_mq import ClientMq

from pystarquant.engine.local_engine import LocalMainEngine

import pystarquant.common.sqglobal as SQGlobal



from pystarquant.gui.ui_common import (
    ContractManager,
    StatusThread,
    AboutWidget,
    # WebWindow,
    GlobalDialog,
    TextEditDialog
)
from pystarquant.gui.ui_worker import (
    RecorderManager,
    CsvLoaderWidget
)
from pystarquant.gui.ui_monitor import (
    MarketMonitor,
    OrderMonitor,
    TradeMonitor,
    PositionMonitor,
    AccountMonitor,
    LogMonitor
)

from pystarquant.gui.ui_strategy_window import CtaManager
from pystarquant.gui.ui_manual_window import ManualWindow
from pystarquant.gui.ui_bt_main import BacktesterManager
from pystarquant.gui.ui_dataview import MarketDataView,StrategyDataView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # member variables
        self._current_time = None
        self._lang_dict = SQGlobal.lang_dict
        self._font = self._lang_dict['font']
        self._widget_dict = {}
        self.central_widget = None
        # self.central_widget = QtWidgets.QStackedWidget()
        self.market_window = None
        self.message_window = None
        self.order_window = None
        self.fill_window = None
        self.position_window = None
        self.closeposition_window = None
        self.account_window = None
        self.strategy_window = None
        self.manualorderid = 0

        #  0. order_manager; some of ui_windows uses order_manager
        # self._order_manager = OrderManager()

        # 1. event engine
        # outgoing queue from client side
        self._outgoing_queue = Queue()
        self._events_engine = EventEngine()        # update ui
        self._main_engine = LocalMainEngine(self._events_engine)

        # TODO add task scheduler;produce result_packet
        self._flowrate_timer = QtCore.QTimer()

        # 5. risk manager and compliance manager
        self.risk_manager = PassThroughRiskManager()

        # 7 portfolio manager and position manager
        self.contract_manager = ContractManager()
        self.recorder_manager = RecorderManager(
            contracts=self.contract_manager.contracts)
        self.recorder_manager.signal_recorder_out.connect(
            self._outgoing_general_request_handler)
        self.pgconsole = pyqtgraph.console.ConsoleWidget()
        self.pgconsole.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.pgconsole.setStyleSheet("background-color: #CCE8CF; color:black")

        # 8. client mq
        self._client_mq = ClientMq(self._events_engine, self._outgoing_queue)


        # 1. set up gui windows
        # self.setGeometry(50, 50, 850, 650)
        self.setWindowTitle('StarQuant-Backtest')
        self.setWindowIcon(QtGui.QIcon("pystarquant/gui/image/quant_logo.png"))
        self.init_menu()
        self.init_status_bar()
        self.init_central_area()

        # 9. wire up event handlers
        self._events_engine.register(EventType.TICK, self._tick_event_handler)
        self._events_engine.register(
            EventType.ORDERSTATUS, self._order_status_event_handler)
        self._events_engine.register(EventType.FILL, self._fill_event_handler)
        self._events_engine.register(
            EventType.POSITION, self._position_event_handler)
        self._events_engine.register(
            EventType.ACCOUNT, self._account_event_handler)
        self._events_engine.register(
            EventType.CONTRACT, self._contract_event_handler)
        self._events_engine.register(
            EventType.HISTORICAL, self._historical_event_handler)
        self._events_engine.register(EventType.INFO, self._info_event_handler)
        self._events_engine.register(
            EventType.STRATEGY_CONTROL, self._strategy_control_event_handler)
        self._events_engine.register(
            EventType.ENGINE_CONTROL, self._engine_control_event_handler)
        self._events_engine.register(
            EventType.RECORDER_CONTROL, self._recorder_control_event_handler)
        self._events_engine.register(
            EventType.ORDER, self._outgoing_order_request_handler)
        self._events_engine.register(
            EventType.QRY, self._outgoing_qry_request_handler)
        self._events_engine.register(
            EventType.SUBSCRIBE, self._outgoing_general_request_handler)
        self._events_engine.register(
            EventType.GENERAL_REQ, self._outgoing_general_request_handler)

        # timer event to reset riskmanager flow rate count
        self._flowrate_timer.timeout.connect(self.risk_manager.reset)
        # 10. start
        self._events_engine.start()
        self._client_mq.start()
        self._flowrate_timer.start(5000)




    #################################################################################################
    # -------------------------------- Event Handler   --------------------------------------------#
    #################################################################################################

    def _tick_event_handler(self, tick_event):
        self.dataviewindow.tick_signal.emit(tick_event)
        self.strategydataui.tick_signal.emit(tick_event)
        self.strategydataui_1.tick_signal.emit(tick_event)
        self.strategydataui_2.tick_signal.emit(tick_event)

        self.strategydataui_20.tick_signal.emit(tick_event)
        self.strategydataui_21.tick_signal.emit(tick_event)
        self.strategydataui_22.tick_signal.emit(tick_event)

        self.strategydataui_30.tick_signal.emit(tick_event)
        self.strategydataui_31.tick_signal.emit(tick_event)
        self.strategydataui_32.tick_signal.emit(tick_event)

        self.strategydataui_40.tick_signal.emit(tick_event)
        self.strategydataui_41.tick_signal.emit(tick_event)
        self.strategydataui_42.tick_signal.emit(tick_event)


        self._current_time = tick_event.data.timestamp
        # self._order_manager.on_tick(tick_event)     # check standing stop orders


    def _order_status_event_handler(self, order_status_event):  # including cancel
        pass

    def _fill_event_handler(self, fill_event):
        try:
            trade = fill_event.data
            msg = f"{trade.full_symbol}: ({trade.direction.value},{trade.offset.value}),({trade.price},{trade.volume})"
            # itchat.send_msg(msg, 'filehelper')
        except:
            pass

    def _position_event_handler(self, position_event):
        pass

    def _account_event_handler(self, account_event):
        pass

    def _contract_event_handler(self, contract_event):
        contract = contract_event.data
        self.contract_manager.on_contract(contract)

    def _historical_event_handler(self, historical_event):
        pass
        # print(historical_event)

    def _strategy_control_event_handler(self, sc_event):
        self.ctastrategywindow.signal_strategy_in.emit(sc_event)

    def _engine_control_event_handler(self, ec_event):
        self.manual_widget.updateapistatusdict(ec_event)

    def _recorder_control_event_handler(self, rc_event):
        self.recorder_manager.signal_recorder_update.emit(rc_event)

    def _info_event_handler(self, info_event):
        pass
        # self.log_window.msg_signal.emit(info_event)

# ----------------------------------------outgoing event ------------------------------------
    def _outgoing_order_request_handler(self, o):
        """
         process o, check against risk manager and compliance manager
        """
        self.risk_manager.order_in_compliance(
            o)  # order pointer; modify order directly
        if (self.risk_manager.passorder()):
            # self._order_manager.on_order(o)
            # self.order_window.
            msg = o.serialize()
            print('client send msg: ' + msg, datetime.now())
            # print('client send msg: ' + msg)
            # text = o.destination + o.source + str(o.clientID)
            # requests.get('https://sc.ftqq.com/SCU49995T54cd0bf4d42dd8448359347830d62bd85cc3f69d085ee.send?text=%s &desp=%s'%(text,msg))
            self._outgoing_queue.put(msg)

    def _outgoing_qry_request_handler(self, qry):
        if (self.risk_manager.passquery()):
            msg = qry.serialize()
            print('client send msg: ' + msg)
            self._outgoing_queue.put(msg)

    def _outgoing_general_request_handler(self, gr):
        msg = gr.serialize()
        print('client send msg: ' + msg)
        self._outgoing_queue.put(msg)

    #################################################################################################
    # ------------------------------ Event Handler Ends --------------------------------------------#
    #################################################################################################

    #################################################################################################
    # -------------------------------- User Interface  --------------------------------------------#
    #################################################################################################

    def set_font(self, font):
        self._font = font

    def displaytrade(self):
        self.central_widget.setCurrentIndex(1)

    def displaybacktest(self):
        self.central_widget.setCurrentIndex(0)

    def displaytools(self):
        self.central_widget.setCurrentIndex(2)



    def init_menu(self):
        menubar = self.menuBar()
        # sys menu --
        sysMenu = menubar.addMenu('File')
        editsettingAction = QtWidgets.QAction('Setting', self)
        editsettingAction.setStatusTip('edit python setting')
        editsettingAction.triggered.connect(self.edit_client_setting)
        sysMenu.addAction(editsettingAction)
        editfileAction = QtWidgets.QAction('view/edit', self)
        editfileAction.setStatusTip('edit server config...')
        editfileAction.triggered.connect(self.file_edit)
        sysMenu.addAction(editfileAction)
        # --exit
        sysMenu.addSeparator()
        sys_exitAction = QtWidgets.QAction('Exit', self)
        sys_exitAction.setShortcut('Ctrl+Q')
        sys_exitAction.setStatusTip('Exit GUI')
        sys_exitAction.triggered.connect(self.close)
        sysMenu.addAction(sys_exitAction)
        # mode menu
        modeMenu = menubar.addMenu('Mode')
        mode_backtestAction = QtWidgets.QAction('Backtest', self)
        mode_backtestAction.triggered.connect(self.displaybacktest)
        modeMenu.addAction(mode_backtestAction)
  
        # tool menu
        toolMenu = menubar.addMenu('Tools')

        tool_recorder = QtWidgets.QAction('Data Recorder', self)
        tool_recorder.triggered.connect(self.recorder_manager.show)
        toolMenu.addAction(tool_recorder)
        # tool_csvloader = QtWidgets.QAction('Data Loader', self)
        # tool_csvloader.triggered.connect(self.opencsvloader)
        # toolMenu.addAction(tool_csvloader)
        # tool_datadownloader = QtWidgets.QAction('Data Downloader', self)
        # tool_datadownloader.triggered.connect(self.data_downloader.show)
        # toolMenu.addAction(tool_datadownloader)
        # tool_pgconsole = QtWidgets.QAction('Python Console', self)
        # tool_pgconsole.triggered.connect(self.pgconsole.show)
        # toolMenu.addAction(tool_pgconsole)

        # view menu
        viewMenu = menubar.addMenu('View')

        # help menu
        helpMenu = menubar.addMenu('Help')
        help_contractaction = QtWidgets.QAction('Query Contracts', self)
        help_contractaction.triggered.connect(self.contract_manager.show)
        helpMenu.addAction(help_contractaction)
        # help_webaction = QtWidgets.QAction('Web/Jupyter Notebook', self)
        # help_webaction.triggered.connect(self.openweb)
        # helpMenu.addAction(help_webaction)
        help_action = QtWidgets.QAction('About', self)
        help_action.triggered.connect(self.openabout)
        helpMenu.addAction(help_action)

    def toggleviewmanual(self, state):
        if state:
            self.manual_widget.setVisible(True)
        else:
            self.manual_widget.hide()

    def toggleviewMarketMonitor(self, state):
        if state:
            self.marketmonitors.setVisible(True)
        else:
            self.marketmonitors.hide()

    def toggleviewTradeMonitor(self, state):
        if state:
            self.trademonitors.setVisible(True)
        else:
            self.trademonitors.hide()

    def toggleviewMarketChart(self, state):
        if state:
            self.marketcharts.setVisible(True)
        else:
            self.marketcharts.hide()

    def toggleviewCtaManager(self, state):
        if state:
            self.algomanagers.setVisible(True)
        else:
            self.algomanagers.hide()

    def toggleviewBtSetting(self, state):
        if state:
            self.backtestwidget.bt_setting.setVisible(True)
        else:
            self.backtestwidget.bt_setting.hide()

    def toggleviewBtTopM(self, state):
        if state:
            self.backtestwidget.bt_topmiddle.setVisible(True)
        else:
            self.backtestwidget.bt_topmiddle.hide()

    def toggleviewBtBottomM(self, state):
        if state:
            self.backtestwidget.bt_bottommiddle.setVisible(True)
        else:
            self.backtestwidget.bt_bottommiddle.hide()

    def file_edit(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'open file', 'etc/')
        print(filename)
        if not filename:
            return
        a = TextEditDialog(filename)
        a.exec_()

    def opencsvloader(self):
        try:
            self._widget_dict['csvloader'].show()
        except KeyError:
            self._widget_dict['csvloader'] = CsvLoaderWidget()
            self._widget_dict['csvloader'].show()

    def edit_client_setting(self):
        """
        """
        dialog = GlobalDialog()
        dialog.exec_()

    def openabout(self):
        try:
            self._widget_dict['about'].show()
        except KeyError:
            self._widget_dict['about'] = AboutWidget()
            self._widget_dict['about'].show()

    def openweb(self):
        pass
        # try:
        #     self._widget_dict['web'].show()
        # except KeyError:
        #     self._widget_dict['web'] = WebWindow()
        #     self._widget_dict['web'].show()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        print('closing main window')
        self._events_engine.stop()
        self._client_mq.stop()

    def init_status_bar(self):
        self.statusthread = StatusThread()
        self.statusthread.status_update.connect(self.update_status_bar)
        self.statusthread.start()

    def update_status_bar(self, message):
        self.statusBar().showMessage(message)

    def init_central_area(self):
        self.central_widget = QtWidgets.QStackedWidget()

# -------Trade Widgets----------
        # --------------------------------  manulwidget  ---------------------------------
        manualwidget = ManualWindow(SQGlobal.config_server['gateway'])
        manualwidget.order_signal.connect(self._outgoing_order_request_handler)
        manualwidget.qry_signal.connect(self._outgoing_qry_request_handler)
        manualwidget.manual_req.connect(self._outgoing_queue.put)
        manualwidget.subscribe_signal.connect(
            self._outgoing_general_request_handler)
        manualwidget.cancelall_signal.connect(
            self._outgoing_general_request_handler)
        self.manual_widget = manualwidget



        # -------------------------------- marketmonitors ------------------------------------------#

        marketmonitors = QtWidgets.QTabWidget()
        marketmonitors.setContentsMargins(0, 0, 0, 0)

        tltab1 = MarketMonitor(self._events_engine)
        tltab2 = QtWidgets.QWidget()
        tltab3 = QtWidgets.QWidget()
        marketmonitors.addTab(tltab1,'单标的')
        marketmonitors.addTab(tltab2,'组合')
        marketmonitors.addTab(tltab3,'期权')

        self.market_window = tltab1
        self.marketmonitors = marketmonitors
        # -------------------------------- trademonitors------------------------------------------#
        trademonitors = QtWidgets.QTabWidget()
        trademonitors.setContentsMargins(0, 0, 0, 0)
        trademonitors.setFont(self._font)
        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()
        tab3 = QtWidgets.QWidget()
        tab4 = QtWidgets.QWidget()
        # tab5 = QtWidgets.QWidget()
        tab6 = QtWidgets.QWidget()
        trademonitors.addTab(tab1, self._lang_dict['Log'])
        trademonitors.addTab(tab2, self._lang_dict['Order'])
        trademonitors.addTab(tab3, self._lang_dict['Fill'])
        trademonitors.addTab(tab4, self._lang_dict['Position'])
        trademonitors.addTab(tab6, self._lang_dict['Account'])
        trademonitors.setTabPosition(QtWidgets.QTabWidget.West)

        # self.log_window = LogWindow(self._lang_dict)
        self.log_window = LogMonitor(self._events_engine)
        tab1_layout = QtWidgets.QVBoxLayout()
        tab1_layout.addWidget(self.log_window)
        tab1.setLayout(tab1_layout)

        self.order_window = OrderMonitor(self._events_engine)
        tab2_layout = QtWidgets.QVBoxLayout()
        tab2_layout.addWidget(self.order_window)
        tab2.setLayout(tab2_layout)

        self.fill_window = TradeMonitor(self._events_engine)
        tab3_layout = QtWidgets.QVBoxLayout()
        tab3_layout.addWidget(self.fill_window)
        tab3.setLayout(tab3_layout)

        self.position_window = PositionMonitor(self._events_engine)
        tab4_layout = QtWidgets.QVBoxLayout()
        tab4_layout.addWidget(self.position_window)
        tab4.setLayout(tab4_layout)

        self.account_window = AccountMonitor(self._events_engine)
        tab6_layout = QtWidgets.QVBoxLayout()
        tab6_layout.addWidget(self.account_window)
        tab6.setLayout(tab6_layout)

        self.trademonitors = trademonitors

        # -------------------------------- algoengine managers ------------------------------------------#
        algomanagers = QtWidgets.QTabWidget()
        algomanagers.setContentsMargins(0, 0, 0, 0)
        brtab1 = QtWidgets.QFrame()
        brtab1.setFrameShape(QtWidgets.QFrame.StyledPanel)
        brtab1.setFont(self._font)
        strategy_manager_layout = QtWidgets.QFormLayout()
        self.ctastrategywindow = CtaManager(self._events_engine)
        # 外发策略控制消息
        self.ctastrategywindow.signal_strategy_out.connect(
            self._outgoing_general_request_handler)

        # 对local发送信号
        self.ctastrategywindow.signal_strategy_out.connect(
            self._events_engine.put)

        strategy_manager_layout.addWidget(self.ctastrategywindow)

        brtab1.setLayout(strategy_manager_layout)

        brtab2 = QtWidgets.QWidget()
        brtab3 = QtWidgets.QWidget()
        brtab4 = QtWidgets.QWidget()
        
        algomanagers.addTab(brtab1,'策略管理')
        algomanagers.addTab(self.manual_widget,'远程控制台')

        # algomanagers.addTab(brtab3,'算法交易')
        # algomanagers.addTab(brtab4,'期权交易')
        algomanagers.setTabPosition(QtWidgets.QTabWidget.West)
        self.algomanagers = algomanagers
        self.strategydataui = StrategyDataView()

        # -----------------------marketcharts------------------------------------------------------#
        marketcharts = QtWidgets.QTabWidget()
        marketcharts.setContentsMargins(0, 0, 0, 0)
        # marketcharts.setTabPosition(QtWidgets.QTabWidget.South)
        tmtab1 = MarketDataView()
        tmtab2 = QtWidgets.QWidget()
        marketcharts.addTab(tmtab1,'行情k线')
        marketcharts.addTab(tmtab2,'期权')
        self.marketcharts = marketcharts

        self.dataviewindow = tmtab1
        self.market_window.symbol_signal.connect(
            self.dataviewindow.symbol_signal.emit)



        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)




        self.strategydataui_1 = StrategyDataView(wid=1)
        self.strategydataui_2 = StrategyDataView(wid=2)


        self.strategydataui_20 = StrategyDataView(wid=3)
        self.strategydataui_21 = StrategyDataView(wid=4)
        self.strategydataui_22 = StrategyDataView(wid=5)

        self.strategydataui_30 = StrategyDataView(wid=6)
        self.strategydataui_31 = StrategyDataView(wid=7)
        self.strategydataui_32 = StrategyDataView(wid=8)

        self.strategydataui_40 = StrategyDataView(wid=9)
        self.strategydataui_41 = StrategyDataView(wid=10)
        self.strategydataui_42 = StrategyDataView(wid=11)

        self.ctastrategywindow.signal_strategy_internal.connect(
            self.process_ctasignal_internal)

        splitter11 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter11.addWidget(self.strategydataui)
        splitter11.addWidget(self.strategydataui_1)
        splitter11.addWidget(self.strategydataui_2)

        splitter12 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter12.addWidget(self.strategydataui_20)
        splitter12.addWidget(self.strategydataui_21)
        splitter12.addWidget(self.strategydataui_22)

        splitter13 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter13.addWidget(self.strategydataui_30)
        splitter13.addWidget(self.strategydataui_31)
        splitter13.addWidget(self.strategydataui_32)

        splitter14 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter14.addWidget(self.strategydataui_40)
        splitter14.addWidget(self.strategydataui_41)
        splitter14.addWidget(self.strategydataui_42)


        splitter21 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter21.addWidget(splitter11)
        splitter21.addWidget(splitter12)
        splitter21.addWidget(splitter13)
        splitter21.addWidget(splitter14)

        self.scrollstrategyui = QtWidgets.QScrollArea()
        self.scrollstrategyui.setWidget(splitter21)
        self.scrollstrategyui.setWidgetResizable(True)

        splitter1.addWidget(self.scrollstrategyui)

        # splitter1.addWidget(algomanagers)
        splitter1.addWidget(trademonitors)


        splitter2 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter2.addWidget(marketcharts)
        splitter2.addWidget(marketmonitors)
        # splitter2.addWidget(self.recorder_manager)
        splitter2.setSizes([800, 400])

        splitter21 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        # splitter21.addWidget(self.manual_widget)
        splitter21.addWidget(algomanagers)
        # splitter21.setSizes([400, 800])

        splitter3 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter3.addWidget(splitter2)
        splitter3.addWidget(splitter21)

        splitter4 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter4.addWidget(splitter1)
        splitter4.addWidget(splitter3)
        splitter4.setSizes([600, 1200])

# ---------Backtest ----------------------------------------
        self.backtestwidget = BacktesterManager(self._events_engine)


# --------------------mainwindow----------------------


        self.central_widget.addWidget(self.backtestwidget)
        self.central_widget.setCurrentIndex(0)
        self.setCentralWidget(self.central_widget)

    #################################################################################################
    # ------------------------------ User Interface End --------------------------------------------#
    #################################################################################################

    def  process_ctasignal_internal(self,event):
        data = event.data
        wid  = int(event.destination[2:])
        if wid == 0:
            self.strategydataui.strategy_signal.emit(event)
        elif wid == 1:
            self.strategydataui_1.strategy_signal.emit(event)
        elif wid == 2:
            self.strategydataui_2.strategy_signal.emit(event)
        elif wid == 3:
            self.strategydataui_20.strategy_signal.emit(event)
        elif wid == 4:
            self.strategydataui_21.strategy_signal.emit(event)
        elif wid == 5:
            self.strategydataui_22.strategy_signal.emit(event)
        elif wid == 6:
            self.strategydataui_30.strategy_signal.emit(event)
        elif wid == 7:
            self.strategydataui_31.strategy_signal.emit(event)
        elif wid == 8:
            self.strategydataui_32.strategy_signal.emit(event)
        elif wid == 9:
            self.strategydataui_40.strategy_signal.emit(event)
        elif wid == 10:
            self.strategydataui_41.strategy_signal.emit(event)
        elif wid == 11:
            self.strategydataui_42.strategy_signal.emit(event)

