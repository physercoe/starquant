#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
import sys
import os
import webbrowser
import psutil
from pathlib import Path
import csv

from queue import Queue, Empty
from PyQt5 import QtCore, QtWidgets, QtGui, QtWebEngineWidgets
from datetime import datetime
import requests
import itchat
from pathlib import Path
import yaml
from typing import TextIO

from source.common.datastruct import * 
from mystrategy import strategy_list
from source.data.data_board import DataBoard
from source.data import database_manager
from source.trade.order_manager import OrderManager
from source.strategy.strategy_manager import StrategyManager
from source.trade.portfolio_manager import PortfolioManager
from source.trade.risk_manager import PassThroughRiskManager
from source.trade.account_manager import AccountManager
from source.engine.live_event_engine import LiveEventEngine
from source.common.client_mq import ClientMq

from .ui_basic import EnumCell,BaseCell
from .ui_market_window import MarketWindow
from .ui_order_window import OrderWindow
from .ui_fill_window import FillWindow
from .ui_position_window import PositionWindow
from .ui_closeposition_window import ClosePositionWindow
from .ui_account_window import AccountWindow
from .ui_strategy_window import StrategyWindow, CtaManager
from .ui_log_window import LogWindow
from .ui_bt_dataview import BtDataViewWidget,BtDataPGChart
from .ui_bt_resultsoverview import BtResultViewWidget
from .ui_bt_posview import BtPosViewWidget
from .ui_bt_txnview import BtTxnViewWidget
from .ui_manual_window import ManualWindow 
from .ui_bt_setting import BtSettingWindow
from .ui_web_window import WebWindow
from .ui_dataview import MarketDataView

