#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt


import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import datetime
# import itchat
sys.path.insert(0, "../..")


from pystarquant.api.ctp_constant import (
    THOST_FTDC_HF_Speculation,
    THOST_FTDC_HF_Arbitrage,
    THOST_FTDC_HF_Hedge,
    THOST_FTDC_HF_MarketMaker,
    THOST_FTDC_HF_SpecHedge,
    THOST_FTDC_HF_HedgeSpec,
    THOST_FTDC_D_Buy,
    THOST_FTDC_D_Sell,
    THOST_FTDC_OPT_LimitPrice,
    THOST_FTDC_OPT_AnyPrice,
    THOST_FTDC_OF_Open,
    THOST_FTDC_OF_Close,
    THOST_FTDC_OF_CloseToday,
    THOST_FTDC_OF_CloseYesterday,
    THOST_FTDC_OF_ForceOff,
    THOST_FTDC_OF_ForceClose,
    THOST_FTDC_OF_LocalForceClose,
    THOST_FTDC_OPT_BestPrice,
    THOST_FTDC_OPT_LastPrice,
    THOST_FTDC_OPT_AskPrice1,
    THOST_FTDC_OPT_BidPrice1,
    THOST_FTDC_CC_Immediately,
    THOST_FTDC_CC_Touch,
    THOST_FTDC_CC_TouchProfit,
    THOST_FTDC_CC_ParkedOrder,
    THOST_FTDC_CC_LastPriceGreaterThanStopPrice,
    THOST_FTDC_CC_LastPriceLesserThanStopPrice,
    THOST_FTDC_TC_GFS,
    THOST_FTDC_TC_GTD,
    THOST_FTDC_TC_GTC,
    THOST_FTDC_TC_GFA,
    THOST_FTDC_TC_GFD,
    THOST_FTDC_TC_IOC,
    THOST_FTDC_VC_MV,
    THOST_FTDC_VC_AV,
    THOST_FTDC_VC_CV,
    THOST_FTDC_FCC_NotForceClose
)
from pystarquant.common.constant import (
    ESTATE, EventType, MSG_TYPE, SYMBOL_TYPE,
    OrderFlag, OrderType
)
import pystarquant.common.sqglobal as SQGlobal
from pystarquant.common.datastruct import (
    Event,
    OrderData,
    CtpOrderField,
    PaperOrderField,
    QryContractRequest,
    CancelAllRequest,
    SubscribeRequest
)




# @itchat.msg_register(itchat.content.TEXT)
def print_content(msg):
    print(msg['Text'])
    strmsg = str(msg['Text'])
    SQGlobal.wxcmd = strmsg
    # if strmsg.startswith('!SQ:'):
    #     datastruct.wxcmd = strmsg.split(':')[1]
    #     print(datastruct.wxcmd)


