#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import Event,PositionData


class PositionWindow(QtWidgets.QTableWidget):
    position_signal = QtCore.pyqtSignal(Event)

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
                       'Time']

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
        # side = 'b' if position.volume > 0 else 's'

        position = position_event.data
        if (not position.key) :
            return
        if position.key in self._poskey:
            row = self._poskey.index(position.key)
            if (position.volume == 0) and (position.yd_volume == 0):
                self.removeRow(row)
            else:
                self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(position.price)))
                self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(abs(position.volume))))
                self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(position.yd_volume)))
                self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(position.frozen)))
                self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(position.pnl)))
                self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(position.realized_pnl)))
                self.setItem(0, 9, QtWidgets.QTableWidgetItem(position.api))
                self.setItem(0, 10, QtWidgets.QTableWidgetItem(position.timestamp))
        else:
            self._poskey.insert(0, position.key)
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(position.account))
            self.setItem(0, 1, QtWidgets.QTableWidgetItem(position.full_symbol))
            self.setItem(0, 2, QtWidgets.QTableWidgetItem(str(self._lang_dict['Long'] if position.volume > 0 else self._lang_dict['Short'])))
            self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(position.price)))
            self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(abs(position.volume))))
            self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(position.yd_volume)))
            self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(position.frozen)))
            self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(position.pnl)))
            self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(position.realized_pnl)))
            self.setItem(0, 9, QtWidgets.QTableWidgetItem(position.api))
            self.setItem(0, 10, QtWidgets.QTableWidgetItem(position.timestamp))

        
        self.resizeRowsToContents()

    def on_fill(self, fill_evnet):
        pass

