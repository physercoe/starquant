#include <mutex>
#include <Common/Order/orderstatus.h>
#include <Common/Order/fill.h>
#include <Common/Order/ordermanager.h>
#include <Common/Security/portfoliomanager.h>
#include <Common/Data/datamanager.h>
#include <Common/Logger/logger.h>
#include <Common/Util/util.h>
#include <Brokers/Tap/tapbrokerage.h>

using namespace std;
namespace StarQuant
{
	extern std::atomic<bool> gShutdown;

	Tapbrokerage::Tapbrokerage() 
		: isConnected_(false)
		, isLogedin_(false)
		, apiisready(false)
		, isAuthenticated_(false)
		, reqId_(0)
		, orderRef_(0)
		, frontID_(0)
		, sessionID_(0)
	{
        //创建目录
		string path = CConfig::instance().logDir() + "/Tap/";
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);

		///创建TraderApi
        TAPIINT32 iResult = TAPIERROR_SUCCEED;
        TapAPIApplicationInfo stAppInfo;
		//std::cout<<"authcode:"<<CConfig::instance().tap_auth_code<<" size: "<<CConfig::instance().tap_auth_code.size()<<endl;
        strcpy(stAppInfo.AuthCode, CConfig::instance().tap_auth_code.c_str());
        strcpy(stAppInfo.KeyOperationLogPath, "./log");

        // TapAPITradeLoginAuth stLoginAuth;
        // strcpy(stLoginAuth.UserNo, CConfig::instance().tap_user_name.c_str());
        // strcpy(stLoginAuth.Password, CConfig::instance().tap_password.c_str());
        // stLoginAuth.ISModifyPassword = APIYNFLAG_NO;
        // stLoginAuth.ISDDA = APIYNFLAG_NO;

	    ITapTradeAPI *pAPI = CreateTapTradeAPI(&stAppInfo, iResult);
        if (NULL == pAPI){
            cout << "create tap trade API fail，err num is ：" << iResult <<endl;
    //		return -1;
        }

