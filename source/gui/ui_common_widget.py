"""
Basic widgets for VN Trader.
"""

import csv
from enum import Enum
from typing import Any
import psutil
from PyQt5 import QtCore, QtGui, QtWidgets,QtWebEngineWidgets
import yaml
from typing import TextIO
from datetime import datetime,timedelta
from pathlib import Path
import csv,json
from copy import copy
import webbrowser
from threading import Thread
from time import time as ttime
import gzip
import io
from ..common.constant import (
    Exchange,Interval,Product,PRODUCT_CTP2VT,OPTIONTYPE_CTP2VT,
    EventType
    )
from ..common.datastruct import (
    Event,MSG_TYPE,
    TickData,BarData,HistoryRequest,ContractData
)
from ..engine.iengine import EventEngine
from source.data import database_manager
from source.data.rqdata import rqdata_client
from ..common.utility import (
    load_json, save_json,generate_full_symbol,extract_full_symbol
    )    
from ..common.config import SETTING_FILENAME, SETTINGS
from ..api.ctp_constant import THOST_FTDC_PT_Net
from source.common import sqglobal
from .ui_basic import EnumCell,BaseCell

class WebWindow(QtWidgets.QFrame):


    def __init__(self):
        super(WebWindow, self).__init__()

        ## member variables
        self.init_gui()

    def init_gui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel) 
        weblayout = QtWidgets.QFormLayout()

        self.web =  QtWebEngineWidgets.QWebEngineView()
        self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.web.setMinimumHeight(1000)
        # self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        # self.web.setMinimumWidth(1000)
        self.web.load(QtCore.QUrl("http://localhost:8888"))

        self.web_addr = QtWidgets.QLineEdit()
        self.web_btn_jn = QtWidgets.QPushButton('Jupyter Notebook') 
        self.web_btn_jn.clicked.connect(lambda:self.web.load(QtCore.QUrl("http://localhost:8888")))
        self.web_btn_go = QtWidgets.QPushButton('Go') 
        self.web_btn_go.clicked.connect(lambda:self.web.load(QtCore.QUrl(self.web_addr.text())))
        
        webhboxlayout1 = QtWidgets.QHBoxLayout()
        webhboxlayout1.addWidget(self.web_btn_jn)
        webhboxlayout1.addWidget(QtWidgets.QLabel('Web'))
        webhboxlayout1.addWidget(self.web_addr)
        webhboxlayout1.addWidget(self.web_btn_go)

        weblayout.addRow(webhboxlayout1)
        weblayout.addRow(self.web)
        self.setLayout(weblayout)