from ..api.ctp_constant import THOST_FTDC_PT_Net

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config_server, config_client, lang_dict):
        super(MainWindow, self).__init__()

        ## member variables
        self._current_time = None
        self._config_server = config_server
        self._config_client = config_client
        self._symbols =  config_server['tickers']
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
        self._order_manager = OrderManager()

        ## 1. event engine
        self._outgoing_queue = Queue()                    # outgoing queue from client side
        self._ui_events_engine = LiveEventEngine()        # update ui
        self._outgoing_request_events_engine = LiveEventEngine()          # events/actions request from client
        self._flowrate_timer = QtCore.QTimer()                  #  TODO add task scheduler;produce result_packet

        # 3. data board
        self._data_board = DataBoard()

        # 5. risk manager and compliance manager
        self.risk_manager = PassThroughRiskManager()

        # 6. account manager
        self.account_manager = AccountManager(self._config_server)

        # 7 portfolio manager and position manager
        self.portfolio_manager = PortfolioManager(self._config_client['initial_cash'],self._symbols[:])
        self.contract_manager = ContractManager()
        ## 4. strategy_manager
        self._strategy_manager = StrategyManager(self._config_client, self._outgoing_request_events_engine,self._order_manager,self.portfolio_manager)
        self._strategy_manager.load_strategy()

        ## 8. client mq
        self._client_mq = ClientMq(self._config_server,self._ui_events_engine, self._outgoing_queue)
        
        # 1. set up gui windows
        self.setGeometry(50, 50, 850, 650)
        self.setWindowTitle(lang_dict['Prog_Name'])
        self.setWindowIcon(QtGui.QIcon("source/gui/image/star.png"))       
        self.init_menu()
        self.init_status_bar()  
        self.init_central_area()
 
        ## 9. wire up event handlers
        self._ui_events_engine.register_handler(EventType.TICK, self._tick_event_handler)
        self._ui_events_engine.register_handler(EventType.ORDERSTATUS, self._order_status_event_handler)
        self._ui_events_engine.register_handler(EventType.FILL, self._fill_event_handler)
        self._ui_events_engine.register_handler(EventType.POSITION, self._position_event_handler)
        self._ui_events_engine.register_handler(EventType.ACCOUNT, self._account_event_handler)
        self._ui_events_engine.register_handler(EventType.CONTRACT, self._contract_event_handler)
        self._ui_events_engine.register_handler(EventType.HISTORICAL, self._historical_event_handler)
        self._ui_events_engine.register_handler(EventType.INFO, self._info_event_handler)
        self._ui_events_engine.register_handler(EventType.STRATEGY_CONTROL, self.ctastrategywindow.signal_strategy_in.emit)
        # TODO:add info and error handler

        self._outgoing_request_events_engine.register_handler(EventType.ORDER, self._outgoing_order_request_handler)
        self._outgoing_request_events_engine.register_handler(EventType.QRY_ACCOUNT, self._outgoing_account_request_handler)
        self._outgoing_request_events_engine.register_handler(EventType.QRY_POS, self._outgoing_position_request_handler)
        self._outgoing_request_events_engine.register_handler(EventType.QRY_CONTRACT, self._outgoing_contract_request_handler)        
        self._outgoing_request_events_engine.register_handler(EventType.SUBSCRIBE, self._outgoing_general_request_handler)
        self._outgoing_request_events_engine.register_handler(EventType.GENERAL_REQ, self._outgoing_general_request_handler)
        
        self._flowrate_timer.timeout.connect(self.risk_manager.reset)   #timer event to reset riskmanager flow rate count
        ## 10. start
        self._ui_events_engine.start()
        self._outgoing_request_events_engine.start()
        self._client_mq.start()
        self._flowrate_timer.start(5000)


    #################################################################################################
    # -------------------------------- Event Handler   --------------------------------------------#
    #################################################################################################
    def update_status_bar(self, message):
        self.statusBar().showMessage(message)

    def open_proj_folder(self):
        webbrowser.open('.')

    def reload_strategy(self):
        self._strategy_manager.reload_strategy()
        self.strategy_window.reload_table()

    def start_strategy(self):
        self.strategy_window.update_status(self.strategy_window.currentRow(), True)

    def stop_strategy(self):
        self.strategy_window.update_status(self.strategy_window.currentRow(), False)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        print('closing main window')
        self._ui_events_engine.stop()
        self._outgoing_request_events_engine.stop()
        self._client_mq.stop()

    def _tick_event_handler(self, tick_event):
        self.dataviewindow.tick_signal.emit(tick_event)
        self._current_time = tick_event.data.timestamp
        self._data_board.on_tick(tick_event)       # update databoard
        self._order_manager.on_tick(tick_event)     # check standing stop orders
        self._strategy_manager.on_tick(tick_event)  # feed strategies
        self.market_window.tick_signal.emit(tick_event)         # display
        

    def _order_status_event_handler(self, order_status_event):  # including cancel
        self.order_window.order_status_signal.emit(order_status_event)


    def _fill_event_handler(self, fill_event):
        # self.portfolio_manager.on_fill_live(fill_event)
        # update portfolio manager for pnl
        #self._order_manager.on_fill(fill_event)  # update order manager with fill

        #self._strategy_manager.on_fill(fill_event)  # feed fill to strategy
        #print('fill str')
        self.fill_window.fill_signal.emit(fill_event)     # display
        #print('begin update',fill_event.client_order_id,self._order_manager.retrieve_order(fill_event.client_order_id).order_status)
        #print('fill update')
        #利用fill事件重新更新pos开仓来源，因为有时候回调函数先返回的是pos，然后是fill信息
        #self._strategy_manager.update_position()
        #self.strategy_window.fill_signal.emit(fill_event)

    def _position_event_handler(self, position_event):
        #self.portfolio_manager.on_position_live(position_event)       # position received

        self.position_window.position_signal.emit(position_event)     # display

        #self.closeposition_window.position_signal.emit(position_event)

        #self._strategy_manager.update_position()
        #self._strategy_manager.on_position(position_event)

        #self.strategy_window.position_signal.emit(position_event)


    def _account_event_handler(self, account_event):
        #self.portfolio_manager.on_account(account_event)  # fund info add 
        self.account_window.account_signal.emit(account_event)
        pass

    def _contract_event_handler(self, contract_event):
        contract = contract_event.data
        # self.portfolio_manager.on_contract(contract)
        self.contract_manager.on_contract(contract)
        # msg = "Contract {} tickprice = {} multiples = {}".format(contract.full_symbol,contract.pricetick,contract.size) 
        # self.manual_widget.logoutput.append(msg)

    def _historical_event_handler(self, historical_event):
        pass
        # print(historical_event)

    def _info_event_handler(self,info_event):
        if(info_event.msg_type == MSG_TYPE.MSG_TYPE_INFO_ENGINE_STATUS):
            self.manual_widget.updateapistatusdict(info_event)
        else:
            self.log_window.msg_signal.emit(info_event)

    def _general_event_handler(self, general_event):
        pass
