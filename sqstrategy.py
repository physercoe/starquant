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
        opts, args = getopt.getopt(sys.argv[1:],'bni',longopts=[])
        for opt, arg in opts:
            if "-n" == opt:
                for i in range(len(args)):
                    p = Process(target=mystrategy.startstrategy, args=(args[i],))
                    p.start()
                    spids.append(p.pid)
                    
            elif '-i' == opt :
                for i in range(len(args)):
                    p = Process(target=mystrategy.startsid, args=(int(args[i]),))
                    p.start()
                    spids.append(p.pid)                    
            elif  '-b' == opt :
                for i in range(len(args)):
                    p = Process(target=mystrategy.backtestsid, args=(int(args[i]),))
                    p.start() 
                    spids.append(p.pid)
                    print('Strategy {} run pid {}'.format(args[i],p.pid))
                                         
    except getopt.GetoptError as e:
        print(e.msg, 'usage: -i [strategy id] or -n [startegy class name],eg:./runstrategy -i 9999 ')
        sys.exit(1)


