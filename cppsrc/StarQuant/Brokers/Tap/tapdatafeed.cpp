#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>

#include <Brokers/Tap/tapdatafeed.h>
#include <Brokers/Tap/TapQuoteAPI.h>
#include <Common/Util/util.h>
#include <Common/Order/orderstatus.h>
#include <Common/Logger/logger.h>
#include <Common/Data/datamanager.h>
#include <Common/Order/ordermanager.h>

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

using namespace std;

namespace StarQuant
{
extern std::atomic<bool> gShutdown;

Tapdatafeed::Tapdatafeed()
	: loginReqId_(0)
	, isConnected_(false)
	, IsAPIReady(false)
{
	// 创建Tap目录
	string path = CConfig::instance().logDir() + "/Tap/";
	boost::filesystem::path dir(path.c_str());
	boost::filesystem::create_directory(dir);

    TAPIINT32 iResult = TAPIERROR_SUCCEED;
    TapAPIApplicationInfo stAppInfo;
    strcpy(stAppInfo.AuthCode, CConfig::instance().tap_auth_code.c_str());
	strcpy(stAppInfo.KeyOperationLogPath, "./log");
//    SetTapQuoteAPIDataPath("./data");

	// 创建API对象
    ITapQuoteAPI *pAPI = CreateTapQuoteAPI(&stAppInfo, iResult);

    if (NULL == pAPI){
		cout << "create tap Quote API fail，err num is ：" << iResult <<endl;
//		return -1;
    }

	//注册回调接口
	pAPI->SetAPINotify(this);
	this->api_ =pAPI ;


	// 创建API对象
//	this->api_ = CThostFtdcMdApi::CreateFtdcMdApi(path.c_str());
	///注册回调接口
	///@param pSpi 派生自回调接口类的实例
//	this->api_->RegisterSpi(this);
}

Tapdatafeed::~Tapdatafeed() {
	if (api_ != NULL) {
		disconnectFromMarketDataFeed();
	}
}

// start http request thread
bool Tapdatafeed::connectToMarketDataFeed()
{
	if (!isConnected_) {

		///注册前置机网络地址
		///@param pszFrontAddress：前置机网络地址。
		///@remark 网络地址的格式为：“protocol://ipaddress:port”，如：”tcp://127.0.0.1:17001”。
		///@remark “tcp”代表传输协议，“127.0.0.1”代表服务器地址。”17001”代表服务器端口号。
		//登录服务器

		TAPIINT32 iErr = TAPIERROR_SUCCEED;
		//设定服务器IP、端口
		iErr = this->api_->SetHostAddress(CConfig::instance().tap_data_ip.c_str(), CConfig::instance().tap_data_port);
		if(TAPIERROR_SUCCEED != iErr) {
			std::cout << "tap quote SetHostAddress Error:" << iErr <<endl;
			return false;
		}

		TapAPIQuoteLoginAuth stLoginAuth;
		memset(&stLoginAuth, 0, sizeof(stLoginAuth));
		APIStrncpy(stLoginAuth.UserNo, CConfig::instance().tap_user_name.c_str());
		APIStrncpy(stLoginAuth.Password, CConfig::instance().tap_password.c_str());
		stLoginAuth.ISModifyPassword = APIYNFLAG_NO;
		stLoginAuth.ISDDA = APIYNFLAG_NO;
		iErr = this->api_->Login(&stLoginAuth);
		if(TAPIERROR_SUCCEED != iErr) {
			cout << "tap quote connect Error:" << iErr <<endl;
			return false;
		}



//		this->api_->RegisterFront((char*)CConfig::instance().Tap_data_address.c_str());		// 服务器地址

		// 初始化运行环境, 只有调用后, 接口才开始工作
		// if success, server calls for onFrontConnected
//		this->api_->Init();

		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap datasource connecting...!\n", __FILE__, __LINE__, __FUNCTION__);
	}

	return true;
}

// stop http request thread
void Tapdatafeed::disconnectFromMarketDataFeed() {
	this->api_->Disconnect();
	FreeTapQuoteAPI(this->api_);
//	this->api_->Release();
	this->api_ = NULL;
	isConnected_ = false;
}

// is http request thread running ?
bool Tapdatafeed::isConnectedToMarketDataFeed() const {
	return isConnected_;
}

void Tapdatafeed::processMarketMessages() {
	if (!heatbeat(5)) {
		disconnectFromMarketDataFeed();
		return;
	}

	switch (_mkstate) {
		case MK_ACCOUNT:
			requestMarketDataAccountInformation(CConfig::instance().account);
			break;
		case MK_ACCOUNTACK:
			break;
		case MK_REQCONTRACT:
			break;
		case MK_REQCONTRACT_ACK:
			break;
		case MK_REQREALTIMEDATA:
			subscribeMarketData();
			break;
		case MK_REQREALTIMEDATAACK:
			break;
	}
}

////////////////////////////////////////////////////// outgoing function ///////////////////////////////////////

void Tapdatafeed::subscribeMarketData() {
//	cout<<"begin subscribeMarketdata"<<endl;
	for (auto it = CConfig::instance().securities.begin(); it != CConfig::instance().securities.end(); ++it)
	{
//		char* buffer = (char*)(*it).c_str();
//		char* myreq[1] = { buffer };
//		int i = this->api_->SubscribeMarketData(myreq, 1);		// parameter 1 = myreq has one contract; return 0 = 发送订阅行情请求失败

		TapAPIContract stContract1;
		memset(&stContract1, 0, sizeof(stContract1));

		vector<string> v = stringsplit(*it, ' ');

		APIStrncpy(stContract1.Commodity.ExchangeNo, v[0].c_str());
//		APIStrncpy(stContract1.Commodity.CommodityType, v[1].c_str());
		stContract1.Commodity.CommodityType = v[1][0];
		APIStrncpy(stContract1.Commodity.CommodityNo, v[2].c_str());
		APIStrncpy(stContract1.ContractNo1, v[3].c_str());
		stContract1.CallOrPutFlag1 = TAPI_CALLPUT_FLAG_NONE;
		stContract1.CallOrPutFlag2 = TAPI_CALLPUT_FLAG_NONE;
//		cout<<"contract Exchange is "<<stContract1.Commodity.ExchangeNo<<endl;
//		cout<<"contract type is "<<stContract1.Commodity.CommodityType<<endl;
//		cout<<"contract No is "<<stContract1.Commodity.CommodityNo<<endl;
//		cout<<"contract No2 is "<<stContract1.ContractNo1<<endl;
		this->stContract=stContract1;
		this->m_uiSessionID=CConfig::instance().tap_sessionid;
		TAPIINT32 iErr = TAPIERROR_SUCCEED;
		iErr = this->api_->SubscribeQuote(&m_uiSessionID, &stContract);
		if(TAPIERROR_SUCCEED != iErr) {
			std::cout << "SubscribeQuote Error:" << iErr <<endl;
			return;
		}


	}

	/*int count = instruments.size();
	char* *allInstruments = new char*[count];
	for (int i = 0; i < count; i++) {
	allInstruments[i] = new char[7];
	strcpy(allInstruments[i], instruments.at(i).toStdString().c_str());
	}
	api_->SubscribeMarketData(allInstruments, count);*/

	if (_mkstate <= MK_REQREALTIMEDATAACK)
		_mkstate = MK_REQREALTIMEDATAACK;
}

void Tapdatafeed::unsubscribeMarketData(TickerId reqId) {
	for (auto it = CConfig::instance().securities.begin(); it != CConfig::instance().securities.end(); ++it)
	{
		char* buffer = (char*)(*it).c_str();
		char* myreq[1] = { buffer };
//		int i = this->api_->UnSubscribeMarketData(myreq, 1);		// parameter 1 = myreq has one contract; return 0 = 发送订阅行情请求失败
	}
}

void Tapdatafeed::subscribeMarketDepth() {
}

void Tapdatafeed::unsubscribeMarketDepth(TickerId reqId) {
}

void Tapdatafeed::subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH) {

}

