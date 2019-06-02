import os,sys,gzip
import random
import pandas as pd

import numpy as np
from PyQt5 import QtCore,QtWidgets,QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget
import matplotlib as mpl
mpl_agg = 'Qt5Agg'
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import matplotlib.dates as mdates
import matplotlib.ticker as mtk
import mpl_finance as mpf
from datetime import datetime,timedelta
from dateutil.parser import parse
from matplotlib.pylab import date2num
import pyqtgraph as pg

from .ui_basic import CandlestickItem
from ..data.data_board import BarGenerator
from ..common.datastruct import Event
from ..common.utility import extract_full_symbol
from ..data import database_manager
from ..common.constant import Interval

sys.path.insert(0,"..")
from pyfolio import plotting
from pyfolio.utils import (to_utc, to_series)

# def mydate(x,pos=None):
# 	tt=np.clip(int(x+0.5),0,len(list_ktime)-1)
# 	return list_ktime[tt]

class BtDataViewFC(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = plt.figure("dataview",figsize=(width, height), dpi=dpi)
        #self.fig = Figure(figsize=(width, height), dpi=dpi)  # 新建一个figure
        self.fig.set_tight_layout(True)
        self.ax_k = self.fig.add_subplot(211)  # 建立一个子图，如果要建立复合图，可以在这里修改
        self.ax_v = self.fig.add_subplot(212,sharex = self.ax_k)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.setMinimumSize(800,800)
        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def load_data(self,sid):
        print('dataview load sid',sid)
        for ax in self.fig.axes:
            ax.clear()   
        datapath = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        datapath = datapath + '/../../data/'
        bar = pd.read_csv(datapath + 'histbar_min.csv', index_col=0, parse_dates=True)
        bar['date'] = pd.to_datetime(bar["date"],format='%Y-%m-%d %H:%M:%S')
        barvalue = bar.values
        def mydate(x,pos=None):
            tt=np.clip(int(x+0.5),0,len(barvalue[:,0])-1)
            return barvalue[tt,0]
        mpf.candlestick2_ohlc(self.ax_k,barvalue[:,1],barvalue[:,3],barvalue[:,4],barvalue[:,2],width=1,colorup='r',colordown='g')
        self.ax_k.xaxis.set_major_formatter(mtk.FuncFormatter(mydate))
        #self.ax_k.grid(True)
        self.ax_v.bar(np.arange(len(barvalue[:,0])),barvalue[:,5],width=0.5)
        self.ax_v.xaxis.set_major_formatter(mtk.FuncFormatter(mydate))
        #self.ax_v.grid(True)
        self.fig.autofmt_xdate()
        # self.fig.suptitle('Market Data')
        # self.axes.set_ylabel('静态图：Y轴')
        # self.axes.set_xlabel('静态图：X轴')
        # self.axes.grid(True)
        self.draw()



class BtDataViewWidget(QWidget):
    def __init__(self, parent=None):
        super(BtDataViewWidget, self).__init__(parent)
        self.initui()
    def initui(self):
        self.layout = QVBoxLayout(self)
        self.mpl = BtDataViewFC(self, width=5, height=4, dpi=100)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 添加完整的 toolbar
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.mpl)
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.mpl_ntb)
    def update(self,sid = 1):
        self.mpl.load_data(sid)



