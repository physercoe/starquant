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

#include <Engine/XtpMDEngine.h>
#include <APIs/Xtp/xtp_quote_api.h>
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

XtpMDEngine ::XtpMDEngine()
    : _client_id(0)
    , loginReqId_(0)
    , reqId_(0)
    , apiinited_(false)
    , inconnectaction_(false)
    , autoconnect_(false)
    , timercount_(0)
    , msgqMode_(0) {
    name_ = "XTP.MD";
    init();
}

XtpMDEngine::~XtpMDEngine() {
    if (estate_ != STOP)
        stop();
    releaseapi();
}

void XtpMDEngine::releaseapi() {
    if (api_ != nullptr) {
        // this->api_->Join();
        // make sure ctpapi is idle
        msleep(500);
        this->api_->RegisterSpi(nullptr);
        if (apiinited_)
            this->api_->Release();  // api must init() or will segfault
        this->api_ = nullptr;
    }
}

void XtpMDEngine::reset() {
    disconnect();
    releaseapi();
    CConfig::instance().readConfig();
    init();
    LOG_DEBUG(logger, name_ << " reset");
}

void XtpMDEngine::init() {
    // if (IEngine::msgq_send_ == nullptr){
    // 	lock_guard<mutex> g(IEngine::sendlock_);
    // 	IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
    // }
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
    xtpacc_ = CConfig::instance()._gatewaymap[name_];
    string path = CConfig::instance().logDir() + "/xtp/md";
    boost::filesystem::path dir(path.c_str());
    boost::filesystem::create_directory(dir);
    _client_id = xtpacc_.intid;
    // 创建API对象
    this->api_ = XTP::API::QuoteApi::CreateQuoteApi(_client_id, path.c_str());
    this->api_->RegisterSpi(this);
    estate_ = DISCONNECTED;
    auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                MSG_TYPE_ENGINE_STATUS,
                to_string(estate_));
    messenger_->send(pmsgs);
    apiinited_ = true;
    autoconnect_ = CConfig::instance().autoconnect;
    LOG_DEBUG(logger, name_ << " inited, api version:" << this->api_->GetApiVersion());
    LOG_DEBUG(logger, name_ << " client_id:"<< xtpacc_.intid<< ", "<< unsigned(_client_id));
}

void XtpMDEngine::stop() {
    int32_t tmp = disconnect();
    estate_ = EState::STOP;
    auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                    MSG_TYPE_ENGINE_STATUS,
                    to_string(estate_));
    messenger_->send(pmsgs);
    LOG_DEBUG(logger, name_ << "  stoped");
}

