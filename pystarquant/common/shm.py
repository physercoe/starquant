#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ctypes import ( c_char, c_double, c_int, c_int8, c_uint8, c_int16, 
c_int32, c_uint32, c_int64, c_uint64,Structure, c_ubyte, c_bool)

import ctypes
import datetime

class SOURCE:
    CTP = 1

class EXCHANGE:
    SSE = 'SSE' #上海证券交易所
    SZE = 'SZE' #深圳证券交易所
    CFFEX = 'CFFEX' #中国金融期货交易所
    SHFE = 'SHFE' #上海期货交易所
    DCE = 'DCE' #大连商品交易所
    CZCE = 'CZCE' #郑州商品交易所

class EXCHANGE_ID:
    SSE = 1 #上海证券交易所
    SZE = 2 #深圳证券交易所
    CFFEX = 11 #中国金融期货交易所
    SHFE = 12 #上海期货交易所
    DCE = 13 #大连商品交易所
    CZCE = 14 #郑州商品交易所

class MsgTypes:
    MD = 101
    L2_MD = 102
    L2_INDEX = 103
    L2_ORDER = 104
    L2_TRADE = 105
    BAR_MD = 110
    QRY_POS = 201
    RSP_POS = 202
    ORDER = 204
    RTN_ORDER = 205
    RTN_TRADE = 206
    ORDER_ACTION = 207
    QRY_ACCOUNT = 208
    RSP_ACCOUNT = 209

###################################
# LfActionFlagType: 报单操作标志
###################################
class LfActionFlagType:
    Delete = '0' #删除
    Suspend = '1' #挂起
    Active = '2' #激活
    Modify = '3' #修改

###################################
# LfContingentConditionType: 触发条件
###################################
class LfContingentConditionType:
    Immediately = '1' #立即
    Touch = '2' #止损
    TouchProfit = '3' #止赢
    ParkedOrder = '4' #预埋单
    LastPriceGreaterThanStopPrice = '5' #最新价大于条件价
    LastPriceGreaterEqualStopPrice = '6' #最新价大于等于条件价
    LastPriceLesserThanStopPrice = '7' #最新价小于条件价
    LastPriceLesserEqualStopPrice = '8' #最新价小于等于条件价
    AskPriceGreaterThanStopPrice = '9' #卖一价大于条件价
    AskPriceGreaterEqualStopPrice = 'A' #卖一价大于等于条件价
    AskPriceLesserThanStopPrice = 'B' #卖一价小于条件价
    AskPriceLesserEqualStopPrice = 'C' #卖一价小于等于条件价
    BidPriceGreaterThanStopPrice = 'D' #买一价大于条件价
    BidPriceGreaterEqualStopPrice = 'E' #买一价大于等于条件价
    BidPriceLesserThanStopPrice = 'F' #买一价小于条件价
    BidPriceLesserEqualStopPrice = 'H' #买一价小于等于条件价

###################################
# LfDirectionType: 买卖方向
###################################
class LfDirectionType:
    Buy = '0' #买
    Sell = '1' #卖

###################################
# LfForceCloseReasonType: 强平原因
###################################
class LfForceCloseReasonType:
    NotForceClose = '0' #非强平
    LackDeposit = '1' #资金不足
    ClientOverPositionLimit = '2' #客户超仓
    MemberOverPositionLimit = '3' #会员超仓
    NotMultiple = '4' #持仓非整数倍
    Violation = '5' #违规
    Other = '6' #其它
    PersonDeliv = '7' #自然人临近交割

###################################
# LfHedgeFlagType: 投机套保标志
###################################
class LfHedgeFlagType:
    Speculation = '1' #投机
    Argitrage = '2' #套利
    Hedge = '3' #套保
    MarketMaker = '4' #做市商(femas)
    AllValue = '9' #匹配所有的值(femas)

###################################
# LfOffsetFlagType: 开平标志
###################################
class LfOffsetFlagType:
    Open = '0' #开仓
    Close = '1' #平仓
    ForceClose = '2' #强平
    CloseToday = '3' #平今
    CloseYesterday = '4' #平昨
    ForceOff = '5' #强减
    LocalForceClose = '6' #本地强平
    Non = 'N' #不分开平

###################################
# LfOrderPriceTypeType: 报单价格条件
###################################
class LfOrderPriceTypeType:
    AnyPrice = '1' #任意价
    LimitPrice = '2' #限价
    BestPrice = '3' #最优价

###################################
# LfOrderStatusType: 报单状态
###################################
class LfOrderStatusType:
    AllTraded = '0' #全部成交（最终状态）
    PartTradedQueueing = '1' #部分成交还在队列中
    PartTradedNotQueueing = '2' #部分成交不在队列中（部成部撤， 最终状态）
    NoTradeQueueing = '3' #未成交还在队列中
    NoTradeNotQueueing = '4' #未成交不在队列中（被拒绝，最终状态）
    Canceled = '5' #撤单
    AcceptedNoReply = '6' #订单已报入交易所未应答
    Unknown = 'a' #未知
    NotTouched = 'b' #尚未触发
    Touched = 'c' #已触发
    Error = 'd' #废单错误（最终状态）
    OrderInserted = 'i' #订单已写入
    OrderAccepted = 'j' #前置已接受

###################################
# LfPosiDirectionType: 持仓多空方向
###################################
class LfPosiDirectionType:
    Net = '1' #净
    Long = '2' #多头
    Short = '3' #空头

###################################
# LfPositionDateType: 持仓日期
###################################
class LfPositionDateType:
    Today = '1' #今日持仓
    History = '2' #历史持仓
    Both = '3' #两种持仓

###################################
# LfTimeConditionType: 有效期类型
###################################
class LfTimeConditionType:
    IOC = '1' #立即完成，否则撤销
    GFS = '2' #本节有效
    GFD = '3' #当日有效
    GTD = '4' #指定日期前有效
    GTC = '5' #撤销前有效
    GFA = '6' #集合竞价有效
    FAK = 'A' #FAK或IOC(yisheng)
    FOK = 'O' #FOK(yisheng)

###################################
# LfVolumeConditionType: 成交量类型
###################################
class LfVolumeConditionType:
    AV = '1' #任何数量
    MV = '2' #最小数量
    CV = '3' #全部数量

###################################
# LfYsHedgeFlagType: 易盛投机保值类型
###################################
class LfYsHedgeFlagType:
    YsB = 'B' #保值
    YsL = 'L' #套利
    YsNon = 'N' #无
    YsT = 'T' #投机

###################################
# LfYsOrderStateType: 易盛委托状态类型
###################################
class LfYsOrderStateType:
    YsSubmit = '0' #终端提交
    YsAccept = '1' #已受理
    YsTriggering = '2' #策略待触发
    YsExctriggering = '3' #交易所待触发
    YsQueued = '4' #已排队
    YsPartFinished = '5' #部分成交
    YsFinished = '6' #完全成交
    YsCanceling = '7' #待撤消(排队临时状态)
    YsModifying = '8' #待修改(排队临时状态)
    YsCanceled = '9' #完全撤单
    YsLeftDeleted = 'A' #已撤余单
    YsFail = 'B' #指令失败
    YsDeleted = 'C' #策略删除
    YsSuppended = 'D' #已挂起
    YsDeletedForExpire = 'E' #到期删除
    YsEffect = 'F' #已生效——询价成功
    YsApply = 'G' #已申请——行权、弃权、套利等申请成功

###################################
# LfYsOrderTypeType: 易盛委托类型
###################################
class LfYsOrderTypeType:
    YsMarket = '1' #市价
    YsLimit = '2' #限价

###################################
# LfYsPositionEffectType: 易盛开平类型
###################################
class LfYsPositionEffectType:
    YsClose = 'C' #平仓
    YsNon = 'N' #不分开平
    YsOpen = 'O' #开仓
    YsCloseToday = 'T' #平当日

###################################
# LfYsSideTypeType: 易盛买卖类型
###################################
class LfYsSideTypeType:
    YsAll = 'A' #双边
    YsBuy = 'B' #买入
    YsNon = 'N' #无
    YsSell = 'S' #卖出