#----------------------------------------outgoing event ------------------------------------
    def _outgoing_order_request_handler(self, o):
        """
         process o, check against risk manager and compliance manager
        """
        self.risk_manager.order_in_compliance(o)  # order pointer; modify order directly
        if (self.risk_manager.passorder()):
            self._order_manager.on_order(o)
            #self.order_window.
            msg = o.serialize()
            print('client send msg: ' + msg,datetime.now())
            # print('client send msg: ' + msg)
            # text = o.destination + o.source + str(o.clientID)
            # requests.get('https://sc.ftqq.com/SCU49995T54cd0bf4d42dd8448359347830d62bd85cc3f69d085ee.send?text=%s &desp=%s'%(text,msg))
            self._outgoing_queue.put(msg)

    def _outgoing_account_request_handler(self, a):
        if (self.risk_manager.passquery()):
            msg = a.serialize()
            print('client send msg: ' + msg)
            self._outgoing_queue.put(msg)

    def _outgoing_position_request_handler(self, p):
        if (self.risk_manager.passquery()):
            msg = p.serialize()
            print('client send msg: ' + msg)
            self._outgoing_queue.put(msg)

    def _outgoing_contract_request_handler(self, c):
        if (self.risk_manager.passquery()):
            msg = c.serialize()
            print('client send msg: ' + msg)
            self._outgoing_queue.put(msg)

    def _outgoing_general_request_handler(self,gr):
        msg = gr.serialize()
        print('client send msg: ' + msg)
        self._outgoing_queue.put(msg)
    
    def _outgoing_general_msg_request_handler(self, g):
        self.log_window.update_table(g)           # append to log window
        
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
        #sys menu --filebrowser
        sysMenu = menubar.addMenu(self._lang_dict['File'])
        sys_folderAction = QtWidgets.QAction(self._lang_dict['Folder'], self)
        sys_folderAction.setStatusTip(self._lang_dict['Open_Folder'])
        sys_folderAction.triggered.connect(self.open_proj_folder)
        sysMenu.addAction(sys_folderAction)
            # --exit
        sysMenu.addSeparator()
        sys_exitAction = QtWidgets.QAction(self._lang_dict['Exit'], self)
        sys_exitAction.setShortcut('Ctrl+Q')
        sys_exitAction.setStatusTip(self._lang_dict['Exit_App'])
        sys_exitAction.triggered.connect(self.close)
        sysMenu.addAction(sys_exitAction)
        #mode menu 
        modeMenu = menubar.addMenu('Mode')
        mode_tradeAction = QtWidgets.QAction('Trade',self)
        mode_tradeAction.triggered.connect(self.displaytrade)
        modeMenu.addAction(mode_tradeAction)
        mode_backtestAction = QtWidgets.QAction('Backtest',self)
        mode_backtestAction.triggered.connect(self.displaybacktest)
        modeMenu.addAction(mode_backtestAction)

        #tool menu
        toolMenu = menubar.addMenu('Tools')
        tool_csvloader = QtWidgets.QAction('CSV Loader',self)
        tool_csvloader.triggered.connect(self.opencsvloader)
        toolMenu.addAction(tool_csvloader)


        #help menu
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

    def opencsvloader(self):
        try:
            self._widget_dict['csvloader'].show()           
        except KeyError:
            self._widget_dict['csvloader'] = CsvLoaderWidget()
            self._widget_dict['csvloader'].show()  


    def openabout(self):
        try:
            self._widget_dict['about'].show()
        except KeyError:
            self._widget_dict['about'] =AboutWidget(self)
            self._widget_dict['about'].show()
    def openweb(self):        
        try:
            self._widget_dict['web'].show()
        except KeyError:
            self._widget_dict['web'] = WebWindow()
            self._widget_dict['web'].show()


    def init_status_bar(self):
        self.statusthread = StatusThread()
        self.statusthread.status_update.connect(self.update_status_bar)
        self.statusthread.start()

    def init_central_area(self):
        self.central_widget = QtWidgets.QStackedWidget()      

