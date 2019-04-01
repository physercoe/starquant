#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
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
		stop();
	}

	void CtpMDEngine::init(){
		// if (IEngine::msgq_send_ == nullptr){
		// 	lock_guard<mutex> g(IEngine::sendlock_);
		// 	IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		// }
		cout<<"ctp md init"<<endl;
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
		}	
		name_ = "CTP_MD";
		ctpacc_ = CConfig::instance()._apimap["CTP"];
		string path = CConfig::instance().logDir() + "/ctp/";
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);
		// 创建API对象
		this->api_ = CThostFtdcMdApi::CreateFtdcMdApi(path.c_str());
		this->api_->RegisterSpi(this);
	}

	void CtpMDEngine::stop(){
		int tmp = disconnect();
		estate_ = EState::STOP; 	
		if (api_ != NULL) {
			this->api_->RegisterSpi(NULL);
			this->api_->Release();
			this->api_ = NULL;
		}
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
			bool tmp;
			switch (msgintype)
			{
				case MSG_TYPE_MD_ENGINE_OPEN:
					tmp = connect();
					break;
				case MSG_TYPE_MD_ENGINE_CLOSE:
					tmp = disconnect();
					break;
				case MSG_TYPE_SUBSCRIBE_MARKET_DATA:
					if (estate_ == LOGIN_ACK){
						subscribe(v[2]);
					}
					else{
						cout<<"md is not connected,can not subscribe! "<<endl;
						string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"md is not connected,can not subscribe";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_UNSUBSCRIBE:
					if (estate_ == LOGIN_ACK){
						unsubscribe(v[2]);
					}
					else{
						cout<<"md is not connected,can not unsubscribe! "<<endl;
						string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"md is not connected,can not unsubscribe";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_ENGINE_STATUS:
					{
						string msgout = to_string(MSG_TYPE_ENGINE_STATUS) + SERIALIZATION_SEPARATOR + to_string(estate_);
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
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
		while(estate_ != EState::LOGIN_ACK){
			switch(estate_){
				case EState::DISCONNECTED:
					this->api_->RegisterFront((char*)ctp_data_address.c_str());
					this->api_->Init();
					estate_ = CONNECTING;
					PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Md connecting to frontend...!\n", __FILE__, __LINE__, __FUNCTION__);
					count++;
					break;
				case EState::CONNECTING:
					msleep(100);
					break;
				case EState::CONNECT_ACK:
					PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Md logining ...\n", __FILE__, __LINE__, __FUNCTION__);
					strcpy(loginField.BrokerID, ctpacc_.brokerid.c_str());
					strcpy(loginField.UserID, ctpacc_.userid.c_str());
					strcpy(loginField.Password, ctpacc_.password.c_str());
					///用户登录请求
					error = this->api_->ReqUserLogin(&loginField, loginReqId_);	
					count++;
					estate_ = EState::LOGINING;
					if (error != 0){
						cout<<"Ctp login error : "<<error<<endl;//TODO: send error msg to client
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
				cout<<"too many tries fails, give up connecting"<<endl;
				//estate_ = EState::DISCONNECTED;
				return false;
			}
		}
		return true;
	}

	bool CtpMDEngine::disconnect() {
		if (estate_ == LOGIN_ACK){
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Md logouting ...\n", __FILE__, __LINE__, __FUNCTION__);
			CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();
			strcpy(logoutField.BrokerID, ctpacc_.brokerid.c_str());
			strcpy(logoutField.UserID, ctpacc_.userid.c_str());
			int error = this->api_->ReqUserLogout(&logoutField, loginReqId_);
			estate_ = EState::LOGOUTING;
			if (error != 0){
				cout<<"Ctp md logout error : "<<error<<endl;//TODO: send error msg to client
				estate_ = EState::LOGIN_ACK;
				return false;
				}		
			return true;
		}
		else{
			cout<<"ctp md is not connected(logined), can not disconnect! "<<endl;
			return false;
		}
	}

	void CtpMDEngine::subscribe(const string& symbol) {
		int error;
		string ctbticker = CConfig::instance().SecurityFullNameToCtpSymbol(symbol);			
		char* buffer = (char*)ctbticker.c_str();
		char* myreq[1] = { buffer };
		cout<<"subcribe "<<myreq<<endl;
		error = this->api_->SubscribeMarketData(myreq, 1);
		if (error != 0){
			cout<<"subscribe  error "<<error<<endl;
		}		
	}

	void CtpMDEngine::unsubscribe(const string& symbol) {

		int error;
		string ctbticker = CConfig::instance().SecurityFullNameToCtpSymbol(symbol);			
		char* buffer = (char*)ctbticker.c_str();
		char* myreq[1] = { buffer };
		cout<<"unsubcribe "<<myreq<<endl;
		error = this->api_->UnSubscribeMarketData(myreq, 1);
		if (error != 0){
			cout<<"unsubscribe  error "<<error<<endl;
		}		
	}

	/////////////////////////////////////////////// end of outgoing functions ///////////////////////////////////////

	////////////////////////////////////////////////////// callback  function ///////////////////////////////////////
	
	void CtpMDEngine::OnFrontConnected() {
		 estate_ = CONNECT_ACK;			// not used
		cout<< "Ctp md frontend connected "<<endl;
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md frontend is connected.\n", __FILE__, __LINE__, __FUNCTION__);
	}
	void CtpMDEngine::OnFrontDisconnected(int nReason) {
		estate_ = DISCONNECTED;			// not used
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md frontend is  disconnected, nReason=%d.\n", __FILE__, __LINE__, __FUNCTION__, nReason);
	}
	void CtpMDEngine::OnHeartBeatWarning(int nTimeLapse) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp data server heartbeat overtime error, nTimeLapse=%d.\n", __FILE__, __LINE__, __FUNCTION__, nTimeLapse);
	}
	void CtpMDEngine::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp data server error: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());		
	}
	void CtpMDEngine::OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp md user login failed: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());	
		}
		else{
			estate_ = EState::LOGIN_ACK;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp data server user logged in; TradingDay=%s, LoginTime=%s, BrokerID=%s, UserID=%s.\n", __FILE__, __LINE__, __FUNCTION__,
				pRspUserLogin->TradingDay, pRspUserLogin->LoginTime, pRspUserLogin->BrokerID, pRspUserLogin->UserID);
		}

	}
	void CtpMDEngine::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp data server user logout failed: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());	
		}
		else {
			estate_ = EState::CONNECT_ACK;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp data server user logged out; BrokerID=%s, UserID=%s.\n", __FILE__, __LINE__, __FUNCTION__, pUserLogout->BrokerID, pUserLogout->UserID);
		}
	}

	///订阅行情应答
	void CtpMDEngine::OnRspSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo !=nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md OnRspSubMarketData: InstrumentID=%s.\n", __FILE__, __LINE__, __FUNCTION__, pSpecificInstrument->InstrumentID);
		}
		else {
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp md OnRspSubMarketData failed: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());
		}

	}

	///取消订阅行情应答
	void CtpMDEngine::OnRspUnSubMarketData(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo !=nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md OnRspUnSubMarketData: InstrumentID=%s.\n", __FILE__, __LINE__, __FUNCTION__, pSpecificInstrument->InstrumentID);
		}
		else {
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp md OnRspUnSubMarketData failed: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());
		}
	}

	///订阅询价应答
	void CtpMDEngine::OnRspSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo !=nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md OnRspSubForQuoteRsp: InstrumentID=%s.\n", __FILE__, __LINE__, __FUNCTION__, pSpecificInstrument->InstrumentID);
		}
		else {
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp md OnRspSubForQuoteRsp failed: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());
		}
	}

	///取消订阅询价应答
	void CtpMDEngine::OnRspUnSubForQuoteRsp(CThostFtdcSpecificInstrumentField *pSpecificInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult) {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md OnRspUnSubForQuoteRsp: InstrumentID=%s.\n", __FILE__, __LINE__, __FUNCTION__, pSpecificInstrument->InstrumentID);
		}
		else {
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp md OnRspUnSubForQuoteRsp failed: ErrorID=%d, ErrorMsg=%s.\n", __FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, GBKToUTF8(pRspInfo->ErrorMsg).c_str());
		}
	}

	void CtpMDEngine::OnRtnDepthMarketData(CThostFtdcDepthMarketDataField *pDepthMarketData) {
		if (pDepthMarketData == nullptr){
			return;
		}
			
		cout<<"quote return at"<< ymdhmsf6() <<endl;
		Tick_L1 k;
		cout<<pDepthMarketData->ExchangeID<<' '<<pDepthMarketData->ExchangeInstID<<" "<<pDepthMarketData->InstrumentID<<" price "
			<<pDepthMarketData->LastPrice<<" vol "
			<<pDepthMarketData->Volume<<" bidprice "
			<<pDepthMarketData->BidPrice1<<" bidvol "
			<<pDepthMarketData->BidVolume1<<" askprice "
			<<pDepthMarketData->AskPrice1<<" askvol "
			<<pDepthMarketData->AskVolume1<<" openi "
			<<pDepthMarketData->OpenInterest<<" openprice "
			<<pDepthMarketData->OpenPrice<<" hp "
			<<pDepthMarketData->HighestPrice<<" lp "
			<<pDepthMarketData->LowestPrice<<" pcp "
			<<pDepthMarketData->PreClosePrice<<" ulp "
			<<pDepthMarketData->UpperLimitPrice<<" llp "
			<<pDepthMarketData->LowerLimitPrice<<" updatime "
			<<pDepthMarketData->UpdateTime<<" updatemillis"
			<<pDepthMarketData->UpdateMillisec<<" "
			<<endl;
		//k.time_ = ymdhmsf();
		char buf[64];
		char a[9];
		char b[9];
		strcpy(a,pDepthMarketData->ActionDay);
		strcpy(b,pDepthMarketData->UpdateTime);
        std::sprintf(buf, "%c%c%c%c-%c%c-%c%c %c%c:%c%c:%c%c.%.3d", a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],b[0],b[1],b[3],b[4],b[6],b[7],pDepthMarketData->UpdateMillisec );
		//k.time_ = string(pDepthMarketData->ActionDay) + " " + string(pDepthMarketData->UpdateTime) + "." + to_string(pDepthMarketData->UpdateMillisec);
		k.time_ = buf;
		//cout<<"time "<<pDepthMarketData->ActionDay<< k.time_<<endl;
		k.msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L1;
		k.fullsymbol_ = CConfig::instance().CtpSymbolToSecurityFullName(pDepthMarketData->InstrumentID);
		//cout<< "quote fullsymbol"<<k.fullsymbol_<<endl;;
		k.price_ = pDepthMarketData->LastPrice;
		k.size_ = pDepthMarketData->Volume;			// not valid without volume
		k.bidprice_L1_ = pDepthMarketData->BidPrice1;
		k.bidsize_L1_ = pDepthMarketData->BidVolume1;
		k.askprice_L1_ = pDepthMarketData->AskPrice1;
		k.asksize_L1_ = pDepthMarketData->AskVolume1;
		k.open_interest = pDepthMarketData->OpenInterest;
		//k.open_ = pDepthMarketData->OpenPrice;
		//k.high_ = pDepthMarketData->HighestPrice;
		//k.low_ = pDepthMarketData->LowestPrice;
		k.pre_close_ = pDepthMarketData->PreClosePrice;
		k.upper_limit_price_ = pDepthMarketData->UpperLimitPrice;
		k.lower_limit_price_ = pDepthMarketData->LowerLimitPrice;
		
		lock_guard<mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(k.serialize());

	}

	///询价通知
	void CtpMDEngine::OnRtnForQuoteRsp(CThostFtdcForQuoteRspField *pForQuoteRsp) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp md OnRtnForQuoteRsp; TradingDay=%s, ExchangeID=%s, InstrumentID=%s, ForQuoteSysID=%s.\n", __FILE__, __LINE__, __FUNCTION__,
			pForQuoteRsp->TradingDay, pForQuoteRsp->ExchangeID, pForQuoteRsp->InstrumentID, pForQuoteRsp->ForQuoteSysID);
	}
	/////////////////////////////////////////////// end of callback ///////////////////////////////////////


}
