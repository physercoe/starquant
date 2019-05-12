#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import copy
from functools import lru_cache

from ..common.datastruct import *
from ..common.config import marginrate
from ..engine.iengine import BaseEngine
class PortfolioManager(object):
    def __init__(self, initial_cash,symbolsall):
        """
        PortfolioManager is one component of PortfolioManager
        """
        self.cash = initial_cash
        self.margin = 0.0
        self.total_value = initial_cash
        self.contracts = {}            # symbol ==> contract
        self.positions = {}            #for backtest use
        self.liveopenpositions = {}          #for live use, key is posNo
        self.liveclosepositions = {}         # for live use key is closeorderNo
        self.commission = 0
        self.open_pnl = 0
        self.closed_pnl = 0

        for sym in symbolsall:
            pos =Position(sym,0,0)
            self.positions[sym]= pos

    def reset(self):
        self.contracts.clear()
        self.positions.clear()

    def on_account(self,acc_event):
        self.cash = acc_event.available
        self.margin = acc_event.margin
        self.total_value = acc_event.balance
        self.commission = acc_event.commission
        self.open_pnl = acc_event.open_pnl
        self.closed_pnl = acc_event.closed_pnl

    def on_contract(self, contract):
        if contract.full_symbol not in self.contracts:
            self.contracts[contract.full_symbol] = contract
            print("Contract %s information received. " % contract.full_symbol)
        else:
            print("Contract %s information already exists " % contract.full_symbol)

    def on_position(self, pos_event):
        """get initial position"""
        pos = pos_event.to_position()

        if pos.full_symbol not in self.positions:
            self.positions[pos.full_symbol] = pos
        else:

            print("Symbol %s already exists in the portfolio " % pos.full_symbol)
    def on_position_live(self,pos_event):
        if (pos_event.type == 'n') or (pos_event.type =='a'):
            # print(pos_event.opensource)
            pos = pos_event.to_position()
            self.liveopenpositions[pos.posno] = pos
            if pos_event.size == 0:
                self.liveopenpositions.pop(pos.posno)

        elif (pos_event.type == 'u'):
            if pos_event.posno in self.liveopenpositions:
                self.liveopenpositions[pos_event.posno].unrealized_pnl = pos_event.unrealized_pnl
            else:
                print("warning: posno not in portfolio list, cant update openprofit!")
        elif (pos_event.type == 'c' ):
            pos = pos_event.to_position()
            self.liveclosepositions[pos_event.closeorderNo] = pos
        else:
            print("warning: unknown position event type!")
            pass

    def on_fill(self, fill_event):
        """
        处理成交信息，更新持仓信息
        """
        # 计算手续费
        self.commission += fill_event.commission
        self.cash -= fill_event.commission
        #调整持仓头寸和持仓价格
        if fill_event.full_symbol not in self.positions:      # adjust existing position
            print('new pos')
            pos = Position(fill_event.full_symbol,0,0)
            self.positions[fill_event.full_symbol] = pos
        self.positions[fill_event.full_symbol].on_fill(fill_event)
        #保证金计算
        if(fill_event.fill_flag == OrderFlag.OPEN):
            tmp = abs(fill_event.fill_size) * fill_event.fill_price * marginrate(fill_event.full_symbol)            
            self.margin += tmp
            self.cash -= tmp
        else: 
            if (fill_event.fill_size >0):  # buy close
                tmp = abs(fill_event.fill_size) * self.positions[fill_event.full_symbol].avg_sell_price * marginrate(fill_event.full_symbol)
                self.margin -= tmp
                self.cash += tmp
            else :   # sell close
                tmp = abs(fill_event.fill_size) * self.positions[fill_event.full_symbol].avg_buy_price * marginrate(fill_event.full_symbol)
                self.margin -= tmp
                self.cash += tmp                
            self.cash += self.positions[fill_event.full_symbol].last_realized_pnl
            fill_event.fill_pnl = self.positions[fill_event.full_symbol].last_realized_pnl
        #更新浮盈
        self.positions[fill_event.full_symbol].mark_to_market(fill_event.fill_price)


    def on_fill_live(self,fill_event):
        fillno = fill_event.broker_fill_id
        for pos in self.liveopenpositions.values():
            if (pos.openorderNo == fillno):
                pos.opensource = fill_event.source
        for pos in self.liveclosepositions.values():
            if (pos.closeorderNo == fillno):
                pos.closesource = fill_event.source        
    #根据市场价格更新持仓浮盈
    def mark_to_market(self, current_time, symbol, last_price):
        #for sym, pos in self.positions.items():
        if symbol in self.positions:
            self.positions[symbol].mark_to_market(last_price)
    #计算总权益
    def get_total_value(self,directflag= False):
        if not directflag:
            tmp =0.0  
            for sym, pos in self.positions.items():
                tmp += pos.unrealized_pnl        
            self.total_value = self.cash + self.margin + tmp
        return self.total_value
        #print("mark2m")
    # 实盘信息统计，根据合约全称    
    def get_live_posinfo_bysymbol(self,symbol):
        buyqty = 0
        sellqty = 0
        openpnl = 0.0
        closepnl = 0.0 
        for pos in self.liveopenpositions.values():
            if (pos.full_symbol == symbol):
                buyqty += pos.buy_quantity
                sellqty += pos.sell_quantity
                openpnl += pos.unrealized_pnl
        for pos in self.liveclosepositions.values():
            if (pos.full_symbol == symbol):
                closepnl += pos.realized_pnl
        return buyqty,sellqty,openpnl,closepnl
    # 实盘信息统计，根据下单来源
    def get_live_posinfo_bysid(self,sid):
        buyqty = 0
        sellqty = 0
        openpnl = 0.0
        closepnl = 0.0  
        for pos in self.liveopenpositions.values():
            if (pos.opensource == sid):
                buyqty += pos.buy_quantity
                sellqty += pos.sell_quantity
                openpnl += pos.unrealized_pnl
        for pos in self.liveclosepositions.values():
            if (pos.closesource == sid):
                closepnl += pos.realized_pnl
        return buyqty,sellqty,openpnl,closepnl



