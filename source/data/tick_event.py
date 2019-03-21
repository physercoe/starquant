#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
from enum import Enum
from ..event.event import *
import time
import pandas as pd
class TickType(Enum):
    Tick_L1 = 0
    Tick_L5 = 1
    Tick_L20 = 2
    Bar_1min = 3
    Bar_5min = 4
    Bar_15min = 5
    Bar_1h = 6
    Bar_1d = 7
    Bar_1w = 8
    Bar_1m = 9
    Trade = 10		
    Bid = 11
    Ask = 12
    Full = 13
    BidPrice = 14
    BidSize = 15
    AskPrice = 16
    AskSize = 17
    Price = 18
    TradeSize = 19
    OpenPrice = 20
    HighPrice = 21
    LowPrice = 22
    ClosePrice = 23
    Volume = 24
    OpenInterest = 25
    Bar = 26
    Account = 27
    Position = 28






class TickEvent(Event):
    """
    Tick event
    """

    def __init__(self):
        """
        Initialises Tick
        """
        self.event_type = EventType.TICK
        self.tick_type = TickType.Trade
        self.timestamp = Timestamp('1970-01-01', tz='UTC')
        self.full_symbol = ''
        self.price = 0.0
        self.size = 0
        self.depth = 1

        self.bid_price_L1 = 0.0
        self.bid_size_L1 = 0
        self.ask_price_L1 = 0.0
        self.ask_size_L1 = 0
        self.bid_price_L2 = 0.0
        self.bid_size_L2 = 0
        self.ask_price_L2 = 0.0
        self.ask_size_L2 = 0
        self.bid_price_L3 = 0.0
        self.bid_size_L3 = 0
        self.ask_price_L3 = 0.0
        self.ask_size_L3 = 0
        self.bid_price_L4 = 0.0
        self.bid_size_L4 = 0
        self.ask_price_L4 = 0.0
        self.ask_size_L4 = 0
        self.bid_price_L5 = 0.0
        self.bid_size_L5 = 0
        self.ask_price_L5 = 0.0
        self.ask_size_L5 = 0

        self.open_interest = 0
        self.open = 0.0
        self.high = 0.0
        self.low = 0.0
        self.pre_close = 0.0
        self.upper_limit_price = 0.0
        self.lower_limit_price = 0.0
        self.totalq = 0.0
        self.position =0.0
        self.bors = ''
    def deserialize(self, msg):
        # print('begin deserial tick')
        try:
            v = msg.split('|')
            self.tick_type = TickType(int(v[0]))
            # print('tick type',self.tick_type,self.tick_type == TickType.Tick_L1)
            self.full_symbol = v[1]
            #self.timestamp = time.mktime(time.strptime(v[1],'%Y-%m-%d %H:%M:%S.%f'))
            self.timestamp =pd.to_datetime(v[2])
            self.price = float(v[3])
            self.size = int(v[4])

            if (self.tick_type == TickType.Tick_L1):
                # print('tickl1 deserialize')
                self.bid_price_L1 = float(v[5])
                self.bid_size_L1 = int(v[6])
                self.ask_price_L1 = float(v[7])
                self.ask_size_L1 = int(v[8])
                self.open_interest = int(v[9])
                self.open = float(v[10])
                self.high = float(v[11])
                self.low = float(v[12])
                self.pre_close = float(v[13])
                self.upper_limit_price = float(v[14])
                self.lower_limit_price = float(v[15])
            elif (self.tick_type == TickType.Tick_L5):
                self.bid_price_L1 = float(v[5])
                self.bid_size_L1 = int(v[6])
                self.ask_price_L1 = float(v[7])
                self.ask_size_L1 = int(v[8])
                self.bid_price_L2 = float(v[9])
                self.bid_size_L2 = int(v[10])
                self.ask_price_L2 = float(v[11])
                self.ask_size_L2 = int(v[12])
                self.bid_price_L3 = float(v[13])
                self.bid_size_L3 = int(v[14])
                self.ask_price_L3 = float(v[15])
                self.ask_size_L3 = int(v[16])
                self.bid_price_L4 = float(v[17])
                self.bid_size_L4 = int(v[18])
                self.ask_price_L4 = float(v[19])
                self.ask_size_L4 = int(v[20])
                self.bid_price_L5 = float(v[21])
                self.bid_size_L5 = int(v[22])
                self.ask_price_L5 = float(v[23])
                self.ask_size_L5 = int(v[24])
                self.open_interest = int(v[25])
                self.open = float(v[26])
                self.high = float(v[27])
                self.low = float(v[28])
                self.pre_close = float(v[29])
                self.upper_limit_price = float(v[30])
                self.lower_limit_price = float(v[31])
        except:
            pass

    def __str__(self):
        return "Time: %s, Ticker: %s, Type: %s,  Price: %s, Size %s" % (
            str(self.timestamp), str(self.full_symbol), (self.tick_type),
            str(self.price), str(self.size)
        )
