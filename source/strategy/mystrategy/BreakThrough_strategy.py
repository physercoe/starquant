#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..strategy_base import StrategyBase
from ...order.order_event import OrderEvent
from ...order.order_type import OrderType
from ...order.order_flag import OrderFlag
from ...position.margin import marginrate
from datetime import timedelta
from pandas import Timestamp
import numpy as np
class BreakThroughStrategy(StrategyBase):
    """
    high point sell and low point buy
    """
    def __init__(self, events_engine,order_manager,portfolio_manager,
                start_time=Timestamp('1970-01-01'),end_time = Timestamp('1970-01-01'),
                act_period=3600,ordersize=30,buy_trig = 20,sell_trig=20,close_trig=20):
        super(BreakThroughStrategy, self).__init__(events_engine,order_manager,portfolio_manager)
        """
        state:action indicator
        **trig:action conditon
        """
        self.ticks = 0
        self.sign = 1
        self.high_point= 4078
        self.low_point= 4045
        self.prices = []
        self.sizeperorder = ordersize
        self.state = 0
        self.starttime = start_time
        self.endtime = end_time
        self.actperiod = act_period
        self.zuli = buy_trig
        self.zhicheng = sell_trig
        self.buy_stop_loss = 3.0
        self.sell_stop_loss = 0.0
        self.closetrig = close_trig
        self.openprice =0.0
        self.endprice =0.0
        self.orderclosetime = Timestamp('1970-01-01')
        self.orderopenprice =0
        self.orderopentime =Timestamp('1970-01-01')
        self.firstpass = True
        self.lastprice = 0.0

        self.openclosetime = 3     #开盘多长时间内不交易
        self.openhour = 21
        self.closehour = 22
        self.closeminute = 60
        self.fudong = 3            #入场滑点
        self.zisundianwei = 3.0    #止损点位

    def on_tick(self, k):
#        if(self.state == -1):
#            return

        self.prices.append(k.price)
#        if (k.timestamp.hour == 21 and k.timestamp.minute <= 1) : #开盘一段时间内确定高低点
#            self.high_point = max(self.prices)    #前一天高点
#            self.low_point = min(self.prices)     #前一天低点
        #print("breakthrough on tick")
        if (k.timestamp.hour ==15) :           
            self.high_point = max(self.prices)    #前一天高点
            self.low_point = min(self.prices)     #前一天低点
            print('今日高点：',self.high_point)
            print('今日低点：',self.low_point)
            self.prices = []
            print('下午收盘时间:',k.timestamp)
        
        symbol = self.symbols[0]

        if k.full_symbol == symbol:
            if(len(self.prices)>1):    #判断价格高低点
                self.high_point = max(self.high_point,self.lastprice)
                self.low_point = min(self.low_point,self.lastprice)            
            self.lastprice = k.price

#开盘收盘时间范围布尔值
            dayopenCondition = (k.timestamp.hour > 9 or k.timestamp.hour == 9 and k.timestamp.minute > self.openclosetime)
            daycloseCondition = (k.timestamp.hour < 15  or k.timestamp.hour == 14 and k.timestamp.minute < 60 - self.openclosetime)
            nightopenCondition = (k.timestamp.hour > self.openhour or k.timestamp.hour == self.openhour and k.timestamp.minute > self.openclosetime)
            nightcloseCondition = (k.timestamp.hour < self.closehour  or k.timestamp.hour == self.closehour and k.timestamp.minute < self.closeminute - self.openclosetime)
            opencondition = (dayopenCondition and daycloseCondition) or( nightopenCondition and nightcloseCondition)
#开盘收盘时间范围布尔值end

            if(symbol in self._portfolio_manager.positions):
                pnl = self._portfolio_manager.positions[symbol].unrealized_pnl
                allmoney =self._portfolio_manager.cash   #现金
                buy_qty = self._portfolio_manager.positions[symbol].buy_quantity
                sell_qty = self._portfolio_manager.positions[symbol].sell_quantity
                #print(pnl,allmoney,buy_qty)

                if (pnl <-0.03*allmoney):
                    self.orderclosetime = k.timestamp
                    if( buy_qty > 0):
                        print('亏损超过总权益特定百分比，平多仓')
                        self.sell_close(symbol,buy_qty,type='lmt',price=k.ask_price_L1,closetoday=True)
                    if (sell_qty > 0):
                        print('亏损超过总权益特定百分比，平空仓')
                        self.buy_close(symbol,sell_qty,type='lmt',price=k.bid_price_L1,closetoday=True)
                    return


#一、出场条件

#出场条件1，下午收盘前一段时间与晚上睡觉前一段时间必须平仓

                if ((k.timestamp.hour ==14) and (k.timestamp.minute == 60- self.openclosetime) and (buy_qty != 0)):
                    self.orderclosetime = k.timestamp
                    if( buy_qty > 0):
                        print('下午收盘平多仓')
                        self.sell_close(symbol,buy_qty,type='lmt',price=k.ask_price_L1,closetoday=True)
                    if (buy_qty < 0):
                        print('下午收盘平空仓')
                        self.buy_close(symbol,sell_qty,type ='lmt',price=k.bid_price_L1,closetoday=True)
                    opencondition=False
                    return

                if ((k.timestamp.hour == self.closehour) and(k.timestamp.minute == self.closeminute - self.openclosetime) and (buy_qty != 0)):
                    self.orderclosetime = k.timestamp
                    if( buy_qty > 0):
                        print('晚收盘平多仓')
                        self.sell_close(symbol,buy_qty,type='lmt',price=k.ask_price_L1,closetoday=True)
                    if (buy_qty < 0):
                        print('晚收盘平空仓')
                        self.buy_close(symbol,sell_qty,type ='lmt',price=k.bid_price_L1,closetoday=True)
                    opencondition=False
                    return

