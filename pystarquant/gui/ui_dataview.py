import importlib
import traceback
import sys
import numpy as np
from pathlib import Path
import os
from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import timedelta, datetime
import pyqtgraph as pg

sys.path.insert(0, "../..")

from pystarquant.gui.ui_basic import (
    CandlestickItem,
    SCandlestickItem, 
    VolumeItem,
    DateAxis,
    DateAxis2,
    VolumeAxis,
    OpenInterestAxis,
    PriceAxis
)
from pystarquant.common.constant import Interval
from pystarquant.data import database_manager
from pystarquant.common.utility import extract_full_symbol
from pystarquant.common.datastruct import Event
from pystarquant.data.data_board import BarGenerator
from pystarquant.strategy.strategy_base import IndicatorBase
import pystarquant.common.sqglobal as SQGlobal





class MarketDataView(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)

    def __init__(self, sym: str = ""):
        """"""
        super().__init__()

        self.full_symbol = ""
        self.init_ui()
        self.register_event()

    def init_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.datachart = QuotesChart(self.full_symbol)
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
        self.tick_signal.connect(self.datachart.on_tick)
        self.symbol_signal.connect(self.orderbook.symbol_signal.emit)
        self.orderbook.symbol_signal.connect(self.datachart.reset)
        self.orderbook.day_signal.connect(self.datachart.reload)
        self.orderbook.indicator_signal.connect(self.datachart.set_indicator)
        # self.symbol_signal.connect(self.datachart.reset)


class StrategyDataView(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)
    strategy_signal = QtCore.pyqtSignal(Event)

    def __init__(self, sym: str = "",wid: int = 0):
        """"""
        super().__init__()
        self._id = wid
        self.full_symbol = ""
        self.init_ui()
        self.register_event()

    def init_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.datachart = QuotesChart(self.full_symbol,{})

        self.orderbook = StrategyUIWidget()
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.datachart)
        self.scroll.setWidgetResizable(True)

        hbox = QtWidgets.QHBoxLayout()
        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(self.scroll)
        splitter1.addWidget(self.orderbook)

        hbox.addWidget(splitter1)

        self.setLayout(hbox)
        self.setMinimumWidth(600)
    def register_event(self):
        """"""
        self.tick_signal.connect(self.orderbook.tick_signal.emit)
        self.tick_signal.connect(self.datachart.on_tick)

        # self.symbol_signal.connect(self.orderbook.symbol_signal.emit)
        # self.orderbook.symbol_signal.connect(self.datachart.reset)

        # self.orderbook.day_signal.connect(self.datachart.reload)
        self.orderbook.day_signal.connect(self.process_day_signal)

        self.orderbook.indicator_signal.connect(self.datachart.set_indicator)

        self.strategy_signal.connect(self.process_strategy_signal)
        # self.strategy_signal.connect(self.orderbook.process_strategy_signal)
        # self.strategy_signal.connect(self.datachart.process_strategy_signal)

    def process_strategy_signal(self,event: Event):
        wid  = int(event.destination[2:])
        if wid != self._id:
            pass
        
        self.orderbook.process_strategy_signal(event)
        self.datachart.process_strategy_signal(event)

    def process_day_signal(self,sdata):
        days = sdata[0]
        sinterval = Interval(sdata[1])
        self.datachart.reload(days,sinterval)



CHART_MARGINS = (0, 0, 20, 10)


