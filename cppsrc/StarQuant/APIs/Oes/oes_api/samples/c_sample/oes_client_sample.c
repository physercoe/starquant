/*
 * Copyright 2016 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @file    oes_client_sample.c
 *
 * OES API接口库的示例程序
 *
 * @version 1.0 2016/10/21
 * @since   2016/10/21
 */


#include    <oes_api/oes_api.h>
#include    <sutil/logger/spk_log.h>


/**
 * 发送委托请求
 *
 * 提示:
 * - 可以通过 OesApi_GetClEnvId() 方法获得到当前通道所使用的客户端环境号(clEnvId), 如:
 *   <code>int8 clEnvId = OesApi_GetClEnvId(pOrdChannel);</code>
 *
 * @param   pOrdChannel     委托通道的会话信息
 * @param   mktId           市场代码 (必填) @see eOesMarketIdT
 * @param   pSecurityId     股票代码 (必填)
 * @param   pInvAcctId      股东账户代码 (可不填)
 * @param   ordType         委托类型 (必填) @see eOesOrdTypeT, eOesOrdTypeShT, eOesOrdTypeSzT
 * @param   bsType          买卖类型 (必填) @see eOesBuySellTypeT
 * @param   ordQty          委托数量 (必填, 单位为股/张)
 * @param   ordPrice        委托价格 (必填, 单位精确到元后四位，即1元 = 10000)
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static inline int32
_OesApiSample_SendOrderReq(OesApiSessionInfoT *pOrdChannel,
        uint8 mktId, const char *pSecurityId, const char *pInvAcctId,
        uint8 ordType, uint8 bsType, int32 ordQty, int32 ordPrice) {
    OesOrdReqT          ordReq = {NULLOBJ_OES_ORD_REQ};

    SLOG_ASSERT2(pOrdChannel
            && mktId > 0 && mktId < __OES_MKT_ID_MAX
            && pSecurityId && ordType < __OES_ORD_TYPE_FOK_MAX
            && bsType > 0 && bsType < __OES_BS_TYPE_MAX_TRADING
            && ordQty > 0 && ordPrice >= 0,
            "pOrdChannel[%p], mktId[%hhu], pSecurityId[%s], " \
            "ordType[%hhu], bsType[%hhu], ordQty[%d], ordPrice[%d]",
            pOrdChannel, mktId, pSecurityId ? pSecurityId : "NULL",
            ordType, bsType, ordQty, ordPrice);

    ordReq.clSeqNo = (int32) ++pOrdChannel->lastOutMsgSeq;
    ordReq.mktId = mktId;
    ordReq.ordType = ordType;
    ordReq.bsType = bsType;

    strncpy(ordReq.securityId, pSecurityId, sizeof(ordReq.securityId) - 1);
    if (pInvAcctId) {
        /* 股东账户可不填 */
        strncpy(ordReq.invAcctId, pInvAcctId, sizeof(ordReq.invAcctId) - 1);
    }

    ordReq.ordQty = ordQty;
    ordReq.ordPrice = ordPrice;

    return OesApi_SendOrderReq(pOrdChannel, &ordReq);
}


