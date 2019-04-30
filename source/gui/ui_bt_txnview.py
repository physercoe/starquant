import os,sys,gzip
import random
import pandas as pd
import datetime
from numpy import arange, sin, pi
import warnings
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

sys.path.insert(0,"..")
from pyfolio import plotting
from pyfolio import pos
from pyfolio.utils import (to_utc, to_series)
from pyfolio import utils

class BtTxnViewFC(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)  # 新建一个figure
        self.fig.set_tight_layout(True)
        self.ax_turnover = self.fig.add_subplot(411)
        #self.ax_top_positions = self.fig.add_subplot(412)
        self.ax_daily_volume = self.fig.add_subplot(412)
        self.ax_turnover_hist = self.fig.add_subplot(413)
        self.ax_txn_timings = self.fig.add_subplot(414)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.setMinimumSize(800,1600)
        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def load_data(self,sid):
        print('txnview load ',sid)
        for ax in self.fig.axes:
            ax.clear()     
        datapath = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        datapath = datapath + '/../../pyfolio/tests/test_data/'
        test_returns = pd.read_csv(gzip.open(datapath + 'test_returns.csv.gz'), index_col=0, parse_dates=True)
        test_returns = to_series(to_utc(test_returns))
        test_txn = to_utc(pd.read_csv(gzip.open(datapath + 'test_txn.csv.gz'),  index_col=0, parse_dates=True))
        test_pos = to_utc(pd.read_csv(gzip.open(datapath + 'test_pos.csv.gz'),  index_col=0, parse_dates=True))
        positions = utils.check_intraday('infer', test_returns, test_pos, test_txn)

        plotting.plot_turnover(test_returns, test_txn, positions,  ax=self.ax_turnover)
        plotting.plot_daily_volume(test_returns, test_txn, ax=self.ax_daily_volume)
        try:
            plotting.plot_daily_turnover_hist(test_txn, positions, ax=self.ax_turnover_hist)
        except ValueError:
            warnings.warn('Unable to generate turnover plot.', UserWarning)
        plotting.plot_txn_time_hist(test_txn, ax=self.ax_txn_timings)
        for ax in self.fig.axes:
            plt.setp(ax.get_xticklabels(), visible=True) 
        self.draw()



class BtTxnViewWidget(QWidget):
    def __init__(self, parent=None):
        super(BtTxnViewWidget, self).__init__(parent)
        self.initui()
    def initui(self):
        self.layout = QVBoxLayout(self)
        self.mpl = BtTxnViewFC(self, width=5, height=4, dpi=100)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 添加完整的 toolbar
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.mpl)
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.mpl_ntb)
    def update(self,sid =1):
        self.mpl.load_data(sid)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtTxnViewWidget()
    ui.mpl.load_data(1)  #
    ui.show()
    app.exec_()