###################################
# LfYsTimeConditionType: 易盛委托有效类型
###################################
class LfYsTimeConditionType:
    YsGFD = '0' #当日有效
    YsGTC = '1' #撤销前有效
    YsGTD = '2' #指定日期前有效
    YsFAK = '3' #FAK或IOC
    YsFOK = '4' #FOK

LfActionFlagTypeMap = {
    '0': 'Delete',
    '1': 'Suspend',
    '2': 'Active',
    '3': 'Modify',
}

LfContingentConditionTypeMap = {
    '1': 'Immediately',
    '2': 'Touch',
    '3': 'TouchProfit',
    '4': 'ParkedOrder',
    '5': 'LastPriceGreaterThanStopPrice',
    '6': 'LastPriceGreaterEqualStopPrice',
    '7': 'LastPriceLesserThanStopPrice',
    '8': 'LastPriceLesserEqualStopPrice',
    '9': 'AskPriceGreaterThanStopPrice',
    'A': 'AskPriceGreaterEqualStopPrice',
    'B': 'AskPriceLesserThanStopPrice',
    'C': 'AskPriceLesserEqualStopPrice',
    'D': 'BidPriceGreaterThanStopPrice',
    'E': 'BidPriceGreaterEqualStopPrice',
    'F': 'BidPriceLesserThanStopPrice',
    'H': 'BidPriceLesserEqualStopPrice',
}

LfDirectionTypeMap = {
    '0': 'Buy',
    '1': 'Sell',
}

LfForceCloseReasonTypeMap = {
    '0': 'NotForceClose',
    '1': 'LackDeposit',
    '2': 'ClientOverPositionLimit',
    '3': 'MemberOverPositionLimit',
    '4': 'NotMultiple',
    '5': 'Violation',
    '6': 'Other',
    '7': 'PersonDeliv',
}

LfHedgeFlagTypeMap = {
    '1': 'Speculation',
    '2': 'Argitrage',
    '3': 'Hedge',
    '4': 'MarketMaker',
    '9': 'AllValue',
}

LfOffsetFlagTypeMap = {
    '0': 'Open',
    '1': 'Close',
    '2': 'ForceClose',
    '3': 'CloseToday',
    '4': 'CloseYesterday',
    '5': 'ForceOff',
    '6': 'LocalForceClose',
    'N': 'Non',
}

LfOrderPriceTypeTypeMap = {
    '1': 'AnyPrice',
    '2': 'LimitPrice',
    '3': 'BestPrice',
}

LfOrderStatusTypeMap = {
    '0': 'AllTraded',
    '1': 'PartTradedQueueing',
    '2': 'PartTradedNotQueueing',
    '3': 'NoTradeQueueing',
    '4': 'NoTradeNotQueueing',
    '5': 'Canceled',
    '6': 'AcceptedNoReply',
    'a': 'Unknown',
    'b': 'NotTouched',
    'c': 'Touched',
    'd': 'Error',
    'i': 'OrderInserted',
    'j': 'OrderAccepted',
}

LfPosiDirectionTypeMap = {
    '1': 'Net',
    '2': 'Long',
    '3': 'Short',
}

LfPositionDateTypeMap = {
    '1': 'Today',
    '2': 'History',
    '3': 'Both',
}

LfTimeConditionTypeMap = {
    '1': 'IOC',
    '2': 'GFS',
    '3': 'GFD',
    '4': 'GTD',
    '5': 'GTC',
    '6': 'GFA',
    'A': 'FAK',
    'O': 'FOK',
}

LfVolumeConditionTypeMap = {
    '1': 'AV',
    '2': 'MV',
    '3': 'CV',
}

LfYsHedgeFlagTypeMap = {
    'B': 'YsB',
    'L': 'YsL',
    'N': 'YsNon',
    'T': 'YsT',
}

LfYsOrderStateTypeMap = {
    '0': 'YsSubmit',
    '1': 'YsAccept',
    '2': 'YsTriggering',
    '3': 'YsExctriggering',
    '4': 'YsQueued',
    '5': 'YsPartFinished',
    '6': 'YsFinished',
    '7': 'YsCanceling',
    '8': 'YsModifying',
    '9': 'YsCanceled',
    'A': 'YsLeftDeleted',
    'B': 'YsFail',
    'C': 'YsDeleted',
    'D': 'YsSuppended',
    'E': 'YsDeletedForExpire',
    'F': 'YsEffect',
    'G': 'YsApply',
}

LfYsOrderTypeTypeMap = {
    '1': 'YsMarket',
    '2': 'YsLimit',
}

LfYsPositionEffectTypeMap = {
    'C': 'YsClose',
    'N': 'YsNon',
    'O': 'YsOpen',
    'T': 'YsCloseToday',
}

LfYsSideTypeTypeMap = {
    'A': 'YsAll',
    'B': 'YsBuy',
    'N': 'YsNon',
    'S': 'YsSell',
}

LfYsTimeConditionTypeMap = {
    '0': 'YsGFD',
    '1': 'YsGTC',
    '2': 'YsGTD',
    '3': 'YsFAK',
    '4': 'YsFOK',
}


class XSPEED_L1_ANLIANG(Structure):
	_fields_ = [
		("exchangeID", c_char * 3),
		("validFlag", c_uint8),
		("instrumentID", c_char * 7),
		("updateTime", c_char * 9),
		("updateMillisec", c_int),
		("lastPrice", c_double),
		("matchAmount", c_int),
		("matchTotalMoney", c_double),
		("openInterest", c_double),
		("buyPrice1", c_double),
		("buyAmount1", c_int),
		("sellPrice1", c_double),
		("sellAmount1", c_int),
		]
	_pack_ = 1

class XSPEED_L2_ANLIANG(Structure):
	_fields_ = [
		("packetLen", c_int),
		("versionNo", c_ubyte),
		("updateTime", c_int),
		("exchangeID", c_char * 3),
		("instrumentID", c_char * 30),
		("stopFlag", c_bool),
		("preSettlementPrice", c_double),
		("settlementPrice", c_double),
		("averageMatchPrice", c_double),
		("yesterdayClosePrice", c_double),
		("todayClosePrice", c_double),
		("todayOpenPrice", c_double),
		("yesterdayPositionAmount", c_int),
		("positionAmount", c_int),
		("lastPrice", c_double),
		("matchAmount", c_int),
		("matchTotalMoney", c_double),
		("highestPrice", c_double),
		("lowestPrice", c_double),
		("upperPrice", c_double),
		("lowerPrice", c_double),
		("yesterdayImagineRealDegree", c_double),
		("imagineRealDegree", c_double),
		("buyPrice1", c_double),
		("sellPrice1", c_double),
		("buyAmount1", c_int),
		("sellAmount1", c_int),
		("buyPrice2", c_double),
		("sellPrice2", c_double),
		("buyAmount2", c_int),
		("sellAmount2", c_int),
		("buyPrice3", c_double),
		("sellPrice3", c_double),
		("buyAmount3", c_int),
		("sellAmount3", c_int),
		("buyPrice4", c_double),
		("sellPrice4", c_double),
		("buyAmount4", c_int),
		("sellAmount4", c_int),
		("buyPrice5", c_double),
		("sellPrice5", c_double),
		("buyAmount5", c_int),
		("sellAmount5", c_int),
		]
	_pack_ = 1

class XSPEED_L1(Structure):
	_fields_ = [
		("length", c_int32),
		("versionNo", c_ubyte),
		("updateTime", c_int32),
		("exchangeID", c_char * 3),
		("symbol", c_char * 31),
		("lastClearPrice", c_double),
		("clearPrice", c_double),
		("avgPrice", c_double),
		("lastClose", c_double),
		("todayClosePrice", c_double),
		("openPrice", c_double),
		("yesterdayPositionAmount", c_int),
		("positionAmount", c_int),
		("lastPrice", c_double),
		("matchAmount", c_int),
		("matchTotalMoney", c_double),
		("riseLimit", c_double),
		("fallLimit", c_double),
		("highPrice", c_double),
		("lowPrice", c_double),
		("yesterdayImagineRealDegree", c_double),
		("imagineRealDegree", c_double),
		("bestBidPrice", c_double),
		("bestAskPrice", c_double),
		("bestBidQty", c_int32),
		("bestAskQty", c_int32),
		]
	_pack_ = 1