class CsvTickLoader(QtCore.QObject):
    startsig = QtCore.pyqtSignal(str)
    finishmsg = QtCore.pyqtSignal(str)
    def __init__(self,
        file_path: str,
        symbol: str,
        exchange: Exchange,
        datetime_head: str,
        lastprice_head:str,
        volume_head: str,
        openinterest_head: str,
        askprice1_head: str,
        askvolume1_head: str,
        bidprice1_head:str,
        bidvolume1_head: str,
        datetime_format: str,
        saveto:str='DataBase'):
        super(CsvTickLoader,self).__init__()
        self.file_path = file_path
        self.symbol = symbol
        self.exchange = exchange
        self.datetime_head = datetime_head
        self.lastprice_head = lastprice_head
        self.volume_head = volume_head
        self.openinterest_head = openinterest_head
        self.askprice1_head = askprice1_head
        self.askvolume1_head = askvolume1_head
        self.bidprice1_head = bidprice1_head
        self.bidvolume1_head = bidvolume1_head
        self.datetime_format = datetime_format
        self.saveto = saveto
        self.startsig.connect(self.run)

    # @QtCore.pyqtSlot()
    def run(self,suffix:str = 'csv'):
        if suffix == 'csv':
            with open(self.file_path, "rt") as f:
                self.load_tick_by_handle(f)
        elif suffix == 'csv.gz':
            with gzip.open(self.file_path,'rt') as f:
                self.load_tick_by_handle(f)

    def load_tick_by_handle(self, f: TextIO):
        """
        load by text mode file handle
        """
        reader = csv.DictReader(f)

        ticks = []
        start = None
        count = 0
        full_sym = generate_full_symbol(self.exchange,self.symbol)
        alreadyhas = bool(sqglobal.history_tick[full_sym])        
        starttime = ttime()
        try:
            for item in reader:                
                if self.datetime_format:
                    dt = datetime.strptime(item[self.datetime_head], self.datetime_format)
                else:
                    dt = datetime.fromisoformat(item[self.datetime_head])

                tick = TickData(
                    symbol=self.symbol,
                    exchange=self.exchange,
                    datetime=dt,
                    volume=int(item[self.volume_head]),
                    last_price=float(item[self.lastprice_head]),
                    open_interest=int(item[self.openinterest_head]),
                    ask_price_1=float(item[self.askprice1_head]),
                    ask_volume_1=int(item[self.askvolume1_head]),
                    bid_price_1=float(item[self.bidprice1_head]),
                    bid_volume_1=int(item[self.bidvolume1_head]),
                    depth=1,                
                    gateway_name="DB",
                )
                ticks.append(tick)

                # do some statistics
                count += 1
                if not start:
                    start = tick.datetime
                if count % 100000 == 0:
                    if self.saveto == 'DataBase': 
                        database_manager.save_tick_data(ticks)
                        ticks.clear()
        except Exception as e:
            msg = "Load csv error: {0}".format(str(e.args[0]))
            self.finishmsg.emit(msg)
            return

        end = tick.datetime
        if self.saveto == 'Memory' and not alreadyhas:
            sqglobal.history_tick[full_sym] = ticks 
        elif self.saveto == 'DataBase': 
            database_manager.save_tick_data(ticks)         
        endtime = ttime()
        totalloadtime = int(endtime-starttime)
        if start and end and count:
            msg = f"\
                CSV载入Tick成功\n\
                代码：{self.symbol}\n\
                交易所：{self.exchange.value}\n\
                起始：{start}\n\
                结束：{end}\n\
                总数量：{count}\n\
                耗时：{totalloadtime}s\n\
                "
            self.finishmsg.emit(msg)


class CsvBarLoader(QtCore.QObject):
    startsig = QtCore.pyqtSignal(str)
    finishmsg = QtCore.pyqtSignal(str)
    def __init__(self,
        file_path: str,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
        saveto:str='DataBase'):
        super(CsvBarLoader,self).__init__()
        self.file_path = file_path
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval
        self.datetime_head = datetime_head
        self.open_head = open_head
        self.high_head = high_head
        self.low_head = low_head
        self.close_head = close_head
        self.volume_head = volume_head
        self.datetime_format = datetime_format
        self.saveto = saveto
        self.startsig.connect(self.run)

    # @QtCore.pyqtSlot()
    def run(self,suffix:str = 'csv'):
        if suffix == 'csv':
            with open(self.file_path, "rt") as f:
                self.load_by_handle(f)
        elif suffix == 'csv.gz':
            with gzip.open(self.file_path,"rt") as f:
                self.load_by_handle(f)

    def load_by_handle(self, f: TextIO):
        """
        load by text mode file handle
        """
        reader = csv.DictReader(f)

        bars = []
        start = None
        count = 0
        full_sym = generate_full_symbol(self.exchange,self.symbol)
        alreadyhas = bool(sqglobal.history_bar[full_sym])        
        starttime = ttime()
        try:
            for item in reader:
                if self.datetime_format:
                    dt = datetime.strptime(item[self.datetime_head], self.datetime_format)
                else:
                    dt = datetime.fromisoformat(item[self.datetime_head])

                bar = BarData(
                    symbol=self.symbol,
                    exchange=self.exchange,
                    datetime=dt,
                    interval=self.interval,
                    volume=int(item[self.volume_head]),
                    open_price=float(item[self.open_head]),
                    high_price=float(item[self.high_head]),
                    low_price=float(item[self.low_head]),
                    close_price=float(item[self.close_head]),
                    gateway_name="DB",
                )

                bars.append(bar)

                # do some statistics
                count += 1
                if not start:
                    start = bar.datetime
                if count % 100000 == 0:
                    if self.saveto == 'DataBase': 
                        database_manager.save_bar_data(bars)
                        bars.clear()
        except Exception as e:
            msg = "Load csv error: {0}".format(str(e.args[0]))
            self.finishmsg.emit(msg)
            return

        end = bar.datetime
        # insert into database

        if self.saveto == 'Memory' and not alreadyhas:
            sqglobal.history_bar[full_sym] = bars
        elif self.saveto == 'DataBase': 
            database_manager.save_bar_data(bars)
        endtime = ttime()
        totalloadtime = int(endtime-starttime)
        if start and end and count:
            msg = f"\
                CSV载入Bar成功\n\
                代码：{self.symbol}\n\
                交易所：{self.exchange.value}\n\
                周期：{self.interval.value}\n\
                起始：{start}\n\
                结束：{end}\n\
                总数量：{count}\n\
                耗时：{totalloadtime}s\n\
                "
            self.finishmsg.emit(msg)              


