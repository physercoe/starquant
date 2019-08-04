#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import sys,getopt
# import os
# import signal
# from multiprocessing import Process
import atexit


from source.engine.tbt_recorder_engine import TBTRecorderEngine

recorderengine = TBTRecorderEngine()
atexit.register(recorderengine.stop)
recorderengine.start()