class XSPEED_L2(Structure):
	_fields_ = [
		("type", c_int8),
		("__0_1", c_uint8 * 3),
		("length", c_int16),
		("__0_2", c_uint8 * 2),
		("date", c_char * 9),
		("symbol", c_char * 27),
		("symbolChineseName", c_char * 44),
		("lastPrice", c_double),
		("highPrice", c_double),
		("lowPrice", c_double),
		("lastMatchQty", c_int32),
		("matchTotQty", c_int32),
		("turnOver", c_double),
		("lastOpenInterest", c_int32),
		("openInterest", c_int32),
		("interestChange", c_int32),
		("clearPrice", c_double),
		("lifeLow", c_double),
		("lifeHigh", c_double),
		("riseLimit", c_double),
		("fallLimit", c_double),
		("lastClearPrice", c_double),
		("lastClose", c_double),
		("bestBidPrice", c_double),
		("bestBidQty", c_int16),
		("__0_3", c_uint8 * 6),
		("bestAskPrice", c_double),
		("bestAskQty", c_int16),
		("__0_4", c_uint8 * 6),
		("avgPrice", c_double),
		("time", c_char * 12),
		("__0_5", c_uint8 * 4),
		("openPrice", c_double),
		("closePrice", c_double),
		("__0_6", c_uint8 * 4),
		("bidPrice1", c_double),
		("bidVolume1", c_int16),
		("__b0_1", c_int16),
		("bidImplyQty1", c_int16),
		("__b1__", c_uint8 * 18),
		("bidPrice2", c_double),
		("bidVolume2", c_int16),
		("__b0_2", c_int16),
		("bidImplyQty2", c_int16),
		("__b2__", c_uint8 * 18),
		("bidPrice3", c_double),
		("bidVolume3", c_int16),
		("__b0_3", c_int16),
		("bidImplyQty3", c_int16),
		("__b3__", c_uint8 * 18),
		("bidPrice4", c_double),
		("bidVolume4", c_int16),
		("__b0_4", c_int16),
		("bidImplyQty4", c_int16),
		("__b4__", c_uint8 * 18),
		("bidPrice5", c_double),
		("bidVolume5", c_int16),
		("__b0_5", c_int16),
		("bidImplyQty5", c_int16),
		("__b5__", c_uint8 * 18),
		("askPrice1", c_double),
		("askVolume1", c_int16),
		("__a0_1", c_int16),
		("askImplyQty1", c_int16),
		("__a1__", c_uint8 * 18),
		("askPrice2", c_double),
		("askVolume2", c_int16),
		("__a0_2", c_int16),
		("askImplyQty2", c_int16),
		("__a2__", c_uint8 * 18),
		("askPrice3", c_double),
		("askVolume3", c_int16),
		("__a0_3", c_int16),
		("askImplyQty3", c_int16),
		("__a3__", c_uint8 * 18),
		("askPrice4", c_double),
		("askVolume4", c_int16),
		("__a0_4", c_int16),
		("askImplyQty4", c_int16),
		("__a4__", c_uint8 * 18),
		("askPrice5", c_double),
		("askVolume5", c_int16),
		("__a0_5", c_int16),
		("askImplyQty5", c_int16),
		("__a5__", c_uint8 * 18),
		("trailer", c_uint8 * 80),
		]
	_pack_ = 1

class XSPEED_L2_ORDER10(Structure):
	_fields_ = [
		("type", c_int8),
		("symbol", c_char * 27),
		("symbol_chinese_name", c_char * 56),
		("best_bid_price", c_double),
		("bid_qty_1", c_int32),
		("bid_qty_2", c_int32),
		("bid_qty_3", c_int32),
		("bid_qty_4", c_int32),
		("bid_qty_5", c_int32),
		("bid_qty_6", c_int32),
		("bid_qty_7", c_int32),
		("bid_qty_8", c_int32),
		("bid_qty_9", c_int32),
		("bid_qty_10", c_int32),
		("best_ask_price", c_double),
		("ask_qty_1", c_int32),
		("ask_qty_2", c_int32),
		("ask_qty_3", c_int32),
		("ask_qty_4", c_int32),
		("ask_qty_5", c_int32),
		("ask_qty_6", c_int32),
		("ask_qty_7", c_int32),
		("ask_qty_8", c_int32),
		("ask_qty_9", c_int32),
		("ask_qty_10", c_int32),
		("time", c_char * 16),
		("trailer", c_uint8 * 4),
		]
	_pack_ = 1

class XSPEED_L2_MATCH_BY_PRICE(Structure):
	_fields_ = [
		("type", c_int8),
		("__0_1", c_uint8 * 3),
		("symbol", c_char * 27),
		("__0_2", c_uint8 * 57),
		("match_price1", c_double),
		("buy_open_qty1", c_int),
		("buy_close_qty1", c_int),
		("sell_open_qty1", c_int),
		("sell_close_qty1", c_int),
		("match_price2", c_double),
		("buy_open_qty2", c_int),
		("buy_close_qty2", c_int),
		("sell_open_qty2", c_int),
		("sell_close_qty2", c_int),
		("match_price3", c_double),
		("buy_open_qty3", c_int),
		("buy_close_qty3", c_int),
		("sell_open_qty3", c_int),
		("sell_close_qty3", c_int),
		("match_price4", c_double),
		("buy_open_qty4", c_int),
		("buy_close_qty4", c_int),
		("sell_open_qty4", c_int),
		("sell_close_qty4", c_int),
		("match_price5", c_double),
		("buy_open_qty5", c_int),
		("buy_close_qty5", c_int),
		("sell_open_qty5", c_int),
		("sell_close_qty5", c_int),
		("trailer", c_uint8 * 4),
		]
	_pack_ = 1

class XSPEED_L2_ORDER_STATISTICS(Structure):
	_fields_ = [
		("type", c_int8),
		("__0_1", c_uint8 * 3),
		("symbol", c_char * 27),
		("__0_2", c_uint8 * 57),
		("bid_total_qty", c_int32),
		("ask_total_qty", c_int32),
		("bid_weighted_avg_price", c_double),
		("ask_weighted_avg_price", c_double),
		("trailer", c_uint8 * 4),
		]
	_pack_ = 1

class XSPEED_L2_CURRENT_SETTLE(Structure):
	_fields_ = [
		("type", c_int8),
		("__0_1", c_uint8 * 3),
		("symbol", c_char * 27),
		("__0_2", c_uint8 * 57),
		("current_settle_price", c_double),
		("trailer", c_uint8 * 4),
		]
	_pack_ = 1

class XSPEED_L2_ARB(Structure):
	_fields_ = [
		("type", c_int8),
		("__0_1", c_uint8 * 3),
		("length", c_int32),
		("date", c_char * 9),
		("symbol", c_char * 27),
		("__0_2", c_uint8 * 60),
		("last_price", c_double),
		("low_price", c_double),
		("high_price", c_double),
		("historical_low_price", c_double),
		("historical_high_price", c_double),
		("high_limit", c_double),
		("low_limit", c_double),
		("best_bid_price1", c_double),
		("best_bid_qty1", c_int32),
		("best_ask_price1", c_double),
		("best_ask_qty1", c_int32),
		("time", c_char * 12),
		("__0_3", c_uint8 * 4),
		("bid_price_1", c_double),
		("bid_volume_1", c_int32),
		("bid_imply_qty_1", c_int32),
		("__b1__", c_uint8 * 16),
		("bid_price_2", c_double),
		("bid_volume_2", c_int32),
		("bid_imply_qty_2", c_int32),
		("__b2__", c_uint8 * 16),
		("bid_price_3", c_double),
		("bid_volume_3", c_int32),
		("bid_imply_qty_3", c_int32),
		("__b3__", c_uint8 * 16),
		("bid_price_4", c_double),
		("bid_volume_4", c_int32),
		("bid_imply_qty_4", c_int32),
		("__b4__", c_uint8 * 16),
		("bid_price_5", c_double),
		("bid_volume_5", c_int32),
		("bid_imply_qty_5", c_int32),
		("__b5__", c_uint8 * 16),
		("ask_price_1", c_double),
		("ask_volume_1", c_int32),
		("ask_imply_qty_1", c_int32),
		("__a1__", c_uint8 * 16),
		("ask_price_2", c_double),
		("ask_volume_2", c_int32),
		("ask_imply_qty_2", c_int32),
		("__a2__", c_uint8 * 16),
		("ask_price_3", c_double),
		("ask_volume_3", c_int32),
		("ask_imply_qty_3", c_int32),
		("__a3__", c_uint8 * 16),
		("ask_price_4", c_double),
		("ask_volume_4", c_int32),
		("ask_imply_qty_4", c_int32),
		("__a4__", c_uint8 * 16),
		("ask_price_5", c_double),
		("ask_volume_5", c_int32),
		("ask_imply_qty_5", c_int32),
		("__a5__", c_uint8 * 16),
		("trailer", c_uint8 * 4),
		]
	_pack_ = 1

