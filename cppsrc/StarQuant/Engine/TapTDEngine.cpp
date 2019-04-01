#include <mutex>
#include <Trade/orderstatus.h>
#include <Trade/fill.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
#include <Data/datamanager.h>
#include <Common/logger.h>
#include <Common/util.h>
#include <Engine/TapTDEngine.h>
#include <APIs/Tap/TapTradeAPI.h>
#include <APIs/Tap/TapAPIError.h>

using namespace std;
namespace StarQuant
{
	//extern std::atomic<bool> gShutdown;
TapTDEngine::TapTDEngine() 
	: sessionID_(0)
	, m_brokerOrderId_(0)
{
	init();
}

TapTDEngine::~TapTDEngine() {
	stop();
}

void TapTDEngine::init(){
	if (msgq_recv_ == nullptr){
		msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
	}	
	//创建目录
	name_ = "TAP_TD";
	tapacc_ = CConfig::instance()._apimap["TAP"];
	string path = CConfig::instance().logDir() + "/Tap/";
	boost::filesystem::path dir(path.c_str());
	boost::filesystem::create_directory(dir);
	///创建TraderApi
	TAPIINT32 iResult = TAPIERROR_SUCCEED;
	TapAPIApplicationInfo stAppInfo;
	strcpy(stAppInfo.AuthCode, tapacc_.auth_code.c_str());
	strcpy(stAppInfo.KeyOperationLogPath, "./log");
	// TapAPITradeLoginAuth stLoginAuth;
	// strcpy(stLoginAuth.UserNo, CConfig::instance().tap_user_name.c_str());
	// strcpy(stLoginAuth.Password, CConfig::instance().tap_password.c_str());
	// stLoginAuth.ISModifyPassword = APIYNFLAG_NO;
	// stLoginAuth.ISDDA = APIYNFLAG_NO;
	ITapTradeAPI *pAPI = CreateTapTradeAPI(&stAppInfo, iResult);
	if (NULL == pAPI){
		cout << "create tap trade API fail，err num is ：" << iResult <<endl;
	}
	//注册回调接口
	pAPI->SetAPINotify(this);
	this->api_ = pAPI ;
}

void TapTDEngine::stop(){
	int tmp = disconnect();
	int count = 0;
	while( estate_ != DISCONNECTED){
		msleep(100);
		count++;
		if(count > 20)
			break;
	}
	estate_ = EState::STOP; 
	if (api_ != NULL) {
		FreeTapTradeAPI(this->api_);
		this->api_ = NULL;
	}
}

bool TapTDEngine::connect() {
	TAPIINT32 iErr = TAPIERROR_SUCCEED;
	TapAPITradeLoginAuth stLoginAuth;
	memset(&stLoginAuth, 0, sizeof(stLoginAuth));
	strcpy(stLoginAuth.UserNo, tapacc_.userid.c_str());
	strcpy(stLoginAuth.Password, tapacc_.password.c_str());
	stLoginAuth.ISModifyPassword = APIYNFLAG_NO;
	stLoginAuth.ISDDA = APIYNFLAG_NO;
	int count = 0;
	while(estate_ != EState::LOGIN_ACK){
		switch(estate_){
			case EState::DISCONNECTED:
				//设定服务器IP、端口
				iErr = this->api_->SetHostAddress(tapacc_.td_ip.c_str(), tapacc_.td_port);
				if(TAPIERROR_SUCCEED != iErr) {
					std::cout << "tap td SetHostAddress Error:" << iErr <<endl;
				}
				iErr = this->api_->Login(&stLoginAuth);
				estate_ = CONNECTING;
				count++;
				if(TAPIERROR_SUCCEED != iErr) {
					cout << "tap td connect Error:" << iErr <<endl;
					estate_ = EState::DISCONNECTED;
					break;
				}
				PRINT_TO_FILE("INFO:[%s,%d][%s]Tap td logining...!\n", __FILE__, __LINE__, __FUNCTION__);
				break;
			case EState::CONNECTING:
				msleep(500);
				break;
			case EState::CONNECT_ACK:
				estate_ = EState::LOGINING;
				break;
			case EState::LOGINING:
				msleep(500);
				break;
			default:
				msleep(100);
				break;
		}
		if(count > 5){
			cout<<"too many tries fails, give up connecting"<<endl;
			//estate_ = EState::DISCONNECTED;
			return false;
		}
	}
	return true;
}

bool TapTDEngine::disconnect() {
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap td disconnecting!\n", __FILE__, __LINE__, __FUNCTION__);
	estate_ = LOGOUTING;
	int i = api_->Disconnect();
	if (i != TAPIERROR_SUCCEED){
		cout<<"tap td disconnect error:"<<i<<endl;
		return false;
	}
	estate_ = LOGOUTING;
	return true;
}

void TapTDEngine::start(){
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
			case MSG_TYPE_TD_ENGINE_OPEN:
				tmp = connect();
				break;
			case MSG_TYPE_TD_ENGINE_CLOSE:
				tmp = disconnect();
				break;
			case MSG_TYPE_ORDER:
				if (estate_ == LOGIN_ACK){
					PRINT_TO_FILE_AND_CONSOLE("INFO[%s,%d][%s]receive order: %s\n", __FILE__, __LINE__, __FUNCTION__, msgin.c_str());
					insertOrder(v);
				}
				else{
					cout<<"TAP_TD is not connected,can not place order! "<<endl;
					string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"CTP_TD is not connected,can not place order";
					lock_guard<std::mutex> g(IEngine::sendlock_);
					IEngine::msgq_send_->sendmsg(msgout);
				}
				break;
			case MSG_TYPE_CANCEL_ORDER:
				if (estate_ == LOGIN_ACK){
					PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order clientorderId=%ld\n", __FILE__, __LINE__, __FUNCTION__, stol(v[3]));
					cancelOrder(v);
				}
				else{
					cout<<"TAP_TD is not connected,can not cancel order! "<<endl;
					string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"CTP_TD is not connected,can not cancel order";
					lock_guard<std::mutex> g(IEngine::sendlock_);
					IEngine::msgq_send_->sendmsg(msgout);
				}
				break;
			case MSG_TYPE_QRY_POS:
				if (estate_ == LOGIN_ACK){
					queryPosition();//TODO:区分不同来源，回报中添加目的地信息
				}
				else{
					cout<<"TAP_TD is not connected,can not cancel order! "<<endl;
					string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"CTP_TD is not connected,can not cancel order";
					lock_guard<std::mutex> g(IEngine::sendlock_);
					IEngine::msgq_send_->sendmsg(msgout);
				}
				break;
			case MSG_TYPE_QRY_ACCOUNT:
				if (estate_ == LOGIN_ACK){
					queryAccount();
				}
				else{
					cout<<"TAP_TD is not connected,can not cancel order! "<<endl;
					string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"CTP_TD is not connected,can not cancel order";
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

void TapTDEngine::insertOrder(const vector<string>& v) {
	std::shared_ptr<Order> o = make_shared<Order>();
	lock_guard<mutex> g(oid_mtx);
	o->serverOrderId = m_serverOrderId++;
	o->brokerOrderId = m_brokerOrderId_++;
	o->createTime = ymdhmsf();	
	o->orderStatus = OrderStatus::OS_NewBorn;	
	o->api = v[0];// = name_;	
	o->source = stoi(v[1]);
	o->clientId = stoi(v[1]);
	o->account = v[3];
	o->clientOrderId = stoi(v[4]);
	o->orderType = static_cast<OrderType>(stoi(v[5]));
	o->fullSymbol = v[6];
	o->orderSize = stoi(v[7]);
	if (o->orderType == OrderType::OT_Limit){
		o->limitPrice = stof(v[8]);
	}else if (o->orderType == OrderType::OT_StopLimit){
		o->stopPrice = stof(v[8]);
	}
	o->orderFlag = static_cast<OrderFlag>(stoi(v[9]));
	o->tag = v[10];
	OrderManager::instance().trackOrder(o);
	// call api to send order
	TAPIINT32 iErr = TAPIERROR_SUCCEED;
	TapAPINewOrder stNewOrder;
	memset(&stNewOrder, 0, sizeof(stNewOrder));
	string symbol = o->fullSymbol;
	vector<string> symv = stringsplit(symbol, ' ');
	strcpy(stNewOrder.AccountNo, tapacc_.userid.c_str());			
	strcpy(stNewOrder.ExchangeNo, symv[0].c_str());		
	stNewOrder.CommodityType = symv[1][0];		
	strcpy(stNewOrder.CommodityNo, symv[2].c_str());		
	strcpy(stNewOrder.ContractNo, symv[3].c_str());
	//stNewOrder.RefInt = order->brokerOrderId;
	strcpy(stNewOrder.RefString, to_string(o->serverOrderId).c_str());
	stNewOrder.OrderType = OrderTypeToTapOrderType(o->orderType);
	if (o->orderType == OrderType::OT_Limit){
		stNewOrder.OrderPrice = o->limitPrice;
	}else if (o->orderType == OrderType::OT_StopLimit){
		stNewOrder.StopPrice = o->stopPrice;
	}
	stNewOrder.OrderSide = o->orderSize > 0 ? TAPI_SIDE_BUY : TAPI_SIDE_SELL;			
	stNewOrder.PositionEffect = OrderFlagToTapPositionEffect(o->orderFlag);	
	stNewOrder.OrderQty = std::abs(o->orderSize);		
	strcpy(stNewOrder.StrikePrice, "");		
	stNewOrder.CallOrPutFlag = TAPI_CALLPUT_FLAG_NONE;		
	stNewOrder.OrderSource = TAPI_ORDER_SOURCE_ESUNNY_API;		
	stNewOrder.TimeInForce = TAPI_ORDER_TIMEINFORCE_GFD;		
	strcpy(stNewOrder.ExpireTime, "");		
	stNewOrder.IsRiskOrder = APIYNFLAG_NO;
	strcpy(stNewOrder.ContractNo2, "");		
	strcpy(stNewOrder.StrikePrice2, "");		
	stNewOrder.CallOrPutFlag2 = TAPI_CALLPUT_FLAG_NONE;
	stNewOrder.PositionEffect2 = TAPI_PositionEffect_NONE;	
	stNewOrder.HedgeFlag2 = TAPI_HEDGEFLAG_NONE;
	strcpy(stNewOrder.InquiryNo,"");			
	stNewOrder.HedgeFlag = TAPI_HEDGEFLAG_T;
	stNewOrder.TacticsType = TAPI_TACTICS_TYPE_NONE;		
	stNewOrder.TriggerCondition = TAPI_TRIGGER_CONDITION_NONE;	
	stNewOrder.TriggerPriceType = TAPI_TRIGGER_PRICE_NONE;	
	stNewOrder.AddOneIsValid = APIYNFLAG_NO;	
	stNewOrder.MarketLevel = TAPI_MARKET_LEVEL_0;
	stNewOrder.OrderDeleteByDisConnFlag = APIYNFLAG_NO; 
	
	iErr = this->api_->InsertOrder(&this->sessionID_, &stNewOrder);
	PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Placing Order : sessionid = %d,serverorderId=%ld, clientorderId=%ld,fullSymbol=%s\n", __FILE__, __LINE__, __FUNCTION__, this->sessionID_,o->serverOrderId, o->clientOrderId,o->fullSymbol.c_str());
	if (iErr == TAPIERROR_SUCCEED){
		lock_guard<mutex> g(orderStatus_mtx);
		o->orderStatus = OrderStatus::OS_Submitted;
		string msg = o->serialize() 
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
		cout<<"Tap td send orderestatus msg:"<<msg<<endl;
		lock_guard<mutex> g2(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msg);
	}
	else{
		cout<<"tap insert order error "<<iErr<<endl;
		lock_guard<mutex> g(orderStatus_mtx);
		o->orderStatus = OrderStatus::OS_Error;
		string msg = o->serialize() 
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
		cout<<"Tap td send orderestatus msg:"<<msg<<endl;
		lock_guard<mutex> g2(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msg);		
	}
}

void TapTDEngine::cancelOrder(long oid) {
	PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order m_serverorderId=%ld\n", __FILE__, __LINE__, __FUNCTION__, (long)oid);
	std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
	if (o != nullptr){
		TAPIINT32 iErr = TAPIERROR_SUCCEED;
		TapAPIOrderCancelReq myreq;
		//strcpy(myreq.OrderNo, o->orderNo.c_str());
		strcpy(myreq.RefString,to_string(oid).c_str());
		iErr = this->api_->CancelOrder(&this->sessionID_, &myreq);
		if(iErr != TAPIERROR_SUCCEED){
			cout<<"Tap TD cancle order error "<<iErr<<endl;
		}
	}else{
		cout<<"ordermanager cannot find order, cannot cancel!"<<endl;
	}
}

void TapTDEngine::cancelOrder(const vector<string>& v) {
	int source = stoi(v[1]);
	long coid = stol(v[3]);
	PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order clientOrderId=%ld\n", __FILE__, __LINE__, __FUNCTION__, coid);
	TAPIINT32 iErr = TAPIERROR_SUCCEED;
	TapAPIOrderCancelReq myreq;
	std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromSourceAndClientOrderId(source,coid);
	if (o != nullptr){
		//strcpy(myreq.OrderNo, ono.c_str());
		strcpy(myreq.RefString, to_string(o->serverOrderId).c_str());
		iErr = this->api_->CancelOrder(&this->sessionID_, &myreq);	
		if(iErr != TAPIERROR_SUCCEED){
			cout<<"Tap TD cancle order error "<<iErr<<endl;
		}		
	}
	else{
		cout<<"ordermanager cannot find order!"<<endl;
	}
}

// 查询账户
void TapTDEngine::queryAccount(){
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap td requests account and fund information.\n", __FILE__, __LINE__, __FUNCTION__);
	TAPIINT32 iErr1 = TAPIERROR_SUCCEED;
	TAPIINT32 iErr2 = TAPIERROR_SUCCEED;
	TapAPIAccQryReq myaccreq;
	TapAPIFundReq myfundreq;
	strcpy(myaccreq.AccountNo, tapacc_.userid.c_str());
	strcpy(myfundreq.AccountNo, tapacc_.userid.c_str());
	iErr1 = this->api_->QryAccount(&this->sessionID_, &myaccreq);
	if (iErr1 != TAPIERROR_SUCCEED){
		cout<<"Tap td qry acc error "<<iErr1<<endl;
	}
	iErr2 = this->api_->QryFund(&this->sessionID_, &myfundreq);	
	if (iErr2 != TAPIERROR_SUCCEED){
		cout<<"Tap qry fund error "<<iErr2<<endl;
	}		
}

void TapTDEngine::queryOrder(const vector<string>& msgv)
{
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap td qry open orders.\n", __FILE__, __LINE__, __FUNCTION__);
	TAPIINT32 iErr = TAPIERROR_SUCCEED;
	TapAPIOrderQryReq myreq;
	//myreq.OrderQryType = TAPI_ORDER_QRY_TYPE_ALL;
	//myreq.OrderQryType = msgv[3];
	myreq.OrderQryType = TAPI_ORDER_QRY_TYPE_UNENDED;
	iErr = this->api_->QryOrder(&this->sessionID_, &myreq);	
	if (iErr != TAPIERROR_SUCCEED){
		cout<<"qry order error "<<iErr<<endl;
	}			
}
/// 查询持仓信息， trigger onRspQryInvestorPosition
void TapTDEngine::queryPosition() {
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap td qry positions.\n", __FILE__, __LINE__, __FUNCTION__);
	TAPIINT32 iErr = TAPIERROR_SUCCEED;
	TapAPIPositionQryReq myreq;
	iErr = this->api_->QryPosition(&this->sessionID_, &myreq);		
	if (iErr != TAPIERROR_SUCCEED)
	{
		cout<<"Tap td qry position ierr:"<<iErr<<endl;
	}
}
////////////////////////////////////////////////////// begin callback/incoming function ///////////////////////////////////////

void TAP_CDECL TapTDEngine::OnConnect() {
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap Td connected; Continue to login.\n", __FILE__, __LINE__, __FUNCTION__);
	estate_ = CONNECT_ACK;
}

void TAP_CDECL TapTDEngine::OnAPIReady()    {
	estate_ = LOGIN_ACK;
	cout << "TAP交易API初始化完成" << endl;
}

void TAP_CDECL TapTDEngine::OnRspLogin( TAPIINT32 errorCode, const TapAPITradeLoginRspInfo *loginRspInfo )
{
	if(TAPIERROR_SUCCEED == errorCode) {
		cout << "TAP交易登录成功，等待交易API初始化..." << endl;
		estate_ = LOGINING;
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap td server user logged in, waiting api ready \n.",__FILE__, __LINE__, __FUNCTION__);
		//sendGeneralMessage(string("Tap broker server user logged in:"));
	}
	else {
		estate_ = DISCONNECTED;
		cout << "TAP交易登录失败，错误码:" << errorCode << endl;
		PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server user login failed: Errorcode=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, errorCode);
		//sendGeneralMessage(string("Tap Trader Server OnRspUserLogin error:") + SERIALIZATION_SEPARATOR + to_string(errorCode) );
		}     
}

void TapTDEngine::OnDisconnect(TAPIINT32 reasonCode) {
	cout << "TAP API断开,断开原因:"<<reasonCode << endl;
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker disconnected, nReason=%d.\n", __FILE__, __LINE__, __FUNCTION__, reasonCode);
	estate_ = DISCONNECTED;
}

void TAP_CDECL TapTDEngine::OnRtnFund( const TapAPIFundData *info ){
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRtnFund: AccountNo=%s, Available=%.2f, PreBalance=%.2f,Balance=%.2f, Commission=%.2f, CurrMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f\n",
		__FILE__, __LINE__, __FUNCTION__, info->AccountNo, info->Available, info->PreBalance,
		info->Balance, info->AccountFee,info->AccountMaintenanceMargin,info->CloseProfit,info->PositionProfit);
	AccountInfo accinfo;
	accinfo.AccountID = info->AccountNo;
	accinfo.PreviousDayEquityWithLoanValue = info->PreBalance;
	accinfo.NetLiquidation = info->Balance;
	accinfo.AvailableFunds = info->Available;
	accinfo.Commission = info->AccountFee;
	accinfo.FullMaintainanceMargin = info->AccountMaintenanceMargin;
	accinfo.RealizedPnL = info->CloseProfit;
	accinfo.UnrealizedPnL = info->PositionProfit;
	PortfolioManager::instance().accinfomap_[tapacc_.id] = accinfo;
	string msg = "0"  // destination is all
		+ SERIALIZATION_SEPARATOR + name_  //source
		+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_ACCOUNT)
		+ SERIALIZATION_SEPARATOR + accinfo.AccountID						// AccountID
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.PreviousDayEquityWithLoanValue)	// prev-day
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.NetLiquidation)				// balance
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.AvailableFunds)				// available
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.Commission)					// commission
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.FullMaintainanceMargin)		// margin
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.RealizedPnL)					// closed pnl
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.UnrealizedPnL)					// open pnl
		+ SERIALIZATION_SEPARATOR + ymdhmsf();
	cout<<"Tap Td send account fund msg "<<msg<<endl;
	lock_guard<mutex> g(IEngine::sendlock_);
	IEngine::msgq_send_->sendmsg(msg);
}

