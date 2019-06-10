import os,sys,gzip
import random
import pandas as pd
from datetime import datetime
from numpy import arange, sin, pi
import warnings
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

import numpy as np
import pyqtgraph as pg
from source.common.constant import Direction,Offset

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



class TradesTable(QtWidgets.QTableWidget):

    cols = np.array(
        [
            ('成交时间', 'datetime'),
            ('合约全称', 'full_symbol'),
            ('买卖方向', 'direction'),
            ('开平方向', 'offset'),
            ('成交价格', 'price'),                 
            ('成交量', 'volume'),
        ]
    )
    colored_cols = (
        'direction',
        'offset'
    )
    fg_positive_color = pg.mkColor('#0000cc')
    fg_negative_color = pg.mkColor('#cc0000')
    bg_positive_color = pg.mkColor('#e3ffe3')
    bg_negative_color = pg.mkColor('#ffe3e3')

    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)
        self.setColumnCount(len(self.cols))
        self.setHorizontalHeaderLabels(self.cols[:, 0])
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.verticalHeader().hide()

    def set_data(self,trades):
        if not trades:
            return
        self.setRowCount(len(trades))
        for irow, trade in enumerate(trades):
            for icol, col in enumerate(self.cols[:, 1]):
                fg_color = None
                if col == 'direction':
                    val, fg_color = (
                        ('▲ 买', QtGui.QColor(255, 174, 201) )
                        if trade.direction == Direction.LONG
                        else ('▼ 卖', QtGui.QColor(160, 255, 160))
                    )
                elif col == 'offset':
                    val = '开' if trade.offset == Offset.OPEN else '平'
                else:
                    val = trade.__getattribute__(col)

                if isinstance(val, float):
                    s_val = '%.2f' % val
                elif isinstance(val, datetime):
                    s_val = val.strftime('%Y.%m.%d %H:%M:%S')
                elif isinstance(val, (int, str, np.int_, np.str_)):
                    s_val = str(val)

                item = QtWidgets.QTableWidgetItem(s_val)
                align = QtCore.Qt.AlignVCenter
                # align |= (
                #     QtCore.Qt.AlignLeft
                #     if col in ('type', 'entry', 'exit')
                #     else QtCore.Qt.AlignRight
                # )
                item.setTextAlignment(align)
                item.setFlags(
                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                )
                # bg_color = (
                #     self.bg_positive_color
                #     if trade.offset == Offset.OPEN
                #     else self.bg_negative_color
                # )
                # item.setBackground(bg_color)

                if col in self.colored_cols:
                    if fg_color is None:
                        fg_color = (
                            QtGui.QColor("red")
                            if trade.offset == Offset.OPEN
                            else QtGui.QColor("green")
                        )
                    item.setForeground(fg_color)
                self.setItem(irow, icol, item)
        self.resizeColumnsToContents()












if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtTxnViewWidget()
    ui.mpl.load_data(1)  #
    ui.show()
    app.exec_()