class QuotesChart(QtWidgets.QWidget):
    signal = QtCore.pyqtSignal(Event)

    short_pen = pg.mkPen('#00ffff')
    short_brush = pg.mkBrush('#00ffff')
    long_pen = pg.mkPen('r')
    long_brush = pg.mkBrush('#ff0000')

    zoomIsDisabled = QtCore.pyqtSignal(bool)

    def __init__(self, symbol: str = "",sdata=None):
        super().__init__()
        self.full_symbol = symbol
        self.interval = Interval.MINUTE
        self.strategy_data = sdata
        self.data = []
        self.indicator = None
        self.isignals_group_arrow = None
        self.psignals_group_arrow = None

        self.bg = BarGenerator(self.on_bar)
        self.chart = None
        self.charv = None
        self.load_bar()
        self.init_ui()


    def reset(self, symbol: str,sdata=None):
        # if not self.layout.isEmpty():
        #     self.layout.removeWidget(self.splitter)
        #     self.splitter.deleteLater()
        # self.full_symbol = symbol
        # self.bg = BarGenerator(self.on_bar)
        # self.load_bar()
        # self.init_ui()
        self.full_symbol = symbol
        self.strategy_data = sdata


        self.bg = BarGenerator(self.on_bar)
        self.load_bar()


        if self.isignals_group_arrow:
            self.chartv.removeItem(self.isignals_group_arrow)
            del self.isignals_group_arrow   
        if self.psignals_group_arrow:
            self.chart.removeItem(self.psignals_group_arrow)
            del self.psignals_group_arrow    

        self.klineitem.generatePicture()
        self.update_indicator()
        # self.volumeitem.generatePicture()
        # self.oicurve.setData([bar.open_interest for bar in self.data])
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
        if self.strategy_data is None:
            self.klineitem = CandlestickItem(self.data)
        else:
            self.klineitem = SCandlestickItem(self.data,self.strategy_data)
        # self.volumeitem = VolumeItem(self.data)
        # self.oicurve = pg.PlotCurveItem(
        #     [bar.open_interest for bar in self.data], pen='w')

        self.arrowitem = None

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setHandleWidth(0)
        self.layout.addWidget(self.splitter)

        self.init_chart()
        # self.init_chart_item()

    def load_bar(self, days: int = 1, interval: Interval = Interval.MINUTE):
        # symbol, exchange = extract_full_symbol(self.full_symbol)
        end = datetime.now()
        self.interval = interval
        self.bg =  BarGenerator(self.on_bar,1,self.on_window_bar,interval)
        if interval == Interval.DAILY:
            start = end - timedelta(days)            
        elif interval == Interval.MINUTE:
            start = end - timedelta(minutes=days)
        elif interval == Interval.HOUR:
            start = end - timedelta(hours=days)


        else:
            start = end - timedelta(2)

        if start > end:
            tmp = end
            end = start
            start = tmp
   
        bars = database_manager.load_bar_data(
            full_symbol=self.full_symbol,
            interval=interval,
            start=start,
            end=end,
            # collectionname='db_bar_data',
            # using_in=True
        )
        self.data.clear()
        self.data.extend(bars)

    def reload(self, count=1,sinter: Interval = Interval.MINUTE):
        self.load_bar(days=count,interval=sinter)
        self.klineitem.generatePicture()
        self.update_indicator()

        if self.arrowitem:
            self.chart.removeItem(self.arrowitem)
        
        try:
            sdt = datetime.strptime(self.strategy_data['last_tradetime'],'%Y-%m-%d %H:%M:%S')
            pos = self.strategy_data['pos']
        except:
            sdt = datetime(2020,1,1)
            pos = 0



        for t, bar in enumerate(self.data):
            # if type(bar.datetime) != type(datetime):
            #     print(bar.datetime,type(bar.datetime),type(datetime),type(sdt))

            if bar.datetime > sdt and pos >0:
                self.arrowitem = pg.ArrowItem(
                        pos=(t, bar.low_price),
                        pen=pg.mkPen('r'),
                        brush=pg.mkBrush('r'),
                        angle=90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                )
                self.chart.addItem(self.arrowitem)
                return
            if bar.datetime > sdt and pos < 0:
                self.arrowitem = pg.ArrowItem(
                        pos=(t, bar.high_price),
                        pen=pg.mkPen('#00ffff'),
                        brush=pg.mkBrush('#00ffff'),
                        angle=-90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                )
                self.chart.addItem(self.arrowitem)                
                return



        # self.volumeitem.generatePicture()
        # self.oicurve.setData([bar.open_interest for bar in self.data])

    def on_bar(self, bar):
        self.bg.update_bar(bar)

        # self.data.append(bar)
        # self.klineitem.on_bar(bar)
        # self.update_indicator()
        # self.volumeitem.on_bar(bar)
        # self.oicurve.setData([abar.open_interest for abar in self.data])

    def on_window_bar(self,bar):
        self.data.append(bar)
        self.klineitem.on_bar(bar)
        self.update_indicator()        

    def on_tick(self, tickevent):
        tick = tickevent.data
        if tick.full_symbol == self.full_symbol:
            self.bg.update_tick(tick)

    def process_strategy_signal(self,event: Event):
        data = event.data
        self.full_symbol = data["full_symbol"]
        self.strategy_data.update(data['variables'])


        self.bg = BarGenerator(self.on_bar)
        self.load_bar()
        self.klineitem.generatePicture()
        self.update_indicator()

        if self.arrowitem:
            self.chart.removeItem(self.arrowitem)
        
        try:
            sdt = datetime.strptime(self.strategy_data['last_tradetime'],'%Y-%m-%d %H:%M:%S')
            pos = self.strategy_data['pos']
        except:
            sdt = datetime(2020,1,1)
            pos = 0



        for t, bar in enumerate(self.data):
            
            if bar.datetime > sdt and pos >0:
                self.arrowitem = pg.ArrowItem(
                        pos=(t, bar.low_price),
                        pen=pg.mkPen('r'),
                        brush=pg.mkBrush('r'),
                        angle=90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                )
                self.chart.addItem(self.arrowitem)
                return
            if bar.datetime > sdt and pos < 0:
                self.arrowitem = pg.ArrowItem(
                        pos=(t, bar.high_price),
                        pen=pg.mkPen('#00ffff'),
                        brush=pg.mkBrush('#00ffff'),
                        angle=-90,
                        headLen=12,
                        tipAngle=30,
                        tailLen=20,
                        tailWidth=1.5,
                )
                self.chart.addItem(self.arrowitem)                
                return


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
        self.chart.addItem(self.klineitem)
        self.chartlegend = self.chart.addLegend()

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
        # self.chartv.showAxis('left')
        self.chartv.showAxis('right')
        self.chartv.setXLink(self.chart)
        self.chartvlegend = self.chartv.addLegend()
        # self.chartv.setClipToView(True)
        # self.chartv.enableAutoRange(axis='y', enable=True)

    def set_indicator(self,indicator):
        self.indicator = indicator
        self.indicator.set_data(self.data)
        self.update_indicator()

    def update_indicator(self):
        if not self.indicator:
            return
        
        if not self.indicator.primary:
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

            # self.chartv.enableAutoRange(axis='y', enable=True)
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