class USTP_L2(Structure):
	_fields_ = [
		("version", c_uint8),
		("chain", c_uint8),
		("_1_", c_uint8 * 22),
		("symbol", c_char * 31),
		("time", c_char * 9),
		("updateMilliSec", c_uint32),
		("_2_", c_uint8 * 4),
		("open_price", c_double),
		("highest_price", c_double),
		("lowest_price", c_double),
		("_3_", c_uint8 * 8),
		("upperlimit_price", c_double),
		("lowerlimit_price", c_double),
		("_4_", c_uint8 * 20),
		("last_price", c_double),
		("volume", c_int),
		("turnover", c_double),
		("open_interest", c_double),
		("_5_", c_uint8 * 4),
		("bid_price1", c_double),
		("bid_volume1", c_int),
		("ask_price1", c_double),
		("ask_volume1", c_int),
		("_6_", c_uint8 * 4),
		("bid_price2", c_double),
		("bid_volume2", c_int),
		("bid_price3", c_double),
		("bid_volume3", c_int),
		("_7_", c_uint8 * 4),
		("ask_price2", c_double),
		("ask_volume2", c_int),
		("ask_price3", c_double),
		("ask_volume3", c_int),
		("_8_", c_uint8 * 4),
		("bid_price4", c_double),
		("bid_volume4", c_int),
		("bid_price5", c_double),
		("bid_volume5", c_int),
		("_9_", c_uint8 * 4),
		("ask_price4", c_double),
		("ask_volume4", c_int),
		("ask_price5", c_double),
		("ask_volume5", c_int),
		]
	_pack_ = 1

class GUAVA_L1(Structure):
	_fields_ = [
		("sequence", c_uint32),
		("exchange_id", c_char),
		("channel_id", c_uint8),
		("quote_flag", c_uint8),
		("symbol", c_char * 8),
		("update_time", c_char * 9),
		("millisecond", c_int32),
		("last_px", c_double),
		("last_share", c_int32),
		("total_value", c_double),
		("total_pos", c_double),
		("bid_px", c_double),
		("bid_share", c_int32),
		("ask_px", c_double),
		("ask_share", c_int32),
		]
	_pack_ = 1

SnifferMsgType2Struct = {
	 11904 : XSPEED_L2_ANLIANG,
	 11905 : XSPEED_L2_ORDER10,
	 11906 : XSPEED_L2_MATCH_BY_PRICE,
	 11907 : XSPEED_L2_ORDER_STATISTICS,
	 11908 : XSPEED_L2_CURRENT_SETTLE,
	 11909 : XSPEED_L2_ARB,
	 11910 : USTP_L2,
	 11911 : GUAVA_L1,
	 12901 : XSPEED_L1,
	 12902 : XSPEED_L2,
	 12903 : XSPEED_L1_ANLIANG,
	 12904 : XSPEED_L2_ANLIANG,
	 12905 : XSPEED_L2_ORDER10,
	 12906 : XSPEED_L2_MATCH_BY_PRICE,
	 12907 : XSPEED_L2_ORDER_STATISTICS,
	 12908 : XSPEED_L2_CURRENT_SETTLE,
	 12909 : XSPEED_L2_ARB,
	 12910 : USTP_L2,
	 12911 : GUAVA_L1,
	 11901 : XSPEED_L1,
	 11902 : XSPEED_L2,
	 11903 : XSPEED_L1_ANLIANG,
}

class LFMarketDataField(Structure):
    _fields_ = [
        ("TradingDay", c_char * 13),	# 交易日 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ("ExchangeInstID", c_char * 64),	# 合约在交易所的代码 
        ("LastPrice", c_double),	# 最新价 
        ("PreSettlementPrice", c_double),	# 上次结算价 
        ("PreClosePrice", c_double),	# 昨收盘 
        ("PreOpenInterest", c_double),	# 昨持仓量 
        ("OpenPrice", c_double),	# 今开盘 
        ("HighestPrice", c_double),	# 最高价 
        ("LowestPrice", c_double),	# 最低价 
        ("Volume", c_int),	# 数量 
        ("Turnover", c_double),	# 成交金额 
        ("OpenInterest", c_double),	# 持仓量 
        ("ClosePrice", c_double),	# 今收盘 
        ("SettlementPrice", c_double),	# 本次结算价 
        ("UpperLimitPrice", c_double),	# 涨停板价 
        ("LowerLimitPrice", c_double),	# 跌停板价 
        ("PreDelta", c_double),	# 昨虚实度 
        ("CurrDelta", c_double),	# 今虚实度 
        ("UpdateTime", c_char * 13),	# 最后修改时间 
        ("UpdateMillisec", c_int),	# 最后修改毫秒 
        ("BidPrice1", c_double),	# 申买价一 
        ("BidVolume1", c_int),	# 申买量一 
        ("AskPrice1", c_double),	# 申卖价一 
        ("AskVolume1", c_int),	# 申卖量一 
        ("BidPrice2", c_double),	# 申买价二 
        ("BidVolume2", c_int),	# 申买量二 
        ("AskPrice2", c_double),	# 申卖价二 
        ("AskVolume2", c_int),	# 申卖量二 
        ("BidPrice3", c_double),	# 申买价三 
        ("BidVolume3", c_int),	# 申买量三 
        ("AskPrice3", c_double),	# 申卖价三 
        ("AskVolume3", c_int),	# 申卖量三 
        ("BidPrice4", c_double),	# 申买价四 
        ("BidVolume4", c_int),	# 申买量四 
        ("AskPrice4", c_double),	# 申卖价四 
        ("AskVolume4", c_int),	# 申卖量四 
        ("BidPrice5", c_double),	# 申买价五 
        ("BidVolume5", c_int),	# 申买量五 
        ("AskPrice5", c_double),	# 申卖价五 
        ("AskVolume5", c_int),	# 申卖量五 
        ]