class CsvLoaderWidget(QtWidgets.QWidget):
    """"""

    def __init__(self):
        """"""
        super().__init__()
        self.isbusy = False
        self.thread = QtCore.QThread()
        self.thread.start() 
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("数据载入")
        self.setFixedWidth(300)

        self.setWindowFlags(
            (self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
            & ~QtCore.Qt.WindowMaximizeButtonHint)

        self.fileformat_combo = QtWidgets.QComboBox()
        self.fileformat_combo.addItems(['csv.gz','csv','hdf5'])

        file_button = QtWidgets.QPushButton("选择文件")
        file_button.clicked.connect(self.select_file)

        load_button = QtWidgets.QPushButton("载入数据")
        load_button.clicked.connect(self.load_data)

        self.file_edit = QtWidgets.QLineEdit()

        self.saveto_combo =  QtWidgets.QComboBox()
        self.saveto_combo.addItems(['Memory','DataBase'])

        self.symbol_edit = QtWidgets.QLineEdit()

        self.exchange_combo = QtWidgets.QComboBox()
        for i in Exchange:
            self.exchange_combo.addItem(str(i.name), i)

        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItem('tick')
        for i in Interval:
            self.interval_combo.addItem(str(i.name), i)
        self.interval_combo.currentIndexChanged.connect(self.change_head)

        self.datetime_edit = QtWidgets.QLineEdit("Datetime")

        self.open_edit = QtWidgets.QLineEdit("Open")
        self.high_edit = QtWidgets.QLineEdit("High")
        self.low_edit = QtWidgets.QLineEdit("Low")
        self.close_edit = QtWidgets.QLineEdit("Close")
        self.volume_edit = QtWidgets.QLineEdit("Volume")


        self.tick_last_price = QtWidgets.QLineEdit("Lastprice")
        self.tick_volume = QtWidgets.QLineEdit("Volume")
        self.tick_open_interest = QtWidgets.QLineEdit("Openinterest")
        self.tick_ask_price_1 = QtWidgets.QLineEdit("Askprice1")
        self.tick_ask_volume_1 = QtWidgets.QLineEdit("Askvolume1")
        self.tick_bid_price_1 = QtWidgets.QLineEdit("Bidprice1")
        self.tick_bid_volume_1 = QtWidgets.QLineEdit("Bidvolume1")


        self.format_edit = QtWidgets.QLineEdit("%Y-%m-%d %H:%M:%S.%f")

        info_label = QtWidgets.QLabel("合约信息")
        info_label.setAlignment(QtCore.Qt.AlignCenter)

        head_label = QtWidgets.QLabel("表头信息")
        head_label.setAlignment(QtCore.Qt.AlignCenter)

        format_label = QtWidgets.QLabel("格式信息")
        format_label.setAlignment(QtCore.Qt.AlignCenter)

        form = QtWidgets.QFormLayout()
        form.addRow("文件格式",self.fileformat_combo)
        form.addRow(file_button, self.file_edit)
        form.addRow("存储位置",self.saveto_combo)
        form.addRow(QtWidgets.QLabel())
        form.addRow(info_label)
        form.addRow("代码", self.symbol_edit)
        form.addRow("交易所", self.exchange_combo)
        form.addRow("时间尺度", self.interval_combo)
        form.addRow(QtWidgets.QLabel())
        form.addRow(head_label)
        form.addRow("时间戳", self.datetime_edit)

        barwidget = QtWidgets.QWidget()
        formbar = QtWidgets.QFormLayout()
        formbar.addRow("开盘价", self.open_edit)
        formbar.addRow("最高价", self.high_edit)
        formbar.addRow("最低价", self.low_edit)
        formbar.addRow("收盘价", self.close_edit)
        formbar.addRow("成交量", self.volume_edit)
        barwidget.setLayout(formbar)
        barwidget.setContentsMargins(0,0,0,0)

        tickwidget = QtWidgets.QWidget()
        formtick = QtWidgets.QFormLayout()
        formtick.addRow("最新价", self.tick_last_price)
        formtick.addRow("总成交量", self.tick_volume)
        formtick.addRow("总持仓量", self.tick_open_interest)
        formtick.addRow("买一价", self.tick_ask_price_1)
        formtick.addRow("买一量", self.tick_ask_volume_1)
        formtick.addRow("卖一价", self.tick_bid_price_1)
        formtick.addRow("卖一量", self.tick_bid_volume_1)        
        tickwidget.setLayout(formtick)        
        tickwidget.setContentsMargins(0,0,0,0)

        self.headwidget = QtWidgets.QStackedWidget()
        self.headwidget.addWidget(barwidget)
        self.headwidget.addWidget(tickwidget)
        self.headwidget.setCurrentIndex(1)
        self.headwidget.setContentsMargins(0,0,0,0)

        form.addRow(self.headwidget)
        form.addRow(QtWidgets.QLabel())
        form.addRow(format_label)
        form.addRow("时间格式", self.format_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(load_button)

        self.setLayout(form)

    def change_head(self,index):
        if self.interval_combo.currentText() == 'tick':
            self.headwidget.setCurrentIndex(1)
            self.format_edit.setText("%Y-%m-%d %H:%M:%S.%f")
        else:
            self.headwidget.setCurrentIndex(0)
            self.format_edit.setText("%Y-%m-%d %H:%M:%S")

    def select_file(self):
        """"""
        result: str = QtWidgets.QFileDialog.getOpenFileName(
            self, filter="CSV GZ(*.csv.gz);;CSV (*.csv);;HDF5(*.hdf5);;H5(*.h5)")
        filename = result[0]
        if filename:
            self.file_edit.setText(filename)

    def load_data(self):
        """"""
        fileformat = self.fileformat_combo.currentText()
        file_path = self.file_edit.text()
        symbol = self.symbol_edit.text()
        exchange = self.exchange_combo.currentData()
        datetime_head = self.datetime_edit.text()
        datetime_format = self.format_edit.text()
        saveto = self.saveto_combo.currentText()
        if self.isbusy:
            QtWidgets.QMessageBox().information(
                None, 'Info','已有数据在导入，请等待!',
                QtWidgets.QMessageBox.Ok)
            return

        if self.interval_combo.currentText() == 'tick':
            tick_last_price = self.tick_last_price.text()
            tick_volume = self.tick_volume.text()
            tick_open_interest = self.tick_open_interest.text()
            tick_ask_price_1 = self.tick_ask_price_1.text()
            tick_ask_volume_1 = self.tick_ask_volume_1.text()
            tick_bid_price_1 = self.tick_bid_price_1.text()
            tick_bid_volume_1 = self.tick_bid_volume_1.text()
            alreadyhas = bool(sqglobal.history_tick[symbol])
            if alreadyhas:
                QtWidgets.QMessageBox().information(
                    None, 'Info','内存已有该数据，若要覆盖请先点击清空内存!',
                    QtWidgets.QMessageBox.Ok)
                return

            self.isbusy = True
            self.worker = CsvTickLoader(
                file_path,
                symbol,
                exchange,
                datetime_head,
                tick_last_price,
                tick_volume,
                tick_open_interest,
                tick_ask_price_1,
                tick_ask_volume_1,
                tick_bid_price_1,
                tick_bid_volume_1,
                datetime_format,
                saveto
            )
            self.worker.moveToThread(self.thread)
            self.worker.finishmsg.connect(self.load_finished)
            self.worker.startsig.emit(fileformat)            
            # self.thread.started.connect(self.worker.load_data)
            #self.thread.finished.connect(self.worker.deleteLater)
                  
        else:
            interval = self.interval_combo.currentData()
            open_head = self.open_edit.text()
            low_head = self.low_edit.text()
            high_head = self.high_edit.text()
            close_head = self.close_edit.text()
            volume_head = self.volume_edit.text()
            alreadyhas = bool(sqglobal.history_bar[symbol])
            if alreadyhas:
                QtWidgets.QMessageBox().information(
                    None, 'Info','内存已有该数据，若要覆盖请先点击清空内存!',
                    QtWidgets.QMessageBox.Ok)
                return

            self.isbusy = True
            self.worker = CsvBarLoader(
                file_path,
                symbol,
                exchange,
                interval,
                datetime_head,
                open_head,
                high_head,
                low_head,
                close_head,
                volume_head,
                datetime_format,
                saveto                    
            )
            self.worker.moveToThread(self.thread)
            self.worker.finishmsg.connect(self.load_finished)
            self.worker.startsig.emit(fileformat)
            # self.thread.started.connect(self.worker.load_data)
            # self.thread.finished.connect(self.worker.deleteLater)
            # self.thread.start()

    def load_finished(self,msg):
        QtWidgets.QMessageBox().information(
            None, 'Info',msg,
            QtWidgets.QMessageBox.Ok)
        self.worker.deleteLater()
        # self.thread.wait()
        self.isbusy = False

class DataDownloaderWidget(QtWidgets.QWidget):
    """"""
    log_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        """"""
        super().__init__()
        self.thread = None

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("数据下载")
        # self.setFixedWidth(300)

        self.datasource_combo = QtWidgets.QComboBox()
        self.datasource_combo.addItems(['RQData','Tushare','JoinQuant'])

        self.symbol_line = QtWidgets.QLineEdit("")
        self.interval_combo = QtWidgets.QComboBox()
        for inteval in Interval:
            self.interval_combo.addItem(inteval.value)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=3 * 365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(
                start_dt.year,
                start_dt.month,
                start_dt.day
            )
        )
        self.end_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate.currentDate()
        )
        self.downloading_button = QtWidgets.QPushButton("下载数据")
        self.downloading_button.clicked.connect(self.start_downloading)

        self.log = QtWidgets.QTextBrowser(self)
        self.log_signal.connect(self.log.append)

        form = QtWidgets.QFormLayout()
        form.addRow("数据源", self.datasource_combo)
        form.addRow("合约全称",self.symbol_line)
        form.addRow("时间间隔",self.interval_combo)
        form.addRow("开始日期", self.start_date_edit)
        form.addRow("结束日期", self.end_date_edit)
        form.addRow(self.downloading_button)
        form.addRow(self.log)
        self.setLayout(form)

    def start_downloading(self):
        """"""
        data_source = self.datasource_combo.currentText()
        full_symbol = self.symbol_line.text()
        interval = self.interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()

        if self.thread:
            QtWidgets.QMessageBox().information(
                None, 'Info','已有数据在下载，请等待!',
                QtWidgets.QMessageBox.Ok)
            return False

        self.thread = Thread(
            target=self.run_downloading,
            args=(
                data_source,
                full_symbol,
                interval,
                start,
                end
            )
        )
        self.thread.start()

        return True

    def run_downloading(
        self,
        data_source:str,
        full_symbol: str,
        interval: str,
        start: datetime,
        end: datetime
    ):
        """
        Query bar data from RQData.
        """

        self.write_log(f"{full_symbol}-{interval}开始从{data_source}下载历史数据")
        
        symbol, exchange = extract_full_symbol(full_symbol)

        req = HistoryRequest(
            symbol=symbol,
            exchange=exchange,
            interval=Interval(interval),
            start=start,
            end=end
        )

        if data_source == 'RQData':
            data = rqdata_client.query_history(req)

        elif data_source == 'Tushare':
            QtWidgets.QMessageBox().information(
                None, 'Info','待实现!',
                QtWidgets.QMessageBox.Ok)
            data = None
        elif data_source == 'JoinQuant':
            QtWidgets.QMessageBox().information(
                None, 'Info','待实现!',
                QtWidgets.QMessageBox.Ok)
            data = None
        if data:
            database_manager.save_bar_data(data)
            self.write_log(f"{full_symbol}-{interval}历史数据从{data_source}下载完成")
        else:
            self.write_log(f"无法从{data_source}获取{full_symbol}的历史数据")
        # Clear thread object handler.
        self.thread = None

    def write_log(self,log:str):
        logmsg = str(datetime.now()) + " : " + log
        self.log_signal.emit(logmsg)

