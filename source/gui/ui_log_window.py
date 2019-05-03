#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..common.datastruct import InfoEvent

class LogWindow(QtWidgets.QTableWidget):
    msg_signal = QtCore.pyqtSignal(type(InfoEvent()))

    def __init__(self, lang_dict, parent=None):
        super(LogWindow, self).__init__(parent)

        self.header = ['Source',
                        'Type',
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
        self.insertRow(0)
        self.setItem(0, 0, QtWidgets.QTableWidgetItem(geneal_event.source ))
        self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(geneal_event.msg_type.name)))
        self.setItem(0, 2, QtWidgets.QTableWidgetItem(geneal_event.content))
        self.setItem(0, 3, QtWidgets.QTableWidgetItem(geneal_event.timestamp ))
        self.resizeRowsToContents()

