#ifndef _StarQuant_Brokers_CtpDataFeed_H_
#define _StarQuant_Brokers_CtpDataFeed_H_

#include <mutex>
#include <Common/config.h>
#include <Common/Data/marketdatafeed.h>
#include <Brokers/Ctp/ThostFtdcMdApi.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
	struct Security;

	class ctpdatafeed : public marketdatafeed, CThostFtdcMdSpi {
	public:
		ctpdatafeed();
		~ctpdatafeed();

		virtual void processMarketMessages();
		virtual bool connectToMarketDataFeed();
		virtual void disconnectFromMarketDataFeed();
		virtual bool isConnectedToMarketDataFeed() const;

		virtual void subscribeMarketData();
		virtual void unsubscribeMarketData(TickerId reqId);
		virtual void subscribeMarketDepth();
		virtual void unsubscribeMarketDepth(TickerId reqId);
		virtual void subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH);
		virtual void unsubscribeRealTimeBars(TickerId tickerId);
		virtual void requestContractDetails();
		virtual void requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH);
		virtual void requestMarketDataAccountInformation(const string& account);

	public:
		void requestUserLogin();
		void requestUserLogout(int nRequestID);
		// events
		///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
		virtual void OnFrontConnected();
		///当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
		///@param nReason 错误原因
		///        0x1001 网络读失败
		///        0x1002 网络写失败
		///        0x2001 接收心跳超时
		///        0x2002 发送心跳失败
		///        0x2003 收到错误报文
		virtual void OnFrontDisconnected(int nReason);
		///心跳超时警告。当长时间未收到报文时，该方法被调用。
		///@param nTimeLapse 距离上次接收报文的时间
		virtual void OnHeartBeatWarning(int nTimeLapse);
		///登录请求响应
		virtual void OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///登出请求响应
		virtual void OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///错误应答
		virtual void OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///订阅行情应答
		virtual void OnRspSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///取消订阅行情应答
		virtual void OnRspUnSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///订阅询价应答
		virtual void OnRspSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///取消订阅询价应答
		virtual void OnRspUnSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast);
		///深度行情通知
		virtual void OnRtnDepthMarketData(CThostFtdcDepthMarketDataField *pDepthMarketData);
		///询价通知
		virtual void OnRtnForQuoteRsp(CThostFtdcForQuoteRspField *pForQuoteRsp);
	private:
		bool isConnected_;
		int loginReqId_;
		CThostFtdcMdApi* api_;		// TODO: change it to unique_ptr

		//string SecurityFullNameToCtpSymbol(const std::string& symbol);
		//string CtpSymbolToSecurityFullName(const std::string& symbol);
		
	};
}

#endif
