#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import Event

class LogWindow(QtWidgets.QTableWidget):
    msg_signal = QtCore.pyqtSignal(Event)

    def __init__(self, lang_dict, parent=None):
        super(LogWindow, self).__init__(parent)

        self.header = ['Source',
                       'Content',
                       'Time']

        self.init_table()
        self._lang_dict = lang_dict
        self.msg_signal.connect(self.update_table)

    def init_table(self):
        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

    def update_table(self,geneal_event):
        '''
        Only add row
        '''
        if(geneal_event.data.msg):
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(geneal_event.source))
            self.setItem(0, 1, QtWidgets.QTableWidgetItem(geneal_event.data.msg))
            self.setItem(0, 2, QtWidgets.QTableWidgetItem(geneal_event.data.timestamp))
            self.resizeRowsToContents()
            self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

