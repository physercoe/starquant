#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import PositionEvent,FillEvent


class ClosePositionWindow(QtWidgets.QTableWidget):
    position_signal = QtCore.pyqtSignal(type(PositionEvent()))

    def __init__(self, lang_dict, parent=None):
        super(ClosePositionWindow, self).__init__(parent)

        self.header = [lang_dict['FullSymbol'],
                       lang_dict['Close_Price'],
                       lang_dict['CloseQuantity'],
                       lang_dict['Closed_PnL'],
                       lang_dict['Account'],
                       lang_dict['API'],
                       lang_dict['SID'],
                       lang_dict['Time']]
        self.init_table()
        self._symbols = []
        self._lang_dict = lang_dict
        self.position_signal.connect(self.update_table)

    def init_table(self):
        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

    def update_table(self,position_event):
        if (position_event.type == 'c'):
            self._symbols.insert(0, str(position_event.full_symbol))
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(position_event.full_symbol))
            self.setItem(0, 1, QtWidgets.QTableWidgetItem(str((position_event.average_cost))))
            self.setItem(0, 2, QtWidgets.QTableWidgetItem(str(position_event.size)))
            self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(position_event.realized_pnl)))
            self.setItem(0, 4, QtWidgets.QTableWidgetItem((position_event.account)))
            self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(position_event.closeapi)))
            self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(position_event.closesource)))
            self.setItem(0, 7, QtWidgets.QTableWidgetItem((position_event.timestamp)))
        self.resizeRowsToContents()
    def on_fill(self, fill_evnet):
        pass