class OrderBookWidget(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)
    day_signal = QtCore.pyqtSignal(int)
    indicator_signal = QtCore.pyqtSignal(IndicatorBase)

    def __init__(self):
        """"""
        super().__init__()

        self.full_symbol = ""
        self.indicator_classes = {}    # name->indictor
        self.indicator = None
        self.settings = {}
        self.init_ui()
        self.register_event()
        self.clear_label_text()
        self.load_indicator()


    def load_indicator(self, reload: bool = False):
        if reload:
            SQGlobal.indicatorloader.load_class(True)            

        self.indicator_classes =  SQGlobal.indicatorloader.classes
        self.settings = SQGlobal.indicatorloader.settings

        self.indicator_combo.clear()
        self.indicator_combo.addItems(list(self.indicator_classes.keys()))        
        

    def init_ui(self):
        self.symbol_line = QtWidgets.QLineEdit()
        # self.symbol_line.setReadOnly(True)
        self.symbol_line.returnPressed.connect(self.process_symbol)

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
        self.last_volume = 0
        form2 = QtWidgets.QFormLayout()

        historylabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        historylabel.setText('History Data')
        form2.addRow(historylabel)
        self.histbar_day = QtWidgets.QLineEdit()
        self.histbar_day.setValidator(QtGui.QIntValidator())
        self.histbar_day.setText('1')
        self.histbar_day.returnPressed.connect(self.process_days)
        self.last_days = 1
        form2.addRow('Days', self.histbar_day)
        self.intervalcombo = QtWidgets.QComboBox()
        self.intervalcombo.addItems(["1m", "1h"])
        form2.addRow('Interval', self.intervalcombo)

        self.indicator_combo = QtWidgets.QComboBox()
        self.indicator_combo.addItems(list(self.indicator_classes.keys()))
        refresh_button = QtWidgets.QPushButton("重新加载")
        refresh_button.clicked.connect(lambda:self.load_indicator(True))
        showindicator_button = QtWidgets.QPushButton("显示指标")
        showindicator_button.clicked.connect(self.show_indicator)
        form2.addRow('指标',self.indicator_combo)
        # form2.addRow('指标',)
        form2.addRow(refresh_button, showindicator_button)
        form2.setLabelAlignment(QtCore.Qt.AlignLeft)
        # hbox2 = QtWidgets.QHBoxLayout()
        # hbox2.addWidget(refresh_button)
        # hbox2.addWidget(showindicator_button)
        # form2.addRow(hbox2)


        titlelabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        titlelabel.setText('OrderBook')

        # pricelable = self.create_label(alignment=QtCore.Qt.AlignLeft)
        # pricelable.setText('Price')
        # volumelable =  self.create_label(alignment=QtCore.Qt.AlignRight)
        # volumelable.setText('Volume')

        # verticalSpacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        form2.addRow(titlelabel)
        form2.addRow(self.symbol_line)
        form2.addRow(self.change_label, self.open_label)
        form2.addRow(self.low_label, self.high_label)
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
        self.setFixedWidth(160)
        # self.setFixedSize(160,500)

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

    def process_tick_event(self, tickevent: Event):
        """"""
        tick = tickevent.data
        if not tick:
            return
        if (tick.full_symbol != self.full_symbol):
            return
        self.lp_label.setText(str(tick.last_price))
        self.open_label.setText(str(tick.open_price))
        self.low_label.setText(str(tick.low_price))
        self.high_label.setText(str(tick.high_price))
        self.size_label.setText(str(tick.volume - self.last_volume))
        self.last_volume = tick.volume
        self.bp1_label.setText(str(tick.bid_price_1))
        self.bv1_label.setText(str(tick.bid_volume_1))
        self.ap1_label.setText(str(tick.ask_price_1))
        self.av1_label.setText(str(tick.ask_volume_1))
        self.uplimit_label.setText(str(tick.limit_up))
        self.lplimit_lable.setText(str(tick.limit_down))

        if tick.pre_close != 0.0:
            r = (tick.last_price / tick.pre_close - 1) * 100
            self.change_label.setText(f"{r:.2f}%")

        if tick.depth == 5:
            self.bp2_label.setText(str(tick.bid_price_2))
            self.bv2_label.setText(str(tick.bid_volume_2))
            self.ap2_label.setText(str(tick.ask_price_2))
            self.av2_label.setText(str(tick.ask_volume_2))

            self.bp3_label.setText(str(tick.bid_price_3))
            self.bv3_label.setText(str(tick.bid_volume_3))
            self.ap3_label.setText(str(tick.ask_price_3))
            self.av3_label.setText(str(tick.ask_volume_3))

            self.bp4_label.setText(str(tick.bid_price_4))
            self.bv4_label.setText(str(tick.bid_volume_4))
            self.ap4_label.setText(str(tick.ask_price_4))
            self.av4_label.setText(str(tick.ask_volume_4))

            self.bp5_label.setText(str(tick.bid_price_5))
            self.bv5_label.setText(str(tick.bid_volume_5))
            self.ap5_label.setText(str(tick.ask_price_5))
            self.av5_label.setText(str(tick.ask_volume_5))

    def process_symbol(self):
        sym = self.symbol_line.text()
        if sym:
            self.symbol_signal.emit(sym)

    def process_days(self):
        days = int(self.histbar_day.text())
        if days != self.last_days:
            self.last_days = days
            self.day_signal.emit(days)

    def set_full_symbol(self, symbol: str):
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
        self.bv1_label.setText("")
        self.bv2_label.setText("")
        self.bv3_label.setText("")
        self.bv4_label.setText("")
        self.bv5_label.setText("")

        self.av1_label.setText("")
        self.av2_label.setText("")
        self.av3_label.setText("")
        self.av4_label.setText("")
        self.av5_label.setText("")

        self.bp1_label.setText("")
        self.bp2_label.setText("")
        self.bp3_label.setText("")
        self.bp4_label.setText("")
        self.bp5_label.setText("")

        self.ap1_label.setText("")
        self.ap2_label.setText("")
        self.ap3_label.setText("")
        self.ap4_label.setText("")
        self.ap5_label.setText("")

    def show_indicator(self):
        
        class_name = self.indicator_combo.currentText()
        old_setting = self.settings[class_name]
        new_setting = None
        if old_setting:
            dialog = IndicatorSettingEditor(class_name, old_setting)
            i = dialog.exec()
            if i != dialog.Accepted:
                return
            new_setting = dialog.get_setting()
            self.settings[class_name] = new_setting

        indicator_class = self.indicator_classes.get(class_name, None)
        if indicator_class:
            self.indicator = indicator_class()
            if new_setting:
                self.indicator.update_setting(new_setting)
            self.indicator_signal.emit(self.indicator)
            # self.indicator.set_data(self.data)
            # self.update_indicator()




