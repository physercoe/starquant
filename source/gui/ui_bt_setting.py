#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

from PyQt5 import QtCore, QtWidgets, QtGui

sys.path.insert(0,"../..")
from mystrategy import strategy_list,strategy_list_reload,startstrategy




class BtSettingWindow(QtWidgets.QFrame):
    showresult_signal = QtCore.pyqtSignal(int)
    showanalysis_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        super(BtSettingWindow, self).__init__()

        ## member variables
        self.init_gui()

    def init_gui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        bt_setting_layout = QtWidgets.QFormLayout()
        bt_setting_layout.addRow(QtWidgets.QLabel('Backtest Setting'))

        self.datasource = QtWidgets.QComboBox()
        self.datasource.addItems(['CSV','MongoDB','Tushare'])
        self.datascale = QtWidgets.QComboBox()
        self.datascale.addItems(['Tick','Bar'])
        bt_data_layout = QtWidgets.QHBoxLayout()
        bt_data_layout.addWidget(QtWidgets.QLabel('Data Source'))
        bt_data_layout.addWidget(self.datasource)  
        bt_data_layout.addWidget(QtWidgets.QLabel('Time Scale'))
        bt_data_layout.addWidget(self.datascale)
        bt_setting_layout.addRow(bt_data_layout)

        self.sym = QtWidgets.QLineEdit()
        self.sym_multi = QtWidgets.QLineEdit()
        bt_sym_layout = QtWidgets.QHBoxLayout()
        bt_sym_layout.addWidget(QtWidgets.QLabel('Symbol'))
        bt_sym_layout.addWidget(self.sym)  
        bt_sym_layout.addWidget(QtWidgets.QLabel('Mulitpliers'))
        bt_sym_layout.addWidget(self.sym_multi)
        bt_setting_layout.addRow(bt_sym_layout)

        self.margin = QtWidgets.QLineEdit()
        self.commision = QtWidgets.QLineEdit()
        bt_margin_layout = QtWidgets.QHBoxLayout()
        bt_margin_layout.addWidget(QtWidgets.QLabel('Margin'))
        bt_margin_layout.addWidget(self.margin)  
        bt_margin_layout.addWidget(QtWidgets.QLabel('Commision'))
        bt_margin_layout.addWidget(self.commision)
        bt_setting_layout.addRow(bt_margin_layout)


        self.starttime = QtWidgets.QDateTimeEdit()
        self.starttime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.starttime.setCalendarPopup(True)
        self.endtime = QtWidgets.QDateTimeEdit()
        self.endtime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.endtime.setCalendarPopup(True)
        bt_time_layout = QtWidgets.QHBoxLayout()         
        bt_time_layout.addWidget(QtWidgets.QLabel('Start time'))
        bt_time_layout.addWidget(self.starttime)
        bt_time_layout.addWidget(QtWidgets.QLabel('End time'))
        bt_time_layout.addWidget(self.endtime)
        bt_setting_layout.addRow(bt_time_layout)


        bt_setting_layout.addRow(QtWidgets.QLabel('Strategy Lists'))
        self.strategy_window = BtStrategyWindow()
        self.strategy_window.strategyend_signal.connect(self.showresult_signal.emit)
        bt_setting_layout.addRow(self.strategy_window)



        self.btn_strat_start = QtWidgets.QPushButton('Start_Strat')
        self.btn_strat_start.clicked.connect(self.strategy_window.start_strategy)
        self.btn_strat_stop = QtWidgets.QPushButton('Stop_Strat')
        self.btn_strat_stop.clicked.connect(self.strategy_window.stop_strategy)
        self.btn_strat_reload = QtWidgets.QPushButton('Reload')
        self.btn_strat_reload.clicked.connect(self.strategy_window.reload_strategy)        
        self.btn_showresult = QtWidgets.QPushButton('Show Results')
        self.btn_showresult.clicked.connect(self.update_btresult)

        bt_btn_strat_layout = QtWidgets.QHBoxLayout()
        bt_btn_strat_layout.addWidget(self.btn_strat_start)
        bt_btn_strat_layout.addWidget(self.btn_strat_stop)
        bt_btn_strat_layout.addWidget(self.btn_strat_reload)
        bt_btn_strat_layout.addWidget(self.btn_showresult)        
        bt_setting_layout.addRow(bt_btn_strat_layout)

        self.textoutput = QtWidgets.QTextBrowser() 
        bt_setting_layout.addRow(self.textoutput)          

        verticalSpacer = QtWidgets.QSpacerItem(100, 100, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        bt_setting_layout.addItem(verticalSpacer)
        bt_setting_layout.addRow(QtWidgets.QLabel('Analysis'))

        self.md_starttime = QtWidgets.QDateTimeEdit()
        self.md_starttime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.md_starttime.setCalendarPopup(True)
        self.md_endtime = QtWidgets.QDateTimeEdit()
        self.md_endtime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.md_endtime.setCalendarPopup(True)
        bt_md_time_layout = QtWidgets.QHBoxLayout()         
        bt_md_time_layout.addWidget(QtWidgets.QLabel('Start time'))
        bt_md_time_layout.addWidget(self.md_starttime)
        bt_md_time_layout.addWidget(QtWidgets.QLabel('End time'))
        bt_md_time_layout.addWidget(self.md_endtime)
        bt_setting_layout.addRow(bt_md_time_layout)


        self.md_sym =  QtWidgets.QLineEdit()
        bt_setting_layout.addRow('Symbol',self.md_sym)

        self.md_datasource = QtWidgets.QComboBox()
        self.md_datasource.addItems(['CSV','MongoDB','Tushare'])
        self.md_datascale = QtWidgets.QComboBox()
        self.md_datascale.addItems(['Tick','Bar1M','Bar5M','Bar1H','Bar1D'])
        bt_md_data_layout = QtWidgets.QHBoxLayout()
        bt_md_data_layout.addWidget(QtWidgets.QLabel('Data Source'))
        bt_md_data_layout.addWidget(self.md_datasource)  
        bt_md_data_layout.addWidget(QtWidgets.QLabel('Time Scale'))
        bt_md_data_layout.addWidget(self.md_datascale) 
        bt_setting_layout.addRow(bt_md_data_layout)


        self.btn_showmd = QtWidgets.QPushButton('Show MarketData')
        self.btn_showmd.clicked.connect(self.update_analysis)
        bt_setting_layout.addRow(self.btn_showmd)

        bt_setting_layout.addRow(QtWidgets.QLabel('Optimazation'))


        self.setLayout(bt_setting_layout)

    def update_btresult(self):
        sid = self.strategy_window.sids[self.strategy_window.currentRow()]
        self.showresult_signal.emit(sid)

    def update_analysis(self):
        sid = self.strategy_window.sids[self.strategy_window.currentRow()]
        self.showanalysis_signal.emit(sid)        










class BtStrategyWindow(QtWidgets.QTableWidget):
    strategystart_signal = QtCore.pyqtSignal(int)
    strategyend_signal = QtCore.pyqtSignal(int)
    '''
    Strategy Monitor
    '''
    def __init__(self, parent=None):
        super(BtStrategyWindow, self).__init__(parent)
        
        self.sids =[]
        self._strategy_dict = {}
        self.sid_process_dict = {}
 
        self.header = ['SID',
                       'SName',
                       'SStatus']

        self.init_table()


    def init_table(self):
        for key,value in strategy_list.items():
            strategyClass = value
                # strategy = strategyClass(self._outgoing_request_event_engine,self._order_manager,self._portfolio_manager)
                # strategy.name = key          # assign class name to the strategy
                # for sym in strategy.symbols:
                #     if sym in self._tick_strategy_dict:
                #         self._tick_strategy_dict[sym].append(strategy.id)
                #     else:
                #         self._tick_strategy_dict[sym] = [strategy.id]
                # strategy.active = False
            self._strategy_dict[strategyClass.ID] = strategyClass

        col = len(self.header)
        self.setColumnCount(col)

        self.setHorizontalHeaderLabels(self.header)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

        for key, value in self._strategy_dict.items():
            try:
                self.sids.insert(0,key)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(str(key)))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(value.name)))
                self.setItem(0, 2, QtWidgets.QTableWidgetItem('inactive'))
            except:
                pass

    def add_table(self, row, string):
        pass
    
    def reload_table(self):
        strategy_list_reload()
        self._strategy_dict.clear()
        for key,value in strategy_list.items():
            strategyClass = value
            # strategy = strategyClass(self._outgoing_request_event_engine,self._order_manager,self._portfolio_manager)
            # strategy.name = key          # assign class name to the strategy
            # for sym in strategy.symbols:
            #     if sym in self._tick_strategy_dict:
            #         self._tick_strategy_dict[sym].append(strategy.id)
            #     else:
            #         self._tick_strategy_dict[sym] = [strategy.id]
            # strategy.active = False
            self._strategy_dict[strategyClass.ID] = strategyClass

        for key, value in self._strategy_dict.items():
            try:            
                if key in self.sids:
                    row = self.sids.index(key)
                    self.setItem(row, 1, QtWidgets.QTableWidgetItem(str(value.name)))
                    self.setItem(row, 2, QtWidgets.QTableWidgetItem('inactive'))
                    continue
                self.sids.insert(0,key)
                self.insertRow(0)
                self.setItem(0, 0, QtWidgets.QTableWidgetItem(str(key)))
                self.setItem(0, 1, QtWidgets.QTableWidgetItem(str(value.name)))
                self.setItem(0, 22, QtWidgets.QTableWidgetItem('inactive'))
            except:
                pass
        #倒序删除不存在的策略 
        for i in range(len(self.sids)-1,-1,-1):
            key = self.sids[i]
            if key not in self._strategy_dict:
                self.removeRow(i)
                self.sids.remove(key)

    def update_status(self, row, active):
        sid = int(self.item(row,0).text())
        if active:
            self._strategy_manager.start_strategy(sid)
        else:
            self._strategy_manager.stop_strategy(sid)    
        # self._strategy_manager._strategy_dict[sid].active = active
        self.setItem(row, 7, QtWidgets.QTableWidgetItem('active' if active else 'inactive'))

    def start_strategy(self):
        pass

    def stop_strategy(self):
        pass
    def reload_strategy(self):
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    ui = BtSettingWindow()
    ui.show()
    app.exec_()