void TAP_CDECL TapTDEngine::OnRtnContract( const TapAPITradeContractInfo *info ){
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
}

void TAP_CDECL TapTDEngine::OnRtnOrder( const TapAPIOrderInfoNotice *info ){
	if(NULL == info){
		return;
	}
	if (info->ErrorCode != TAPIERROR_SUCCEED) {
		cout << "服务器返回了一个关于委托信息的错误：" << info->ErrorCode << endl;
		return;
	} 
	if (info->OrderInfo) {
		long soid = stol(info->OrderInfo->RefString);
		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(soid);
		if ((o != nullptr))			//if (info->SessionID == this->sessionID_)
		{
			if (TAPIERROR_SUCCEED != info->OrderInfo->ErrorCode){
				cout << "报单失败，"
					<< "错误码:"<<info->OrderInfo->ErrorCode << ","
					<< "委托编号:"<<info->OrderInfo->OrderNo
					<<endl;
				PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server OnRtnOrder: ErrorID=%d, OrderNo=%s.\n",
					__FILE__, __LINE__, __FUNCTION__, info->OrderInfo->ErrorCode, info->OrderInfo->OrderNo);
				lock_guard<mutex> g(orderStatus_mtx);
				o->orderStatus = OS_Error;
				o->orderNo = info->OrderInfo->OrderNo;
				//o->api = info->OrderInfo->OrderSource;					
				string msg = o->serialize() 
					+ SERIALIZATION_SEPARATOR + ymdhmsf();
				cout<<"Ctp td send orderestatus msg:"<<msg<<endl;
				lock_guard<mutex> g2(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msg);
			} else{
				cout << "报单成功，"
					<< "状态:"<<info->OrderInfo->OrderState << ","
					<< "委托编号:"<<info->OrderInfo->OrderNo <<" "
					<<endl;
				PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRtnOrder: serverOrderId=%s, LimitPrice=%.2f, VolumeTotalOriginal=%d, Side=%c, Direction=%c.\n",
					__FILE__, __LINE__, __FUNCTION__, info->OrderInfo->RefString, info->OrderInfo->OrderPrice, info->OrderInfo->OrderQty, info->OrderInfo->OrderSide, info->OrderInfo->PositionEffect);
				lock_guard<mutex> g(orderStatus_mtx);
				o->orderStatus = TapOrderStatusToOrderStatus(info->OrderInfo->OrderState);
				o->orderNo = info->OrderInfo->OrderNo;
				//o->api = info->OrderInfo->OrderSource;
				string msg = o->serialize() 
					+ SERIALIZATION_SEPARATOR + ymdhmsf();
				cout<<"Ctp td send orderestatus msg:"<<msg<<endl;
				lock_guard<mutex> g2(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msg);
			}
		}
		else {
			//the order is from other brokerage, creat an order for ordermanager 
			PRINT_TO_FILE_AND_CONSOLE("Warning:[%s,%d][%s]Tap Trader server OnRtnOrder not in OM tracklist, sessionid = %d, OrderNo=%s\n",
				__FILE__, __LINE__, __FUNCTION__, info->SessionID,info->OrderInfo->OrderNo);
			lock_guard<mutex> g(oid_mtx);
			std::shared_ptr<Order> o = make_shared<Order>();
			//o->account = info->OrderInfo->AccountNo;
			//o->api = info->OrderInfo->OrderSource;;
			o->account = tapacc_.id;
			o->api = "others";
			char temp[128] = {};
			sprintf(temp, "%s %c %s %s", info->OrderInfo->ExchangeNo, info->OrderInfo->CommodityType, info->OrderInfo->CommodityNo,info->OrderInfo->ContractNo);
			o->fullSymbol = temp;
			o->serverOrderId = m_serverOrderId;
			m_serverOrderId++;
			o->orderStatus = TapOrderStatusToOrderStatus(info->OrderInfo->OrderState);
			o->orderFlag = TapPositionEffectToOrderFlag(info->OrderInfo->PositionEffect);
			o->orderNo = info->OrderInfo->OrderNo;
			o->orderSize = (info->OrderInfo->OrderSide == TAPI_SIDE_BUY ? 1 : -1) * info->OrderInfo->OrderQty;
			o->createTime = ymdhmsf();
			o->orderType = TapOrderTypeToOrderType(info->OrderInfo->OrderType);
			if (o->orderType == OrderType::OT_Limit){
				o->limitPrice = info->OrderInfo->OrderPrice;
			}else if (o->orderType == OrderType::OT_StopLimit){
				o->stopPrice = info->OrderInfo->StopPrice;
			}
			OrderManager::instance().trackOrder(o);
			string msg = o->serialize() 
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
			cout<<"Ctp td send orderestatus msg:"<<msg<<endl;
			lock_guard<mutex> g2(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
	}
}