class BtDataPGChart(pg.GraphicsWindow):
    """"""

    def __init__(self):
        """"""
        super().__init__(title="Backtester Chart")

        self.dates = {}

        self.init_ui()

    def init_ui(self):
        """"""
        pg.setConfigOptions(antialias=True)

        # Create plot widgets
        self.balance_plot = self.addPlot(
            title="账户净值",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.drawdown_plot = self.addPlot(
            title="净值回撤",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.pnl_plot = self.addPlot(
            title="每日盈亏",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.nextRow()

        self.distribution_plot = self.addPlot(title="盈亏分布")

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
        self.pnl_plot.addItem(self.profit_pnl_bar)
        self.pnl_plot.addItem(self.loss_pnl_bar)

        distribution_color = "#6d4c41"
        self.distribution_curve = self.distribution_plot.plot(
            fillLevel=-0.3, brush=distribution_color, pen=distribution_color
        )

    def clear_data(self):
        """"""
        self.balance_curve.setData([], [])
        self.drawdown_curve.setData([], [])
        self.profit_pnl_bar.setOpts(x=[], height=[])
        self.loss_pnl_bar.setOpts(x=[], height=[])
        self.distribution_curve.setData([], [])

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

        # Set data for pnl distribution
        hist, x = np.histogram(df["net_pnl"], bins="auto")
        x = x[:-1]
        self.distribution_curve.setData(x, hist)




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
        self.count = len(self.data) 
    def tickStrings(self, values, scale, spacing):
        """"""
        strings = []
        for v in values:
            if v > self.count:
                return strings
            dt = self.data[int(v)].datetime
            strings.append(dt.strftime('%H:%M\n %d-%b '))
        return strings
    def on_bar(self,bar):
        self.data.append(bar)
        self.count += 1




class PriceAxis(pg.AxisItem):
    def __init__(self):
        super().__init__(orientation='right')
        self.style.update({'textFillLimits': [(0, 0.8)]})

    def tickStrings(self, vals, scale, spacing):
        digts = max(0, np.ceil(-np.log10(spacing * scale)))
        return [
            ('{:<8,.%df}' % digts).format(v).replace(',', ' ') for v in vals
        ]


CHART_MARGINS = (0, 0, 20, 5)
class QuotesChart(QtGui.QWidget):
    signal = QtCore.pyqtSignal(Event)

    long_pen = pg.mkPen('#006000')
    long_brush = pg.mkBrush('#00ff00')
    short_pen = pg.mkPen('#600000')
    short_brush = pg.mkBrush('#ff0000')

    zoomIsDisabled = QtCore.pyqtSignal(bool)

    def __init__(self,symbol:str):
        super().__init__()
        self.full_symbol = symbol
        self.bg = BarGenerator(self.on_bar)
        self.load_bar()
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setHandleWidth(4)
        self.layout.addWidget(self.splitter)
        if self.data:
            self.plot()

    def reset(self,symbol:str):
        self.full_symbol = symbol
        self.bg = BarGenerator(self.on_bar)
        self.load_bar()
        if self.data:
            self.plot()

    def plot(self):
        self.xstart = 60*(self.data[0].datetime.hour - 9) + self.data[0].datetime.minute
        self.xaxis = DateAxis2(self.data, orientation='bottom')
        self.xaxis.setStyle(
            tickTextOffset=7, textFillLimits=[(0, 0.80)], showValues=False
        )
        self.klineitem = CandlestickItem(self.data)
        self.init_chart()
        self.init_quotes_chart()

    def load_bar(self,days:int =1,interval: Interval = Interval.MINUTE):
        symbol, exchange = extract_full_symbol(self.full_symbol)
        end = datetime.now()
        start = end - timedelta(days)

        bars = database_manager.load_bar_data(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start=start,
            end=end,
        )
        self.data = bars

    def on_bar(self,bar):
        self.data.append(bar)
        self.klineitem.on_bar(bar)
    
    def on_tick(self,tick):
        if tick.full_symbol == self.full_symbol:
            self.bg.update_tick(tick)

    def init_quotes_chart(self):
        self.chart.hideAxis('left')
        self.chart.showAxis('right')
        self.chart.addItem(self.klineitem)
        barf = self.data[0]
        bare = self.data[-1]
        tmin = 60*(barf.datetime.hour - 9) + barf.datetime.minute
        tmax = 60*(bare.datetime.hour - 9) + bare.datetime.minute
        pmax = 0
        pmin = 999999
        for bar in self.data:
            pmax = max(pmax,bar.high_price)
            pmin = min(pmin,bar.low_price)
        self.chart.setLimits(
            xMin=tmin,
            xMax=tmax,
            minXRange=60,
            yMin=pmin * 0.95,
            yMax=pmax * 1.05,
        )
        self.chart.showGrid(x=True, y=True)
        self.chart.setCursor(QtCore.Qt.BlankCursor)
        self.chart.sigXRangeChanged.connect(self._update_yrange_limits)


    def _update_yrange_limits(self):
        vr = self.chart.viewRect()
        lbar, rbar = max(0,int(vr.left())-self.xstart), min(len(self.data),int(vr.right())-self.xstart)
        bars = self.data[lbar:rbar]
        pmax = 0
        pmin = 999999
        pmean = 0
        for bar in bars:
            pmax = max(pmax,bar.high_price)
            pmin = min(pmin,bar.low_price)
            pmean += bar.close_price
        pmean = pmean/(len(bars))
        ylow = pmin * 0.95
        yhigh = pmax * 1.05

        self.chart.setLimits(yMin=ylow, yMax=yhigh, minYRange= 3*abs(pmax-pmean))
        self.chart.setYRange(ylow, yhigh)


    def init_chart(self):
        self.chart = pg.PlotWidget(
            parent=self.splitter,
            axisItems={'bottom': self.xaxis, 'right': PriceAxis()},
            enableMenu=False,
        )
        self.chart.getPlotItem().setContentsMargins(*CHART_MARGINS)
        self.chart.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        

















if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtDataViewWidget()
    ui.mpl.load_data(1)  #
    ui.show()
    app.exec_()
