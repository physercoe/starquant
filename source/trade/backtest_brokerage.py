#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .brokerage_base import BrokerageBase
from ..common.datastruct import *

from queue import Queue, Empty

class BacktestBrokerage(BrokerageBase):
    """
    Backtest brokerage: market order will be immediately filled.
            limit/stop order will be saved to _active_orders for next tick
    """
    def __init__(self, events_engine, data_board):
        """
        Initialises the handler, setting the event queue
        as well as access to local pricing.
        """
        self._events_engine = events_engine
        self._data_board = data_board
        self._active_orders = {}
        self._queue = Queue()
        self._active = True

    # ------------------------------------ private functions -----------------------------#
    def _calculate_commission(self, full_symbol, fill_price, fill_size):        #手续费计算方法
        # take ib commission as example
        # if 'STK' in full_symbol:
        #     commission = max(0.005*abs(fill_size), 1)
        # elif 'FUT' in full_symbol:
        #     commission = 2.01 * abs(fill_size)
        # elif 'OPT' in full_symbol:
        #     commission = max(0.7 * abs(fill_size), 1)
        # elif 'CASH' in full_symbol:
        #     commission = max(0.000002 * abs(fill_price * fill_size), 2)
        # else:
        #     commission = 0
        commission = 0.1*abs(fill_size)        #手续费计算方法

        return commission

    def _cross_limit_order(self):
        pass

    def _cross_stop_order(self):
        pass

    def _cross_market_order(self):
        pass
    # -------------------------------- end of private functions -----------------------------#

    # -------------------------------------- public functions -------------------------------#
    def reset(self):
        self._active_orders.clear()

    def on_bar(self):
        pass

    def on_tick(self,tickevent):
        if not self._active:
            return False
        while (self._active):
            try:
                event = self._queue.get(False)                
            except Empty:   # throw good exception
                self._active = False
            else:  # not empty
                try:
                    # call event handlers
                    #print(event.event_type)
                    self.place_order(event)
                except Exception as e:
                    #print("Error in event handler")
                    print("Error {0}".format(str(e.args[0])).encode("utf-8"))
        return True

    def place_order(self, order_event):
        """
        immediate fill, no latency or slippage
        """
        ## TODO: acknowledge the order
        order_event.order_status = OrderStatus.FILLED

        fill = FillEvent()
        fill.client_order_id = order_event.client_order_id
        fill.broker_order_id = order_event.broker_order_id
        fill.timestamp = self._data_board.get_last_timestamp(order_event.full_symbol)
        fill.full_symbol = order_event.full_symbol
        fill.fill_size = order_event.order_size
       

        if fill.fill_size > 0 :
            fill.fill_price = self._data_board.get_s1_price(order_event.full_symbol)      #滑点可以在此处设置。
        elif fill.fill_size < 0 :
            fill.fill_price = self._data_board.get_b1_price(order_event.full_symbol)      #滑点可以在此处设置。
        else :
            print('order_size = 0 or somewhere is wrong')      #滑点可以在此处设置。
            return

        fill.fill_flag = order_event.order_flag
        fill.exchange = 'BACKTEST'
        fill.commission = self._calculate_commission(fill.full_symbol, fill.fill_price, fill.fill_size)   #手续费

        self._events_engine.put(fill)

    def cancel_order(self, order_id):
        """cancel order is not supported"""
        pass

    def put(self, event):
        """
        put event in the queue; call from outside
        """
        self._queue.put(event)
        self._active = True
    # ------------------------------- end of public functions -----------------------------#