void TAP_CDECL TapTDEngine::OnRtnFill( const TapAPIFillInfo *info ){
	if(info == NULL){
		return;
	}
	PRINT_TO_FILE("INFO:[%s,%d][%s]TAP trade server OnRtnFill details: OrderNo=%s,  MatchTime=%s, Side=%c, Direction=%c, Price=%f, Volume=%d.\n",
		__FILE__, __LINE__, __FUNCTION__, info->OrderNo, info->MatchDateTime,
		info->MatchSide, info->PositionEffect, info->MatchPrice, info->MatchQty);		// TODO: diff between tradeid and orderref
	Fill t;
	char temp[128] = {};
	sprintf(temp, "%s %c %s %s", info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo);
	string sym = temp;
	//t.account = info->AccountNo;
	t.fullSymbol = sym;
	t.tradetime = info->MatchDateTime;
	t.orderNo = info->OrderNo;
	t.tradeNo = info->MatchNo;
	t.tradePrice = info->MatchPrice;
	t.tradeSize = (info->MatchSide == TAPI_SIDE_BUY ? 1 : -1)* info->MatchQty;
	t.fillflag = TapPositionEffectToOrderFlag(info->PositionEffect);
	t.commission = info->FeeValue;
	auto o = OrderManager::instance().retrieveOrderFromOrderNo(info->OrderNo);
	if (o != nullptr) {
		t.serverOrderId = o->serverOrderId;
		t.clientOrderId = o->clientOrderId;
		t.brokerOrderId = o->brokerOrderId;
		o->fillNo = t.tradeNo;
		t.account = o->account;
		t.api = o->api;
		t.source = o->source;
		OrderManager::instance().gotFill(t);
		string msg = t.serialize()
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
		cout<<"Tap td send fill msg:"<<msg<<endl;
		lock_guard<mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msg);	
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]fill order id is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->OrderNo);
		t.api = "others";
		t.account = tapacc_.id;
		string msg = t.serialize()
			+ SERIALIZATION_SEPARATOR + ymdhmsf();
		cout<<"Tap td send fill msg:"<<msg<<endl;
		lock_guard<mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msg);
	}		
}