        //注册回调接口
        pAPI->SetAPINotify(this);
        this->api_ =pAPI ;

	}

	Tapbrokerage::~Tapbrokerage() {
		if (api_ != NULL) {
			disconnectFromBrokerage();
		}
	}

	void Tapbrokerage::processBrokerageMessages()
	{
		if (!brokerage::heatbeat(5)) {
			disconnectFromBrokerage();
			return;
		}
		switch (_bkstate) {
		case BK_ACCOUNT:		// not used
			break;
		case BK_ACCOUNTACK:		// not used
			break;
		case BK_GETORDERID:		// start from here
			requestNextValidOrderID();
			break;
		case BK_GETORDERIDACK:
			break;
		case BK_READYTOORDER:
			monitorClientRequest();
			break;
		case BK_PLACEORDER_ACK:
			break;
		case BK_CANCELORDER:
			cancelOrder(0); //TODO
			break;
		case BK_CANCELORDER_ACK:
			break;
		}
	}

	bool Tapbrokerage::connectToBrokerage() {
		if (!isConnected_) {

            TAPIINT32 iErr = TAPIERROR_SUCCEED;

            //设定服务器IP、端口
            iErr = this->api_->SetHostAddress(CConfig::instance().tap_broker_ip.c_str(), CConfig::instance().tap_broker_port);
            if(TAPIERROR_SUCCEED != iErr) {
                cout << "SetHostAddress Error:" << iErr <<endl;
                return false;
            }

            //登录服务器
            TapAPITradeLoginAuth stLoginAuth;
            memset(&stLoginAuth, 0, sizeof(stLoginAuth));
            strcpy(stLoginAuth.UserNo, CConfig::instance().tap_user_name.c_str());
            strcpy(stLoginAuth.Password, CConfig::instance().tap_password.c_str());
            stLoginAuth.ISModifyPassword = APIYNFLAG_NO;
            stLoginAuth.ISDDA = APIYNFLAG_NO;
            iErr = this->api_->Login(&stLoginAuth);

			PRINT_TO_FILE("INFO:[%s,%d][%s]Tap brokerage connecting!\n", __FILE__, __LINE__, __FUNCTION__);
			sendGeneralMessage("Connecting to Tap brokerage");

            if(TAPIERROR_SUCCEED != iErr) {
                cout << "connect Error:" << iErr <<endl;
                return false;
            }






		}

		return true;
	}

	void Tapbrokerage::disconnectFromBrokerage() {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap brokerage connection disconnected!\n", __FILE__, __LINE__, __FUNCTION__);

		this->api_->Disconnect();
        FreeTapTradeAPI(this->api_);
		this->api_ = NULL;
		isConnected_ = false;
		isLogedin_ = false;
		isAuthenticated_ = false;
		apiisready = false;
	}

	bool Tapbrokerage::isConnectedToBrokerage() const {
		return (isConnected_) && (_bkstate >= BK_CONNECTED);						// automatic disconnect when shutdown
	}

	void Tapbrokerage::placeOrder(std::shared_ptr<Order> order) {
		if (order->orderStatus != OrderStatus::OS_NewBorn)
			return;

		// send order
		TAPIINT32 iErr = TAPIERROR_SUCCEED;
        TapAPINewOrder stNewOrder;
        memset(&stNewOrder, 0, sizeof(stNewOrder));
		string symbol = order->fullSymbol;
		vector<string> v = stringsplit(symbol, ' ');

        strcpy(stNewOrder.AccountNo, CConfig::instance().tap_user_name.c_str());			
        strcpy(stNewOrder.ExchangeNo, v[0].c_str());		
        stNewOrder.CommodityType = v[1][0];		
        strcpy(stNewOrder.CommodityNo, v[2].c_str());		
        strcpy(stNewOrder.ContractNo, v[3].c_str());
//        stNewOrder.RefInt = order->brokerOrderId;
		strcpy(stNewOrder.RefString, to_string(order->brokerOrderId).c_str());
		stNewOrder.OrderType = OrderTypeToTapOrderType(order->orderType);
		if (order->orderType == OrderType::OT_Limit){
			stNewOrder.OrderPrice = order->limitPrice;

		}else if (order->orderType == OrderType::OT_StopLimit){
			stNewOrder.StopPrice = order->stopPrice;
		}

		// if (order->orderType == "MKT"){
		// 	stNewOrder.OrderType = TAPI_ORDER_TYPE_MARKET;
		// }
		// else if(order->orderType =="LMT"){
		// 	stNewOrder.OrderType = TAPI_ORDER_TYPE_LIMIT;
		// 	stNewOrder.OrderPrice = order->limitPrice;
		// }else if(order->orderType =="STP"){
		// 	stNewOrder.OrderType = TAPI_ORDER_TYPE_STOP_MARKET;
		// }
		// else if (order->orderType == "STPLMT")
		// {
		// 	stNewOrder.OrderType = TAPI_ORDER_TYPE_STOP_LIMIT;
		// 	stNewOrder.StopPrice = order->stopPrice;
		// }
		

        stNewOrder.OrderSide = order->orderSize > 0 ? TAPI_SIDE_BUY : TAPI_SIDE_SELL;			
        stNewOrder.PositionEffect = OrderFlagToTapPositionEffect(order->orderFlag);	
        stNewOrder.OrderQty = std::abs(order->orderSize);		

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
        stNewOrder.OrderQty2;
        stNewOrder.HedgeFlag2 = TAPI_HEDGEFLAG_NONE;

        strcpy(stNewOrder.InquiryNo,"");			
        stNewOrder.HedgeFlag = TAPI_HEDGEFLAG_T;
	    stNewOrder.OrderMinQty ;		
        stNewOrder.MinClipSize;		
        stNewOrder.MaxClipSize;		
		
	
        stNewOrder.TacticsType = TAPI_TACTICS_TYPE_NONE;		
        stNewOrder.TriggerCondition = TAPI_TRIGGER_CONDITION_NONE;	
        stNewOrder.TriggerPriceType = TAPI_TRIGGER_PRICE_NONE;	
        stNewOrder.AddOneIsValid = APIYNFLAG_NO;	

        stNewOrder.MarketLevel = TAPI_MARKET_LEVEL_0;
        stNewOrder.OrderDeleteByDisConnFlag = APIYNFLAG_NO; // V9.0.2.0 20150520
        
        //iErr = this->api_->InsertOrder(&this->sessionID_, &stNewOrder);

		//unsigned int _sessionid = (unsigned int)stoi(to_string(order->brokerOrderId));
		//cout<<"sessionid "<<(unsigned int)order->brokerOrderId<<to_string(order->brokerOrderId)<<" "<<stoi(to_string(order->brokerOrderId))<<" "<<_sessionid<<endl;
		//cout<<"byte"<<sizeof(unsigned int)<<" "<<sizeof(int)<<" "<<sizeof(long)<<endl;
		//this->sessionID_ = _sessionid;
		iErr = this->api_->InsertOrder(&this->sessionID_, &stNewOrder);
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Placing Order : sessionid = %d,serverorderId=%ld, brokerorderId=%ld,fullSymbol=%s\n", __FILE__, __LINE__, __FUNCTION__, this->sessionID_,order->serverOrderId, order->brokerOrderId,order->fullSymbol.c_str());
		
		lock_guard<mutex> g(orderStatus_mtx);
		order->api = "TAP";
		order->orderStatus = OrderStatus::OS_Submitted;
		sendOrderStatus(order->serverOrderId);



	}



	void Tapbrokerage::requestNextValidOrderID() {
//		if (_bkstate < BK_GETORDERIDACK)
//			_bkstate = BK_GETORDERIDACK;

//		lock_guard<mutex> g(oid_mtx);
//		m_brokerOrderId = 0;

		// if (requireAuthentication_) {
		// 	// trigger onRspAuthenticate()
		// 	requestAuthenticate(CConfig::instance().Tap_user_id, CConfig::instance().Tap_auth_code, 
		// 		CConfig::instance().Tap_broker_id, CConfig::instance().Tap_user_prod_info);				// authenticate first
		// }
		// else if (!isLogedin_) {
		// 	requestUserLogin();
		// }
		if (isLogedin_ && apiisready){
			if (_bkstate < BK_READYTOORDER)
				_bkstate = BK_READYTOORDER;
			requestBrokerageAccountInformation(CConfig::instance().account);
			requestOpenPositions(CConfig::instance().account);
		}

		


	}


	void Tapbrokerage::reqGlobalCancel() {
	}

	// TODO: 弄清撤单结构的含义
	void Tapbrokerage::cancelOrder(int oid) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order m_serverorderId=%ld\n", __FILE__, __LINE__, __FUNCTION__, (long)oid);

		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
		if (o != nullptr){
			TAPIINT32 iErr = TAPIERROR_SUCCEED;
			TapAPIOrderCancelReq myreq;
			strcpy(myreq.OrderNo, o->orderNo.c_str());
			iErr = this->api_->CancelOrder(&this->sessionID_, &myreq);

		}else{
			cout<<"error serverorderId is not in list, cannot cancel!"<<endl;
		}

	}

	void Tapbrokerage::cancelOrder(const string& ono) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order symbol=%s\n", __FILE__, __LINE__, __FUNCTION__, ono.c_str());
		TAPIINT32 iErr = TAPIERROR_SUCCEED;
		TapAPIOrderCancelReq myreq;
		//std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
		strcpy(myreq.OrderNo, ono.c_str());
		//strcpy(myreq.RefString, to_string(o->brokerOrderId).c_str());

		iErr = this->api_->CancelOrder(&this->sessionID_, &myreq);	
	
	
	}
	void Tapbrokerage::cancelOrders(const string& symbols){

	}

	void Tapbrokerage::cancelAllOrders() {
		lock_guard<mutex> _g(mtx_CANCELALL);
	}

	// 查询账户
	void Tapbrokerage::requestBrokerageAccountInformation(const string& account_) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker requests brokerage account and fund information.\n", __FILE__, __LINE__, __FUNCTION__);
		TAPIINT32 iErr1 = TAPIERROR_SUCCEED;
		TAPIINT32 iErr2 = TAPIERROR_SUCCEED;
		TapAPIAccQryReq myaccreq;
		TapAPIFundReq myfundreq;
		strcpy(myaccreq.AccountNo, account_.c_str());
		strcpy(myfundreq.AccountNo, account_.c_str());
		iErr1 = this->api_->QryAccount(&this->sessionID_, &myaccreq);
		if (iErr1 != TAPIERROR_SUCCEED){
			cout<<"qry acc error "<<iErr1<<endl;
		}
		iErr2 = this->api_->QryFund(&this->sessionID_, &myfundreq);	
		if (iErr2 != TAPIERROR_SUCCEED){
			cout<<"qry fund error "<<iErr2<<endl;
		}		
	}

	void Tapbrokerage::requestOpenOrders(const string& account_)
	{
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker requests open orders.\n", __FILE__, __LINE__, __FUNCTION__);
		TAPIINT32 iErr = TAPIERROR_SUCCEED;
		TapAPIOrderQryReq myreq;

		myreq.OrderQryType = TAPI_ORDER_QRY_TYPE_ALL;
		//myreq.OrderQryType = TAPI_ORDER_QRY_TYPE_UNENDED;
		iErr = this->api_->QryOrder(&this->sessionID_, &myreq);	
		if (iErr != TAPIERROR_SUCCEED){
			cout<<"qry order error "<<iErr<<endl;
		}			

	}

	/// 查询持仓信息， trigger onRspQryInvestorPosition
	void Tapbrokerage::requestOpenPositions(const string& account_) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker requests open positions.\n", __FILE__, __LINE__, __FUNCTION__);
		TAPIINT32 iErr = TAPIERROR_SUCCEED;
		TapAPIPositionQryReq myreq;
		
		iErr = this->api_->QryPosition(&this->sessionID_, &myreq);		
		if (iErr != TAPIERROR_SUCCEED)
		{
			cout<<"qry position ierr:"<<iErr<<endl;
		}
	}

	void Tapbrokerage::requestAuthenticate(string userid, string authcode, string brokerid, string userproductinfo) {
		// CThostFtdcReqAuthenticateField authField;

		// strcpy(authField.UserID, userid.c_str());
		// strcpy(authField.BrokerID, brokerid.c_str());
		// strcpy(authField.AuthCode, authcode.c_str());
		// strcpy(authField.UserProductInfo, userproductinfo.c_str());

		// this->api_->ReqAuthenticate(&authField, reqId_++);
	}

	///用户登录请求
	void Tapbrokerage::requestUserLogin() {
		// CThostFtdcReqUserLoginField loginField = CThostFtdcReqUserLoginField();

		// strcpy(loginField.BrokerID, CConfig::instance().Tap_broker_id.c_str());
		// strcpy(loginField.UserID, CConfig::instance().Tap_user_id.c_str());
		// strcpy(loginField.Password, CConfig::instance().Tap_password.c_str());

		// int i = this->api_->ReqUserLogin(&loginField, reqId_++);
	}

	///登出请求
	void Tapbrokerage::requestUserLogout() {
		// CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();

		// strcpy(logoutField.BrokerID, CConfig::instance().Tap_broker_id.c_str());
		// strcpy(logoutField.UserID, CConfig::instance().Tap_user_id.c_str());

		// int i = this->api_->ReqUserLogout(&logoutField, reqId_++);
	}

	/// 投资者结算结果确认, trigger response onRspSettlementInfoConfirm
	void Tapbrokerage::requestSettlementInfoConfirm() {
		// PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker requests settlement info comfirm.\n", __FILE__, __LINE__, __FUNCTION__);

		// CThostFtdcSettlementInfoConfirmField myreq = CThostFtdcSettlementInfoConfirmField();
		// strcpy(myreq.BrokerID, CConfig::instance().Tap_broker_id.c_str());
		// strcpy(myreq.InvestorID, CConfig::instance().Tap_user_id.c_str());
		// api_->ReqSettlementInfoConfirm(&myreq, reqId_++);			
	}








	////////////////////////////////////////////////////// begin callback/incoming function ///////////////////////////////////////

