import numpy as np

import sys
import csv
from datetime import datetime, date

from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg

from pystarquant.common.constant import Offset
from pystarquant.common.constant import Direction, Offset
from pystarquant.common.datastruct import TradeData
from pystarquant.gui.ui_basic import QFloatTableWidgetItem



class BacktesterChart(pg.GraphicsWindow):
    """"""

    def __init__(self):
        """"""
        super().__init__(title="Backtester Chart")

        self.dates = {}
        self.compare_balance_plotlist = []
        self.init_ui()

    def init_ui(self):
        """"""
        pg.setConfigOptions(antialias=True)

        # Create plot widgets
        self.balance_plot = self.addPlot(
            title="账户净值",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.balance_plot.addLegend()
        self.balance_plot.showAxis('right')
        self.balance_plot.showGrid(x=True,y=True)

        self.nextRow()

        self.drawdown_plot = self.addPlot(
            title="净值回撤",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.drawdown_plot.showAxis('right')
        self.drawdown_plot.showGrid(x=True,y=True)

        self.nextRow()

        self.pnl_plot = self.addPlot(
            title="每日盈亏",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.pnl_plot.showAxis('right')
        self.pnl_plot.showGrid(x=True,y=True)
        self.nextRow()

        self.distribution_plot = self.addPlot(title="盈亏分布")
        self.distribution_plot.showAxis('right')
        self.distribution_plot.showGrid(x=True,y=True)
        self.nextRow()

        self.staticvstrade_plot = self.addPlot(
            title="资金占用",
            axisItems={"bottom": DateAxis(self.dates, orientation="bottom")}
        )
        self.staticvstrade_plot.showAxis('right')
        self.staticvstrade_plot.showGrid(x=True,y=True)

        # Add curves and bars on plot widgets
        self.balance_curve = self.balance_plot.plot(
            pen=pg.mkPen("#ffc107", width=3),name='balance'
        )
        self.beta_curve = self.balance_plot.plot(
            pen=pg.mkPen("g", width=1),name='beta'
        )        
        self.alpha_curve = self.balance_plot.plot(
            pen=pg.mkPen("r", width=1),name='alpha'
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

        self.static_curve = self.staticvstrade_plot.plot(
            pen=pg.mkPen("#ffc107", width=3)
        )

    def clear_data(self):
        """"""
        self.balance_curve.setData([], [])
        self.beta_curve.setData([], [])
        self.alpha_curve.setData([], [])

        self.drawdown_curve.setData([], [])
        self.profit_pnl_bar.setOpts(x=[], height=[])
        self.loss_pnl_bar.setOpts(x=[], height=[])
        self.distribution_curve.setData([], [])
        self.static_curve.setData([], [])


                

    def set_data(self, df):
        """"""
        if df is None:
            return
        self.clear_data()
        
        count = len(df)

        self.dates.clear()
        for n, date in enumerate(df.index):
            self.dates[n] = date

        # Set data for curve of balance and drawdown
        self.balance_curve.setData(df["balance"])
        if df["close_price"].iloc[0]:            
            capindex = np.where(df["maxmargin"] !=0)[0][0]
            multiplier = df["maxmargin"].iloc[capindex] / df["close_price"].iloc[capindex]
            baseline = df["balance"].iloc[0] -multiplier*df["close_price"].iloc[0] + multiplier*df["close_price"]
            print(multiplier)
            self.beta_curve.setData(baseline)
            self.alpha_curve.setData(df["balance"] - baseline + df["balance"].iloc[0])

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

        self.static_curve.setData(df["maxmargin"])


    def set_trade(self, trades):
        pass
        # if not trades:
        #     return
        # staticlist = []
        # net_pnl = 0
        # for trade in trades:
        #     if trade.offset == Offset.CLOSE:
        #         net_pnl += trade.short_pnl + trade.long_pnl - trade.slippage - trade.commission
        #         staticlist.append(net_pnl)

        # self.static_curve.setData(staticlist)

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


class StatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "total_net_pnl": "总盈亏",
        "long_profit":"多头盈亏",
        "short_profit":"空头盈亏",
        "return_turnover":"成交额收益率",
        "total_return": "总收益率",
        "annual_return": "年化收益",
        "daily_net_pnl": "日均盈亏",
        "daily_return": "日均收益率",
        "profit_per_trade":"每笔平均收益",
        "long_profit_per_trade":"多头每笔盈亏",
        "short_profit_per_trade":"空头每笔盈亏",

    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        # vertical layout
        # self.setRowCount(len(self.KEY_NAME_MAP))
        # self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))


        # self.setColumnCount(1)
        # self.horizontalHeader().setVisible(False)
        # self.horizontalHeader().setSectionResizeMode(
        #     QtWidgets.QHeaderView.Stretch
        # )
        # self.setEditTriggers(self.NoEditTriggers)

        # for row, key in enumerate(self.KEY_NAME_MAP.keys()):
        #     cell = QtWidgets.QTableWidgetItem()
        #     self.setItem(row, 0, cell)
        #     self.cells[key] = cell
        # self.setMinimumHeight(450)
        # # self.setFixedWidth(200)

        # horizental layout


        self.setRowCount(1)
        self.setColumnCount(len(self.KEY_NAME_MAP))
        self.setHorizontalHeaderLabels(list(self.KEY_NAME_MAP.values()))
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setFamily('Arial')        
        # font.setBold(True)
        head = self.horizontalHeader()
        head.setFont(font)


        for column, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            cell.setTextAlignment(QtCore.Qt.AlignHCenter)
            self.setItem(0, column, cell)
            self.cells[key] = cell
        self.setMinimumWidth(600)
        self.setMaximumHeight(70)
        # self.setFixedWidth(200)



    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):

        """"""
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setFamily('Arial')        
        font.setBold(True)

        data["capital"] = f"{data['capital']:,.2f}"
        data["end_balance"] = f"{data['end_balance']:,.2f}"
        data["total_return"] = f"{data['total_return']:,.2f}%"
        data["annual_return"] = f"{data['annual_return']:,.2f}%"
        data["return_turnover"] = f"{data['return_turnover']:,.2f}%%" 
        data["total_net_pnl"] = f"{data['total_net_pnl']:,.2f}"
        data["long_profit"] = f"{data['long_profit']:,.2f}"
        data["short_profit"] = f"{data['short_profit']:,.2f}"
        data["profit_per_trade"] = f"{data['profit_per_trade']:,.4f}"
        data["long_profit_per_trade"] = f"{data['long_profit_per_trade']:,.4f}"
        data["short_profit_per_trade"] = f"{data['short_profit_per_trade']:,.4f}"

        data["daily_net_pnl"] = f"{data['daily_net_pnl']:,.4f}"
        data["daily_return"] = f"{data['daily_return']:,.2f}%"

        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))
            cell.setFont(font)

        # self.resizeColumnsToContents()



class RiskStatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "sharpe_ratio": "夏普比率",
        "return_std": "收益标准差",
        "mar":'MAR',
        "return_drawdown_ratio": "收益回撤比",
        "max_drawdown": "最大回撤",
        "max_ddpercent": "百分比最大回撤",
        "max_drawdown_capital":"本金最大回撤比",
        "max_drawdown_duration":"最长回撤天数",
        "recent_drawdown":"最近回撤",
        "recent_ddpercent":"最近回撤百分比",
    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        # vertical layout
        # self.setRowCount(len(self.KEY_NAME_MAP))
        # self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))


        # self.setColumnCount(1)
        # self.horizontalHeader().setVisible(False)
        # self.horizontalHeader().setSectionResizeMode(
        #     QtWidgets.QHeaderView.Stretch
        # )
        # self.setEditTriggers(self.NoEditTriggers)

        # for row, key in enumerate(self.KEY_NAME_MAP.keys()):
        #     cell = QtWidgets.QTableWidgetItem()
        #     self.setItem(row, 0, cell)
        #     self.cells[key] = cell
        # self.setMinimumHeight(450)
        # # self.setFixedWidth(200)

        # horizental layout
        self.setRowCount(1)
        self.setColumnCount(len(self.KEY_NAME_MAP))
        self.setHorizontalHeaderLabels(list(self.KEY_NAME_MAP.values()))
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)

        for column, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            cell.setTextAlignment(QtCore.Qt.AlignHCenter)
            self.setItem(0, column, cell)
            self.cells[key] = cell
        self.setMinimumWidth(600)
        self.setMaximumHeight(70)
        # self.setFixedWidth(200)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setFamily('Arial')        
        # font.setBold(True)
        head = self.horizontalHeader()
        head.setFont(font)


    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):
        """"""
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setFamily('Arial')        
        font.setBold(True)
        if data["capital"]:
            data["max_drawdown_capital"] =  data["max_drawdown"]*100/data["capital"]
        else:
            data["max_drawdown_capital"] = 0.0
        data['mar'] = data["annual_return"]*data["capital"]/(abs(data["max_drawdown"]) + 1e-4)


        data["max_drawdown"] = f"{data['max_drawdown']:,.2f}"
        data["max_ddpercent"] = f"{data['max_ddpercent']:,.2f}%"        
        data["max_drawdown_capital"] = f"{data['max_drawdown_capital']:,.2f}%"
        data["recent_drawdown"] = f"{data['recent_drawdown']:,.2f}"
        data["recent_ddpercent"] = f"{data['recent_ddpercent']:,.2f}%"        
        data["return_std"] = f"{data['return_std']:,.2f}%"
        data["sharpe_ratio"] = f"{data['sharpe_ratio']:,.2f}"
        data["return_drawdown_ratio"] = f"{data['return_drawdown_ratio']:,.2f}"
        data['mar'] = f"{data['mar']:,.2f}"
        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))
            cell.setFont(font)

        # self.resizeColumnsToContents()



class TxnStatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "total_days": "总交易日数",
        "total_trade_count": "总成交次数",
        "long_count":"多头交易次数",
        "short_count":"空头交易次数",
        "total_turnover": "总成交额/万",
        "total_commission": "总手续费",
        "total_slippage": "总滑点",
        "daily_turnover": "日均成交额/万",
        "daily_trade_count": "日均成交笔数",
        "daily_commission": "日均手续费",
        "daily_slippage": "日均滑点",
        "maxmargin": '日最大资金/万',
    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        # vertical layout
        # self.setRowCount(len(self.KEY_NAME_MAP))
        # self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        # self.setColumnCount(1)
        # self.horizontalHeader().setVisible(False)
        # self.horizontalHeader().setSectionResizeMode(
        #     QtWidgets.QHeaderView.Stretch
        # )
        # self.setEditTriggers(self.NoEditTriggers)

        # for row, key in enumerate(self.KEY_NAME_MAP.keys()):
        #     cell = QtWidgets.QTableWidgetItem()
        #     self.setItem(row, 0, cell)
        #     self.cells[key] = cell
        # self.setMinimumHeight(450)
        # # self.setFixedWidth(200)


        # horizontal layout
        self.setRowCount(1)
        self.setColumnCount(len(self.KEY_NAME_MAP))
        self.setHorizontalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)

        for column, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            cell.setTextAlignment(QtCore.Qt.AlignHCenter)
            self.setItem(0, column, cell)
            self.cells[key] = cell
        self.setMinimumWidth(600)
        self.setMaximumHeight(70)

        font = QtGui.QFont()
        font.setPointSize(11)
        font.setFamily('Arial')        
        # font.setBold(True)
        head = self.horizontalHeader()
        head.setFont(font)


    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):
        """"""
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setFamily('Arial')        
        font.setBold(True)
        data["total_commission"] = f"{data['total_commission']:,.2f}"
        data["total_slippage"] = f"{data['total_slippage']:,.2f}"
        data["total_turnover"] = f"{data['total_turnover']/10000.0:,.2f}"
        data["daily_commission"] = f"{data['daily_commission']:,.2f}"
        data["daily_slippage"] = f"{data['daily_slippage']:,.2f}"
        data["daily_turnover"] = f"{data['daily_turnover']/10000.0:,.2f}"
        data["daily_trade_count"] = f"{data['daily_trade_count']:,.3f}"   
        data["maxmargin"] = f"{data['maxmargin']/10000.0:,.2f}"
        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))
            cell.setFont(font)
        # self.resizeColumnsToContents()


class RatioStatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "profit_days": "盈利交易日数",
        "loss_days": "亏损交易日数",
        "win_ratio": "胜率",
        "long_win_ratio":"多头胜率",
        "short_win_ratio":"空头胜率",
        "win_loss": "盈亏比",
        "long_win_loss": "多头盈亏比",
        "short_win_loss": "空头盈亏比",
    }

    def __init__(self):
        """"""
        super().__init__()

        self.cells = {}

        self.init_ui()

    def init_ui(self):
        """"""
        # vertical layout
        # self.setRowCount(len(self.KEY_NAME_MAP))
        # self.setVerticalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        # self.setColumnCount(1)
        # self.horizontalHeader().setVisible(False)
        # self.horizontalHeader().setSectionResizeMode(
        #     QtWidgets.QHeaderView.Stretch
        # )
        # self.setEditTriggers(self.NoEditTriggers)

        # for row, key in enumerate(self.KEY_NAME_MAP.keys()):
        #     cell = QtWidgets.QTableWidgetItem()
        #     self.setItem(row, 0, cell)
        #     self.cells[key] = cell
        # self.setMinimumHeight(450)
        # # self.setFixedWidth(200)


        # horizontal layout
        self.setRowCount(1)
        self.setColumnCount(len(self.KEY_NAME_MAP))
        self.setHorizontalHeaderLabels(list(self.KEY_NAME_MAP.values()))

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.setEditTriggers(self.NoEditTriggers)

        for column, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem()
            cell.setTextAlignment(QtCore.Qt.AlignHCenter)
            self.setItem(0, column, cell)
            self.cells[key] = cell
        self.setMinimumWidth(600)
        self.setMaximumHeight(70)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setFamily('Arial')        
        # font.setBold(True)
        head = self.horizontalHeader()
        head.setFont(font)



    def clear_data(self):
        """"""
        for cell in self.cells.values():
            cell.setText("")

    def set_data(self, data: dict):
        """"""
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setFamily('Arial')        
        font.setBold(True)

        data["win_ratio"] = f"{data['win_ratio']:,.2f}"
        data["long_win_ratio"] = f"{data['long_win_ratio']:,.2f}"
        data["short_win_ratio"] = f"{data['short_win_ratio']:,.2f}"
        data["win_loss"] = f"{data['win_loss']:,.2f}"
        data["long_win_loss"] = f"{data['long_win_loss']:,.2f}"
        data["short_win_loss"] = f"{data['short_win_loss']:,.2f}"        

        for key, cell in self.cells.items():
            value = data.get(key, "")
            cell.setText(str(value))
            cell.setFont(font)
        # self.resizeColumnsToContents()










