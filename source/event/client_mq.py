#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue, Empty
from threading import Thread
from nanomsg import Socket, PAIR, SUB, PUB, SUB_SUBSCRIBE, AF_SP
from source.data.tick_event import TickEvent, TickType
from source.order.order_status_event import OrderStatusEvent
from source.order.fill_event import FillEvent
from source.event.event import GeneralEvent,MSG_TYPE
from source.position.position_event import PositionEvent
from source.position.contract_event import ContractEvent
from source.data.historical_event import HistoricalEvent
from source.account.account_event import AccountEvent

class ClientMq(object):
    def __init__(self, ui_event_engine, outgoing_quue):
        self._ui_event_engine = ui_event_engine
        self._outgoing_quue = outgoing_quue
        self._tick_sock = Socket(SUB)
        self._msg_sock = Socket(PUB)

        self._active = False
        self._thread = Thread(target=self._run)

    def _run(self):
        while self._active:
            try:
                # subscribed market data msg from server
                msg1 = self._tick_sock.recv(flags=1)
                msg1 = msg1.decode("utf-8")
                if msg1 is not None and msg1.index('|') > 0:
                    #print('client rec tick msg',msg1)
                    if msg1[-1] == '\0':
                        msg1 = msg1[:-1]
                    # print('client recv tick: ',msg1)
                    k = TickEvent()
                    k.deserialize(msg1)
                    #print(k.ask_price_L1)
                    self._ui_event_engine.put(k)
            except Exception as e:
                pass

            try:
                # response msg from server
                msg2 = self._tick_sock.recv(flags=1)
                msg2 = msg2.decode("utf-8")
                if msg2 is not None and msg2.index('|') > 0:
                    print('client rec broker msg:',msg2)
                    if msg2[-1] == '\0':
                        msg2 = msg2[:-1]
                    if msg2[-1] == '\x00':
                        msg2 = msg2[:-1]
                    v = msg2.split('|')
                    msg2type = MSG_TYPE(int(v[2]))
                    if msg2type == MSG_TYPE.MSG_TYPE_RTN_ORDER:
                       m = OrderStatusEvent()
                       m.deserialize(msg2)
                       self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RTN_TRADE:
                        m = FillEvent()
                        m.deserialize(msg2)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_POS:
                        m = PositionEvent()
                        m.deserialize(msg2)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_Hist:
                        m = HistoricalEvent()
                        m.deserialize(msg2)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_ACCOUNT:
                        m = AccountEvent()
                        m.deserialize(msg2)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_CONTRACT:
                        m = ContractEvent()
                        m.deserialize(msg2)
                        self._ui_event_engine.put(m)
                    elif msg2type == MSG_TYPE.MSG_TYPE_INFO:
                        m = GeneralEvent()
                        m.deserialize(msg2)
                        self._ui_event_engine.put(m)
                        pass

            except Exception as e:
                pass
                # print('PAIR error: '+ str(i) + '' + str(e));
                # time.sleep(1)

            try:
                # request, qry msg to server
                msg3 = self._outgoing_quue.get(False)
                print('outgoing get msg,begin nano',msg3)
                self._msg_sock.send(bytes(msg3,"ascii"), flags=1)
            except Exception as e:
                pass

    def start(self, timer=True):
        """
        start the mq thread
        """
        #self._tick_sock.connect(b'tcp://127.0.0.1:55559')
        self._tick_sock.connect('tcp://127.0.0.1:55555')
        #self._tick_sock.connect('tcp://localhost:55555')
        self._tick_sock.set_string_option(SUB, SUB_SUBSCRIBE, '')  # receive msg start with all

        #self._msg_sock.connect('tcp://localhost:55558')
        #self._msg_sock.connect(b'tcp://127.0.0.1:55558')
        self._msg_sock.bind('tcp://127.0.0.1:55558')
        # self._msg_sock.connect('tcp://127.0.0.1:55558')
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