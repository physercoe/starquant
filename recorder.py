#!/usr/bin/env python
# -*- coding: utf-8 -*-
import mystrategy
import sys,getopt
import os
import atexit
import signal
from multiprocessing import Process

from source.engine.recorder_engine import RecorderEngine

recorderengine = RecorderEngine()
recorderengine.start()