void TAP_CDECL TapTDEngine::OnRtnClose( const TapAPICloseInfo *info ){
	if(info == NULL){
		return;
	}
	char temp[128] = {};
	sprintf(temp, "%s %c %s %s", info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo);
	string sym = temp;
	Position pos;
	pos._type ='c';
	pos._fullsymbol = sym;
	//pos._openapi = info->OpenMatchSource;
	//pos._closeapi = info->CloseMatchSource;
	pos._size = (info->CloseSide == TAPI_SIDE_BUY ? 1 : -1) * info->CloseQty;
	pos._avgprice = info->ClosePrice;
	pos._closedpl = info->CloseProfit;
	//pos._account = info->AccountNo;
	pos._account = tapacc_.id;
	pos._openorderNo = info->OpenMatchNo;
	pos._closeorderNo = info->CloseMatchNo;
	auto oo = OrderManager::instance().retrieveOrderFromMatchNo(info->OpenMatchNo);
	if (oo != nullptr) {
		pos._opensource =  oo->source;
		pos._openapi = oo->api;
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position openorderNO is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->OpenMatchNo);
	}		
	auto co = OrderManager::instance().retrieveOrderFromMatchNo(info->CloseMatchNo);
	if (co != nullptr) {
		pos._closesource =  co->source;
		pos._closeapi = co->api;
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position closeorderNO is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->CloseMatchNo);
	}	
	// PortfolioManager::instance().Add(pos);
	string msg = "0"  // destination is all
			+ SERIALIZATION_SEPARATOR + name_  //source
			+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_POS)
			+ SERIALIZATION_SEPARATOR + pos._type
			+ SERIALIZATION_SEPARATOR + pos._account
			+ SERIALIZATION_SEPARATOR + pos._posNo
			+ SERIALIZATION_SEPARATOR + pos._openorderNo
			+ SERIALIZATION_SEPARATOR + pos._openapi
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._opensource)
			+ SERIALIZATION_SEPARATOR + pos._closeorderNo			
			+ SERIALIZATION_SEPARATOR + pos._closeapi
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._closesource)									
			+ SERIALIZATION_SEPARATOR + pos._fullsymbol
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._avgprice)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._pre_size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._freezed_size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._closedpl)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._openpl)
			+ SERIALIZATION_SEPARATOR + ymdhmsf();
		cout<<"Tap TD send postion msg:"<<msg<<endl;
		lock_guard<mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msg);
}

