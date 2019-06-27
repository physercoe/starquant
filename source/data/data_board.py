#!/usr/bin/env python
# -*- coding: utf-8 -*-


from typing import Callable

import numpy as np
import talib

from ..common.datastruct import TickData, BarData
from ..common.constant import Interval


class BarGenerator:
    """
    For: 
    1. generating 1 minute bar data from tick data
    2. generateing x minute bar/x hour bar data from 1 minute data

    Notice:
    1. for x minute bar, x must be able to divide 60: 2, 3, 5, 6, 10, 15, 20, 30
    2. for x hour bar, x can be any number
    """

    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        """Constructor"""
        self.bar = None
        self.on_bar = on_bar

        self.interval = interval
        self.interval_count = 0

        self.window = window
        self.window_bar = None
        self.on_window_bar = on_window_bar

        self.last_tick = None
        self.last_bar = None
        self.tick_counts = 0  # bar should contail at least 2 ticks

    def update_tick(self, tick: TickData):
        """
        Update new tick data into generator.
        """
        new_minute = False

        # Filter tick data with 0 last price
        if not tick.last_price:
            return
        if not tick.ask_price_1 or not tick.bid_price_1:
            return

        if not self.bar:
            new_minute = True
        # in backtest when switching day there should be a new bar
        elif self.bar.datetime.minute != tick.datetime.minute or self.bar.datetime.hour != tick.datetime.hour:
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            if self.tick_counts > 3:
                self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
            self.tick_counts = 1
        else:
            if self.bar.datetime.time() != tick.datetime.time():
                self.tick_counts += 1
                self.bar.high_price = max(self.bar.high_price, tick.last_price)
                self.bar.low_price = min(self.bar.low_price, tick.last_price)
                self.bar.close_price = tick.last_price
                self.bar.open_interest = tick.open_interest
                self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        self.last_tick = tick

    def update_bar(self, bar: BarData):
        """
        Update 1 minute bar into generator
        """
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest
        
        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            if not (bar.datetime.minute + 1) % self.window:
                finished = True
        elif self.interval == Interval.HOUR:
            if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
                # 1-hour bar
                if self.window == 1:
                    finished = True
                # x-hour bar
                else:
                    self.interval_count += 1

                    if not self.interval_count % self.window:
                        finished = True
                        self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar

    def generate(self):
        """
        Generate the bar data and call callback immediately.
        """
        self.on_bar(self.bar)
        self.bar = None