class OffsetConverter:
    """"""

    def __init__(self, main_engine: BaseEngine):
        """"""
        self.main_engine = main_engine
        self.holdings = {}
        # self.add_function()

    # def add_function(self):
    #     self.main_engine.get_position_holding = self.get_position_holding

    def update_position(self, position: PositionData):
        """"""
        if not self.is_convert_required(position.full_symbol):
            return

        holding = self.get_position_holding(position.account,position.full_symbol)
        holding.update_position(position)

    def update_trade(self, trade: TradeData):
        """"""
        if not self.is_convert_required(trade.full_symbol):
            return

        holding = self.get_position_holding(trade.account,trade.full_symbol)
        holding.update_trade(trade)

    def update_order(self, order: OrderData):
        """"""
        if not self.is_convert_required(order.full_symbol):
            return

        holding = self.get_position_holding(order.account,order.full_symbol)
        holding.update_order(order)

    def update_order_request(self, req: OrderRequest):
        """"""
        if not self.is_convert_required(req.full_symbol):
            return

        holding = self.get_position_holding(req.account,req.full_symbol)
        holding.update_order_request(req)

    def get_position_holding(self, acc: str, full_symbol: str):
        """"""
        holdingid = acc + "." + full_symbol
        holding = self.holdings.get(holdingid, None)
        if not holding:
            holding = PositionHolding(acc,full_symbol)
            self.holdings[holdingid] = holding
        return holding

    def convert_order_request(self, req: OrderRequest, lock: bool):
        """"""
        if not self.is_convert_required(req.full_symbol):
            return [req]

        holding = self.get_position_holding(req.account,req.full_symbol)

        if lock:
            return holding.convert_order_request_lock(req)
        elif req.exchange == Exchange.SHFE:
            return holding.convert_order_request_shfe(req)
        else:
            return [req]

    @lru_cache()
    def is_convert_required(self, full_symbol: str):
        """
        Check if the contract needs offset convert.
        """
        contract = self.main_engine.get_contract(full_symbol)

        # Only contracts with long-short position mode requires convert
        if not contract.net_position:
            return True
        else:
            return False