class TradesTable(QtWidgets.QTableWidget):
    tradesig = QtCore.pyqtSignal(TradeData)
    cols = np.array(
        [
            ('成交时间', 'datetime'),
            ('合约全称', 'full_symbol'),
            ('买卖方向', 'direction'),
            ('开平方向', 'offset'),
            ('净盈亏', 'net_pnl'),
            ('成交价格', 'price'),
            ('成交数量', 'volume'),
            ('成交金额', 'turnover'),
            ('手续费用', 'commission'),
            ('滑点费用', 'slippage'),
            ('多仓数量', 'long_pos'),
            ('多仓开仓价格', 'long_price'),
            ('多仓平仓盈亏', 'long_pnl'),
            ('空仓数量', 'short_pos'),
            ('空仓开仓价格', 'short_price'),
            ('空仓平仓盈亏', 'short_pnl'),
        ]
    )
    colored_cols = (
        'direction',
        'long_pnl',
        'short_pnl',
        'net_pnl'
    )
    numerical_cols = (
        'price',
        'volume',
        'turnover',
        'commission',
        'slippage',
        'long_pos',
        'long_price',
        'long_pnl',
        'short_pos',
        'short_price',
        'short_pnl',
        'net_pnl'
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
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.itemDoubleClicked.connect(self.show_data)
        self.init_menu()
        self.trades = []

    def init_menu(self):
        self.menu = QtWidgets.QMenu(self)

        save_action = QtWidgets.QAction("保存显示的数据", self)
        save_action.triggered.connect(self.save_csv)

        saveall_action = QtWidgets.QAction("保存全部数据", self)
        saveall_action.triggered.connect(lambda: self.save_trade_csv(self.trades))

        clear_action = QtWidgets.QAction("清空显示", self)
        clear_action.triggered.connect(lambda: self.setRowCount(0))
        find_action = QtWidgets.QAction("显示指定条件的记录",self)
        find_action.triggered.connect(self.find_trades)
        
        self.menu.addAction(save_action)
        self.menu.addAction(saveall_action)
        self.menu.addAction(clear_action)
        self.menu.addAction(find_action)

        self.setToolTip("大于1000的交易记录将自动直接保存到Result下csv文件，不直接显示")

    def find_trades(self):
        dialog = FindSettingEditor()
        i = dialog.exec()
        if i != dialog.Accepted:
            return
        filter = dialog.get_setting()
        filteredtrades = []
        for trade in self.trades:
            if trade.datetime < filter['start'] or trade.datetime > filter['end']:
                continue
            if filter['direction'] and trade.direction.value != filter['direction']:
                continue
            if filter['offset'] and trade.offset.value != filter['offset']:
                continue
            if filter['symbol'] and (trade.full_symbol not in filter['symbol']):
                continue
            val = trade.short_pnl + trade.long_pnl - trade.slippage - trade.commission
            if filter['netlower'] != None and val < filter['netlower']:
                continue
            if filter['netupper'] != None and val > filter['netupper']:
                continue
            filteredtrades.append(trade)
        self.setRowCount(0)
        if not filteredtrades:
            QtWidgets.QMessageBox().information(
                None, 'Info', '0 filtered records!', QtWidgets.QMessageBox.Ok)
            return        
        if len(filteredtrades) > 1000:
            self.save_trade_csv(filteredtrades, 'Result/tradesfiltered.csv')
            QtWidgets.QMessageBox().information(
                None, 'Info', f'{len(filteredtrades)} filtered records, save to Result/tradesfiltered.csv!', QtWidgets.QMessageBox.Ok)
            return
        
        self.showtrades(filteredtrades)
       

    def save_csv(self):
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV(*.csv)")

        if not path:
            return
        self.setSortingEnabled(False)
        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")

            writer.writerow(self.cols[:, 0])

            for row in range(self.rowCount()):
                row_data = []
                for column in range(self.columnCount()):
                    item = self.item(row, column)
                    if item:
                        row_data.append(str(item.text()))
                    else:
                        row_data.append("")
                writer.writerow(row_data)
        self.setSortingEnabled(True)

    def save_trade_csv(self, trades, path:str = "Result/trades.csv"):
        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(self.cols[:, 1])            
            for trade in trades:
                row_data = []
                for icol, col in enumerate(self.cols[:, 1]):
                    fg_color = None
                    if col == 'direction':
                        val = trade.direction.value
                    elif col == 'offset':
                        val = trade.offset.value
                    elif col == 'net_pnl':
                        val = trade.short_pnl + trade.long_pnl - trade.slippage - trade.commission
                    else:
                        val = trade.__getattribute__(col)

                    if isinstance(val, float):
                        s_val = '%.2f' % val
                    elif isinstance(val, datetime):
                        s_val = val.strftime('%Y.%m.%d %H:%M:%S')
                    elif isinstance(val, (int, str, np.int_, np.str_)):
                        s_val = str(val)
                    row_data.append(s_val)
                writer.writerow(row_data)
            

    def show_data(self, item):
        row = item.row()
        if row >= 0:
            timestr = self.item(row, 0).text()
            dt = datetime.strptime(timestr, "%Y.%m.%d %H:%M:%S")
            fullsym = self.item(row, 1).text()
            trade = TradeData(datetime=dt, full_symbol=fullsym)
            self.tradesig.emit(trade)

    def showtrades(self,trades):
        self.setRowCount(len(trades))
        self.setSortingEnabled(False)
        for irow, trade in enumerate(trades):
            for icol, col in enumerate(self.cols[:, 1]):
                fg_color = None
                if col == 'direction':
                    if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
                        val, fg_color = ('▲ 买', QtGui.QColor(255, 174, 201))
                    elif trade.direction == Direction.LONG and trade.offset == Offset.CLOSE:
                        val, fg_color = ('▵ 买', QtGui.QColor(255, 174, 201))
                    elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
                        val, fg_color = ('▼ 卖', QtGui.QColor(160, 255, 160))
                    elif trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
                        val, fg_color = ('▿ 卖', QtGui.QColor(160, 255, 160))
                elif col == 'offset':
                    val = '开' if trade.offset == Offset.OPEN else '平'
                elif col == 'net_pnl':
                    val = trade.short_pnl + trade.long_pnl - trade.slippage - trade.commission
                else:
                    val = trade.__getattribute__(col)

                if isinstance(val, float):
                    s_val = '%.2f' % val
                elif isinstance(val, datetime):
                    s_val = val.strftime('%Y.%m.%d %H:%M:%S')
                elif isinstance(val, (int, str, np.int_, np.str_)):
                    s_val = str(val)

                item = QtWidgets.QTableWidgetItem(s_val)
                if col in self.numerical_cols:
                    item = QFloatTableWidgetItem(s_val)
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
                        if trade.offset == Offset.CLOSE:
                            fg_color = (
                                QtGui.QColor("red")
                                if val > 0
                                else QtGui.QColor("green")
                            )
                        else:
                            fg_color = QtGui.QColor("white")
                    item.setForeground(fg_color)
                self.setItem(irow, icol, item)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
    def set_data(self, trades):
        self.trades  = trades
        self.setRowCount(0)
        if not trades:
            return        
        if len(trades) > 1000:
            self.save_trade_csv(trades)
            QtWidgets.QMessageBox().information(
                None, 'Info', f'{len(trades)} records, save to Result/trades.csv!', QtWidgets.QMessageBox.Ok)
            return
        
        self.showtrades(trades)


    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())