void XtpMDEngine::start() {
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
                            "ctp md is not connected,can not subscribe");
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
                            "ctp md is not connected,can not unsubscribe");
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
                            "ctp md is not connected,can not subscribetbt");
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
                            "ctp md is not connected,can not unsubscribetbt");
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
bool XtpMDEngine::connect() {
    inconnectaction_ = true;
    int32_t error;
    XTPRI errorinfo;
    int32_t count = 0;  // count numbers of tries, two many tries ends
    string mdaddress;
    string ip;
    int32_t port;
    XTP_PROTOCOL_TYPE protocal = XTP_PROTOCOL_TCP;
    while (estate_ != EState::LOGIN_ACK && estate_ != STOP) {
        switch (estate_) {
            case EState::DISCONNECTED:
                if (!apiinited_) {
                    apiinited_ = true;
                }
                estate_ = CONNECT_ACK;
                LOG_INFO(logger, name_ <<" api inited, begin logining...");
                // {auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                //     MSG_TYPE_ENGINE_STATUS,
                //     to_string(estate_));
                // messenger_->send(pmsgs);}
                // count++;
                break;
            case EState::CONNECTING:
                msleep(1000);
                count++;
                estate_ = CONNECT_ACK;
                break;
            case EState::CONNECT_ACK:
                //  only last mdaddress is used
                for (auto it : xtpacc_.md_address) {
                    mdaddress = it;
                }
                ip = extractIp(mdaddress);
                port = extractPort(mdaddress);
                if (startwith(mdaddress, "UDP") || startwith(mdaddress, "udp")) {
                    protocal = XTP_PROTOCOL_UDP;
                    //  SetUDPBufferSize(uint32_t buff_size);
                }
                LOG_DEBUG(logger, name_ <<"login field "<<ip<<" "<<port<<" "<<xtpacc_.userid<<" "<<xtpacc_.password<<" "<<protocal);
                error = this->api_->Login(ip.c_str(), port, xtpacc_.userid.c_str(), xtpacc_.password.c_str(), protocal);
                if (error == 0) {
                    estate_ = LOGIN_ACK;
                    LOG_INFO(logger, name_ <<" logined.");
                    // auto subscribe last securities
                    if (lastsubs_.size())
                        subscribe(lastsubs_);
                    if (lastsubstbt_.size())
                        subscribeTickByTick(lastsubstbt_);
                    if (subscribeAllMarketData_)
                        subscribe(lastsubs_, SymbolType::ST_Full);
                    if (subscribeAllMarketTBT_)
                        subscribeTickByTick(lastsubstbt_, SymbolType::ST_Full);

                } else {
                    estate_ = CONNECTING;
                    errorinfo = *this->api_->GetApiLastError();
                    LOG_ERROR(logger, name_ << " login error:" << errorinfo.error_id<<":"<< errorinfo.error_msg);
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
    if (!DataManager::instance().xtpContractUpdated_) {
        this->api_->QueryAllTickers(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH);
        this->api_->QueryAllTickers(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ);
        DataManager::instance().xtpContractUpdated_ = true;
    }

    return true;
}

bool XtpMDEngine::disconnect() {
    if (estate_ == LOGIN_ACK) {
        LOG_INFO(logger, name_ << "  logouting ..");
        estate_ = EState::LOGOUTING;
        int32_t error = this->api_->Logout();
        if (error != 0) {
            XTPRI errorinfo;
            errorinfo = *this->api_->GetApiLastError();
            LOG_ERROR(logger, name_ << "  logout error:" << errorinfo.error_id <<":"<<errorinfo.error_msg);
            estate_ = EState::LOGIN_ACK;
            // make sure ctpapi callback done before return
            // msleep(500);
            return false;
        }
        // make sure ctpapi callback done
        // msleep(500);
        estate_ = EState::DISCONNECTED;
        auto pmsg = make_shared<InfoMsg>(DESTINATION_ALL, name_,
                    MSG_TYPE_ENGINE_STATUS,
                    to_string(estate_));
        messenger_->send(pmsg);
        LOG_INFO(logger, name_ << "  Logout.");
        return true;
    } else {
        LOG_DEBUG(logger, name_ << "  is not connected(logined), cannot disconnect!");
        // make sure ctpapi callback done
        // msleep(500);
        return false;
    }
}

void XtpMDEngine::subscribe(const vector<string>& symbol,SymbolType st) {
    int32_t error;
    //  subscribe all 
    if (st == SymbolType::ST_Full) {
        error = this->api_->SubscribeAllMarketData(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ);        
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribe SZSE error " << error);
        }
        error = this->api_->SubscribeAllMarketData(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribe SSE error " << error);
        }
        subscribeAllMarketData_ = true;
        return;
    }

    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    vector<string> tickersymbol(symbol);
    XTP_EXCHANGE_TYPE exchange_id = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;
    string sout;
    for (int32_t i = 0; i < nCount; i++) {
        vector<string> partsymbol = stringsplit(symbol[i], ' ');
        if (partsymbol.size() < 4) {
            LOG_ERROR(logger, name_ << " subscribe symbol error " << symbol[i]);
            return;
        }
        tickersymbol[i] = partsymbol[2];
        exchange_id = string2XtpExchange(partsymbol[0]);
    }
    char** insts = new char*[nCount];
    for (int32_t i = 0; i < nCount; i++) {
        insts[i] = (char*)tickersymbol[i].c_str();
        if (find(lastsubs_.begin(), lastsubs_.end(), symbol[i]) == lastsubs_.end())
            lastsubs_.push_back(symbol[i]);
        sout += tickersymbol[i] +string("|");
    }
    error = this->api_->SubscribeMarketData(insts, nCount, exchange_id);
    if (error != 0) {
        LOG_ERROR(logger, name_ << " subscribe  error " << error);
    }
    delete[] insts;
    LOG_INFO(logger, name_ << " subcribe " << nCount << "|" << sout << ".");

}

void XtpMDEngine::unsubscribe(const vector<string>& symbol,SymbolType st) {
    int32_t error;
    //  unsubscribe all 
    if (st == SymbolType::ST_Full) {
        error = this->api_->UnSubscribeAllMarketData(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ);        
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribe SZSE error " << error);
        }
        error = this->api_->UnSubscribeAllMarketData(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribe SSE error " << error);
        }
        subscribeAllMarketData_ = false;
        return;
    }
    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    vector<string> tickersymbol(symbol);
    XTP_EXCHANGE_TYPE exchange_id = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;

    string sout;
    for (int32_t i = 0; i < nCount; i++){
        vector<string> partsymbol = stringsplit(symbol[i], ' ');
        if (partsymbol.size() < 4) {
            LOG_ERROR(logger, name_ << " subscribe symbol error " << symbol[i]);
            return;
        }
        tickersymbol[i] = partsymbol[2];
        exchange_id = string2XtpExchange(partsymbol[0]);
    }
    char** insts = new char*[nCount];
    for (int32_t i = 0; i < nCount; i++) {
        insts[i] = (char*)tickersymbol[i].c_str();
        sout += tickersymbol[i] +string("|");
        // remove last subcriptions
        for (auto it = lastsubs_.begin(); it != lastsubs_.end();) {
            if (*it == symbol[i]) {
                it = lastsubs_.erase(it);
            } else {
                ++it;
            }
        }
    }
    error = this->api_->UnSubscribeMarketData(insts, nCount, exchange_id);
    if (error != 0) {
        LOG_ERROR(logger, name_ << " unsubscribe  error " << error);
    }
    delete[] insts;
    LOG_INFO(logger, name_ << " unsubcribe " << nCount << "|" << sout << ".");
}


//  OnTickByTick
void XtpMDEngine::subscribeTickByTick(const vector<string>& symbol, SymbolType st) {
    int32_t error;
    //  subscribe all 
    if (st == SymbolType::ST_Full) {
        error = this->api_->SubscribeAllTickByTick(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ);        
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribetbt SZSE error " << error);
        }
        error = this->api_->SubscribeAllTickByTick(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " subscribetbt SSE error " << error);
        }
        subscribeAllMarketTBT_ = true;
        return;
    }

    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    vector<string> tickersymbol(symbol);
    XTP_EXCHANGE_TYPE exchange_id = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;
    string sout;
    for (int32_t i = 0; i < nCount; i++) {
        vector<string> partsymbol = stringsplit(symbol[i], ' ');
        if (partsymbol.size() < 4) {
            LOG_ERROR(logger, name_ << " subscribetbt symbol error " << symbol[i]);
            return;
        }
        tickersymbol[i] = partsymbol[2];
        exchange_id = string2XtpExchange(partsymbol[0]);
    }
    char** insts = new char*[nCount];
    for (int32_t i = 0; i < nCount; i++) {
        insts[i] = (char*)tickersymbol[i].c_str();
        if (find(lastsubstbt_.begin(), lastsubstbt_.end(), symbol[i]) == lastsubstbt_.end())
            lastsubstbt_.push_back(symbol[i]);
        sout += tickersymbol[i] +string("|");
    }
    error = this->api_->SubscribeTickByTick(insts, nCount, exchange_id);
    if (error != 0) {
        LOG_ERROR(logger, name_ << " subscribetbt  error " << error);
    }
    delete[] insts;
    LOG_INFO(logger, name_ << " subcribetbt " << nCount << "|" << sout << ".");

}
void XtpMDEngine::unsubscribeTickByTick(const vector<string>& symbol, SymbolType st) {
    int32_t error;
    //  unsubscribe all 
    if (st == SymbolType::ST_Full) {
        error = this->api_->UnSubscribeAllTickByTick(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ);        
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribetbt SZSE error " << error);
        }
        error = this->api_->UnSubscribeAllTickByTick(XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH);
        if (error != 0) {
            LOG_ERROR(logger, name_ << " unsubscribetbt SSE error " << error);
        }
        subscribeAllMarketTBT_ = false;
        return;
    }
    const int32_t nCount = symbol.size();
    if (nCount == 0)
        return;
    vector<string> tickersymbol(symbol);
    XTP_EXCHANGE_TYPE exchange_id = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;

    string sout;
    for (int32_t i = 0; i < nCount; i++){
        vector<string> partsymbol = stringsplit(symbol[i], ' ');
        if (partsymbol.size() < 4) {
            LOG_ERROR(logger, name_ << " subscribetbt symbol error " << symbol[i]);
            return;
        }
        tickersymbol[i] = partsymbol[2];
        exchange_id = string2XtpExchange(partsymbol[0]);
    }
    char** insts = new char*[nCount];
    for (int32_t i = 0; i < nCount; i++) {
        insts[i] = (char*)tickersymbol[i].c_str();
        sout += tickersymbol[i] +string("|");
        // remove last subcriptions
        for (auto it = lastsubstbt_.begin(); it != lastsubstbt_.end();) {
            if (*it == symbol[i]) {
                it = lastsubstbt_.erase(it);
            } else {
                ++it;
            }
        }
    }
    error = this->api_->UnSubscribeTickByTick(insts, nCount, exchange_id);
    if (error != 0) {
        LOG_ERROR(logger, name_ << " unsubscribetbt  error " << error);
    }
    delete[] insts;
    LOG_INFO(logger, name_ << " unsubcribetbt " << nCount << "|" << sout << ".");

}
// query