//服务器被动的推送信息
	///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
	void TAP_CDECL Tapbrokerage::OnConnect() {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker connected; Continue to login.\n", __FILE__, __LINE__, __FUNCTION__);
		
		_bkstate = BK_CONNECTED;
		isConnected_ = true;
		reqId_ = 0;
	}

    void TAP_CDECL Tapbrokerage::OnAPIReady()    {
		apiisready = true;
        cout << "TAP交易API初始化完成" << endl;
    }



    void TAP_CDECL Tapbrokerage::OnRspLogin( TAPIINT32 errorCode, const TapAPITradeLoginRspInfo *loginRspInfo )
 {
	///当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
    // loginRspInfo->
	// TAPISTR_20					UserNo;							///< 用户编号
	// TAPIUserTypeType			UserType;						///< 用户类型
	// TAPISTR_20					UserName;						///< 用户名
	// TAPISTR_20					QuoteTempPassword;				///< 行情临时密码
	// TAPISTR_50					ReservedInfo;					///< 预留信息
	// TAPISTR_40					LastLoginIP;					///< 上次登录IP
	// TAPIUINT32					LastLoginProt;					///< 上次登录端口
	// TAPIDATETIME				LastLoginTime;					///< 上次登录时间
	// TAPIDATETIME				LastLogoutTime;					///< 上次退出时间
	// TAPIDATE					TradeDate;						///< 当前交易日期
	// TAPIDATETIME				LastSettleTime;					///< 上次结算时间
	// TAPIDATETIME				StartTime;						///< 系统启动时间
	// TAPIDATETIME				InitTime;	

    if(TAPIERROR_SUCCEED == errorCode) {
        cout << "TAP交易登录成功，等待交易API初始化..." << endl;
        isLogedin_ = true;
        PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server user logged in \n.",__FILE__, __LINE__, __FUNCTION__);
        sendGeneralMessage(string("Tap broker server user logged in:"));

	}

     else {
        cout << "TAP交易登录失败，错误码:" << errorCode << endl;
        PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server user login failed: Errorcode=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, errorCode);
        sendGeneralMessage(string("Tap Trader Server OnRspUserLogin error:") + SERIALIZATION_SEPARATOR + to_string(errorCode) );
        }    

    
}


	void Tapbrokerage::OnDisconnect(TAPIINT32 reasonCode) {
        cout << "TAP API断开,断开原因:"<<reasonCode << endl;
		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker disconnected, nReason=%d.\n", __FILE__, __LINE__, __FUNCTION__, reasonCode);
		_bkstate = BK_DISCONNECTED;
		isConnected_ = false;
		isLogedin_ = false;
		isAuthenticated_ = false;
	}





void TAP_CDECL Tapbrokerage::OnRtnFund( const TapAPIFundData *info )
{
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
		// double balance = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
		// 	+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
		// 	+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;

		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRtnFund: AccountNo=%s, Available=%.2f, PreBalance=%.2f,Balance=%.2f, Commission=%.2f, CurrMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f\n",
		 	__FILE__, __LINE__, __FUNCTION__, info->AccountNo, info->Available, info->PreBalance,
			info->Balance, info->AccountFee,info->AccountMaintenanceMargin,info->CloseProfit,info->PositionProfit);

		PortfolioManager::instance()._account.AccountID = info->AccountNo;
		PortfolioManager::instance()._account.PreviousDayEquityWithLoanValue = info->PreBalance;
		PortfolioManager::instance()._account.NetLiquidation = info->Balance;
		PortfolioManager::instance()._account.AvailableFunds = info->Available;
		PortfolioManager::instance()._account.Commission = info->AccountFee;
		PortfolioManager::instance()._account.FullMaintainanceMargin = info->AccountMaintenanceMargin;
		PortfolioManager::instance()._account.RealizedPnL = info->CloseProfit;
		PortfolioManager::instance()._account.UnrealizedPnL = info->PositionProfit;

		sendAccountMessage();

       

}