class PositionHolding:
    """"""

    def __init__(self, acc:str,full_symbol:str):
        """"""
        self.account = acc
        self.full_symbol = full_symbol

        tmp = full_symbol.split(' ')[0]
        self.exchange = Exchange(tmp)

        self.active_orders = {}         # orderstatus received, server_order_id ->order
        self.active_requests = {}   # requests, reqid ->order

        self.long_pos = 0
        self.long_yd = 0
        self.long_td = 0

        self.short_pos = 0
        self.short_yd = 0
        self.short_td = 0

        self.long_pos_frozen = 0
        self.long_yd_frozen = 0
        self.long_td_frozen = 0

        self.short_pos_frozen = 0
        self.short_yd_frozen = 0
        self.short_td_frozen = 0

    def update_position(self, position: PositionData):
        """"""
        if position.direction == Direction.LONG:
            self.long_pos = position.volume
            self.long_yd = position.yd_volume
            self.long_td = self.long_pos - self.long_yd
        else:
            self.short_pos = position.volume
            self.short_yd = position.yd_volume
            self.short_td = self.short_pos - self.short_yd

    def update_order(self, order: OrderData):
        """"""
        reqid  = str(order.clientID) + '.' + str(order.client_order_id)
        if reqid in self.active_requests:                
            self.active_requests.pop(reqid)
        if order.is_active(): 
            self.active_orders[order.server_order_id] = order
        else:
            if order.server_order_id in self.active_orders:
                self.active_orders.pop(order.server_order_id)
        
        self.calculate_frozen()

    def update_order_request(self, req: OrderRequest):
        """"""
        # gateway_name, orderid = vt_orderid.split(".")
        # order = req.create_order_data(orderid, gateway_name)
        reqid = str(req.clientID) + '.' + str(req.client_order_id)
        self.active_requests[reqid] = req

        self.calculate_frozen()

    def update_trade(self, trade: TradeData):
        """"""
        if trade.direction == Direction.LONG:
            if trade.offset == Offset.OPEN:
                self.long_td += trade.volume
            elif trade.offset == Offset.CLOSETODAY:
                self.short_td -= trade.volume
            elif trade.offset == Offset.CLOSEYESTERDAY:
                self.short_yd -= trade.volume
            elif trade.offset == Offset.CLOSE:
                if trade.exchange == Exchange.SHFE:
                    self.short_yd -= trade.volume
                else:
                    self.short_td -= trade.volume

                    if self.short_td < 0:
                        self.short_yd += self.short_td
                        self.short_td = 0
        else:
            if trade.offset == Offset.OPEN:
                self.short_td += trade.volume
            elif trade.offset == Offset.CLOSETODAY:
                self.long_td -= trade.volume
            elif trade.offset == Offset.CLOSEYESTERDAY:
                self.long_yd -= trade.volume
            elif trade.offset == Offset.CLOSE:
                if trade.exchange == Exchange.SHFE:
                    self.long_yd -= trade.volume
                else:
                    self.long_td -= trade.volume

                    if self.long_td < 0:
                        self.long_yd += self.long_td
                        self.long_td = 0

        self.long_pos = self.long_td + self.long_yd
        self.short_pos = self.short_td + self.short_yd

    def calculate_frozen(self):
        """"""
        self.long_pos_frozen = 0
        self.long_yd_frozen = 0
        self.long_td_frozen = 0

        self.short_pos_frozen = 0
        self.short_yd_frozen = 0
        self.short_td_frozen = 0

        for order in self.active_orders.values():
            # Ignore position open orders
            if order.offset == Offset.OPEN:
                continue

            frozen = order.volume - order.traded

            if order.direction == Direction.LONG:
                if order.offset == Offset.CLOSETODAY:
                    self.short_td_frozen += frozen
                elif order.offset == Offset.CLOSEYESTERDAY:
                    self.short_yd_frozen += frozen
                elif order.offset == Offset.CLOSE:
                    self.short_td_frozen += frozen

                    if self.short_td_frozen > self.short_td:
                        self.short_yd_frozen += (self.short_td_frozen
                                                 - self.short_td)
                        self.short_td_frozen = self.short_td
            elif order.direction == Direction.SHORT:
                if order.offset == Offset.CLOSETODAY:
                    self.long_td_frozen += frozen
                elif order.offset == Offset.CLOSEYESTERDAY:
                    self.long_yd_frozen += frozen
                elif order.offset == Offset.CLOSE:
                    self.long_td_frozen += frozen

                    if self.long_td_frozen > self.short_td:
                        self.long_yd_frozen += (self.long_td_frozen
                                                - self.long_td)
                        self.long_td_frozen = self.long_td

            self.long_pos_frozen = self.long_td_frozen + self.long_yd_frozen
            self.short_pos_frozen = self.short_td_frozen + self.short_yd_frozen

        for order in self.active_requests.values():
            # Ignore position open orders
            if order.offset == Offset.OPEN:
                continue

            frozen = order.volume - order.traded

            if order.direction == Direction.LONG:
                if order.offset == Offset.CLOSETODAY:
                    self.short_td_frozen += frozen
                elif order.offset == Offset.CLOSEYESTERDAY:
                    self.short_yd_frozen += frozen
                elif order.offset == Offset.CLOSE:
                    self.short_td_frozen += frozen

                    if self.short_td_frozen > self.short_td:
                        self.short_yd_frozen += (self.short_td_frozen
                                                 - self.short_td)
                        self.short_td_frozen = self.short_td
            elif order.direction == Direction.SHORT:
                if order.offset == Offset.CLOSETODAY:
                    self.long_td_frozen += frozen
                elif order.offset == Offset.CLOSEYESTERDAY:
                    self.long_yd_frozen += frozen
                elif order.offset == Offset.CLOSE:
                    self.long_td_frozen += frozen

                    if self.long_td_frozen > self.short_td:
                        self.long_yd_frozen += (self.long_td_frozen
                                                - self.long_td)
                        self.long_td_frozen = self.long_td

            self.long_pos_frozen = self.long_td_frozen + self.long_yd_frozen
            self.short_pos_frozen = self.short_td_frozen + self.short_yd_frozen


    def convert_order_request_shfe(self, req: OrderRequest):
        """"""
        if req.offset == Offset.OPEN:
            return [req]

        if req.direction == Direction.LONG:
            pos_available = self.short_pos - self.short_pos_frozen
            td_available = self.short_td - self.short_td_frozen
        else:
            pos_available = self.long_pos - self.long_pos_frozen
            td_available = self.long_td - self.long_td_frozen

        if req.volume > pos_available:
            return [req]
        elif req.volume <= td_available:
            req_td = copy(req)            
            req_td.offset = Offset.CLOSETODAY
            if req_td.api == "CTP":
                req_td.orderfield.CombOffsetFlag = '3'
            return [req_td]
        else:
            req_list = []

            if td_available > 0:
                req_td = copy(req)
                req_td.offset = Offset.CLOSETODAY             
                req_td.volume = td_available
                if req_td.api == "CTP":
                    req_td.orderfield.CombOffsetFlag = '3' 
                    req_td.orderfield.VolumeTotalOriginal = td_available            
                req_list.append(req_td)

            req_yd = copy(req)
            req_yd.offset = Offset.CLOSEYESTERDAY
            req_yd.volume = req.volume - td_available
            if req_yd.api == "CTP":
                req_yd.orderfield.CombOffsetFlag = '4' 
                req_yd.orderfield.VolumeTotalOriginal = req_yd.volume               
            req_list.append(req_yd)

            return req_list

    def convert_order_request_lock(self, req: OrderRequest):
        """"""
        if req.direction == Direction.LONG:
            td_volume = self.short_td
            yd_available = self.short_yd - self.short_yd_frozen
        else:
            td_volume = self.long_td
            yd_available = self.long_yd - self.long_yd_frozen

        # If there is td_volume, we can only lock position
        if td_volume:
            req_open = copy(req)
            req_open.offset = Offset.OPEN
            return [req_open]
        # If no td_volume, we close opposite yd position first
        # then open new position
        else:
            open_volume = max(0, yd_available - req.volume)
            req_list = []

            if yd_available:
                req_yd = copy(req)
                if self.exchange == Exchange.SHFE:
                    req_yd.offset = Offset.CLOSEYESTERDAY
                    if req_yd.api == "CTP":
                        req_yd.orderfield.CombOffsetFlag = '4' 
                else:
                    req_yd.offset = Offset.CLOSE
                    if req_yd.api == "CTP":
                        req_yd.orderfield.CombOffsetFlag = '2'  
                req_list.append(req_yd)

            if open_volume:
                req_open = copy(req)
                req_open.offset = Offset.OPEN
                req_open.volume = open_volume
                if req_open.api == "CTP":
                    req_open.orderfield.CombOffsetFlag = '1' 
                    req_open.orderfield.VolumeTotalOriginal = req_open.volume 
                req_list.append(req_open)

            return req_list