void TAP_CDECL TapTDEngine::OnRtnPosition( const TapAPIPositionInfo *info ){	
	if(info == NULL){
		return;
	}
	char temp[128] = {};	
	sprintf(temp, "%s %c %s %s", info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo);
	string sym = temp;
	PRINT_TO_FILE("INFO:[%s,%d][%s]tap broker server OnRtnPosition, fullsymbol=%s %c %s %s, PosPrice=%f, PosQty=%d, MatchSide=%c, PositionProfit=%.2f, PositionCost=%.2f, TradingTime=%s\n",
		__FILE__, __LINE__, __FUNCTION__, info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo,  
		info->PositionPrice,  info->PositionQty, info->MatchSide, info->PositionProfit, info->Turnover, info->MatchTime );
	Position pos;
	pos._type ='n';
	pos._fullsymbol = sym;
	pos._posNo = info->PositionNo;
	pos._size = (info->MatchSide == TAPI_SIDE_BUY ? 1 : -1) * info->PositionQty;
	pos._avgprice = info->PositionPrice;
	pos._openpl = info->PositionProfit;
	pos._account = tapacc_.id;
	pos._openorderNo = info->OrderNo;
	auto oo = OrderManager::instance().retrieveOrderFromMatchNo(info->MatchNo);
	if (oo != nullptr) {
		pos._opensource =  oo->source;
		pos._openapi = oo->api;
	}
	else {
		//cout<<info->MatchNo<<endl;
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position MatchNO is not tracked. MatchNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->MatchNo);
	}	
	PortfolioManager::instance().Add(pos);
	string msg = "0"  // destination is all
			+ SERIALIZATION_SEPARATOR + name_  //source
			+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_POS)
			+ SERIALIZATION_SEPARATOR + pos._type
			+ SERIALIZATION_SEPARATOR + pos._account
			+ SERIALIZATION_SEPARATOR + pos._posNo
			+ SERIALIZATION_SEPARATOR + pos._openorderNo
			+ SERIALIZATION_SEPARATOR + pos._openapi
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._opensource)
			+ SERIALIZATION_SEPARATOR + pos._closeorderNo			
			+ SERIALIZATION_SEPARATOR + pos._closeapi
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._closesource)									
			+ SERIALIZATION_SEPARATOR + pos._fullsymbol
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._avgprice)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._pre_size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._freezed_size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._closedpl)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._openpl)
			+ SERIALIZATION_SEPARATOR + ymdhmsf();
		cout<<"Tap TD send postion msg:"<<msg<<endl;
		lock_guard<mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msg);
}