void XtpMDEngine::timertask() {
    timercount_++;
    // // send status every second 
    // auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
    // 	MSG_TYPE_ENGINE_STATUS,
    // 	to_string(estate_));
    // messenger_->send(pmsgout);

}
void XtpMDEngine::processbuf() {
}

/////////////////////////////////////////////// end of outgoing functions ///////////////////////////////////////

////////////////////////////////////////////////////// callback  function ///////////////////////////////////////

void XtpMDEngine::OnDisconnected(int32_t nReason) {
    estate_ = DISCONNECTED;  // automatic connecting
    if (autoconnect_ && !inconnectaction_) {
        std::shared_ptr<InfoMsg> pmsg = make_shared<InfoMsg>(name_, name_, MSG_TYPE_ENGINE_CONNECT, "CTP.MD Front connected.");
        CMsgqRMessenger::Send(pmsg);
    }
    // loginReqId_++;
    // if (loginReqId_ % 4000 == 0) {
    //     auto pmsg = make_shared<InfoMsg>(DESTINATION_ALL, name_,
    //                 MSG_TYPE_ENGINE_STATUS,
    //                 to_string(estate_));
    //     messenger_->send(pmsg);
    //     loginReqId_ = 0;
    //     auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
    //         MSG_TYPE_INFO_ENGINE_MDDISCONNECTED,
    //         fmt::format("Ctp md disconnected, nReason={}", nReason)
    //     );
    //     messenger_->send(pmsgout);
    //     LOG_INFO(logger, name_ << "  is  disconnected, nReason=" << nReason);
    // }
}