/**
 * 发送撤单请求
 *
 * @param   pOrdChannel     委托通道的会话信息
 * @param   mktId           被撤委托的市场代码 (必填) @see eOesMarketIdT
 * @param   pSecurityId     被撤委托的股票代码 (选填, 若不为空则校验待撤订单是否匹配)
 * @param   pInvAcctId      被撤委托的股东账户代码 (选填, 若不为空则校验待撤订单是否匹配)
 * @param   origClSeqNo     被撤委托的流水号 (若使用 origClOrdId, 则不必填充该字段)
 * @param   origClEnvId     被撤委托的客户端环境号 (小于等于0, 则使用当前会话的 clEnvId)
 * @param   origClOrdId     被撤委托的客户订单编号 (若使用 origClSeqNo, 则不必填充该字段)
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static inline int32
_OesApiSample_SendOrderCancelReq(OesApiSessionInfoT *pOrdChannel,
        uint8 mktId, const char *pSecurityId, const char *pInvAcctId,
        int32 origClSeqNo, int8 origClEnvId, int64 origClOrdId) {
    OesOrdCancelReqT    cancelReq = {NULLOBJ_OES_ORD_CANCEL_REQ};

    SLOG_ASSERT2(pOrdChannel && mktId > 0 && mktId < __OES_MKT_ID_MAX,
            "pOrdChannel[%p], mktId[%hhu]", pOrdChannel, mktId);

    cancelReq.clSeqNo = (int32) ++pOrdChannel->lastOutMsgSeq;
    cancelReq.mktId = mktId;

    if (pSecurityId) {
        /* 撤单时被撤委托的股票代码可不填 */
        strncpy(cancelReq.securityId, pSecurityId, sizeof(cancelReq.securityId) - 1);
    }

    if (pInvAcctId) {
        /* 撤单时被撤委托的股东账户可不填 */
        strncpy(cancelReq.invAcctId, pInvAcctId, sizeof(cancelReq.invAcctId) - 1);
    }

    cancelReq.origClSeqNo = origClSeqNo;
    cancelReq.origClEnvId = origClEnvId;
    cancelReq.origClOrdId = origClOrdId;

    return OesApi_SendOrderCancelReq(pOrdChannel, &cancelReq);
}


/**
 * 对资金查询返回的资金信息进行处理的回调函数
 *
 * @param   pSessionInfo    会话信息
 * @param   pMsgHead        消息头
 * @param   pMsgBody        消息体数据 @see OesCashAssetItemT
 * @param   pCallbackParams 外部传入的参数
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static int32
_OesApiSample_OnQryCashAssetCallback(OesApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead, void *pMsgBody, OesQryCursorT *pQryCursor,
        void *pCallbackParams) {
    OesCashAssetItemT   *pCashAssetItem = (OesCashAssetItemT *) pMsgBody;

    printf(">>> Recv QryCashRsp: {index[%d], isEnd[%c], " \
            "cashAcctId[%s], currentAvailableBal[%lld], " \
            "currentDrawableBal[%lld]}\n",
            pQryCursor->seqNo, pQryCursor->isEnd ? 'Y' : 'N',
            pCashAssetItem->cashAcctId,
            pCashAssetItem->currentAvailableBal,
            pCashAssetItem->currentDrawableBal);

    return 0;
}


/**
 * 查询资金
 *
 * @param   pQryChannel     查询通道的会话信息
 * @param   pCashAcctId     资金账户代码
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static inline int32
_OesApiSample_QueryCashAsset(OesApiSessionInfoT *pQryChannel,
        const char *pCashAcctId) {
    OesQryCashAssetFilterT
                        qryFilter = {NULLOBJ_OES_QRY_CASH_ASSET_FILTER};
    int32               ret = 0;

    SLOG_ASSERT(pQryChannel);

    if (pCashAcctId) {
        strncpy(qryFilter.cashAcctId, pCashAcctId,
                sizeof(qryFilter.cashAcctId) - 1);
    }

    ret = OesApi_QueryCashAsset(pQryChannel, &qryFilter,
            _OesApiSample_OnQryCashAssetCallback, NULL);
    if (unlikely(ret < 0)) {
        SLOG_ERROR("Query stock holding failure! " \
                "ret[%d], pCashAcctId[%s]",
                ret, pCashAcctId ? pCashAcctId : "NULL");
        return ret;
    } else {
        SLOG_DEBUG("Query cash asset success! total count: [%d]", ret);
    }

    return 0;
}


/**
 * 对股票持仓查询返回的持仓信息进行处理的回调函数
 *
 * @param   pSessionInfo    会话信息
 * @param   pMsgHead        消息头
 * @param   pMsgBody        消息体数据 @see OesStkHoldingItemT
 * @param   pCallbackParams 外部传入的参数
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static int32
_OesApiSample_OnQryStkHoldingCallback(OesApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead, void *pMsgBody, OesQryCursorT *pQryCursor,
        void *pCallbackParams) {
    OesStkHoldingItemT  *pHoldingItem = (OesStkHoldingItemT *) pMsgBody;

    printf(">>> Recv QryStkHoldingRsp: {index[%d], isEnd[%c], " \
            "invAcctId[%s], securityId[%s], mktId[%hhu], sellAvlHld[%lld]}\n",
            pQryCursor->seqNo, pQryCursor->isEnd ? 'Y' : 'N',
            pHoldingItem->invAcctId, pHoldingItem->securityId,
            pHoldingItem->mktId, pHoldingItem->sellAvlHld);

    return 0;
}


/**
 * 查询股票持仓
 *
 * @param   pQryChannel     查询通道的会话信息
 * @param   mktId           市场代码 @see eOesMarketIdT
 * @param   pSecurityId     股票代码 (char[6]/char[8])
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static inline int32
_OesApiSample_QueryStkHolding(OesApiSessionInfoT *pQryChannel,
        uint8 mktId, const char *pSecurityId) {
    OesQryStkHoldingFilterT
                        qryFilter = {NULLOBJ_OES_QRY_STK_HOLDING_FILTER};
    int32               ret = 0;

    SLOG_ASSERT2(pQryChannel && mktId < __OES_MKT_ID_MAX,
            "pOrdChannel[%p], mktId[%hhu]", pQryChannel, mktId);

    qryFilter.mktId = mktId;
    if (pSecurityId) {
        strncpy(qryFilter.securityId, pSecurityId,
                sizeof(qryFilter.securityId) - 1);
    }

    ret = OesApi_QueryStkHolding(pQryChannel, &qryFilter,
            _OesApiSample_OnQryStkHoldingCallback, NULL);
    if (unlikely(ret < 0)) {
        SLOG_ERROR("Query stock holding failure! " \
                "ret[%d], mktId[%hhu], pSecurityId[%s]",
                ret, mktId, pSecurityId ? pSecurityId : "NULL");
        return ret;
    } else {
        SLOG_DEBUG("Query stock holding success! total count: [%d]", ret);
    }

    return 0;
}


/**
 * 对执行报告消息进行处理的回调函数
 *
 * @param   pRptChannel     回报通道的会话信息
 * @param   pMsgHead        消息头
 * @param   pMsgBody        消息体数据
 * @param   pCallbackParams 外部传入的参数
 * @return  大于等于0，成功；小于0，失败（错误号）
 */