void Tapdatafeed::unsubscribeRealTimeBars(TickerId tickerId) {

}

void Tapdatafeed::requestContractDetails() {
}

void Tapdatafeed::requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH) {

}

// 当前置机连接后 (OnFrontConnected), 用户开始请求登陆
// 登陆成功后调用 OnRspUserLogin
void Tapdatafeed::requestMarketDataAccountInformation(const string& account)
{
//	requestUserLogin();

//	if (_mkstate <= MK_ACCOUNTACK)
//		_mkstate = MK_ACCOUNTACK;

	if(IsAPIReady && isConnected_){

		if (_mkstate < MK_REQREALTIMEDATA){
			//std::cout<<"mkstate is "<<_mkstate<<endl;
			_mkstate = MK_REQREALTIMEDATA;
		}

	}


}

//void Tapdatafeed::requestUserLogin() {
//	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap data server logging in....\n", __FILE__, __LINE__, __FUNCTION__);

//	//CThostFtdcReqUserLoginField loginReq;
//	//memset(&loginReq, 0, sizeof(loginReq));
//	CThostFtdcReqUserLoginField loginField = CThostFtdcReqUserLoginField();

//	strcpy(loginField.BrokerID, CConfig::instance().Tap_broker_id.c_str());
//	strcpy(loginField.UserID, CConfig::instance().Tap_user_id.c_str());
//	strcpy(loginField.Password, CConfig::instance().Tap_password.c_str());

