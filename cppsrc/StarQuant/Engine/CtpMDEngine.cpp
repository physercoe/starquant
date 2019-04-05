#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <boost/locale.hpp>
#include <boost/algorithm/string.hpp>

#include <Engine/CtpMDEngine.h>
#include <APIs/Ctp/ThostFtdcMdApi.h>
#include <Common/util.h>
#include <Common/logger.h>
#include <Common/timeutil.h>
#include <Data/tick.h>
using namespace std;

namespace StarQuant
{
	//extern std::atomic<bool> gShutdown;

	CtpMDEngine ::CtpMDEngine() 
		: loginReqId_(0)
	{
		init();
	}

	CtpMDEngine::~CtpMDEngine() {
		if(estate_ != STOP)
			stop();
		if (api_ != nullptr) {
			this->api_->RegisterSpi(nullptr);
			this->api_->Release();// api must init() or will segfault
			this->api_ = nullptr;
		}
	}

	void CtpMDEngine::init(){
		// if (IEngine::msgq_send_ == nullptr){
		// 	lock_guard<mutex> g(IEngine::sendlock_);
		// 	IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		// }
		if(logger == nullptr){
			logger = SQLogger::getLogger("MDEngine.CTP");
		}	
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
		}	
		name_ = "CTP_MD";
		ctpacc_ = CConfig::instance()._apimap["CTP"];
		string path = CConfig::instance().logDir() + "/ctp/md";
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);
		// 创建API对象
		this->api_ = CThostFtdcMdApi::CreateFtdcMdApi(path.c_str());
		this->api_->RegisterSpi(this);
		string ctp_data_address = ctpacc_.md_ip + ":" + to_string(ctpacc_.md_port);	
		this->api_->RegisterFront((char*)ctp_data_address.c_str());
		this->api_->Init();
		estate_ = CONNECTING;
		LOG_DEBUG(logger,"CTP MD inited");

	}

	void CtpMDEngine::stop(){
		int tmp = disconnect();
		estate_ = EState::STOP; 
		LOG_DEBUG(logger,"CTP MD stoped");	
	}

	void CtpMDEngine::start(){
		while(estate_ != EState::STOP){
			string msgin = msgq_recv_->recmsg(1);
			if (msgin.empty())
				continue;
			MSG_TYPE msgintype = MsgType(msgin);
			vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
			if (v[0] != name_) //filter message according to its destination
				continue;
			LOG_DEBUG(logger,"CTP MD recv msg:"<<msgin );	
			bool tmp;
			switch (msgintype)
			{
				case MSG_TYPE_ENGINE_CONNECT:
					if (connect()){
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_INFO_ENGINE_MDCONNECTED);
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_ENGINE_DISCONNECT:
					tmp = disconnect();
					break;
				case MSG_TYPE_SUBSCRIBE_MARKET_DATA:
					if (estate_ == LOGIN_ACK){
						subscribe(v[3]);
					}
					else{
						LOG_DEBUG(logger,"CTP MD is not connected,can not subscribe!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "ctp md is not connected,can not subscribe";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_UNSUBSCRIBE:
					if (estate_ == LOGIN_ACK){
						unsubscribe(v[3]);
					}
					else{
						LOG_DEBUG(logger,"CTP MD is not connected,can not unsubscribe!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR  
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) + SERIALIZATION_SEPARATOR 
							+ "ctp md is not connected,can not subscribe";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_ENGINE_STATUS:
					{
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ENGINE_STATUS) + SERIALIZATION_SEPARATOR 
							+ to_string(estate_);
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_TEST:
					{						
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_TEST) + SERIALIZATION_SEPARATOR 
							+ ymdhmsf6();
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
						LOG_DEBUG(logger,"CTP_MD return test msg!");
					}
					break;					
				default:
					break;
			}
		}
	}

////////////////////////////////////////////////////// outgoing function ///////////////////////////////////////
	bool CtpMDEngine::connect()
	{
		int error;
		int count = 0;// count numbers of tries, two many tries ends
		string ctp_data_address = ctpacc_.md_ip + ":" + to_string(ctpacc_.md_port);	
		CThostFtdcReqUserLoginField loginField = CThostFtdcReqUserLoginField();		
		while(estate_ != EState::LOGIN_ACK && estate_ != STOP){
			switch(estate_){
				case EState::DISCONNECTED:
					// this->api_->RegisterFront((char*)ctp_data_address.c_str());
					// this->api_->Init();
					// estate_ = CONNECTING;
					// PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Md connecting to frontend...!\n", __FILE__, __LINE__, __FUNCTION__);
					// count++;
					break;
				case EState::CONNECTING:
					msleep(100);
					break;
				case EState::CONNECT_ACK:
					LOG_INFO(logger,"Ctp Md logining ...");
					strcpy(loginField.BrokerID, ctpacc_.brokerid.c_str());
					strcpy(loginField.UserID, ctpacc_.userid.c_str());
					strcpy(loginField.Password, ctpacc_.password.c_str());
					///用户登录请求
					error = this->api_->ReqUserLogin(&loginField, loginReqId_);	
					count++;
					estate_ = EState::LOGINING;
					if (error != 0){
						LOG_ERROR(logger,"Ctp md login error : "<<error);//TODO: send error msg to client
						estate_ = EState::CONNECT_ACK;
						msleep(1000);
					}
					break;
				case EState::LOGINING:
					msleep(500);
					break;
				default:
					msleep(100);
					break;
			}
			if(count >10){
				LOG_ERROR(logger,"too many tries fails, give up connecting");
				//estate_ = EState::DISCONNECTED;
				return false;
			}
		}
		return true;
	}

	bool CtpMDEngine::disconnect() {
		if (estate_ == LOGIN_ACK){
			LOG_INFO(logger,"Ctp md logouting ..");
			CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();
			strcpy(logoutField.BrokerID, ctpacc_.brokerid.c_str());
			strcpy(logoutField.UserID, ctpacc_.userid.c_str());
			int error = this->api_->ReqUserLogout(&logoutField, loginReqId_);
			estate_ = EState::LOGOUTING;
			if (error != 0){
				LOG_ERROR(logger,"ctp md logout error:"<<error);//TODO: send error msg to client
				estate_ = EState::LOGIN_ACK;
				return false;
				}		
			return true;
		}
		else{
			LOG_DEBUG(logger,"ctp md is not connected(logined), cannot disconnect!");
			return false;
		}
	}

	void CtpMDEngine::subscribe(const string& symbol) {
		int error;
		string ctbticker = CConfig::instance().SecurityFullNameToCtpSymbol(symbol);			
		char* buffer = (char*)ctbticker.c_str();
		char* myreq[1] = { buffer };
		LOG_INFO(logger,"ctp md subcribe "<<myreq);
		error = this->api_->SubscribeMarketData(myreq, 1);
		if (error != 0){
			LOG_ERROR(logger,"ctp md subscribe  error "<<error);
		}		
	}

	void CtpMDEngine::unsubscribe(const string& symbol) {

		int error;
		string ctbticker = CConfig::instance().SecurityFullNameToCtpSymbol(symbol);			
		char* buffer = (char*)ctbticker.c_str();
		char* myreq[1] = { buffer };
		LOG_INFO(logger,"ctp md unsubcribe "<<myreq);
		error = this->api_->UnSubscribeMarketData(myreq, 1);
		if (error != 0){
			LOG_ERROR(logger,"ctp md unsubscribe  error "<<error);
		}		
	}

	/////////////////////////////////////////////// end of outgoing functions ///////////////////////////////////////

	////////////////////////////////////////////////////// callback  function ///////////////////////////////////////
	
	void CtpMDEngine::OnFrontConnected() {
		estate_ = CONNECT_ACK;			// not used
		LOG_INFO(logger,"Ctp md frontend connected. ");		
	}

	void CtpMDEngine::OnFrontDisconnected(int nReason) {
		estate_ = DISCONNECTED;			// not used
		LOG_INFO(logger,"Ctp md frontend is  disconnected, nReason="<<nReason);			
	}

	void CtpMDEngine::OnHeartBeatWarning(int nTimeLapse) {
		LOG_INFO(logger,"Ctp md heartbeat overtime error, nTimeLapse="<<nTimeLapse);
	}

	void CtpMDEngine::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		LOG_ERROR(logger,"Ctp md OnRspError: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<GBKToUTF8(pRspInfo->ErrorMsg));  
	}

	void CtpMDEngine::OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			LOG_ERROR(logger,"Ctp md login failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8);
		}
		else{
			estate_ = EState::LOGIN_ACK;
			LOG_INFO(logger,"Ctp md server user logged in,"
				<<"TradingDay="<<pRspUserLogin->TradingDay
				<<"LoginTime="<<pRspUserLogin->LoginTime
				<<"frontID="<<pRspUserLogin->FrontID
				<<"sessionID="<<pRspUserLogin->SessionID
			);
		}

	}
	void CtpMDEngine::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			LOG_ERROR(logger,"Ctp Md logout failed: "<<"ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8); 

		}
		else {
			estate_ = EState::CONNECT_ACK;
			LOG_INFO(logger,"Ctp Md Logout,BrokerID="<<pUserLogout->BrokerID<<" UserID="<<pUserLogout->UserID);
		}
	}

	///订阅行情应答
	void CtpMDEngine::OnRspSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo !=nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			LOG_INFO(logger,"Ctp md OnRspSubMarketData:InstrumentID="<<pSpecificInstrument->InstrumentID);
		}
		else {
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_SUBSCRIBE);
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp md OnRspSubMarketData failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<GBKToUTF8(pRspInfo->ErrorMsg));
		}

	}

	///取消订阅行情应答
	void CtpMDEngine::OnRspUnSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo !=nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			LOG_INFO(logger,"Ctp md OnRspUnSubMarketData:InstrumentID="<<pSpecificInstrument->InstrumentID);
		}
		else {
			LOG_ERROR(logger,"Ctp md OnRspUnSubMarketData failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<GBKToUTF8(pRspInfo->ErrorMsg));
		}
	}

	///订阅询价应答
	void CtpMDEngine::OnRspSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo !=nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			LOG_INFO(logger,"Ctp md OnRspSubForQuoteRsp:InstrumentID="<<pSpecificInstrument->InstrumentID);
		}
		else {
			LOG_ERROR(logger,"Ctp md OnRspSubForQuotoRsp failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<GBKToUTF8(pRspInfo->ErrorMsg));
		}
	}

	///取消订阅询价应答
	void CtpMDEngine::OnRspUnSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			LOG_INFO(logger,"Ctp md OnRspUnSubForQuoteRsp:InstrumentID="<<pSpecificInstrument->InstrumentID);
		}
		else {
			LOG_ERROR(logger,"Ctp md OnRspUnSubForQuoteRsp failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<GBKToUTF8(pRspInfo->ErrorMsg));
		}
	}

	void CtpMDEngine::OnRtnDepthMarketData(CThostFtdcDepthMarketDataField *pDepthMarketData) {
		if (pDepthMarketData == nullptr){
			LOG_DEBUG(logger,"ctp md OnRtnDepthMarketData is nullptr");
			return;
		}
		string arrivetime = ymdhmsf6();
		Tick_L1 k;
		char buf[64];
		char a[9];
		char b[9];
		strcpy(a,pDepthMarketData->ActionDay);
		strcpy(b,pDepthMarketData->UpdateTime);
        std::sprintf(buf, "%c%c%c%c-%c%c-%c%c %c%c:%c%c:%c%c.%.3d", a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],b[0],b[1],b[3],b[4],b[6],b[7],pDepthMarketData->UpdateMillisec );
		k.time_ = buf;
		k.msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L1;
		k.fullsymbol_ = CConfig::instance().CtpSymbolToSecurityFullName(pDepthMarketData->InstrumentID);
		k.price_ = pDepthMarketData->LastPrice;
		k.size_ = pDepthMarketData->Volume;			
		k.bidprice_L1_ = pDepthMarketData->BidPrice1;
		k.bidsize_L1_ = pDepthMarketData->BidVolume1;
		k.askprice_L1_ = pDepthMarketData->AskPrice1;
		k.asksize_L1_ = pDepthMarketData->AskVolume1;
		k.open_interest = pDepthMarketData->OpenInterest;
		k.open_ = pDepthMarketData->OpenPrice;
		k.high_ = pDepthMarketData->HighestPrice;
		k.low_ = pDepthMarketData->LowestPrice;
		k.pre_close_ = pDepthMarketData->PreClosePrice;
		k.upper_limit_price_ = pDepthMarketData->UpperLimitPrice;
		k.lower_limit_price_ = pDepthMarketData->LowerLimitPrice;
		lock_guard<mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(k.serialize());
		LOG_DEBUG(logger,"Ctp md OnRtnDepthMarketData at"<<arrivetime
			<<"InstrumentID="<<pDepthMarketData->InstrumentID
			<<"LastPrice="<<pDepthMarketData->LastPrice
			<<"Volume="<<pDepthMarketData->Volume
			<<"BidPrice1="<<pDepthMarketData->BidPrice1
			<<"BidVolume1="<<pDepthMarketData->BidVolume1
			<<"AskPrice1="<<pDepthMarketData->AskPrice1
			<<">AskVolume1="<<pDepthMarketData->AskVolume1
			<<"OpenInterest="<<pDepthMarketData->OpenInterest
			<<"OpenPrice="<<pDepthMarketData->OpenPrice
			<<"HighestPrice="<<pDepthMarketData->HighestPrice
			<<"LowestPrice="<<pDepthMarketData->LowestPrice
			<<"PreClosePrice="<<pDepthMarketData->PreClosePrice
			<<"UpperLimitPrice="<<pDepthMarketData->UpperLimitPrice
			<<"LowerLimitPrice="<<pDepthMarketData->LowerLimitPrice
			<<"UpdateTime="<<pDepthMarketData->UpdateTime<<"."<<pDepthMarketData->UpdateMillisec
		);


	}

	///询价通知
	void CtpMDEngine::OnRtnForQuoteRsp(CThostFtdcForQuoteRspField *pForQuoteRsp) {
		LOG_INFO(logger,"Ctp md OnRtnForQuoteRsp:"
			<<"TradingDay="<<pForQuoteRsp->TradingDay
			<<"ExchangeID="<<pForQuoteRsp->ExchangeID
			<<"InstrumentID="<<pForQuoteRsp->InstrumentID
			<<"ForQuoteSysID="<<pForQuoteRsp->ForQuoteSysID
		);
	}
	/////////////////////////////////////////////// end of callback ///////////////////////////////////////

}
