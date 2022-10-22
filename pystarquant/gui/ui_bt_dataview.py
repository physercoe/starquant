
import sys
import os
import numpy as np
from pathlib import Path
import importlib
import traceback
from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import datetime, timedelta
import pyqtgraph as pg
import random

import pystarquant.common.sqglobal as SQGlobal
from pystarquant.gui.ui_basic import (
    CandlestickItem, 
    VolumeItem,
    CenteredTextItem,
    OFTextItem,
    DateAxis,
    DateAxis2,
    VolumeAxis,
    OpenInterestAxis,
    PriceAxis
)
from pystarquant.common.datastruct import Event, TickData
from pystarquant.common.utility import extract_full_symbol
from pystarquant.data import database_manager
from pystarquant.common.constant import Interval, Direction, Offset
from pystarquant.strategy.strategy_base import IndicatorBase

sys.path.insert(0, "..")


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

        # self.drawdown_plot.setXLink(self.balance_plot)

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

CHART_MARGINS = (0, 0, 20, 10)


class BTQuotesChart(QtWidgets.QWidget):
    signal = QtCore.pyqtSignal(Event)

    short_pen = pg.mkPen('#00ffff')
    short_brush = pg.mkBrush('#00ffff')
    long_pen = pg.mkPen('r')
    long_brush = pg.mkBrush('#ff0000')
    digits = 1

    zoomIsDisabled = QtCore.pyqtSignal(bool)

    def __init__(self, dbtype: str = "Bar"):
        super().__init__()
        self.full_symbol = ''
        self.data = []
        self.db_type = dbtype   
        self.combo_setting = []
        self.combo_op = '+'
        self.indicator_classes = {}    # name->indictor
        self.indicator = None
        self.settings = {}
        self.chart = None
        self.charv = None
        self.signals_group_arrow = None
        self.isignals_group_arrow = None # secondary pic
        self.psignals_group_arrow = None # primary pic



        self.signals_group_text = None

        self.orderflow_group_text = None 
        self.orderflow_items = np.empty(len(self.data), dtype=object)
        self.orderflow_visible = False

        self.trades_count = 0
        self.signals_text_items = np.empty(self.trades_count, dtype=object)
        self.buy_count_at_x = np.zeros(len(self.data))
        self.sell_count_at_x = np.zeros(len(self.data))
        self.signals_visible = False
        self.init_ui()


    def reset(self, 
        combo_symbol: tuple, 
        start: datetime, 
        end: datetime, 
        interval: Interval = Interval.MINUTE, 
        datasource: str = 'DataBase',
        dbcollection: str = 'db_bar_data'        
        ):

        # TODO:add combo symbols,now only single
        self.combo_setting = combo_symbol[0]
        self.combo_op = combo_symbol[1]            
        symbol = combo_symbol[0][0][0]
        self.full_symbol = symbol

        if self.db_type == 'Bar':
            self.load_bar(start, end, interval, datasource,dbcollection)
            self.klineitem.generatePicture()
        elif self.db_type == 'TbtBar':
            self.load_tbtbar(start, end, interval, datasource,dbcollection)
            self.klineitem.generatePicture()            
        elif self.db_type == 'Tick':    
            self.load_tick(start, end, datasource,dbcollection)
            self.pcurve.setData([t.last_price for t in self.data])    


        if self.signals_group_arrow:
            self.chart.removeItem(self.signals_group_arrow)
            del self.signals_group_arrow
        if self.isignals_group_arrow:
            self.chartv.removeItem(self.isignals_group_arrow)
            del self.isignals_group_arrow   
        if self.psignals_group_arrow:
            self.chart.removeItem(self.psignals_group_arrow)
            del self.psignals_group_arrow              

        if self.signals_group_text:
            self.chart.removeItem(self.signals_group_text)
            del self.signals_group_text

        if self.orderflow_group_text:
            self.chart.removeItem(self.orderflow_group_text)
            del self.orderflow_group_text

        # del self.signals_text_items
        self.signals_visible = False
        self.orderflow_visible = False

        self.update_indicator()
        self.chart.setTitle(self.full_symbol)

    def add_trades(self, trades):
        if not self.data:
            return
        if self.db_type == 'Tick':  # TODO: tick type not supported
            return

        self.buy_count_at_x = np.zeros(len(self.data))
        self.sell_count_at_x = np.zeros(len(self.data))

        self.signals_group_text = QtWidgets.QGraphicsItemGroup()
        self.signals_group_arrow = QtWidgets.QGraphicsItemGroup()
        self.trades_count = len(trades)
        self.signals_text_items = np.empty(len(trades), dtype=object)

        # TODO:here only last signal in bar will show

        id_bar = 0
        for ix, trade in enumerate(trades):
            if trade.datetime < self.data[0].datetime:
                continue
            if trade.datetime > self.data[-1].datetime:
                break
            while self.data[id_bar].datetime < trade.datetime:
                id_bar = id_bar + 1
            x = id_bar - 1
            price = trade.price
            if trade.direction == Direction.LONG:
                self.buy_count_at_x[x] += 1
                ya = self.data[x].low_price * 0.999
                yt = self.data[x].low_price * \
                    (1 - 0.001 * self.buy_count_at_x[x])
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
                pen = pg.mkPen('w')
                if trade.offset == Offset.CLOSE:
                    opacity = 0.0
                    pen=self.long_pen
                    if trade.short_pnl + trade.long_pnl < 0:
                        brush = self.short_brush
                        pen = self.short_pen
                text_sig = CenteredTextItem(
                    parent=self.signals_group_text,
                    pos=(x, yt),
                    pen=pen,
                    brush=brush,
                    text=('{:.%df}' % self.digits).format(price),
                    valign=QtCore.Qt.AlignBottom,
                    opacity=opacity
                )
                text_sig.hide()
            else:
                self.sell_count_at_x[x] += 1
                ya = self.data[x].high_price * 1.001
                yt = self.data[x].low_price * \
                    (1 + 0.001 * self.sell_count_at_x[x])
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
                pen= pg.mkPen('w')
                if trade.offset == Offset.CLOSE:
                    opacity = 0.0
                    pen=self.long_pen
                    if trade.short_pnl + trade.long_pnl < 0:
                        brush = self.short_brush
                        pen=self.short_pen
                text_sig = CenteredTextItem(
                    parent=self.signals_group_text,
                    pos=(x, yt),
                    pen=pen,
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

        if len(signals) <= 20:
            for sig in signals:
                sig.show()
        else:
            for sig in signals:
                sig.hide()

    def show_orderflow(self, lbar=0, rbar=0):
        if rbar == 0:
            rbar = len(self.data)
        ofs = []
        

        for ix,of in enumerate(self.orderflow_items):
            if ix > lbar and ix < rbar:
                ofs.append(of)

        if len(ofs) <= 14:
            for of in ofs:
                of.show()
        else:
            for of in ofs:
                of.hide()


    def update_yrange_limits(self):
        if self.db_type not in ['Bar','TbtBar']:
            return
        if len(self.data) == 0:
            return
        vr = self.chart.viewRect()
        lbar, rbar = int(vr.left()), int(vr.right())
        if lbar < 0:
            lbar = 0
        if rbar > len(self.data):
            rbar = len(self.data)
        ymin = self.data[lbar].low_price
        ymax = self.data[rbar - 1].high_price
        for bar in self.data[lbar:rbar]:
            if bar.high_price > ymax:
                ymax = bar.high_price
            if bar.low_price < ymin:
                ymin = bar.low_price
        # self.chart.setYRange(ymin * 0.996, ymax * 1.004)
        if self.signals_visible:
            self.show_text_signals(lbar, rbar)
        if self.orderflow_visible:
            self.show_orderflow(lbar, rbar)

    def _get_x_axis(self):
        xaxis = DateAxis2(self.data, orientation='bottom')
        xaxis.setStyle(
            tickTextOffset=7, textFillLimits=[(0, 0.80)], showValues=True
        )
        return xaxis


    def init_ui(self):

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  
        # self.xaxis = DateAxis2(self.data, orientation='bottom')
        # self.xaxis.setStyle(
        #     tickTextOffset=7, textFillLimits=[(0, 0.80)], showValues=True
        # )
        # for bar
        self.klineitem = CandlestickItem(self.data)

        # self.volumeitem = VolumeItem(self.data)
        # self.oicurve = pg.PlotCurveItem(
        #     [bar.open_interest for bar in self.data], pen='w')

        # for tick
        self.pcurve = pg.PlotCurveItem(
            [tick.last_price for tick in self.data], pen='w')

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setHandleWidth(0)
        self.layout.addWidget(self.splitter)

        self.init_chart()

    def init_chart(self):

        self.chart = pg.PlotWidget(
            parent=self.splitter,
            axisItems={'bottom': self._get_x_axis(), 'right': PriceAxis()},
            enableMenu=True,
        )
        self.chart.getPlotItem().setContentsMargins(0, 0, 20, 0)
        self.chart.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.chart.hideAxis('left')
        self.chart.showAxis('right')
        self.chart.showGrid(x=True, y=True)
        self.chart.sigXRangeChanged.connect(self.update_yrange_limits)
        self.chart.setClipToView(True)
        self.chartlegend = self.chart.addLegend()

        if self.db_type in ['Bar','TbtBar']:
            self.chart.addItem(self.klineitem)
        elif self.db_type in ['Tick']:
            self.chart.addItem(self.pcurve)


        self.chartv = pg.PlotWidget(
            parent=self.splitter,
            axisItems={'bottom': self._get_x_axis(),
                       'right': VolumeAxis()},
            enableMenu=True,
        )
        self.chartv.getPlotItem().setContentsMargins(0, 0, 15, 15)
        self.chartv.setFrameStyle(
            QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        self.chartv.hideAxis('left')
        self.chartv.showAxis('right')
        self.chartv.setXLink(self.chart)
        self.chartvlegend = self.chartv.addLegend()
        self.chartv.setClipToView(True)
        self.chartv.enableAutoRange(axis='y', enable=True)


    def load_bar(self, 
        start: datetime, 
        end: datetime, 
        interval: Interval = Interval.MINUTE, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_bar_data'
        ):
        # symbol, exchange = extract_full_symbol(self.full_symbol)

        if start > end:
            tmp = end
            end = start
            start = tmp

        bars = []
        if datasource == 'DataBase':
            bars = database_manager.load_bar_data(
                full_symbol=self.full_symbol,
                interval=interval,
                start=start,
                end=end,
                collectionname=dbcollection,
                using_in=True
            )
        elif datasource == 'Memory':
            startix = 0
            endix = 0
            fullsyminterval = self.full_symbol + '-' + interval.value
            totalbarlist = SQGlobal.history_bar[fullsyminterval]
            if not totalbarlist:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'No data in memory!', QtWidgets.QMessageBox.Ok)
                return
            totalbars = len(totalbarlist)
            for i in range(totalbars):
                if totalbarlist[i].datetime < start and i < totalbars-1:                    
                    continue
                startix = i
                break
            for i in reversed(range(totalbars)):
                if totalbarlist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalbars)
            bars = totalbarlist[startix:endix]

        self.data.clear()
        self.data.extend(bars)



    def load_tick(self, 
        start: datetime, 
        end: datetime, 
        datasource: str = 'DataBase',
        dbcollection:str = 'db_tick_data'
    ):
        fullsymbollist = []
        weight = []
        last_tick_dict = {}
        combomode = len(self.combo_setting) > 1 
        if combomode:
            for fullsym, w in self.combo_setting:
                fullsymbollist.append(fullsym)
                last_tick_dict[fullsym] = None
                weight.append(w)
        else:
            fullsymbollist = self.full_symbol

        ticks = []
        if datasource == 'DataBase':
            ticks = database_manager.load_tick_data(
                full_symbol=fullsymbollist,
                start=start,
                end=end,
                collectionname=dbcollection,
                using_in=True
            )
        elif datasource == 'Memory':
            startix = 0
            endix = 0
            totalticklist = SQGlobal.history_tick[self.full_symbol]
            if not totalticklist:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'No data in memory!', QtWidgets.QMessageBox.Ok)
                return
            totalticks = len(totalticklist)
            for i in range(totalticks):
                if totalticklist[i].datetime < start and i < totalticks-1:
                    continue
                startix = i
                break
            for i in reversed(range(totalticks)):
                if totalticklist[i].datetime > end:
                    continue
                endix = i
                break
            endix = min(endix + 1, totalticks)
            ticks = totalticklist[startix:endix]
        self.data.clear()
        if not combomode:
            # for i in reversed(range(1,len(ticks))):
            #     ticks[i].open_interest -= ticks[i-1].open_interest
            #     ticks[i].volume -= ticks[i-1].volume
            # self.data.extend(ticks[1:])
            self.data.extend(ticks)

        else:
            lastdatetime = None
            if self.combo_op == '+':
                for tick in ticks:
                    if lastdatetime and (tick.datetime - lastdatetime) > timedelta(seconds=10):
                        for key in last_tick_dict.keys():
                            last_tick_dict[key] = None
                    if all(last_tick_dict.values()):
                        lastprice = 0
                        volume = 0
                        oi = 0

                        for i in range(len(fullsymbollist)):
                            lastprice += last_tick_dict[fullsymbollist[i]].last_price * weight[i]
                            volume += last_tick_dict[fullsymbollist[i]].volume * abs(weight[i])
                            oi += last_tick_dict[fullsymbollist[i]].open_interest* abs(weight[i])
                        newtick = TickData(
                            datetime=tick.datetime,
                            last_price=lastprice,
                            volume=volume,
                            open_interest=oi
                        )
                        self.data.append(newtick)
                    last_tick_dict[tick.full_symbol] = tick
                    lastdatetime = tick.datetime
            elif self.combo_op == '*':
                for tick in ticks:
                    if lastdatetime and (tick.datetime - lastdatetime) > timedelta(seconds=10):
                        for key in last_tick_dict.keys():
                            last_tick_dict[key] = None
                    if all(last_tick_dict.values()):
                        lastprice = 1
                        volume = 0
                        oi = 0
                        for i in range(len(fullsymbollist)):
                            lastprice *= last_tick_dict[fullsymbollist[i]].last_price ** weight[i]
                            volume += last_tick_dict[fullsymbollist[i]].volume * abs(weight[i])
                            oi += last_tick_dict[fullsymbollist[i]].open_interest* abs(weight[i])
                        newtick = TickData(
                            datetime=tick.datetime,
                            last_price=lastprice,
                            volume=volume,
                            open_interest=oi
                        )
                        self.data.append(newtick)
                    last_tick_dict[tick.full_symbol] = tick
                    lastdatetime = tick.datetime           



    def load_tbtbar(self, 
        start: datetime, 
        end: datetime, 
        interval: Interval = Interval.MINUTE, 
        datasource: str = 'DataBase',
        dbcollection: str = 'db_tbtbar_data'
    ):


        bars = []
        if datasource == 'DataBase':
            bars = database_manager.load_tbtbar_data(
                full_symbol=self.full_symbol,
                interval=interval,
                start=start,
                end=end,
                collectionname=dbcollection
            )
        elif datasource == 'Memory':
            startix = 0
            endix = 0
            fullsyminterval = self.full_symbol + '-' + interval.value
            totalbarlist = SQGlobal.history_tbtbar[fullsyminterval]
            if not totalbarlist:
                QtWidgets.QMessageBox().information(
                    None, 'Info', 'No data in memory!', QtWidgets.QMessageBox.Ok)
                return
            totalbars = len(totalbarlist)
            startix = totalbars - 1
            endix = 0
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
            endix = min(endix + 1, totalbars)
            if endix < startix:
                endix = startix
            bars = totalbarlist[startix:endix]
        # rm bar if bar.open_price ==0
        datas = [bar for bar in bars if bar.open_price ]
        self.data.clear()
        self.data.extend(datas)




    def set_indicator(self,indicator):
        if indicator:
            self.indicator = indicator
            self.indicator.set_data(self.data)
            self.update_indicator()


    def set_orderflow(self):
        if self.db_type == 'Tick':  # TODO: tick type not supported
            return
        self.orderflow_group_text = QtWidgets.QGraphicsItemGroup()
        self.orderflow_items = np.empty(len(self.data), dtype=object)
        mintick = 1.0
        for ix, bar in enumerate(self.data):
            ofix = QtWidgets.QGraphicsItemGroup()
            
            maxpen= pg.mkPen('w')
            normalpen = pg.mkPen('w')
            maxbrush= pg.mkBrush('y')
            normalbrush = pg.mkBrush('#000000')

            abuypen = pg.mkPen('r')
            asellpen = self.short_pen


            # used for test
            ofvp = dict()
            maxvol = 0
            maxvp = 0
            ticknum = int((bar.high_price-bar.low_price)/mintick)+1
            for iprice in range(ticknum):
                sellnum = random.randint(0,1000)
                buynum = random.randint(0,1000)
                ofvp[iprice] = (sellnum,buynum)
                if sellnum + buynum >maxvol:
                    maxvol= sellnum + buynum
                    maxvp = iprice

            for iprice in range(ticknum):
                price = bar.low_price + iprice*mintick
                opacity = 0
                sellpen = normalpen
                buypen = normalpen
                brush = normalbrush
                if iprice == maxvp:
                    brush = maxbrush
                    opacity = 0.5

                if iprice < ticknum-1:
                    if ofvp[iprice][0] > 2*ofvp[iprice+1][1] and ofvp[iprice][0] >20:
                        sellpen= asellpen
                if iprice > 0: 
                    if ofvp[iprice][1] > 2*ofvp[iprice-1][0] and ofvp[iprice][1] >20:
                        buypen = abuypen

                text_sell = OFTextItem(
                    parent=ofix,
                    pos=(ix-0.2, price),
                    pen=sellpen,
                    brush=brush,
                    text=str(ofvp[iprice][0]),
                    valign=QtCore.Qt.AlignLeft,
                    opacity=opacity
                )

                # text_sell.hide()

                text_buy = OFTextItem(
                    parent=ofix,
                    pos=(ix + 0.2, price),
                    pen=buypen,
                    brush=brush,
                    text=str(ofvp[iprice][1]),
                    valign=QtCore.Qt.AlignRight,
                    opacity=opacity
                )

                # text_buy.hide()
            ofix.hide()
            self.orderflow_group_text.addToGroup(ofix)         
            self.orderflow_items[ix] = ofix
        self.chart.addItem(self.orderflow_group_text)
        self.orderflow_visible = True

    
    def update_indicator(self):
        if not self.indicator:
            return
        if 'test' in self.indicator.parameters:
            self.set_orderflow()
            return

        if not self.indicator.primary:  # distinguish primary pic and secondary pic
            self.chartv.clear()
            if self.chartvlegend and self.chartvlegend.scene():
                self.chartvlegend.scene().removeItem(self.chartvlegend)
            self.chartvlegend = self.chartv.addLegend()
            self.isignals_group_arrow = QtWidgets.QGraphicsItemGroup()

            try:
                curvedatas, signals_up, signals_down = self.indicator.calculate()
                index = 0
                for key, data in curvedatas.items():
                    curve = pg.PlotCurveItem(data, pen=pg.mkPen(pg.intColor(index)), name=str(key))
                    
                    self.chartv.addItem(curve)
                    index += 1
                for x,y in signals_up:
                    pg.ArrowItem(
                        parent=self.isignals_group_arrow,
                        pos=(x, y),
                        pen=self.long_pen,
                        brush=self.long_brush,
                        angle=90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                    )
                for x, y in signals_down:
                    pg.ArrowItem(
                        parent=self.isignals_group_arrow,
                        pos=(x, y),
                        pen=self.short_pen,
                        brush=self.short_brush,
                        angle=-90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                    )
                self.chartv.addItem(self.isignals_group_arrow)
            except:
                msg = f"指标计算触发异常：\n{traceback.format_exc()}"
                QtWidgets.QMessageBox().information(
                    None, 'Info', msg, QtWidgets.QMessageBox.Ok)

            self.chartv.enableAutoRange(axis='y', enable=True)            
        else:
            itemlists = self.chart.listDataItems()
            for pitem in itemlists:
                if pitem != self.klineitem:
                    self.chart.removeItem(pitem)
            if self.chartlegend and self.chartlegend.scene():
                self.chartlegend.scene().removeItem(self.chartlegend)
            self.chartlegend = self.chart.addLegend()
            if self.psignals_group_arrow:
                self.chart.removeItem(self.psignals_group_arrow)
            self.psignals_group_arrow = QtWidgets.QGraphicsItemGroup()

            try:
                curvedatas, signals_up, signals_down = self.indicator.calculate()
                index = 0
                for key, data in curvedatas.items():
                    curve = pg.PlotCurveItem(data, pen=pg.mkPen(pg.intColor(index)), name=str(key))
                    
                    self.chart.addItem(curve)


                    index += 1
                for x,y in signals_up:
                    pg.ArrowItem(
                        parent=self.psignals_group_arrow,
                        pos=(x, y),
                        pen=self.long_pen,
                        brush=self.long_brush,
                        angle=90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                    )

                    # text2 = pg.TextItem("100")
                    # text2.setPos(x,y)
                    # self.chart.addItem(text2)

                    # _font = QtGui.QFont()
                    # _font.setPixelSize(1)
                    # _font.setBold(False)

                    # testtext = QtWidgets.QGraphicsSimpleTextItem()
                    # testtext.setFont(_font)
                    # testtext.setText('100')
                    # testtext.setPos(x,y)
                    # testtext.setBrush(pg.mkBrush('w'))
                    # self.chart.addItem(testtext)


                for x, y in signals_down:
                    pg.ArrowItem(
                        parent=self.psignals_group_arrow,
                        pos=(x, y),
                        pen=self.short_pen,
                        brush=self.short_brush,
                        angle=-90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                    )
                self.chart.addItem(self.psignals_group_arrow)
            except:
                msg = f"指标计算触发异常：\n{traceback.format_exc()}"
                QtWidgets.QMessageBox().information(
                    None, 'Info', msg, QtWidgets.QMessageBox.Ok)