//	///用户登录请求
//	int i = this->api_->ReqUserLogin(&loginField, loginReqId_++);		// i=0： 发送登录请求失败
//}

/////登出请求
//void Tapdatafeed::requestUserLogout(int nRequestID) {
//	CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();

//	strcpy(logoutField.BrokerID, CConfig::instance().Tap_broker_id.c_str());
//	strcpy(logoutField.UserID, CConfig::instance().Tap_user_id.c_str());

//	int i = this->api_->ReqUserLogout(&logoutField, nRequestID);
//}
/////////////////////////////////////////////// end of outgoing functions ///////////////////////////////////////



////////////////////////////////////////////////////// incoming function ///////////////////////////////////////

void TAP_CDECL Tapdatafeed::OnRspLogin(TAPIINT32 errorCode, const TapAPIQuotLoginRspInfo *info)
{
	if(TAPIERROR_SUCCEED == errorCode) {
		cout << "TAP行情登录成功，等待行情API初始化..." << endl;
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap data server is connected.\n", __FILE__, __LINE__, __FUNCTION__);

		_mkstate = MK_CONNECTED;			// not used
		isConnected_ = true;

	} else {
		cout << "TAP行情登录失败，错误码:" << errorCode << endl;
		_mkstate = MK_DISCONNECTED;			// not used
		isConnected_ = false;
//		m_Event.SignalEvent();
	}
}

void TAP_CDECL Tapdatafeed::OnAPIReady()
{
	IsAPIReady = true;
	cout << "TAP行情API初始化完成" << endl;
//		if (_mkstate <= MK_REQREALTIMEDATA)
//			_mkstate = MK_REQREALTIMEDATA;
//	m_Event.SignalEvent();
}

void TAP_CDECL Tapdatafeed::OnDisconnect(TAPIINT32 reasonCode)
{
	cout << "TAP行情API断开,断开原因:"<<reasonCode << endl;
}

void TAP_CDECL Tapdatafeed::OnRspChangePassword(TAPIUINT32 sessionID, TAPIINT32 errorCode)
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapdatafeed::OnRspQryExchange(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIExchangeInfo *info)
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapdatafeed::OnRspQryCommodity(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteCommodityInfo *info)
{
	cout << __FUNCTION__ << " is called." << endl;
	cout << info->CommodityEngName<<" "<<info->ContractSize<<endl;
}

void TAP_CDECL Tapdatafeed::OnRspQryContract(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteContractInfo *info)
{
	cout << __FUNCTION__ << " is called." << endl;
	cout << info->ContractName<<" "<<info->ContractExpDate<<" "<<endl;
}

