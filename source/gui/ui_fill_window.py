#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import Event,TradeData

class FillWindow(QtWidgets.QTableWidget):
    fill_signal = QtCore.pyqtSignal(Event)

    def __init__(self, order_manager, lang_dict, parent=None):
        super(FillWindow, self).__init__(parent)

        self.header = ['Account',
                       'ClientID',
                       'FullSymbol',
                       'Direction',
                       'Flag',
                       'Price',
                       'Size',
                       'Time',
                       'Commission',                    
                       'APP',
                       'EXFillID',
                       'EXOrderID',
                       'SQOrderID',
                       'ClientOrderID']

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
        fill = fill_event.data
        if fill.vt_tradeid in self._fillids:
            row = self._fillids.index(fill.vt_tradeid)
            self.item(row, 7).setText(fill.time)
            print('received same fill twice')
        else:  # including empty
            try:
                self._fillids.insert(0, fill.vt_tradeid)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(fill.account))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(fill.clientID)))
                self.setItem(0, 2, QtWidgets.QTableWidgetItem(fill.full_symbol))
                self.setItem(0, 3, QtWidgets.QTableWidgetItem(fill.direction.name))
                self.setItem(0, 4, QtWidgets.QTableWidgetItem(fill.fill_flag.name))
                self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(fill.price)))
                self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(fill.volume)))
                self.setItem(0, 7, QtWidgets.QTableWidgetItem(fill.time))
                self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(fill.commission)))
                self.setItem(0, 9, QtWidgets.QTableWidgetItem(fill.api))
                self.setItem(0, 10, QtWidgets.QTableWidgetItem(str(fill.tradeid)))
                self.setItem(0, 11, QtWidgets.QTableWidgetItem(str(fill.orderNo)))
                self.setItem(0, 12, QtWidgets.QTableWidgetItem(str(fill.server_order_id)))
                self.setItem(0, 13, QtWidgets.QTableWidgetItem(str(fill.client_order_id)))
            except:
                print('unable to find order that matches this fill')
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

