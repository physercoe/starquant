import os,sys,gzip
import random
import pandas as pd
import numpy as np
from PyQt5 import QtCore,QtWidgets,QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget

import mpl_finance as mpf
from datetime import timedelta,datetime
from dateutil.parser import parse

import pyqtgraph as pg

sys.path.insert(0,"../..")

from .ui_basic import CandlestickItem,VolumeItem
from source.common.datastruct import Event, TickData

from ..data.data_board import BarGenerator
from ..common.datastruct import Event
from ..common.utility import extract_full_symbol
from ..data import database_manager
from ..common.constant import Interval


class MarketDataView(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)
    def __init__(self,sym:str = ""):
        """"""
        super(MarketDataView, self).__init__()

        self.full_symbol = ""
        self.init_ui()
        self.register_event() 
    def init_ui(self):
        # self.datachart = DataPGChart()
        self.datachart = QuotesChart(self.full_symbol)
        self.orderbook = OrderBookWidget()
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.datachart)
        self.scroll.setWidgetResizable(True)  

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.scroll)
        hbox.addWidget(self.orderbook)
        self.setLayout(hbox)

    def register_event(self):
        """"""
        self.tick_signal.connect(self.orderbook.tick_signal.emit)
        self.tick_signal.connect(self.datachart.on_tick)
        self.symbol_signal.connect(self.orderbook.symbol_signal.emit)
        self.orderbook.symbol_signal.connect(self.datachart.reset)
        self.orderbook.day_signal.connect(self.datachart.reload)
        # self.symbol_signal.connect(self.datachart.reset) 