class ManualWindow(QtWidgets.QFrame):
    order_signal = QtCore.pyqtSignal(Event)
    subscribe_signal = QtCore.pyqtSignal(Event)
    qry_signal = QtCore.pyqtSignal(Event)
    manual_req = QtCore.pyqtSignal(str)
    cancelall_signal = QtCore.pyqtSignal(Event)
    localorder_signal = QtCore.pyqtSignal(Event)

    def __init__(self, apilist):
        super().__init__()

        # member variables
        self._current_time = None
        self._gwlist = apilist
        self._gwstatusdict = {}
        self._widget_dict = {}

        self.manualorderid = 0
        self.init_gui()
        self.wechat = ItchatThread()
        self.init_wxcmd()

    def wxlogin(self):
        # itchat.auto_login()
        self.wechat.start()

    def sendwxcmd(self, msg):
        self.textbrowser.append(msg)
        if msg.startswith('!SQ:'):
            req = msg.split(':')[1]
            self.manual_req.emit(req)

    def updatestatus(self, index=0):
        key = self.gateway.currentText()
        gwstatus = str(self._gwstatusdict[key].name)
        self.gwstatus.setText(gwstatus)

    def updateapistatusdict(self, info_event):
        key = info_event.source
        state = info_event.data.split('|')[0]
        self._gwstatusdict[key] = ESTATE(int(state))
        self.updatestatus()

    def refresh(self):
        msg2 = '*' \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_STATUS.value)
        self.manual_req.emit(msg2)

    def connect(self):
        msg = self.gateway.currentText() \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_CONNECT.value)
        self.manual_req.emit(msg)

    def disconnect(self):
        msg = self.gateway.currentText() \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_DISCONNECT.value)
        self.manual_req.emit(msg)

    def reset(self):
        msg = self.gateway.currentText() \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_RESET.value)
        self.manual_req.emit(msg)

    def send_cmd(self):
        try:
            cmdstr = str(self.cmd.text())
            self.manual_req.emit(cmdstr)
        except:
            print('send cmd error')

    def subsrcibe(self, ss):
        ss.destination = self.gateway.currentText()
        ss.source = '0'
        self.subscribe_signal.emit(ss)

    def place_order_ctp(self, of):
        try:
            m = Event(EventType.ORDER)
            m.msg_type = MSG_TYPE.MSG_TYPE_ORDER_CTP
            m.destination = self.gateway.currentText()
            m.source = '0'
            ot = OrderType.DEFAULT
            if (of.OrderPriceType == THOST_FTDC_OPT_AnyPrice) and (of.ContingentCondition in [THOST_FTDC_CC_Touch, THOST_FTDC_CC_TouchProfit]):
                ot = OrderType.STP
            elif (of.OrderPriceType == THOST_FTDC_OPT_LimitPrice) and (of.ContingentCondition in [THOST_FTDC_CC_Touch, THOST_FTDC_CC_TouchProfit]):
                ot = OrderType.STPLMT
            elif (of.OrderPriceType == THOST_FTDC_OPT_AnyPrice) and (of.ContingentCondition == THOST_FTDC_CC_Immediately) and (of.TimeCondition == THOST_FTDC_TC_GFD):
                ot = OrderType.MKT
            elif (of.OrderPriceType == THOST_FTDC_OPT_LimitPrice) and (of.ContingentCondition == THOST_FTDC_CC_Immediately) and (of.TimeCondition == THOST_FTDC_TC_GFD):
                ot = OrderType.LMT
            elif (of.ContingentCondition == THOST_FTDC_CC_Immediately) and (of.TimeCondition == THOST_FTDC_TC_IOC) and (of.VolumeCondition == THOST_FTDC_VC_AV):
                ot = OrderType.FAK
            elif (of.ContingentCondition == THOST_FTDC_CC_Immediately) and (of.TimeCondition == THOST_FTDC_TC_IOC) and (of.VolumeCondition == THOST_FTDC_VC_CV):
                ot = OrderType.FOK
            o = OrderData(
                api="CTP.TD",
                account=m.destination[7:],
                clientID=0,
                client_order_id=self.manualorderid,
                type=ot,
                orderfield=of
            )
            # o.api = "CTP.TD"       #self.gateway.currentText()
            # o.account = m.destination[7:]
            # o.clientID = 0
            # o.client_order_id = self.manualorderid
            # # o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            # o.orderfield = of
            m.data = o
            self.order_signal.emit(m)
            self.manualorderid = self.manualorderid + 1
        except:
            print('place ctp order error')

    def place_local_order_ctp(self, of):
        try:
            m = Event(EventType.ORDER)
            m.msg_type = MSG_TYPE.MSG_TYPE_ORDER_CTP
            m.destination = self.gateway.currentText()
            m.source = '0'
            ot = OrderType.LPT
            if of.ContingentCondition in [THOST_FTDC_CC_Touch, THOST_FTDC_CC_TouchProfit]:
                of.ContingentCondition = THOST_FTDC_CC_Immediately
            o = OrderData(
                api="CTP.TD",
                account=m.destination[7:],
                clientID=0,
                client_order_id=self.manualorderid,
                type=ot,
                orderfield=of
            )
            m.data = o
            self.order_signal.emit(m)
            self.manualorderid = self.manualorderid + 1
        except:
            print('place ctp local order error')

    def place_order_paper(self, of):
        try:
            m = Event(EventType.ORDER)
            m.msg_type = MSG_TYPE.MSG_TYPE_ORDER_PAPER
            m.destination = self.gateway.currentText()
            m.source = '0'
            o = OrderData()
            o.api = "PAPER.TD"  # self.api_type.currentText()
            o.account = "manual"
            o.clientID = 0
            o.client_order_id = self.manualorderid
            self.manualorderid = self.manualorderid + 1
            # o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            o.orderfield = of
            m.data = o
            self.order_signal.emit(m)
        except:
            print('place paper order error')

    def qry(self, qa):
        qa.destination = self.gateway.currentText()
        qa.source = '0'
        self.qry_signal.emit(qa)

    def cancelall(self, ca):
        ca.destination = self.gateway.currentText()
        ca.source = '0'
        self.cancelall_signal.emit(ca)

    def init_wxcmd(self):
        self.wechatmsg = ItchatMsgThread()
        # self.wechatmsg.wechatcmd.connect(self._outgoing_queue.put)
        self.wechatmsg.wechatcmd.connect(self.sendwxcmd)
        self.wechatmsg.start()

    def init_gui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        manuallayout = QtWidgets.QFormLayout()
        # manuallayout.addRow(QtWidgets.QLabel('Manual Control Center'))

        self.gateway = QtWidgets.QComboBox()
        self.gateway.addItems([str(element) for element in self._gwlist])
        for api in self._gwlist:
            self._gwstatusdict[str(api)] = ESTATE.STOP

        self.gwstatus = QtWidgets.QLineEdit()
        self.gwstatus.setText('STOP')
        self.gwstatus.setReadOnly(True)
        self.gateway.currentIndexChanged.connect(self.updatestatus)
        self.btn_refresh = QtWidgets.QPushButton('Refresh')
        self.btn_refresh.clicked.connect(self.refresh)

        manualhboxlayout1 = QtWidgets.QHBoxLayout()
        manualhboxlayout1.addWidget(QtWidgets.QLabel('Gateway'))
        manualhboxlayout1.addWidget(self.gateway)

        manualhboxlayout1.addWidget(QtWidgets.QLabel('Status'))
        manualhboxlayout1.addWidget(self.gwstatus)
        manualhboxlayout1.addWidget(self.btn_refresh)
        manuallayout.addRow(manualhboxlayout1)

        self.btn_connect = QtWidgets.QPushButton('Connect')
        self.btn_connect.clicked.connect(self.connect)
        self.btn_disconnect = QtWidgets.QPushButton('Logout')
        self.btn_disconnect.clicked.connect(self.disconnect)
        self.btn_reset = QtWidgets.QPushButton('Reset')
        self.btn_reset.clicked.connect(self.reset)

        manualhboxlayout2 = QtWidgets.QHBoxLayout()
        manualhboxlayout2.addWidget(self.btn_connect)
        manualhboxlayout2.addWidget(self.btn_disconnect)
        manualhboxlayout2.addWidget(self.btn_reset)
        manuallayout.addRow(manualhboxlayout2)

        self.btn_cmd = QtWidgets.QPushButton('User-Defined')
        self.btn_cmd.clicked.connect(self.send_cmd)
        self.cmd = QtWidgets.QLineEdit()
        self.cmd.returnPressed.connect(self.send_cmd)
        manualhboxlayout3 = QtWidgets.QHBoxLayout()
        manualhboxlayout3.addWidget(self.btn_cmd)
        manualhboxlayout3.addWidget(self.cmd)
        manuallayout.addRow(manualhboxlayout3)





        self.api_widget = QtWidgets.QStackedWidget()

        ctpapi = CtpApiWindow()
        ctpapi.subscribe_signal.connect(self.subsrcibe)
        ctpapi.qry_signal.connect(self.qry)
        ctpapi.cancelall_signal.connect(self.cancelall)
        ctpapi.orderfield_signal.connect(self.place_order_ctp)
        ctpapi.local_orderfield_signal.connect(self.place_local_order_ctp)

        xtpapi = XtpApiWindow()
        xtpapi.subscribe_signal.connect(self.subsrcibe)
        xtpapi.qry_signal.connect(self.qry)
        # TODO: change to oes        
        xtpapi.orderfield_signal.connect(self.place_order_paper)

        paperapi = PaperApiWindow()
        paperapi.orderfield_signal.connect(self.place_order_paper)

        self.api_widget.addWidget(ctpapi)
        self.api_widget.addWidget(xtpapi)
        self.api_widget.addWidget(paperapi)
        self.api_widget.setCurrentIndex(0)
        self.gateway.currentIndexChanged.connect(self.set_apiwidget)
        manuallayout.addRow(self.api_widget)

        self.btn_wx_login = QtWidgets.QPushButton('Login')
        self.btn_wx_logout = QtWidgets.QPushButton('Logout')
        self.btn_wx_login.clicked.connect(self.wxlogin)
        # self.btn_wx_logout.clicked.connect(itchat.logout)



        self.textbrowser = QtWidgets.QTextBrowser()
        manuallayout.addRow(self.textbrowser)
        
        manualhboxlayout4 = QtWidgets.QHBoxLayout()
        manualhboxlayout4.addWidget(QtWidgets.QLabel('Wechat Notify'))
        manualhboxlayout4.addWidget(self.btn_wx_login)
        manualhboxlayout4.addWidget(self.btn_wx_logout)
        manuallayout.addRow(manualhboxlayout4)
        # self.logoutput = QtWidgets.QTextBrowser()
        # self.logoutput.setMinimumHeight(400)
        # manuallayout.addRow(self.logoutput)

        self.setLayout(manuallayout)

    def set_apiwidget(self, index=0):
        key = self.gateway.currentText()
        if key.startswith("CTP"):
            self.api_widget.setCurrentIndex(0)
        elif key.startswith("XTP") or key.startswith("OES"):
            self.api_widget.setCurrentIndex(1)
        else:
            self.api_widget.setCurrentIndex(2)


