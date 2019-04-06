#!/usr/bin/env python
# -*- coding: utf-8 -*-
from queue import Queue, Empty
from threading import Thread
from nanomsg import Socket, PAIR, SUB, PUB, PUSH,SUB_SUBSCRIBE, AF_SP
from source.data.tick_event import TickEvent, TickType
from source.order.order_status_event import OrderStatusEvent
from source.order.fill_event import FillEvent
from source.event.event import InfoEvent,MSG_TYPE
from source.position.position_event import PositionEvent
from source.position.contract_event import ContractEvent
from source.data.historical_event import HistoricalEvent
from source.account.account_event import AccountEvent
from datetime import datetime
import os
from collections import defaultdict

class TradeEngine(object):
    """
    Send to and receive from msg  server ,used for strategy 
    """
    def __init__(self,config):
        """
        two sockets to send and recv msg
        """
        self.__active = False

        self._recv_sock = Socket(SUB)
        self._send_sock = Socket(PUSH)
        self._config = config
        self._handlers = defaultdict(list)


    #------------------------------------ public functions -----------------------------#
    def start(self, timer=True):
        """
        start the dispatcher thread
        """

        self._recv_sock.connect(self._config['serverpub_url'])
        self._recv_sock.set_string_option(SUB, SUB_SUBSCRIBE, '')  # receive msg start with all
        self._send_sock.connect(self._config['serverpull_url'])
        self.__active = True
        print(self._config['serverpub_url'])
        while self.__active:
            try:
                msgin = self._recv_sock.recv(flags=1)
                msgin = msgin.decode("utf-8")
                if msgin is not None and msgin.index('|') > 0:
                    # print('tradeengine rec broker msg:',msgin,'at ', datetime.now())
                    if msgin[-1] == '\0':
                        msgin = msgin[:-1]
                    if msgin[-1] == '\x00':
                        msgin = msgin[:-1]
                    v = msgin.split('|')
                    msg2type = MSG_TYPE(int(v[2]))
                    if msg2type == MSG_TYPE.MSG_TYPE_TICK_L1:
                        m = TickEvent()
                        m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RTN_ORDER:
                       m = OrderStatusEvent()
                       m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RTN_TRADE:
                        m = FillEvent()
                        m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_POS:
                        m = PositionEvent()
                        m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_Hist:
                        m = HistoricalEvent()
                        m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_ACCOUNT:
                        m = AccountEvent()
                        m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_RSP_CONTRACT:
                        m = ContractEvent()
                        m.deserialize(msgin)
                    elif msg2type == MSG_TYPE.MSG_TYPE_INFO:
                        m = InfoEvent()
                        m.deserialize(msgin)
                        pass
                    if m.event_type in self._handlers:
                        [handler(m) for handler in self._handlers[m.event_type]]
            except Exception as e:
                pass
                # print("TradeEngineError {0}".format(str(e.args[0])).encode("utf-8"))
 
    def stop(self):
        """
        stop 
        """
        self.__active = False

    def put(self, event):
        """
        send event msg,TODO:check the event
        """
        # 
        self._send_sock.send(event.serialize(),flags=1)

    def register_handler(self, type_, handler):
        """
        register handler/subscriber
        """
        handlerList = self._handlers[type_]

        if handler not in handlerList:
            self._handlers[type_].append(handler)
            #handlerList.append(handler)

    def unregister_handler(self, type_, handler):
        """
        unregister handler/subscriber
        """
        handlerList = self._handlers[type_]

        if handler in handlerList:
            self._handlers.remove(handler)

        if not handlerList:
            del self._handlers[type_]


    # -------------------------------- end of public functions -----------------------------#