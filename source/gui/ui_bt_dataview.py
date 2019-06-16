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

from .ui_basic import CandlestickItem,VolumeItem
from ..data.data_board import BarGenerator
from ..common.datastruct import Event
from ..common.utility import extract_full_symbol
from ..data import database_manager
from ..common.constant import Interval,Direction,Offset

sys.path.insert(0,"..")
from pyfolio import plotting
from pyfolio.utils import (to_utc, to_series)
import source.common.sqglobal as sqglobal

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
class BTQuotesChart(QtGui.QWidget):
    signal = QtCore.pyqtSignal(Event)

    short_pen = pg.mkPen('#006000')
    short_brush = pg.mkBrush('#00ff00')
    long_pen = pg.mkPen('#600000')
    long_brush = pg.mkBrush('#ff0000')
    digits = 1

    zoomIsDisabled = QtCore.pyqtSignal(bool)

    def __init__(self,symbol:str = ""):
        super().__init__()
        self.full_symbol = symbol
        self.data = []
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)        
        self.chart = None
        self.charv = None
        self.signals_group_arrow = None
        self.signals_group_text = None
        self.trades_count = 0
        self.signals_text_items = np.empty(self.trades_count, dtype=object)
        self.buy_count_at_x = np.zeros(len(self.data))
        self.sell_count_at_x = np.zeros(len(self.data))
        self.signals_visible = False
        self.plot()

    def reset(self,symbol:str,start: datetime, end: datetime,interval: Interval = Interval.MINUTE, datasource:str = 'DataBase'):
        self.full_symbol = symbol
        self.load_bar(start,end,interval,datasource)
        self.klineitem.generatePicture()
        self.volumeitem.generatePicture()
        if self.signals_group_arrow:
            self.chart.removeItem(self.signals_group_arrow)
            del self.signals_group_arrow
        if self.signals_group_text:            
            self.chart.removeItem(self.signals_group_text)
            del self.signals_group_text
        # del self.signals_text_items


        self.signals_visible = False


    def add_trades(self,trades):
        if not self.data:
            return
        self.buy_count_at_x = np.zeros(len(self.data))
        self.sell_count_at_x = np.zeros(len(self.data))  

        self.signals_group_text = QtGui.QGraphicsItemGroup()
        self.signals_group_arrow = QtGui.QGraphicsItemGroup()
        self.trades_count = len(trades)
        self.signals_text_items = np.empty(len(trades), dtype=object)

        #TODO:here only last signal in bar will show

        id_bar = 0   
        for ix,trade in enumerate(trades):
            if trade.datetime < self.data[0].datetime:             
                continue
            if trade.datetime > self.data[-1].datetime:
                break
            while self.data[id_bar].datetime < trade.datetime :
                id_bar = id_bar +1
            x = id_bar -1
            price = trade.price
            if trade.direction == Direction.LONG:
                self.buy_count_at_x[x] += 1
                ya = self.data[x].low_price * 0.999
                yt = self.data[x].low_price * (1 -0.001*self.buy_count_at_x[x])
                pg.ArrowItem(
                    parent=self.signals_group_arrow,
                    pos=(x, ya),
                    pen=self.long_pen,
                    brush=self.long_brush,
                    angle=90,
                    headLen=12,
                    tipAngle=50,
                )
                opacity = 0
                brush = self.long_brush
                if trade.offset == Offset.CLOSE:
                    opacity = 0.15
                    if trade.short_pnl + trade.long_pnl < 0:
                        brush = self.short_brush 
                text_sig = CenteredTextItem(
                    parent=self.signals_group_text,
                    pos=(x, yt),
                    pen=self.long_pen,
                    brush=brush,
                    text=('{:.%df}' % self.digits).format(price),
                    valign=QtCore.Qt.AlignBottom,
                    opacity=opacity
                )
                text_sig.hide()
            else:
                self.sell_count_at_x[x] += 1
                ya = self.data[x].high_price * 1.001
                yt = self.data[x].low_price * (1 + 0.001*self.sell_count_at_x[x])
                pg.ArrowItem(
                    parent=self.signals_group_arrow,
                    pos=(x, ya),
                    pen=self.short_pen,
                    brush=self.short_brush,
                    angle=-90,
                    headLen=12,
                    tipAngle=50,
                )
                opacity = 0
                brush = self.long_brush
                if trade.offset == Offset.CLOSE:
                    opacity = 0.15
                    if trade.short_pnl + trade.long_pnl < 0:
                        brush = self.short_brush                
                text_sig = CenteredTextItem(
                    parent=self.signals_group_text,
                    pos=(x, yt),
                    pen=self.short_pen,
                    brush=brush,
                    text=('{:.%df}' % self.digits).format(price),
                    valign=QtCore.Qt.AlignTop,
                    opacity=opacity
                )
                text_sig.hide()

            self.signals_text_items[ix] = text_sig       
        self.chart.addItem(self.signals_group_arrow)
        self.chart.addItem(self.signals_group_text)
        self.signals_visible = True

    def show_text_signals(self, lbar=0, rbar=0):
        if rbar == 0:
            rbar = len(self.data)
        signals = []
        for sig in self.signals_text_items:
            if isinstance(sig, CenteredTextItem):                
                x = sig.pos().x()
                if x > lbar and x < rbar:
                    signals.append(sig)

        if len(signals) <= 40:
            for sig in signals:
                sig.show()
        else:
            for sig in signals:
                sig.hide()

    def update_yrange_limits(self):
        if len(self.data) == 0:
            return
        vr = self.chart.viewRect()
        lbar, rbar = int(vr.left()), int(vr.right())
        if lbar < 0:
            lbar = 0
        if rbar > len(self.data):
            rbar = len(self.data)
        ymin = self.data[lbar].low_price
        ymax = self.data[rbar-1].high_price
        for bar in self.data[lbar:rbar]:
            if bar.high_price > ymax:
                ymax = bar.high_price
            if bar.low_price < ymin:
                ymin = bar.low_price
        self.chart.setYRange(ymin*0.996, ymax*1.004)
        if self.signals_visible:
            self.show_text_signals(lbar, rbar) 


    def plot(self):       
        self.xaxis = DateAxis2(self.data, orientation='bottom')
        self.xaxis.setStyle(
            tickTextOffset=7, textFillLimits=[(0, 0.80)], showValues=True
        )
        self.klineitem = CandlestickItem(self.data)
        self.volumeitem = VolumeItem(self.data)
        self.init_chart()
        self.init_chart_item()

    def load_bar(self,start: datetime,end: datetime,interval: Interval = Interval.MINUTE, datasource:str = 'DataBase'):
        symbol, exchange = extract_full_symbol(self.full_symbol)

        if start > end:
            tmp = end
            end = start
            start = tmp

        bars = []
        if datasource == 'DataBase': 
            bars = database_manager.load_bar_data(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start=start,
                end=end,
            )
        elif datasource == 'Memory':
            startix = 0
            endix = 0
            totalbarlist = sqglobal.history_bar[self.full_symbol]
            if not totalbarlist:
                QtWidgets.QMessageBox().information(None, 'Info','No data in memory!',QtWidgets.QMessageBox.Ok)
                return
            totalbars = len(totalbarlist)
            for i in range(totalbars):
                if totalbarlist[i].datetime.date() < start:
                    continue
                startix = i
                break
            for i in reversed(range(totalbars)):
                if totalbarlist[i].datetime.date() > end:
                    continue
                endix = i
                break                
            endix = min(endix+1,totalbars)
            bars = totalbarlist[startix:endix]

        self.data.clear()
        self.data.extend(bars)

    def init_chart_item(self):
        self.chart.addItem(self.klineitem)
        self.chartv.addItem(self.volumeitem)



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
        self.chart.sigXRangeChanged.connect(self.update_yrange_limits)
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
        