void TAP_CDECL TapTDEngine::OnRtnPositionProfit( const TapAPIPositionProfitNotice *info )
{	
	if(info == NULL || info->Data == NULL){
		return;
	}
	Position pos;
	pos._posNo = info->Data->PositionNo;
	pos._openpl = info->Data->PositionProfit;
	pos._type ='u';
	// PortfolioManager::instance().Add(pos);
	string msg = "0"  // destination is all
		+ SERIALIZATION_SEPARATOR + name_  //source
		+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_POS)
		+ SERIALIZATION_SEPARATOR + pos._type
		+ SERIALIZATION_SEPARATOR + pos._account
		+ SERIALIZATION_SEPARATOR + pos._posNo
		+ SERIALIZATION_SEPARATOR + pos._openorderNo
		+ SERIALIZATION_SEPARATOR + pos._openapi
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._opensource)
		+ SERIALIZATION_SEPARATOR + pos._closeorderNo			
		+ SERIALIZATION_SEPARATOR + pos._closeapi
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._closesource)									
		+ SERIALIZATION_SEPARATOR + pos._fullsymbol
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._avgprice)
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._size)
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._pre_size)
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._freezed_size)
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._closedpl)
		+ SERIALIZATION_SEPARATOR + std::to_string(pos._openpl)
		+ SERIALIZATION_SEPARATOR + ymdhmsf();
	cout<<"Tap TD send postion msg:"<<msg<<endl;
	lock_guard<mutex> g(IEngine::sendlock_);
	IEngine::msgq_send_->sendmsg(msg);
}

void TAP_CDECL TapTDEngine::OnRtnExchangeStateInfo(const TapAPIExchangeStateInfoNotice * info)
{
	if(info == NULL){
		return;
	}
	string msg = "0"
	+ SERIALIZATION_SEPARATOR + name_
	+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE_INFO)
	+ SERIALIZATION_SEPARATOR + "Exchange State is: " + info->ExchangeStateInfo.TradingState;
	lock_guard<mutex> g(IEngine::sendlock_);
	IEngine::msgq_send_->sendmsg(msg);
}

void TAP_CDECL TapTDEngine::OnRtnReqQuoteNotice(const TapAPIReqQuoteNotice *info)
{
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
}

