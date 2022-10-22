"""
tool widgets which usually is cpu-consuming , 
so an event engine and working thread is needed to 
work asynchronously and communicate
"""


from PyQt5 import QtCore, QtGui, QtWidgets
from typing import TextIO
from datetime import datetime, date,timedelta
from pathlib import Path
import csv
import json
from copy import copy
from threading import Thread
from time import time as ttime
import gzip

from pystarquant.common.constant import (
    Exchange,
    Interval, 
    Product, 
    PRODUCT_CTP2VT, 
    OPTIONTYPE_CTP2VT,
    PRODUCT_SQ2VT,
    PRODUCT_VT2SQ,
    EventType
)
from pystarquant.common.datastruct import (
    Event, 
    MSG_TYPE,
    TickData,
    BarData, 
    TBTBarData, 
    HistoryRequest, 
    ContractData
)
from pystarquant.data import database_manager
from pystarquant.data.rqdata import rqdata_client
from pystarquant.common.utility import (
    generate_full_symbol, 
    extract_full_symbol
)
import pystarquant.common.sqglobal as SQGlobal
from pystarquant.engine.iengine import EventEngine

class DataLoader:
    def __init__(self,event_engine: EventEngine = None):

        super().__init__()
        if event_engine:
            self.event_engine = event_engine
        else:
            self.event_engine = None

        self.thread = None

    def write_log(self,msg):
        if self.event_engine:
            event = Event(type=EventType.DATALOAD_LOG)
            event.data = msg
            self.event_engine.put(event)
        else:
            print(str)

    def start_load_tick(
        self,
        suffix,
        file_path,
        symbol,
        datetime_head,
        tick_last_price,
        tick_volume,
        tick_open_interest,
        tick_ask_price_1,
        tick_ask_volume_1,
        tick_bid_price_1,
        tick_bid_volume_1,
        datetime_format,
        saveto,
        isupdate
    ):
        if self.thread:
            self.write_log('已有任务，请等待完成')
            return False

        self.write_log("开始导入数据......")
        self.thread = Thread(
            target=self.load_tick,
            args=(
                suffix,
                file_path,
                symbol,
                datetime_head,
                tick_last_price,
                tick_volume,
                tick_open_interest,
                tick_ask_price_1,
                tick_ask_volume_1,
                tick_bid_price_1,
                tick_bid_volume_1,
                datetime_format,
                saveto,
                isupdate
            )
        )
        self.thread.start()

        return True

    def load_tick(
        self,
        suffix,
        file_path,
        symbol,
        datetime_head,
        tick_last_price,
        tick_volume,
        tick_open_interest,
        tick_ask_price_1,
        tick_ask_volume_1,
        tick_bid_price_1,
        tick_bid_volume_1,
        datetime_format,
        saveto,
        isupdate     
    ):
        """
        load tick
        """
        f = None
        full_symbol =  symbol
        try:
            if suffix == 'csv':
                f =  open(file_path, "rt")
            elif suffix == 'csv.gz':
                f = gzip.open(file_path, 'rt') 

            reader = csv.DictReader(f)
            ticks = []
            start = None
            count = 0
            alreadyhas = bool(SQGlobal.history_tick[full_symbol])
            starttime = ttime()

            for item in reader:
                if datetime_format:
                    dt = datetime.strptime(
                        item[datetime_head], datetime_format)
                else:
                    dt = datetime.fromisoformat(item[datetime_head])

                tick = TickData(
                    full_symbol=full_symbol,
                    datetime=dt,
                    volume=int(float(item[tick_volume])),
                    last_price=float(item[tick_last_price]),
                    open_interest=int(float(item[tick_open_interest])),
                    ask_price_1=float(item[tick_ask_price_1]),
                    ask_volume_1=int(float(item[tick_ask_volume_1])),
                    bid_price_1=float(item[tick_bid_price_1]),
                    bid_volume_1=int(float(item[tick_bid_volume_1])),
                    depth=1,
                    gateway_name="DB",
                )
                ticks.append(tick)

                # do some statistics
                count += 1
                if not start:
                    start = tick.datetime
                if count % 100000 == 0:
                    if saveto == 'DataBase':
                        database_manager.save_tick_data(ticks, isupdate)
                        ticks.clear()
        
        except Exception as e:
            msg = "Load csv error: {0}".format(str(e.args[0]))
            self.write_log(msg)
            self.thread = None
            if f is not None:
                f.close()
            return

        end = tick.datetime
        if saveto == 'Memory' and not alreadyhas:
            SQGlobal.history_tick[full_symbol] = ticks
        elif saveto == 'DataBase':
            database_manager.save_tick_data(ticks, isupdate)
        endtime = ttime()
        totalloadtime = int(endtime - starttime)
        if start and end and count:
            msg = f"\
                CSV载入Tick成功\n\
                代码：{symbol}\n\
                起始：{start}\n\
                结束：{end}\n\
                总数量：{count}\n\
                耗时：{totalloadtime}s\n\
                "
            self.write_log(msg)

        self.thread = None
        f.close()


    def start_load_bar(
        self,
        suffix,
        file_path,
        symbol,
        interval,
        datetime_head,
        open_head,
        high_head,
        low_head,
        close_head,
        volume_head,
        openinterest_head,
        datetime_format,
        saveto,
        isupdate
    ):
        if self.thread:
            self.write_log('已有任务，请等待完成')
            return False

        self.write_log("开始导入数据......")
        self.thread = Thread(
            target=self.load_bar,
            args=(
                suffix,
                file_path,
                symbol,
                interval,
                datetime_head,
                open_head,
                high_head,
                low_head,
                close_head,
                volume_head,
                openinterest_head,
                datetime_format,
                saveto,
                isupdate
            )
        )
        self.thread.start()

        return True

    def load_bar(
        self,
        suffix,
        file_path,
        symbol,
        interval,
        datetime_head,
        open_head,
        high_head,
        low_head,
        close_head,
        volume_head,
        openinterest_head,
        datetime_format,
        saveto,
        isupdate
    ):
        """
        load bar
        """
        f = None
        full_symbol =  symbol
        try:
            if suffix == 'csv':
                f =  open(file_path, "rt")
            elif suffix == 'csv.gz':
                f = gzip.open(file_path, 'rt') 

            reader = csv.DictReader(f)

            bars = []
            start = None
            count = 0
            # change fullsym include interval 
            fullsyminterval = full_symbol + '-' + interval.value
            alreadyhas = bool(SQGlobal.history_bar[fullsyminterval])
            starttime = ttime()

            for item in reader:
                if datetime_format:
                    dt = datetime.strptime(
                        item[datetime_head], datetime_format)
                else:
                    dt = datetime.fromisoformat(item[datetime_head])

                bar = BarData(
                    full_symbol=full_symbol,
                    datetime=dt,
                    interval=interval,
                    volume=int(float(item[volume_head])),
                    open_interest=int(float(item[openinterest_head])),
                    open_price=float(item[open_head]),
                    high_price=float(item[high_head]),
                    low_price=float(item[low_head]),
                    close_price=float(item[close_head]),
                    gateway_name="DB",
                )
                bars.append(bar)

                # do some statistics
                count += 1
                if not start:
                    start = bar.datetime
                if count % 100000 == 0:
                    if saveto == 'DataBase':
                        database_manager.save_bar_data(bars, isupdate)
                        bars.clear()
        except Exception as e:
            msg = "Load csv error: {0}".format(str(e.args[0]))
            self.write_log(msg)
            if f is not None:
                f.close()
            self.thread = None
            return

        end = bar.datetime
        # insert into database

        if saveto == 'Memory' and not alreadyhas:
            SQGlobal.history_bar[fullsyminterval] = bars
        elif saveto == 'DataBase':
            database_manager.save_bar_data(bars,isupdate)
        endtime = ttime()
        totalloadtime = int(endtime - starttime)
        if start and end and count:
            msg = f"\
                CSV载入Bar成功\n\
                代码：{symbol}\n\
                周期：{interval.value}\n\
                起始：{start}\n\
                结束：{end}\n\
                总数量：{count}\n\
                耗时：{totalloadtime}s\n\
                "
            self.write_log(msg)
        self.thread = None
        f.close()



    def start_load_tbtbar(
        self,
        suffix,
        file_path,
        symbol,
        datetime_head,
        tbtsymbol_head,
        interval,
        tbtopen_head,
        tbthigh_head,
        tbtlow_head,
        tbtclose_head,
        tbtvolume_head,
        tbtaskq_head,
        tbtbidq_head,
        tbtaskm_head,
        tbtbidm_head,
        tbtbiga_head,
        tbtbigb_head,
        tbtbigaskleft,
        tbtbigbidleft,
        bigmoney,
        datetime_format,
        saveto,
        isupdate
    ):
        if self.thread:
            self.write_log('已有任务，请等待完成')
            return False

        self.write_log("开始导入数据......")
        self.thread = Thread(
            target=self.load_tbtbar,
            args=(
                suffix,
                file_path,
                symbol,
                datetime_head,
                tbtsymbol_head,
                interval,
                tbtopen_head,
                tbthigh_head,
                tbtlow_head,
                tbtclose_head,
                tbtvolume_head,
                tbtaskq_head,
                tbtbidq_head,
                tbtaskm_head,
                tbtbidm_head,
                tbtbiga_head,
                tbtbigb_head,
                tbtbigaskleft,
                tbtbigbidleft,
                bigmoney,
                datetime_format,
                saveto,
                isupdate
            )
        )
        self.thread.start()

        return True

    def load_tbtbar(
        self,
        suffix,
        file_path,
        symbol,
        datetime_head,
        tbtsymbol_head,
        interval,
        tbtopen_head,
        tbthigh_head,
        tbtlow_head,
        tbtclose_head,
        tbtvolume_head,
        tbtaskq_head,
        tbtbidq_head,
        tbtaskm_head,
        tbtbidm_head,
        tbtbiga_head,
        tbtbigb_head,
        tbtbigaskleft,
        tbtbigbidleft,
        bigmoney,
        datetime_format,
        saveto,
        isupdate  
    ):
        """
        load tick
        """
        f = None
        full_symbol =  symbol
        try:
            if suffix == 'csv':
                f =  open(file_path, "rt")
            elif suffix == 'csv.gz':
                f = gzip.open(file_path, 'rt') 

            reader = csv.DictReader(f)

            bars = []
            start = None
            count = 0
            fullsyminterval = full_symbol + '-' + interval.value
            alreadyhas = bool(SQGlobal.history_tbtbar[fullsyminterval])
            starttime = ttime()

            for item in reader:
                if datetime_format:
                    dt = datetime.strptime(
                        item[datetime_head], datetime_format)
                else:
                    dt = datetime.fromisoformat(item[datetime_head])
                sym, ex = extract_full_symbol(item[tbtsymbol_head])

                bar = TBTBarData(
                    full_symbol=item[tbtsymbol_head],
                    datetime=dt,
                    interval=interval,
                    bigmoney=bigmoney,
                    volume=int(float(item[tbtvolume_head])),
                    open_price=float(item[tbtopen_head]),
                    high_price=float(item[tbthigh_head]),
                    low_price=float(item[tbtlow_head]),
                    close_price=float(item[tbtclose_head]),
                    ask_totalqty=float(item[tbtaskq_head]),
                    bid_totalqty=float(item[tbtbidq_head]),
                    ask_totalmoney=float(item[tbtaskm_head]),
                    bid_totalmoney=float(item[tbtbidm_head]),
                    ask_bigmoney=float(item[tbtbiga_head]),
                    bid_bigmoney=float(item[tbtbigb_head]),
                    ask_bigleft=float(item[tbtbigaskleft]),
                    bid_bigleft=float(item[tbtbigbidleft]),
                    gateway_name="DB",
                )

                bars.append(bar)

                # do some statistics
                count += 1
                if not start:
                    start = bar.datetime
                if count % 100000 == 0:
                    if saveto == 'DataBase':
                        database_manager.save_tbtbar_data(bars, isupdate)
                        bars.clear()

        except Exception as e:
            msg = "Load csv error: {0}".format(str(e.args[0]))
            self.write_log(msg)
            if f is not None:
                f.close()
            self.thread = None
            return

        end = bar.datetime
        # insert into database

        if saveto == 'Memory' and not alreadyhas:
            SQGlobal.history_tbtbar[fullsyminterval] = bars
        elif saveto == 'DataBase':
            database_manager.save_tbtbar_data(bars, isupdate)
        endtime = ttime()
        totalloadtime = int(endtime - starttime)
        if start and end and count:
            msg = f"\
                CSV载入TbtBar成功\n\
                代码：{symbol}\n\
                周期：{interval.value}\n\
                起始：{start}\n\
                结束：{end}\n\
                总数量：{count}\n\
                耗时：{totalloadtime}s\n\
                "
            self.write_log(msg)

        self.thread = None
        f.close()




