#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..strategy_base import StrategyBase
from ...order.order_event import OrderEvent
from ...order.order_type import OrderType
from ...order.order_flag import OrderFlag


class OrderPerIntervalStrategy(StrategyBase):
    """
    buy on the first tick then hold to the end
    """
    def __init__(self, events_engine,order_manager,portfolio_manager):
        super(OrderPerIntervalStrategy, self).__init__(events_engine,order_manager,portfolio_manager)
        self.ticks = 0
        self.tick_trigger_threshold = 2
        self.sign = 1

    def on_tick(self, k):
        print("OPI handle tick",self.id)
        symbol = self.symbols[0]
        if k.full_symbol == symbol:
            #print(k)
            if (self.ticks > self.tick_trigger_threshold):
                print("pos info: ",self._portfolio_manager.get_live_posinfo_bysymbol(symbol))
                print("total value: ",self._portfolio_manager.get_total_value(True))
                # o = OrderEvent()
                # o.full_symbol = symbol
                # o.account ="Q359047946"
                # o.order_type = OrderType.MKT
                # o.order_flag = OrderFlag.OPEN
                # o.order_size = 1 * self.sign
                # print('place order')
                # self.place_order(o)

                # self.ticks = 0
                # self.sign = self.sign * (-1)
            else:
                self.ticks += 1