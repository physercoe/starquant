#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui

from source.common.datastruct import Event,OrderData,MSG_TYPE   #EventType
class OrderWindow(QtWidgets.QTableWidget):
    '''
    Order Monitor
    '''
    order_status_signal = QtCore.pyqtSignal(Event)

    def __init__(self, order_manager, outgoing_queue, lang_dict, parent=None):
        super(OrderWindow, self).__init__(parent)

        self.header = ['Account',
                       'ClientID',
                       'FullSymbol',
                       'Flag',
                       'Price',
                       'Quantity',
                       'Status',
                       'Create_Time',
                       'Update_Time',
                       'Tag',
                       'API',
                       'ClientOrderID',
                       'SQOrderID',
                       'EXOrderID']

        self.init_table()
        self._orderids = []
        self._order_manager = order_manager
        self._outgoingqueue = outgoing_queue
        self._lang_dict = lang_dict
        self.order_status_signal.connect(self.update_table)

    def init_table(self):
        col = len(self.header)
        self.setColumnCount(col)
        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.itemDoubleClicked.connect(self.cancel_order)

    def update_table(self, order_status_event:Event):
        '''
        If order id exist, update status
        else append one row
        '''
        # update = self._order_manager.on_order_status(order_status_event)
        # print("update order status",update)
        orderstatus = order_status_event.data
        if (True):
            if orderstatus.server_order_id in self._orderids:
                row = self._orderids.index(orderstatus.server_order_id)
                self.item(row, 6).setText(orderstatus.order_status.name)
                self.item(row, 8).setText(orderstatus.update_time)
                self.item(row, 9).setText(orderstatus.tag)
            else:  # including empty
                self._orderids.insert(0, orderstatus.server_order_id)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(orderstatus.account))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(orderstatus.clientID)))
                self.setItem(0, 2, QtWidgets.QTableWidgetItem(orderstatus.full_symbol))
                self.setItem(0, 3, QtWidgets.QTableWidgetItem(orderstatus.flag.name))
                self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(orderstatus.price)))
                self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(orderstatus.volume)))
                self.setItem(0, 6, QtWidgets.QTableWidgetItem(orderstatus.order_status.name))
                self.setItem(0, 7, QtWidgets.QTableWidgetItem(orderstatus.create_time))
                self.setItem(0, 8, QtWidgets.QTableWidgetItem(orderstatus.update_time))
                self.setItem(0, 9, QtWidgets.QTableWidgetItem(orderstatus.tag))
                self.setItem(0, 10, QtWidgets.QTableWidgetItem(orderstatus.api))
                self.setItem(0, 11, QtWidgets.QTableWidgetItem(str(orderstatus.client_order_id)))
                self.setItem(0, 12, QtWidgets.QTableWidgetItem(str(orderstatus.server_order_id)))
                self.setItem(0, 13, QtWidgets.QTableWidgetItem(orderstatus.orderNo))
        self.resizeRowsToContents()

    def cancel_order(self,mi):
        row = mi.row()
        order_id = self.item(row, 12).text()
        order_api = self.item(row,10).text()
        order_acc = self.item(row,0).text()
        order_client = self.item(row,1).text()
        order_cid = self.item(row,11).text()
        msg = order_api + '.TD.' + order_acc + '|0|' + str(MSG_TYPE.MSG_TYPE_CANCEL_ORDER.value) \
             + '|' + order_client + '|' + order_cid + '|' + order_id
        self._outgoingqueue.put(msg)

