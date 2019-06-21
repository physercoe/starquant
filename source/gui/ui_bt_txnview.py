from source.common.constant import Direction, Offset
from source.common.datastruct import TradeData
from source.gui.ui_basic import QFloatTableWidgetItem
import sys
import csv
from datetime import datetime, date

from PyQt5 import QtCore, QtWidgets, QtGui
import numpy as np
import pyqtgraph as pg
sys.path.insert(0, "..")


class TradesTable(QtWidgets.QTableWidget):
    tradesig = QtCore.pyqtSignal(TradeData)
    cols = np.array(
        [
            ('成交时间', 'datetime'),
            ('合约全称', 'full_symbol'),
            ('买卖方向', 'direction'),
            ('开平方向', 'offset'),
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
            ('净盈亏', 'net_pnl'),
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
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
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

    def show_data(self, item):
        row = item.row()
        if row >= 0:
            timestr = self.item(row, 0).text()
            dt = datetime.strptime(timestr, "%Y.%m.%d %H:%M:%S")
            fullsym = self.item(row, 1).text()
            trade = TradeData(datetime=dt, full_symbol=fullsym)
            self.tradesig.emit(trade)

    def set_data(self, trades):
        if not trades:
            return
        self.setRowCount(len(trades))
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
            ('成交金额', 'turnover'),
            ('手续费用', 'commission'),
            ('滑点费用', 'slippage'),
            ('持仓盈亏', 'holding_pnl'),
            ('交易盈亏', 'trading_pnl'),
            ('总盈亏', 'total_pnl'),
            ('净盈亏', 'net_pnl'),
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
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
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
        if not dailyresults:
            return
        self.setRowCount(len(dailyresults))
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

    def contextMenuEvent(self, event):
        """
        Show menu with right click.
        """
        self.menu.popup(QtGui.QCursor.pos())