#-------Trade Widgets----------
        tradewidget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        #-------------------------------- Top Left ------------------------------------------#
        topleft = MarketWindow(self._symbols, self._lang_dict)
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

        self.log_window = LogWindow(self._lang_dict)
        tab1_layout = QtWidgets.QVBoxLayout()
        tab1_layout.addWidget(self.log_window)
        tab1.setLayout(tab1_layout)

        self.order_window = OrderWindow(self._order_manager,self._outgoing_queue, self._lang_dict)       # cancel_order outgoing nessage
        tab2_layout = QtWidgets.QVBoxLayout()
        tab2_layout.addWidget(self.order_window)
        tab2.setLayout(tab2_layout)

        self.fill_window =FillWindow(self._order_manager, self._lang_dict)
        tab3_layout = QtWidgets.QVBoxLayout()
        tab3_layout.addWidget(self.fill_window)
        tab3.setLayout(tab3_layout)

        self.position_window = PositionWindow(self._lang_dict)
        tab4_layout = QtWidgets.QVBoxLayout()
        tab4_layout.addWidget(self.position_window)
        tab4.setLayout(tab4_layout)

        # self.closeposition_window = ClosePositionWindow(self._lang_dict)
        # tab5_layout = QtWidgets.QVBoxLayout()
        # tab5_layout.addWidget(self.closeposition_window)
        # tab5.setLayout(tab5_layout)

        self.account_window = AccountWindow(self.account_manager, self._lang_dict)
        tab6_layout = QtWidgets.QVBoxLayout()
        tab6_layout.addWidget(self.account_window)
        tab6.setLayout(tab6_layout)

        # -------------------------------- bottom right ------------------------------------------#
        bottomright = QtWidgets.QFrame()
        bottomright.setFrameShape(QtWidgets.QFrame.StyledPanel)
        bottomright.setFont(self._font)
        strategy_manager_layout = QtWidgets.QFormLayout()
        self.ctastrategywindow = CtaManager()
        self.ctastrategywindow.signal_strategy_out.connect(self._outgoing_general_request_handler) 
        # self.strategy_window = StrategyWindow(self._lang_dict, self._strategy_manager)
        # self.btn_strat_reload = QtWidgets.QPushButton(self._lang_dict['Load_Strat'])
        # self.btn_strat_reload.clicked.connect(self.reload_strategy)
        # self.btn_strat_start = QtWidgets.QPushButton(self._lang_dict['Start_Strat'])
        # self.btn_strat_start.clicked.connect(self.start_strategy)
        # self.btn_strat_stop = QtWidgets.QPushButton(self._lang_dict['Stop_Strat'])
        # self.btn_strat_stop.clicked.connect(self.stop_strategy)
        # self.btn_strat_liquidate = QtWidgets.QPushButton(self._lang_dict['Liquidate_Strat'])
        # btn_strat_layout = QtWidgets.QHBoxLayout()
        # btn_strat_layout.addWidget(self.btn_strat_start)
        # btn_strat_layout.addWidget(self.btn_strat_stop)
        # btn_strat_layout.addWidget(self.btn_strat_liquidate)
        # btn_strat_layout.addWidget(self.btn_strat_reload)

        strategy_manager_layout.addRow(QtWidgets.QLabel('Strategy Manager'))
        strategy_manager_layout.addWidget(self.ctastrategywindow)
        # strategy_manager_layout.addRow(btn_strat_layout)
        bottomright.setLayout(strategy_manager_layout)

        # --------------------------------------------------------------------------------------#

        self.dataviewindow = MarketDataView()
        self.market_window.symbol_signal.connect(self.dataviewindow.symbol_signal.emit)

        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter1.addWidget(topleft)
        splitter1.addWidget(bottomleft)
        splitter1.setSizes([500,500])

        splitter2 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(self.dataviewindow)
        splitter2.addWidget(bottomright)
        splitter2.setSizes([400, 400])

        splitter3 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter3.addWidget(splitter1)
        splitter3.addWidget(splitter2)
        splitter3.setSizes([600, 600])

        hbox.addWidget(splitter3)
        tradewidget.setLayout(hbox)

