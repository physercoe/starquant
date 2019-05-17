#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..common.datastruct import AccountData

class AccountManager(object):
    def __init__(self, config_server):
        self._config_server = config_server
        self._account_dict = {}            # account id ==> account
        self.reset()

    def reset(self):
        self._account_dict.clear()
        # initialize accounts from server_config.yaml
        for a in self._config_server['gateway']:
            account = AccountData()
            account.accountid = self._config_server[a]['userid']
            account.gateway_name = str(a)
            self._account_dict[account.accountid] = account

    def on_account(self, account_event):
        if account_event.accountid in self._account_dict:
            self._account_dict[account_event.accountid].yd_balance = account_event.yd_balance
            self._account_dict[account_event.accountid].balance = account_event.balance
            self._account_dict[account_event.accountid].available = account_event.available
            self._account_dict[account_event.accountid].frozen = account_event.frozen
            self._account_dict[account_event.accountid].netliquid = account_event.netliquid
            self._account_dict[account_event.accountid].commission = account_event.commission
            self._account_dict[account_event.accountid].margin = account_event.margin
            self._account_dict[account_event.accountid].closed_pnl = account_event.closed_pnl
            self._account_dict[account_event.accountid].open_pnl = account_event.open_pnl
            self._account_dict[account_event.accountid].timestamp = account_event.timestamp
        else:
            self._account_dict[account_event.accountid] = account_event