#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
from pathlib import Path
from typing import Callable

import numpy as np
import talib

from ..common.datastruct import Event,TickData, BarData

class DataBoard(object):
    """
    Data tracker that holds current market data info
    TODO: jsut store last tick and last bar
    """
    def __init__(self):
        self._symbol_tick_dict = {}
        self._symbol_bar_dict = {}

    def on_tick(self, tick_event):
        tick = tick_event.data
        if tick.full_symbol not in self._symbol_tick_dict:
            self._symbol_tick_dict[tick.full_symbol]  = None

        self._symbol_tick_dict[tick.full_symbol] = tick

    def on_bar(self, bar):
        
        if bar.full_symbol not in self._symbol_bar_dict:
            self._symbol_bar_dict[bar.full_symbol]  = None

        self._symbol_bar_dict[bar.full_symbol] = bar
        #print("on bar")

    def get_last_price(self, symbol):
        """
        Returns the most recent actual timestamp for a given ticker
        """
        if symbol in self._symbol_tick_dict:       # tick takes priority
            return self._symbol_tick_dict[symbol].price
        elif symbol in self._symbol_bar_dict:
            return self._symbol_bar_dict[symbol].adj_close_price
        else:
            print(
                "LastPrice for ticker %s is not found" % (symbol)
            )
            return None
    
    def get_s1_price(self, symbol):
        """
        Returns the most recent actual timestamp for a given ticker
        """
        if symbol in self._symbol_tick_dict:       # tick takes priority
            print('以卖一价成交',self._symbol_tick_dict[symbol].ask_price_L1)
            return self._symbol_tick_dict[symbol].ask_price_L1
        elif symbol in self._symbol_bar_dict:
            return self._symbol_bar_dict[symbol].adj_close_price
        else:
            print(
                "LastPrice for ticker %s is not found" % (symbol)
            )
            return None

    def get_b1_price(self, symbol):
        """
        Returns the most recent actual timestamp for a given ticker
        """
        if symbol in self._symbol_tick_dict:       # tick takes priority
            print('以买一价成交',self._symbol_tick_dict[symbol].bid_price_L1)
            return self._symbol_tick_dict[symbol].bid_price_L1
        elif symbol in self._symbol_bar_dict:
            return self._symbol_bar_dict[symbol].adj_close_price
        else:
            print(
                "LastPrice for ticker %s is not found" % (symbol)
            )
            return None




    def get_last_timestamp(self, symbol):
        """
        Returns the most recent actual timestamp for a given ticker
        """
        if symbol in self._symbol_tick_dict:         # tick takes priority
            return self._symbol_tick_dict[symbol].timestamp
        elif symbol in self._symbol_bar_dict:
            return self._symbol_bar_dict[symbol].bar_end_time()
        else:
            print(
                "Timestamp for ticker %s is not found" % (symbol)
            )
            return None



class BarGenerator:
    """
    For: 
    1. generating 1 minute bar data from tick data
    2. generateing x minute bar data from 1 minute data
    """

    def __init__(
        self, on_bar: Callable, xmin: int = 0, on_xmin_bar: Callable = None
    ):
        """Constructor"""
        self.bar = None
        self.on_bar = on_bar

        self.xmin = xmin
        self.xmin_bar = None
        self.on_xmin_bar = on_xmin_bar

        self.last_tick = None

    def update_tick(self, tick: TickData):
        """
        Update new tick data into generator.
        """
        new_minute = False

        if not self.bar:
            new_minute = True
        elif self.bar.datetime.minute != tick.datetime.minute:
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
            )
        else:
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            self.bar.close_price = tick.last_price
            self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        self.last_tick = tick

    def update_bar(self, bar: BarData):
        """
        Update 1 minute bar into generator
        """
        if not self.xmin_bar:
            self.xmin_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=bar.datetime,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        else:
            self.xmin_bar.high_price = max(
                self.xmin_bar.high_price, bar.high_price)
            self.xmin_bar.low_price = min(
                self.xmin_bar.low_price, bar.low_price)

        self.xmin_bar.close_price = bar.close_price
        self.xmin_bar.volume += int(bar.volume)

        if not (bar.datetime.minute + 1) % self.xmin:
            self.xmin_bar.datetime = self.xmin_bar.datetime.replace(
                second=0, microsecond=0
            )
            self.on_xmin_bar(self.xmin_bar)

            self.xmin_bar = None

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