class CtpApiWindow(QtWidgets.QFrame):
    local_orderfield_signal = QtCore.pyqtSignal(CtpOrderField)
    orderfield_signal = QtCore.pyqtSignal(CtpOrderField)
    subscribe_signal = QtCore.pyqtSignal(Event)
    qry_signal = QtCore.pyqtSignal(Event)
    cancelall_signal = QtCore.pyqtSignal(Event)

    def __init__(self):
        super().__init__()
        self.orderfielddict = {}
        self.init_gui()

    def init_gui(self):
        ctpapilayout = QtWidgets.QFormLayout()

        # self.exchange = QtWidgets.QComboBox()
        # self.exchange.addItems(['SHFE','ZCE','DCE','CFFEX','INE'])
        # self.sec_type = QtWidgets.QComboBox()
        # self.sec_type.addItems(['Future', 'Option', 'Combination','Spot'])
        # ctphboxlayout1 = QtWidgets.QHBoxLayout()
        # ctphboxlayout1.addWidget(QtWidgets.QLabel('Exchange'))
        # ctphboxlayout1.addWidget(self.exchange)
        # ctphboxlayout1.addWidget(QtWidgets.QLabel('Security'))
        # ctphboxlayout1.addWidget(self.sec_type)
        # ctpapilayout.addRow(ctphboxlayout1)

        self.qry_type = QtWidgets.QComboBox()
        self.qry_type.addItems(
            ['Account', 'Position', 'Order', 'Trade', 'PositionDetail', 'Contract'])
        self.qry_content = QtWidgets.QLineEdit()
        self.btn_qry = QtWidgets.QPushButton('QUERY')
        self.btn_qry.clicked.connect(self.qry)
        ctphboxlayout0 = QtWidgets.QHBoxLayout()
        ctphboxlayout0.addWidget(QtWidgets.QLabel('Query Type'))
        ctphboxlayout0.addWidget(self.qry_type)
        ctphboxlayout0.addWidget(self.qry_content)
        ctphboxlayout0.addWidget(self.btn_qry)
        ctpapilayout.addRow(ctphboxlayout0)

        self.sym = QtWidgets.QLineEdit()
        self.sym.returnPressed.connect(self.subscribe)  # subscribe market data
        self.order_ref = QtWidgets.QLineEdit()
        self.hedge_type = QtWidgets.QComboBox()
        self.hedge_type.addItems(
            ['Speculation', 'Arbitrage', 'Hedge', 'MarketMaker', 'SpecHedge', 'HedgeSpec'])
        self.orderfielddict['hedge'] = [THOST_FTDC_HF_Speculation, THOST_FTDC_HF_Arbitrage,
                                        THOST_FTDC_HF_Hedge, THOST_FTDC_HF_MarketMaker, THOST_FTDC_HF_SpecHedge, THOST_FTDC_HF_HedgeSpec]
        ctphboxlayout3 = QtWidgets.QHBoxLayout()
        ctphboxlayout3.addWidget(QtWidgets.QLabel('InstrumentID'))
        ctphboxlayout3.addWidget(self.sym)
        ctphboxlayout3.addWidget(QtWidgets.QLabel('Hedge'))
        ctphboxlayout3.addWidget(self.hedge_type)
        # ctphboxlayout3.addWidget(QtWidgets.QLabel('OrderRef'))
        # ctphboxlayout3.addWidget(self.order_ref)
        ctpapilayout.addRow(ctphboxlayout3)

        self.direction_type = QtWidgets.QComboBox()
        self.direction_type.addItems(['Buy', 'Sell'])
        self.orderfielddict['direction'] = [
            THOST_FTDC_D_Buy, THOST_FTDC_D_Sell]
        self.order_flag_type = QtWidgets.QComboBox()
        self.order_flag_type.addItems(
            ['Open', 'Close', 'Force_Close', 'Close_Today', 'Close_Yesterday', 'Force_Off', 'Local_Forceclose'])
        self.orderfielddict['orderflag'] = [THOST_FTDC_OF_Open, THOST_FTDC_OF_Close, THOST_FTDC_OF_ForceClose,
                                            THOST_FTDC_OF_CloseToday, THOST_FTDC_OF_CloseYesterday, THOST_FTDC_OF_ForceOff, THOST_FTDC_OF_LocalForceClose]
        ctphboxlayout4 = QtWidgets.QHBoxLayout()
        ctphboxlayout4.addWidget(QtWidgets.QLabel('Direction'))
        ctphboxlayout4.addWidget(self.direction_type)
        ctphboxlayout4.addWidget(QtWidgets.QLabel('OrderFlag'))
        ctphboxlayout4.addWidget(self.order_flag_type)
        ctpapilayout.addRow(ctphboxlayout4)

        self.order_price_type = QtWidgets.QComboBox()
        self.order_price_type.addItems(
            ['AnyPrice', 'LimitPrice', 'BestPrice', 'LastPrice', 'AskPrice1', 'BidPrice1'])
        self.orderfielddict['pricetype'] = [THOST_FTDC_OPT_AnyPrice, THOST_FTDC_OPT_LimitPrice,
                                            THOST_FTDC_OPT_BestPrice, THOST_FTDC_OPT_LastPrice, THOST_FTDC_OPT_AskPrice1, THOST_FTDC_OPT_BidPrice1]
        self.limit_price = QtWidgets.QLineEdit()
        self.limit_price.setValidator(QtGui.QDoubleValidator())
        self.limit_price.setText('0')
        ctphboxlayout5 = QtWidgets.QHBoxLayout()
        ctphboxlayout5.addWidget(QtWidgets.QLabel('PriceType'))
        ctphboxlayout5.addWidget(self.order_price_type)
        ctphboxlayout5.addWidget(QtWidgets.QLabel('LimitPrice'))
        ctphboxlayout5.addWidget(self.limit_price)
        ctpapilayout.addRow(ctphboxlayout5)

        self.order_quantity = QtWidgets.QLineEdit()
        self.order_quantity.setValidator(QtGui.QIntValidator())
        self.order_quantity.setText('1')
        self.order_minquantity = QtWidgets.QLineEdit()
        self.order_minquantity.setValidator(QtGui.QIntValidator())
        self.order_minquantity.setText('1')
        ctphboxlayout6 = QtWidgets.QHBoxLayout()
        ctphboxlayout6.addWidget(QtWidgets.QLabel('Volume'))
        ctphboxlayout6.addWidget(self.order_quantity)
        ctphboxlayout6.addWidget(QtWidgets.QLabel('MinVolume'))
        ctphboxlayout6.addWidget(self.order_minquantity)
        ctpapilayout.addRow(ctphboxlayout6)

        self.order_condition_type = QtWidgets.QComboBox()
        self.order_condition_type.addItems(
            ['Immediately', 'Touch', 'TouchProfit', 'ParkedOrder', 'LastPriceGreater', 'LastPriceLesser'])
        self.orderfielddict['condition'] = [THOST_FTDC_CC_Immediately, THOST_FTDC_CC_Touch, THOST_FTDC_CC_TouchProfit,
                                            THOST_FTDC_CC_ParkedOrder, THOST_FTDC_CC_LastPriceGreaterThanStopPrice, THOST_FTDC_CC_LastPriceLesserThanStopPrice]
        self.stop_price = QtWidgets.QLineEdit()
        self.stop_price.setValidator(QtGui.QDoubleValidator())
        self.stop_price.setText('0.0')
        ctphboxlayout7 = QtWidgets.QHBoxLayout()
        ctphboxlayout7.addWidget(QtWidgets.QLabel('Condition'))
        ctphboxlayout7.addWidget(self.order_condition_type)
        ctphboxlayout7.addWidget(QtWidgets.QLabel('StopPrice'))
        ctphboxlayout7.addWidget(self.stop_price)
        ctpapilayout.addRow(ctphboxlayout7)

        self.time_condition_type = QtWidgets.QComboBox()
        self.time_condition_type.addItems(
            ['立即或取消', 'GFS', '当日有效', 'GTD', 'GTC', 'GFA'])
        self.orderfielddict['timecondition'] = [THOST_FTDC_TC_IOC, THOST_FTDC_TC_GFS,
                                                THOST_FTDC_TC_GFD, THOST_FTDC_TC_GTD, THOST_FTDC_TC_GTC, THOST_FTDC_TC_GFA]
        self.time_condition_time = QtWidgets.QLineEdit()
        self.volume_condition_type = QtWidgets.QComboBox()
        self.volume_condition_type.addItems(['Any', 'Min', 'Total'])
        self.orderfielddict['volumecondition'] = [
            THOST_FTDC_VC_AV, THOST_FTDC_VC_MV, THOST_FTDC_VC_CV]
        ctphboxlayout8 = QtWidgets.QHBoxLayout()
        ctphboxlayout8.addWidget(QtWidgets.QLabel('TimeCondition'))
        ctphboxlayout8.addWidget(self.time_condition_type)
        ctphboxlayout8.addWidget(self.time_condition_time)
        ctphboxlayout8.addWidget(QtWidgets.QLabel('VolumeCondition'))
        ctphboxlayout8.addWidget(self.volume_condition_type)
        ctpapilayout.addRow(ctphboxlayout8)

        # self.ordertag = QtWidgets.QLineEdit()
        # ctpapilayout.addRow(self.ordertag)

        # self.option_type = QtWidgets.QComboBox()
        # self.option_type.addItems(['Call','Put'])

        # ctpapilayout.addRow(self.btn_request)
        self.request_type = QtWidgets.QComboBox()
        # self.request_type.addItems(['Order','ParkedOrder',
        #     'OrderAction',
        #     'ParkedOrderAction',
        #     'ExecOrder',
        #     'ExecOrderAction',
        #     'ForQuote',
        #     'Quote',
        #     'QuoteAction',
        #     'OptionSelfClose',
        #     'OptionSelfCloseAction',
        #     'CombActionInsert']
        #     )
        self.request_type.addItems(['Order',
                                    'LocalOrder',
                                    'ParkedOrder',
                                    'CancelAll',
                                    'CloseAll',
                                    'Lock']
                                   )
        self.algo_type = QtWidgets.QComboBox()
        self.algo_type.addItems(['None', 'TWAP', 'Iceberg', 'Sniper'])

        ctphboxlayout2 = QtWidgets.QHBoxLayout()
        ctphboxlayout2.addWidget(QtWidgets.QLabel('Request Type'))
        ctphboxlayout2.addWidget(self.request_type)
        ctphboxlayout2.addWidget(QtWidgets.QLabel('Algo-trading Option'))
        ctphboxlayout2.addWidget(self.algo_type)
        ctpapilayout.addRow(ctphboxlayout2)

        self.algoswidgets = QtWidgets.QStackedWidget()
        ctpapilayout.addRow(self.algoswidgets)

        self.btn_request = QtWidgets.QPushButton('REQUEST')
        self.btn_request.clicked.connect(
            self.generate_request)     # insert order
        ctpapilayout.addRow(self.btn_request)

        self.setLayout(ctpapilayout)

    def qry(self):
        qry = Event(EventType.QRY)
        if(self.qry_type.currentText() == 'Account'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_ACCOUNT
        if (self.qry_type.currentText() == 'Position'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_POS
        if (self.qry_type.currentText() == 'Contract'):
            qc = QryContractRequest()
            qc.sym_type = SYMBOL_TYPE.CTP
            qc.content = self.qry_content.text()
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_CONTRACT
            qry.data = qc
        if (self.qry_type.currentText() == 'Order'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_ORDER
        if (self.qry_type.currentText() == 'Trade'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_TRADE
        if (self.qry_type.currentText() == 'PositionDetail'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_POSDETAIL
        self.qry_signal.emit(qry)

    def generate_request(self):
        print("ctp request at ", datetime.now())
        if (self.request_type.currentText() == 'Order'):
            of = CtpOrderField()
            of.InstrumentID = self.sym.text()
            of.OrderPriceType = self.orderfielddict['pricetype'][self.order_price_type.currentIndex(
            )]
            of.Direction = self.orderfielddict['direction'][self.direction_type.currentIndex(
            )]
            of.CombOffsetFlag = self.orderfielddict['orderflag'][self.order_flag_type.currentIndex(
            )]
            of.CombHedgeFlag = self.orderfielddict['hedge'][self.hedge_type.currentIndex(
            )]
            of.TimeCondition = self.orderfielddict['timecondition'][self.time_condition_type.currentIndex(
            )]
            of.GTDDate = self.time_condition_time.text()
            of.VolumeCondition = self.orderfielddict['volumecondition'][self.volume_condition_type.currentIndex(
            )]
            of.ContingentCondition = self.orderfielddict['condition'][self.order_condition_type.currentIndex(
            )]
            of.ForceCloseReason = THOST_FTDC_FCC_NotForceClose
            try:
                of.LimitPrice = float(self.limit_price.text())
                of.VolumeTotalOriginal = int(self.order_quantity.text())
                of.MinVolume = int(self.order_minquantity.text())
                of.StopPrice = float(self.stop_price.text())
            except:
                print('ctp request error,please check numerical field')
                return

            self.orderfield_signal.emit(of)
        elif (self.request_type.currentText() == 'LocalOrder'):
            of = CtpOrderField()
            of.InstrumentID = self.sym.text()
            of.OrderPriceType = self.orderfielddict['pricetype'][self.order_price_type.currentIndex(
            )]
            of.Direction = self.orderfielddict['direction'][self.direction_type.currentIndex(
            )]
            of.CombOffsetFlag = self.orderfielddict['orderflag'][self.order_flag_type.currentIndex(
            )]
            of.CombHedgeFlag = self.orderfielddict['hedge'][self.hedge_type.currentIndex(
            )]
            of.TimeCondition = self.orderfielddict['timecondition'][self.time_condition_type.currentIndex(
            )]
            of.GTDDate = self.time_condition_time.text()
            of.VolumeCondition = self.orderfielddict['volumecondition'][self.volume_condition_type.currentIndex(
            )]
            of.ContingentCondition = self.orderfielddict['condition'][self.order_condition_type.currentIndex(
            )]
            of.ForceCloseReason = THOST_FTDC_FCC_NotForceClose
            try:
                of.LimitPrice = float(self.limit_price.text())
                of.VolumeTotalOriginal = int(self.order_quantity.text())
                of.MinVolume = int(self.order_minquantity.text())
                of.StopPrice = float(self.stop_price.text())
            except:
                print('ctp request error,please check numerical field')
                return
            if of.StopPrice <= 0:
                QtWidgets.QMessageBox().information(
                    None, 'Error', 'Stop Price must be positive number !', QtWidgets.QMessageBox.Ok)
                return
            self.local_orderfield_signal.emit(of)

        elif (self.request_type.currentText() == 'CancelAll'):
            ss = CancelAllRequest()
            ss.sym_type = SYMBOL_TYPE.CTP
            ss.content = str(self.sym.text())
            m = Event(EventType.CANCEL)
            m.msg_type = MSG_TYPE.MSG_TYPE_CANCEL_ALL
            m.data = ss
            self.cancelall_signal.emit(m)

    def subscribe(self):
        ss = SubscribeRequest()
        ss.sym_type = SYMBOL_TYPE.CTP
        ss.content = str(self.sym.text())
        m = Event(EventType.SUBSCRIBE)
        m.msg_type = MSG_TYPE.MSG_TYPE_SUBSCRIBE_MARKET_DATA
        m.data = ss
        self.subscribe_signal.emit(m)


class PaperApiWindow(QtWidgets.QFrame):
    orderfield_signal = QtCore.pyqtSignal(PaperOrderField)

    def __init__(self):
        super().__init__()
        self.orderfielddict = {}
        self.init_gui()

    def init_gui(self):
        paperapilayout = QtWidgets.QFormLayout()

        self.exchange = QtWidgets.QComboBox()
        self.exchange.addItems(['SHFE', 'ZCE', 'DCE', 'CFFEX', 'INE'])
        self.orderfielddict['exchange'] = [
            'SHFE', 'ZCE', 'DCE', 'CFFEX', 'INE']
        self.sec_type = QtWidgets.QComboBox()
        self.sec_type.addItems(['Future', 'Option', 'Spread', 'Stock'])
        self.orderfielddict['sectype'] = ['F', 'O', 'S', 'T']
        paperhboxlayout1 = QtWidgets.QHBoxLayout()
        paperhboxlayout1.addWidget(QtWidgets.QLabel('Exchange'))
        paperhboxlayout1.addWidget(self.exchange)
        paperhboxlayout1.addWidget(QtWidgets.QLabel('Security'))
        paperhboxlayout1.addWidget(self.sec_type)
        paperapilayout.addRow(paperhboxlayout1)

        self.sym = QtWidgets.QLineEdit()
        self.sym_no = QtWidgets.QLineEdit()
        paperhboxlayout2 = QtWidgets.QHBoxLayout()
        paperhboxlayout2.addWidget(QtWidgets.QLabel('SymbolName'))
        paperhboxlayout2.addWidget(self.sym)
        paperhboxlayout2.addWidget(QtWidgets.QLabel('SymbolNo'))
        paperhboxlayout2.addWidget(self.sym_no)
        paperapilayout.addRow(paperhboxlayout2)

        self.order_type = QtWidgets.QComboBox()
        self.order_type.addItems(['MKT', 'LMT', 'STP', 'STPLMT', 'FAK', 'FOK'])
        self.orderfielddict['ordertype'] = [OrderType.MKT, OrderType.LMT,
                                            OrderType.STP, OrderType.STPLMT, OrderType.FAK, OrderType.FOK]
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(['Long', 'Short'])
        self.orderfielddict['direction'] = [1, -1]
        self.order_flag = QtWidgets.QComboBox()
        self.order_flag.addItems(
            ['Open', 'Close', 'Close_Today', 'Close_Yesterday'])
        self.orderfielddict['orderflag'] = [
            OrderFlag.OPEN, OrderFlag.CLOSE, OrderFlag.CLOSE_TODAY, OrderFlag.CLOSE_YESTERDAY]
        paperhboxlayout3 = QtWidgets.QHBoxLayout()
        paperhboxlayout3.addWidget(QtWidgets.QLabel('Order Type'))
        paperhboxlayout3.addWidget(self.order_type)
        paperhboxlayout3.addWidget(QtWidgets.QLabel('Direction'))
        paperhboxlayout3.addWidget(self.direction)
        paperhboxlayout3.addWidget(QtWidgets.QLabel('Order Flag'))
        paperhboxlayout3.addWidget(self.order_flag)
        paperapilayout.addRow(paperhboxlayout3)

        self.limit_price = QtWidgets.QLineEdit()
        self.limit_price.setValidator(QtGui.QDoubleValidator())
        self.limit_price.setText('0.0')
        self.stop_price = QtWidgets.QLineEdit()
        self.stop_price.setText('0.0')
        self.stop_price.setValidator(QtGui.QDoubleValidator())
        self.order_quantity = QtWidgets.QLineEdit()
        self.order_quantity.setValidator(QtGui.QIntValidator())
        self.order_quantity.setText('0')
        paperhboxlayout4 = QtWidgets.QHBoxLayout()
        paperhboxlayout4.addWidget(QtWidgets.QLabel('LimitPrice'))
        paperhboxlayout4.addWidget(self.limit_price)
        paperhboxlayout4.addWidget(QtWidgets.QLabel('StopPrice'))
        paperhboxlayout4.addWidget(self.stop_price)
        paperhboxlayout4.addWidget(QtWidgets.QLabel('Quantity'))
        paperhboxlayout4.addWidget(self.order_quantity)
        paperapilayout.addRow(paperhboxlayout4)

        self.btn_order = QtWidgets.QPushButton('Place_Order')
        self.btn_order.clicked.connect(self.place_order)     # insert order

        paperapilayout.addRow(self.btn_order)

        self.setLayout(paperapilayout)

    def place_order(self):
        sectype = self.orderfielddict['sectype'][self.sec_type.currentIndex()]
        fullname = self.exchange.currentText() + ' ' + sectype + \
            ' ' + str(self.sym.text()).upper() + ' ' + self.sym_no.text()
        o = PaperOrderField()
        o.full_symbol = fullname
        o.order_type = self.orderfielddict['ordertype'][self.order_type.currentIndex(
        )]
        o.order_flag = self.orderfielddict['orderflag'][self.order_flag.currentIndex(
        )]
        try:
            o.order_size = int(self.order_quantity.text(
            )) * self.orderfielddict['direction'][self.direction.currentIndex()]
            o.limit_price = float(self.limit_price.text())
            o.stop_price = float(self.stop_price.text())
        except:
            pass
        self.orderfield_signal.emit(o)

class XtpApiWindow(QtWidgets.QFrame):
    orderfield_signal = QtCore.pyqtSignal(PaperOrderField)
    local_orderfield_signal = QtCore.pyqtSignal(CtpOrderField)

    subscribe_signal = QtCore.pyqtSignal(Event)
    qry_signal = QtCore.pyqtSignal(Event)
    cancelall_signal = QtCore.pyqtSignal(Event)

    def __init__(self):
        super().__init__()
        self.orderfielddict = {}
        self.init_gui()

    def init_gui(self):
        xtpapilayout = QtWidgets.QFormLayout()


        self.qry_type = QtWidgets.QComboBox()
        self.qry_type.addItems(
            ['Account', 'Position', 'Order', 'Trade', 'PositionDetail', 'Ticker'])
        self.qry_content = QtWidgets.QLineEdit()
        self.btn_qry = QtWidgets.QPushButton('Query')
        self.btn_qry.clicked.connect(self.qry)

        xtphboxlayout0 = QtWidgets.QHBoxLayout()
        xtphboxlayout0.addWidget(QtWidgets.QLabel('Query Type'))
        xtphboxlayout0.addWidget(self.qry_type)
        xtphboxlayout0.addWidget(self.qry_content)
        xtphboxlayout0.addWidget(self.btn_qry)
        xtpapilayout.addRow(xtphboxlayout0)

        self.exchange = QtWidgets.QComboBox()
        self.exchange.addItems(['SSE', 'SZSE'])
        self.orderfielddict['exchange'] = ['SSE','SZSE']
        self.sec_type = QtWidgets.QComboBox()
        self.sec_type.addItems(['Stock', 'Fund', 'Bond', 'INDEX','OPTION','TECH_S'])
        self.orderfielddict['sectype'] = ['T', 'F', 'B', 'Z', 'O', 't']
        xtphboxlayout1 = QtWidgets.QHBoxLayout()
        xtphboxlayout1.addWidget(QtWidgets.QLabel('Exchange'))
        xtphboxlayout1.addWidget(self.exchange)
        xtphboxlayout1.addWidget(QtWidgets.QLabel('Security'))
        xtphboxlayout1.addWidget(self.sec_type)
        xtpapilayout.addRow(xtphboxlayout1)

        self.sub_type = QtWidgets.QComboBox()
        self.sub_type.addItems(['MarketData', 'TickByTick', 'OrderBook'])
        self.sym = QtWidgets.QLineEdit()
        self.sym.returnPressed.connect(self.subscribe)
        self.btn_unsubs = QtWidgets.QPushButton('UnSub')
        self.btn_unsubs.clicked.connect(self.unsubscribe)
        self.btn_subs = QtWidgets.QPushButton('Sub')
        self.btn_subs.clicked.connect(self.subscribe)

        xtphboxlayout2 = QtWidgets.QHBoxLayout()
        xtphboxlayout2.addWidget(QtWidgets.QLabel('Ticker'))
        xtphboxlayout2.addWidget(self.sym)
        xtphboxlayout2.addWidget(QtWidgets.QLabel('SubType'))
        xtphboxlayout2.addWidget(self.sub_type)
        xtphboxlayout2.addWidget(self.btn_subs)
        xtphboxlayout2.addWidget(self.btn_unsubs)
        xtpapilayout.addRow(xtphboxlayout2)

        self.order_type = QtWidgets.QComboBox()
        self.order_type.addItems(['MKT', 'LMT', 'STP', 'STPLMT', 'FAK', 'FOK'])
        self.orderfielddict['ordertype'] = [OrderType.MKT, OrderType.LMT,
                                            OrderType.STP, OrderType.STPLMT, OrderType.FAK, OrderType.FOK]
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(['Long', 'Short'])
        self.orderfielddict['direction'] = [1, -1]
        self.order_flag = QtWidgets.QComboBox()
        self.order_flag.addItems(
            ['Open', 'Close', 'Close_T', 'Close_YD'])
        self.orderfielddict['orderflag'] = [
            OrderFlag.OPEN, OrderFlag.CLOSE, OrderFlag.CLOSE_TODAY, OrderFlag.CLOSE_YESTERDAY]
        xtphboxlayout3 = QtWidgets.QHBoxLayout()
        xtphboxlayout3.addWidget(QtWidgets.QLabel('Order Type'))
        xtphboxlayout3.addWidget(self.order_type)
        xtphboxlayout3.addWidget(QtWidgets.QLabel('Direction'))
        xtphboxlayout3.addWidget(self.direction)
        xtphboxlayout3.addWidget(QtWidgets.QLabel('Order Flag'))
        xtphboxlayout3.addWidget(self.order_flag)
        xtpapilayout.addRow(xtphboxlayout3)

        self.limit_price = QtWidgets.QLineEdit()
        self.limit_price.setValidator(QtGui.QDoubleValidator())
        self.limit_price.setText('0.0')
        self.stop_price = QtWidgets.QLineEdit()
        self.stop_price.setText('0.0')
        self.stop_price.setValidator(QtGui.QDoubleValidator())
        self.order_quantity = QtWidgets.QLineEdit()
        self.order_quantity.setValidator(QtGui.QIntValidator())
        self.order_quantity.setText('0')
        xtphboxlayout4 = QtWidgets.QHBoxLayout()
        xtphboxlayout4.addWidget(QtWidgets.QLabel('LimitPrice'))
        xtphboxlayout4.addWidget(self.limit_price)
        xtphboxlayout4.addWidget(QtWidgets.QLabel('StopPrice'))
        xtphboxlayout4.addWidget(self.stop_price)
        xtphboxlayout4.addWidget(QtWidgets.QLabel('Quantity'))
        xtphboxlayout4.addWidget(self.order_quantity)
        xtpapilayout.addRow(xtphboxlayout4)

        self.request_type = QtWidgets.QComboBox()
        self.request_type.addItems(['Order',
                                    'LocalOrder',
                                    'ParkedOrder',
                                    'CancelAll',
                                    'CloseAll']
                                   )
        self.btn_order = QtWidgets.QPushButton('Request')
        self.btn_order.clicked.connect(self.place_order)     # insert order

        xtpapilayout.addRow(self.btn_order)

        self.setLayout(xtpapilayout)

    def qry(self):
        qry = Event(EventType.QRY)
        if(self.qry_type.currentText() == 'Account'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_ACCOUNT
        if (self.qry_type.currentText() == 'Position'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_POS
        if (self.qry_type.currentText() == 'Contract'):
            qc = QryContractRequest()
            qc.sym_type = SYMBOL_TYPE.XTP
            qc.content = self.qry_content.text()
            if not qc.content:
                qc.sym_type = SYMBOL_TYPE.FULL
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_CONTRACT
            qry.data = qc
        if (self.qry_type.currentText() == 'Order'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_ORDER
        if (self.qry_type.currentText() == 'Trade'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_TRADE
        if (self.qry_type.currentText() == 'PositionDetail'):
            qry.msg_type = MSG_TYPE.MSG_TYPE_QRY_POSDETAIL
        self.qry_signal.emit(qry)

    def subscribe(self):
        sectype = self.orderfielddict['sectype'][self.sec_type.currentIndex()]
        ticker = str(self.sym.text()).upper()
        fullname = self.exchange.currentText() + ' ' + sectype + \
            ' ' + ticker + ' 0'
        ss = SubscribeRequest()
        ss.sym_type = SYMBOL_TYPE.XTP
        if not ticker:
            ss.sym_type = SYMBOL_TYPE.FULL
        ss.content = fullname        
        m = Event(EventType.SUBSCRIBE)
        if self.sub_type.currentText() == "MarketData":
            m.msg_type = MSG_TYPE.MSG_TYPE_SUBSCRIBE_MARKET_DATA
        elif self.sub_type.currentText() == 'TickByTick':
            m.msg_type = MSG_TYPE.MSG_TYPE_SUBSCRIBE_ORDER_TRADE        
        m.data = ss
        self.subscribe_signal.emit(m)

    def unsubscribe(self):
        sectype = self.orderfielddict['sectype'][self.sec_type.currentIndex()]
        ticker = str(self.sym.text()).upper()
        fullname = self.exchange.currentText() + ' ' + sectype + \
            ' ' + ticker + ' 0'
        ss = SubscribeRequest()
        ss.sym_type = SYMBOL_TYPE.XTP
        if not ticker:
            ss.sym_type = SYMBOL_TYPE.FULL
        ss.content = fullname        
        m = Event(EventType.SUBSCRIBE)
        if self.sub_type.currentText() == "MarketData":
            m.msg_type = MSG_TYPE.MSG_TYPE_UNSUBSCRIBE
        elif self.sub_type.currentText() == 'TickByTick':
            m.msg_type = MSG_TYPE.MSG_TYPE_UNSUBSCRIBE_ORDER_TRADE        
        m.data = ss
        self.subscribe_signal.emit(m)

    def place_order(self):
        sectype = self.orderfielddict['sectype'][self.sec_type.currentIndex()]
        fullname = self.exchange.currentText() + ' ' + sectype + \
            ' ' + str(self.sym.text()).upper()
        o = PaperOrderField()
        o.full_symbol = fullname
        o.order_type = self.orderfielddict['ordertype'][self.order_type.currentIndex(
        )]
        o.order_flag = self.orderfielddict['orderflag'][self.order_flag.currentIndex(
        )]
        try:
            o.order_size = int(self.order_quantity.text(
            )) * self.orderfielddict['direction'][self.direction.currentIndex()]
            o.limit_price = float(self.limit_price.text())
            o.stop_price = float(self.stop_price.text())
        except:
            pass
        self.orderfield_signal.emit(o)

class ItchatThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        # itchat.run()
        pass


class ItchatMsgThread(QtCore.QThread):
    wechatcmd = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            if (SQGlobal.wxcmd):
                print(SQGlobal.wxcmd)
                self.wechatcmd.emit(SQGlobal.wxcmd)
                SQGlobal.wxcmd = ''
            self.sleep(1)