void XtpMDEngine::OnError(XTPRI *error_info) {
    if (error_info == nullptr) {
        return;
    }
    LOG_ERROR(logger, name_
    << "  OnError: ErrorID="
    << error_info->error_id
    << "ErrorMsg="
    << error_info->error_msg);
    // <<GBKToUTF8(pRspInfo->ErrorMsg));
}


///订阅行情应答
void XtpMDEngine::OnSubMarketData(XTPST *ticker, XTPRI *error_info, bool is_last) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << "  OnSubMarketData:InstrumentID=" << ticker->ticker);
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnSubMarketData failed: ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}

// 取消订阅行情应答
void XtpMDEngine::OnUnSubMarketData(XTPST *ticker, XTPRI *error_info, bool is_last) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << " OnUnSubMarketData:InstrumentID=" << ticker->ticker);
    } else {
        LOG_ERROR(logger, name_ << " OnUnSubMarketData failed: ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}

void XtpMDEngine::OnDepthMarketData(XTPMD *market_data,
    int64_t bid1_qty[],
    int32_t bid1_count,
    int32_t max_bid1_count,
    int64_t ask1_qty[],
    int32_t ask1_count, int32_t max_ask1_count) {
    if (market_data == nullptr) {
        LOG_DEBUG(logger, name_ << " OnDepthMarketData is nullptr");
        return;
    }

    string arrivetime = ymdhmsf6();
    auto pk = make_shared<TickMsg>();
    pk->msgtype_ = MSG_TYPE_TICK_L5;
    pk->data_.fullSymbol_ = xtpExchange2string(market_data->exchange_id) + " T " + string(market_data->ticker) + " 0";
    pk->destination_ = DESTINATION_ALL;
    pk->source_ = name_;
    pk->data_.time_ = arrivetime;
    pk->data_.price_ = market_data->last_price;
    pk->data_.size_ = market_data->qty;
    pk->data_.depth_ = 5;
    for (int i = 0; i < 5; i++) {
        pk->data_.bidPrice_[i] = market_data->bid[i];
        pk->data_.bidSize_[i] = market_data->bid_qty[i];
        pk->data_.askPrice_[i] = market_data->ask[i];
        pk->data_.askSize_[i] = market_data->ask_qty[i];
    }

    pk->data_.openInterest_ = market_data->total_long_positon;
    pk->data_.open_ = market_data->open_price;
    pk->data_.high_ = market_data->high_price;
    pk->data_.low_ =  market_data->low_price;
    pk->data_.preClose_ = market_data->pre_close_price;
    pk->data_.upperLimitPrice_ = market_data->upper_limit_price;
    pk->data_.lowerLimitPrice_ = market_data->lower_limit_price;

    messenger_->send(pk, 1);
    DataManager::instance().updateOrderBook(pk->data_);
    LOG_DEBUG(logger, name_ << " OnDepthMarketData at"<< arrivetime
        <<" ticker=" << market_data->ticker
        <<" LastPrice="<< market_data->last_price
        <<" Volume="<< market_data->qty
        <<" BidPrice1="<< market_data->bid[0]
        <<" BidVolume1="<< market_data->bid_qty[0]
        <<" AskPrice1="<< market_data->ask[0]
        <<" AskVolume1="<< market_data->ask_qty[0]
        <<" BidPrice10="<< market_data->bid[9]
        <<" BidVolume10="<< market_data->bid_qty[9]
        <<" AskPrice10="<< market_data->ask[9]
        <<" AskVolume10="<< market_data->ask_qty[9]);

    // DataManager::instance().recorder_.insertdb(k);
}

void XtpMDEngine::OnSubTickByTick(XTPST *ticker, XTPRI *error_info, bool is_last) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << "  OnSubTickByTick:ticker=" << ticker->ticker);
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnSubTickByTick failed: ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}

