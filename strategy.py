#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import sys,getopt
# import os
# import signal
# from multiprocessing import Process

import atexit
from source.engine.strategy_engine import StrategyEngine


ctaengine = StrategyEngine()
atexit.register(ctaengine.stop)
ctaengine.start()




