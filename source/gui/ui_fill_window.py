#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..order.fill_event import FillEvent

class FillWindow(QtWidgets.QTableWidget):
    fill_signal = QtCore.pyqtSignal(type(FillEvent()))

    def __init__(self, order_manager, lang_dict, parent=None):
        super(FillWindow, self).__init__(parent)

        self.header = [lang_dict['OrderID'],
                       lang_dict['FillID'],
                       lang_dict['FullSymbol'],
                       lang_dict['Direction'],
                       lang_dict['Order_Flag'],
                       lang_dict['Fill_Price'],
                       lang_dict['Filled'],
                       lang_dict['Fill_Time'],
                       lang_dict['Account'],
                       lang_dict['API'],
                       lang_dict['SID']]

        self.init_table()
        self._order_manager = order_manager
        self._lang_dict = lang_dict
        self._fillids = []
        self.fill_signal.connect(self.update_table)

    def init_table(self):
        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

    def update_table(self,fill_event):
        '''
        Only add row
        '''
        if fill_event.orderNo in self._fillids:
            row = self._fillids.index(fill_event.orderNo)
            self.item(row, 9).setText(fill_event.fill_time)
            print('received same fill twice')
        else:  # including empty
            try:
                self._fillids.insert(0, fill_event.orderNo)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(fill_event.orderNo))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(fill_event.broker_fill_id)))
                self.setItem(0, 2, QtWidgets.QTableWidgetItem(fill_event.full_symbol))
                self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(self._lang_dict['Long'] if fill_event.fill_size > 0 else self._lang_dict['Short'])))
                self.setItem(0, 4, QtWidgets.QTableWidgetItem(fill_event.fill_flag.name))
                self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(fill_event.fill_price)))
                self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(fill_event.fill_size)))
                self.setItem(0, 7, QtWidgets.QTableWidgetItem(fill_event.fill_time))
                self.setItem(0, 8, QtWidgets.QTableWidgetItem(fill_event.account))
                self.setItem(0, 9, QtWidgets.QTableWidgetItem(fill_event.api))
                self.setItem(0, 10, QtWidgets.QTableWidgetItem(str(fill_event.source)))
            except:
                print('unable to find order that matches this fill')


