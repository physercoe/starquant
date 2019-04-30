import os,sys,gzip
import random
import pandas as pd
import datetime
import numpy as np
from PyQt5 import QtCore,QtWidgets
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
from datetime import timedelta
from dateutil.parser import parse
from matplotlib.pylab import date2num

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtDataViewWidget()
    ui.mpl.load_data(1)  #
    ui.show()
    app.exec_()