class LFL2MarketDataField(Structure):
    _fields_ = [
        ("TradingDay", c_char * 9),	# 交易日 
        ("TimeStamp", c_char * 9),	# 时间戳 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("PreClosePrice", c_double),	# 昨收盘价 
        ("OpenPrice", c_double),	# 今开盘价 
        ("ClosePrice", c_double),	# 收盘价 
        ("IOPV", c_double),	# 净值估值 
        ("YieldToMaturity", c_double),	# 到期收益率 
        ("AuctionPrice", c_double),	# 动态参考价格 
        ("TradingPhase", c_char),	# 交易阶段 char
        ("OpenRestriction", c_char),	# 开仓限制 char
        ("HighPrice", c_double),	# 最高价 
        ("LowPrice", c_double),	# 最低价 
        ("LastPrice", c_double),	# 最新价 
        ("TradeCount", c_double),	# 成交笔数 
        ("TotalTradeVolume", c_double),	# 成交总量 
        ("TotalTradeValue", c_double),	# 成交总金额 
        ("OpenInterest", c_double),	# 持仓量 
        ("TotalBidVolume", c_double),	# 委托买入总量 
        ("WeightedAvgBidPrice", c_double),	# 加权平均委买价 
        ("AltWeightedAvgBidPrice", c_double),	# 债券加权平均委买价 
        ("TotalOfferVolume", c_double),	# 委托卖出总量 
        ("WeightedAvgOfferPrice", c_double),	# 加权平均委卖价 
        ("AltWeightedAvgOfferPrice", c_double),	# 债券加权平均委卖价格 
        ("BidPriceLevel", c_int),	# 买价深度 
        ("OfferPriceLevel", c_int),	# 卖价深度 
        ("BidPrice1", c_double),	# 申买价一 
        ("BidVolume1", c_double),	# 申买量一 
        ("BidCount1", c_int),	# 实际买总委托笔数一 
        ("BidPrice2", c_double),	# 申买价二 
        ("BidVolume2", c_double),	# 申买量二 
        ("BidCount2", c_int),	# 实际买总委托笔数二 
        ("BidPrice3", c_double),	# 申买价三 
        ("BidVolume3", c_double),	# 申买量三 
        ("BidCount3", c_int),	# 实际买总委托笔数三 
        ("BidPrice4", c_double),	# 申买价四 
        ("BidVolume4", c_double),	# 申买量四 
        ("BidCount4", c_int),	# 实际买总委托笔数四 
        ("BidPrice5", c_double),	# 申买价五 
        ("BidVolume5", c_double),	# 申买量五 
        ("BidCount5", c_int),	# 实际买总委托笔数五 
        ("BidPrice6", c_double),	# 申买价六 
        ("BidVolume6", c_double),	# 申买量六 
        ("BidCount6", c_int),	# 实际买总委托笔数六 
        ("BidPrice7", c_double),	# 申买价七 
        ("BidVolume7", c_double),	# 申买量七 
        ("BidCount7", c_int),	# 实际买总委托笔数七 
        ("BidPrice8", c_double),	# 申买价八 
        ("BidVolume8", c_double),	# 申买量八 
        ("BidCount8", c_int),	# 实际买总委托笔数八 
        ("BidPrice9", c_double),	# 申买价九 
        ("BidVolume9", c_double),	# 申买量九 
        ("BidCount9", c_int),	# 实际买总委托笔数九 
        ("BidPriceA", c_double),	# 申买价十 
        ("BidVolumeA", c_double),	# 申买量十 
        ("BidCountA", c_int),	# 实际买总委托笔数十 
        ("OfferPrice1", c_double),	# 申卖价一 
        ("OfferVolume1", c_double),	# 申卖量一 
        ("OfferCount1", c_int),	# 实际卖总委托笔数一 
        ("OfferPrice2", c_double),	# 申卖价二 
        ("OfferVolume2", c_double),	# 申卖量二 
        ("OfferCount2", c_int),	# 实际卖总委托笔数二 
        ("OfferPrice3", c_double),	# 申卖价三 
        ("OfferVolume3", c_double),	# 申卖量三 
        ("OfferCount3", c_int),	# 实际卖总委托笔数三 
        ("OfferPrice4", c_double),	# 申卖价四 
        ("OfferVolume4", c_double),	# 申卖量四 
        ("OfferCount4", c_int),	# 实际卖总委托笔数四 
        ("OfferPrice5", c_double),	# 申卖价五 
        ("OfferVolume5", c_double),	# 申卖量五 
        ("OfferCount5", c_int),	# 实际卖总委托笔数五 
        ("OfferPrice6", c_double),	# 申卖价六 
        ("OfferVolume6", c_double),	# 申卖量六 
        ("OfferCount6", c_int),	# 实际卖总委托笔数六 
        ("OfferPrice7", c_double),	# 申卖价七 
        ("OfferVolume7", c_double),	# 申卖量七 
        ("OfferCount7", c_int),	# 实际卖总委托笔数七 
        ("OfferPrice8", c_double),	# 申卖价八 
        ("OfferVolume8", c_double),	# 申卖量八 
        ("OfferCount8", c_int),	# 实际卖总委托笔数八 
        ("OfferPrice9", c_double),	# 申卖价九 
        ("OfferVolume9", c_double),	# 申卖量九 
        ("OfferCount9", c_int),	# 实际卖总委托笔数九 
        ("OfferPriceA", c_double),	# 申卖价十 
        ("OfferVolumeA", c_double),	# 申卖量十 
        ("OfferCountA", c_int),	# 实际卖总委托笔数十 
        ("InstrumentStatus", c_char * 7),	# 合约状态 
        ("PreIOPV", c_double),	# 昨净值估值 
        ("PERatio1", c_double),	# 市盈率一 
        ("PERatio2", c_double),	# 市盈率二 
        ("UpperLimitPrice", c_double),	# 涨停价 
        ("LowerLimitPrice", c_double),	# 跌停价 
        ("WarrantPremiumRatio", c_double),	# 权证溢价率 
        ("TotalWarrantExecQty", c_double),	# 权证执行总数量 
        ("PriceDiff1", c_double),	# 升跌一 
        ("PriceDiff2", c_double),	# 升跌二 
        ("ETFBuyNumber", c_double),	# ETF申购笔数 
        ("ETFBuyAmount", c_double),	# ETF申购数量 
        ("ETFBuyMoney", c_double),	# ETF申购金额 
        ("ETFSellNumber", c_double),	# ETF赎回笔数 
        ("ETFSellAmount", c_double),	# ETF赎回数量 
        ("ETFSellMoney", c_double),	# ETF赎回金额 
        ("WithdrawBuyNumber", c_double),	# 买入撤单笔数 
        ("WithdrawBuyAmount", c_double),	# 买入撤单数量 
        ("WithdrawBuyMoney", c_double),	# 买入撤单金额 
        ("TotalBidNumber", c_double),	# 买入总笔数 
        ("BidTradeMaxDuration", c_double),	# 买入委托成交最大等待时间 
        ("NumBidOrders", c_double),	# 买方委托价位数 
        ("WithdrawSellNumber", c_double),	# 卖出撤单笔数 
        ("WithdrawSellAmount", c_double),	# 卖出撤单数量 
        ("WithdrawSellMoney", c_double),	# 卖出撤单金额 
        ("TotalOfferNumber", c_double),	# 卖出总笔数 
        ("OfferTradeMaxDuration", c_double),	# 卖出委托成交最大等待时间 
        ("NumOfferOrders", c_double),	# 卖方委托价位数 
        ]

class LFL2IndexField(Structure):
    _fields_ = [
        ("TradingDay", c_char * 9),	# 交易日 
        ("TimeStamp", c_char * 9),	# 行情时间（秒） 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ("InstrumentID", c_char * 31),	# 指数代码 
        ("PreCloseIndex", c_double),	# 前收盘指数 
        ("OpenIndex", c_double),	# 今开盘指数 
        ("CloseIndex", c_double),	# 今日收盘指数 
        ("HighIndex", c_double),	# 最高指数 
        ("LowIndex", c_double),	# 最低指数 
        ("LastIndex", c_double),	# 最新指数 
        ("TurnOver", c_double),	# 参与计算相应指数的成交金额（元） 
        ("TotalVolume", c_double),	# 参与计算相应指数的交易数量（手） 
        ]

class LFL2OrderField(Structure):
    _fields_ = [
        ("OrderTime", c_char * 9),	# 委托时间（秒） 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("Price", c_double),	# 委托价格 
        ("Volume", c_double),	# 委托数量 
        ("OrderKind", c_char * 2),	# 报单类型 
        ]

class LFL2TradeField(Structure):
    _fields_ = [
        ("TradeTime", c_char * 9),	# 成交时间（秒） 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("Price", c_double),	# 成交价格 
        ("Volume", c_double),	# 成交数量 
        ("OrderKind", c_char * 2),	# 报单类型 
        ("OrderBSFlag", c_char * 2),	# 内外盘标志 
        ]