void TAP_CDECL Tapbrokerage::OnRtnContract( const TapAPITradeContractInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
}

void TAP_CDECL Tapbrokerage::OnRtnOrder( const TapAPIOrderInfoNotice *info )
{
	if(NULL == info){
		return;
	}

	if (info->ErrorCode != 0) {
		cout << "服务器返回了一个关于委托信息的错误：" << info->ErrorCode << endl;
	} else {
		if (info->OrderInfo) {
			long boid = stol(info->OrderInfo->RefString);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromBrokerOrderId(boid);
			if ((o != nullptr))			//if (info->SessionID == this->sessionID_)
			{
				//long soid = stol(info->OrderInfo->RefString); //本地服务器提交的订单号
				if (0!= info->OrderInfo->ErrorCode){
					cout << "报单失败，"
						<< "错误码:"<<info->OrderInfo->ErrorCode << ","
						<< "委托编号:"<<info->OrderInfo->OrderNo
						<<endl;
					PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server OnRtnOrder: ErrorID=%d, OrderNo=%s.\n",
						__FILE__, __LINE__, __FUNCTION__, info->OrderInfo->ErrorCode, info->OrderInfo->OrderNo);
					lock_guard<mutex> g(orderStatus_mtx);
					//std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(soid);
					//if (o != nullptr) {
					o->orderStatus = OS_Error;
					o->orderNo = info->OrderInfo->OrderNo;
					o->api = info->OrderInfo->OrderSource;					
					sendOrderStatus(o->serverOrderId);
					sendGeneralMessage(string("TAP Trader Server OnRtnOrder error:") +
						SERIALIZATION_SEPARATOR + to_string(info->OrderInfo->ErrorCode) + SERIALIZATION_SEPARATOR + info->OrderInfo->OrderNo);
					//}
					// else {
					// 	PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Tap broker server OnRtnOrder cant find order : serverOrderId=%s\n",
					// 		__FILE__, __LINE__, __FUNCTION__, info->OrderInfo->RefString);
					// }			

				} else{
					cout << "报单成功，"
						<< "状态:"<<info->OrderInfo->OrderState << ","
						<< "委托编号:"<<info->OrderInfo->OrderNo <<" "
						<<endl;
					PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRtnOrder: serverOrderId=%s, LimitPrice=%.2f, VolumeTotalOriginal=%d, Side=%c, Direction=%c.\n",
						__FILE__, __LINE__, __FUNCTION__, info->OrderInfo->RefString, info->OrderInfo->OrderPrice, info->OrderInfo->OrderQty, info->OrderInfo->OrderSide, info->OrderInfo->PositionEffect);

					lock_guard<mutex> g(orderStatus_mtx);
					//std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(soid);

					//if (o != nullptr) {
					o->orderStatus = TapOrderStatusToOrderStatus(info->OrderInfo->OrderState);
					o->orderNo = info->OrderInfo->OrderNo;
					o->api = info->OrderInfo->OrderSource;			
					sendOrderStatus(o->serverOrderId);
					sendGeneralMessage(string("TAP Trader Server OnRtnOrder :") +
						SERIALIZATION_SEPARATOR + info->OrderInfo->RefString + SERIALIZATION_SEPARATOR + getOrderStatusString(o->orderStatus));
					// }
					// else {
					// 	PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]tap broker server OnRtnOrder cant find order : serverorderId=%d\n",
					// 		__FILE__, __LINE__, __FUNCTION__, soid);
					// }


				}


			}else {
				//the order is from other brokerage, creat an order for ordermanager 
				PRINT_TO_FILE_AND_CONSOLE("Warning:[%s,%d][%s]Tap Trader server OnRtnOrder not in OM tracklist, sessionid = %d, OrderNo=%s\n",
					__FILE__, __LINE__, __FUNCTION__, info->SessionID,info->OrderInfo->OrderNo);
				lock_guard<mutex> g(oid_mtx);
				std::shared_ptr<Order> o = make_shared<Order>();
				o->account = info->OrderInfo->AccountNo;
				o->api = info->OrderInfo->OrderSource;;
				char temp[128] = {};
				sprintf(temp, "%s %c %s %s", info->OrderInfo->ExchangeNo, info->OrderInfo->CommodityType, info->OrderInfo->CommodityNo,info->OrderInfo->ContractNo);
				o->fullSymbol = temp;
				o->clientOrderId = -1;
				o->source = -1;
				o->clientId = -1;
				o->serverOrderId = m_serverOrderId;
				m_serverOrderId++;
				o->brokerOrderId = -1;
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
				sendOrderStatus(o->serverOrderId);
				sendGeneralMessage(string("TAP Trader Server OnRtnOrder receive an outer source order:") +
						SERIALIZATION_SEPARATOR  + info->OrderInfo->OrderNo);

			}
		}

	}
}



void TAP_CDECL Tapbrokerage::OnRtnFill( const TapAPIFillInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
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
	t.account = info->AccountNo;
	t.api = info->MatchSource;			
	t.fullSymbol = sym;
	t.tradetime = info->MatchDateTime;
	t.orderNo = info->OrderNo;
	t.tradeNo = info->MatchNo;
	t.tradePrice = info->MatchPrice;
	t.tradeSize = (info->MatchSide == TAPI_SIDE_BUY ? 1 : -1)* info->MatchQty;
	t.fillflag = TapPositionEffectToOrderFlag(info->PositionEffect);
	// cout<<"fill size:"<<t.tradeSize<<endl;
	t.commission = info->FeeValue;
	auto o = OrderManager::instance().retrieveOrderFromOrderNo(info->OrderNo);
	if (o != nullptr) {
		t.serverOrderId = o->serverOrderId;
		t.clientOrderId = o->clientOrderId;
		t.brokerOrderId = o->brokerOrderId;
		o->fillNo = t.tradeNo;
		//t.account = o->account;
		//t.api = o->api;
		t.source = o->source;
		OrderManager::instance().gotFill(t);
		// sendOrderStatus(o->serverOrderId);
		sendOrderFilled(t);		
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]fill order id is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->OrderNo);

		t.serverOrderId = -1;
		t.clientOrderId = -1;
		t.brokerOrderId = -1;
		//t.account = info->AccountNo;
		//t.api = "outer "+info->MatchSource;		
		sendOrderFilled(t);		// BOT SLD
	}		






}