class IndicatorSettingEditor(QtWidgets.QDialog):
    """
    For creating new indicator and editing straindicator parameters.
    """

    def __init__(
        self, class_name: str, parameters: dict
    ):
        """"""
        super().__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle(f"指标参数配置：{self.class_name}")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        button_text = "确定"
        parameters = self.parameters

        for name, value in parameters.items():
            type_ = type(value)
            if type_ == int:
                type_ = float
            edit = QtWidgets.QLineEdit(str(value))
            # if type_ is int:
            #     validator = QtGui.QIntValidator()
            #     edit.setValidator(validator)
            # elif type_ is float:
            validator = QtGui.QDoubleValidator()
            edit.setValidator(validator)

            form.addRow(f"{name} {type_}", edit)

            self.edits[name] = (edit, type_)

        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        form.addRow(button)

        self.setLayout(form)

    def get_setting(self):
        """"""
        setting = {}

        for name, tp in self.edits.items():
            edit, type_ = tp
            value_text = edit.text()

            if type_ == bool:
                if value_text == "True":
                    value = True
                else:
                    value = False
            elif type_ == datetime:
                value = datetime.strptime(value_text,'%Y-%m-%d %H:%M:%S')
            else:
                value = type_(value_text)

            setting[name] = value

        return setting


class ComboSettingEditor(QtWidgets.QDialog):
    """
    For creating combo parameters.
    """

    def __init__(self,nums: int = 1):
        """"""
        super().__init__()

        self.num_combos = nums
        self.edits = []
        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle(f"{self.num_combos}个合约组合设置")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        button_text = "确定"
        for i in range(self.num_combos):

            symbol = QtWidgets.QLineEdit()
            symbol.setToolTip(f'组合中第{i+1}个合约全称')
            symbol.setFixedWidth(180)
            weight = QtWidgets.QLineEdit('0')
            weight.setFixedWidth(50)
            weight.setToolTip(f'第{i+1}个合约权重')
            validator = QtGui.QIntValidator()
            weight.setValidator(validator)

            form.addRow(symbol, weight)

            self.edits.append((symbol, weight))
        self.opcombo = QtWidgets.QComboBox()
        self.opcombo.addItems(['+','*'])

        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        form.addRow('运算符', self.opcombo)
        form.addRow(button)

        self.setLayout(form)

    def get_setting(self):
        """"""
        setting = []
        op = self.opcombo.currentText()
        for name, num in self.edits:
            symbol = name.text()
            weight = int(num.text())
            setting.append((symbol, weight))
        return setting, op

