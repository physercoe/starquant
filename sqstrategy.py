#!/usr/bin/env python
# -*- coding: utf-8 -*-
import mystrategy
import sys,getopt
import os
import atexit
import signal
from multiprocessing import Process

spids = []
def stopstrategy():
    global spids
    if spids:
        for pid in spids:
            os.kill(pid,signal.SIGINT)


if __name__ == "__main__":
    atexit.register(stopstrategy)
    if len(sys.argv) < 2:
        print('no parameters, usage: -i [strategy id] or -n [startegy class name] ')
    try:
        opts, args = getopt.getopt(sys.argv[1:],'ni',longopts=[])
        for opt, arg in opts:
            if "-n" == opt:
                for i in range(len(args)):
                    p = Process(target=mystrategy.startstrategy, args=(args[i],))
                    spids.append(p.pid)
                    p.start()
            elif '-i' == opt :
                for i in range(len(args)):
                    p = Process(target=mystrategy.startsid, args=(int(args[i]),))
                    spids.append(p.pid)
                    p.start()        
    except getopt.GetoptError as e:
        print(e.msg, 'usage: -i [strategy id] or -n [startegy class name],eg:./runstrategy -i 9999 ')
        sys.exit(1)