#---------Backtest ----------------------------------------
        backtestwidget = QtWidgets.QWidget()
        bt_hbox = QtWidgets.QHBoxLayout()
      # bt top middle---result
        bt_topmiddle = QtWidgets.QTabWidget()
        bt_resulttab1 = BtResultViewWidget()
        bt_resulttab2 = BtPosViewWidget()
        bt_resulttab3 = BtTxnViewWidget()
        bt_topmiddle.addTab(bt_resulttab1, 'OverView and Returns')
        bt_topmiddle.addTab(bt_resulttab2, 'Position')
        bt_topmiddle.addTab(bt_resulttab3, 'Transactions')
    #  bottom middle:  data
        bt_bottommiddle = QtWidgets.QTabWidget()
        bt_bottommiddle.setFont(self._font)
        bt_datatab1 = BtDataViewWidget()
        bt_datatab2 = BtDataPGChart()
        bt_bottommiddle.addTab(bt_datatab1, 'Data')
        bt_bottommiddle.addTab(bt_datatab2, 'PGData')
      
    #   bt  left: setting
        bt_left = BtSettingWindow()

    #-------------------------------- 
 
        bt_splitter1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        bt_splitter1.addWidget(bt_topmiddle)
        bt_splitter1.addWidget(bt_bottommiddle)
        bt_splitter1.setSizes([400,400])

        # bt_splitter2 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        # bt_splitter2.addWidget(bt_left)
        # bt_splitter2.addWidget(bt_right)
        # bt_splitter2.setSizes([1000, 600])

        bt_splitter3 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        bt_splitter3.addWidget(bt_left)
        bt_splitter3.addWidget(bt_splitter1)
        # bt_splitter3.addWidget(bt_right)
        bt_splitter3.setSizes([300, 1200])

        bt_hbox.addWidget(bt_splitter3)
        backtestwidget.setLayout(bt_hbox)


#--------------------mainwindow----------------------
        manualwidget = ManualWindow(self._config_server['gateway'])
        manualwidget.order_signal.connect(self._outgoing_order_request_handler)
        manualwidget.qryacc_signal.connect(self._outgoing_account_request_handler)
        manualwidget.qrypos_signal.connect(self._outgoing_position_request_handler)
        manualwidget.qrycontract_signal.connect(self._outgoing_contract_request_handler)
        manualwidget.manual_req.connect(self._outgoing_queue.put)
        manualwidget.subscribe_signal.connect(self._outgoing_general_request_handler)
        self.manual_widget = manualwidget
        dockmanual = QtWidgets.QDockWidget('Manual Control Center',self)
        dockmanual.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        # dockmanual.setFloating(True)
        dockmanual.setAllowedAreas(QtCore.Qt.RightDockWidgetArea|QtCore.Qt.LeftDockWidgetArea)
        dockmanual.setWidget(manualwidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea,dockmanual)

        # webwidget = WebWindow()
        # dockweb = QtWidgets.QDockWidget('Web Browser',self)
        # dockweb.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        # # dockweb.setFloating(True)
        # dockweb.setAllowedAreas(QtCore.Qt.RightDockWidgetArea|QtCore.Qt.LeftDockWidgetArea)
        # dockweb.setWidget(webwidget)
        # self.addDockWidget(QtCore.Qt.RightDockWidgetArea,dockweb)   
        # self.tabifyDockWidget(dockmanual,dockweb)
        # dockmanual.raise_()

        self.central_widget.addWidget(tradewidget)
        self.central_widget.addWidget(backtestwidget)
        self.central_widget.setCurrentIndex(0)
        self.setCentralWidget(self.central_widget)

    #################################################################################################
    # ------------------------------ User Interface End --------------------------------------------#
    #################################################################################################