void TAP_CDECL TapTDEngine::OnRspChangePassword( TAPIUINT32 sessionID, TAPIINT32 errorCode )
{
	cout << __FUNCTION__ << " is called." << endl;

}
void TAP_CDECL TapTDEngine::OnRspSetReservedInfo( TAPIUINT32 sessionID, TAPIINT32 errorCode, const TAPISTR_50 info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryAccount( TAPIUINT32 sessionID, TAPIUINT32 errorCode, TAPIYNFLAG isLast, const TapAPIAccountInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryFund( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIFundData *info )
{
	if(errorCode != 0 || info == NULL){
		cout<<"qryfund error "<<errorCode<<endl;
		return;
	}
	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRtnFund: AccountNo=%s, Available=%.2f, PreBalance=%.2f,Balance=%.2f, Commission=%.2f, CurrMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f\n",
		__FILE__, __LINE__, __FUNCTION__, info->AccountNo, info->Available, info->PreBalance,
		info->Balance, info->AccountFee,info->AccountMaintenanceMargin,info->CloseProfit,info->PositionProfit);
	AccountInfo accinfo;
	accinfo.AccountID = info->AccountNo;
	accinfo.PreviousDayEquityWithLoanValue = info->PreBalance;
	accinfo.NetLiquidation = info->Balance;
	accinfo.AvailableFunds = info->Available;
	accinfo.Commission = info->AccountFee;
	accinfo.FullMaintainanceMargin = info->AccountMaintenanceMargin;
	accinfo.RealizedPnL = info->CloseProfit;
	accinfo.UnrealizedPnL = info->PositionProfit;
	PortfolioManager::instance().accinfomap_[tapacc_.id] = accinfo;
	string msg = "0"  // destination is all
		+ SERIALIZATION_SEPARATOR + name_  //source
		+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_ACCOUNT)
		+ SERIALIZATION_SEPARATOR + accinfo.AccountID						// AccountID
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.PreviousDayEquityWithLoanValue)	// prev-day
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.NetLiquidation)				// balance
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.AvailableFunds)				// available
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.Commission)					// commission
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.FullMaintainanceMargin)		// margin
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.RealizedPnL)					// closed pnl
		+ SERIALIZATION_SEPARATOR + std::to_string(accinfo.UnrealizedPnL)					// open pnl
		+ SERIALIZATION_SEPARATOR + ymdhmsf();
	cout<<"Tap Td send account fund msg "<<msg<<endl;
	lock_guard<mutex> g(IEngine::sendlock_);
	IEngine::msgq_send_->sendmsg(msg);
}

void TAP_CDECL TapTDEngine::OnRspQryExchange( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIExchangeInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryCommodity( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPICommodityInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryContract( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPITradeContractInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspOrderAction( TAPIUINT32 sessionID, TAPIUINT32 errorCode, const TapAPIOrderActionRsp *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryOrder( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIOrderInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;

}

void TAP_CDECL TapTDEngine::OnRspQryOrderProcess( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIOrderInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryFill( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIFillInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryPosition( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIPositionInfo *info )
{
	if( errorCode != TAPIERROR_SUCCEED || info == NULL){
		cout<<"tap td qrypos error :"<<errorCode<<endl; 
		return;
	}
	char temp[128] = {};
	sprintf(temp, "%s %c %s %s", info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo);
	string sym = temp;
	PRINT_TO_FILE("INFO:[%s,%d][%s]tap broker server OnRtnQryPosition, fullsymbol=%s %c %s %s, PosPrice=%f, PosQty=%d, MatchSide=%c, PositionProfit=%.2f, PositionCost=%.2f, TradingTime=%s\n",
		__FILE__, __LINE__, __FUNCTION__, info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo,  
		info->PositionPrice,  info->PositionQty, info->MatchSide, info->PositionProfit, info->Turnover, info->MatchTime );
	Position pos;
	pos._type ='n';
	pos._fullsymbol = sym;
	pos._posNo = info->PositionNo;
	pos._size = (info->MatchSide == TAPI_SIDE_BUY ? 1 : -1) * info->PositionQty;
	pos._avgprice = info->PositionPrice;
	pos._openpl = info->PositionProfit;
	pos._account = tapacc_.id;
	pos._openorderNo = info->OrderNo;
	auto oo = OrderManager::instance().retrieveOrderFromMatchNo(info->MatchNo);
	if (oo != nullptr) {
		pos._opensource =  oo->source;
		pos._openapi = oo->api;
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position MatchNO is not tracked. MatchNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->MatchNo);
	}	
	PortfolioManager::instance().Add(pos);
	string msg = "0"  // destination is all
			+ SERIALIZATION_SEPARATOR + name_  //source
			+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_POS)
			+ SERIALIZATION_SEPARATOR + pos._type
			+ SERIALIZATION_SEPARATOR + pos._account
			+ SERIALIZATION_SEPARATOR + pos._posNo
			+ SERIALIZATION_SEPARATOR + pos._openorderNo
			+ SERIALIZATION_SEPARATOR + pos._openapi
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._opensource)
			+ SERIALIZATION_SEPARATOR + pos._closeorderNo			
			+ SERIALIZATION_SEPARATOR + pos._closeapi
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._closesource)									
			+ SERIALIZATION_SEPARATOR + pos._fullsymbol
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._avgprice)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._pre_size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._freezed_size)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._closedpl)
			+ SERIALIZATION_SEPARATOR + std::to_string(pos._openpl)
			+ SERIALIZATION_SEPARATOR + ymdhmsf();
	cout<<"Tap TD send postion msg:"<<msg<<endl;
	lock_guard<mutex> g(IEngine::sendlock_);
	IEngine::msgq_send_->sendmsg(msg);

}

