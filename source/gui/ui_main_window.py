#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
import sys
import os
import webbrowser
import psutil
from queue import Queue, Empty
from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import datetime

from source.event.event import *   #EventType
from source.order.order_flag import OrderFlag
from .ui_market_window import MarketWindow
from .ui_order_window import OrderWindow
from .ui_fill_window import FillWindow
from .ui_position_window import PositionWindow
from .ui_closeposition_window import ClosePositionWindow
from .ui_account_window import AccountWindow
from .ui_strategy_window import StrategyWindow
from .ui_log_window import LogWindow
from mystrategy import strategy_list
from source.data.data_board import DataBoard
from source.order.order_manager import OrderManager
from source.strategy.strategy_manager import StrategyManager
from source.position.portfolio_manager import PortfolioManager
from source.risk.risk_manager import PassThroughRiskManager
from source.account.account_manager import AccountManager
from source.event.live_event_engine import LiveEventEngine
from source.event.client_mq import ClientMq
from ..order.order_event import OrderEvent
from ..order.order_type import OrderType
from ..order.order_status import OrderStatus
from .MatplotlibWidget import MatplotlibWidget

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

        ## 4. strategy_manager
        self._strategy_manager = StrategyManager(self._config_client, self._outgoing_request_events_engine,self._order_manager,self.portfolio_manager)
        self._strategy_manager.load_strategy()

        ## 8. client mq
        self._client_mq = ClientMq(self._config_server,self._ui_events_engine, self._outgoing_queue)

        # 1. set up gui windows
        self.setGeometry(50, 50, 600, 400)
        self.setWindowTitle(lang_dict['Prog_Name'])
        self.setWindowIcon(QtGui.QIcon("logo.png"))       
        self.init_menu()
        self.init_status_bar()  
        self.init_central_area()
 
        ## 9. wire up event handlers
        self._ui_events_engine.register_handler(EventType.TICK, self._tick_event_handler)
        self._ui_events_engine.register_handler(EventType.ORDERSTATUS, self.order_window.order_status_signal.emit)
        self._ui_events_engine.register_handler(EventType.FILL, self._fill_event_handler)
        self._ui_events_engine.register_handler(EventType.POSITION, self._position_event_handler)
        self._ui_events_engine.register_handler(EventType.ACCOUNT, self._account_event_handler)
        self._ui_events_engine.register_handler(EventType.CONTRACT, self._contract_event_handler)
        self._ui_events_engine.register_handler(EventType.HISTORICAL, self._historical_event_handler)
        self._ui_events_engine.register_handler(EventType.INFO, self.log_window.msg_signal.emit)
        # TODO:add info and error handler

        self._outgoing_request_events_engine.register_handler(EventType.ORDER, self._outgoing_order_request_handler)
        self._outgoing_request_events_engine.register_handler(EventType.QRY_ACCOUNT, self._outgoing_account_request_handler)
        self._outgoing_request_events_engine.register_handler(EventType.QRY_POS, self._outgoing_position_request_handler)
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

    def send_cmd(self):
        try:
            cmdstr= str(self.cmd.text()) + '|' + str(datetime.now())
            gr = GeneralReqEvent()
            gr.req = cmdstr
            self._outgoing_request_events_engine.put(gr)   
        except:
            print('send cmd error')

    def subsrcibe(self):
        ss = SubscribeEvent()
        echa = ['SHFE','ZCE','DCE','CFFEX','INE','OPTION','SSE']
        stype = ['F','O','T','Z']

        sno = str(self.sym.text())
        sname = str(self.sym_name.text())
        stypeid = self.sec_type.currentIndex()
        echid = self.exchange.currentIndex()
        s = echa[echid] + ' ' + stype[stypeid] + ' ' + sname.upper() + ' ' + sno  #合约全称        
        try:
            ss.api = self.account.currentText()+'_MD'
            ss.content = s
            ss.source = 0
            self._outgoing_request_events_engine.put(ss)
        except:
            print('subsribe error')


    def place_order(self):
        echa = ['SHFE','ZCE','DCE','CFFEX','INE','OPTION','SSE']
        stype = ['F','O','T','Z']

        sno = str(self.sym.text())
        sname = str(self.sym_name.text())
        stypeid = self.sec_type.currentIndex()
        echid = self.exchange.currentIndex()

        s = echa[echid] + ' ' + stype[stypeid] + ' ' + sname.upper() + ' ' + sno  #合约全称
        print(s)
        n = self.direction.currentIndex()
        f = self.order_flag.currentIndex()
        p = str(self.order_price.text())
        q = str(self.order_quantity.text())
        t = self.order_type.currentIndex()
        a = self.account.currentText() + '_TD'
        #print("manual order ",s,n,f,p,q,t)
        # to be checked by risk manger
        try:
            o = OrderEvent()
            o.api = a
            o.source = 0
            o.client_order_id = self.manualorderid
            self.manualorderid = self.manualorderid + 1
            o.full_symbol = s
            o.order_size = int(q) if (n == 0) else -1 * int(q)
            o.order_flag = OrderFlag(f)
            o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            # o.account = self._config_client['account']
            
            if (t == 0):
                o.order_type = OrderType.MKT
                self._outgoing_request_events_engine.put(o)
            elif (t == 1):
                o.order_type = OrderType.LMT
                o.limit_price = float(p)
                self._outgoing_request_events_engine.put(o)
            elif (t == 2):
                o.order_type = OrderType.STP
                self._outgoing_request_events_engine.put(o)
            elif (t == 3):
                o.order_type = OrderType.STPLMT
                o.stop_price = float(p)
                self._outgoing_request_events_engine.put(o)
            else:
                pass
        except:
            print('place order error')


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
        
        self._current_time = tick_event.timestamp

        self._data_board.on_tick(tick_event)       # update databoard
        self._order_manager.on_tick(tick_event)     # check standing stop orders
        # print('tick arrive timestamp:',datetime.now())                       # test latency
        self._strategy_manager.on_tick(tick_event)  # feed strategies
        self.market_window.tick_signal.emit(tick_event)         # display

    def _order_status_event_handler(self, order_status_event):  # including cancel
        # this is moved to ui_thread for consistency
        pass

    def _fill_event_handler(self, fill_event):
        self.portfolio_manager.on_fill_live(fill_event)
        # update portfolio manager for pnl
        self._order_manager.on_fill(fill_event)  # update order manager with fill
        #print('fill orderman')
        self._strategy_manager.on_fill(fill_event)  # feed fill to strategy
        #print('fill str')
        self.fill_window.fill_signal.emit(fill_event)     # display
        #print('begin update',fill_event.client_order_id,self._order_manager.retrieve_order(fill_event.client_order_id).order_status)
        #self.order_window.update_order_status(fill_event.client_order_id,OrderStatus.FILLED )
        #print('fill update')
        #利用fill事件重新更新pos开仓来源，因为有时候回调函数先返回的是pos，然后是fill信息
        self._strategy_manager.update_position()
        self.strategy_window.fill_signal.emit(fill_event)

    def _position_event_handler(self, position_event):
        self.portfolio_manager.on_position_live(position_event)       # position received
        # print("pm on n")
        self.position_window.position_signal.emit(position_event)     # display
        # print("pw on n")
        self.closeposition_window.position_signal.emit(position_event)
        # print("cpw on n")
        self._strategy_manager.update_position()
        self._strategy_manager.on_position(position_event)
        #print("sm on n")
        self.strategy_window.position_signal.emit(position_event)
        #print("sw on n")

    def _account_event_handler(self, account_event):
        self.portfolio_manager.on_account(account_event)  # fund info add 
        self.account_window.account_signal.emit(account_event)
        pass

    def _contract_event_handler(self, contract_event):
        self.portfolio_manager.on_contract(contract_event)

    def _historical_event_handler(self, historical_event):
        print(historical_event)

    def _general_event_handler(self, general_event):
        pass

    def _outgoing_order_request_handler(self, o):
        """
         process o, check against risk manager and compliance manager
        """
        self.risk_manager.order_in_compliance(o)  # order pointer; modify order directly
        if (self.risk_manager.passorder()):
            self._order_manager.on_order(o)
            #self.order_window.
            msg = o.serialize()
            print('client send msg: ' + msg)
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

        #help menu
        helpMenu = menubar.addMenu('Help')
        help_action = QtWidgets.QAction('About', self)
        help_action.triggered.connect(self.openabout)
        helpMenu.addAction(help_action)

    def openabout(self):
        try:
            self._widget_dict['about'].show()
        except KeyError:
            self._widget_dict['about'] =AboutWidget(self)
            self._widget_dict['about'].show()

    def init_status_bar(self):
        self.statusthread = StatusThread()
        self.statusthread.status_update.connect(self.update_status_bar)
        self.statusthread.start()

    def init_central_area(self):
        self.central_widget = QtWidgets.QStackedWidget()      
        # self.central_widget = QtWidgets.QWidget()





