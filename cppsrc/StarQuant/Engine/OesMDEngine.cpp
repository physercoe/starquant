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

#include <Engine/OesMDEngine.h>
#include <Common/util.h>
#include <Common/logger.h>
#include <Common/datastruct.h>
#include <Common/config.h>
#include <Data/datamanager.h>

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <fmt/format.h>

#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <vector>
#include <sstream>
#include <limits>
#include <memory>
#include <mutex>
#include <algorithm>
#include <boost/locale.hpp>
#include <boost/algorithm/string.hpp>




using namespace std;

namespace StarQuant {
// extern std::atomic<bool> gShutdown;

MdsClientSpi* MdsClientApi::_spi = nullptr;

OesMDEngine ::OesMDEngine()
    : _client_id(0)
    , loginReqId_(0)
    , reqId_(0)
    , apiinited_(false)
    , inconnectaction_(false)
    , autoconnect_(false)
    , timercount_(0)
    , msgqMode_(0) {
    name_ = "OES.MD";
    init();
}

OesMDEngine::~OesMDEngine() {
    if (estate_ != STOP)
        stop();
    releaseapi();
}

void OesMDEngine::releaseapi() {
    if (api_ != nullptr) {
        // this->api_->Join();
        // make sure ctpapi is idle
        this->api_->RegisterSpi(nullptr);
        if (apiinited_)
            this->api_->Release();  // api must init() or will segfault
        this->api_ = nullptr;
    }
}

void OesMDEngine::reset() {
    disconnect();
    releaseapi();
    CConfig::instance().readConfig();
    init();
    LOG_DEBUG(logger, name_ << " reset");
}

void OesMDEngine::init() {
    reqId_ = 0;
    lastsubs_.clear();
    lastsubstbt_.clear();
    subscribeAllMarketData_ = false;
    subscribeAllMarketTBT_ = false;
    msgqMode_ = 0;
    if (logger == nullptr) {
        logger = SQLogger::getLogger("MDEngine.XTP");
    }

    if (messenger_ == nullptr) {
        messenger_ = std::make_unique<CMsgqEMessenger>(name_, CConfig::instance().SERVERSUB_URL);
        msleep(100);
    }
    oesacc_ = CConfig::instance()._gatewaymap[name_];
    string path = CConfig::instance().logDir() + "/oes/md";
    boost::filesystem::path dir(path.c_str());
    boost::filesystem::create_directory(dir);
    _client_id = oesacc_.intid;
    // 创建API对象
    this->api_ = make_unique<MdsClientApi>();
    this->api_->RegisterSpi(this);
    estate_ = DISCONNECTED;
    auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                MSG_TYPE_ENGINE_STATUS,
                to_string(estate_));
    messenger_->send(pmsgs);
    autoconnect_ = CConfig::instance().autoconnect;
    LOG_DEBUG(logger, name_ << " created, api version:" << MdsApi_GetApiVersion());
}

void OesMDEngine::stop() {
    int32_t tmp = disconnect();
    estate_ = EState::STOP;
    auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                    MSG_TYPE_ENGINE_STATUS,
                    to_string(estate_));
    messenger_->send(pmsgs);
    LOG_DEBUG(logger, name_ << "  stoped");
}