void TAP_CDECL TapTDEngine::OnRspQryClose( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPICloseInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryDeepQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIDeepQuoteQryRsp *info)
{
	//	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspQryExchangeStateInfo(TAPIUINT32 sessionID,TAPIINT32 errorCode, TAPIYNFLAG isLast,const TapAPIExchangeStateInfo * info)
{
	//	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL TapTDEngine::OnRspUpperChannelInfo(TAPIUINT32 sessionID,TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIUpperChannelInfo * info)
{

}

void TAP_CDECL TapTDEngine::OnRspAccountRentInfo(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIAccountRentInfo * info)
{}


//--------------------------------end callback functions-------------------------

OrderStatus TapTDEngine::TapOrderStatusToOrderStatus(const TAPIOrderStateType status) {
	OrderStatus f;
	switch (status) {
		case TAPI_ORDER_STATE_SUBMIT:
			f = OrderStatus:: OS_Submitted;
			break;
		case TAPI_ORDER_STATE_ACCEPT:
			f = OrderStatus:: OS_Acknowledged;
			break;
		case TAPI_ORDER_STATE_TRIGGERING:
			f = OrderStatus:: OS_Trig;
			break;
		case TAPI_ORDER_STATE_EXCTRIGGERING:
			f = OrderStatus:: OS_Exctrig;
			break;
		case TAPI_ORDER_STATE_QUEUED:
			f = OrderStatus:: OS_Queued;
			break;
		case TAPI_ORDER_STATE_PARTFINISHED:
			f = OrderStatus:: OS_PartiallyFilled;
			break;
		case TAPI_ORDER_STATE_FINISHED:
			f = OrderStatus:: OS_Filled;
			break;
		case TAPI_ORDER_STATE_CANCELING:
			f = OrderStatus:: OS_PendingCancel;
			break;
		case TAPI_ORDER_STATE_MODIFYING:
			f = OrderStatus:: OS_PendingModify;
			break;				
		case TAPI_ORDER_STATE_CANCELED:
			f = OrderStatus:: OS_Canceled;
			break;
		case TAPI_ORDER_STATE_LEFTDELETED:
			f = OrderStatus:: OS_LeftDelete;
			break;
		case TAPI_ORDER_STATE_FAIL:
			f= OrderStatus::OS_Fail;
			break;
		case TAPI_ORDER_STATE_DELETED:
			f = OrderStatus::OS_Deleted;
			break;
		case TAPI_ORDER_STATE_SUPPENDED:
			f = OrderStatus::OS_Suspended;
			break;	
		case TAPI_ORDER_STATE_DELETEDFOREXPIRE:
			f = OrderStatus::OS_Deleted;
			break;
		case TAPI_ORDER_STATE_EFFECT:
			f = OrderStatus:: OS_Effect;
			break;
		case TAPI_ORDER_STATE_APPLY:
			f = OrderStatus:: OS_Apply;
			break;
		default:
			f = OrderStatus::OS_UNKNOWN;
			break;
	}
	return f;			
}

OrderFlag TapTDEngine::TapPositionEffectToOrderFlag(const TAPIPositionEffectType flag) {
	OrderFlag f;

	switch (flag) {
		case TAPI_PositionEffect_OPEN:
			f = OrderFlag::OF_OpenPosition;
			break;
		case TAPI_PositionEffect_COVER:
			f = OrderFlag::OF_ClosePosition;
			break;
		case TAPI_PositionEffect_COVER_TODAY:
			f = OrderFlag::OF_CloseToday;
			break;
		default:
			f = OrderFlag::OF_None;
			break;
	}
	return f;
}

TAPIPositionEffectType TapTDEngine::OrderFlagToTapPositionEffect(const OrderFlag flag) {
	TAPIPositionEffectType c;

	switch (flag) {
		case OrderFlag::OF_OpenPosition:
			c = TAPI_PositionEffect_OPEN;	// 开仓
			break;
		case OrderFlag::OF_ClosePosition:
			c = TAPI_PositionEffect_COVER;	// 平仓
			break;
		case OrderFlag::OF_ForceClose:
			c = TAPI_PositionEffect_COVER;	// tap没有强平类型，设置为平仓
			break;
		case OrderFlag::OF_CloseToday:
			c = TAPI_PositionEffect_COVER_TODAY;	// 平今
			break;
		case OrderFlag::OF_CloseYesterday:
			c = TAPI_PositionEffect_COVER;	// tap没有平昨，设置为平仓
			break;
		default:
			c = TAPI_PositionEffect_NONE;	// 不分开平
			break;
	}
	return c;
}
OrderType TapTDEngine::TapOrderTypeToOrderType(const TAPIOrderTypeType type){
	OrderType f;
	switch (type) {
		case TAPI_ORDER_TYPE_MARKET:
			f = OrderType::OT_Market;
			break;
		case TAPI_ORDER_TYPE_LIMIT:
			f = OrderType::OT_Limit;
			break;
		case TAPI_ORDER_TYPE_STOP_MARKET:
			f = OrderType::OT_Stop;
			break;
		case TAPI_ORDER_TYPE_STOP_LIMIT:
			f = OrderType::OT_StopLimit;
			break;
		case TAPI_ORDER_TYPE_OPT_EXEC:
			f = OrderType::OT_OptExec;
			break;
		case TAPI_ORDER_TYPE_OPT_ABANDON:
			f = OrderType::OT_OptAbandon;
			break;
		case TAPI_ORDER_TYPE_REQQUOT:
			f = OrderType::OT_Reqquot;
			break;
		case TAPI_ORDER_TYPE_RSPQUOT:
			f = OrderType::OT_Rspquot;
			break;
		case TAPI_ORDER_TYPE_SWAP:
			f = OrderType::OT_Swap;
			break;
		default:
			f = OrderType::OT_None;
			break;
	}
	return f;		
}

TAPIOrderTypeType TapTDEngine::OrderTypeToTapOrderType(const OrderType type){
	TAPIOrderTypeType c;
	switch (type) {
		case OrderType::OT_Market:
			c = TAPI_ORDER_TYPE_MARKET;	
			break;
		case OrderType::OT_Limit:
			c = TAPI_ORDER_TYPE_LIMIT;	
			break;
		case OrderType::OT_Stop:
			c = TAPI_ORDER_TYPE_STOP_MARKET;	
			break;
		case OrderType::OT_StopLimit:
			c = TAPI_ORDER_TYPE_STOP_LIMIT;	
			break;
		case OrderType::OT_OptExec:
			c = TAPI_ORDER_TYPE_OPT_EXEC;	
			break;
		case OrderType::OT_OptAbandon:
			c = TAPI_ORDER_TYPE_OPT_ABANDON;	
			break;
		case OrderType::OT_Reqquot:
			c = TAPI_ORDER_TYPE_REQQUOT;	
			break;
		case OrderType::OT_Rspquot:
			c = TAPI_ORDER_TYPE_RSPQUOT;	
			break;		
		case OrderType::OT_Swap:
			c = TAPI_ORDER_TYPE_SWAP;	
			break;												
		default:
			c = TAPI_ORDER_TYPE_MARKET;	   //默认市价
			break;
	}
	return c;
}



}