class LFBarMarketDataField(Structure):
    _fields_ = [
        ("TradingDay", c_char * 9),	# 交易日 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("UpperLimitPrice", c_double),	# 涨停板价 
        ("LowerLimitPrice", c_double),	# 跌停板价 
        ("StartUpdateTime", c_char * 13),	# 首tick修改时间 
        ("StartUpdateMillisec", c_int),	# 首tick最后修改毫秒 
        ("EndUpdateTime", c_char * 13),	# 尾tick最后修改时间 
        ("EndUpdateMillisec", c_int),	# 尾tick最后修改毫秒 
        ("Open", c_double),	# 开 
        ("Close", c_double),	# 收 
        ("Low", c_double),	# 低 
        ("High", c_double),	# 高 
        ("Volume", c_double),	# 区间交易量 
        ("StartVolume", c_double),	# 初始总交易量 
        ]

class LFQryPositionField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ]

class LFRspPositionField(Structure):
    _fields_ = [
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("YdPosition", c_int),	# 上日持仓 
        ("Position", c_int),	# 总持仓 
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("PositionCost", c_double),	# 持仓成本 
        ("HedgeFlag", c_char),	# 投机套保标志 LfHedgeFlagType
        ("PosiDirection", c_char),	# 持仓多空方向 LfPosiDirectionType
        ]

class LFInputOrderField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("UserID", c_char * 16),	# 用户代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("BusinessUnit", c_char * 21),	# 业务单元 
        ("ExchangeID", c_char * 9),	# 交易所代码 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("OrderRef", c_char * 21),	# 报单引用 
        ("LimitPrice", c_double),	# 价格 
        ("Volume", c_int),	# 数量 
        ("MinVolume", c_int),	# 最小成交量 
        ("TimeCondition", c_char),	# 有效期类型 LfTimeConditionType
        ("VolumeCondition", c_char),	# 成交量类型 LfVolumeConditionType
        ("OrderPriceType", c_char),	# 报单价格条件 LfOrderPriceTypeType
        ("Direction", c_char),	# 买卖方向 LfDirectionType
        ("OffsetFlag", c_char),	# 开平标志 LfOffsetFlagType
        ("HedgeFlag", c_char),	# 投机套保标志 LfHedgeFlagType
        ("ForceCloseReason", c_char),	# 强平原因 LfForceCloseReasonType
        ("StopPrice", c_double),	# 止损价 
        ("IsAutoSuspend", c_int),	# 自动挂起标志 
        ("ContingentCondition", c_char),	# 触发条件 LfContingentConditionType
        ("MiscInfo", c_char * 30),	# 委托自定义标签 
        ]

class LFRtnOrderField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("UserID", c_char * 16),	# 用户代码 
        ("ParticipantID", c_char * 11),	# 会员代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("BusinessUnit", c_char * 21),	# 业务单元 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("OrderRef", c_char * 21),	# 报单引用 
        ("ExchangeID", c_char * 11),	# 交易所代码 
        ("LimitPrice", c_double),	# 价格 
        ("VolumeTraded", c_int),	# 今成交数量 
        ("VolumeTotal", c_int),	# 剩余数量 
        ("VolumeTotalOriginal", c_int),	# 数量 
        ("TimeCondition", c_char),	# 有效期类型 LfTimeConditionType
        ("VolumeCondition", c_char),	# 成交量类型 LfVolumeConditionType
        ("OrderPriceType", c_char),	# 报单价格条件 LfOrderPriceTypeType
        ("Direction", c_char),	# 买卖方向 LfDirectionType
        ("OffsetFlag", c_char),	# 开平标志 LfOffsetFlagType
        ("HedgeFlag", c_char),	# 投机套保标志 LfHedgeFlagType
        ("OrderStatus", c_char),	# 报单状态 LfOrderStatusType
        ("RequestID", c_int),	# 请求编号 
        ]

class LFRtnTradeField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("UserID", c_char * 16),	# 用户代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("BusinessUnit", c_char * 21),	# 业务单元 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("OrderRef", c_char * 21),	# 报单引用 
        ("ExchangeID", c_char * 11),	# 交易所代码 
        ("TradeID", c_char * 21),	# 成交编号 
        ("OrderSysID", c_char * 31),	# 报单编号 
        ("ParticipantID", c_char * 11),	# 会员代码 
        ("ClientID", c_char * 21),	# 客户代码 
        ("Price", c_double),	# 价格 
        ("Volume", c_int),	# 数量 
        ("TradingDay", c_char * 13),	# 交易日 
        ("TradeTime", c_char * 13),	# 成交时间 
        ("Direction", c_char),	# 买卖方向 LfDirectionType
        ("OffsetFlag", c_char),	# 开平标志 LfOffsetFlagType
        ("HedgeFlag", c_char),	# 投机套保标志 LfHedgeFlagType
        ]

class LFOrderActionField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("InstrumentID", c_char * 31),	# 合约代码 
        ("ExchangeID", c_char * 11),	# 交易所代码 
        ("UserID", c_char * 16),	# 用户代码 
        ("OrderRef", c_char * 21),	# 报单引用 
        ("OrderSysID", c_char * 31),	# 报单编号 
        ("RequestID", c_int),	# 请求编号 
        ("ActionFlag", c_char),	# 报单操作标志 char
        ("LimitPrice", c_double),	# 价格 
        ("VolumeChange", c_int),	# 数量变化 
        ("KfOrderID", c_int),	# Kf系统内订单ID 
        ]

class LFQryAccountField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ]

class LFRspAccountField(Structure):
    _fields_ = [
        ("BrokerID", c_char * 11),	# 经纪公司代码 
        ("InvestorID", c_char * 19),	# 投资者代码 
        ("PreMortgage", c_double),	# 上次质押金额 
        ("PreCredit", c_double),	# 上次信用额度 
        ("PreDeposit", c_double),	# 上次存款额 
        ("preBalance", c_double),	# 上次结算准备金 
        ("PreMargin", c_double),	# 上次占用的保证金 
        ("Deposit", c_double),	# 入金金额 
        ("Withdraw", c_double),	# 出金金额 
        ("FrozenMargin", c_double),	# 冻结的保证金（报单未成交冻结的保证金） 
        ("FrozenCash", c_double),	# 冻结的资金（报单未成交冻结的总资金） 
        ("FrozenCommission", c_double),	# 冻结的手续费（报单未成交冻结的手续费） 
        ("CurrMargin", c_double),	# 当前保证金总额 
        ("CashIn", c_double),	# 资金差额 
        ("Commission", c_double),	# 手续费 
        ("CloseProfit", c_double),	# 平仓盈亏 
        ("PositionProfit", c_double),	# 持仓盈亏 
        ("Balance", c_double),	# 结算准备金 
        ("Available", c_double),	# 可用资金 
        ("WithdrawQuota", c_double),	# 可取资金 
        ("Reserve", c_double),	# 基本准备金 
        ("TradingDay", c_char * 9),	# 交易日 
        ("Credit", c_double),	# 信用额度 
        ("Mortgage", c_double),	# 质押金额 
        ("ExchangeMargin", c_double),	# 交易所保证金 
        ("DeliveryMargin", c_double),	# 投资者交割保证金 
        ("ExchangeDeliveryMargin", c_double),	# 交易所交割保证金 
        ("ReserveBalance", c_double),	# 保底期货结算准备金 
        ("Equity", c_double),	# 当日权益 
        ("MarketValue", c_double),	# 账户市值 
        ]