void OesMDEngine::start() {
    while (estate_ != EState::STOP) {
        auto pmsgin = messenger_->recv(msgqMode_);
        bool processmsg = ((pmsgin != nullptr) \
        && (startwith(pmsgin->destination_, DESTINATION_ALL) || (pmsgin->destination_ == name_)));
        // if (pmsgin == nullptr || (pmsgin->destination_ != name_ && ! startwith(pmsgin->destination_,DESTINATION_ALL)) ) 
        // 	continue;
        if (processmsg) {
            switch (pmsgin->msgtype_) {
                case MSG_TYPE_ENGINE_CONNECT:
                    if (connect()) {
                        auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
                            MSG_TYPE_INFO_ENGINE_MDCONNECTED, "XTP.MD connected.");
                        messenger_->send(pmsgout, 1);
                    }
                    break;
                case MSG_TYPE_ENGINE_DISCONNECT:
                    disconnect();
                    break;
                case MSG_TYPE_SUBSCRIBE_MARKET_DATA:
                    if (estate_ == LOGIN_ACK) {
                        auto pmsgin2 = static_pointer_cast<SubscribeMsg>(pmsgin);
                        subscribe(pmsgin2->data_, pmsgin2->symtype_);
                    } else {
                        LOG_DEBUG(logger,name_ << "  is not connected,can not subscribe!");
                        auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
                            MSG_TYPE_ERROR_ENGINENOTCONNECTED,
                            "oes md is not connected,can not subscribe");
                        messenger_->send(pmsgout);
                    }
                    break;
                case MSG_TYPE_UNSUBSCRIBE:
                    if (estate_ == LOGIN_ACK){
                        auto pmsgin2 = static_pointer_cast<UnSubscribeMsg>(pmsgin);
                        unsubscribe(pmsgin2->data_, pmsgin2->symtype_);
                    } else {
                        LOG_DEBUG(logger,name_ <<"  is not connected,can not unsubscribe!");
                        auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
                            MSG_TYPE_ERROR_ENGINENOTCONNECTED,
                            "oes md is not connected,can not unsubscribe");
                        messenger_->send(pmsgout);
                    }
                    break;
                case MSG_TYPE_QRY_CONTRACT:
                    break;
                case MSG_TYPE_SUBSCRIBE_ORDER_TRADE:
                    if (estate_ == LOGIN_ACK) {
                        auto pmsgin2 = static_pointer_cast<SubscribeMsg>(pmsgin);
                        subscribeTickByTick(pmsgin2->data_, pmsgin2->symtype_);
                    } else {
                        LOG_DEBUG(logger,name_ << "  is not connected,can not subscribe!");
                        auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
                            MSG_TYPE_ERROR_ENGINENOTCONNECTED,
                            "oes md is not connected,can not subscribetbt");
                        messenger_->send(pmsgout);
                    }
                    break;
                case MSG_TYPE_UNSUBSCRIBE_ORDER_TRADE:
                    if (estate_ == LOGIN_ACK){
                        auto pmsgin2 = static_pointer_cast<UnSubscribeMsg>(pmsgin);
                        unsubscribeTickByTick(pmsgin2->data_, pmsgin2->symtype_);
                    } else {
                        LOG_DEBUG(logger,name_ <<"  is not connected,can not unsubscribe!");
                        auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
                            MSG_TYPE_ERROR_ENGINENOTCONNECTED,
                            "oes md is not connected,can not unsubscribetbt");
                        messenger_->send(pmsgout);
                    }
                    break;
                case MSG_TYPE_ENGINE_STATUS:
                    {
                        auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
                            MSG_TYPE_ENGINE_STATUS,
                            to_string(estate_));
                        messenger_->send(pmsgout);
                    }
                    break;
                case MSG_TYPE_TEST:
                    {
                        auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
                            MSG_TYPE_TEST,
                            "test");
                        messenger_->send(pmsgout);
                        LOG_DEBUG(logger,name_ << " return test msg!");
                    }
                    break;
                case MSG_TYPE_SWITCH_TRADING_DAY:
                    switchday();
                    break;
                case MSG_TYPE_ENGINE_RESET:
                    reset();
                    break;
                default:
                    processbuf();
                    break;
            }
        } else {
            processbuf();
        }
    }
}