#-------Trade Widgets----------
        tradewidget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        #-------------------------------- Top Left ------------------------------------------#
        topleft = MarketWindow(self._symbols, self._lang_dict)
        # self.scrollAreaWidgetContents = QtWidgets.QWidget()
        # self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 763, 967))
        # self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        # topleft = MatplotlibWidget(self.scrollAreaWidgetContents)
        self.market_window = topleft

        # -------------------------------- Top right ------------------------------------------#
        topright = QtWidgets.QFrame()
        topright.setFrameShape(QtWidgets.QFrame.StyledPanel)
        topright.setFont(self._font)
        place_order_layout = QtWidgets.QFormLayout()
        self.sym = QtWidgets.QLineEdit()
        self.sym_name = QtWidgets.QLineEdit()
        self.sec_type = QtWidgets.QComboBox()
        self.sec_type.addItems([self._lang_dict['Future'], self._lang_dict['Option'], self._lang_dict['Stock'],self._lang_dict['Index']])
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems([self._lang_dict['Long'], self._lang_dict['Short']])
        self.order_flag = QtWidgets.QComboBox()
        self.order_flag.addItems([self._lang_dict['Open'], self._lang_dict['Close'], self._lang_dict['Close_Today'],self._lang_dict['Close_Yesterday'], self._lang_dict['Force_Close'],self._lang_dict['Force_Off'],self._lang_dict['Local_Forceclose']])
        self.order_price = QtWidgets.QLineEdit()
        self.order_quantity = QtWidgets.QLineEdit()
        self.order_type = QtWidgets.QComboBox()
        self.order_type.addItems([self._lang_dict['MKT'], self._lang_dict['LMT'], self._lang_dict['STP'],self._lang_dict['STPLMT'],self._lang_dict['FAK'], self._lang_dict['FOK']])
        self.exchange = QtWidgets.QComboBox()
        self.exchange.addItems(['上期所','郑商所','大商所','中金所','能源','期权','上证'])
        self.account = QtWidgets.QComboBox()
        # self.account.addItems(['FROM', 'CONFIG'])
        self.account.addItems([str(element) for element in self._config_server['apis']])
        self.btn_order = QtWidgets.QPushButton(self._lang_dict['Place_Order'])
        self.btn_order.clicked.connect(self.place_order)     # insert order
        self.sym_name.returnPressed.connect(self.subsrcibe) # subscbre market data
        self.sym.returnPressed.connect(self.subsrcibe)  # subscbre market data
        self.cmd = QtWidgets.QLineEdit()
        self.cmd.returnPressed.connect(self.send_cmd)
        self.btn_cmd = QtWidgets.QPushButton('Enter')
        self.btn_cmd.clicked.connect(self.send_cmd)
        
        place_order_layout.addRow(QtWidgets.QLabel(self._lang_dict['Discretionary']))
        place_order_layout.addRow(self._lang_dict['Symbol'], self.sym)
        place_order_layout.addRow(self._lang_dict['Name'], self.sym_name)
        place_order_layout.addRow(self._lang_dict['Security_Type'], self.sec_type)
        place_order_layout.addRow(self._lang_dict['Direction'], self.direction)
        place_order_layout.addRow(self._lang_dict['Order_Flag'], self.order_flag)
        place_order_layout.addRow(self._lang_dict['Price'], self.order_price)
        place_order_layout.addRow(self._lang_dict['Quantity'], self.order_quantity)
        place_order_layout.addRow(self._lang_dict['Order_Type'], self.order_type)
        place_order_layout.addRow(self._lang_dict['Exchange'], self.exchange)
        place_order_layout.addRow(self._lang_dict['Account'], self.account)
        place_order_layout.addRow(self.btn_order)
        place_order_layout.addRow(QtWidgets.QLabel('Console'))
        place_order_layout.addRow('Command',self.cmd)
        place_order_layout.addRow(self.btn_cmd)
        topright.setLayout(place_order_layout)

        # -------------------------------- bottom Left ------------------------------------------#
        bottomleft = QtWidgets.QTabWidget()
        bottomleft.setFont(self._font)
        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()
        tab3 = QtWidgets.QWidget()
        tab4 = QtWidgets.QWidget()
        tab5 = QtWidgets.QWidget()
        tab6 = QtWidgets.QWidget()
        bottomleft.addTab(tab1, self._lang_dict['Log'])
        bottomleft.addTab(tab2, self._lang_dict['Order'])
        bottomleft.addTab(tab3, self._lang_dict['Fill'])
        bottomleft.addTab(tab4, self._lang_dict['Position'])
        bottomleft.addTab(tab5, self._lang_dict['ClosePosition'])
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

        self.closeposition_window = ClosePositionWindow(self._lang_dict)
        tab5_layout = QtWidgets.QVBoxLayout()
        tab5_layout.addWidget(self.closeposition_window)
        tab5.setLayout(tab5_layout)

        self.account_window = AccountWindow(self.account_manager, self._lang_dict)
        tab6_layout = QtWidgets.QVBoxLayout()
        tab6_layout.addWidget(self.account_window)
        tab6.setLayout(tab6_layout)

        # -------------------------------- bottom right ------------------------------------------#
        bottomright = QtWidgets.QFrame()
        bottomright.setFrameShape(QtWidgets.QFrame.StyledPanel)
        bottomright.setFont(self._font)
        strategy_manager_layout = QtWidgets.QFormLayout()
        self.strategy_window = StrategyWindow(self._lang_dict, self._strategy_manager)
        self.btn_strat_reload = QtWidgets.QPushButton(self._lang_dict['Load_Strat'])
        self.btn_strat_reload.clicked.connect(self.reload_strategy)
        self.btn_strat_start = QtWidgets.QPushButton(self._lang_dict['Start_Strat'])
        self.btn_strat_start.clicked.connect(self.start_strategy)
        self.btn_strat_stop = QtWidgets.QPushButton(self._lang_dict['Stop_Strat'])
        self.btn_strat_stop.clicked.connect(self.stop_strategy)
        self.btn_strat_liquidate = QtWidgets.QPushButton(self._lang_dict['Liquidate_Strat'])
        btn_strat_layout = QtWidgets.QHBoxLayout()
        btn_strat_layout.addWidget(self.btn_strat_start)
        btn_strat_layout.addWidget(self.btn_strat_stop)
        btn_strat_layout.addWidget(self.btn_strat_liquidate)
        btn_strat_layout.addWidget(self.btn_strat_reload)

        strategy_manager_layout.addRow(QtWidgets.QLabel(self._lang_dict['Automatic']))
        strategy_manager_layout.addRow(self.strategy_window)
        strategy_manager_layout.addRow(btn_strat_layout)
        bottomright.setLayout(strategy_manager_layout)

        # --------------------------------------------------------------------------------------#
        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(topleft)
        splitter1.addWidget(topright)
        splitter1.setSizes([400,100])

        splitter2 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter2.addWidget(bottomleft)
        splitter2.addWidget(bottomright)
        splitter2.setSizes([400, 100])

        splitter3 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter3.addWidget(splitter1)
        splitter3.addWidget(splitter2)
        splitter3.setSizes([400, 100])

        hbox.addWidget(splitter3)
        tradewidget.setLayout(hbox)
#---------Backtest ----------------------------
        backtestwidget = MarketWindow(self._symbols, self._lang_dict)

        

#--------------------mainwindow----------------------
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


class AboutWidget(QtWidgets.QDialog):
    """显示关于信息"""
    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle('Star Quant')

        text = u"""
            StarQuant
            易数量化交易系统
            Lightweight Algorithmic Trading System            
            Language: C++,Python
            Contact: dr.wb@qq.com
            License：MIT
     
            """
        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)            