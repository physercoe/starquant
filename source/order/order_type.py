#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

# OrderType.MKT.name == 'MKT'  OderType.MKT.value == 0
class OrderType(Enum):
    MKT = 0
    MKTC = 1    #market on close
    LMT = 2     #limit
    LMTC = 3
    PTM = 4        # peggedtomarket
    STP = 5       
    STPLMT = 6
    TRAIING_STOP = 7
    REL = 8           #relative
    VWAP = 9        # volumeweightedaverageprice
    TSL = 10            #trailingstoplimit
    VLT = 11           #volatility
    NONE = 12
    EMPTY = 13
    DEFAULT = 14
    SCALE = 15        
    MKTT =16           # market if touched
    LMTT =17           # limit if touched
    OPTE = 18         # used in tap opt exec
    OPTA = 19        # opt abandon
    REQQ = 20        #  request quot
    RSPQ = 21       # response quot
    SWAP = 22        # swap