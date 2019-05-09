#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import Event, AccountData

class AccountWindow(QtWidgets.QTableWidget):
    account_signal = QtCore.pyqtSignal(Event)

    def __init__(self, account_manager, lang_dict, parent=None):
        super(AccountWindow, self).__init__(parent)

        self.header = ['AccountID',
                       'Yd_Balance',
                       'Balance',
                       'Available',
                        'Frozen',
                       'Commission',
                       'Margin',
                       'Closed_PnL',
                       'Open_PnL',
                       'API',
                       'Time']

        self.init_table()
        self._account_manager = account_manager
        self._account_ids = []
        self._lang_dict = lang_dict
        self.account_signal.connect(self.update_table)

    def init_table(self):
        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

    def update_table(self,event):
        '''
        Only add row
        '''
        accdata = event.data

        self._account_manager.on_account(accdata)

        if accdata.accountid in self._account_ids:
            row = self._account_ids.index(accdata.accountid)
            self.setItem(row, 1, QtWidgets.QTableWidgetItem(str(accdata.yd_balance)))
            self.setItem(row, 2, QtWidgets.QTableWidgetItem(str(accdata.balance)))
            self.setItem(row, 3, QtWidgets.QTableWidgetItem(str(accdata.available)))
            self.setItem(row, 4, QtWidgets.QTableWidgetItem(str(accdata.frozen)))
            self.setItem(row, 5, QtWidgets.QTableWidgetItem(str(accdata.commission)))
            self.setItem(row, 6, QtWidgets.QTableWidgetItem(str(accdata.margin)))
            self.setItem(row, 7, QtWidgets.QTableWidgetItem(str(accdata.closed_pnl)))
            self.setItem(row, 8, QtWidgets.QTableWidgetItem(str(accdata.open_pnl)))
            self.setItem(row, 9, QtWidgets.QTableWidgetItem(accdata.gateway_name))
            self.setItem(row, 10, QtWidgets.QTableWidgetItem(accdata.timestamp))

        else:
            self._account_ids.insert(0, accdata.accountid)
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(accdata.accountid))
            self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(accdata.yd_balance)))
            self.setItem(0, 2, QtWidgets.QTableWidgetItem(str(accdata.balance)))
            self.setItem(0, 3, QtWidgets.QTableWidgetItem(str(accdata.available)))
            self.setItem(0, 4, QtWidgets.QTableWidgetItem(str(accdata.frozen)))
            self.setItem(0, 5, QtWidgets.QTableWidgetItem(str(accdata.commission)))
            self.setItem(0, 6, QtWidgets.QTableWidgetItem(str(accdata.margin)))
            self.setItem(0, 7, QtWidgets.QTableWidgetItem(str(accdata.closed_pnl)))
            self.setItem(0, 8, QtWidgets.QTableWidgetItem(str(accdata.open_pnl)))
            self.setItem(0, 9, QtWidgets.QTableWidgetItem(accdata.gateway_name))
            self.setItem(0, 10, QtWidgets.QTableWidgetItem(accdata.timestamp))
        
        self.resizeRowsToContents()
