#!/usr/bin/env python
# -*- coding: utf-8 -*-
class DataBoard(object):
    """
    Data tracker that holds current market data info
    TODO: jsut store last tick and last bar
    """
    def __init__(self):
        self._symbol_tick_dict = {}
        self._symbol_bar_dict = {}

    def on_tick(self, tick):
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