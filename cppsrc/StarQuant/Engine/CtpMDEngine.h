#ifndef _StarQuant_Engine_CtpMDEngine_H_
#define _StarQuant_Engine_CtpMDEngine_H_

#include <mutex>
#include <Common/datastruct.h>
#include <Engine/IEngine.h>
#include <APIs/Ctp/ThostFtdcMdApi.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
	class CtpMDEngine : public IEngine, CThostFtdcMdSpi {
	public:
		string name_;
		Account ctpacc_;

		CtpMDEngine();
		~CtpMDEngine();

		virtual void init();
		virtual void start();
		virtual void stop();
		
		virtual bool connect() ;
		virtual bool disconnect() ;
		void releaseapi();
		void reset();
		void switchday(){};	
		void timertask();
		void processbuf(); 

		void subscribe(const vector<string>& symbols,SymbolType st = ST_Ctp) ;
		void unsubscribe(const vector<string>& symbols,SymbolType st = ST_Ctp) ;	


	public:
		virtual void OnFrontConnected();
		virtual void OnFrontDisconnected(int nReason);
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
		int loginReqId_;
		CThostFtdcMdApi* api_;		
		bool apiinited_;
		bool inconnectaction_;
		bool autoconnect_;
		vector<string> lastsubs_;
		int timercount_;		
	};
}

#endif