void XtpMDEngine::OnUnSubTickByTick(XTPST *ticker, XTPRI *error_info, bool is_last) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << "  OnUnSubTickByTick:ticker=" << ticker->ticker);
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnUnSubTickByTick failed: ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}

void XtpMDEngine::OnTickByTick(XTPTBT *tbt_data) {
    if (tbt_data == nullptr) {
        return;
    }
    auto pk = make_shared<TickByTickMsg>();
    pk->data_.fullSymbol_ = xtpExchange2string(tbt_data->exchange_id) + " T " + string(tbt_data->ticker) + " 0";
    pk->data_.time_ = time_t2str(tbt_data->data_time);  // need check
    if (tbt_data->type == XTP_TBT_ENTRUST) {
        pk->msgtype_ = MSG_TYPE_STOCK_TickByTickEntrust;
        pk->data_.channel_no_ = tbt_data->entrust.channel_no;
        pk->data_.seq_ = tbt_data->entrust.seq;
        pk->data_.price_ = tbt_data->entrust.price;
        pk->data_.size_ = tbt_data->entrust.qty;
        pk->data_.side_ = tbt_data->entrust.side;
        pk->data_.ord_type_ = tbt_data->entrust.ord_type;
    } else {
        pk->data_.channel_no_ = tbt_data->trade.channel_no;
        pk->data_.seq_ = tbt_data->trade.seq;
        pk->data_.price_ = tbt_data->trade.price;
        pk->data_.size_ = tbt_data->trade.qty;
        pk->data_.money_ = tbt_data->trade.money;
        pk->data_.bid_no_  = tbt_data->trade.bid_no;
        pk->data_.ask_no_ = tbt_data->trade.ask_no;
        pk->data_.trade_flag_ = tbt_data->trade.trade_flag;
    }

    pk->destination_ = DESTINATION_ALL;
    pk->source_ = name_;
    messenger_->send(pk, 1);
}

