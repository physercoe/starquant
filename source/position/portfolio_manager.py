#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .position import Position

from ..order.order_flag import OrderFlag
from .margin import marginrate
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