class DataPGChart(pg.GraphicsWindow):
    """"""

    def __init__(self):
        """"""
        super().__init__(title="Live Market Chart")

        self.dates = {}

        self.init_ui()

    def init_ui(self):
        """"""
        pg.setConfigOptions(antialias=True)

        # Create plot widgets
        self.balance_plot = self.addPlot(
            title="K line",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.drawdown_plot = self.addPlot(
            title="Volume",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()


        # Add curves and bars on plot widgets
        self.balance_curve = self.balance_plot.plot(
            pen=pg.mkPen("#ffc107", width=3)
        )

        dd_color = "#303f9f"
        self.drawdown_curve = self.drawdown_plot.plot(
            fillLevel=-0.3, brush=dd_color, pen=dd_color
        )

        profit_color = 'r'
        loss_color = 'g'
        self.profit_pnl_bar = pg.BarGraphItem(
            x=[], height=[], width=0.3, brush=profit_color, pen=profit_color
        )
        self.loss_pnl_bar = pg.BarGraphItem(
            x=[], height=[], width=0.3, brush=loss_color, pen=loss_color
        )


    def clear_data(self):
        """"""
        self.balance_curve.setData([], [])
        self.drawdown_curve.setData([], [])
        self.profit_pnl_bar.setOpts(x=[], height=[])
        self.loss_pnl_bar.setOpts(x=[], height=[])

    def set_data(self, df):
        """"""
        count = len(df)

        self.dates.clear()
        for n, date in enumerate(df.index):
            self.dates[n] = date

        # Set data for curve of balance and drawdown
        self.balance_curve.setData(df["balance"])
        self.drawdown_curve.setData(df["drawdown"])

        # Set data for daily pnl bar
        profit_pnl_x = []
        profit_pnl_height = []
        loss_pnl_x = []
        loss_pnl_height = []

        for count, pnl in enumerate(df["net_pnl"]):
            if pnl >= 0:
                profit_pnl_height.append(pnl)
                profit_pnl_x.append(count)
            else:
                loss_pnl_height.append(pnl)
                loss_pnl_x.append(count)

        self.profit_pnl_bar.setOpts(x=profit_pnl_x, height=profit_pnl_height)
        self.loss_pnl_bar.setOpts(x=loss_pnl_x, height=loss_pnl_height)



class DateAxis(pg.AxisItem):
    """Axis for showing date data"""

    def __init__(self, dates: dict, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)
        self.dates = dates

    def tickStrings(self, values, scale, spacing):
        """"""
        strings = []
        for v in values:
            dt = self.dates.get(v, "")
            strings.append(str(dt))
        return strings


class DateAxis2(pg.AxisItem):
    """Axis for showing date data"""

    def __init__(self, datalist:list, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)
        self.data = datalist
    def tickStrings(self, values, scale, spacing):
        """"""
        strings = []
        xstart = 0  # 60*(self.data[0].datetime.hour - 9) + self.data[0].datetime.minute        
        for value in values:
            v = value - xstart
            if v > len(self.data) -1 or v <0:
                return strings
            dt = self.data[int(v)].datetime
            strings.append(dt.strftime('%H:%M\n %b-%d '))
        return strings

class PriceAxis(pg.AxisItem):
    def __init__(self):
        super().__init__(orientation='right')
        self.style.update({'textFillLimits': [(0, 0.8)]})

    def tickStrings(self, vals, scale, spacing):
        digts = max(0, np.ceil(-np.log10(spacing * scale)))
        return [
            ('{:<8,.%df}' % digts).format(v).replace(',', ' ') for v in vals
        ]
class VolumeAxis(pg.AxisItem):
    def __init__(self):
        super().__init__(orientation='right')
        self.style.update({'textFillLimits': [(0, 0.8)]})

    def tickStrings(self, vals, scale, spacing):
        digts = max(0, np.ceil(-np.log10(spacing * scale)))
        return [
            ('{:<8,.%df}' % digts).format(v).replace(',', ' ') for v in vals
        ]

CHART_MARGINS = (0, 0, 20, 10)
class QuotesChart(QtGui.QWidget):
    signal = QtCore.pyqtSignal(Event)

    long_pen = pg.mkPen('#006000')
    long_brush = pg.mkBrush('#00ff00')
    short_pen = pg.mkPen('#600000')
    short_brush = pg.mkBrush('#ff0000')

    zoomIsDisabled = QtCore.pyqtSignal(bool)

    def __init__(self,symbol:str = ""):
        super().__init__()
        self.full_symbol = symbol
        self.data = []
        self.bg = BarGenerator(self.on_bar)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.chart = None
        self.charv = None
        self.load_bar()
        self.plot()

    def reset(self,symbol:str):
        # if not self.layout.isEmpty():
        #     self.layout.removeWidget(self.splitter)
        #     self.splitter.deleteLater()     
        # self.full_symbol = symbol
        # self.bg = BarGenerator(self.on_bar)
        # self.load_bar()
        # self.plot()
        self.full_symbol = symbol
        self.bg = BarGenerator(self.on_bar)
        self.load_bar()
        self.klineitem.generatePicture()
        self.volumeitem.generatePicture()


    def plot(self):       
        self.xaxis = DateAxis2(self.data, orientation='bottom')
        self.xaxis.setStyle(
            tickTextOffset=7, textFillLimits=[(0, 0.80)], showValues=True
        )
        self.klineitem = CandlestickItem(self.data)
        self.volumeitem = VolumeItem(self.data)
        self.init_chart()
        self.init_chart_item()

    def load_bar(self,days:int =1,interval: Interval = Interval.MINUTE):
        symbol, exchange = extract_full_symbol(self.full_symbol)
        end = datetime.now()
        start = end - timedelta(days)
        if start > end:
            tmp = end
            end = start
            start = tmp 
        bars = database_manager.load_bar_data(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start=start,
            end=end,
        )
        self.data.clear()
        self.data.extend(bars)

    def reload(self, count = 1):
        self.load_bar(days=count)
        self.klineitem.generatePicture()
        self.volumeitem.generatePicture()        

    def on_bar(self,bar):
        self.data.append(bar)
        self.klineitem.on_bar(bar)
        self.volumeitem.on_bar(bar)
        # self.xaxis.on_bar(bar)
        # self.tmax += 1
        # self.pmax = max(self.pmax,bar.high_price)
        # self.pmin = min(self.pmin,bar.low_price)
        # self.chart.setLimits(
        #     xMin=self.tmin,
        #     xMax=self.tmax,
        #     minXRange=60,
        #     yMin=self.pmin * 0.95,
        #     yMax=self.pmax * 1.05,
        # )        

    def on_tick(self,tickevent):
        tick = tickevent.data
        if tick.full_symbol == self.full_symbol:
            self.bg.update_tick(tick)

    def init_chart_item(self):

        self.chart.addItem(self.klineitem)
        # barf = self.data[0]
        # bare = self.data[-1]
        # self.tmin = 60*(barf.datetime.hour - 9) + barf.datetime.minute - 20
        # self.tmax = 60*(bare.datetime.hour - 9) + bare.datetime.minute + 20
        # self.pmax = 0
        # self.pmin = 999999
        # for bar in self.data:
        #     self.pmax = max(self.pmax,bar.high_price)
        #     self.pmin = min(self.pmin,bar.low_price)
        # self.chart.setLimits(
        #     xMin=self.tmin,
        #     xMax=self.tmax,
        #     minXRange=60,
        #     yMin=self.pmin * 0.95,
        #     yMax=self.pmax * 1.05,
        # )
        self.chartv.addItem(self.volumeitem)

        # self.chart.setCursor(QtCore.Qt.BlankCursor)
        # self.chart.sigXRangeChanged.connect(self._update_yrange_limits)


    # def _update_yrange_limits(self):
    #     vr = self.chart.viewRect()
    #     lbar, rbar = max(0,int(vr.left())), min(len(self.data),int(vr.right()))
    #     bars = self.data[lbar:rbar]
    #     pmax = 0
    #     pmin = 999999
    #     pmean = 0
    #     for bar in bars:
    #         pmax = max(pmax,bar.high_price)
    #         pmin = min(pmin,bar.low_price)
    #         pmean += bar.close_price
    #     pmean = pmean/(len(bars))
    #     ylow = pmin * 0.95
    #     yhigh = pmax * 1.05
    #     print(pmax-pmean)
    #     self.chart.setLimits(yMin=ylow, yMax=yhigh, minYRange= 0.5*abs(pmax-pmean))
    #     self.chart.setYRange(ylow, yhigh)


    def init_chart(self):
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setHandleWidth(0)
        self.layout.addWidget(self.splitter)
        self.chart = pg.PlotWidget(
            parent=self.splitter,
            axisItems={'bottom': self.xaxis, 'right': PriceAxis()},
            enableMenu=True,
        )
        self.chart.getPlotItem().setContentsMargins(0,0,20,0)
        self.chart.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        self.chart.hideAxis('left')
        self.chart.showAxis('right')
        self.chart.showGrid(x=True, y=True)

        self.chartv = pg.PlotWidget(
            parent=self.splitter,
            axisItems={'bottom': self.xaxis, 'right': VolumeAxis()},
            enableMenu=True,
        )
        self.chartv.getPlotItem().setContentsMargins(0,0,15,15)
        self.chartv.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)       
        self.chartv.hideAxis('left')
        self.chartv.showAxis('right')      
        self.chartv.setXLink(self.chart)



class OrderBookWidget(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)
    day_signal = QtCore.pyqtSignal(int)
    def __init__(self):
        """"""
        super(OrderBookWidget, self).__init__()

        self.full_symbol = ""
        self.init_ui()
        self.register_event()
        self.clear_label_text()
    
    def init_ui(self):
        self.symbol_line = QtWidgets.QLineEdit()
        # self.symbol_line.setReadOnly(True)
        self.symbol_line.returnPressed.connect(self.process_symbol)

        self.change_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        self.open_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        self.low_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        self.high_label = self.create_label(alignment=QtCore.Qt.AlignRight)  

        bid_color = "rgb(255,174,201)"
        ask_color = "rgb(160,255,160)"

        self.uplimit_label = self.create_label()
        
        self.bp1_label = self.create_label(bid_color)
        self.bp2_label = self.create_label(bid_color)
        self.bp3_label = self.create_label(bid_color)
        self.bp4_label = self.create_label(bid_color)
        self.bp5_label = self.create_label(bid_color)

        self.bv1_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv2_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv3_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv4_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)
        self.bv5_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)

        self.ap1_label = self.create_label(ask_color)
        self.ap2_label = self.create_label(ask_color)
        self.ap3_label = self.create_label(ask_color)
        self.ap4_label = self.create_label(ask_color)
        self.ap5_label = self.create_label(ask_color)

        self.av1_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av2_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av3_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av4_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)
        self.av5_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)

        self.lplimit_lable = self.create_label()
        self.lp_label = self.create_label()

        self.size_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        self.last_volume = 0
        form2 = QtWidgets.QFormLayout()

        historylabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        historylabel.setText('History Data')
        form2.addRow(historylabel)
        self.histbar_day = QtWidgets.QLineEdit()
        self.histbar_day.setValidator(QtGui.QIntValidator())
        self.histbar_day.setText('1')
        self.histbar_day.returnPressed.connect(self.process_days)
        self.last_days = 1
        form2.addRow('Days',self.histbar_day)
        self.intervalcombo = QtWidgets.QComboBox()
        self.intervalcombo.addItems(["1m","1h"])
        form2.addRow('Interval',self.intervalcombo)
        self.indicators = QtWidgets.QComboBox()
        self.indicators.addItems(['ma','sma'])
        form2.addRow('Indicator',self.indicators)
        form2.addItem(QtWidgets.QSpacerItem(40, 40, QtWidgets.QSizePolicy.Expanding))
        titlelabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        titlelabel.setText('OrderBook')

        # pricelable = self.create_label(alignment=QtCore.Qt.AlignLeft)
        # pricelable.setText('Price')
        # volumelable =  self.create_label(alignment=QtCore.Qt.AlignRight)
        # volumelable.setText('Volume')

        # verticalSpacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        form2.addRow(titlelabel)
        form2.addRow(self.symbol_line)
        form2.addRow(self.change_label,self.open_label)
        form2.addRow(self.low_label,self.high_label)        
        form2.addRow(self.uplimit_label)
        form2.addRow(self.ap5_label, self.av5_label)
        form2.addRow(self.ap4_label, self.av4_label)
        form2.addRow(self.ap3_label, self.av3_label)
        form2.addRow(self.ap2_label, self.av2_label)
        form2.addRow(self.ap1_label, self.av1_label)
        form2.addRow(self.lp_label, self.size_label)
        form2.addRow(self.bp1_label, self.bv1_label)
        form2.addRow(self.bp2_label, self.bv2_label)
        form2.addRow(self.bp3_label, self.bv3_label)
        form2.addRow(self.bp4_label, self.bv4_label)
        form2.addRow(self.bp5_label, self.bv5_label)
        form2.addRow(self.lplimit_lable)


        # Overall layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form2)
        self.setLayout(vbox)
        self.setFixedWidth(160)
        # self.setFixedSize(160,500)

    def create_label(self, color: str = "", alignment: int = QtCore.Qt.AlignLeft):
        """
        Create label with certain font color.
        """
        label = QtWidgets.QLabel()
        if color:
            label.setStyleSheet(f"color:{color}")
        label.setAlignment(alignment)
        return label

    def register_event(self):
        """"""
        self.tick_signal.connect(self.process_tick_event)
        self.symbol_signal.connect(self.set_full_symbol)

    def process_tick_event(self, tickevent: Event):        
        """"""
        tick = tickevent.data
        if not tick:
            return
        if (tick.full_symbol != self.full_symbol):
            return
        self.lp_label.setText(str(tick.last_price))
        self.open_label.setText(str(tick.open_price))
        self.low_label.setText(str(tick.low_price))
        self.high_label.setText(str(tick.high_price))        
        self.size_label.setText(str(tick.volume - self.last_volume))
        self.last_volume = tick.volume
        self.bp1_label.setText(str(tick.bid_price_1))
        self.bv1_label.setText(str(tick.bid_volume_1))
        self.ap1_label.setText(str(tick.ask_price_1))
        self.av1_label.setText(str(tick.ask_volume_1))
        self.uplimit_label.setText(str(tick.limit_up))
        self.lplimit_lable.setText(str(tick.limit_down))

        if tick.pre_close != 0.0:
            r = (tick.last_price / tick.pre_close - 1) * 100
            self.change_label.setText(f"{r:.2f}%")

        if tick.depth == 5:
            self.bp2_label.setText(str(tick.bid_price_2))
            self.bv2_label.setText(str(tick.bid_volume_2))
            self.ap2_label.setText(str(tick.ask_price_2))
            self.av2_label.setText(str(tick.ask_volume_2))

            self.bp3_label.setText(str(tick.bid_price_3))
            self.bv3_label.setText(str(tick.bid_volume_3))
            self.ap3_label.setText(str(tick.ask_price_3))
            self.av3_label.setText(str(tick.ask_volume_3))

            self.bp4_label.setText(str(tick.bid_price_4))
            self.bv4_label.setText(str(tick.bid_volume_4))
            self.ap4_label.setText(str(tick.ask_price_4))
            self.av4_label.setText(str(tick.ask_volume_4))

            self.bp5_label.setText(str(tick.bid_price_5))
            self.bv5_label.setText(str(tick.bid_volume_5))
            self.ap5_label.setText(str(tick.ask_price_5))
            self.av5_label.setText(str(tick.ask_volume_5))

    def process_symbol(self):
        sym = self.symbol_line.text()
        if sym:
            self.symbol_signal.emit(sym)
    def process_days(self):
        days = int(self.histbar_day.text())
        if days != self.last_days :
            self.last_days = days
            self.day_signal.emit(days)


    def set_full_symbol(self,symbol: str):
        """
        Set the tick depth data to monitor by full_symbol.
        """

        # Update name line widget and clear all labels
        self.full_symbol = symbol
        self.symbol_line.setText(symbol)
        self.clear_label_text()


    def clear_label_text(self):
        """
        Clear text on all labels.
        """
        self.lp_label.setText("Last")
        self.change_label.setText("Change")
        self.lplimit_lable.setText('LowerLimit')
        self.uplimit_label.setText('UpperLimit')
        self.open_label.setText('Open')
        self.low_label.setText('Low')
        self.high_label.setText('High')
        self.size_label.setText('Volume')
        self.bv1_label.setText("")
        self.bv2_label.setText("")
        self.bv3_label.setText("")
        self.bv4_label.setText("")
        self.bv5_label.setText("")

        self.av1_label.setText("")
        self.av2_label.setText("")
        self.av3_label.setText("")
        self.av4_label.setText("")
        self.av5_label.setText("")

        self.bp1_label.setText("")
        self.bp2_label.setText("")
        self.bp3_label.setText("")
        self.bp4_label.setText("")
        self.bp5_label.setText("")

        self.ap1_label.setText("")
        self.ap2_label.setText("")
        self.ap3_label.setText("")
        self.ap4_label.setText("")
        self.ap5_label.setText("")













if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MarketDataView()

    ui.show()
    app.exec_()