class DailyTable(QtWidgets.QTableWidget):
    tradesig = QtCore.pyqtSignal(TradeData)
    cols = np.array(
        [
            ('日期', 'date'),
            ('成交笔数', 'trade_count'),
            ('开盘净持仓', 'start_pos'),
            ('收盘净持仓', 'end_pos'),
            ('净盈亏', 'net_pnl'),
            ('成交金额', 'turnover'),
            ('手续费用', 'commission'),
            ('滑点费用', 'slippage'),
            ('持仓盈亏', 'holding_pnl'),
            ('交易盈亏', 'trading_pnl'),
            ('总盈亏', 'total_pnl'),
        ]
    )
    colored_cols = (
        'start_pos',
        'end_pos',
        'holding_pnl',
        'trading_pnl',
        'total_pnl',
        'net_pnl'
    )
    numerical_cols = (
        'trade_count',
        'turnover',
        'commission',
        'slippage',
        'holding_pnl',
        'trading_pnl',
        'total_pnl',
        'net_pnl'
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
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.itemDoubleClicked.connect(self.show_data)
        self.init_menu()

    def init_menu(self):
        self.menu = QtWidgets.QMenu(self)

        save_action = QtWidgets.QAction("保存数据", self)
        save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)

    def save_csv(self):
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV(*.csv)")

        if not path:
            return
        self.setSortingEnabled(False)
        with open(path, "w") as f:
            writer = csv.writer(f, lineterminator="\n")

            writer.writerow(self.cols[:, 0])

            for row in range(self.rowCount()):
                row_data = []
                for column in range(self.columnCount()):
                    item = self.item(row, column)
                    if item:
                        row_data.append(str(item.text()))
                    else:
                        row_data.append("")
                writer.writerow(row_data)
        self.setSortingEnabled(True)

    def show_data(self, item):
        row = item.row()
        pass
        # if row >= 0:
        #     timestr = self.item(row,0).text()
        #     dt = datetime.strptime(timestr, "%Y.%m.%d %H:%M:%S")
        #     fullsym = self.item(row,1).text()
        #     trade = TradeData(datetime=dt,full_symbol=fullsym)
        #     self.tradesig.emit(trade)

    def set_data(self, dailyresults):
        self.setRowCount(0)
        if not dailyresults:
            return
        self.setRowCount(len(dailyresults))
        self.setSortingEnabled(False)
        for irow, trade in enumerate(dailyresults):
            for icol, col in enumerate(self.cols[:, 1]):
                fg_color = None
                if col == 'start_pos' or col == 'end_pos':
                    val = trade.__getattribute__(col)
                    if val > 0:
                        val = "多 " + str(val)
                        fg_color = QtGui.QColor("red")
                    elif val < 0:
                        val = '空 ' + str(abs(val))
                        fg_color = QtGui.QColor("green")
                    else:
                        fg_color = QtGui.QColor("white")
                else:
                    val = trade.__getattribute__(col)

                if isinstance(val, float):
                    s_val = '%.2f' % val
                elif isinstance(val, date):
                    s_val = val.strftime('%Y.%m.%d')
                elif isinstance(val, (int, str, np.int_, np.str_)):
                    s_val = str(val)

                item = QtWidgets.QTableWidgetItem(s_val)
                if col in self.numerical_cols:
                    item = QFloatTableWidgetItem(s_val)
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
                        if val > 0:
                            fg_color = QtGui.QColor("red")
                        elif val < 0:
                            fg_color = QtGui.QColor("green")
                        else:
                            fg_color = QtGui.QColor("white")
                    item.setForeground(fg_color)
                self.setItem(irow, icol, item)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())