void TAP_CDECL Tapbrokerage::OnRtnClose( const TapAPICloseInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
	char temp[128] = {};
	sprintf(temp, "%s %c %s %s", info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo);
	string sym = temp;
	Position pos;
	pos._type ='c';
	pos._fullsymbol = sym;
	pos._openapi = info->OpenMatchSource;
	pos._closeapi = info->CloseMatchSource;
	pos._size = (info->CloseSide == TAPI_SIDE_BUY ? 1 : -1) * info->CloseQty;
	pos._avgprice = info->ClosePrice;
	pos._closedpl = info->CloseProfit;
	pos._account = info->AccountNo;
	pos._openorderNo = info->OpenMatchNo;
	pos._closeorderNo = info->CloseMatchNo;
	auto oo = OrderManager::instance().retrieveOrderFromMatchNo(info->OpenMatchNo);
	if (oo != nullptr) {
		pos._opensource =  oo->source;

	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position openorderNO is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->OpenMatchNo);
		pos._opensource = -1;
	}		
	auto co = OrderManager::instance().retrieveOrderFromMatchNo(info->CloseMatchNo);
	if (co != nullptr) {
		pos._closesource =  co->source;
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position closeorderNO is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->CloseMatchNo);
		pos._closesource = -1;
	}	
	// PortfolioManager::instance().Add(pos);
	sendOpenPositionMessage(pos);



}

void TAP_CDECL Tapbrokerage::OnRtnPosition( const TapAPIPositionInfo *info )
{	
	cout << __FUNCTION__ << " is called." << endl;

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
	//cout<< "pos sizze "<<pos._size<<endl;
	pos._avgprice = info->PositionPrice;
	pos._openpl = info->PositionProfit;
	pos._account = info->AccountNo;
	pos._openorderNo = info->MatchNo;
	pos._openapi = info->MatchSource;
	auto oo = OrderManager::instance().retrieveOrderFromMatchNo(info->MatchNo);
	if (oo != nullptr) {
		pos._opensource =  oo->source;
	}
	else {
		//cout<<info->MatchNo<<endl;
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position MatchNO is not tracked. MatchNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->MatchNo);
		pos._opensource = -1;
	}	

	PortfolioManager::instance().Add(pos);
	sendOpenPositionMessage(pos);


}


void TAP_CDECL Tapbrokerage::OnRtnPositionProfit( const TapAPIPositionProfitNotice *info )
{	
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL || info->Data == NULL){
		// cout<<"null info in pos u"<<endl;
		return;
	}

	Position pos;
	pos._posNo = info->Data->PositionNo;
	pos._openpl = info->Data->PositionProfit;
	//pos._account = CConfig::instance().account;
	//pos._openapi = "TAP";
	pos._type ='u';
	// PortfolioManager::instance().Add(pos);
	sendOpenPositionMessage(pos);
	//cout << "finish send pos u" <<endl;



}


void TAP_CDECL Tapbrokerage::OnRtnExchangeStateInfo(const TapAPIExchangeStateInfoNotice * info)
{
	cout << __FUNCTION__ << " is called." << endl;

	if(info == NULL){
		return;
	}
	sendGeneralMessage(string("Exchange State is : ")+info->ExchangeStateInfo.TradingState);


}

void TAP_CDECL Tapbrokerage::OnRtnReqQuoteNotice(const TapAPIReqQuoteNotice *info)
{
	cout << __FUNCTION__ << " is called." << endl;
	if(info == NULL){
		return;
	}
}


//交易服务器对主动请求的响应，如查询

