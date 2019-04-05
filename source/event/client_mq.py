#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue, Empty
from threading import Thread
from nanomsg import Socket, PAIR, SUB, PUB, SUB_SUBSCRIBE, AF_SP
from source.data.tick_event import TickEvent, TickType
from source.order.order_status_event import OrderStatusEvent
from source.order.fill_event import FillEvent
from source.event.event import InfoEvent,MSG_TYPE
from source.position.position_event import PositionEvent
from source.position.contract_event import ContractEvent
from source.data.historical_event import HistoricalEvent
from source.account.account_event import AccountEvent
from datetime import datetime
class ClientMq(object):
    def __init__(self, config, ui_event_engine, outgoing_quue):
        self._ui_event_engine = ui_event_engine
        self._outgoing_quue = outgoing_quue
        self._recv_sock = Socket(SUB)
        self._send_sock = Socket(PUB)
        self._config = config

        self._active = False
        self._thread = Thread(target=self._run)

    def _run(self):
        while self._active:
            try:
                # response msg from server
                msgin = self._recv_sock.recv(flags=1)
                msgin = msgin.decode("utf-8")
                if msgin is not None and msgin.index('|') > 0:
                    print('client rec broker msg:',msgin,'at ', datetime.now())
                    if msgin[-1] == '\0':
                        msgin = msgin[:-1]
                    if msgin[-1] == '\x00':
                        msgin = msgin[:-1]
                    v = msgin.split('|')
                    msg2type = MSG_TYPE(int(v[2]))
                    if msg2type == MSG_TYPE.MSG_TYPE_TICK_L1:
                        k = TickEvent()
                        k.deserialize(msgin)
                        self._ui_event_engine.put(k)    
                    elif msg2type == MSG_TYPE.MSG_TYPE_RTN_ORDER:
                       m = OrderStatusEvent()
                       m.deserialize(msgin)
                       self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RTN_TRADE:
                        m = FillEvent()
                        m.deserialize(msgin)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_POS:
                        m = PositionEvent()
                        m.deserialize(msgin)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_Hist:
                        m = HistoricalEvent()
                        m.deserialize(msgin)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_ACCOUNT:
                        m = AccountEvent()
                        m.deserialize(msgin)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_CONTRACT:
                        m = ContractEvent()
                        m.deserialize(msgin)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_INFO:
                        m = InfoEvent()
                        m.deserialize(msgin)
                        self._ui_event_engine.put(m)
                        pass
            except Exception as e:               
                pass
            try:
                # request, qry msg to server
                msgout = self._outgoing_quue.get(False)
                print('outgoing get msg,begin send',msgout)
                # self._send_sock.send(bytes(msgout,"ascii"), flags=0)
                self._send_sock.send(msgout, flags=1)
            except Exception as e:
                pass

    def start(self, timer=True):
        """
        start the mq thread
        """
        
        self._recv_sock.connect(self._config['serverpub_url'])
        self._recv_sock.set_string_option(SUB, SUB_SUBSCRIBE, '')  # receive msg start with all
        self._send_sock.bind(self._config['serversub_url'])
        self._active = True
        if not self._thread.isAlive():
            self._thread.start()

    def stop(self):
        """
        stop the mq thread
        """
        self._active = False

        if self._thread.isAlive():
            self._thread.join()