/*****************************************************************************
 * Copyright [2019] 
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *****************************************************************************/

#ifndef CPPSRC_STARQUANT_ENGINE_OESMDENGINE_H_
#define CPPSRC_STARQUANT_ENGINE_OESMDENGINE_H_

#include <Common/datastruct.h>
#include <Engine/IEngine.h>
#include <APIs/Oes/mds_api/mds_api.h>
#include <APIs/Oes/mds_api/parser/mds_protocol_parser.h>
#include <APIs/Oes/mds_api/parser/json_parser/mds_json_parser.h>
#include <APIs/Oes/sutil/time/spk_times.h>
#include <APIs/Oes/sutil/logger/spk_log.h>

#include <mutex>
#include <string>
#include <vector>
#include <memory>

using std::mutex;
using std::string;
using std::vector;

namespace StarQuant
{


class MdsClientSpi {
 public:
    MdsClientSpi() {}
    virtual ~MdsClientSpi() {}

  // callback function
    virtual int32_t OnSnapshotFullRefresh(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsMktDataSnapshotT *pRspBody) = 0;

    virtual int32_t OnL2Trade(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsL2TradeT *pRspBody) = 0;

    virtual int32_t OnL2Order(
    MdsApiSessionInfoT *pSessionInfo,
    SMsgHeadT *pMsgHead,
    MdsL2OrderT *pRspBody) = 0;

    virtual int32_t OnTradingSessionStatus(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsTradingSessionStatusMsgT *pRspBody) = 0;

    virtual int32_t OnSecurityStatus(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsSecurityStatusMsgT *pRspBody) = 0;

    virtual int32_t OnMktDataRequestRsp(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsMktDataRequestRspT *pMsgBody) = 0;

    static int32_t OnTimeout(MdsApiSessionInfoT *pSessionInfo) {
                /*
        int64               recvInterval = 0;

        SLOG_ASSERT(pSessionInfo);

        recvInterval = STime_GetSysTime() - MdsApi_GetLastRecvTime(pSessionInfo);
        if (unlikely(pSessionInfo->heartBtInt > 0
                && recvInterval > pSessionInfo->heartBtInt * 2)) {
            SLOG_ERROR("会话已超时, 将主动断开与服务器[%s:%d]的连接! " \
                    "lastRecvTime[%lld], lastSendTime[%lld], " \
                    "heartBtInt[%d], recvInterval[%lld]",
                    pSessionInfo->channel.remoteAddr,
                    pSessionInfo->channel.remotePort,
                    MdsApi_GetLastRecvTime(pSessionInfo),
                    MdsApi_GetLastSendTime(pSessionInfo),
                    pSessionInfo->heartBtInt, recvInterval);
            return ETIMEDOUT;
        }
        */
        return 0;
    }


};

class MdsClientApi {
 public:
    MdsClientApi() {
        cliEnv = {NULLOBJ_MDSAPI_CLIENT_ENV};
    }
    virtual ~MdsClientApi() {
        // pthread_exit(NULL);
    }

    int32_t Init(const char* conf_file) {
        if (!MdsApi_InitAll(&cliEnv, conf_file,
            MDSAPI_CFG_DEFAULT_SECTION_LOGGER, MDSAPI_CFG_DEFAULT_SECTION,
            MDSAPI_CFG_DEFAULT_KEY_TCP_ADDR, MDSAPI_CFG_DEFAULT_KEY_QRY_ADDR,
            (char *) NULL, (char *) NULL, (char *) NULL, (char *) NULL)) {
            return -1;
        }
        return 0;
    }
    void RegisterSpi(MdsClientSpi* spi) {
        _spi = spi;
    }
    void Logout(bool release = true) {
        MdsApi_LogoutAll(&cliEnv, release);
    }
    void Release() {
        MdsApi_DestoryAll(&cliEnv);
        for (auto pt : _threads) {
            pthread_join(pt, NULL);
        }
        _threads.clear();
    }

    std::string GetApiVersion() {
        string tmp = "0.15.5, 20180220";
        return tmp;
    }

    static inline int32 _MdsApiSample_HandleMsg(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        void *pMsgBody,
        void *pCallbackParams) {
      MdsMktRspMsgBodyT   *pRspMsg = (MdsMktRspMsgBodyT *) pMsgBody;

      /*
      * 根据消息类型对行情消息进行处理
      */
      switch (pMsgHead->msgId) {
      case MDS_MSGTYPE_L2_TRADE:
         /* 处理Level2逐笔成交消息 */
         return _spi->OnL2Trade(
                  pSessionInfo, pMsgHead, &pRspMsg->trade);

      case MDS_MSGTYPE_L2_ORDER:
         /* 处理Level2逐笔委托消息 */
         return _spi->OnL2Order(
                  pSessionInfo, pMsgHead, &pRspMsg->order);

      case MDS_MSGTYPE_L2_MARKET_DATA_SNAPSHOT:
      case MDS_MSGTYPE_L2_BEST_ORDERS_SNAPSHOT:
      case MDS_MSGTYPE_L2_MARKET_DATA_INCREMENTAL:
      case MDS_MSGTYPE_L2_BEST_ORDERS_INCREMENTAL:
      case MDS_MSGTYPE_L2_MARKET_OVERVIEW:
      case MDS_MSGTYPE_L2_VIRTUAL_AUCTION_PRICE:
      case MDS_MSGTYPE_MARKET_DATA_SNAPSHOT_FULL_REFRESH:
      case MDS_MSGTYPE_OPTION_SNAPSHOT_FULL_REFRESH:
      case MDS_MSGTYPE_INDEX_SNAPSHOT_FULL_REFRESH:
         /* 处理证券行情全幅消息 */
         return _spi->OnSnapshotFullRefresh(
                  pSessionInfo, pMsgHead, &pRspMsg->mktDataSnapshot);

      case MDS_MSGTYPE_SECURITY_STATUS:
         /* 处理(深圳)证券状态消息 */
         return _spi->OnSecurityStatus(
                  pSessionInfo, pMsgHead, &pRspMsg->securityStatus);

      case MDS_MSGTYPE_TRADING_SESSION_STATUS:
         /* 处理(上证)市场状态消息 */
         return _spi->OnTradingSessionStatus(
                  pSessionInfo, pMsgHead, &pRspMsg->trdSessionStatus);

      case MDS_MSGTYPE_HEARTBEAT:
         /* 直接忽略心跳消息即可 */
         break;

      case MDS_MSGTYPE_MARKET_DATA_REQUEST:
         /* 处理行情订阅请求的应答消息 */
         return _spi->OnMktDataRequestRsp(pSessionInfo, pMsgHead,
                  &pRspMsg->mktDataRequestRsp);

      default:
         SLOG_ERROR("无效的消息类型! msgId[0x%02X], server[%s:%d]",
                  pMsgHead->msgId, pSessionInfo->channel.remoteAddr,
                  pSessionInfo->channel.remotePort);
         return EFTYPE;
      }

      return 0;
    }