static inline int32
_OesApiSample_HandleReportMsg(OesApiSessionInfoT *pRptChannel,
        SMsgHeadT *pMsgHead, void *pMsgBody, void *pCallbackParams) {
    OesRspMsgBodyT      *pRspMsg = (OesRspMsgBodyT *) pMsgBody;
    OesRptMsgT          *pRptMsg = &pRspMsg->rptMsg;

    assert(pRptChannel && pMsgHead && pRspMsg);

    switch (pMsgHead->msgId) {
    case OESMSG_RPT_ORDER_INSERT:               /* OES委托已生成 (已通过风控检查) */
        printf(">>> Recv OrdInsertRsp: {clSeqNo: %d, clOrdId: %lld}\n",
                pRptMsg->rptBody.ordInsertRsp.clSeqNo,
                pRptMsg->rptBody.ordInsertRsp.clOrdId);
        break;

    case OESMSG_RPT_BUSINESS_REJECT:            /* OES业务拒绝 (未通过风控检查等) */
        printf(">>> Recv OrdRejectRsp: {clSeqNo: %d, ordRejReason: %d}\n",
                pRptMsg->rptBody.ordRejectRsp.clSeqNo,
                pRptMsg->rptHead.ordRejReason);
        break;

    case OESMSG_RPT_ORDER_REPORT:               /* 交易所委托回报 (包括交易所委托拒绝、委托确认和撤单完成通知) */
        printf(">>> Recv OrdCnfm: {clSeqNo: %d, clOrdId: %lld}\n",
                pRptMsg->rptBody.ordCnfm.clSeqNo,
                pRptMsg->rptBody.ordCnfm.clOrdId);
        break;

    case OESMSG_RPT_TRADE_REPORT:               /* 交易所成交回报 */
        printf(">>> Recv TrdCnfm: {clSeqNo: %d, clOrdId: %lld}\n",
                pRptMsg->rptBody.trdCnfm.clSeqNo,
                pRptMsg->rptBody.trdCnfm.clOrdId);
        break;

    case OESMSG_RPT_CASH_ASSET_VARIATION:       /* 资金变动信息 */
        printf(">>> Recv CashAsset: {cashAcctId: %s, currentAvailableBal: %lld}\n",
                pRptMsg->rptBody.cashAssetRpt.cashAcctId,
                pRptMsg->rptBody.cashAssetRpt.currentAvailableBal);
        break;

    case OESMSG_RPT_STOCK_HOLDING_VARIATION:    /* 持仓变动信息 (股票) */
        printf(">>> Recv StkHolding: {invAcctId: %s, sellAvlHld: %lld}\n",
                pRptMsg->rptBody.stkHoldingRpt.invAcctId,
                pRptMsg->rptBody.stkHoldingRpt.sellAvlHld);
        break;

    case OESMSG_RPT_FUND_TRSF_REJECT:           /* 出入金委托响应-业务拒绝 */
        printf(">>> Recv FundTrsfReject: {cashAcctId: %s, rejReason: %d}\n",
                pRptMsg->rptBody.fundTrsfRejectRsp.cashAcctId,
                pRptMsg->rptBody.fundTrsfRejectRsp.rejReason);
        break;

    case OESMSG_RPT_FUND_TRSF_REPORT:           /* 出入金委托执行报告 */
        printf(">>> Recv FundTrsfReport: {cashAcctId: %s, trsfStatus: %hhu}\n",
                pRptMsg->rptBody.fundTrsfCnfm.cashAcctId,
                pRptMsg->rptBody.fundTrsfCnfm.trsfStatus);
        break;

    case OESMSG_RPT_REPORT_SYNCHRONIZATION:     /* 回报同步响应 */
        printf(">>> Recv report synchronization: " \
                "{subscribeEnvId: %hhd, subscribeRptTypes: %d, lastRptSeqNum: %lld}\n",
                pRspMsg->reportSynchronizationRsp.subscribeEnvId,
                pRspMsg->reportSynchronizationRsp.subscribeRptTypes,
                pRspMsg->reportSynchronizationRsp.lastRptSeqNum);
        break;

    case OESMSG_SESS_HEARTBEAT:
        printf(">>> Recv heartbeat message.\n");
        break;

    default:
        fprintf(stderr, "Invalid message type! msgId[0x%02X]\n",
                pMsgHead->msgId);
        break;
    }

    return 0;
}


