#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
from ..data.tick_event import TickEvent, TickType
import time
class MarketWindow(QtWidgets.QTableWidget):
    tick_signal = QtCore.pyqtSignal(type(TickEvent()))

    def __init__(self, symbols, lang_dict, parent=None):
        super(MarketWindow, self).__init__(parent)
        # self._symbolsshort = {}
        self._symbols = symbols
        # 生成简写和全称之间对应的字典
        # for ticker in self._symbols:
        #     v = ticker.split(' ')
        #     instrumentid = v[2].lower()+v[3]
        #     self._symbolsshort.update({instrumentid:ticker})
        
        self._lang_dict = lang_dict
        self.setFont(lang_dict['font'])
        self.header = [lang_dict['FullSymbol'],
                       lang_dict['Last_Price'],
                       lang_dict['Volume'],
                       lang_dict['Open_Interest'],
                       lang_dict['Bid_Size'],
                       lang_dict['Bid'],
                       lang_dict['Ask'],
                       lang_dict['Ask_Size'],
                       lang_dict['Yesterday_Close'],
                       lang_dict['Open_Price'],
                       lang_dict['High_Price'],
                       lang_dict['Low_Price'],
                       lang_dict['Time'],
                       lang_dict['API']]

        self.init_table()
        self.tick_signal.connect(self.update_table)

    def init_table(self):
        row = len(self._symbols)
        self.setRowCount(row)
        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

        for i in range(row):
            self.setItem(i, 0, QtWidgets.QTableWidgetItem(self._symbols[i]))
            for j in range(1,col):
                self.setItem(i, j, QtWidgets.QTableWidgetItem(0.0))

    def update_table(self,tickevent):
        if tickevent.full_symbol in self._symbols:
            row = self._symbols.index(tickevent.full_symbol)
            # else:
            #     row = self._symbols.index(self._symbolsshort.get(tickevent.full_symbol))
            if (tickevent.price > 0.0):
                #timestr = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tickevent.timestamp))
                timestr = tickevent.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
                self.item(row, 12).setText(timestr)
                if (tickevent.tick_type == TickType.Bid):
                    self.item(row, 4).setText(str(tickevent.size))
                    self.item(row, 5).setText(str(tickevent.price))
                elif (tickevent.tick_type == TickType.Ask):
                    self.item(row, 6).setText(str(tickevent.price))
                    self.item(row, 7).setText(str(tickevent.size))
                elif (tickevent.tick_type == TickType.Trade):
                    self.item(row, 1).setText(str(tickevent.price))
                    self.item(row, 2).setText(str(tickevent.size))
                elif (tickevent.tick_type == TickType.Tick_L1 or tickevent.tick_type == TickType.Tick_L5):
                    self.item(row, 1).setText(str(tickevent.price))
                    self.item(row, 2).setText(str(tickevent.size))
                    self.item(row, 3).setText(str(tickevent.open_interest))
                    self.item(row, 4).setText(str(tickevent.bid_size_L1))
                    self.item(row, 5).setText(str(tickevent.bid_price_L1))
                    self.item(row, 6).setText(str(tickevent.ask_price_L1))
                    self.item(row, 7).setText(str(tickevent.ask_size_L1))
                    self.item(row, 8).setText(str(tickevent.pre_close))
                    self.item(row, 9).setText(str(tickevent.open))
                    self.item(row, 10).setText(str(tickevent.high))
                    self.item(row, 11).setText(str(tickevent.low))
        else:
            self._symbols.insert(0,tickevent.full_symbol)
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(tickevent.full_symbol))
            if(tickevent.tick_type == TickType.Tick_L1 or tickevent.tick_type == TickType.Tick_L5):
                self.item(0, 1).setText(str(tickevent.price))
                self.item(0, 2).setText(str(tickevent.size))
                self.item(0, 3).setText(str(tickevent.open_interest))
                self.item(0, 4).setText(str(tickevent.bid_size_L1))
                self.item(0, 5).setText(str(tickevent.bid_price_L1))
                self.item(0, 6).setText(str(tickevent.ask_price_L1))
                self.item(0, 7).setText(str(tickevent.ask_size_L1))
                self.item(0, 8).setText(str(tickevent.pre_close))
                self.item(0, 9).setText(str(tickevent.open))
                self.item(0, 10).setText(str(tickevent.high))
                self.item(0, 11).setText(str(tickevent.low))