class RecorderManager(QtWidgets.QWidget):
    """"""

    signal_log = QtCore.pyqtSignal(Event)
    signal_recorder_update = QtCore.pyqtSignal(Event)
    signal_recorder_out = QtCore.pyqtSignal(Event)
    signal_contract = QtCore.pyqtSignal(Event)

    def __init__(self, contracts: dict = {}):
        super().__init__()
        self.full_symbols = [c for c in contracts.keys()]
        self.init_ui()
        self.register_event()
        self.engineid = ''

    def init_ui(self):
        """"""
        self.setWindowTitle("行情记录")
        self.resize(800, 600)

        # Create widgets
        self.engine_status = QtWidgets.QLineEdit()
        self.engine_status.setMaximumWidth(50)
        self.engine_status.setReadOnly(True)
        self.engine_status.setText('False')
        self.engine_pid = QtWidgets.QLineEdit()
        self.engine_pid.setReadOnly(True)
        self.engine_pid.setMaximumWidth(70)
        refresh_button = QtWidgets.QPushButton("refresh")
        refresh_button.clicked.connect(self.refresh_status)

        self.data_source = QtWidgets.QComboBox()
        self.data_source.addItems(['CTP.MD','TAP.MD']) 

        start_button = QtWidgets.QPushButton("订阅所有合约")
        start_button.clicked.connect(self.start_engine)
        stop_button = QtWidgets.QPushButton("清空所有合约")
        stop_button.clicked.connect(self.stop_engine)


        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.setMaximumWidth(300)
        # self.symbol_line.setFixedHeight(
        #     self.symbol_line.sizeHint().height() * 2)

        self.symbol_completer = QtWidgets.QCompleter(self.full_symbols)
        self.symbol_completer.setFilterMode(QtCore.Qt.MatchContains)
        self.symbol_completer.setCompletionMode(
            self.symbol_completer.PopupCompletion)
        self.symbol_line.setCompleter(self.symbol_completer)



        self.record_choice = QtWidgets.QComboBox()
        self.record_choice.addItems(['tick', 'bar'])        
        add_button = QtWidgets.QPushButton("添加")
        add_button.clicked.connect(self.add_recording)

        remove_button = QtWidgets.QPushButton("移除")
        remove_button.clicked.connect(self.remove_recording)

        # add_tick_button = QtWidgets.QPushButton("添加")
        # add_tick_button.clicked.connect(self.add_tick_recording)

        # remove_tick_button = QtWidgets.QPushButton("移除")
        # remove_tick_button.clicked.connect(self.remove_tick_recording)

        self.bar_recording_edit = QtWidgets.QTextEdit()
        self.bar_recording_edit.setReadOnly(True)

        self.tick_recording_edit = QtWidgets.QTextEdit()
        self.tick_recording_edit.setReadOnly(True)

        self.log_edit = QtWidgets.QTextEdit()
        self.log_edit.setReadOnly(True)

        # Set layout
        statusbox = QtWidgets.QHBoxLayout()
        statusbox.addWidget(refresh_button)
        statusbox.addWidget(QtWidgets.QLabel("Recorder PID"))
        statusbox.addWidget(self.engine_pid)
        statusbox.addWidget(QtWidgets.QLabel("Alive"))
        statusbox.addWidget(self.engine_status)
        statusbox.addWidget(QtWidgets.QLabel("DataSource"))
        statusbox.addWidget(self.data_source)
        statusbox.addWidget(start_button)
        statusbox.addWidget(stop_button)

        # grid = QtWidgets.QGridLayout()
        # grid.addWidget(QtWidgets.QLabel("Bar记录"), 0, 0)
        # grid.addWidget(add_bar_button, 0, 1)
        # grid.addWidget(remove_bar_button, 0, 2)
        # grid.addWidget(QtWidgets.QLabel("Tick记录"), 1, 0)
        # grid.addWidget(add_tick_button, 1, 1)
        # grid.addWidget(remove_tick_button, 1, 2)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("代码全称"))
        hbox.addWidget(self.symbol_line)
        hbox.addWidget(QtWidgets.QLabel("记录选项"))
        hbox.addWidget(self.record_choice)
        hbox.addWidget(add_button)
        hbox.addWidget(remove_button)
        # hbox.addStretch()

        grid2 = QtWidgets.QGridLayout()
        grid2.addWidget(QtWidgets.QLabel("Bar记录列表"), 0, 0)
        grid2.addWidget(QtWidgets.QLabel("Tick记录列表"), 0, 1)
        grid2.addWidget(self.bar_recording_edit, 1, 0)
        grid2.addWidget(self.tick_recording_edit, 1, 1)
        grid2.addWidget(self.log_edit, 2, 0, 1, 2)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(statusbox)
        vbox.addLayout(hbox)
        vbox.addLayout(grid2)
        self.setLayout(vbox)

    def register_event(self):
        """"""
        self.signal_log.connect(self.process_log_event)
        self.signal_contract.connect(self.process_contract_event)
        self.signal_recorder_update.connect(self.process_update_event)

    def start_engine(self):
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src=self.data_source.currentText(),            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_START
        )
        self.signal_recorder_out.emit(m)

    def stop_engine(self):
        mbox = QtWidgets.QMessageBox().question(None, 'confirm','are you sure',QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,QtWidgets.QMessageBox.No)
        if mbox == QtWidgets.QMessageBox.Yes:
            m = Event(type=EventType.RECORDER_CONTROL,
                des='@' + self.engineid,
                src='0',            
                msgtype=MSG_TYPE.MSG_TYPE_RECORDER_STOP
            )
            self.signal_recorder_out.emit(m)

    def refresh_status(self):
        self.engine_pid.setText('')
        self.engine_status.setText('False')
        self.engineid = ''
        self.bar_recording_edit.clear()
        self.tick_recording_edit.clear()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@*',
            src='0',            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_STATUS
        )
        self.signal_recorder_out.emit(m)

    def process_log_event(self, event: Event):
        """"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp}\t{event.data}"
        self.log_edit.append(msg)

    def process_update_event(self, event: Event):
        """"""
        data = event.data
        msgtype = event.msg_type
        if msgtype == MSG_TYPE.MSG_TYPE_RECORDER_STATUS:
            self.engine_pid.setText(event.source)
            self.engine_status.setText(data)
            self.engineid = event.source
        elif msgtype == MSG_TYPE.MSG_TYPE_RECORDER_RTN_DATA:
            data = json.loads(data)
            self.bar_recording_edit.clear()
            bar_text = "\n".join(data["bar"])
            self.bar_recording_edit.setText(bar_text)

            self.tick_recording_edit.clear()
            tick_text = "\n".join(data["tick"])
            self.tick_recording_edit.setText(tick_text)

    def process_contract_event(self, event: Event):
        """"""
        contract = event.data
        self.full_symbols.append(contract.full_symbol)

        model = self.symbol_completer.model()
        model.setStringList(self.full_symbols)

    def add_recording(self):
        if self.engine_status.text() == 'False' or self.engine_pid.text() == '': 
            QtWidgets.QMessageBox().information(None, 'Error','RecorderEngine is not running!',QtWidgets.QMessageBox.Ok)
            return
        if self.record_choice.currentText() == 'tick':
            self.add_tick_recording()
        elif self.record_choice.currentText() == 'bar':
            self.add_bar_recording()

    def remove_recording(self):
        if self.engine_status.text() == 'False' or self.engine_pid.text() == '': 
            QtWidgets.QMessageBox().information(None, 'Error','RecorderEngine is not running!',QtWidgets.QMessageBox.Ok)
            return
        if self.record_choice.currentText() == 'tick':
            self.remove_tick_recording()
        elif self.record_choice.currentText() == 'bar':
            self.remove_bar_recording()

    def add_bar_recording(self):
        """"""
        full_symbol = self.symbol_line.text()

        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src=self.data_source.currentText(),
            data=full_symbol,            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_ADD_BAR
        )
        self.signal_recorder_out.emit(m)

    def add_tick_recording(self):
        """"""
        full_symbol = self.symbol_line.text()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src=self.data_source.currentText(), 
            data=full_symbol,           
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_ADD_TICK
        )
        self.signal_recorder_out.emit(m)

    def remove_bar_recording(self):
        """"""
        full_symbol = self.symbol_line.text()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0',
            data=full_symbol,          
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_REMOVE_BAR
        )
        self.signal_recorder_out.emit(m)

    def remove_tick_recording(self):
        """"""
        full_symbol = self.symbol_line.text()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0', 
            data=full_symbol,           
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_REMOVE_TICK
        )
        self.signal_recorder_out.emit(m)


class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
    """

    headers = {
        "full_symbol":"全称",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "net_position":"是否净持仓",
        "long_margin_ratio":"多仓保证金率",
        "short_margin_ratio":"空仓保证金率"
    }

    def __init__(self):
        super(ContractManager, self).__init__()

        self.contracts = {}
        self.load_contract()


        self.init_ui()

    def load_contract(self):
        contractfile = Path.cwd().joinpath("etc/ctpcontract.yaml")
        with open(contractfile, encoding='utf8') as fc: 
            contracts = yaml.load(fc)
        print('loading contracts, total number:',len(contracts))
        for sym, data in contracts.items():
            contract = ContractData(
                symbol=data["symbol"],
                exchange=Exchange(data["exchange"]),
                name=data["name"],
                product=PRODUCT_CTP2VT[str(data["product"])],
                size=data["size"],
                pricetick=data["pricetick"],
                net_position = True if str(data["positiontype"]) == THOST_FTDC_PT_Net else False,
                long_margin_ratio = data["long_margin_ratio"],
                short_margin_ratio = data["short_margin_ratio"],
                full_symbol = data["full_symbol"]
            )            
            # For option only
            if contract.product == Product.OPTION:
                contract.option_underlying = data["option_underlying"],
                contract.option_type = OPTIONTYPE_CTP2VT.get(str(data["option_type"]), None),
                contract.option_strike = data["option_strike"],
                contract.option_expiry = datetime.strptime(str(data["option_expiry"]), "%Y%m%d"),
            self.contracts[contract.full_symbol] = contract      

    def init_ui(self):
        """"""
        self.setWindowTitle("合约查询")
        self.resize(1000, 600)

        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText("输入全称字段（交易所,类别，产品代码，合约编号），留空则查询所有合约")
        self.filter_line.returnPressed.connect(self.show_contracts)
        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def show_contracts(self):
        """
        Show contracts by symbol
        """
        flt = str(self.filter_line.text()).upper()


        if flt:
            contracts = [
                contract for contract in self.contracts.values() if flt in contract.full_symbol
            ]
        else:
            contracts = self.contracts

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value = getattr(contract, name)
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()
    
    def on_contract(self,contract):
        self.contracts[contract.full_symbol] = contract