/**
 * 超时检查处理
 *
 * @param   pRptChannel     回报通道的会话信息
 * @return  等于0，运行正常，未超时；大于0，已超时，需要重建连接；小于0，失败（错误号）
 */
static inline int32
_OesApiSample_OnTimeout(OesApiClientEnvT *pClientEnv) {
    OesApiSessionInfoT  *pRptChannel = &pClientEnv->rptChannel;
    int64               recvInterval = 0;

    if (pRptChannel->heartBtInt > 0) {
        recvInterval = time((time_t *) NULL) - OesApi_GetLastRecvTime(pRptChannel);
        if (recvInterval > pRptChannel->heartBtInt * 2) {
            SLOG_ERROR("会话已超时, 将主动断开与服务器[%s:%d]的连接! " \
                    "lastRecvTime: [%lld], lastSendTime: [%lld], " \
                    "heartBtInt: [%d], recvInterval: [%lld]",
                    pRptChannel->channel.remoteAddr,
                    pRptChannel->channel.remotePort,
                    (int64) pRptChannel->lastRecvTime.tv_sec,
                    (int64) pRptChannel->lastSendTime.tv_sec,
                    pRptChannel->heartBtInt, recvInterval);
            return ETIMEDOUT;
        }
    }

    return 0;
}


/**
 * 回报采集处理 (可以做为线程的主函数运行)
 *
 * @param   pRptChannel     回报通道的会话信息
 * @return  TRUE 处理成功; FALSE 处理失败
 */