class StrategyUIWidget(QtWidgets.QWidget):
    tick_signal = QtCore.pyqtSignal(Event)
    symbol_signal = QtCore.pyqtSignal(str)
    day_signal = QtCore.pyqtSignal(tuple)
    indicator_signal = QtCore.pyqtSignal(IndicatorBase)

    def __init__(self):
        """"""
        super().__init__()

        self.full_symbol = ""
        
        self.last_tradetime = None

        self.indicator_classes = {}    # name->indictor
        self.indicator = None
        self.settings = {}
        self.init_ui()
        self.register_event()
        self.clear_label_text()
        self.load_indicator()


    def load_indicator(self, reload: bool = False):
        if reload:
            SQGlobal.indicatorloader.load_class(True)            

        self.indicator_classes =  SQGlobal.indicatorloader.classes
        self.settings = SQGlobal.indicatorloader.settings

        self.indicator_combo.clear()
        self.indicator_combo.addItems(list(self.indicator_classes.keys()))        
        

    def init_ui(self):

        self.strategy_line = QtWidgets.QLineEdit()
        self.strategy_line.setReadOnly(True)

        self.strategy_pid = QtWidgets.QLineEdit()
        self.strategy_pid.setReadOnly(True)

        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.setReadOnly(True)


        self.pnl_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        self.cost_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        
        bid_color = "rgb(255,174,201)"
        ask_color = "rgb(160,255,160)"

        self.pos_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)


        # basic quote, price and volume

        self.bp1_label = self.create_label(bid_color)

        self.bv1_label = self.create_label(
            bid_color, alignment=QtCore.Qt.AlignRight)

        self.ap1_label = self.create_label(ask_color)

        self.av1_label = self.create_label(
            ask_color, alignment=QtCore.Qt.AlignRight)

        self.lp_label = self.create_label()
        self.size_label = self.create_label(alignment=QtCore.Qt.AlignRight)
        self.last_volume = 0


        form2 = QtWidgets.QFormLayout()

        historylabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        historylabel.setText('历史数据')
        # form2.addRow(historylabel)
        self.histbar_day = QtWidgets.QLineEdit()
        self.histbar_day.setValidator(QtGui.QIntValidator())
        self.histbar_day.setText('1')
        self.histbar_day.returnPressed.connect(self.process_days)
        self.last_days = 1
        form2.addRow('时长', self.histbar_day)
        self.intervalcombo = QtWidgets.QComboBox()
        self.intervalcombo.addItems(["1m", "1h","d"])
        form2.addRow('尺度', self.intervalcombo)

        self.indicator_combo = QtWidgets.QComboBox()
        self.indicator_combo.addItems(list(self.indicator_classes.keys()))
        refresh_button = QtWidgets.QPushButton("重新加载")
        refresh_button.clicked.connect(lambda:self.load_indicator(True))
        showindicator_button = QtWidgets.QPushButton("显示指标")
        showindicator_button.clicked.connect(self.show_indicator)
        form2.addRow('指标',self.indicator_combo)
        form2.addRow(refresh_button, showindicator_button)
        form2.setLabelAlignment(QtCore.Qt.AlignLeft)



        titlelabel = self.create_label(alignment=QtCore.Qt.AlignCenter)
        titlelabel.setText('策略概况')

 
        # form2.addRow(titlelabel)
        form2.addRow(self.strategy_line)
        form2.addRow(self.symbol_line)

        form2.addRow('进程ID',self.strategy_pid)
        form2.addRow('盈亏', self.pnl_label)
        form2.addRow('持仓数量',self.pos_label)
        form2.addRow('持仓成本',self.cost_label)

        # verticalSpacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        # form2.addItem(verticalSpacer)
        title2label = self.create_label(alignment=QtCore.Qt.AlignCenter)
        title2label.setText('基本行情')
        # form2.addRow(title2label)

        form2.addRow(self.ap1_label, self.av1_label)
        form2.addRow(self.lp_label, self.size_label)
        form2.addRow(self.bp1_label, self.bv1_label)


        # Overall layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form2)
        self.setLayout(vbox)
        self.setFixedWidth(160)
        # self.setFixedSize(160,500)

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

    def process_tick_event(self, tickevent: Event):
        """"""
        tick = tickevent.data
        if not tick:
            return
        if (tick.full_symbol != self.full_symbol):
            return
        self.lp_label.setText(str(tick.last_price))
        self.size_label.setText(str(tick.volume - self.last_volume))
        self.last_volume = tick.volume
        self.bp1_label.setText(str(tick.bid_price_1))
        self.bv1_label.setText(str(tick.bid_volume_1))
        self.ap1_label.setText(str(tick.ask_price_1))
        self.av1_label.setText(str(tick.ask_volume_1))
        
        pnl = float(self.pos_label.text())* (tick.last_price - float(self.cost_label.text()) )
        self.pnl_label.setText(str(pnl))


    def process_strategy_signal(self,event:Event):
        data = event.data
        self.strategy_line.setText(data["strategy_name"])
        self.strategy_pid.setText(str(data["engine_id"]))
        self.symbol_line.setText(data["full_symbol"])
        self.full_symbol = data["full_symbol"]
        self.pos_label.setText(str(data['variables']["pos"]))
        self.cost_label.setText(str(data['variables']["cost"]))
        
        # tstr = data['variables']["last_tradetime"]
        # if tstr:
        #     try:
        #         self.last_tradetime = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
        #     except:
        #         pass


    def process_symbol(self):
        sym = self.symbol_line.text()
        if sym:
            self.symbol_signal.emit(sym)

    def process_days(self):
        days = int(self.histbar_day.text())
        if days != self.last_days:
            self.last_days = days
            interv = self.intervalcombo.currentText()
            sdata = (days,interv)
            self.day_signal.emit(sdata)

    def set_full_symbol(self, symbol: str):
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
        self.pos_label.setText('0')
        self.cost_label.setText('')
        # tstr = data['variables']["last_tradetime"]
        # if tstr:
        #     try:
        #         self.last_tradetime = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
        #     except:
        #         pass

        self.pnl_label.setText('0')
        self.strategy_line.setText('策略名称')
        self.symbol_line.setText('标的全称')
        self.strategy_pid.setText('')

        self.lp_label.setText("最新价格")
        self.size_label.setText('成交量')

        self.bv1_label.setText("买一量")
        self.av1_label.setText("卖一量")
        self.bp1_label.setText("买一价")

        self.ap1_label.setText("卖一价")


    def show_indicator(self):
        
        class_name = self.indicator_combo.currentText()
        old_setting = self.settings[class_name]
        new_setting = None
        if old_setting:
            dialog = IndicatorSettingEditor(class_name, old_setting)
            i = dialog.exec()
            if i != dialog.Accepted:
                return
            new_setting = dialog.get_setting()
            self.settings[class_name] = new_setting

        indicator_class = self.indicator_classes.get(class_name, None)
        if indicator_class:
            self.indicator = indicator_class()
            if new_setting:
                self.indicator.update_setting(new_setting)
            self.indicator_signal.emit(self.indicator)
            # self.indicator.set_data(self.data)
            # self.update_indicator()




















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
        button_text = "确定"
        parameters = self.parameters

        for name, value in parameters.items():
            type_ = type(value)

            edit = QtWidgets.QLineEdit(str(value))
            if type_ is int:
                validator = QtGui.QIntValidator()
                edit.setValidator(validator)
            elif type_ is float:
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
            else:
                value = type_(value_text)

            setting[name] = value

        return setting


