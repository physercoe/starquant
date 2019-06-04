#!/usr/bin/env python
# -*- coding: utf-8 -*-
import mystrategy
import sys,getopt
import os
import atexit
import signal
from multiprocessing import Process

from source.engine.strategy_engine import StrategyEngine



ctaengine = StrategyEngine()
atexit.register(ctaengine.stop)
ctaengine.start()




