#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import copy
from functools import lru_cache
from typing import Union

from ..api.ctp_constant import (
    THOST_FTDC_OF_Open, THOST_FTDC_OF_Close, THOST_FTDC_OF_CloseToday, THOST_FTDC_OF_CloseYesterday
)
from ..common.constant import Exchange, Direction, Offset
from ..common.datastruct import (
    PositionData, TradeData, OrderData, OrderRequest, ContractData, BacktestTradeData
)
from ..engine.iengine import BaseEngine


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

        holding = self.get_position_holding(
            position.account, position.full_symbol)
        holding.update_position(position)

    def update_trade(self, trade: TradeData):
        """"""
        if not self.is_convert_required(trade.full_symbol):
            return

        holding = self.get_position_holding(trade.account, trade.full_symbol)
        holding.update_trade(trade)

    def update_order(self, order: OrderData):
        """"""
        if not self.is_convert_required(order.full_symbol):
            return

        holding = self.get_position_holding(order.account, order.full_symbol)
        holding.update_order(order)

    def update_order_request(self, req: OrderRequest):
        """"""
        if not self.is_convert_required(req.full_symbol):
            return

        holding = self.get_position_holding(req.account, req.full_symbol)
        holding.update_order_request(req)

    def get_position_holding(self, acc: str, full_symbol: str):
        """"""
        holdingid = acc + "." + full_symbol
        holding = self.holdings.get(holdingid, None)
        if not holding:
            contract = self.main_engine.get_contract(full_symbol)
            holding = PositionHolding(acc, contract)
            self.holdings[holdingid] = holding
        return holding

    def convert_order_request(self, req: OrderRequest, lock: bool):
        """"""
        if not self.is_convert_required(req.full_symbol):
            # print('--------------------not convert------------------')
            return [req]

        holding = self.get_position_holding(req.account, req.full_symbol)

        if lock:
            return holding.convert_order_request_lock(req)
        elif req.exchange == Exchange.SHFE:
            return holding.convert_order_request_shfe(req)
        else:
            # print('--------------------not convert------------------')
            return [req]

    @lru_cache()
    def is_convert_required(self, full_symbol: str):
        """
        Check if the contract needs offset convert.
        """
        contract = self.main_engine.get_contract(full_symbol)
        if not contract:
            return False
        # Only contracts with long-short position mode requires convert
        if not contract.net_position:
            return True
        else:
            return False


class PositionHolding:
    """"""

    def __init__(self, acc: str, contract: ContractData):
        """"""
        self.account = acc
        self.full_symbol = contract.full_symbol
        self.exchange = contract.exchange
        self.size = contract.size
        self.active_orders = {}         # orderstatus received, server_order_id ->order
        self.active_requests = {}   # requests, reqid ->order

        self.long_pos = 0
        self.long_yd = 0
        self.long_td = 0
        self.long_price = 0

        self.short_pos = 0
        self.short_yd = 0
        self.short_td = 0
        self.short_price = 0

        self.long_pos_frozen = 0
        self.long_yd_frozen = 0
        self.long_td_frozen = 0

        self.short_pos_frozen = 0
        self.short_yd_frozen = 0
        self.short_td_frozen = 0

        self.last_price = 0

    def update_position(self, position: PositionData):
        """"""
        if position.direction == Direction.LONG:
            self.long_pos = position.volume
            self.long_yd = position.yd_volume
            self.long_td = self.long_pos - self.long_yd
            self.long_price = position.price
        else:
            self.short_pos = position.volume
            self.short_yd = position.yd_volume
            self.short_td = self.short_pos - self.short_yd
            self.short_price = position.price

    def update_order(self, order: OrderData):
        """"""
        reqid = str(order.clientID) + '.' + str(order.client_order_id)
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

    def update_trade(self, trade: Union[TradeData, BacktestTradeData]):
        """"""
        old_long_pos = self.long_pos
        old_short_pos = self.short_pos
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
        if self.long_pos:
            self.long_price = (old_long_pos*self.long_price +
                               (self.long_pos-old_long_pos)*trade.price)/self.long_pos
        else:
            pass
            #self.long_price = 0.0
        if self.short_pos:
            self.short_price = (old_short_pos*self.short_price +
                                (self.short_pos-old_short_pos)*trade.price)/self.short_pos
        else:
            pass
            #self.short_price = 0.0

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

                    if self.long_td_frozen > self.long_td:
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
        # print('-------------posholding:',pos_available,td_available)
        if req.volume > pos_available:
            return [req]
        elif req.volume <= td_available:
            req_td = copy(req)
            req_td.offset = Offset.CLOSETODAY
            if req_td.api == "CTP.TD":
                req_td.orderfield.CombOffsetFlag = THOST_FTDC_OF_CloseToday
            return [req_td]
        else:
            req_list = []

            if td_available > 0:
                req_td = copy(req)
                req_td.offset = Offset.CLOSETODAY
                req_td.volume = td_available
                if req_td.api == "CTP.TD":
                    req_td.orderfield.CombOffsetFlag = THOST_FTDC_OF_CloseToday
                    req_td.orderfield.VolumeTotalOriginal = td_available
                req_list.append(req_td)

            req_yd = copy(req)
            req_yd.offset = Offset.CLOSEYESTERDAY
            req_yd.volume = req.volume - td_available
            if req_yd.api == "CTP.TD":
                req_yd.orderfield.CombOffsetFlag = THOST_FTDC_OF_CloseYesterday
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
                    if req_yd.api == "CTP.TD":
                        req_yd.orderfield.CombOffsetFlag = THOST_FTDC_OF_CloseYesterday
                else:
                    req_yd.offset = Offset.CLOSE
                    if req_yd.api == "CTP.TD":
                        req_yd.orderfield.CombOffsetFlag = THOST_FTDC_OF_Close
                req_list.append(req_yd)

            if open_volume:
                req_open = copy(req)
                req_open.offset = Offset.OPEN
                req_open.volume = open_volume
                if req_open.api == "CTP.TD":
                    req_open.orderfield.CombOffsetFlag = THOST_FTDC_OF_Open
                    req_open.orderfield.VolumeTotalOriginal = req_open.volume
                req_list.append(req_open)

            return req_list
