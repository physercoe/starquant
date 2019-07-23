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

#ifndef CPPSRC_STARQUANT_ENGINE_CTPMDENGINE_H_
#define CPPSRC_STARQUANT_ENGINE_CTPMDENGINE_H_

#include <Common/datastruct.h>
#include <Engine/IEngine.h>
#include <APIs/Ctp/ThostFtdcMdApi.h>
#include <mutex>
#include <string>
#include <vector>

using std::mutex;
using std::string;
using std::vector;

namespace StarQuant
{
class CtpMDEngine : public IEngine, CThostFtdcMdSpi {
 public:
    string name_;
    Gateway ctpacc_;

    CtpMDEngine();
    ~CtpMDEngine();

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

    void subscribe(const vector<string>& symbols, SymbolType st = ST_Ctp);
    void unsubscribe(const vector<string>& symbols, SymbolType st = ST_Ctp);


 public:
    virtual void OnFrontConnected();
    virtual void OnFrontDisconnected(int32_t nReason);
    virtual void OnHeartBeatWarning(int32_t nTimeLapse);
    // /登录请求响应
    virtual void OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /登出请求响应
    virtual void OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /错误应答
    virtual void OnRspError(CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /订阅行情应答
    virtual void OnRspSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /取消订阅行情应答
    virtual void OnRspUnSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /订阅询价应答
    virtual void OnRspSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /取消订阅询价应答
    virtual void OnRspUnSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int32_t nRequestID, bool bIsLast);
    // /深度行情通知
    virtual void OnRtnDepthMarketData(CThostFtdcDepthMarketDataField *pDepthMarketData);
    // /询价通知
    virtual void OnRtnForQuoteRsp(CThostFtdcForQuoteRspField *pForQuoteRsp);

 private:
    int32_t loginReqId_;
    int32_t reqId_;
    CThostFtdcMdApi* api_;
    bool apiinited_;
    bool inconnectaction_;
    bool autoconnect_;
    vector<string> lastsubs_;
    int32_t timercount_;
    int32_t msgqMode_;   // dontwaitmode flags
};
}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_ENGINE_CTPMDENGINE_H_
