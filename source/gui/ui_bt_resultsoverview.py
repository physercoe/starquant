import os,sys,gzip
import random
import pandas as pd
import datetime
from numpy import arange, sin, pi

import numpy as np
import pyqtgraph as pg


from PyQt5 import QtCore,QtWidgets,QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget,QTableWidget,QTableWidgetItem
import matplotlib as mpl
mpl_agg = 'Qt5Agg'
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import matplotlib.dates as mdates
#print(sys.path)
sys.path.insert(0,"..")
from pyfolio import plotting
from pyfolio.utils import (to_utc, to_series)


class BtResultViewFC(FigureCanvas):
    def __init__(self, parent=None, width=10, height=16, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)  # 新建一个figure
        self.fig.set_tight_layout(True)
        self.ax_rolling_returns = self.fig.add_subplot(511)  #
        self.ax_returns = self.fig.add_subplot(512) 
        self.ax_rolling_volatility = self.fig.add_subplot(513) 
        self.ax_rolling_sharpe = self.fig.add_subplot(514) 
        self.ax_underwater = self.fig.add_subplot(515) 

        #self.axes.hold(False)  
        #self.axes.clear()
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.setMinimumSize(800,2000)
        FigureCanvas.setSizePolicy(self,QSizePolicy.Expanding,QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def load_data(self,sid):
        print('resultview load ',sid)
        for ax in self.fig.axes:
            ax.clear()
        datapath = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        datapath = datapath + '/../../pyfolio/tests/test_data/'
        test_returns = pd.read_csv(gzip.open(datapath + 'test_returns.csv.gz'), index_col=0, parse_dates=True)
        test_returns = to_series(to_utc(test_returns))
        test_txn = to_utc(pd.read_csv(gzip.open(datapath + 'test_txn.csv.gz'),  index_col=0, parse_dates=True))
        test_pos = to_utc(pd.read_csv(gzip.open(datapath + 'test_pos.csv.gz'),  index_col=0, parse_dates=True))
        self.perf_stats = plotting.get_perf_stats(test_returns,positions=test_pos,transactions=test_txn)
        #print(self.perf_stats)
        plotting.plot_rolling_returns(test_returns, ax= self.ax_rolling_returns)
        self.ax_rolling_returns.set_title('Cumulative returns')
        plotting.plot_returns(test_returns, ax=self.ax_returns)
        self.ax_returns.set_title('Returns')
        plotting.plot_rolling_volatility(test_returns, ax=self.ax_rolling_volatility)
        plotting.plot_rolling_sharpe(test_returns, ax=self.ax_rolling_sharpe)        
        plotting.plot_drawdown_underwater(returns=test_returns, ax=self.ax_underwater)

        # self.fig.suptitle('Market Data')
        # self.axes.set_ylabel('静态图：Y轴')
        # self.axes.set_xlabel('静态图：X轴')
        # self.axes.grid(True)
        for ax in self.fig.axes:
           plt.setp(ax.get_xticklabels(), visible=True)
        self.draw()
       



class BtResultViewWidget(QWidget):
    def __init__(self, parent=None):
        super(BtResultViewWidget, self).__init__(parent)
        self.initui()
    def initui(self):
        self.layout = QVBoxLayout(self)
        self.mpl = BtResultViewFC(self, width=8, height=12, dpi=100)
        self.mpl_ntb = NavigationToolbar(self.mpl, self)  
        
        table = QTableWidget()
        headers = ['Annual return',
            'Cumulative returns',
            'Annual volatility',
            'Sharpe ratio',
            'Calmar ratio',
            'Stability',
            'Max drawdown',
            'Omega ratio',
            'Skew',
            'Kurtosis',
            'Daily value at risk',
            'Daily turnover',
            'Gross leverage'
        ]
        headerscn = ['年回报率',
            '累计回报率',
            '年波动率',
            '夏普比',
            '卡莫比',
            '稳定性',
            '最大回撤',
            'Omega',
            '偏度',
            '峰度',
            '日VaR',
            '日换手',
            '杠杆'
        ]
        self.headers = headers
        table.setColumnCount(len(headers))
        table.setRowCount(1)
        table.setHorizontalHeaderLabels(headerscn)
        table.setEditTriggers(table.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        table.setShowGrid(False)
        table.horizontalHeader().setFixedHeight(30)
        table.setFixedHeight(70)
        table.setFont(QtGui.QFont('Microsoft YaHei',14,60))                
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        QtWidgets.QTableWidget.resizeColumnsToContents(table)
        self.indicator = table

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.mpl)
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.indicator)
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.mpl_ntb)
    def update(self,sid = 1):
        self.mpl.load_data(sid)
        for i in range(len(self.headers)):
            j = self.mpl.perf_stats.loc[self.headers[i],'Backtest']
            if isinstance(j,float):
                j = '{0:.2f}'.format(j)
            self.indicator.setItem(0, i, QtWidgets.QTableWidgetItem(str(j)))    





class BacktesterChart(pg.GraphicsWindow):
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
        if df is None:
            return

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






if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = BtResultViewWidget()
    ui.update(1)  #
    ui.show()
    app.exec_()