DataFieldMap = {
	'LFL2MarketDataField': {
		'OfferVolumeA': 'd',
		'TotalOfferNumber': 'd',
		'WithdrawSellAmount': 'd',
		'BidCount3': 'i',
		'BidCount2': 'i',
		'BidCount1': 'i',
		'BidCount7': 'i',
		'BidCount6': 'i',
		'BidCount5': 'i',
		'BidCount4': 'i',
		'BidVolume7': 'd',
		'BidVolume6': 'd',
		'BidCount9': 'i',
		'BidCount8': 'i',
		'BidVolume3': 'd',
		'BidVolume2': 'd',
		'BidVolume1': 'd',
		'TradeCount': 'd',
		'BidPrice6': 'd',
		'PreIOPV': 'd',
		'TimeStamp': 'c9',
		'TradingDay': 'c9',
		'BidCountA': 'i',
		'OpenInterest': 'd',
		'BidVolumeA': 'd',
		'NumOfferOrders': 'd',
		'OfferVolume4': 'd',
		'OfferVolume5': 'd',
		'OfferVolume6': 'd',
		'OfferVolume7': 'd',
		'OfferVolume1': 'd',
		'OfferVolume2': 'd',
		'OfferVolume3': 'd',
		'OfferVolume8': 'd',
		'OfferVolume9': 'd',
		'ETFSellMoney': 'd',
		'TotalTradeVolume': 'd',
		'PriceDiff1': 'd',
		'PriceDiff2': 'd',
		'OfferPriceA': 'd',
		'BidPriceLevel': 'i',
		'TotalOfferVolume': 'd',
		'OfferPriceLevel': 'i',
		'InstrumentStatus': 'c7',
		'NumBidOrders': 'd',
		'ETFSellAmount': 'd',
		'WithdrawSellNumber': 'd',
		'AltWeightedAvgBidPrice': 'd',
		'WeightedAvgBidPrice': 'd',
		'OfferPrice8': 'd',
		'BidVolume9': 'd',
		'WithdrawBuyMoney': 'd',
		'OfferPrice4': 'd',
		'BidVolume8': 'd',
		'OfferPrice6': 'd',
		'OfferPrice7': 'd',
		'OfferPrice1': 'd',
		'OfferPrice2': 'd',
		'OfferPrice3': 'd',
		'WithdrawBuyAmount': 'd',
		'BidVolume5': 'd',
		'BidVolume4': 'd',
		'BidPrice9': 'd',
		'BidPrice8': 'd',
		'BidPrice5': 'd',
		'BidPrice4': 'd',
		'BidPrice7': 'd',
		'AltWeightedAvgOfferPrice': 'd',
		'BidPrice1': 'd',
		'TotalWarrantExecQty': 'd',
		'BidPrice3': 'd',
		'BidPrice2': 'd',
		'LowerLimitPrice': 'd',
		'OpenPrice': 'd',
		'WithdrawSellMoney': 'd',
		'OfferTradeMaxDuration': 'd',
		'OfferCount7': 'i',
		'WarrantPremiumRatio': 'd',
		'ExchangeID': 'c9',
		'ETFSellNumber': 'd',
		'AuctionPrice': 'd',
		'OfferPrice9': 'd',
		'YieldToMaturity': 'd',
		'OfferPrice5': 'd',
		'TradingPhase': 'c',
		'BidPriceA': 'd',
		'PERatio2': 'd',
		'TotalBidVolume': 'd',
		'PERatio1': 'd',
		'OfferCount8': 'i',
		'OfferCount9': 'i',
		'OfferCount6': 'i',
		'LowPrice': 'd',
		'OfferCount4': 'i',
		'OfferCount5': 'i',
		'OfferCount2': 'i',
		'OfferCount3': 'i',
		'TotalBidNumber': 'd',
		'OfferCount1': 'i',
		'WithdrawBuyNumber': 'd',
		'OpenRestriction': 'c',
		'BidTradeMaxDuration': 'd',
		'PreClosePrice': 'd',
		'UpperLimitPrice': 'd',
		'WeightedAvgOfferPrice': 'd',
		'InstrumentID': 'c31',
		'ClosePrice': 'd',
		'HighPrice': 'd',
		'TotalTradeValue': 'd',
		'IOPV': 'd',
		'LastPrice': 'd',
		'ETFBuyNumber': 'd',
		'ETFBuyMoney': 'd',
		'ETFBuyAmount': 'd',
		'OfferCountA': 'i',
	},
	'LFRtnTradeField': {
		'InstrumentID': 'c31',
		'ExchangeID': 'c11',
		'ParticipantID': 'c11',
		'TradeID': 'c21',
		'TradingDay': 'c13',
		'BusinessUnit': 'c21',
		'HedgeFlag': LfHedgeFlagTypeMap,
		'Price': 'd',
		'UserID': 'c16',
		'Direction': LfDirectionTypeMap,
		'ClientID': 'c21',
		'OrderRef': 'c21',
		'Volume': 'i',
		'InvestorID': 'c19',
		'BrokerID': 'c11',
		'OrderSysID': 'c31',
		'TradeTime': 'c13',
		'OffsetFlag': LfOffsetFlagTypeMap,
	},
	'LFRspAccountField': {
		'Mortgage': 'd',
		'ExchangeDeliveryMargin': 'd',
		'FrozenMargin': 'd',
		'WithdrawQuota': 'd',
		'PositionProfit': 'd',
		'Commission': 'd',
		'Equity': 'd',
		'CashIn': 'd',
		'Available': 'd',
		'InvestorID': 'c19',
		'PreCredit': 'd',
		'PreMortgage': 'd',
		'ExchangeMargin': 'd',
		'PreMargin': 'd',
		'DeliveryMargin': 'd',
		'preBalance': 'd',
		'TradingDay': 'c9',
		'BrokerID': 'c11',
		'Deposit': 'd',
		'Withdraw': 'd',
		'Balance': 'd',
		'Reserve': 'd',
		'PreDeposit': 'd',
		'Credit': 'd',
		'MarketValue': 'd',
		'ReserveBalance': 'd',
		'CurrMargin': 'd',
		'FrozenCommission': 'd',
		'CloseProfit': 'd',
		'FrozenCash': 'd',
	},
	'LFL2IndexField': {
		'InstrumentID': 'c31',
		'ExchangeID': 'c9',
		'HighIndex': 'd',
		'TimeStamp': 'c9',
		'CloseIndex': 'd',
		'PreCloseIndex': 'd',
		'LastIndex': 'd',
		'TradingDay': 'c9',
		'OpenIndex': 'd',
		'TotalVolume': 'd',
		'LowIndex': 'd',
		'TurnOver': 'd',
	},
	'LFL2OrderField': {
		'InstrumentID': 'c31',
		'OrderTime': 'c9',
		'OrderKind': 'c2',
		'Price': 'd',
		'ExchangeID': 'c9',
		'Volume': 'd',
	},
	'LFQryPositionField': {
		'InstrumentID': 'c31',
		'InvestorID': 'c19',
		'ExchangeID': 'c9',
		'BrokerID': 'c11',
	},
	'LFInputOrderField': {
		'InstrumentID': 'c31',
		'ContingentCondition': LfContingentConditionTypeMap,
		'ExchangeID': 'c9',
		'MinVolume': 'i',
		'OffsetFlag': LfOffsetFlagTypeMap,
		'OrderPriceType': LfOrderPriceTypeTypeMap,
		'BusinessUnit': 'c21',
		'HedgeFlag': LfHedgeFlagTypeMap,
		'IsAutoSuspend': 'i',
		'ForceCloseReason': LfForceCloseReasonTypeMap,
		'UserID': 'c16',
		'Direction': LfDirectionTypeMap,
		'LimitPrice': 'd',
		'OrderRef': 'c21',
		'Volume': 'i',
		'InvestorID': 'c19',
		'VolumeCondition': LfVolumeConditionTypeMap,
		'TimeCondition': LfTimeConditionTypeMap,
		'BrokerID': 'c11',
		'MiscInfo': 'c30',
		'StopPrice': 'd',
	},
	'LFRtnOrderField': {
		'InstrumentID': 'c31',
		'ExchangeID': 'c11',
		'ParticipantID': 'c11',
		'OrderPriceType': LfOrderPriceTypeTypeMap,
		'BusinessUnit': 'c21',
		'HedgeFlag': LfHedgeFlagTypeMap,
		'VolumeTotalOriginal': 'i',
		'RequestID': 'i',
		'UserID': 'c16',
		'Direction': LfDirectionTypeMap,
		'LimitPrice': 'd',
		'OrderRef': 'c21',
		'InvestorID': 'c19',
		'VolumeCondition': LfVolumeConditionTypeMap,
		'TimeCondition': LfTimeConditionTypeMap,
		'BrokerID': 'c11',
		'OrderStatus': LfOrderStatusTypeMap,
		'VolumeTraded': 'i',
		'VolumeTotal': 'i',
		'OffsetFlag': LfOffsetFlagTypeMap,
	},
	'LFQryAccountField': {
		'InvestorID': 'c19',
		'BrokerID': 'c11',
	},
	'LFMarketDataField': {
		'HighestPrice': 'd',
		'BidPrice5': 'd',
		'BidPrice4': 'd',
		'BidPrice1': 'd',
		'BidPrice3': 'd',
		'BidPrice2': 'd',
		'LowerLimitPrice': 'd',
		'OpenPrice': 'd',
		'AskPrice5': 'd',
		'AskPrice4': 'd',
		'AskPrice3': 'd',
		'PreClosePrice': 'd',
		'AskPrice1': 'd',
		'PreSettlementPrice': 'd',
		'AskVolume1': 'i',
		'UpdateTime': 'c13',
		'UpdateMillisec': 'i',
		'BidVolume5': 'i',
		'BidVolume4': 'i',
		'BidVolume3': 'i',
		'BidVolume2': 'i',
		'PreOpenInterest': 'd',
		'AskPrice2': 'd',
		'Volume': 'i',
		'AskVolume3': 'i',
		'AskVolume2': 'i',
		'AskVolume5': 'i',
		'AskVolume4': 'i',
		'UpperLimitPrice': 'd',
		'BidVolume1': 'i',
		'InstrumentID': 'c31',
		'ClosePrice': 'd',
		'ExchangeID': 'c9',
		'TradingDay': 'c13',
		'PreDelta': 'd',
		'OpenInterest': 'd',
		'CurrDelta': 'd',
		'Turnover': 'd',
		'LastPrice': 'd',
		'SettlementPrice': 'd',
		'ExchangeInstID': 'c64',
		'LowestPrice': 'd',
	},
	'LFRspPositionField': {
		'InstrumentID': 'c31',
		'PosiDirection': LfPosiDirectionTypeMap,
		'HedgeFlag': LfHedgeFlagTypeMap,
		'YdPosition': 'i',
		'InvestorID': 'c19',
		'PositionCost': 'd',
		'BrokerID': 'c11',
		'Position': 'i',
	},
	'LFBarMarketDataField': {
		'InstrumentID': 'c31',
		'Volume': 'd',
		'StartVolume': 'd',
		'EndUpdateMillisec': 'i',
		'High': 'd',
		'TradingDay': 'c9',
		'LowerLimitPrice': 'd',
		'Low': 'd',
		'UpperLimitPrice': 'd',
		'Close': 'd',
		'EndUpdateTime': 'c13',
		'StartUpdateTime': 'c13',
		'Open': 'd',
		'StartUpdateMillisec': 'i',
	},
	'LFL2TradeField': {
		'InstrumentID': 'c31',
		'ExchangeID': 'c9',
		'OrderKind': 'c2',
		'OrderBSFlag': 'c2',
		'Price': 'd',
		'Volume': 'd',
		'TradeTime': 'c9',
	},
	'LFOrderActionField': {
		'InstrumentID': 'c31',
		'ExchangeID': 'c11',
		'ActionFlag': 'c',
		'KfOrderID': 'i',
		'UserID': 'c16',
		'LimitPrice': 'd',
		'OrderRef': 'c21',
		'InvestorID': 'c19',
		'VolumeChange': 'i',
		'BrokerID': 'c11',
		'RequestID': 'i',
		'OrderSysID': 'c31',
	},
}