class StatusThread(QtCore.QThread):
    status_update = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            cpuPercent = psutil.cpu_percent()
            memoryPercent = psutil.virtual_memory().percent
            self.status_update.emit('CPU Usage: ' + str(cpuPercent) + '% Memory Usage: ' + str(memoryPercent) + '%')
            self.sleep(2)


class GlobalDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self):
        """"""
        super().__init__()

        self.widgets = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("Python进程相关配置")
        self.setMinimumWidth(800)

        settings = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type = type(field_value)
            widget = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button = QtWidgets.QPushButton("确定")
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        self.setLayout(form)

    def update_setting(self):
        """
        Get setting value from line edits and update global setting file.
        """
        settings = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text = widget.text()

            if field_type == bool:
                if value_text == "True":
                    field_value = True
                else:
                    field_value = False
            else:
                field_value = field_type(value_text)

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "配置的修改需要重启后才会生效！",
            QtWidgets.QMessageBox.Ok
        )

        save_json(SETTING_FILENAME, settings)
        self.accept()


class TextEditDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self,filename:str):
        """"""
        super().__init__()
        self.filename = filename
        self.setWindowTitle("配置编辑文件")
        self.setMinimumWidth(800)
        self.setMinimumHeight(800)
        self.textedit = QtWidgets.QTextEdit()
        self.textedit.setFont(QtGui.QFont('Microsoft Sans Serif', 12) )
        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QVBoxLayout()
        savebutton = QtWidgets.QPushButton("save")
        savebutton.clicked.connect(self.update_file)
        form.addWidget(self.textedit)
        form.addWidget(savebutton)
        self.setLayout(form)
        with open(self.filename,'r') as f:
            my_txt=f.read()
            self.textedit.setText(my_txt)       

    def update_file(self):
        """
        .
        """


        my_text=self.textedit.toPlainText()
        with open(self.filename,'w+') as f:            
            f.write(my_text)   
        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "配置的修改需要重启后才会生效！",
            QtWidgets.QMessageBox.Ok
        )          
        self.accept()





class AboutWidget(QtWidgets.QDialog):
    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle('About StarQuant')

        text = u"""
            StarQuant
            易数交易系统
            Lightweight Algorithmic Trading System            
            Language: C++,Python
            Contact: dr.wb@qq.com
            License：MIT

            莫道交易如浪深，莫言策略似沙沉。
            千回万测虽辛苦，实盘验后始得金。
     
            """
        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(300)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        button = QtWidgets.QPushButton("源代码网址")
        button.clicked.connect(self.open_code)
        vbox.addWidget(button)
        self.setLayout(vbox)  

    def open_code(self):

        webbrowser.open("https://www.github.com/physercoe/starquant")