#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import PositionEvent,FillEvent


class PositionWindow(QtWidgets.QTableWidget):
    position_signal = QtCore.pyqtSignal(type(PositionEvent()))

    def __init__(self, lang_dict, parent=None):
        super(PositionWindow, self).__init__(parent)

        self.header = ['Account',
                       'FullSymbol',
                       'Direction',
                       'Avg_Price',
                       'Quantity',
                       'Yesterday_Q',
                       'Freezed',
                       'Open_PnL',
                       'Closed_PnL',
                       'API',
                       'Time',
                       'Tag']

        self.init_table()
        self._symbols = []
        self._poskey = []
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
        # side = 'b' if position_event.size > 0 else 's'
        # posfullsym = position_event.full_symbol + ' ' +side
        if (not position_event.key) or ( position_event .type == 'c'):
            return
        if position_event.key in self._poskey:
            if(position_event.type  == 'a' ):
                row = self._poskey.index(position_event.key)
                if (position_event.size == 0):
                    self.removeRow(row)
                else:
                    self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(position_event.average_cost)))
                    self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(abs(position_event.size))))
                    self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(position_event.pre_size)))
                    self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(position_event.freezed_size)))
                    self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(position_event.unrealized_pnl)))
                    self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(position_event.realized_pnl)))
                    self.setItem(0, 9, QtWidgets.QTableWidgetItem(position_event.api))
                    self.setItem(0, 10, QtWidgets.QTableWidgetItem(position_event.timestamp))
                    self.setItem(0, 11, QtWidgets.QTableWidgetItem(position_event.type + position_event.posno ))
            elif(position_event.type == 'n'):
                row = self._poskey.index(position_event.key)
                if (position_event.size == 0):
                    self.removeRow(row)
                else:
                    self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(position_event.average_cost)))
                    self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(abs(position_event.size))))
                    self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(position_event.pre_size)))
                    self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(position_event.freezed_size)))
                    self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(position_event.unrealized_pnl)))
                    self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(position_event.realized_pnl)))
                    self.setItem(0, 9, QtWidgets.QTableWidgetItem(position_event.api))
                    self.setItem(0, 10, QtWidgets.QTableWidgetItem(position_event.timestamp))
                    self.setItem(0, 11, QtWidgets.QTableWidgetItem(position_event.type + position_event.posno ))
            elif(position_event.type == 'u'):
                row = self._poskey.index(position_event.key)
                self.setItem(row, 7, QtWidgets.QTableWidgetItem(str(position_event.unrealized_pnl)))
                self.setItem(row, 10, QtWidgets.QTableWidgetItem(position_event.timestamp))

        else:
            self._poskey.insert(0, position_event.key)
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(position_event.account))
            self.setItem(0, 1, QtWidgets.QTableWidgetItem(position_event.full_symbol))
            self.setItem(0, 2, QtWidgets.QTableWidgetItem(str(self._lang_dict['Long'] if position_event.size > 0 else self._lang_dict['Short'])))
            self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(position_event.average_cost)))
            self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(abs(position_event.size))))
            self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(position_event.pre_size)))
            self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(position_event.freezed_size)))
            self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(position_event.unrealized_pnl)))
            self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(position_event.realized_pnl)))
            self.setItem(0, 9, QtWidgets.QTableWidgetItem(position_event.api))
            self.setItem(0, 10, QtWidgets.QTableWidgetItem(position_event.timestamp))
            self.setItem(0, 11, QtWidgets.QTableWidgetItem(position_event.type + position_event.posno ))


    def on_fill(self, fill_evnet):
        pass