void*
OesApiSample_ReportThreadMain(OesApiClientEnvT *pClientEnv) {
    static const int32  THE_TIMEOUT_MS = 1000;

    OesApiSessionInfoT  *pRptChannel = &pClientEnv->rptChannel;
    volatile int32      *pThreadTerminatedFlag = &pRptChannel->__customFlag;
    int32               ret = 0;

    while (! *pThreadTerminatedFlag) {
        /* 等待回报消息到达, 并通过回调函数对消息进行处理 */
        ret = OesApi_WaitReportMsg(pRptChannel, THE_TIMEOUT_MS,
                _OesApiSample_HandleReportMsg, NULL);
        if (unlikely(ret < 0)) {
            if (likely(SPK_IS_NEG_ETIMEDOUT(ret))) {
                /* 执行超时检查 (检查会话是否已超时) */
                if (likely(_OesApiSample_OnTimeout(pClientEnv) == 0)) {
                    continue;
                }

                /* 会话已超时 */
                goto ON_ERROR;
            }

            if (SPK_IS_NEG_EPIPE(ret)) {
                /* 连接已断开 */
            }
            goto ON_ERROR;
        }
    }

    *pThreadTerminatedFlag = -1;
    return (void *) TRUE;

ON_ERROR:
    *pThreadTerminatedFlag = -1;
    return (void *) FALSE;
}


/**
 * API接口库示例程序的主函数
 */