////////////////////////////////////////////////////// outgoing function ///////////////////////////////////////
bool OesMDEngine::connect() {
    inconnectaction_ = true;
    int32_t error;
    int32_t count = 0;  // count numbers of tries, two many tries ends
    string conf_file = "mds_client_sample.conf";
    while (estate_ != EState::LOGIN_ACK && estate_ != STOP) {
        switch (estate_) {
            case EState::DISCONNECTED:
                if (!apiinited_) {
                    LOG_INFO(logger, name_ <<" api begin initing env...");
                    error = this->api_->Init(conf_file.c_str());
                    if (error == 0) {
                        estate_ = CONNECT_ACK;
                        apiinited_ = true;
                        auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                            MSG_TYPE_ENGINE_STATUS,
                            to_string(estate_));
                        messenger_->send(pmsgs);
                    } else {
                        estate_ = CONNECTING;
                        LOG_ERROR(logger, name_ << " init env error.");
                    }
                }
                estate_ = CONNECT_ACK;
                break;
            case EState::CONNECTING:
                msleep(1000);
                count++;
                estate_ = DISCONNECTED;
                break;
            case EState::CONNECT_ACK:
                LOG_INFO(logger, name_ <<" api begin create tcp thread...");
                error = this->api_->createTcpThread();
                if (error == 0) {
                    estate_ = LOGIN_ACK;
                    LOG_INFO(logger, name_ <<" tcp thread created.");

                } else {
                    estate_ = DISCONNECTED;
                    apiinited_ = false;
                    LOG_ERROR(logger, name_ << " create tcp thread error.");
                }
                {auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                    MSG_TYPE_ENGINE_STATUS,
                    to_string(estate_));
                messenger_->send(pmsgs);}
                break;
            case EState::LOGINING:
                msleep(500);
                break;
            default:
                msleep(100);
                break;
        }
        if (count >10) {
            LOG_ERROR(logger,name_ << " connect too many tries fails, give up connecting");
            // estate_ = EState::DISCONNECTED;
            inconnectaction_ = false;
            return false;
        }
    }
    inconnectaction_ = false;
    //  qry all tickers only once everyday
    // if (!DataManager::instance().xtpContractUpdated_) {
    //     this->api_->QueryAllTickers(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH);
    //     this->api_->QueryAllTickers(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ);
    //     DataManager::instance().xtpContractUpdated_ = true;
    // }
    if (lastsubs_.size())
        subscribe(lastsubs_);
    if (lastsubstbt_.size())
        subscribeTickByTick(lastsubstbt_);
    if (subscribeAllMarketData_)
        subscribe(lastsubs_, SymbolType::ST_Full);
    if (subscribeAllMarketTBT_)
        subscribeTickByTick(lastsubstbt_, SymbolType::ST_Full);

    return true;
}

bool OesMDEngine::disconnect() {
    if (estate_ == LOGIN_ACK) {
        LOG_INFO(logger, name_ << "  logouting ..");
        this->api_->Logout();
        estate_ = EState::DISCONNECTED;
    } else {
        LOG_DEBUG(logger, name_ << "  is not connected(logined), cannot disconnect!");
        // make sure ctpapi callback done
        // msleep(500);
        return false;
    }
}

void OesMDEngine::subscribe(const vector<string>& symbol,SymbolType st) {
    int32_t error;
    //  subscribe all 
    if (st == SymbolType::ST_Full) {
        error = this->api_->SubscribeByString(
            (char *) NULL, (char *) NULL,
            MDS_EXCH_SZSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L1_SNAPSHOT
            | MDS_SUB_DATA_TYPE_L2_SNAPSHOT);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribe SZSE error " << error);
        }
        error = this->api_->SubscribeByString(
            (char *) NULL, (char *) NULL,
            MDS_EXCH_SSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L1_SNAPSHOT
            | MDS_SUB_DATA_TYPE_L2_SNAPSHOT);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribe SSE error " << error);
        }
        subscribeAllMarketData_ = true;
        return;
    }

    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    string sout;
    for (int32_t i = 0; i < nCount; i++) {
        if (find(lastsubs_.begin(), lastsubs_.end(), symbol[i]) == lastsubs_.end())
            lastsubs_.push_back(symbol[i]);
        string ticker = fullTicker2Oes(symbol[i]);
        sout += ticker + string(",");
    }
    error = this->api_->SubscribeByString(
            sout.c_str(), (char *) NULL,
            MDS_EXCH_SZSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L1_SNAPSHOT
            | MDS_SUB_DATA_TYPE_L2_SNAPSHOT);
    if (error != 0) {
        LOG_ERROR(logger, name_ << " subscribe  error " << error);
    }
    LOG_INFO(logger, name_ << " subcribe " << nCount << "|" << sout << ".");
}

void OesMDEngine::unsubscribe(const vector<string>& symbol,SymbolType st) {
    int32_t error;
    //  unsubscribe all 
    if (st == SymbolType::ST_Full) {
        string tmp = "";
        error = this->api_->SubscribeByString(
            tmp.c_str(), (char *) NULL,
            MDS_EXCH_SZSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L1_SNAPSHOT
            | MDS_SUB_DATA_TYPE_L2_SNAPSHOT);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribe SZSE error " << error);
        }
        error = this->api_->SubscribeByString(
            tmp.c_str(), (char *) NULL,
            MDS_EXCH_SSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L1_SNAPSHOT
            | MDS_SUB_DATA_TYPE_L2_SNAPSHOT);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribe SSE error " << error);
        }
        subscribeAllMarketData_ = false;
        return;
    }
    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    for (int32_t i = 0; i < nCount; i++) {
        for (auto it = lastsubs_.begin(); it != lastsubs_.end();) {
            if (*it == symbol[i]) {
                it = lastsubs_.erase(it);
            } else {
                ++it;
            }
        }
    }    
    subscribe(lastsubs_);
}


