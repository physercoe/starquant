import os,sys,gzip
import random
import pandas as pd
import datetime
import numpy as np
from PyQt5 import QtCore,QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget

import mpl_finance as mpf
from datetime import timedelta
from dateutil.parser import parse

import pyqtgraph as pg

sys.path.insert(0,"../..")

from source.common.datastruct import TickEvent, TickType



class MarketDataView(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(type(TickEvent()))
    symbol_signal = QtCore.pyqtSignal(str)
    def __init__(self):
        """"""
        super(MarketDataView, self).__init__()

        self.full_symbol = ""
        self.init_ui()
        self.register_event() 
    def init_ui(self):
        self.datachart = DataPGChart()
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
        self.symbol_signal.connect(self.orderbook.symbol_signal.emit) 


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


class OrderBookWidget(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(type(TickEvent()))
    symbol_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        """"""
        super(OrderBookWidget, self).__init__()

        self.full_symbol = ""
        self.init_ui()
        self.register_event()
        self.clear_label_text()
    
    def init_ui(self):
        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.setReadOnly(True)


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

        form2 = QtWidgets.QFormLayout()
        titlelabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        titlelabel.setText('OrderBook')

        # pricelable = self.create_label(alignment=QtCore.Qt.AlignLeft)
        # pricelable.setText('Price')
        # volumelable =  self.create_label(alignment=QtCore.Qt.AlignRight)
        # volumelable.setText('Volume')

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

        self.setFixedSize(160,450)

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

    def process_tick_event(self, tick: TickEvent):
        """"""
        if tick.full_symbol != self.full_symbol:
            return
                    # if (tickevent.tick_type == TickType.Bid):
                    #     self.item(row, 4).setText(str(tickevent.size))
                    #     self.item(row, 5).setText(str(tickevent.price))
                    # elif (tickevent.tick_type == TickType.Ask):
                    #     self.item(row, 6).setText(str(tickevent.price))
                    #     self.item(row, 7).setText(str(tickevent.size))
        self.lp_label.setText(str(tick.price))
        self.open_label.setText(str(tick.open))
        self.low_label.setText(str(tick.low))
        self.high_label.setText(str(tick.high))
        self.size_label.setText(str(tick.size))
        self.bp1_label.setText(str(tick.bid_price_L1))
        self.bv1_label.setText(str(tick.bid_size_L1))
        self.ap1_label.setText(str(tick.ask_price_L1))
        self.av1_label.setText(str(tick.ask_size_L1))

        if tick.pre_close != 0.0:
            r = (tick.price / tick.pre_close - 1) * 100
            self.change_label.setText(f"{r:.2f}%")

        if tick.depth == 5:
            self.bp2_label.setText(str(tick.bid_price_L2))
            self.bv2_label.setText(str(tick.bid_size_L2))
            self.ap2_label.setText(str(tick.ask_price_L2))
            self.av2_label.setText(str(tick.ask_size_L2))

            self.bp3_label.setText(str(tick.bid_price_L3))
            self.bv3_label.setText(str(tick.bid_size_L3))
            self.ap3_label.setText(str(tick.ask_price_L3))
            self.av3_label.setText(str(tick.ask_size_L3))

            self.bp4_label.setText(str(tick.bid_price_L4))
            self.bv4_label.setText(str(tick.bid_size_L4))
            self.ap4_label.setText(str(tick.ask_price_L4))
            self.av4_label.setText(str(tick.ask_size_L4))

            self.bp5_label.setText(str(tick.bid_price_L5))
            self.bv5_label.setText(str(tick.bid_size_L5))
            self.ap5_label.setText(str(tick.ask_price_L5))
            self.av5_label.setText(str(tick.ask_size_L5))

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
        self.bv1_label.setText("BV1")
        self.bv2_label.setText("BV2")
        self.bv3_label.setText("BV3")
        self.bv4_label.setText("BV4")
        self.bv5_label.setText("BV5")

        self.av1_label.setText("AV1")
        self.av2_label.setText("AV2")
        self.av3_label.setText("AV3")
        self.av4_label.setText("AV4")
        self.av5_label.setText("AV5")

        self.bp1_label.setText("BP1")
        self.bp2_label.setText("BP2")
        self.bp3_label.setText("BP3")
        self.bp4_label.setText("BP4")
        self.bp5_label.setText("BP5")

        self.ap1_label.setText("AP1")
        self.ap2_label.setText("AP2")
        self.ap3_label.setText("AP3")
        self.ap4_label.setText("AP4")
        self.ap5_label.setText("AP5")













if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MarketDataView()

    ui.show()
    app.exec_()