    static void* MdsApiSample_TcpThreadMain(MdsApiSessionInfoT *pTcpChannel) {
        static const int32  THE_TIMEOUT_MS = 5000;
        int32               ret = 0;

        SLOG_ASSERT(pTcpChannel);

        while (1) {
            /* 等待行情消息到达, 并通过回调函数对消息进行处理 */
            ret = MdsApi_WaitOnMsg(pTcpChannel, THE_TIMEOUT_MS,
                    _MdsApiSample_HandleMsg, NULL);
            if (unlikely(ret < 0)) {
                if (likely(SPK_IS_NEG_ETIMEDOUT(ret))) {
                    /* 执行超时检查 (检查会话是否已超时) */
                    if (likely(_spi->OnTimeout(pTcpChannel) == 0)) {
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

        return (void *) TRUE;

    ON_ERROR:
        return (void *) FALSE;
    }

    int32_t createTcpThread() {
        pthread_t       tcpThreadId;
        int32           ret = 0;
        if (MdsApi_IsValidTcpChannel(&cliEnv.tcpChannel)) {
            ret = pthread_create(&tcpThreadId, NULL,
                    (void* (*)(void *)) MdsApiSample_TcpThreadMain,
                    &cliEnv.tcpChannel);
            _threads.push_back(tcpThreadId);
            if (unlikely(ret != 0)) {
                SLOG_ERROR("创建行情接收线程失败! error[%d]", ret);
                Release();
                return -1;
            }
            return 0;
        }
        return -2;
    }

    int32_t createQueryThread(){};

    int32_t createUdpThread(){};

    int32_t createCustomizedUdpThread(){};

    int32_t SubscribeByString(
        const char *pSecurityListStr,
        const char *pDelim,
        eMdsExchangeIdT exchangeId,
        eMdsSecurityTypeT securityType,
        eMdsSubscribeModeT subMode,
        int32 dataTypes) {
        if (MdsApi_IsValidTcpChannel(&cliEnv.tcpChannel)) {
            return  MdsApi_SubscribeByString(
                &cliEnv.tcpChannel,
                pSecurityListStr,
                pDelim,
                exchangeId,
                securityType,
                subMode,
                dataTypes);
        }
        return -1;
    }

 private:
    MdsApiClientEnvT cliEnv;
    vector<pthread_t> _threads;
    static MdsClientSpi* _spi;
};



class OesMDEngine : public IEngine, MdsClientSpi {
 public:
    string name_;
    Gateway oesacc_;

    OesMDEngine();
    ~OesMDEngine();

    virtual void init();
    virtual void start();
    virtual void stop();

    virtual bool connect();
    virtual bool disconnect();
    void releaseapi();
    void reset();
    void switchday() {}
    void timertask();
    void processbuf();
   //  marketdata
    void subscribe(const vector<string>& symbols, SymbolType st = ST_Xtp);
    void unsubscribe(const vector<string>& symbols, SymbolType st = ST_Xtp);
   //  OnTickByTick
    void subscribeTickByTick(const vector<string>& symbols, SymbolType st = ST_Xtp);
    void unsubscribeTickByTick(const vector<string>& symbols, SymbolType st = ST_Xtp);
   // query


 public:
    virtual int32_t OnSnapshotFullRefresh(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsMktDataSnapshotT *pRspBody);

    virtual int32_t OnL2Trade(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsL2TradeT *pRspBody);

    virtual int32_t OnL2Order(
    MdsApiSessionInfoT *pSessionInfo,
    SMsgHeadT *pMsgHead,
    MdsL2OrderT *pRspBody);

    virtual int32_t OnTradingSessionStatus(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsTradingSessionStatusMsgT *pRspBody);

    virtual int32_t OnSecurityStatus(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsSecurityStatusMsgT *pRspBody);

    virtual int32_t OnMktDataRequestRsp(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsMktDataRequestRspT *pMsgBody);

 private:
    uint8_t _client_id;
    int32_t loginReqId_;
    int32_t reqId_;
    std::unique_ptr<MdsClientApi> api_;
    bool apiinited_;
    bool inconnectaction_;
    bool autoconnect_;
    bool subscribeAllMarketData_;
    bool subscribeAllMarketTBT_;
    vector<string> lastsubs_;
    vector<string> lastsubstbt_;
    int32_t timercount_;
    int32_t msgqMode_;   // dontwaitmode flags

    string oesTicker2Full(const string& ticker);
    string fullTicker2Oes(const string& ticker);

};
}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_ENGINE_OESMDENGINE_H_