class CenteredTextItem(QtGui.QGraphicsTextItem):
    def __init__(
        self,
        text='',
        parent=None,
        pos=(0, 0),
        pen=None,
        brush=None,
        valign=None,
        opacity=0.1,
    ):
        super().__init__(text, parent)

        self.pen = pen
        self.brush = brush
        self.opacity = opacity
        self.valign = valign
        self.text_flags = QtCore.Qt.AlignCenter
        self.setPos(*pos)
        self.setFlag(self.ItemIgnoresTransformations)

    def boundingRect(self):  # noqa
        r = super().boundingRect()
        if self.valign == QtCore.Qt.AlignTop:
            return QtCore.QRectF(-r.width() / 2, -37, r.width(), r.height())
        elif self.valign == QtCore.Qt.AlignBottom:
            return QtCore.QRectF(-r.width() / 2, 15, r.width(), r.height())

    def paint(self, p, option, widget):
        p.setRenderHint(p.Antialiasing, False)
        p.setRenderHint(p.TextAntialiasing, True)
        p.setPen(self.pen)
        if self.brush.style() != QtCore.Qt.NoBrush:
            p.setOpacity(self.opacity)
            p.fillRect(option.rect, self.brush)
            p.setOpacity(1)
        p.drawText(option.rect, self.text_flags, self.toPlainText())















if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtDataViewWidget()
    ui.mpl.load_data(1)  #
    ui.show()
    app.exec_()