def drawdown(x):
    y = np.cumsum(x)
    return np.max(y)-np.max(y[-1:])

class FindSettingEditor(QtWidgets.QDialog):
    """
    For creating finditems parameters.
    """

    def __init__(self):
        """"""
        super().__init__()

        self.edits = {}
        self.init_ui()

    def init_ui(self):
        """"""
        QLabel = QtWidgets.QLabel
        self.setWindowTitle("筛选设置")

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QLabel("时间范围"), 0, 0)
        grid.addWidget(QLabel("起始"), 0, 1)
        grid.addWidget(QLabel("结束"), 0, 3)
        self.start_date_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.start_date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.end_date_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.end_date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        grid.addWidget(self.start_date_edit, 0, 2)
        grid.addWidget(self.end_date_edit, 0, 4)


        grid.addWidget(QLabel("合约全称"), 1, 0)
        self.symboledit = QtWidgets.QLineEdit('')
        grid.addWidget(self.symboledit,1, 1, 1, 4)

        grid.addWidget(QLabel("买卖方向"), 2, 0)
        self.directioncombo = QtWidgets.QComboBox()
        self.directioncombo.addItems(['',Direction.LONG.value, Direction.SHORT.value])
        grid.addWidget(self.directioncombo, 2, 1, 1, 2)

        grid.addWidget(QLabel("开平方向"), 2, 3)
        self.offsetcombo = QtWidgets.QComboBox()
        self.offsetcombo.addItems(['', Offset.OPEN.value, Offset.CLOSE.value])
        grid.addWidget(self.offsetcombo, 2, 4)

        grid.addWidget(QLabel("净盈亏"), 3, 0)
        grid.addWidget(QLabel("下限"), 3, 1)
        self.netloweredit = QtWidgets.QLineEdit('')
        grid.addWidget(self.netloweredit, 3, 2)
        grid.addWidget(QLabel("上限"), 3, 3)
        self.netupperedit = QtWidgets.QLineEdit('')
        grid.addWidget(self.netupperedit,3, 4)

        button_text = "确定"
        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        grid.addWidget(button, 4, 0, 1, 5)

        self.setLayout(grid)

    def get_setting(self):
        """"""
        setting = {}

        setting['start'] = self.start_date_edit.dateTime().toPyDateTime()
        setting['end'] = self.end_date_edit.dateTime().toPyDateTime()

        symbols = self.symboledit.text()
        if symbols:
            tmp = symbols.split(',')
            setting['symbol'] = [ s.strip() for s in tmp]
        else:
            setting['symbol'] = []
        setting['direction'] = self.directioncombo.currentText()
        setting['offset'] = self.offsetcombo.currentText()

        setting['netlower'] = None if (not self.netloweredit.text()) else float(self.netloweredit.text())
        setting['netupper'] = None if (not self.netupperedit.text()) else float(self.netupperedit.text())

        return setting





