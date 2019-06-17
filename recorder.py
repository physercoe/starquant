#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import sys,getopt
# import os
# import signal
# from multiprocessing import Process
import atexit


from source.engine.recorder_engine import RecorderEngine

recorderengine = RecorderEngine()
atexit.register(recorderengine.stop)
recorderengine.start()