#出场条件1，下午收盘前一段时间与晚上睡觉前一段时间必须平仓end

#出场条件2，在入场之后瞬间价格马上往相反方向走，支撑阻力点位止损
#                if(buy_qty > 0) and (k.timestamp-self.orderopentime >= timedelta(seconds = 2)): #开仓时刻之后2秒开始判断
#                    if (k.price > self.zuli + 2):
#                        self.buy_stop_loss = self.zuli + 1 
##                        print('买仓判断正确，止损调到成本价:',self.buy_stop_loss,',',k.timestamp)
#
#                if(buy_qty < 0) and (k.timestamp-self.orderopentime >= timedelta(seconds = 2)): #开仓时刻之后2秒开始判断
#                    if (k.price < self.zhicheng - 2):
#                        self.sell_stop_loss = self.zhicheng - 1

#                        print('卖仓判断正确，止损调到成本价:',self.sell_stop_loss,',',k.timestamp)


                if(buy_qty > 0) and (k.price <= self.buy_stop_loss):
                    self.orderclosetime = k.timestamp
                    if (self.buy_stop_loss > self.zuli):
                        print('上涨犹豫，成本价卖平出场',k.price,',',k.timestamp)
                        self.sell_close(symbol,buy_qty,type ='lmt',price=k.bid_price_L1,closetoday=True)
                    else:
                        print('方向开错，卖平止损',k.price,',',k.timestamp)
                        self.sell_close(symbol,buy_qty,type ='lmt',price=k.bid_price_L1,closetoday=True)
                    return

                if(sell_qty > 0) and (k.price >= self.sell_stop_loss):
                    self.orderclosetime = k.timestamp
                    if (self.sell_stop_loss < self.zhicheng):
                        print('下跌犹豫，成本价买平出场',k.price,',',k.timestamp)
                        self.buy_close(symbol,sell_qty,type ='lmt',price=k.bid_price_L1,closetoday=True)
                    else:
                        print('方向开错，买平止损',k.price,',',k.timestamp)
                        self.buy_close(symbol,sell_qty,type ='lmt',price=k.bid_price_L1,closetoday=True)
                    return
#出场条件2，在入场之后瞬间价格马上往相反方向走，支撑阻力点位止损end

#时间止损
#                if((buy_qty > 0) and (k.timestamp-self.orderopentime > timedelta(minutes=10))):
#                    obtimedelta = k.timestamp-self.orderopentime
#                    if k.price < self.zuli+5.0+obtimedelta.total_seconds()/60 * 0.0:
#                        o = OrderEvent()
#                        o.full_symbol = symbol
#                        o.order_type = OrderType.MKT
#                        o.order_flag = OrderFlag.CLOSE
#                        o.order_size = -1*buy_qty
#                        self.place_order(o)
#                        self.orderclosetime = k.timestamp
#                        print('时间止损平多仓：',k.price,',',k.timestamp)
#                        return
#
#                if((buy_qty < 0) and (k.timestamp-self.orderopentime > timedelta(minutes=10))):
#                    obtimedelta = k.timestamp-self.orderopentime
#                    if k.price > self.zhicheng-5.0-obtimedelta.total_seconds()/60 * 0.0:
#                        o = OrderEvent()
#                        o.full_symbol = symbol
#                        o.order_type = OrderType.MKT
#                        o.order_flag = OrderFlag.CLOSE
#                        o.order_size = -1*buy_qty
#                        self.place_order(o)
#                        self.orderclosetime = k.timestamp
#                        print('时间止损平空仓：',k.price,',',k.timestamp)
#                        #self.state=-1
#                        return

#时间止损end
#一、出场条件end


#入场条件
                if ((k.price > self.high_point) and (k.price <= self.high_point +self.fudong) and opencondition):
                    if(buy_qty >0):
                        pass
                    elif buy_qty==0:
                        shoushu = int(0.6*allmoney/k.price/marginrate(symbol))
                        shoushu = 1
                        self.orderopentime = k.timestamp
                        self.zuli =self.high_point
                        self.buy_stop_loss = self.zuli - self.zisundianwei
                        print("向上突破阻力，开多,",k.price,',',k.timestamp)
                        self.buy_open(symbol,shoushu,type ='lmt',price=k.bid_price_L1)
                        return

                if ((k.price < self.low_point) and (k.price >= self.low_point -self.fudong) and opencondition):
                    if(sell_qty > 0):
                        pass
                    elif sell_qty==0:
                        shoushu = int(0.6*allmoney/k.price/marginrate(symbol))
                        shoushu  =1
                        self.orderopentime = k.timestamp
                        self.zhicheng =self.low_point
                        self.sell_stop_loss = self.zhicheng + self.zisundianwei
                        print("向下突破支撑，开空,",k.price,',',k.timestamp)
                        self.sell_open(symbol,shoushu,type ='lmt',price=k.ask_price_L1)
                        return
#入场条件end

