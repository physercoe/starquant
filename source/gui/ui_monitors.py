#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from .ui_basic import *

from source.common.datastruct import Event,OrderData,MSG_TYPE,SubscribeRequest   #EventType
from source.common.constant import EventType,ACTIVE_STATUSES,SYMBOL_TYPE





class MarketMonitor(BaseMonitor):

    event_type = EventType.TICK
    data_key = "full_symbol"
    sorting = True

    headers = {
        "full_symbol": {"display": "全称代码", "cell": BaseCell, "update": False},
        "last_price": {"display": "最新价", "cell": BaseCell, "update": True},
        "volume": {"display": "成交量", "cell": BaseCell, "update": True},
        "open_interest": {"display": "持仓量", "cell": BaseCell, "update": True},  
        "pre_close": {"display": "昨收盘价", "cell": BaseCell, "update": True},                
        "open_price": {"display": "开盘价", "cell": BaseCell, "update": True},
        "high_price": {"display": "最高价", "cell": BaseCell, "update": True},
        "low_price": {"display": "最低价", "cell": BaseCell, "update": True},
        "datetime": {"display": "时间", "cell": TimeCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

    symbol_signal = QtCore.pyqtSignal(str)

    def init_ui(self):
        super(MarketMonitor, self).init_ui()
        self.setToolTip("双击单元格显示orderbook")
        self.itemDoubleClicked.connect(self.show_detail)
    
    def init_menu(self):
        super(MarketMonitor, self).init_menu()
        unsubsribe_action = QtWidgets.QAction("取消订阅", self)
        unsubsribe_action.triggered.connect(self.unsubscribe)
        self.menu.addAction(unsubsribe_action)

    def unsubscribe(self):
        cell = self.currentItem()
        if not cell:
            return
        tick = cell.get_data()
        if not tick:
            return
        req = SubscribeRequest(sym_type = SYMBOL_TYPE.FULL,content = tick.full_symbol)
        m = Event(type=EventType.GENERAL_REQ,
            data= req,
            des=tick.gateway_name,
            src='0',
            msgtype=MSG_TYPE.MSG_TYPE_UNSUBSCRIBE)
        self.event_engine.put(m)

    def show_detail(self,cell):
        data = cell.get_data()
        symbol = data["full_symbol"]
        self.symbol_signal.emit(symbol)



class OrderMonitor(BaseMonitor):
    '''
    Order Monitor
    '''


    event_type = EventType.ORDERSTATUS
    data_key = "server_order_id"
    sorting = True

    headers = {
        "account": {"display": "账号", "cell": BaseCell, "update": False},
        "clientID": {"display": "下单客户", "cell": BaseCell, "update": False},
        "full_symbol": {"display": "代码全称", "cell": EnumCell, "update": False},
        "type": {"display": "类型", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "总数量", "cell": BaseCell, "update": True},
        "traded": {"display": "已成交", "cell": BaseCell, "update": True},
        "status": {"display": "状态", "cell": EnumCell, "update": True},
        "create_time": {"display": "创建时间", "cell": BaseCell, "update": True},
        "update_time": {"display": "更新时间", "cell": BaseCell, "update": True},        
        "api": {"display": "接口", "cell": BaseCell, "update": False},
        "client_order_id": {"display": "客户单号", "cell": BaseCell, "update": True}, 
        "server_order_id": {"display": "本地单号", "cell": BaseCell, "update": True}, 
        "orderNo": {"display": "交易所单号", "cell": BaseCell, "update": True}
    }

    def init_menu(self):
        super(OrderMonitor, self).init_menu()
        hide_action =  QtWidgets.QAction("隐藏不活动订单", self)
        hide_action.triggered.connect(self.hide_orders)
        show_action = QtWidgets.QAction("显示所有订单", self)
        show_action.triggered.connect(self.show_orders)
        self.menu.addAction(hide_action)
        self.menu.addAction(show_action)

    def init_ui(self):
        super(OrderMonitor, self).init_ui()
        self.setToolTip("双击单元格撤单")
        self.itemDoubleClicked.connect(self.cancel_order)

    def hide_orders(self):
        for row in range(self.rowCount()):
            cell = self.item(row,0)
            order = cell.get_data()
            if order.status not in ACTIVE_STATUSES:
                self.hideRow(row)
    def show_orders(self):
        for row in range(self.rowCount()):
            cell = self.item(row,0)
            order = cell.get_data()
            if order.status not in ACTIVE_STATUSES:
                self.showRow(row)

    def cancel_order(self,cell):
        order = cell.get_data()
        if not order:
            return
        if order.status not in ACTIVE_STATUSES:
            QtWidgets.QMessageBox().information(None, 'Error','Order not active!',QtWidgets.QMessageBox.Ok)
            return
        req = order.create_cancel_request()
        dest = order.api + '.' + order.account
        m = Event(type=EventType.GENERAL_REQ,data=req,des=dest,src='0',msgtype=MSG_TYPE.MSG_TYPE_CANCEL_ORDER)
        self.event_engine.put(m)


class PositionMonitor(BaseMonitor):
    """
    Monitor for position data.
    """

    event_type = EventType.POSITION
    data_key = "key"
    sorting = True

    headers = {
        "account": {"display": "账号", "cell": BaseCell, "update": False},
        "full_symbol": {"display": "全称", "cell": BaseCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": True},
        "yd_volume": {"display": "昨仓", "cell": BaseCell, "update": True},
        "frozen": {"display": "冻结", "cell": BaseCell, "update": True},
        "price": {"display": "均价", "cell": BaseCell, "update": False},
        "pnl": {"display": "持仓盈亏", "cell": PnlCell, "update": True},
        "realized_pnl": {"display": "平仓盈亏", "cell": PnlCell, "update": True},
        "api": {"display": "接口", "cell": BaseCell, "update": False},
        "timestamp": {"display": "更新时间", "cell": BaseCell, "update": True} 
    }

class AccountMonitor(BaseMonitor):
    """
    Monitor for account data.
    """

    event_type = EventType.ACCOUNT
    data_key = "accountid"
    sorting = True

    headers = {
        "accountid": {"display": "账号", "cell": BaseCell, "update": False},
        "balance": {"display": "余额", "cell": BaseCell, "update": True},
        "yd_balance": {"display": "昨日余额", "cell": BaseCell, "update": True},
        "frozen": {"display": "冻结", "cell": BaseCell, "update": True},
        "available": {"display": "可用", "cell": BaseCell, "update": True},
        "commission": {"display": "手续费", "cell": BaseCell, "update": True},
        "margin": {"display": "保证金", "cell": BaseCell, "update": True},
        "open_pnl": {"display": "持仓盈亏", "cell": BaseCell, "update": True},
        "closed_pnl": {"display": "平仓盈亏", "cell": BaseCell, "update": True},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
        "timestamp": {"display": "更新时间", "cell": BaseCell, "update": True}
    }


class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """

    event_type = EventType.FILL
    data_key = "vt_tradeid"
    sorting = True

    headers = {
        "account": {"display": "账号 ", "cell": BaseCell, "update": False},
        "clientID": {"display": "下单客户", "cell": BaseCell, "update": False},
        "full_symbol": {"display": "合约全称", "cell": BaseCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": False},
        "time": {"display": "时间", "cell": BaseCell, "update": False},
        "commission": {"display": "手续费", "cell": BaseCell, "update": False},
        "api": {"display": "接口", "cell": BaseCell, "update": False},
        "tradeid": {"display": "交易所成交编号", "cell": BaseCell, "update": False},
        "orderNo": {"display": "交易所订单编号", "cell": BaseCell, "update": False},
        "server_order_id": {"display": "本地订单编号", "cell": BaseCell, "update": False},
        "client_order_id": {"display": "客户订单编号", "cell": BaseCell, "update": False}
    }

class LogMonitor(BaseMonitor):
    """
    Monitor for log data.
    """

    event_type = EventType.INFO
    data_key = ""
    sorting = False

    headers = {
        "time": {"display": "时间", "cell": TimeCell, "update": False},
        "msg": {"display": "信息", "cell": MsgCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }
