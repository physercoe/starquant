#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .risk_manager_base import RiskManagerBase

class PassThroughRiskManager(RiskManagerBase):
    def __init__(self):
        self._orderperseconds = 0
        self._queryperseconds = 0
    def reset(self):
        self._orderperseconds = 0
        self._queryperseconds = 0
    def order_in_compliance(self, original_order):
        """
        Pass through the order without constraints
        """
        return original_order
    def passorder(self):
        self._orderperseconds =self._orderperseconds +1
        if (self._orderperseconds > 1):
            print('order flow rate limit reached ')
            return False
        return True
    def passquery(self):
        self._queryperseconds =self._queryperseconds +1
        if (self._queryperseconds > 1):
            print('query flow rate limit reached ')
            return False
        return True