class StatusThread(QtCore.QThread):
    status_update = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            cpuPercent = psutil.cpu_percent()
            memoryPercent = psutil.virtual_memory().percent
            self.status_update.emit('CPU Usage: ' + str(cpuPercent) + '% Memory Usage: ' + str(memoryPercent) + '%')
            self.sleep(1)




class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
    """

    headers = {
        "full_symbol":"全称",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "net_position":"是否净持仓",
        "long_margin_ratio":"多仓保证金率",
        "short_margin_ratio":"空仓保证金率"
    }

    def __init__(self):
        super(ContractManager, self).__init__()

        self.contracts = {}
        self.load_contract()


        self.init_ui()

    def load_contract(self):
        contractfile = Path.cwd().joinpath("etc/ctpcontract.yaml")
        with open(contractfile, encoding='utf8') as fc: 
            contracts = yaml.load(fc)
        print(len(contracts))
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

    def init_ui(self):
        """"""
        self.setWindowTitle("合约查询")
        self.resize(1000, 600)

        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText("输入全称字段（交易所,类别，产品代码，合约编号），留空则查询所有合约")
        self.filter_line.returnPressed.connect(self.show_contracts)
        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def show_contracts(self):
        """
        Show contracts by symbol
        """
        flt = str(self.filter_line.text()).upper()


        if flt:
            contracts = [
                contract for contract in self.contracts.values() if flt in contract.full_symbol
            ]
        else:
            contracts = self.contracts

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value = getattr(contract, name)
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()
    
    def on_contract(self,contract):
        self.contracts[contract.full_symbol] = contract



class CsvLoaderWidget(QtWidgets.QWidget):
    """"""

    def __init__(self):
        """"""
        super().__init__()

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("CSV载入")
        self.setFixedWidth(300)

        self.setWindowFlags(
            (self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
            & ~QtCore.Qt.WindowMaximizeButtonHint)

        file_button = QtWidgets.QPushButton("选择文件")
        file_button.clicked.connect(self.select_file)

        load_button = QtWidgets.QPushButton("载入数据")
        load_button.clicked.connect(self.load_data)

        self.file_edit = QtWidgets.QLineEdit()
        self.symbol_edit = QtWidgets.QLineEdit()

        self.exchange_combo = QtWidgets.QComboBox()
        for i in Exchange:
            self.exchange_combo.addItem(str(i.name), i)

        self.interval_combo = QtWidgets.QComboBox()
        for i in Interval:
            self.interval_combo.addItem(str(i.name), i)

        self.datetime_edit = QtWidgets.QLineEdit("Datetime")
        self.open_edit = QtWidgets.QLineEdit("Open")
        self.high_edit = QtWidgets.QLineEdit("High")
        self.low_edit = QtWidgets.QLineEdit("Low")
        self.close_edit = QtWidgets.QLineEdit("Close")
        self.volume_edit = QtWidgets.QLineEdit("Volume")

        self.format_edit = QtWidgets.QLineEdit("%Y-%m-%d %H:%M:%S")

        info_label = QtWidgets.QLabel("合约信息")
        info_label.setAlignment(QtCore.Qt.AlignCenter)

        head_label = QtWidgets.QLabel("表头信息")
        head_label.setAlignment(QtCore.Qt.AlignCenter)

        format_label = QtWidgets.QLabel("格式信息")
        format_label.setAlignment(QtCore.Qt.AlignCenter)

        form = QtWidgets.QFormLayout()
        form.addRow(file_button, self.file_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(info_label)
        form.addRow("代码", self.symbol_edit)
        form.addRow("交易所", self.exchange_combo)
        form.addRow("周期", self.interval_combo)
        form.addRow(QtWidgets.QLabel())
        form.addRow(head_label)
        form.addRow("时间戳", self.datetime_edit)
        form.addRow("开盘价", self.open_edit)
        form.addRow("最高价", self.high_edit)
        form.addRow("最低价", self.low_edit)
        form.addRow("收盘价", self.close_edit)
        form.addRow("成交量", self.volume_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(format_label)
        form.addRow("时间格式", self.format_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(load_button)

        self.setLayout(form)

    def select_file(self):
        """"""
        result: str = QtWidgets.QFileDialog.getOpenFileName(
            self, filter="CSV (*.csv)")
        filename = result[0]
        if filename:
            self.file_edit.setText(filename)

    def load_data(self):
        """"""
        file_path = self.file_edit.text()
        symbol = self.symbol_edit.text()
        exchange = self.exchange_combo.currentData()
        interval = self.interval_combo.currentData()
        datetime_head = self.datetime_edit.text()
        open_head = self.open_edit.text()
        low_head = self.low_edit.text()
        high_head = self.high_edit.text()
        close_head = self.close_edit.text()
        volume_head = self.volume_edit.text()
        datetime_format = self.format_edit.text()

        start, end, count = self.load(
            file_path,
            symbol,
            exchange,
            interval,
            datetime_head,
            open_head,
            high_head,
            low_head,
            close_head,
            volume_head,
            datetime_format
        )

        msg = f"\
        CSV载入成功\n\
        代码：{symbol}\n\
        交易所：{exchange.value}\n\
        周期：{interval.value}\n\
        起始：{start}\n\
        结束：{end}\n\
        总数量：{count}\n\
        "
        QtWidgets.QMessageBox.information(self, "载入成功！", msg)

    def load_by_handle(
        self,
        f: TextIO,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
    ):
        """
        load by text mode file handle
        """
        reader = csv.DictReader(f)

        bars = []
        start = None
        count = 0
        for item in reader:
            if datetime_format:
                dt = datetime.strptime(item[datetime_head], datetime_format)
            else:
                dt = datetime.fromisoformat(item[datetime_head])

            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=dt,
                interval=interval,
                volume=item[volume_head],
                open_price=item[open_head],
                high_price=item[high_head],
                low_price=item[low_head],
                close_price=item[close_head],
                gateway_name="DB",
            )

            bars.append(bar)

            # do some statistics
            count += 1
            if not start:
                start = bar.datetime
        end = bar.datetime

        # insert into database
        database_manager.save_bar_data(bars)
        return start, end, count

    def load(
        self,
        file_path: str,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
    ):
        """
        load by filename
        """
        with open(file_path, "rt") as f:
            return self.load_by_handle(
                f,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime_head=datetime_head,
                open_head=open_head,
                high_head=high_head,
                low_head=low_head,
                close_head=close_head,
                volume_head=volume_head,
                datetime_format=datetime_format,
            )












class AboutWidget(QtWidgets.QDialog):
    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle('About StarQuant')

        text = u"""
            StarQuant
            易数交易系统
            Lightweight Algorithmic Trading System            
            Language: C++,Python
            Contact: dr.wb@qq.com
            License：MIT

            莫道交易如浪深，莫言策略似沙沉。
            千回万测虽辛苦，实盘验后始得金。
     
            """
        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)            