#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui

from source.common.datastruct import *   #EventType
class OrderWindow(QtWidgets.QTableWidget):
    '''
    Order Monitor
    '''
    order_status_signal = QtCore.pyqtSignal(type(OrderStatusEvent()))

    def __init__(self, order_manager, outgoing_queue, lang_dict, parent=None):
        super(OrderWindow, self).__init__(parent)

        self.header = [lang_dict['OrderID'],
                       lang_dict['FullSymbol'],
                       lang_dict['Direction'],
                       lang_dict['Order_Flag'],
                       lang_dict['Order_Type'],
                       lang_dict['Price'],
                       lang_dict['Quantity'],
                       lang_dict['Filled'],
                       lang_dict['Status'],
                       lang_dict['Order_Time'],
                       lang_dict['Cancel_Time'],
                       lang_dict['API'],
                       lang_dict['Account'],
                       lang_dict['SID']]

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

    def update_table(self, order_status_event):
        '''
        If order id exist, update status
        else append one row
        '''

        
        update = self._order_manager.on_order_status(order_status_event)
        print("update order status",update)
        if (True):
            if order_status_event.server_order_id in self._orderids:
                row = self._orderids.index(order_status_event.server_order_id)
                self.item(row, 10).setText(order_status_event.order_status.name)
            else:  # including empty
                self._orderids.insert(0, order_status_event.server_order_id)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(str(order_status_event.server_order_id)))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(order_status_event.full_symbol))
                self.setItem(0, 2, QtWidgets.QTableWidgetItem(str(self._lang_dict['Long'] if order_status_event.order_size > 0 else self._lang_dict['Short'])))
                self.setItem(0, 3, QtWidgets.QTableWidgetItem(order_status_event.order_flag.name))
                self.setItem(0, 4, QtWidgets.QTableWidgetItem(order_status_event.order_type.name))
                self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(order_status_event.price)))
                self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(abs(order_status_event.order_size))))
                self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(order_status_event.fill_size)))
                self.setItem(0, 8, QtWidgets.QTableWidgetItem(order_status_event.order_status.name))
                self.setItem(0, 9, QtWidgets.QTableWidgetItem(order_status_event.create_time))
                self.setItem(0, 10, QtWidgets.QTableWidgetItem(order_status_event.cancel_time))
                self.setItem(0, 11, QtWidgets.QTableWidgetItem(order_status_event.api))
                self.setItem(0, 12, QtWidgets.QTableWidgetItem(order_status_event.account))
                self.setItem(0, 13, QtWidgets.QTableWidgetItem(str(order_status_event.source)))

    def update_order_status(self, client_order_id, order_status):
        #if client_order_id in self._orderids:
        #print('row 83')
        row = self._orderids.index(client_order_id)
        #print('row',row)
        self.item(row, 10).setText(order_status.name)
        #print('row 90' )
    def cancel_order(self,mi):
        row = mi.row()
        order_id = self.item(row, 0).text()
        order_api = self.item(row,11).text()
        msg = order_api + '|0|' + str(MSG_TYPE.MSG_TYPE_CANCEL_ORDER.value) + '|' + order_id
        self._outgoingqueue.put(msg)