//  OnTickByTick
void OesMDEngine::subscribeTickByTick(const vector<string>& symbol, SymbolType st) {
    int32_t error;
    //  subscribe all 
    if (st == SymbolType::ST_Full) {
        error = this->api_->SubscribeByString(
            (char *) NULL, (char *) NULL,
            MDS_EXCH_SZSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L2_TRADE | MDS_SUB_DATA_TYPE_L2_ORDER);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribetbt SZSE error " << error);
        }
        error = this->api_->SubscribeByString(
            (char *) NULL, (char *) NULL,
            MDS_EXCH_SSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L2_TRADE | MDS_SUB_DATA_TYPE_L2_ORDER);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribetbt SSE error " << error);
        }
        subscribeAllMarketTBT_ = true;
        return;
    }

    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    string sout;
    for (int32_t i = 0; i < nCount; i++) {
        if (find(lastsubstbt_.begin(), lastsubstbt_.end(), symbol[i]) == lastsubstbt_.end())
            lastsubstbt_.push_back(symbol[i]);
        string ticker = fullTicker2Oes(symbol[i]);
        sout += ticker + string(",");
    }
    error = this->api_->SubscribeByString(
            sout.c_str(), (char *) NULL,
            MDS_EXCH_SZSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L2_TRADE | MDS_SUB_DATA_TYPE_L2_ORDER);
    if (error != 0) {
        LOG_ERROR(logger, name_ << " subscribetbt  error " << error);
    }
    LOG_INFO(logger, name_ << " subcribetbt " << nCount << "|" << sout << ".");

}
void OesMDEngine::unsubscribeTickByTick(const vector<string>& symbol, SymbolType st) {
    int32_t error;
    //  unsubscribe all 
    if (st == SymbolType::ST_Full) {
        string tmp = "";
        error = this->api_->SubscribeByString(
            tmp.c_str(), (char *) NULL,
            MDS_EXCH_SZSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L2_TRADE | MDS_SUB_DATA_TYPE_L2_ORDER);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribe SZSE error " << error);
        }
        error = this->api_->SubscribeByString(
            tmp.c_str(), (char *) NULL,
            MDS_EXCH_SSE, MDS_SECURITY_TYPE_STOCK, MDS_SUB_MODE_SET,
            MDS_SUB_DATA_TYPE_L2_TRADE | MDS_SUB_DATA_TYPE_L2_ORDER);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribe SSE error " << error);
        }
        subscribeAllMarketData_ = false;
        return;
    }
    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    for (int32_t i = 0; i < nCount; i++) {
        for (auto it = lastsubstbt_.begin(); it != lastsubstbt_.end();) {
            if (*it == symbol[i]) {
                it = lastsubstbt_.erase(it);
            } else {
                ++it;
            }
        }
    }
    subscribeTickByTick(lastsubstbt_);
}
// query


void OesMDEngine::timertask() {
    timercount_++;
    // // send status every second 
    // auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
    // 	MSG_TYPE_ENGINE_STATUS,
    // 	to_string(estate_));
    // messenger_->send(pmsgout);

}
void OesMDEngine::processbuf() {
}

/////////////////////////////////////////////// end of outgoing functions ///////////////////////////////////////

////////////////////////////////////////////////////// callback  function ///////////////////////////////////////

inline int32_t _MdsApiSample_PrintMsg(
    MdsApiSessionInfoT *pSessionInfo,
    SMsgHeadT *pMsgHead,
    void *pMsgBody,
    FILE *pOutputFp) {
    char encodeBuf[8192] = {0};
    char *pStrMsg = (char *) NULL;

    if (pSessionInfo->protocolType == SMSG_PROTO_BINARY) {
        /* 将行情消息转换为JSON格式的文本数据 */
        pStrMsg = (char *) MdsJsonParser_EncodeRsp(
                pMsgHead, (MdsMktRspMsgBodyT *) pMsgBody,
                encodeBuf, sizeof(encodeBuf),
                pSessionInfo->channel.remoteAddr);
        if (unlikely(! pStrMsg)) {
            SLOG_ERROR("编码接收到的行情消息失败! "
                    "msgFlag: %hhu, msgType: %hhu, msgSize: %d",
                    pMsgHead->msgFlag, pMsgHead->msgId, pMsgHead->msgSize);
            return NEG(EBADMSG);
        }
    } else {
        pStrMsg = (char *) pMsgBody;
    }

    if (pMsgHead->msgSize > 0) {
        pStrMsg[pMsgHead->msgSize - 1] = '\0';
        fprintf(pOutputFp,
                "{" \
                "\"msgType\":%hhu, " \
                "\"mktData\":%s" \
                "}\n",
                pMsgHead->msgId,
                pStrMsg);
    } else {
        fprintf(pOutputFp,
                "{" \
                "\"msgType\":%hhu, " \
                "\"mktData\":{}" \
                "}\n",
                pMsgHead->msgId);
    }

    return 0;
}


