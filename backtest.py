#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import sys,getopt
# import os
# import signal
# from multiprocessing import Process

import sys
import json
import csv
from pathlib import Path
import traceback
from datetime import datetime

import numpy as np
import yaml

from pystarquant.engine.backtest_engine import BacktestingEngine, BacktestingProEngine
from pystarquant.gui.ui_bt_setting import Backtester
from pystarquant.common.datastruct import ContractData
from pystarquant.common.constant import (
    Exchange, Interval, Product, PRODUCT_CTP2VT, OPTIONTYPE_CTP2VT,PRODUCT_SQ2VT,PRODUCT_VT2SQ,
)


colheaders = np.array(
    [
        ('成交时间', 'datetime'),
        ('合约全称', 'full_symbol'),
        ('买卖方向', 'direction'),
        ('开平方向', 'offset'),
        ('成交价格', 'price'),
        ('成交数量', 'volume'),
        ('成交金额', 'turnover'),
        ('手续费用', 'commission'),
        ('滑点费用', 'slippage'),
        ('多仓数量', 'long_pos'),
        ('多仓开仓价格', 'long_price'),
        ('多仓平仓盈亏', 'long_pnl'),
        ('空仓数量', 'short_pos'),
        ('空仓开仓价格', 'short_price'),
        ('空仓平仓盈亏', 'short_pnl'),
        ('净盈亏', 'net_pnl'),
    ]
)


def save_trade_csv(trades, path:str = "Result/bttrades.csv"):
    with open(path, "w") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(colheaders[:, 1])            
        for trade in trades:
            row_data = []
            for icol, col in enumerate(colheaders[:, 1]):
                if col == 'direction':
                    val = trade.direction.value
                elif col == 'offset':
                    val = trade.offset.value
                elif col == 'net_pnl':
                    val = trade.short_pnl + trade.long_pnl - trade.slippage - trade.commission
                else:
                    val = trade.__getattribute__(col)

                if isinstance(val, float):
                    s_val = '%.2f' % val
                elif isinstance(val, datetime):
                    s_val = val.strftime('%Y.%m.%d %H:%M:%S')
                elif isinstance(val, (int, str)):
                    s_val = str(val)
                row_data.append(s_val)
            writer.writerow(row_data)




configfile = 'backtest.json'
if len(sys.argv) > 1:
    configfile = sys.argv[1]
btsetting = {}
with open(configfile, mode='r') as f:
    btsetting = json.load(f)

backtester = Backtester()
backtester.write_log = lambda x: print(datetime.now(),x)
backtester.init_engine()

try:
    if btsetting['mode'] == 'lite':
        backtester.run_backtesting(
            class_name=btsetting["strategy"],
            full_symbol=btsetting["full_symbol"],
            start=datetime.strptime(btsetting["start"],'%Y-%m-%d'),
            end=datetime.strptime(btsetting["end"],'%Y-%m-%d'),
            rate=float(btsetting["rate"]),
            slippage=float(btsetting["slippage"]),
            size=float(btsetting["size"]),
            pricetick=float(btsetting["pricetick"]),
            capital=float(btsetting["capital"]),
            setting=btsetting["parameter"],
            datasource=btsetting["datasource"],
            using_cursor=bool(btsetting["usingcursor"]),
            dbcollection=btsetting["dbcollection"],
            dbtype=btsetting["dbtype"],
            interval=btsetting["interval"],
        )
   
    else:
        btcontracts = {}

        # contractfile = Path.cwd().joinpath("etc/ctpcontract.yaml")
        # with open(contractfile, encoding='utf8') as fc:
        #     contracts = yaml.load(fc, Loader=yaml.SafeLoader)
        # print('loading contracts, total number:', len(contracts))
        # for sym, data in contracts.items():
        #     contract = ContractData(
        #         symbol=data["symbol"],
        #         exchange=Exchange(data["exchange"]),
        #         name=data["name"],
        #         product=PRODUCT_CTP2VT[str(data["product"])],
        #         size=data["size"],
        #         pricetick=data["pricetick"],
        #         net_position=True if str(
        #             data["positiontype"]) == '1' else False,
        #         long_margin_ratio=data["long_margin_ratio"],
        #         short_margin_ratio=data["short_margin_ratio"],
        #         full_symbol=data["full_symbol"]
        #     )
        #     # For option only
        #     if contract.product == Product.OPTION:
        #         contract.option_underlying = data["option_underlying"],
        #         contract.option_type = OPTIONTYPE_CTP2VT.get(
        #             str(data["option_type"]), None),
        #         contract.option_strike = data["option_strike"],
        #         contract.option_expiry = datetime.strptime(
        #             str(data["option_expiry"]), "%Y%m%d"),
        #     btcontracts[contract.full_symbol] = contract
        contractfile = Path.cwd().joinpath("etc/btcontract_stock.csv")
        with open(contractfile, "r") as f:
            reader = csv.DictReader(f, lineterminator="\n")
            for item in reader:
                contract = ContractData(
                    symbol=str(item["symbol"]),
                    exchange=Exchange(item["exchange"]),
                    name=str(item["name"]),
                    product=PRODUCT_SQ2VT[str(item["product"])],
                    size=float(item["size"]),
                    pricetick=float(item["pricetick"]),
                    min_volume=float(item["min_volume"]),
                    net_position=bool(int(item["net_position"])),
                    full_symbol=str(item["full_symbol"]),
                    long_margin_ratio=float(item["long_margin"]),
                    short_margin_ratio=float(item["short_margin"]),
                    slippage=float(item["slippage"]), 
                    rate=float(item["rate"])                 
                )
                btcontracts[contract.full_symbol] = contract

        backtester.run_backtesting_pro(
            class_name=btsetting["strategy"],
            full_symbol=btsetting["full_symbol"],

            start=datetime.strptime(btsetting["start"],'%Y-%m-%d'),
            end=datetime.strptime(btsetting["end"],'%Y-%m-%d'),
            capital=float(btsetting["capital"]),
            contracts=btcontracts,
            setting=btsetting["parameter"],
            datasource=btsetting["datasource"],
            usingcursor=bool(btsetting["usingcursor"]),
            dbcollection=btsetting["dbcollection"],
            dbtype=btsetting["dbtype"],            
            interval=btsetting["interval"],           
        ) 
     
    result_trades = backtester.get_result_trades()
    resultspath = f"Result/{btsetting['strategy']}_{btsetting['full_symbol']}_{btsetting['interval']}_{btsetting['start']}_{btsetting['end']}.csv"
    save_trade_csv(result_trades,resultspath)

    statistics = {}
    tmp = backtester.get_result_statistics()
    statistics.update(tmp)
    for key,value in statistics.items():
        print(key,' : ', value)


except :
    msg = f"回测异常:\n{traceback.format_exc()}"
    print(msg)