class ArrayManager(object):
    """
    For:
    1. time series container of bar data
    2. calculating technical indicator value
    """

    def __init__(self, size=100):
        """Constructor"""
        self.count = 0
        self.size = size
        self.inited = False

        self.open_array = np.zeros(size)
        self.high_array = np.zeros(size)
        self.low_array = np.zeros(size)
        self.close_array = np.zeros(size)
        self.volume_array = np.zeros(size)

    def update_bar(self, bar):
        """
        Update new bar data into array manager.
        """
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.open_array[:-1] = self.open_array[1:]
        self.high_array[:-1] = self.high_array[1:]
        self.low_array[:-1] = self.low_array[1:]
        self.close_array[:-1] = self.close_array[1:]
        self.volume_array[:-1] = self.volume_array[1:]

        self.open_array[-1] = bar.open_price
        self.high_array[-1] = bar.high_price
        self.low_array[-1] = bar.low_price
        self.close_array[-1] = bar.close_price
        self.volume_array[-1] = bar.volume

    @property
    def open(self):
        """
        Get open price time series.
        """
        return self.open_array

    @property
    def high(self):
        """
        Get high price time series.
        """
        return self.high_array

    @property
    def low(self):
        """
        Get low price time series.
        """
        return self.low_array

    @property
    def close(self):
        """
        Get close price time series.
        """
        return self.close_array

    @property
    def volume(self):
        """
        Get trading volume time series.
        """
        return self.volume_array

    def sma(self, n, array=False):
        """
        Simple moving average.
        """
        result = talib.SMA(self.close, n)
        if array:
            return result
        return result[-1]

    def std(self, n, array=False):
        """
        Standard deviation
        """
        result = talib.STDDEV(self.close, n)
        if array:
            return result
        return result[-1]

    def cci(self, n, array=False):
        """
        Commodity Channel Index (CCI).
        """
        result = talib.CCI(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def atr(self, n, array=False):
        """
        Average True Range (ATR).
        """
        result = talib.ATR(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def rsi(self, n, array=False):
        """
        Relative Strenght Index (RSI).
        """
        result = talib.RSI(self.close, n)
        if array:
            return result
        return result[-1]

    def macd(self, fast_period, slow_period, signal_period, array=False):
        """
        MACD.
        """
        macd, signal, hist = talib.MACD(
            self.close, fast_period, slow_period, signal_period
        )
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]

    def adx(self, n, array=False):
        """
        ADX.
        """
        result = talib.ADX(self.high, self.low, self.close, n)
        if array:
            return result
        return result[-1]

    def boll(self, n, dev, array=False):
        """
        Bollinger Channel.
        """
        mid = self.sma(n, array)
        std = self.std(n, array)

        up = mid + std * dev
        down = mid - std * dev

        return up, down

    def keltner(self, n, dev, array=False):
        """
        Keltner Channel.
        """
        mid = self.sma(n, array)
        atr = self.atr(n, array)

        up = mid + atr * dev
        down = mid - atr * dev

        return up, down

    def donchian(self, n, array=False):
        """
        Donchian Channel.
        """
        up = talib.MAX(self.high, n)
        down = talib.MIN(self.low, n)

        if array:
            return up, down
        return up[-1], down[-1]

    def highlow(self, currentHigh, currentLow, HighPoint, LowPoint, HigherRatio, LowerRatio):
        PriceBFired = False
        PriceA = 0.0
        PriceB = 0.0
        PriceBFired2 = False
        PriceA2 = 0.0
        PriceB2 = 0.0

        TempHigh = np.max(self.high)
        TempLow = np.min(self.low)
        TempHighTime = np.where(self.high == TempHigh)[0][-1]  # 最后一个高点位置
        TempLowTime = np.where(self.low == TempLow)[0][0]  # 第一个低点位置
        TempLowMin1 = self.low[TempHighTime:]
        TempHighMin1 = self.high[TempLowTime:]
        if currentHigh == TempHigh and TempHigh > HighPoint:
            TempLow1 = np.min(TempLowMin1)
            TempLow1Time = np.where(TempLowMin1 == TempLow1)[0][-1]
            TempIfTimeBC = len(TempLowMin1) - TempLow1Time > 2
            TempIfTimeAB = TempLow1Time > 2
            TempIfPriceOA = (TempHigh - TempLow1 > LowerRatio *
                             HighPoint) and (TempHigh - TempLow1 < HigherRatio * HighPoint)
            if TempIfTimeBC and TempIfTimeAB and TempIfPriceOA:
                PriceBFired = True
                PriceA = TempHigh
                PriceB = TempLow1
        if currentLow == TempLow and TempLow < LowPoint:
            TempHigh1 = np.max(TempHighMin1)
            TempHigh1Time = np.where(TempHighMin1 == TempHigh1)[0][-1]
            TempIfTimeBC2 = (len(TempHighMin1) - TempHigh1Time > 2)
            TempIfTimeAB2 = (TempHigh1Time > 2)
            TempIfPriceAB2 = (TempHigh1 - TempLow > LowerRatio *
                              LowPoint) and (TempHigh1 - TempLow < HigherRatio * LowPoint)
            if TempIfTimeBC2 and TempIfTimeAB2 and TempIfPriceAB2:
                PriceBFired2 = True
                PriceA2 = TempLow
                PriceB2 = TempHigh1
        return PriceBFired, PriceA, PriceB, PriceBFired2, PriceA2, PriceB2