void XtpMDEngine::OnSubscribeAllMarketData(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << " OnSubscribeAllMarketData: "<<xtpExchange2string(exchange_id));
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnSubscribeAllMarketData ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}

void XtpMDEngine::OnUnSubscribeAllMarketData(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << " OnUnSubscribeAllMarketData: "<<xtpExchange2string(exchange_id));
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnUnSubscribeAllMarketData ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}

void XtpMDEngine::OnSubscribeAllTickByTick(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << " OnSubscribeAllTickByTick: "<<xtpExchange2string(exchange_id));
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnSubscribeAllTickByTick ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }

}

void XtpMDEngine::OnUnSubscribeAllTickByTick(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        LOG_INFO(logger, name_ << " OnUnSubscribeAllTickByTick: "<<xtpExchange2string(exchange_id));
    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_SUBSCRIBE,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnUnSubscribeAllTickByTick ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}


void XtpMDEngine::OnQueryAllTickers(XTPQSI* ticker_info, XTPRI *error_info, bool is_last) {
    bool bResult = (error_info != nullptr) && (error_info->error_id != 0);
    if (!bResult) {
        if (ticker_info == nullptr) {
            LOG_INFO(logger, name_ <<" qry ticker return nullptr");
            return;
        }
        auto pmsg = make_shared<SecurityMsg>();
        pmsg->destination_ = DESTINATION_ALL;
        pmsg->source_ = name_;
        pmsg->data_.symbol_ = ticker_info->ticker;
        pmsg->data_.exchange_ = xtpExchange2string(ticker_info->exchange_id);
        pmsg->data_.securityType_ = xtpSecType2SQ(ticker_info->ticker_type);
        pmsg->data_.fullSymbol_ = pmsg->data_.exchange_ + " " + pmsg->data_.securityType_ + " " + pmsg->data_.symbol_ + " 0";
        pmsg->data_.multiplier_ = ticker_info->buy_qty_unit;
        pmsg->data_.localName_ = ticker_info->ticker_name;
        pmsg->data_.ticksize_ = ticker_info->price_tick;

        messenger_->send(pmsg);
        // string symbol = boost::to_upper_copy(string(ticker_info->InstrumentName));

        DataManager::instance().xtpSecurityDetails_[pmsg->data_.fullSymbol_] = pmsg->data_;
        if (is_last) {
            DataManager::instance().saveXtpSecurityFile_  = true;
            LOG_DEBUG(logger, name_ <<" is last OnQueryAllTickers:"
            <<" fullSymbol_=" <<pmsg->data_.fullSymbol_
            <<" ticker="<< ticker_info->ticker
            <<" Name="<< ticker_info->ticker_name);
        }

    } else {
        auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
            MSG_TYPE_ERROR_QRY_CONTRACT,
            //  GBKToUTF8(pRspInfo->ErrorMsg));
            error_info->error_msg);
        LOG_ERROR(logger, name_ << " OnQueryAllTickers ErrorID=" << error_info->error_id << "ErrorMsg=" << error_info->error_msg);
    }
}


