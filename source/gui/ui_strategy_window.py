#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..position.position_event import PositionEvent
from ..order.fill_event import FillEvent
class StrategyWindow(QtWidgets.QTableWidget):
    position_signal = QtCore.pyqtSignal(type(PositionEvent()))
    fill_signal = QtCore.pyqtSignal(type(FillEvent()))
    '''
    Strategy Monitor
    '''
    def __init__(self, lang_dict, strategy_manager, parent=None):
        super(StrategyWindow, self).__init__(parent)


        self._lang_dict = lang_dict
        self._strategy_manager = strategy_manager

        self.header = [lang_dict['SID'],
                       lang_dict['SName'],
                       lang_dict['nbuyHoldings'],
                       lang_dict['nsellHoldings'],
                       lang_dict['nTrades'],
                       lang_dict['Open_PnL'],
                       lang_dict['Closed_PnL'],
                       lang_dict['SStatus']]
        self.sids =[]
        self.init_table()
        self.position_signal.connect(self.update_table)
        self.fill_signal.connect(self.update_table)

    def init_table(self):
        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

        for key, value in self._strategy_manager._strategy_dict.items():
            try:
                self.sids.insert(0,key)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(str(key)))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(value.name)))
                self.setItem(0, 2, QtWidgets.QTableWidgetItem('0'))
                self.setItem(0, 3, QtWidgets.QTableWidgetItem('0'))               
                self.setItem(0, 4, QtWidgets.QTableWidgetItem('0'))
                self.setItem(0, 5, QtWidgets.QTableWidgetItem('0.0'))
                self.setItem(0, 6, QtWidgets.QTableWidgetItem('0.0'))
                self.setItem(0, 7, QtWidgets.QTableWidgetItem('active' if value.active else 'inactive'))
            except:
                pass

    def update_table(self,updateevent):
         for key in self._strategy_manager._strategy_dict.keys():
            try:
                row = self.sids.index(key)               
                self.setItem(row, 2, QtWidgets.QTableWidgetItem(str(self._strategy_manager.sid_buyqty_dict[key])))
                self.setItem(row, 3, QtWidgets.QTableWidgetItem(str(self._strategy_manager.sid_sellqty_dict[key])))               
                self.setItem(row, 4, QtWidgets.QTableWidgetItem(str(len(self._strategy_manager.sid_oid_dict[key]))))
                self.setItem(row, 5, QtWidgets.QTableWidgetItem(str(self._strategy_manager.sid_openpnl_dict[key])))
                self.setItem(row, 6, QtWidgets.QTableWidgetItem(str(self._strategy_manager.sid_closepnl_dict[key])))
            except:
                pass       

    def add_table(self, row, string):
        pass

    def update_status(self, row, active):
        sid = int(self.item(row,0).text())
        self._strategy_manager._strategy_dict[sid].active = active
        self.setItem(row, 7, QtWidgets.QTableWidgetItem('active' if active else 'inactive'))