void TAP_CDECL Tapdatafeed::OnRtnContract(const TapAPIQuoteContractInfo *info)
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapdatafeed::OnRspSubscribeQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteWhole *info)
{
	if (TAPIERROR_SUCCEED == errorCode)
	{
		cout << "行情订阅成功 ";
		if (NULL != info)
		{
			cout << info->DateTimeStamp << " "
				 << info->TradingState<< " "
				 << info->Contract.Commodity.ExchangeNo << " "
				 << info->Contract.Commodity.CommodityType << " "
				 << info->Contract.Commodity.CommodityNo << " "
				 << info->Contract.ContractNo1 << " "
				 << info->QLastPrice<<" "
				 <<info->QBidPrice[0]<<" "
			     <<info->QAskPrice[0]<<" "
				 <<info->QBidPrice[1]<<" "
			     <<info->QAskPrice[1]<<" "
				 <<info->QBidPrice[2]<<" "
			     <<info->QAskPrice[2]<<" "
				 <<info->QBidPrice[3]<<" "
			     <<info->QAskPrice[3]<<" "
				 <<info->QBidPrice[4]<<" "
			     <<info->QAskPrice[4]<<" "
				 // ...
				 <<endl;

            string ticker= info->Contract.Commodity.ExchangeNo;
			ticker +=" ";
			ticker +=info->Contract.Commodity.CommodityType;
			ticker +=" ";
			ticker +=info->Contract.Commodity.CommodityNo;
			ticker +=" ";
			ticker +=info->Contract.ContractNo1;





			Tick_L5 k;

			k.time_ = ymdhms();
			k.datatype_ = DataType::DT_Tick_L5;
			k.fullsymbol_ = ticker;
			k.price_ = info->QLastPrice;
			k.size_ = info->QTotalQty;			// not valid without volume
	//		k.bidprice_L1_ = info->;
	//		k.bidsize_L1_ = info->BidVolume1;
	//		k.askprice_L1_ = info->AskPrice1;
	//		k.asksize_L1_ = info->AskVolume1;
	//		k.open_interest = info->OpenInterest;
	//		k.open_ = info->OpenPrice;
	//		k.high_ = info->HighestPrice;
	//		k.low_ = info->LowestPrice;
	//		k.pre_close_ = info->PreClosePrice;
	//		k.upper_limit_price_ = info->UpperLimitPrice;
	//		k.lower_limit_price_ = info->LowerLimitPrice;
			
	//		msgq_pub_->sendmsg(k.serialize());





		}

	} else{
		cout << "行情订阅失败，错误码：" << errorCode <<endl;
	}
}

void TAP_CDECL Tapdatafeed::OnRspUnSubscribeQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIContract *info)
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapdatafeed::OnRtnQuote(const TapAPIQuoteWhole *info)
{
	if (NULL != info)
	{
		cout << "行情更新:"<<"tick time"
			 << info->DateTimeStamp <<" rec time"<<ymdhmsf()
			 << info->Contract.Commodity.ExchangeNo << " "
			 << info->Contract.Commodity.CommodityType << " "
			 << info->Contract.Commodity.CommodityNo << " "
			 << info->Contract.ContractNo1 << " "
			 << info->QLastPrice<<" "
			 << info->QOpeningPrice<<" "
			 <<info->QPositionQty<<" "
			 <<info->QBidPrice[0]<<" "
			 <<info->QAskPrice[0]<<" "
			 // ...
			 <<endl;

            string ticker= info->Contract.Commodity.ExchangeNo;
			ticker += " ";
			ticker += info->Contract.Commodity.CommodityType;
			ticker += " ";
			ticker += info->Contract.Commodity.CommodityNo;
			ticker += " ";
			ticker += info->Contract.ContractNo1;

		Tick_L5 k;

//		k.time_ = hmsf();
		k.time_ =info->DateTimeStamp;
		k.datatype_ = DataType::DT_Tick_L5;
		k.fullsymbol_ = ticker;
		k.price_ = info->QLastPrice;
		k.size_ = info->QLastQty;			// not valid without volume
		k.depth_ = 5;
		k.bidprice_L1_ = info->QBidPrice[0];
		k.bidsize_L1_ = info->QBidQty[0];
		k.askprice_L1_ = info->QAskPrice[0];
		k.asksize_L1_ = info->QAskQty[0];
		k.bidprice_L2_ = info->QBidPrice[1];
		k.bidsize_L2_ = info->QBidQty[1];
		k.askprice_L2_ = info->QAskPrice[1];
		k.asksize_L2_ = info->QAskQty[1];
		k.bidprice_L3_ = info->QBidPrice[2];
		k.bidsize_L3_ = info->QBidQty[2];
		k.askprice_L3_ = info->QAskPrice[2];
		k.asksize_L3_ = info->QAskQty[2];		
		k.bidprice_L4_ = info->QBidPrice[3];
		k.bidsize_L4_ = info->QBidQty[3];
		k.askprice_L4_ = info->QAskPrice[3];
		k.asksize_L4_ = info->QAskQty[3];	
		k.bidprice_L5_ = info->QBidPrice[4];
		k.bidsize_L5_ = info->QBidQty[4];
		k.askprice_L5_ = info->QAskPrice[4];
		k.asksize_L5_ = info->QAskQty[4];	
		k.open_interest = info->QPositionQty;
		k.open_ = info->QOpeningPrice;
		k.high_ = info->QHighPrice;
		k.low_ = info->QLowPrice;
		k.pre_close_ = info->QPreClosingPrice;
		k.upper_limit_price_ = info->QLimitUpPrice;
		k.lower_limit_price_ = info->QLimitDownPrice;
		
		msgq_pub_->sendmsg(k.serialize());



	}
}



}
