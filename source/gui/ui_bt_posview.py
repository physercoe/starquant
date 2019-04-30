import os,sys,gzip
import random
import pandas as pd
import datetime
from numpy import arange, sin, pi
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

class BtPosViewFC(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)  # 新建一个figure
        self.fig.set_tight_layout(True)
        self.ax_exposures = self.fig.add_subplot(411)
        #self.ax_top_positions = self.fig.add_subplot(412)
        self.ax_holdings = self.fig.add_subplot(412)
        self.ax_long_short_holdings = self.fig.add_subplot(413)
        self.ax_gross_leverage = self.fig.add_subplot(414)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.setMinimumSize(800,1600)
        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def load_data(self,sid):
        print('posview load ',sid)
        for ax in self.fig.axes:
            ax.clear()     
        datapath = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        datapath = datapath + '/../../pyfolio/tests/test_data/'
        test_returns = pd.read_csv(gzip.open(datapath + 'test_returns.csv.gz'), index_col=0, parse_dates=True)
        test_returns = to_series(to_utc(test_returns))
        test_txn = to_utc(pd.read_csv(gzip.open(datapath + 'test_txn.csv.gz'),  index_col=0, parse_dates=True))
        test_pos = to_utc(pd.read_csv(gzip.open(datapath + 'test_pos.csv.gz'),  index_col=0, parse_dates=True))

        positions = utils.check_intraday('infer', test_returns, test_pos, test_txn)
        positions_alloc = pos.get_percent_alloc(positions)
        plotting.plot_exposures(test_returns, positions, ax=self.ax_exposures)
        plotting.plot_holdings(test_returns, positions_alloc, ax=self.ax_holdings)       
        plotting.plot_long_short_holdings(test_returns, positions_alloc, ax=self.ax_long_short_holdings)
        plotting.plot_gross_leverage(test_returns, positions,ax=self.ax_gross_leverage)

        for ax in self.fig.axes:
            plt.setp(ax.get_xticklabels(), visible=True) 
        self.draw()



class BtPosViewWidget(QWidget):
    def __init__(self, parent=None):
        super(BtPosViewWidget, self).__init__(parent)
        self.initui()
    def initui(self):
        self.layout = QVBoxLayout(self)
        self.mpl = BtPosViewFC(self, width=5, height=4, dpi=100)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.mpl)
        self.scroll.setWidgetResizable(True)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  # 添加完整的 toolbar
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.mpl_ntb)
    def update(self,sid=1):
        self.mpl.load_data(sid)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtPosViewWidget()
    ui.mpl.load_data(1)  #
    ui.show()
    app.exec_()
