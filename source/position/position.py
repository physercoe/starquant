#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..util.util_func import retrieve_multiplier_from_full_symbol
from ..order.order_flag import OrderFlag
class Position(object):
    def __init__(self, full_symbol, average_price=0, size=0, realized_pnl=0):
        """
        Position includes zero/closed security
        """
        ## TODO: add cumulative_commission, long_trades, short_trades, round_trip etc
        self.full_symbol = full_symbol
        # average price includes commission
        self.average_price = average_price
        self.avg_buy_price = 0
        self.avg_sell_price = 0
        self.size = size
        self.buy_quantity = 0            #多头仓位
        self.sell_quantity = 0           #空头仓位
        self.realized_pnl = 0          #平仓盈亏
        self.unrealized_pnl = 0        #浮盈
        self.buy_realized_pnl = 0
        self.sell_realized_pnl = 0
        self.buy_unrealized_pnl = 0
        self.sell_unrealized_pnl = 0
        self.last_realized_pnl =0 
        self.api = ''
        self.account = ''
        self.posno =''
        self.openorderNo = ''
        self.openapi = ''
        self.opensource = -1
        self.closeorderNo = ''
        self.closeapi = ''
        self.closesource = -1

    def mark_to_market(self, last_price):
        """
        given new market price, update the position
        """
        # if long or size > 0, pnl is positive if last_price > average_price
        # else if short or size < 0, pnl is positive if last_price < average_price
        self.buy_unrealized_pnl = (last_price - self.avg_buy_price) * self.buy_quantity \
                              * retrieve_multiplier_from_full_symbol(self.full_symbol)
        self.sell_unrealized_pnl = -1*(last_price - self.avg_sell_price) * self.sell_quantity \
                              * retrieve_multiplier_from_full_symbol(self.full_symbol)
        self.unrealized_pnl = self.buy_unrealized_pnl +self.sell_unrealized_pnl

    def on_fill(self, fill_event):
        """
        adjust average_price and size according to new fill/trade/transaction
        """
        if self.full_symbol != fill_event.full_symbol:
            print(
                "Position symbol %s and fill event symbol %s do not match. "
                % (self.full_symbol, fill_event.full_symbol)
            )
            return

        # if self.size > 0:        # existing long
        #     if fill_event.fill_size > 0:        # long more
        #         self.average_price = (self.average_price * self.size + fill_event.fill_price * fill_event.fill_size
        #                               + fill_event.commission / retrieve_multiplier_from_full_symbol(self.full_symbol)) \
        #                              / (self.size + fill_event.fill_size)
        #     else:        # flat long
        #         if abs(self.size) >= abs(fill_event.fill_size):   # stay long
        #             self.realized_pnl += (self.average_price - fill_event.fill_price) * fill_event.fill_size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #         else:   # flip to short
        #             self.realized_pnl += (fill_event.fill_price - self.average_price) * self.size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #             self.average_price = fill_event.fill_price
        # else:        # existing short
        #     if fill_event.fill_size < 0:         # short more
        #         self.average_price = (self.average_price * self.size + fill_event.fill_price * fill_event.fill_size
        #                               + fill_event.commission / retrieve_multiplier_from_full_symbol(self.full_symbol)) \
        #                              / (self.size + fill_event.fill_size)
        #     else:          # flat short
        #         if abs(self.size) >= abs(fill_event.fill_size):  # stay short
        #             self.realized_pnl += (self.average_price - fill_event.fill_price) * fill_event.fill_size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #         else:   # flip to long
        #             self.realized_pnl += (fill_event.fill_price - self.average_price) * self.size \
        #                                  * retrieve_multiplier_from_full_symbol(self.full_symbol) - fill_event.commission
        #             self.average_price = fill_event.fill_price

        # self.size += fill_event.fill_size
        if fill_event.fill_size > 0 :
            if  fill_event.fill_flag == OrderFlag.OPEN :  # buy open
                self.avg_buy_price = (self.avg_buy_price * self.buy_quantity + fill_event.fill_price * fill_event.fill_size) \
                                    / (self.buy_quantity + fill_event.fill_size)
                self.buy_quantity += fill_event.fill_size
                print('开多仓 ：',fill_event.fill_price,fill_event.fill_size)
                print('当前多仓数量 ：', self.buy_quantity, '持仓价格',self.avg_buy_price)
            else:# buy close
                if self.sell_quantity >= fill_event.fill_size : 
                    tmp = (self.avg_sell_price - fill_event.fill_price) * fill_event.fill_size \
                                          * retrieve_multiplier_from_full_symbol(self.full_symbol)   
                    self.sell_realized_pnl += tmp                    
                    self.last_realized_pnl = tmp
                    print('平空仓盈亏：',tmp)
                    self.sell_quantity -= fill_event.fill_size
                else:  
                    print(" error: fill buy close size >sell postion size") 
        else:
            if  fill_event.fill_flag == OrderFlag.OPEN :  # sell open
                self.avg_sell_price = (self.avg_sell_price * self.sell_quantity - fill_event.fill_price * fill_event.fill_size) \
                                    / (self.sell_quantity - fill_event.fill_size)
                self.sell_quantity -= fill_event.fill_size
                print('开空仓 ：',fill_event.fill_price,fill_event.fill_size)
                print('当前空仓数量：',self.sell_quantity,'持仓价格''',self.avg_sell_price)               
            else: # sell close
                if self.buy_quantity >= abs(fill_event.fill_size) :
                    tmp =  (self.avg_buy_price - fill_event.fill_price) * fill_event.fill_size \
                                        * retrieve_multiplier_from_full_symbol(self.full_symbol) 
                    self.buy_realized_pnl += tmp
                    self.last_realized_pnl = tmp
                    print('平多仓盈亏：',tmp)
                    self.buy_quantity += fill_event.fill_size
                else:  
                    print(" error: fill sell close size >buy postion size")             
        self.realized_pnl = self.buy_realized_pnl + self.sell_realized_pnl

    def withdrawcash(self,ratio=1.0):
        tmp = self.realized_pnl*ratio
        self.realized_pnl =(1-ratio) * self.realized_pnl
        return tmp