// not used yet

void XtpMDEngine::OnSubOrderBook(XTPST *ticker, XTPRI *error_info, bool is_last) {}

void XtpMDEngine::OnUnSubOrderBook(XTPST *ticker, XTPRI *error_info, bool is_last) {}

void XtpMDEngine::OnOrderBook(XTPOB *order_book) {}

void XtpMDEngine::OnSubscribeAllOrderBook(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnUnSubscribeAllOrderBook(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnQueryTickersPriceInfo(XTPTPI* ticker_info, XTPRI *error_info, bool is_last) {}

void XtpMDEngine::OnSubscribeAllOptionMarketData(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnUnSubscribeAllOptionMarketData(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnSubscribeAllOptionOrderBook(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnUnSubscribeAllOptionOrderBook(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnSubscribeAllOptionTickByTick(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}

void XtpMDEngine::OnUnSubscribeAllOptionTickByTick(XTP_EXCHANGE_TYPE exchange_id, XTPRI *error_info) {}


    ////////// end of callback /////////////////////////


string XtpMDEngine::xtpExchange2string(XTP_EXCHANGE_TYPE exchange_id) {
    string ex = "SSE";
    switch (exchange_id) {
        case XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH:
            ex = "SSE";
            break;
        case XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ:
            ex = "SZSE";
        default:
            break;
    }
    return ex;
}
XTP_EXCHANGE_TYPE XtpMDEngine::string2XtpExchange(const string& exchangeid) {
    XTP_EXCHANGE_TYPE eid = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;
    if (exchangeid == "SSE") {
        eid = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SH;
    } else if (exchangeid == "SZSE") {
        eid = XTP_EXCHANGE_TYPE::XTP_EXCHANGE_SZ;
    }
    return eid;
}
char XtpMDEngine::xtpSecType2SQ(XTP_TICKER_TYPE stype) {
    char sqtype = 'T';
    switch (stype) {
        case XTP_TICKER_TYPE::XTP_TICKER_TYPE_STOCK:
            sqtype = 'T';
            break;
        case XTP_TICKER_TYPE::XTP_TICKER_TYPE_INDEX:
            sqtype = 'Z';
            break;
        case XTP_TICKER_TYPE::XTP_TICKER_TYPE_FUND:
            sqtype = 'J';
            break;
        case XTP_TICKER_TYPE::XTP_TICKER_TYPE_BOND:
            sqtype = 'B';
            break;
        case XTP_TICKER_TYPE::XTP_TICKER_TYPE_OPTION:
            sqtype = 'O';
            break;
        case XTP_TICKER_TYPE::XTP_TICKER_TYPE_TECH_STOCK:
            sqtype = 't';
            break;
        default:
            break;
    }
    return sqtype;
}

}  // namespace StarQuant
