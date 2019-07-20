#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue
from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import datetime
import requests
import itchat
from source.common.constant import EventType
import pyqtgraph.console

# from source.trade.order_manager import OrderManager
from source.trade.risk_manager import PassThroughRiskManager
from source.engine.iengine import EventEngine
from source.common.client_mq import ClientMq

from .ui_common_widget import (
    RecorderManager,
    ContractManager,
    StatusThread,
    CsvLoaderWidget,
    DataDownloaderWidget,
    AboutWidget,
    WebWindow,
    GlobalDialog,
    TextEditDialog
)

from .ui_monitors import (
    MarketMonitor,
    OrderMonitor,
    TradeMonitor,
    PositionMonitor,
    AccountMonitor,
    LogMonitor
)

from .ui_strategy_window import CtaManager
from .ui_manual_window import ManualWindow
from .ui_bt_setting import BacktesterManager
from .ui_dataview import MarketDataView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config_server, config_client, lang_dict):
        super().__init__()

        # member variables
        self._current_time = None
        self._config_server = config_server
        self._config_client = config_client
        self._symbols = config_server['tickers']
        self._lang_dict = lang_dict
        self._font = lang_dict['font']
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
        self.data_downloader = DataDownloaderWidget()
        self.pgconsole = pyqtgraph.console.ConsoleWidget()

        # 8. client mq
        self._client_mq = ClientMq(
            self._config_server, self._events_engine, self._outgoing_queue)

        # 1. set up gui windows
        self.setGeometry(50, 50, 850, 650)
        self.setWindowTitle('StarQuant')
        self.setWindowIcon(QtGui.QIcon("source/gui/image/star.png"))
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
        self._current_time = tick_event.data.timestamp
        # self._order_manager.on_tick(tick_event)     # check standing stop orders

    def _order_status_event_handler(self, order_status_event):  # including cancel
        pass

    def _fill_event_handler(self, fill_event):
        try:
            trade = fill_event.data
            msg = f"{trade.full_symbol}: ({trade.direction.value},{trade.offset.value}),({trade.price},{trade.volume})"
            itchat.send_msg(msg, 'filehelper')
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
        self.central_widget.setCurrentIndex(0)

    def displaybacktest(self):
        self.central_widget.setCurrentIndex(1)

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
        mode_tradeAction = QtWidgets.QAction('Trade', self)
        mode_tradeAction.triggered.connect(self.displaytrade)
        modeMenu.addAction(mode_tradeAction)
        mode_backtestAction = QtWidgets.QAction('Backtest', self)
        mode_backtestAction.triggered.connect(self.displaybacktest)
        modeMenu.addAction(mode_backtestAction)

        # tool menu
        toolMenu = menubar.addMenu('Tools')

        tool_recorder = QtWidgets.QAction('Data Recorder', self)
        tool_recorder.triggered.connect(self.recorder_manager.show)
        toolMenu.addAction(tool_recorder)
        tool_csvloader = QtWidgets.QAction('Data Loader', self)
        tool_csvloader.triggered.connect(self.opencsvloader)
        toolMenu.addAction(tool_csvloader)
        tool_datadownloader = QtWidgets.QAction('Data Downloader', self)
        tool_datadownloader.triggered.connect(self.data_downloader.show)
        toolMenu.addAction(tool_datadownloader)
        tool_pgconsole = QtWidgets.QAction('Python Console', self)
        tool_pgconsole.triggered.connect(self.pgconsole.show)
        toolMenu.addAction(tool_pgconsole)

        # view menu
        viewMenu = menubar.addMenu('View')
        viewManual = QtWidgets.QAction(
            'Manual Control Center', self, checkable=True)
        viewManual.setChecked(True)
        viewManual.triggered.connect(self.toggleviewmanual)
        viewMenu.addAction(viewManual)
        viewMarketMonitor = QtWidgets.QAction(
            'Market Monitor', self, checkable=True)
        viewMarketMonitor.setChecked(True)
        viewMarketMonitor.triggered.connect(self.toggleviewMarketMonitor)
        viewMenu.addAction(viewMarketMonitor)
        viewTradeMonitor = QtWidgets.QAction(
            'Trade Monitor', self, checkable=True)
        viewTradeMonitor.setChecked(True)
        viewTradeMonitor.triggered.connect(self.toggleviewTradeMonitor)
        viewMenu.addAction(viewTradeMonitor)
        viewMarketChart = QtWidgets.QAction(
            'Market Chart', self, checkable=True)
        viewMarketChart.setChecked(True)
        viewMarketChart.triggered.connect(self.toggleviewMarketChart)
        viewMenu.addAction(viewMarketChart)
        viewCtaManager = QtWidgets.QAction(
            'Strategy Manager', self, checkable=True)
        viewCtaManager.setChecked(True)
        viewCtaManager.triggered.connect(self.toggleviewCtaManager)
        viewMenu.addAction(viewCtaManager)
        viewBtSetting = QtWidgets.QAction(
            'Backtest Setting', self, checkable=True)
        viewBtSetting.setChecked(True)
        viewBtSetting.triggered.connect(self.toggleviewBtSetting)
        viewMenu.addAction(viewBtSetting)
        viewBtTopM = QtWidgets.QAction(
            'Backtest Details', self, checkable=True)
        viewBtTopM.setChecked(True)
        viewBtTopM.triggered.connect(self.toggleviewBtTopM)
        viewMenu.addAction(viewBtTopM)
        viewBtBottomM = QtWidgets.QAction(
            'Backtest QuotesChart', self, checkable=True)
        viewBtBottomM.setChecked(True)
        viewBtBottomM.triggered.connect(self.toggleviewBtBottomM)
        viewMenu.addAction(viewBtBottomM)

        # help menu
        helpMenu = menubar.addMenu('Help')
        help_contractaction = QtWidgets.QAction('Query Contracts', self)
        help_contractaction.triggered.connect(self.contract_manager.show)
        helpMenu.addAction(help_contractaction)
        help_webaction = QtWidgets.QAction('Web/Jupyter Notebook', self)
        help_webaction.triggered.connect(self.openweb)
        helpMenu.addAction(help_webaction)
        help_action = QtWidgets.QAction('About', self)
        help_action.triggered.connect(self.openabout)
        helpMenu.addAction(help_action)

    def toggleviewmanual(self, state):
        if state:
            self.dockmanual.setVisible(True)
        else:
            self.dockmanual.hide()

    def toggleviewMarketMonitor(self, state):
        if state:
            self.market_window.setVisible(True)
        else:
            self.market_window.hide()

    def toggleviewTradeMonitor(self, state):
        if state:
            self.bottomleft.setVisible(True)
        else:
            self.bottomleft.hide()

    def toggleviewMarketChart(self, state):
        if state:
            self.dataviewindow.setVisible(True)
        else:
            self.dataviewindow.hide()

    def toggleviewCtaManager(self, state):
        if state:
            self.bottomright.setVisible(True)
        else:
            self.bottomright.hide()

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
        a.exec()

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
            self._widget_dict['about'] = AboutWidget(self)
            self._widget_dict['about'].show()

    def openweb(self):
        try:
            self._widget_dict['web'].show()
        except KeyError:
            self._widget_dict['web'] = WebWindow()
            self._widget_dict['web'].show()

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
        tradewidget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        # -------------------------------- Top Left ------------------------------------------#
        # topleft = MarketWindow(self._symbols, self._lang_dict)
        topleft = MarketMonitor(self._events_engine)
        self.market_window = topleft

        # -------------------------------- bottom Left ------------------------------------------#
        bottomleft = QtWidgets.QTabWidget()
        bottomleft.setFont(self._font)
        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()
        tab3 = QtWidgets.QWidget()
        tab4 = QtWidgets.QWidget()
        # tab5 = QtWidgets.QWidget()
        tab6 = QtWidgets.QWidget()
        bottomleft.addTab(tab1, self._lang_dict['Log'])
        bottomleft.addTab(tab2, self._lang_dict['Order'])
        bottomleft.addTab(tab3, self._lang_dict['Fill'])
        bottomleft.addTab(tab4, self._lang_dict['Position'])
        # bottomleft.addTab(tab5, self._lang_dict['ClosePosition'])
        bottomleft.addTab(tab6, self._lang_dict['Account'])

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

        # self.closeposition_window = ClosePositionWindow(self._lang_dict)
        # tab5_layout = QtWidgets.QVBoxLayout()
        # tab5_layout.addWidget(self.closeposition_window)
        # tab5.setLayout(tab5_layout)

        self.account_window = AccountMonitor(self._events_engine)
        tab6_layout = QtWidgets.QVBoxLayout()
        tab6_layout.addWidget(self.account_window)
        tab6.setLayout(tab6_layout)
        self.bottomleft = bottomleft
        # -------------------------------- bottom right ------------------------------------------#
        bottomright = QtWidgets.QFrame()
        bottomright.setFrameShape(QtWidgets.QFrame.StyledPanel)
        bottomright.setFont(self._font)
        strategy_manager_layout = QtWidgets.QFormLayout()
        self.ctastrategywindow = CtaManager()
        self.ctastrategywindow.signal_strategy_out.connect(
            self._outgoing_general_request_handler)
        strategy_manager_layout.addRow(QtWidgets.QLabel('Strategy Manager'))
        strategy_manager_layout.addWidget(self.ctastrategywindow)

        bottomright.setLayout(strategy_manager_layout)
        self.bottomright = bottomright
        # --------------------------------------------------------------------------------------#

        self.dataviewindow = MarketDataView()
        self.market_window.symbol_signal.connect(
            self.dataviewindow.symbol_signal.emit)
        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter1.addWidget(topleft)
        splitter1.addWidget(bottomleft)
        splitter1.setSizes([500, 500])

        splitter2 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(self.dataviewindow)
        splitter2.addWidget(bottomright)
        splitter2.setSizes([500, 500])

        splitter3 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter3.addWidget(splitter1)
        splitter3.addWidget(splitter2)
        splitter3.setSizes([600, 600])

        hbox.addWidget(splitter3)
        tradewidget.setLayout(hbox)

# ---------Backtest ----------------------------------------
        self.backtestwidget = BacktesterManager(self._events_engine)

# --------------------mainwindow----------------------
        manualwidget = ManualWindow(self._config_server['gateway'])
        manualwidget.order_signal.connect(self._outgoing_order_request_handler)
        manualwidget.qry_signal.connect(self._outgoing_qry_request_handler)
        manualwidget.manual_req.connect(self._outgoing_queue.put)
        manualwidget.subscribe_signal.connect(
            self._outgoing_general_request_handler)
        manualwidget.cancelall_signal.connect(
            self._outgoing_general_request_handler)

        self.manual_widget = manualwidget
        dockmanual = QtWidgets.QDockWidget('Manual Control Center', self)
        dockmanual.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        # dockmanual.setFloating(True)
        dockmanual.setAllowedAreas(
            QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dockmanual.setWidget(manualwidget)
        self.dockmanual = dockmanual
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockmanual)

        self.central_widget.addWidget(tradewidget)
        self.central_widget.addWidget(self.backtestwidget)
        self.central_widget.setCurrentIndex(0)
        self.setCentralWidget(self.central_widget)

    #################################################################################################
    # ------------------------------ User Interface End --------------------------------------------#
    #################################################################################################
