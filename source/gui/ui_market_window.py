#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui
import time
from ..common.datastruct import Event, TickData
class MarketWindow(QtWidgets.QTableWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)

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
                       lang_dict['Yesterday_Close'],
                       lang_dict['Open_Price'],
                       lang_dict['High_Price'],
                       lang_dict['Low_Price'],
                       lang_dict['Time'],
                       lang_dict['API']]
        self.init_table()
        self.tick_signal.connect(self.update_table)
        self.itemDoubleClicked.connect(self.show_detail)

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
        self.menu = QtWidgets.QMenu(self)
        save_action = QtWidgets.QAction("保存数据", self)
        # save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)  

    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())      
    
    def show_detail(self,mi):
        row = mi.row()
        symbol = self.item(row, 0).text()
        self.symbol_signal.emit(symbol)

    def update_table(self,tickevent:Event):
        tick = tickevent.data
        if tick.full_symbol in self._symbols:
            row = self._symbols.index(tick.full_symbol)
            timestr = tick.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if (tick.last_price > 0.0):
                try:
                #timestr = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tick.timestamp))
                    self.item(row, 8).setText(timestr)
                    self.item(row, 1).setText(str(tick.last_price))
                    self.item(row, 2).setText(str(tick.volume))
                    self.item(row, 3).setText(str(tick.open_interest))
                    self.item(row, 4).setText(str(tick.pre_close))
                    self.item(row, 5).setText(str(tick.open_price))
                    self.item(row, 6).setText(str(tick.high_price))
                    self.item(row, 7).setText(str(tick.low_price))
                    self.item(row, 9).setText(str(tick.gateway_name))
                except:
                    pass
        else:
            self._symbols.insert(0,tick.full_symbol)
            self.insertRow(0)
            self.setItem(0, 0, QtWidgets.QTableWidgetItem(tick.full_symbol))
            for j in range(1,len(self.header)):
                self.setItem(0, j, QtWidgets.QTableWidgetItem(''))      
            try:
                self.item(0, 1).setText(str(tick.last_price))
                self.item(0, 2).setText(str(tick.volume))
                self.item(0, 3).setText(str(tick.open_interest))
                self.item(0, 4).setText(str(tick.pre_close))
                self.item(0, 5).setText(str(tick.open_price))
                self.item(0, 6).setText(str(tick.high_price))
                self.item(0, 7).setText(str(tick.low_price))
                self.item(0, 8).setText(timestr)
                self.item(0, 9).setText(str(tick.gateway_name))
            except:
                pass
        # self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)