MsgType2LFStruct = {
    MsgTypes.MD: LFMarketDataField,
    MsgTypes.L2_MD: LFL2MarketDataField,
    MsgTypes.L2_INDEX: LFL2IndexField,
    MsgTypes.L2_ORDER: LFL2OrderField,
    MsgTypes.L2_TRADE: LFL2TradeField,
    MsgTypes.BAR_MD: LFBarMarketDataField,
    MsgTypes.QRY_POS: LFQryPositionField,
    MsgTypes.RSP_POS: LFRspPositionField,
    MsgTypes.ORDER: LFInputOrderField,
    MsgTypes.RTN_ORDER: LFRtnOrderField,
    MsgTypes.RTN_TRADE: LFRtnTradeField,
    MsgTypes.ORDER_ACTION: LFOrderActionField,
    MsgTypes.QRY_ACCOUNT: LFQryAccountField,
    MsgTypes.RSP_ACCOUNT: LFRspAccountField,
}

MsgType2LFStruct.update(SnifferMsgType2Struct)

LFStruct2MsgType = {
    LFMarketDataField: MsgTypes.MD,
    LFL2MarketDataField: MsgTypes.L2_MD,
    LFL2IndexField: MsgTypes.L2_INDEX,
    LFL2OrderField: MsgTypes.L2_ORDER,
    LFL2TradeField: MsgTypes.L2_TRADE,
    LFBarMarketDataField: MsgTypes.BAR_MD,
    LFQryPositionField: MsgTypes.QRY_POS,
    LFRspPositionField: MsgTypes.RSP_POS,
    LFInputOrderField: MsgTypes.ORDER,
    LFRtnOrderField: MsgTypes.RTN_ORDER,
    LFRtnTradeField: MsgTypes.RTN_TRADE,
    LFOrderActionField: MsgTypes.ORDER_ACTION,
    LFQryAccountField: MsgTypes.QRY_ACCOUNT,
    LFRspAccountField: MsgTypes.RSP_ACCOUNT,
}




cast_data = lambda x, y: ctypes.cast(x, ctypes.POINTER(y)).contents

cast_frame = lambda f: cast_data(f.get_data(), MsgType2LFStruct[f.msg_type()])

dcast_frame = lambda f: cast_frame(f) if f.msg_type() in MsgType2LFStruct.keys() else None

def write(writer, struct, source=0, last_flag=True, request_id=-1):
    data = ctypes.addressof(struct)
    length = ctypes.sizeof(struct)
    msg_type = LFStruct2MsgType[type(struct)]
    writer.write(data, length, source, msg_type, last_flag, request_id)

def get_contents(frame):
    '''
    :param frame: data frame in yjj
    :return: list of tuple
        [(field1, content1), (field2, content2), ...]
    '''
    data = dcast_frame(frame)
    if data :
        return get_contents_d(data)
    else:
        return []

def get_contents_d(data):
    res = []
    # if DataFieldMap.has_key(data.__class__.__name__):
    if data.__class__.__name__ in DataFieldMap.keys():
        for field_name, field_type in data._fields_:
            tp_s = DataFieldMap[data.__class__.__name__][field_name]
            if type(tp_s) is dict:
                type_s = 't'
                content = tp_s.get(getattr(data, field_name), 'UnExpected')
            else:
                type_s = tp_s
                content = getattr(data, field_name)
            res.append((field_name, type_s, content))
        return res
    else:
        for field_name, field_type in data._fields_:
            res.append((field_name, field_type, getattr(data, field_name)))
        return res

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, bytes):
        return data.decode('utf-8')  # need confirm 'unicode-escape' ?
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
            }
    # if it's anything else, return it in its original form
    return data

class ID2Exchange:

    SSE_CODE = 'SSE'
    SZE_CODE = 'SZE'

    @staticmethod
    def get_stock_exchange(ticker):
        if ticker.startswith('6'):
            return ID2Exchange.SSE_CODE
        else:
            return ID2Exchange.SZE_CODE

def process_position(positions):
    tickers = set().union(* [k.keys() for k in positions.values()])
    investor_position = {ticker: {LfPosiDirectionType.Net:(positions["net_total"].get(ticker, 0), positions["net_yd"].get(ticker, 0)),
                                  LfPosiDirectionType.Long:(positions["long_total"].get(ticker, 0), positions["long_yd"].get(ticker, 0)),
                                  LfPosiDirectionType.Short:(positions["short_total"].get(ticker, 0), positions["short_yd"].get(ticker, 0))} for ticker in tickers }
    return investor_position

def strfnano(nano, format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.fromtimestamp(nano / 1000000000).strftime(format)