int32_t OesMDEngine::OnSnapshotFullRefresh(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsMktDataSnapshotT *pRspBody) {
    return _MdsApiSample_PrintMsg(pSessionInfo, pMsgHead, pRspBody, stdout);
    }



int32_t OesMDEngine::OnL2Trade(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsL2TradeT *pRspBody) {
    return _MdsApiSample_PrintMsg(pSessionInfo, pMsgHead, pRspBody, stdout);
}


// 订阅行情应答
int32_t OesMDEngine::OnL2Order(
    MdsApiSessionInfoT *pSessionInfo,
    SMsgHeadT *pMsgHead,
    MdsL2OrderT *pRspBody) {
    return _MdsApiSample_PrintMsg(pSessionInfo, pMsgHead, pRspBody, stdout);
}

// 取消订阅行情应答
int32_t OesMDEngine::OnTradingSessionStatus(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsTradingSessionStatusMsgT *pRspBody) {
    return _MdsApiSample_PrintMsg(pSessionInfo, pMsgHead, pRspBody, stdout);
}

int32_t OesMDEngine::OnSecurityStatus(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsSecurityStatusMsgT *pRspBody) {
    return _MdsApiSample_PrintMsg(pSessionInfo, pMsgHead, pRspBody, stdout);
}

int32_t OesMDEngine::OnMktDataRequestRsp(
        MdsApiSessionInfoT *pSessionInfo,
        SMsgHeadT *pMsgHead,
        MdsMktDataRequestRspT *pMsgBody) {
    return _MdsApiSample_PrintMsg(pSessionInfo, pMsgHead,
                pMsgBody, stdout);
}


string OesMDEngine::fullTicker2Oes(const string& full_symbol) {
    string oesticker;
    vector<string> partfull;
    partfull = stringsplit(full_symbol, ' ');
    if (partfull[0] == "SSE") {
        oesticker = partfull[2] + ".SH";
    } else if (partfull[0] == "SSE") {
        oesticker = partfull[2] + ".SZ";
    }
    return oesticker;
}

string OesMDEngine::oesTicker2Full(const string& ticker) {
    // TODO: convert to full
    return ticker;
}
// XTP_EXCHANGE_TYPE OesMDEngine::string2XtpExchange(const string& exchangeid) {
//     XTP_EXCHANGE_TYPE eid = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;
//     if (exchangeid == "SSE") {
//         eid = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;
//     } else if (exchangeid == "SZSE") {
//         eid = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ;
//     }
//     return eid;
// }
// char OesMDEngine::xtpSecType2SQ(XTP_TICKER_TYPE stype) {
//     char sqtype = 'T';
//     switch (stype) {
//         case XTP_TICKER_TYPE::XTP_TICKER_TYPE_STOCK:
//             sqtype = 'T';
//             break;
//         case XTP_TICKER_TYPE::XTP_TICKER_TYPE_INDEX:
//             sqtype = 'Z';
//             break;
//         case XTP_TICKER_TYPE::XTP_TICKER_TYPE_FUND:
//             sqtype = 'J';
//             break;
//         case XTP_TICKER_TYPE::XTP_TICKER_TYPE_BOND:
//             sqtype = 'B';
//             break;
//         case XTP_TICKER_TYPE::XTP_TICKER_TYPE_OPTION:
//             sqtype = 'O';
//             break;
//         case XTP_TICKER_TYPE::XTP_TICKER_TYPE_TECH_STOCK:
//             sqtype = 't';
//             break;
//         default:
//             break;
//     }
//     return sqtype;
// }

}  // namespace StarQuant