void TAP_CDECL Tapbrokerage::OnRspChangePassword( TAPIUINT32 sessionID, TAPIINT32 errorCode )
{
	cout << __FUNCTION__ << " is called." << endl;

}
void TAP_CDECL Tapbrokerage::OnRspSetReservedInfo( TAPIUINT32 sessionID, TAPIINT32 errorCode, const TAPISTR_50 info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryAccount( TAPIUINT32 sessionID, TAPIUINT32 errorCode, TAPIYNFLAG isLast, const TapAPIAccountInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryFund( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIFundData *info )
{
	cout << __FUNCTION__ << " is called." << endl;


	if(errorCode != 0 || info == NULL){
		cout<<"qryfund error "<<errorCode<<endl;
		return;
	}
		// double balance = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
		// 	+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
		// 	+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;

		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRtnFund: AccountNo=%s, Available=%.2f, PreBalance=%.2f,Balance=%.2f, Commission=%.2f, CurrMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f\n",
		 	__FILE__, __LINE__, __FUNCTION__, info->AccountNo, info->Available, info->PreBalance,
			info->Balance, info->AccountFee,info->AccountMaintenanceMargin,info->CloseProfit,info->PositionProfit);

		PortfolioManager::instance()._account.AccountID = info->AccountNo;
		PortfolioManager::instance()._account.PreviousDayEquityWithLoanValue = info->PreBalance;
		PortfolioManager::instance()._account.NetLiquidation = info->Balance;
		PortfolioManager::instance()._account.AvailableFunds = info->Available;
		PortfolioManager::instance()._account.Commission = info->AccountFee;
		PortfolioManager::instance()._account.FullMaintainanceMargin = info->AccountMaintenanceMargin;
		PortfolioManager::instance()._account.RealizedPnL = info->CloseProfit;
		PortfolioManager::instance()._account.UnrealizedPnL = info->PositionProfit;

		sendAccountMessage();
}

void TAP_CDECL Tapbrokerage::OnRspQryExchange( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIExchangeInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryCommodity( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPICommodityInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryContract( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPITradeContractInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspOrderAction( TAPIUINT32 sessionID, TAPIUINT32 errorCode, const TapAPIOrderActionRsp *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryOrder( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIOrderInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;

}

void TAP_CDECL Tapbrokerage::OnRspQryOrderProcess( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIOrderInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryFill( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIFillInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryPosition( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIPositionInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
	if( errorCode !=0 || info == NULL){
		cout<<"qrypos error :"<<errorCode<<endl; 
		return;
	}

	char temp[128] = {};
	
	sprintf(temp, "%s %c %s %s", info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo);
	string sym = temp;
	// cout<<"onrtn pos full sym:"<<info->ExchangeNo<<info->CommodityType<<info->CommodityNo<<info->ContractNo <<"_"<<sym<<endl;
	//string fullsym= info->ExchangeNo+' '+info->CommodityType+' '+info->CommodityNo + ' '+info->ContractNo;
	PRINT_TO_FILE("INFO:[%s,%d][%s]tap broker server OnRtnQryPosition, fullsymbol=%s %c %s %s, PosPrice=%f, PosQty=%d, MatchSide=%c, PositionProfit=%.2f, PositionCost=%.2f, TradingTime=%s\n",
		__FILE__, __LINE__, __FUNCTION__, info->ExchangeNo, info->CommodityType, info->CommodityNo,info->ContractNo,  
		info->PositionPrice,  info->PositionQty, info->MatchSide, info->PositionProfit, info->Turnover, info->MatchTime );
	
	Position pos;
	pos._type ='n';
	pos._fullsymbol = sym;
	pos._posNo = info->PositionNo;
	pos._size = (info->MatchSide == TAPI_SIDE_BUY ? 1 : -1) * info->PositionQty;
	//cout<< "pos sizze "<<pos._size<<endl;
	pos._avgprice = info->PositionPrice;
	pos._openpl = info->PositionProfit;
	pos._account = info->AccountNo;
	pos._openorderNo = info->MatchNo;
	pos._openapi = info->MatchSource;
	auto oo = OrderManager::instance().retrieveOrderFromMatchNo(info->MatchNo);
	if (oo != nullptr) {
		pos._opensource =  oo->source;
	}
	else {
		PRINT_TO_FILE_AND_CONSOLE("warning:[%s,%d][%s]position openorderNO is not tracked. OrderNo= %s\n", __FILE__, __LINE__, __FUNCTION__, info->OrderNo);
		pos._opensource = -1;
	}	

	PortfolioManager::instance().Add(pos);
	sendOpenPositionMessage(pos);

}

void TAP_CDECL Tapbrokerage::OnRspQryClose( TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPICloseInfo *info )
{
	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryDeepQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIDeepQuoteQryRsp *info)
{
	//	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspQryExchangeStateInfo(TAPIUINT32 sessionID,TAPIINT32 errorCode, TAPIYNFLAG isLast,const TapAPIExchangeStateInfo * info)
{
	//	cout << __FUNCTION__ << " is called." << endl;
}

void TAP_CDECL Tapbrokerage::OnRspUpperChannelInfo(TAPIUINT32 sessionID,TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIUpperChannelInfo * info)
{

}

void TAP_CDECL Tapbrokerage::OnRspAccountRentInfo(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIAccountRentInfo * info)
{}





























	// ///登出请求响应
	// void Tapbrokerage::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	if (pRspInfo->ErrorID == 0) {
	// 		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server user logged out, BrokerID=%s, UserID=%s.\n",
	// 			__FILE__, __LINE__, __FUNCTION__, pUserLogout->BrokerID, pUserLogout->UserID);
	// 		isLogedin_ = false;
	// 		isAuthenticated_ = false;
	// 	}
	// 	else {
	// 		PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server user logout failed: ErrorID=%d, ErrorMsg=%s.\n",
	// 			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, pRspInfo->ErrorMsg);

	// 		sendGeneralMessage(string("Tap Trader Server OnRspUserLogout error:") +
	// 			SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + pRspInfo->ErrorMsg);
	// 	}
	// }

	// ///报单录入请求响应(参数不通过)
	// void Tapbrokerage::OnRspOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	bool bResult = pRspInfo && (pRspInfo->ErrorID != 0);
	// 	if (!bResult)
	// 	{
	// 		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRspOrderInsert: OrderRef=%s, InstrumentID=%s, LimitPrice=%.2f, VolumeTotalOriginal=%d, Direction=%c.\n",
	// 			__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef, pInputOrder->InstrumentID, pInputOrder->LimitPrice, pInputOrder->VolumeTotalOriginal, pInputOrder->Direction);

	// 		lock_guard<mutex> g(orderStatus_mtx);
	// 		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromBrokerOrderIdAndApi(std::stoi(pInputOrder->OrderRef), "Tap");

	// 		if (o != nullptr) {
	// 			o->orderStatus = OS_Error;			// rejected ?

	// 			sendOrderStatus(o->serverOrderId);
	// 			sendGeneralMessage(string("Tap Trader Server OnRspOrderInsert:") +
	// 				SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + pRspInfo->ErrorMsg);
	// 		}
	// 		else {
	// 			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]tp broker server OnRspOrderInsert cant find order : OrderRef=%s\n",
	// 				__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
	// 		}
	// 	}
	// 	else
	// 	{
	// 		PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server OnRspOrderInsert: ErrorID=%d, ErrorMsg=%s.\n",
	// 			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, pRspInfo->ErrorMsg);

	// 		lock_guard<mutex> g(orderStatus_mtx);
	// 		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromBrokerOrderIdAndApi(std::stoi(pInputOrder->OrderRef), "Tap");

	// 		if (o != nullptr) {
	// 			o->orderStatus = OS_Error;			// rejected ?

	// 			sendOrderStatus(o->serverOrderId);
	// 			sendGeneralMessage(string("Tap Trader Server OnRspOrderInsert error:") +
	// 				SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + pRspInfo->ErrorMsg);
	// 		}
	// 		else {
	// 			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]tp broker server OnRspOrderInsert cant find order : OrderRef=%s\n",
	// 				__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
	// 		}			
	// 	}
	// }

	// ///报单操作请求响应(参数不通过)
	// // 撤单错误（柜台）
	// void Tapbrokerage::OnRspOrderAction(CThostFtdcInputOrderActionField *pInputOrderAction, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	bool bResult = pRspInfo && (pRspInfo->ErrorID != 0);
	// 	if (!bResult)
	// 	{
	// 		PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRspOrderAction: OrderRef=%s, InstrumentID=%s, ActionFlag=%c.\n",
	// 			__FILE__, __LINE__, __FUNCTION__, pInputOrderAction->OrderRef, pInputOrderAction->InstrumentID, pInputOrderAction->ActionFlag);
	// 	}
	// 	else
	// 	{
	// 		PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server OnRspOrderAction failed: ErrorID=%d, ErrorMsg=%s.\n",
	// 			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, pRspInfo->ErrorMsg);

	// 		sendGeneralMessage(to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + pRspInfo->ErrorMsg);
	// 	}
	// }

	// ///投资者结算结果确认响应
	// void Tapbrokerage::OnRspSettlementInfoConfirm(CThostFtdcSettlementInfoConfirmField *pSettlementInfoConfirm, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRspSettlementInfoConfirm, ConfirmDate=%s, ConfirmTime=%s.\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pSettlementInfoConfirm->ConfirmDate, pSettlementInfoConfirm->ConfirmTime);

	// 	// 查询合约代码, trigger response OnRspQryInstrument
	// 	CThostFtdcQryInstrumentField myreq = CThostFtdcQryInstrumentField();
	// 	int i = this->api_->ReqQryInstrument(&myreq, reqId_++);
	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker servers ReqQryInstrument.\n", 	__FILE__, __LINE__, __FUNCTION__);
	// }

	// ///请求查询投资者持仓响应 (respond to requestOpenPositions)
	// void Tapbrokerage::OnRspQryInvestorPosition(CThostFtdcInvestorPositionField *pInvestorPosition, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRspQryInvestorPosition, InstrumentID=%s, InvestorID=%s, OpenAmount=%f, OpenVolume=%d, PosiDirection=%c, PositionProfit=%.2f, PositionCost=%.2f, UseMargin=%.2f, LongFrozen=%d, ShortFrozen=%d, TradingDay=%s, YdPosition=%d, last=%d\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pInvestorPosition->InstrumentID, pInvestorPosition->InvestorID, pInvestorPosition->OpenAmount, pInvestorPosition->OpenVolume,
	// 		pInvestorPosition->PosiDirection, pInvestorPosition->PositionProfit, pInvestorPosition->PositionCost, pInvestorPosition->UseMargin,
	// 		pInvestorPosition->LongFrozen, pInvestorPosition->ShortFrozen, pInvestorPosition->TradingDay, pInvestorPosition->YdPosition, bIsLast);

	// 	// TODO: 针对上期所持仓的今昨分条返回（有昨仓、无今仓），读取昨仓数据
	// 	// pInvestorPosition->YdPosition;
	// 	// TODO: 汇总总仓, 计算持仓均价, 读取冻结

	// 	if (pInvestorPosition->Position != 0.0) {
	// 		Position pos;
	// 		pos._fullsymbol = pInvestorPosition->InstrumentID;
	// 		pos._size = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? 1 : -1) * pInvestorPosition->Position;
	// 		pos._avgprice = pInvestorPosition->PositionCost / pInvestorPosition->Position;
	// 		pos._openpl = pInvestorPosition->PositionProfit;
	// 		pos._closedpl = pInvestorPosition->CloseProfit;
	// 		pos._account = CConfig::instance().Tap_user_id;
	// 		pos._pre_size = pInvestorPosition->YdPosition;
	// 		pos._freezed_size = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? pInvestorPosition->LongFrozen : pInvestorPosition->ShortFrozen);
	// 		pos._api = "Tap";
	// 		PortfolioManager::instance().Add(pos);
	// 		sendOpenPositionMessage(pos);
	// 	}

	// }

	// ///请求查询资金账户响应 (respond to requestAccount)
	// void Tapbrokerage::OnRspQryTradingAccount(CThostFtdcTradingAccountField *pTradingAccount, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	// balance和快期中的账户可能不一样
	// 	double balance = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
	// 		+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
	// 		+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;

	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRspQryTradingAccount: AccountID=%s, Available=%.2f, PreBalance=%.2f, Deposit=%.2f, Withdraw=%.2f, WithdrawQuota=%.2f, Commission=%.2f, CurrMargin=%.2f, FrozenMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f, balance=%.2f.\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pTradingAccount->AccountID, pTradingAccount->Available, pTradingAccount->PreBalance,
	// 		pTradingAccount->Deposit, pTradingAccount->Withdraw, pTradingAccount->WithdrawQuota, pTradingAccount->Commission,
	// 		pTradingAccount->CurrMargin, pTradingAccount->FrozenMargin, pTradingAccount->CloseProfit, pTradingAccount->PositionProfit, balance);

	// 	PortfolioManager::instance()._account.AccountID = pTradingAccount->AccountID;
	// 	PortfolioManager::instance()._account.PreviousDayEquityWithLoanValue = pTradingAccount->PreBalance;
	// 	PortfolioManager::instance()._account.NetLiquidation = balance;
	// 	PortfolioManager::instance()._account.AvailableFunds = pTradingAccount->Available;
	// 	PortfolioManager::instance()._account.Commission = pTradingAccount->Commission;
	// 	PortfolioManager::instance()._account.FullMaintainanceMargin = pTradingAccount->CurrMargin;
	// 	PortfolioManager::instance()._account.RealizedPnL = pTradingAccount->CloseProfit;
	// 	PortfolioManager::instance()._account.UnrealizedPnL = pTradingAccount->PositionProfit;

	// 	sendAccountMessage();
	// }

	// ///请求查询合约响应 (respond to ReqQryInstrument)
	// void Tapbrokerage::OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	// pInstrument->StrikePrice; pInstrument->EndDelivDate; pInstrument->IsTrading;
	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap broker server OnRspQryInstrument: InstrumentID=%s, InstrumentName=%s, ExchangeID=%s, ExchangeInstID=%s, VolumeMultiple=%d, PriceTick=%.2f, UnderlyingInstrID=%s, ProductClass=%c, ExpireDate=%s, LongMarginRatio=%.2f.\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pInstrument->InstrumentID, pInstrument->InstrumentName, pInstrument->ExchangeID, pInstrument->ExchangeInstID,
	// 		pInstrument->VolumeMultiple, pInstrument->PriceTick, pInstrument->UnderlyingInstrID, pInstrument->ProductClass, pInstrument->ExpireDate, pInstrument->LongMarginRatio);

	// 	string symbol = TapSymbolToSecurityFullName(pInstrument);

	// 	auto it = DataManager::instance().securityDetails_.find(symbol);
	// 	if (it == DataManager::instance().securityDetails_.end()) {
	// 		Security s;
	// 		s.symbol = pInstrument->InstrumentName;
	// 		s.exchange = pInstrument->ExchangeID;
	// 		s.securityType = "FUT";
	// 		s.multiplier = pInstrument->VolumeMultiple;
	// 		s.localName = pInstrument->InstrumentName;
	// 		s.ticksize = std::to_string(pInstrument->PriceTick);

	// 		DataManager::instance().securityDetails_[symbol] = s;
	// 	}

	// 	sendContractMessage(symbol, pInstrument->InstrumentName, std::to_string(pInstrument->PriceTick));
	// }

	// ///错误应答
	// void Tapbrokerage::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
	// 	PRINT_TO_FILE("ERROR:[%s,%d][%s]Tap broker server OnRspError: ErrorID=%d, ErrorMsg=%s.\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, pRspInfo->ErrorMsg);

	// 	sendGeneralMessage(string("Tap Trader Server OnRspError") +
	// 		SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + pRspInfo->ErrorMsg);
	// }

	// ///报单通知
	// void Tapbrokerage::OnRtnOrder(CThostFtdcOrderField *pOrder) {
	// 	// 报单回报
	// 	// pOrder->ExchangeID		交易所编号 
	// 	// pOrder->InstrumentID		合约代码
	// 	// pOrder->OrderRef			报单引用
	// 	// pOrder->Direction		买卖方向
	// 	// pOrder->CombOffsetFlag	组合开平标志
	// 	// pOrder->LimitPrice		价格
	// 	// pOrder->VolumeTotalOriginal		数量
	// 	// pOrder->VolumeTraded		今成交数量
	// 	// pOrder->VolumeTotal		剩余数量
	// 	// Order->OrderSysID		报单编号（判断报单是否有效）
	// 	// pOrder->OrderStatus		报单状态
	// 	// pOrder->InsertDate		报单日期
	// 	// pOrder->SequenceNo		序号
	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap trade server OnRtnOrder details: InstrumentID=%s, OrderRef=%s, ExchangeID=%s, InsertTime=%s, CancelTime=%s, FrontID=%d, SessionID=%d, Direction=%c, CombOffsetFlag=%s, OrderStatus=%c, OrderSubmitStatus=%c, StatusMsg=%s, LimitPrice=%f, VolumeTotalOriginal=%d, VolumeTraded=%d, OrderSysID=%s, SequenceNo=%d.\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pOrder->InstrumentID, pOrder->OrderRef, pOrder->ExchangeID, pOrder->InsertTime, pOrder->CancelTime,
	// 		pOrder->FrontID, pOrder->SessionID, pOrder->Direction, pOrder->CombOffsetFlag, pOrder->OrderStatus, pOrder->OrderSubmitStatus, pOrder->StatusMsg,
	// 		pOrder->LimitPrice, pOrder->VolumeTotalOriginal, pOrder->VolumeTraded, pOrder->OrderSysID, pOrder->SequenceNo);	// TODO: diff between tradeid and orderref

	// 	// increase order_id
	// 	int nOrderref = std::stoi(pOrder->OrderRef);
		
	// 	shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromBrokerOrderIdAndApi(nOrderref, "Tap");
	// 	if (o == nullptr) {
	// 		PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Broker order id is yet not tracked. OrderId= %d\n", __FILE__, __LINE__, __FUNCTION__, nOrderref);
	// 		// create an order
	// 		lock_guard<mutex> g(oid_mtx);
	// 		std::shared_ptr<Order> o = make_shared<Order>();
	// 		o->account = CConfig::instance().Tap_user_id;
	// 		o->api = "Tap";
	// 		o->clientOrderId = -1;
	// 		o->fullSymbol = pOrder->InstrumentID;
	// 		o->orderSize = (pOrder->Direction == '0'? 1 : -1) * pOrder->VolumeTotalOriginal;
	// 		o->clientId = -1;
	// 		o->limitPrice = pOrder->LimitPrice;
	// 		o->stopPrice = 0.0;
	// 		o->orderStatus = TapOrderStatusToOrderStatus(pOrder->OrderStatus);
	// 		// o->orderStatus = OrderStatus::OS_Acknowledged;
	// 		o->orderFlag = TapPositionEffectToOrderFlag(pOrder->CombOffsetFlag[0]);

	// 		o->serverOrderId = m_serverOrderId;
	// 		o->brokerOrderId = nOrderref;
	// 		o->createTime = ymdhmsf();
	// 		o->orderType = "LMT";					// assumed

	// 		m_serverOrderId++;
	// 		// m_brokerOrderId++;
	// 		if (m_brokerOrderId <= (nOrderref + 1))
	// 			m_brokerOrderId = nOrderref + 1;

	// 		OrderManager::instance().trackOrder(o);
	// 		sendOrderStatus(o->serverOrderId);
	// 	}
	// 	else {
	// 		// OrderManager::instance().gotOrder(o->serverOrderId);		// order received/confirmed
	// 		// including cancelled
	// 		o->orderStatus = TapOrderStatusToOrderStatus(pOrder->OrderStatus);
	// 		o->orderFlag = TapPositionEffectToOrderFlag(pOrder->CombOffsetFlag[0]);

	// 		sendOrderStatus(o->serverOrderId);			// acknowledged
	// 	}		
	// }

	// /// 成交通知
	// void Tapbrokerage::OnRtnTrade(CThostFtdcTradeField *pTrade) {
	// 	PRINT_TO_FILE("INFO:[%s,%d][%s]Tap trade server OnRtnTrade details: TradeID=%s, OrderRef=%s, InstrumentID=%s, ExchangeID=%s, TradeTime=%s, OffsetFlag=%c, Direction=%c, Price=%f, Volume=%d.\n",
	// 		__FILE__, __LINE__, __FUNCTION__, pTrade->TradeID, pTrade->OrderRef, pTrade->InstrumentID, pTrade->ExchangeID, pTrade->TradeTime,
	// 		pTrade->OffsetFlag, pTrade->Direction, pTrade->Price, pTrade->Volume);		// TODO: diff between tradeid and orderref

	// 	Fill t;
	// 	t.fullSymbol = pTrade->InstrumentID;
	// 	t.tradetime = pTrade->TradeTime;
	// 	t.brokerOrderId = std::stoi(pTrade->OrderRef);
	// 	t.tradeId = std::stoi(pTrade->TraderID);
	// 	t.tradePrice = pTrade->Price;
	// 	t.tradeSize = (pTrade->Direction == THOST_FTDC_D_Buy ? 1 : -1)*pTrade->Volume;

	// 	auto o = OrderManager::instance().retrieveOrderFromBrokerOrderIdAndApi(std::stoi(pTrade->OrderRef), "Tap");
	// 	if (o != nullptr) {
	// 		t.serverOrderId = o->serverOrderId;
	// 		t.clientOrderId = o->clientOrderId;
	// 		t.brokerOrderId = o->brokerOrderId;
	// 		t.account = o->account;
	// 		t.api = o->api;

	// 		OrderManager::instance().gotFill(t);
	// 		// sendOrderStatus(o->serverOrderId);
	// 		sendOrderFilled(t);		// BOT SLD
	// 	}
	// 	else {
	// 		PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]fill order id is not tracked. OrderId= %s\n", __FILE__, __LINE__, __FUNCTION__, pTrade->OrderRef);

	// 		t.serverOrderId = -1;
	// 		t.clientOrderId = -1;
	// 		t.account = CConfig::instance().Tap_broker_id;
	// 		t.api = "Tap";

	// 		sendOrderFilled(t);		// BOT SLD
	// 	}		
	// }



	OrderStatus Tapbrokerage::TapOrderStatusToOrderStatus(const TAPIOrderStateType status) {
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

	OrderFlag Tapbrokerage::TapPositionEffectToOrderFlag(const TAPIPositionEffectType flag) {
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

	TAPIPositionEffectType Tapbrokerage::OrderFlagToTapPositionEffect(const OrderFlag flag) {
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
	OrderType Tapbrokerage::TapOrderTypeToOrderType(const TAPIOrderTypeType type){
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

	TAPIOrderTypeType Tapbrokerage::OrderTypeToTapOrderType(const OrderType type){
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