class OptimizationResultMonitorWidget(QtWidgets.QTableWidget):
    """
    For viewing optimization result.
    """

    DISPLAY_NAME_MAP = {
        "总收益率": "total_return",
        "夏普比率": "sharpe_ratio",
        "收益回撤比": "return_drawdown_ratio",
        "成交额收益率":"return_turnover",
        "最大回撤":"max_drawdown",
        "最近回撤":"recent_drawdown",

    }


    def __init__(
        self, result_values: list=[], target_display: str='夏普比率'
    ):
        """"""
        super().__init__()

        self.result_values = result_values
        self.target_display = target_display

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("参数优化结果")
        self.resize(600, 500)
       

        self.setColumnCount(1+len(self.DISPLAY_NAME_MAP))
        self.setRowCount(len(self.result_values))
        tableheader = [name for name in self.DISPLAY_NAME_MAP.keys() if name != self.target_display]
        tableheader.insert(0, self.target_display)
        tableheader.insert(0,"参数")
        # table.setHorizontalHeaderLabels(["参数", self.target_display])
        self.setHorizontalHeaderLabels(tableheader)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)

        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        # table.horizontalHeader().setSectionResizeMode(
        #     1, QtWidgets.QHeaderView.Stretch
        # )



    def set_data(self,result_values: list,target_display:str):

        self.result_values = result_values
        self.target_display = target_display
        self.setRowCount(0)
        self.setRowCount(len(self.result_values))


        tableheader = [name for name in self.DISPLAY_NAME_MAP.keys() if name != self.target_display]
        tableheader.insert(0, self.target_display)
        tableheader.insert(0,"参数")
        self.setHorizontalHeaderLabels(tableheader)
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().setVisible(False)

        for n, tp in enumerate(self.result_values):
            setting, target_value, statistics = tp
            tmpstr = ''
            for k,v in setting.items():
                tmpstr += f"{k}={round(v,2)}; "
            setting_cell = QtWidgets.QTableWidgetItem(tmpstr)
            target_cell = QtWidgets.QTableWidgetItem(str(round(target_value,2)))

            setting_cell.setTextAlignment(QtCore.Qt.AlignCenter)
            target_cell.setTextAlignment(QtCore.Qt.AlignCenter)

            self.setItem(n, 0, setting_cell)
            self.setItem(n, 1, target_cell)
            for i in range(2,len(tableheader)):
                othertarget = tableheader[i]
                key = self.DISPLAY_NAME_MAP[othertarget]
                value = statistics[key]
                if key == "total_return":
                    svalue = f"{value:,.2f}%"
                elif key in ["sharpe_ratio","return_drawdown_ratio","max_drawdown","recent_drawdown"]: 
                    svalue = f"{value:,.2f}"
                elif key == 'return_turnover':
                    svalue = f"{value:,.2f}%%"
                else:
                    svalue = ''
                other_cell = QtWidgets.QTableWidgetItem(svalue)
                other_cell.setTextAlignment(QtCore.Qt.AlignCenter)
                self.setItem(n, i, other_cell)