class CsvLoaderWidget(QtWidgets.QWidget):
    """"""

    def __init__(self,event_engine: EventEngine):
        """"""
        super().__init__()
        self.event_engine = event_engine
        self.isbusy = False
        self.worker = DataLoader(self.event_engine)
        self.init_ui()
        self.register_event()

    def init_ui(self):
        """"""
        self.setWindowTitle("数据载入")
        # self.setFixedWidth(300)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(
            (self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
            & ~QtCore.Qt.WindowMaximizeButtonHint)

        self.fileformat_combo = QtWidgets.QComboBox()
        self.fileformat_combo.addItems(['csv.gz', 'csv', 'hdf5'])

        file_button = QtWidgets.QPushButton("选择文件")
        file_button.clicked.connect(self.select_file)

        load_button = QtWidgets.QPushButton("载入数据")
        load_button.clicked.connect(self.load_data)

        self.file_edit = QtWidgets.QLineEdit()

        self.saveto_combo = QtWidgets.QComboBox()
        self.saveto_combo.addItems(['Memory', 'DataBase'])

        self.updateinsert = QtWidgets.QCheckBox("update")

        self.symbol_edit = QtWidgets.QLineEdit()

        self.exchange_combo = QtWidgets.QComboBox()
        for i in Exchange:
            self.exchange_combo.addItem(str(i.name), i)

        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItem('tick')
        self.type_combo.addItem('bar')
        self.type_combo.addItem('tbtbar')
        self.type_combo.currentIndexChanged.connect(self.change_head)

        self.interval_combo = QtWidgets.QComboBox()
        for i in Interval:
            self.interval_combo.addItem(str(i.name), i)

        self.interval_combo.currentIndexChanged.connect(self.change_interval)

        self.datetime_edit = QtWidgets.QLineEdit("datetime")

        self.open_edit = QtWidgets.QLineEdit("open")
        self.high_edit = QtWidgets.QLineEdit("high")
        self.low_edit = QtWidgets.QLineEdit("low")
        self.close_edit = QtWidgets.QLineEdit("close")
        self.volume_edit = QtWidgets.QLineEdit("volume")
        self.open_interest_edit = QtWidgets.QLineEdit("open_interest")

        self.tbt_bigmoney_edit = QtWidgets.QLineEdit("0")
        self.tbt_symbol_edit = QtWidgets.QLineEdit("Ticker")
        self.tbt_open_edit = QtWidgets.QLineEdit("open")
        self.tbt_high_edit = QtWidgets.QLineEdit("high")
        self.tbt_low_edit = QtWidgets.QLineEdit("low")
        self.tbt_close_edit = QtWidgets.QLineEdit("close")
        self.tbt_volume_edit = QtWidgets.QLineEdit("volume")
        self.tbt_askq_edit = QtWidgets.QLineEdit("askqty")
        self.tbt_bidq_edit = QtWidgets.QLineEdit("bidqty")
        self.tbt_askm_edit = QtWidgets.QLineEdit("askmoney")
        self.tbt_bidm_edit = QtWidgets.QLineEdit("bidmoney")
        self.tbt_biga_edit = QtWidgets.QLineEdit("bigask1")
        self.tbt_bigb_edit = QtWidgets.QLineEdit("bigbid1")
        self.tbt_bigaskleft_edit = QtWidgets.QLineEdit("bigask2")
        self.tbt_bigbidleft_edit = QtWidgets.QLineEdit("bigbid2")


        self.tick_last_price = QtWidgets.QLineEdit("lastprice")
        self.tick_volume = QtWidgets.QLineEdit("volume")
        self.tick_open_interest = QtWidgets.QLineEdit("open_interest")
        self.tick_ask_price_1 = QtWidgets.QLineEdit("askprice1")
        self.tick_ask_volume_1 = QtWidgets.QLineEdit("askvolume1")
        self.tick_bid_price_1 = QtWidgets.QLineEdit("bidprice1")
        self.tick_bid_volume_1 = QtWidgets.QLineEdit("bidvolume1")

        self.format_edit = QtWidgets.QLineEdit("%Y-%m-%d %H:%M:%S.%f")

        info_label = QtWidgets.QLabel("合约信息")
        info_label.setAlignment(QtCore.Qt.AlignCenter)

        head_label = QtWidgets.QLabel("表头信息")
        head_label.setAlignment(QtCore.Qt.AlignCenter)

        format_label = QtWidgets.QLabel("格式信息")
        format_label.setAlignment(QtCore.Qt.AlignCenter)

        form = QtWidgets.QFormLayout()
        form.addRow(load_button)
        form.addRow("文件格式", self.fileformat_combo)
        form.addRow(file_button, self.file_edit)

        tmph = QtWidgets.QHBoxLayout()
        tmph.addWidget(QtWidgets.QLabel("存储位置"))
        tmph.addWidget(self.saveto_combo)
        tmph.addWidget(self.updateinsert)
        form.addRow(tmph)

        # form.addRow("存储位置", self.saveto_combo)
        # form.addRow(QtWidgets.QLabel())
        form.addRow(info_label)
        form.addRow("合约全称", self.symbol_edit)
        form.addRow("数据类型", self.type_combo)
        form.addRow("时间尺度", self.interval_combo)
        # form.addRow(QtWidgets.QLabel())
        form.addRow(head_label)
        form.addRow("时间戳", self.datetime_edit)

        barwidget = QtWidgets.QWidget()
        formbar = QtWidgets.QFormLayout()
        formbar.addRow("开盘价", self.open_edit)
        formbar.addRow("最高价", self.high_edit)
        formbar.addRow("最低价", self.low_edit)
        formbar.addRow("收盘价", self.close_edit)
        formbar.addRow("成交量", self.volume_edit)
        formbar.addRow("持仓量", self.open_interest_edit)
        barwidget.setLayout(formbar)
        barwidget.setContentsMargins(0, 0, 0, 0)



        tbtbarwidget = QtWidgets.QWidget()
        formtbtbar = QtWidgets.QFormLayout()
        formtbtbar.addRow("标的名称",self.tbt_symbol_edit)
        formtbtbar.addRow("开盘价", self.tbt_open_edit)
        formtbtbar.addRow("最高价", self.tbt_high_edit)
        formtbtbar.addRow("最低价", self.tbt_low_edit)
        formtbtbar.addRow("收盘价", self.tbt_close_edit)
        formtbtbar.addRow("成交量", self.tbt_volume_edit)
        formtbtbar.addRow("总委买量", self.tbt_bidq_edit)
        formtbtbar.addRow("总委卖量", self.tbt_askq_edit)
        formtbtbar.addRow("总委买额", self.tbt_bidm_edit)
        formtbtbar.addRow("总委卖额", self.tbt_askm_edit)
        formtbtbar.addRow("自定义大单买额1", self.tbt_bigb_edit)        
        formtbtbar.addRow("自定义大单卖额1", self.tbt_biga_edit)
        formtbtbar.addRow("自定义大单买额2", self.tbt_bigbidleft_edit)
        formtbtbar.addRow("自定义大单卖额2", self.tbt_bigaskleft_edit)

        formtbtbar.addRow("自定义参数", self.tbt_bigmoney_edit)
        tbtbarwidget.setLayout(formtbtbar)
        tbtbarwidget.setContentsMargins(0, 0, 0, 0)

        # scrollfactor = QtWidgets.QScrollArea()
        # scrollfactor.setWidget(tbtbarwidget)
        # scrollfactor.setWidgetResizable(True)




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
        tickwidget.setContentsMargins(0, 0, 0, 0)

        self.headwidget = QtWidgets.QStackedWidget()

        self.headwidget.addWidget(barwidget)
        self.headwidget.addWidget(tickwidget)
        self.headwidget.addWidget(tbtbarwidget)
        self.headwidget.setCurrentIndex(1)
        self.headwidget.setContentsMargins(0, 0, 0, 0)

        form.addRow(self.headwidget)
        # form.addRow(format_label)
        form.addRow("时间格式", self.format_edit)

        

        self.setLayout(form)

    def register_event(self):
        pass

    def change_head(self, index):
        if self.type_combo.currentText() == 'tick':
            self.headwidget.setCurrentIndex(1)
            self.format_edit.setText("%Y-%m-%d %H:%M:%S.%f")
        elif self.type_combo.currentText() == 'tbtbar':
            self.headwidget.setCurrentIndex(2)
            self.format_edit.setText("%Y-%m-%d %H:%M:%S.%f")
        else :
            self.headwidget.setCurrentIndex(0)
            self.format_edit.setText("%Y-%m-%d %H:%M:%S")         

    def change_interval(self,index):
        if self.interval_combo.currentText() == str(Interval.DAILY.name):
            self.format_edit.setText("%Y-%m-%d")
        else:
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
        isupdate = self.updateinsert.isChecked()
        if self.worker.thread:
            QtWidgets.QMessageBox().information(
                None, 'Info', '已有数据在导入，请等待!',
                QtWidgets.QMessageBox.Ok)
            return

        if self.type_combo.currentText() == 'tick':
            tick_last_price = self.tick_last_price.text()
            tick_volume = self.tick_volume.text()
            tick_open_interest = self.tick_open_interest.text()
            tick_ask_price_1 = self.tick_ask_price_1.text()
            tick_ask_volume_1 = self.tick_ask_volume_1.text()
            tick_bid_price_1 = self.tick_bid_price_1.text()
            tick_bid_volume_1 = self.tick_bid_volume_1.text()
            alreadyhas = bool(SQGlobal.history_tick[symbol])
            if saveto == 'Memory' and alreadyhas:
                QtWidgets.QMessageBox().information(
                    None, 'Info', '内存已有该数据，若要覆盖请先点击清空内存!',
                    QtWidgets.QMessageBox.Ok)
                return

            self.worker.start_load_tick(
                fileformat,
                file_path,
                symbol,
                datetime_head,
                tick_last_price,
                tick_volume,
                tick_open_interest,
                tick_ask_price_1,
                tick_ask_volume_1,
                tick_bid_price_1,
                tick_bid_volume_1,
                datetime_format,
                saveto,
                isupdate
            )

        elif self.type_combo.currentText() == 'tbtbar':
            tbtsymbol_head = self.tbt_symbol_edit.text()
            tbtopen_head = self.tbt_open_edit.text()
            tbtlow_head = self.tbt_low_edit.text()
            tbthigh_head = self.tbt_high_edit.text()
            tbtclose_head = self.tbt_close_edit.text()
            tbtvolume_head = self.tbt_volume_edit.text()
            tbtaskq_head = self.tbt_askq_edit.text()
            tbtbidq_head = self.tbt_bidq_edit.text()
            tbtaskm_head = self.tbt_askm_edit.text()
            tbtbidm_head = self.tbt_bidm_edit.text()
            tbtbiga_head = self.tbt_biga_edit.text()
            tbtbigb_head = self.tbt_bigb_edit.text()
            tbtbigaskleft = self.tbt_bigaskleft_edit.text()
            tbtbigbidleft = self.tbt_bigbidleft_edit.text()            
            interval = self.interval_combo.currentData()
            bigmoney = int(self.tbt_bigmoney_edit.text())
            alreadyhas = bool(SQGlobal.history_tbtbar[symbol])
            if saveto == 'Memory' and alreadyhas:
                QtWidgets.QMessageBox().information(
                    None, 'Info', '内存已有该数据，若要覆盖请先点击清空内存!',
                    QtWidgets.QMessageBox.Ok)
                return

 
            self.worker.start_load_tbtbar(
                fileformat,
                file_path,
                symbol,
                datetime_head,
                tbtsymbol_head,
                interval,
                tbtopen_head,
                tbthigh_head,
                tbtlow_head,
                tbtclose_head,
                tbtvolume_head,
                tbtaskq_head,
                tbtbidq_head,
                tbtaskm_head,
                tbtbidm_head,
                tbtbiga_head,
                tbtbigb_head,
                tbtbigaskleft,
                tbtbigbidleft,
                bigmoney,
                datetime_format,
                saveto,
                isupdate
            )

        else:
            interval = self.interval_combo.currentData()
            open_head = self.open_edit.text()
            low_head = self.low_edit.text()
            high_head = self.high_edit.text()
            close_head = self.close_edit.text()
            volume_head = self.volume_edit.text()
            openinterest_head = self.open_interest_edit.text()
            alreadyhas = bool(SQGlobal.history_bar[symbol])
            if saveto == 'Memory' and alreadyhas:
                QtWidgets.QMessageBox().information(
                    None, 'Info', '内存已有该数据，若要覆盖请先点击清空内存!',
                    QtWidgets.QMessageBox.Ok)
                return

            self.worker.start_load_bar(
                fileformat,
                file_path,
                symbol,
                interval,
                datetime_head,
                open_head,
                high_head,
                low_head,
                close_head,
                volume_head,
                openinterest_head,
                datetime_format,
                saveto,
                isupdate
            )



    def load_finished(self, msg):
        QtWidgets.QMessageBox().information(
            None, 'Info', msg,
            QtWidgets.QMessageBox.Ok)
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
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.datasource_combo = QtWidgets.QComboBox()
        self.datasource_combo.addItems(['RQData', 'Tushare', 'Futu'])

        self.symbol_line = QtWidgets.QLineEdit("")
        self.interval_combo = QtWidgets.QComboBox()
        for inteval in Interval:
            self.interval_combo.addItem(inteval.value)
        self.interval_combo.addItem('tick')

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=0 * 365)

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
        form.addRow("合约全称", self.symbol_line)
        form.addRow("时间间隔", self.interval_combo)
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
                None, 'Info', '已有数据在下载，请等待!',
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
        data_source: str,
        full_symbol: str,
        interval: str,
        start: date,
        end: date
    ):
        """
        Query bar data from RQData.
        """

        self.write_log(f"{full_symbol}-{interval}开始从{data_source}下载历史数据")

        symbol, exchange = extract_full_symbol(full_symbol)

        req = HistoryRequest(
            full_symbol=full_symbol,
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start=start,
            end=end
        )
        try:
            if data_source == 'RQData':
                result = rqdata_client.init()
                if not result:
                    QtWidgets.QMessageBox().information(
                        None, 'Info', 'RQdata 初始化失败!',
                        QtWidgets.QMessageBox.Ok)
                    data = None
                else:
                    data = rqdata_client.query_history(req)

            elif data_source == 'Tushare':
                QtWidgets.QMessageBox().information(
                    None, 'Info', '待实现!',
                    QtWidgets.QMessageBox.Ok)
                data = None
            elif data_source == 'Futu':
                QtWidgets.QMessageBox().information(
                    None, 'Info', '待实现!',
                    QtWidgets.QMessageBox.Ok)
                data = None
            if data:
                if interval == 'tick':
                    database_manager.save_tick_data(data,True)
                else:
                    database_manager.save_bar_data(data,True)
                self.write_log(f"{len(data)}个{full_symbol}-{interval}历史数据从{data_source}下载完成")
            else:
                self.write_log(f"无法从{data_source}获取{full_symbol}的历史数据")
        except Exception as e:
            msg = "data download error: {0}".format(str(e.args[0]))
            self.write_log(f"从{data_source}下载{full_symbol}的历史数据出错{msg}")

        # Clear thread object handler.
        self.thread = None

    def write_log(self, log: str):
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
        self.resize(400, 400)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
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
        self.data_source.addItems(['CTP.MD', 'TAP.MD'])

        start_button = QtWidgets.QPushButton("订阅所有合约")
        start_button.clicked.connect(self.start_engine)
        stop_button = QtWidgets.QPushButton("清空所有合约")
        stop_button.clicked.connect(self.stop_engine)

        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.setMaximumWidth(220)
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

        statusbox.addWidget(QtWidgets.QLabel("PID"))
        statusbox.addWidget(self.engine_pid)
        statusbox.addWidget(QtWidgets.QLabel("isAlive"))
        statusbox.addWidget(self.engine_status)
        statusbox.addWidget(refresh_button)

        commandbox = QtWidgets.QHBoxLayout()
        commandbox.addWidget(QtWidgets.QLabel("DataSource"))
        commandbox.addWidget(self.data_source)
        commandbox.addWidget(start_button)
        commandbox.addWidget(stop_button)

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
        # hbox.addWidget(QtWidgets.QLabel("记录选项"))
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
        vbox.addLayout(commandbox)
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
        mbox = QtWidgets.QMessageBox().question(None, 'confirm', 'are you sure',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
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
            QtWidgets.QMessageBox().information(
                None, 'Error', 'RecorderEngine is not running!', QtWidgets.QMessageBox.Ok)
            return
        if self.record_choice.currentText() == 'tick':
            self.add_tick_recording()
        elif self.record_choice.currentText() == 'bar':
            self.add_bar_recording()

    def remove_recording(self):
        if self.engine_status.text() == 'False' or self.engine_pid.text() == '':
            QtWidgets.QMessageBox().information(
                None, 'Error', 'RecorderEngine is not running!', QtWidgets.QMessageBox.Ok)
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