int32
OesApiSample_Main() {
    static const char   THE_CONFIG_FILE_NAME[] = "oes_client_sample.conf";
    OesApiClientEnvT    cliEnv = {NULLOBJ_OESAPI_CLIENT_ENV};

    /* 初始化客户端环境 (配置文件参见: oes_client_sample.conf) */
    if (! OesApi_InitAll(&cliEnv, THE_CONFIG_FILE_NAME,
            OESAPI_CFG_DEFAULT_SECTION_LOGGER, OESAPI_CFG_DEFAULT_SECTION,
            OESAPI_CFG_DEFAULT_KEY_ORD_ADDR, OESAPI_CFG_DEFAULT_KEY_RPT_ADDR,
            OESAPI_CFG_DEFAULT_KEY_QRY_ADDR, 0, (int32 *) NULL)) {
        return -1;
    }

#if ! (defined (__WINDOWS__) || defined (__MINGW__))
    {
        pthread_t       rptThreadId;
        int32           ret = 0;

        /* 创建回报接收线程 */
        ret = pthread_create(&rptThreadId, NULL,
                (void* (*)(void *)) OesApiSample_ReportThreadMain,
                &cliEnv);
        if (unlikely(ret != 0)) {
            SLOG_ERROR("创建回报接收线程失败! error[%d]", ret);
            goto ON_ERROR;
        }
    }
#else
    {
        /* 创建回报接收线程 */
        CreateThread(NULL, 0,
                (LPTHREAD_START_ROUTINE) OesApiSample_ReportThreadMain,
                (LPVOID) &cliEnv, 0, NULL);
    }
#endif


    /* 查询样例 */
    {
        /* 查询 所有关联资金账户的资金信息 */
        _OesApiSample_QueryCashAsset(&cliEnv.qryChannel, NULL);

        /* 查询 指定资金账户的资金信息 */
        /* _OesApiSample_QueryCashAsset(&cliEnv.qryChannel, "指定资金账户"); */

        /* 查询 上证 600000 股票的持仓 */
        _OesApiSample_QueryStkHolding(&cliEnv.qryChannel, OES_MKT_ID_SH_A,
                "600000");

        /* 查询 上证 所有股票持仓 */
        _OesApiSample_QueryStkHolding(&cliEnv.qryChannel, OES_MKT_ID_SH_A,
                NULL);

        /* 查询 沪深两市 所有股票持仓 */
        _OesApiSample_QueryStkHolding(&cliEnv.qryChannel, OES_MKT_ID_UNDEFINE,
                NULL);
    }

    /* 委托样例 */
    {
        /* 以 12.67元 购买 浦发银行(600000) 100股 */
        _OesApiSample_SendOrderReq(&cliEnv.ordChannel, OES_MKT_ID_SH_A,
                "600000", NULL, OES_ORD_TYPE_LMT, OES_BS_TYPE_BUY,
                100, 126700);

        /* 以 市价 卖出 平安银行(000001) 200股 */
        _OesApiSample_SendOrderReq(&cliEnv.ordChannel, OES_MKT_ID_SZ_A,
                "000001", NULL, OES_ORD_TYPE_SZ_MTL_BEST, OES_BS_TYPE_SELL,
                200, 0);

        /*
         * 以 1.235 的报价做 10万元 GC001(204001)逆回购
         * - 逆回购每张标准券100元，委托份数填 (10万元 除以 100元/张 =) 1000张
         *   上证逆回购报价单位是0.005，份数单位是1000张
         */
        _OesApiSample_SendOrderReq(&cliEnv.ordChannel, OES_MKT_ID_SH_A,
                "204001", NULL, OES_ORD_TYPE_LMT, OES_BS_TYPE_CREDIT_SELL,
                1000, 12350);

        /*
         * 以 4.321 的报价做 1千元 R-001(131810)逆回购
         * - 逆回购每张标准券100元，委托份数填 (1千元 除以 100元/张 =) 10张
         *   深证逆回购报价单位是0.001，份数单位是10张
         */
        _OesApiSample_SendOrderReq(&cliEnv.ordChannel, OES_MKT_ID_SZ_A,
                "131810", NULL, OES_ORD_TYPE_LMT, OES_BS_TYPE_CREDIT_SELL,
                10, 43210);

        /* 以 11.16元 认购 宏达电子(300726) 500股 */
        _OesApiSample_SendOrderReq(&cliEnv.ordChannel, OES_MKT_ID_SZ_A,
                "300726", NULL, OES_ORD_TYPE_LMT, OES_BS_TYPE_SUBSCRIPTION,
                500, 111600);

        /*
         * 新股申购的申购额度的查询方式
         * - 新股申购额度通过 查询股东账户信息(OesApi_QueryInvAcct)接口 返回信息中的
         *   OesInvAcctItemT.subscriptionQuota 来获取
         * - 查询股东账户信息(OesApi_QueryInvAcct)接口 在不指定过滤条件的情况下可以依次返回
         *   沪深两市的股东账户信息，需要通过 OesInvAcctItemT.mktId 来区分不同市场的股东账户
         */
    }

    /* 撤单样例 */
    {
        /* 定义 origOrder 作为模拟的待撤委托 */
        OesOrdCnfmT     origOrder = {NULLOBJ_OES_ORD_CNFM};
        origOrder.mktId = OES_MKT_ID_SH_A;
        origOrder.clEnvId = 0;
        origOrder.clSeqNo = 11;
        origOrder.clOrdId = 111;            /* 真实场景中，待撤委托的clOrdId需要通过回报消息获取 */

        /* 通过待撤委托的 clOrdId 进行撤单 */
        _OesApiSample_SendOrderCancelReq(&cliEnv.ordChannel,
                origOrder.mktId, NULL, NULL, 0, 0, origOrder.clOrdId);

        /*
         * 通过待撤委托的 clSeqNo 进行撤单
         * - 如果撤单时 origClEnvId 填 0，则默认会使用当前客户端实例的 clEnvId 作为
         *   待撤委托的 origClEnvId 进行撤单
         */
        _OesApiSample_SendOrderCancelReq(&cliEnv.ordChannel,
                origOrder.mktId, NULL, NULL,
                origOrder.clSeqNo, origOrder.clEnvId, 0);
    }

    /* 通知并等待回报线程退出 (实际场景中请勿参考此部分代码) */
    {
        /* 等待回报消息接收完成 */
        SPK_SLEEP_MS(1000);

        /* 设置回报线程退出标志 */
        *((volatile int32 *) &cliEnv.rptChannel.__customFlag) = 1;

        /* 回报线程将标志设置为-1后退出, 父进程再释放资源 */
        while(*((volatile int32 *) &cliEnv.rptChannel.__customFlag) != -1) {
            SPK_SLEEP_MS(1000);
        }
    }

    /* 发送注销消息, 并释放会话数据 */
    OesApi_LogoutAll(&cliEnv, TRUE);
    return 0;

ON_ERROR:
    /* 直接关闭连接, 并释放会话数据 */
    OesApi_DestoryAll(&cliEnv);
    return -1;
}


int
main(int argc, char *argv[]) {
    return OesApiSample_Main();
}
