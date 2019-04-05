#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
from enum import Enum
from ..event.event import *
import time
import pandas as pd
class TickType(Enum):
    # same as msg_type
    Tick_L1 = 1000
    Tick_L5 = 1001
    Tick_L10 =1002
    Tick_L20 = 1003
    Bar_1min = 1011
    Bar_5min = 1012
    Bar_15min = 1013
    Bar_1h = 1014
    Bar_1d = 1015
    Bar_1w = 1016
    Bar_1m = 1017
    Trade = 1060		
    Bid = 1061
    Ask = 1062
    Full = 1063
    BidPrice = 1064
    BidSize = 1065
    AskPrice = 1066
    AskSize = 1067
    Price = 1068
    TradeSize = 1069
    OpenPrice = 1070
    HighPrice = 1071
    LowPrice = 1072
    ClosePrice = 1073
    Volume = 1074
    OpenInterest = 1075
    Bar = 1076







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
        self.source = ''
        self.destination = ''
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
            self.destination = v[0]
            self.source = v[1]
            self.tick_type = TickType(int(v[2]))
            # print('tick type',self.tick_type,self.tick_type == TickType.Tick_L1)
            self.full_symbol = v[3]
            #self.timestamp = time.mktime(time.strptime(v[1],'%Y-%m-%d %H:%M:%S.%f'))
            self.timestamp =pd.to_datetime(v[4])
            self.price = float(v[5])
            self.size = int(v[6])

            if (self.tick_type == TickType.Tick_L1):
                # print('tickl1 deserialize')
                self.bid_price_L1 = float(v[7])
                self.bid_size_L1 = int(v[8])
                self.ask_price_L1 = float(v[9])
                self.ask_size_L1 = int(v[10])
                self.open_interest = int(v[11])
                self.open = float(v[12])
                self.high = float(v[13])
                self.low = float(v[14])
                self.pre_close = float(v[15])
                self.upper_limit_price = float(v[16])
                self.lower_limit_price = float(v[17])
            elif (self.tick_type == TickType.Tick_L5):
                self.bid_price_L1 = float(v[7])
                self.bid_size_L1 = int(v[8])
                self.ask_price_L1 = float(v[9])
                self.ask_size_L1 = int(v[10])
                self.bid_price_L2 = float(v[11])
                self.bid_size_L2 = int(v[12])
                self.ask_price_L2 = float(v[13])
                self.ask_size_L2 = int(v[14])
                self.bid_price_L3 = float(v[15])
                self.bid_size_L3 = int(v[16])
                self.ask_price_L3 = float(v[17])
                self.ask_size_L3 = int(v[18])
                self.bid_price_L4 = float(v[19])
                self.bid_size_L4 = int(v[20])
                self.ask_price_L4 = float(v[21])
                self.ask_size_L4 = int(v[22])
                self.bid_price_L5 = float(v[23])
                self.bid_size_L5 = int(v[24])
                self.ask_price_L5 = float(v[25])
                self.ask_size_L5 = int(v[26])
                self.open_interest = int(v[27])
                self.open = float(v[28])
                self.high = float(v[29])
                self.low = float(v[30])
                self.pre_close = float(v[31])
                self.upper_limit_price = float(v[32])
                self.lower_limit_price = float(v[33])
        except:
            pass

    def __str__(self):
        return "Time: %s, Ticker: %s, Type: %s,  Price: %s, Size %s" % (
            str(self.timestamp), str(self.full_symbol), (self.tick_type),
            str(self.price), str(self.size)
        )
