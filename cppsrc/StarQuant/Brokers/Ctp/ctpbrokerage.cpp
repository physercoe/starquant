#include <mutex>
#include <Common/Order/orderstatus.h>
#include <Common/Order/ordertype.h>
#include <Common/Order/fill.h>
#include <Common/Order/ordermanager.h>
#include <Common/Security/portfoliomanager.h>
#include <Common/Data/datamanager.h>
#include <Common/Logger/logger.h>
#include <Common/Util/util.h>
#include <Brokers/Ctp/ctpbrokerage.h>
#include <boost/locale.hpp>

using namespace std;
namespace StarQuant
{
	extern std::atomic<bool> gShutdown;

	ctpbrokerage::ctpbrokerage() 
		: isConnected_(false)
		, isLogedin_(false)
		, isAuthenticated_(false)
		, reqId_(0)
		, orderRef_(0)
		, frontID_(0)
		, sessionID_(0)
	{
		string path = CConfig::instance().logDir() + "/ctp/";
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);

		///创建TraderApi
		///@param pszFlowPath 存贮订阅信息文件的目录，默认为当前目录
		///@return 创建出的UserApi
		this->api_ = CThostFtdcTraderApi::CreateFtdcTraderApi(path.c_str());
		///注册回调接口
		///@param pSpi 派生自回调接口类的实例
		this->api_->RegisterSpi(this);

		if (CConfig::instance().ctp_auth_code == "NA") {
			requireAuthentication_ = false;
		}
		else {
			requireAuthentication_ = true;
		}
	}

	ctpbrokerage::~ctpbrokerage() {
		if (api_ != NULL) {
			disconnectFromBrokerage();
		}
	}

	void ctpbrokerage::processBrokerageMessages()
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
			while(! isLogedin_)
				msleep(1000);
			
			requestBrokerageAccountInformation(CConfig::instance().account);
			msleep(1000);
			requestOpenPositions(CConfig::instance().account);
			msleep(1000);
			requestSettlementInfoConfirm();
			_bkstate = BK_READYTOORDER;
			//_bkstate = BK_READYTOORDER;
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

	bool ctpbrokerage::connectToBrokerage() {
		if (!isConnected_) {
			//订阅共有流、私有流
			THOST_TE_RESUME_TYPE type = THOST_TERT_RESTART;		// THOST_TERT_RESUME, THOST_TERT_QUICK
			this->api_->SubscribePrivateTopic(type);
			this->api_->SubscribePublicTopic(type);

			// 注册前置机并初始化
			this->api_->RegisterFront((char*)CConfig::instance().ctp_broker_address.c_str());

			// 成功后调用 onFrontConnected
			this->api_->Init();

			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp brokerage connecting!\n", __FILE__, __LINE__, __FUNCTION__);
			
			//sendGeneralMessage("Connecting to ctp brokerage");
		}

		return true;
	}

	void ctpbrokerage::disconnectFromBrokerage() {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp brokerage connection disconnected!\n", __FILE__, __LINE__, __FUNCTION__);

		this->api_->RegisterSpi(NULL);
		this->api_->Release();
		this->api_ = NULL;
		isConnected_ = false;
		isLogedin_ = false;
		isAuthenticated_ = false;
	}

	bool ctpbrokerage::isConnectedToBrokerage() const {
		return (isConnected_) && (_bkstate >= BK_CONNECTED);						// automatic disconnect when shutdown
	}

	void ctpbrokerage::placeOrder(std::shared_ptr<Order> order) {
		if (order->orderStatus != OrderStatus::OS_NewBorn)
			return;

		// send order
		CThostFtdcInputOrderField orderfield = CThostFtdcInputOrderField();

		strcpy(orderfield.InstrumentID, order->fullSymbol.c_str());
		orderfield.VolumeTotalOriginal = std::abs(order->orderSize);

		// CTP的模拟交易不支持市价报单
		orderfield.OrderPriceType = order->orderType == OrderType::OT_Market ? THOST_FTDC_OPT_AnyPrice : THOST_FTDC_OPT_LimitPrice;
		orderfield.LimitPrice = order->orderType == OrderType::OT_Market ? 0.0 : order->limitPrice;
		orderfield.Direction = order->orderSize > 0 ? THOST_FTDC_D_Buy : THOST_FTDC_D_Sell;
		orderfield.CombOffsetFlag[0] = OrderFlagToCtpComboOffsetFlag(order->orderFlag);

		strcpy(orderfield.OrderRef, to_string(order->serverOrderId).c_str());

		strcpy(orderfield.InvestorID, CConfig::instance().ctp_user_id.c_str());
		strcpy(orderfield.UserID, CConfig::instance().ctp_user_id.c_str());
		strcpy(orderfield.BrokerID, CConfig::instance().ctp_broker_id.c_str());

		orderfield.CombHedgeFlag[0] = THOST_FTDC_HF_Speculation;			// 投机单
		orderfield.ContingentCondition = THOST_FTDC_CC_Immediately;		// 立即发单
		orderfield.ForceCloseReason = THOST_FTDC_FCC_NotForceClose;		// 非强平
		orderfield.IsAutoSuspend = 0;									// 非自动挂起
		orderfield.UserForceClose = 0;									// 非用户强平
		orderfield.TimeCondition = THOST_FTDC_TC_GFD;					// 今日有效
		orderfield.VolumeCondition = THOST_FTDC_VC_AV;					// 任意成交量
		orderfield.MinVolume = 1;										// 最小成交量为1

		// TODO: 判断FAK和FOK
		//orderfield.OrderPriceType = THOST_FTDC_OPT_LimitPrice;
		//orderfield.TimeCondition = THOST_FTDC_TC_IOC;
		//orderfield.VolumeCondition = THOST_FTDC_VC_CV;				// FAK; FOK uses THOST_FTDC_VC_AV

		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Placing Order orderId=%ld: fullSymbol=%s\n", __FILE__, __LINE__, __FUNCTION__, order->serverOrderId, order->fullSymbol.c_str());
		
		lock_guard<mutex> g(orderStatus_mtx);
		order->api = "CTP";
		int i = api_->ReqOrderInsert(&orderfield, reqId_++);
		if (i != 0){
			cout<<"trade req order insert error "<<i<<endl;
			order->orderStatus = OrderStatus::OS_Error;
			sendOrderStatus(order->serverOrderId);
		}
		order->orderStatus = OrderStatus::OS_Submitted;
		sendOrderStatus(order->serverOrderId);
	}

	void ctpbrokerage::requestNextValidOrderID() {
		cout<<"broker req next order  "<<endl;


		//lock_guard<mutex> g(oid_mtx);
		//m_brokerOrderId = 0;

		if (requireAuthentication_) {
			// trigger onRspAuthenticate()
			requestAuthenticate(CConfig::instance().ctp_user_id, CConfig::instance().ctp_auth_code, 
				CConfig::instance().ctp_broker_id, CConfig::instance().ctp_user_prod_info);				// authenticate first
		}
		else if (!isLogedin_) {

			requestUserLogin();
		}


	}


	void ctpbrokerage::reqGlobalCancel() {
	}

	// does not accept cancel order
	void ctpbrokerage::cancelOrder(int oid) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order m_orderId=%ld\n", __FILE__, __LINE__, __FUNCTION__, (long)oid);

		CThostFtdcInputOrderActionField myreq = CThostFtdcInputOrderActionField();
		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
		strcpy(myreq.InstrumentID, o->fullSymbol.c_str());
		//strcpy(myreq.ExchangeID, o->.c_str());			// TODO: get exchangeID from fullSymbol, e.g. "SHFE"  IF1709 FUT CFFEX 300, where 300 is multiplier
		strcpy(myreq.OrderRef, to_string(o->brokerOrderId).c_str());
		// myreq.OrderSysID		// TODO: what is this used for?
		myreq.FrontID = frontID_;
		myreq.SessionID = sessionID_;
		myreq.ActionFlag = THOST_FTDC_AF_Delete;

		strcpy(myreq.InvestorID, CConfig::instance().ctp_user_id.c_str());
		strcpy(myreq.BrokerID, CConfig::instance().ctp_broker_id.c_str());

		int i = this->api_->ReqOrderAction(&myreq, reqId_++);
		if (i != 0){
			cout<<"trade req order action error "<<i<<endl;
		}
	}

	void ctpbrokerage::cancelOrders(const string& symbol) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order symbol=%s\n", __FILE__, __LINE__, __FUNCTION__, symbol.c_str());
	}

	void ctpbrokerage::cancelOrder(const string& ono) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order symbol=%s\n", __FILE__, __LINE__, __FUNCTION__, ono.c_str());
	}


	void ctpbrokerage::cancelAllOrders() {
		lock_guard<mutex> _g(mtx_CANCELALL);
	}

	// 查询账户
	void ctpbrokerage::requestBrokerageAccountInformation(const string& account_) {


		CThostFtdcQryTradingAccountField myreq = CThostFtdcQryTradingAccountField();

		strcpy(myreq.InvestorID, CConfig::instance().ctp_user_id.c_str());
		strcpy(myreq.BrokerID, CConfig::instance().ctp_broker_id.c_str());

		// triggers OnRspQryTradingAccount
		int i = this->api_->ReqQryTradingAccount(&myreq, reqId_++);			// return 0 = 发送投资者资金账户查询请求失败
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker requests brokerage account information.\n", __FILE__, __LINE__, __FUNCTION__);
		if (i!=0){
			cout<<"trade qry acc error "<<i<<endl;
		}
	}

	void ctpbrokerage::requestOpenOrders(const string& account_)
	{
	}

	/// 查询账户， trigger onRspQryInvestorPosition
	void ctpbrokerage::requestOpenPositions(const string& account_) {
		

		CThostFtdcQryInvestorPositionField myreq = CThostFtdcQryInvestorPositionField();

		strcpy(myreq.BrokerID, CConfig::instance().ctp_broker_id.c_str());
		strcpy(myreq.InvestorID, CConfig::instance().ctp_user_id.c_str());

		int i = this->api_->ReqQryInvestorPosition(&myreq, reqId_++);		// return 0 = 发送投资者持仓查询请求失败
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker requests open positions.\n", __FILE__, __LINE__, __FUNCTION__);
		if (i!=0){
			cout<<"trade qry pos error "<<i<<endl;
		}
		//cout<<"req pos end"<<endl;
	}

	void ctpbrokerage::requestAuthenticate(string userid, string authcode, string brokerid, string userproductinfo) {
		CThostFtdcReqAuthenticateField authField;

		strcpy(authField.UserID, userid.c_str());
		strcpy(authField.BrokerID, brokerid.c_str());
		strcpy(authField.AuthCode, authcode.c_str());
		strcpy(authField.UserProductInfo, userproductinfo.c_str());

		int i = this->api_->ReqAuthenticate(&authField, reqId_++);
		if (i != 0){
			cout<<"trade req auth error "<<i<<endl;
		}
		
	}

	///用户登录请求
	void ctpbrokerage::requestUserLogin() {
		cout<<"brokder req login "<<endl;
		CThostFtdcReqUserLoginField loginField = CThostFtdcReqUserLoginField();

		strcpy(loginField.BrokerID, CConfig::instance().ctp_broker_id.c_str());
		strcpy(loginField.UserID, CConfig::instance().ctp_user_id.c_str());
		strcpy(loginField.Password, CConfig::instance().ctp_password.c_str());

		int i = this->api_->ReqUserLogin(&loginField, reqId_++);
		if (i != 0){
			cout<<"trade req login error "<<i<<endl;
		}
	}

	///登出请求
	void ctpbrokerage::requestUserLogout() {
		CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();

		strcpy(logoutField.BrokerID, CConfig::instance().ctp_broker_id.c_str());
		strcpy(logoutField.UserID, CConfig::instance().ctp_user_id.c_str());

		int i = this->api_->ReqUserLogout(&logoutField, reqId_++);
		if (i != 0){
			cout<<"trade req logout error "<<i<<endl;
		}
	}

	/// 投资者结算结果确认, trigger response onRspSettlementInfoConfirm
	void ctpbrokerage::requestSettlementInfoConfirm() {


		CThostFtdcSettlementInfoConfirmField myreq = CThostFtdcSettlementInfoConfirmField();
		strcpy(myreq.BrokerID, CConfig::instance().ctp_broker_id.c_str());
		strcpy(myreq.InvestorID, CConfig::instance().ctp_user_id.c_str());
		int i = api_->ReqSettlementInfoConfirm(&myreq, reqId_++);			// return 0 = 发送投资者结算结果确认请求失败
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker requests settlement info comfirm.\n", __FILE__, __LINE__, __FUNCTION__);
		if (i != 0){
			cout<<"trade req settle error "<<i<<endl;
		}
	}

	////////////////////////////////////////////////////// begin callback/incoming function ///////////////////////////////////////
	// TODO: where is OnCancel confirmation ? 
	///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
	void ctpbrokerage::OnFrontConnected() {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker connected; Continue to login.\n", __FILE__, __LINE__, __FUNCTION__);
		cout<< "brokder front connected "<<endl;
		_bkstate = BK_CONNECTED;
		isConnected_ = true;
		reqId_ = 0;
	}

	///当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
	///@param nReason 错误原因
	///        0x1001 网络读失败
	///        0x1002 网络写失败
	///        0x2001 接收心跳超时
	///        0x2002 发送心跳失败
	///        0x2003 收到错误报文
	void ctpbrokerage::OnFrontDisconnected(int nReason) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker disconnected, nReason=%d.\n", __FILE__, __LINE__, __FUNCTION__, nReason);
		_bkstate = BK_DISCONNECTED;
		isConnected_ = false;
		isLogedin_ = false;
		isAuthenticated_ = false;
	}

	///心跳超时警告。当长时间未收到报文时，该方法被调用。
	void ctpbrokerage::OnHeartBeatWarning(int nTimeLapse) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp brokerage heartbeat overtime error, nTimeLapse=%d.\n", __FILE__, __LINE__, __FUNCTION__, nTimeLapse);
	}

	///客户端认证响应
	void ctpbrokerage::OnRspAuthenticate(CThostFtdcRspAuthenticateField *pRspAuthenticateField, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo->ErrorID == 0) {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker authenticated. Continue to log in.\n", __FILE__, __LINE__, __FUNCTION__);
			isAuthenticated_ = true;
			// proceed to login
			requestUserLogin();
		}
		else {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker authentication failed. \n", __FILE__, __LINE__, __FUNCTION__);
			//sendGeneralMessage("Ctp broker authentication failed");
		}
	}

	/// 登录请求响应
	void ctpbrokerage::OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo == nullptr)
		{
			cout<<"onrsp login return nullptr"<<endl;
			return;
		}
		
		if (pRspInfo->ErrorID == 0) {
			// 保存会话参数
			// TODO: what frontID_ and sessionID_ are used for? -- one place is in cancelOrder
			frontID_ = pRspUserLogin->FrontID;
			sessionID_ = pRspUserLogin->SessionID;

			isLogedin_ = true;
			cout<<"brokder logged in "<<endl;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server user logged in, TradingDay=%s, LoginTime=%s, BrokerID=%s, UserID=%s, frontID=%d, sessionID=%d, MaxOrderRef=%s\n.",
				__FILE__, __LINE__, __FUNCTION__,
				pRspUserLogin->TradingDay, pRspUserLogin->LoginTime, pRspUserLogin->BrokerID, pRspUserLogin->UserID, pRspUserLogin->FrontID, pRspUserLogin->SessionID, pRspUserLogin->MaxOrderRef);

			// https://stackoverflow.com/questions/22753328/c-error-expression-must-have-integral-or-enum-type-getting-this-from-a-s
			//sendGeneralMessage(string("Ctp broker server user logged in:") +
			//	SERIALIZATION_SEPARATOR + to_string(frontID_) + SERIALIZATION_SEPARATOR + to_string(sessionID_));

			// TODO: pRspUserLogin->MaxOrderRef used for?  
			// strcpy(order_ref, pRspUserLogin->MaxOrderRef);

			if (_bkstate <= BK_GETORDERIDACK)
				_bkstate = BK_GETORDERIDACK;

			// TODO二: 放在 _bkstate 改变后面行吗？


		}
		else {
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );  
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server user login failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());

			//sendGeneralMessage(string("CTP Trader Server OnRspUserLogin error:") +
			//	SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
			//if (pRspInfo->ErrorID==140){
				//ReqUserPasswordUpdate(CThostFtdcUserPasswordUpdateField *pUserPasswordUpdate, int nRequestID) = 0;


			//}
			
		}
	}

	///登出请求响应
	void ctpbrokerage::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo->ErrorID == 0) {
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server user logged out, BrokerID=%s, UserID=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pUserLogout->BrokerID, pUserLogout->UserID);
			isLogedin_ = false;
			isAuthenticated_ = false;
		}
		else {
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server user logout failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());

			sendGeneralMessage(string("CTP Trader Server OnRspUserLogout error:") +
				SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
		}
	}

	///报单录入请求响应(参数不通过)
	void ctpbrokerage::OnRspOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo == nullptr)
		{
			cout<<"onrsp orderinsert return nullptr"<<endl;
			return;
		}
		
		bool bResult = pRspInfo && (pRspInfo->ErrorID != 0);
		string errormsgutf8;
		errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
		if (!bResult)
		{
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspOrderInsert: OrderRef=%s, InstrumentID=%s, LimitPrice=%.2f, VolumeTotalOriginal=%d, Direction=%c.\n",
				__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef, pInputOrder->InstrumentID, pInputOrder->LimitPrice, pInputOrder->VolumeTotalOriginal, pInputOrder->Direction);

			lock_guard<mutex> g(orderStatus_mtx);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stoi(pInputOrder->OrderRef));

			if (o != nullptr) {
				o->orderStatus = OS_Error;			// rejected ?

				sendOrderStatus(o->serverOrderId);

				sendGeneralMessage(string("CTP Trader Server OnRspOrderInsert:") +
					SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
			}
			else {
				PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]tp broker server OnRspOrderInsert cant find order : OrderRef=%s\n",
					__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
			}
		}
		else
		{
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnRspOrderInsert: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());

			lock_guard<mutex> g(orderStatus_mtx);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stoi(pInputOrder->OrderRef));

			if (o != nullptr) {
				o->orderStatus = OS_Error;			// rejected ?

				sendOrderStatus(o->serverOrderId);
				sendGeneralMessage(string("CTP Trader Server OnRspOrderInsert error:") +
					SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
			}
			else {
				PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]tp broker server OnRspOrderInsert cant find order : OrderRef=%s\n",
					__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
			}			
		}
	}

	///报单操作请求响应(参数不通过)
	// 撤单错误（柜台）
	void ctpbrokerage::OnRspOrderAction(CThostFtdcInputOrderActionField *pInputOrderAction, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {

		// if ((pRspInfo == nullptr) && (pInputOrderAction == nullptr))
		// {
		// 	cout<<"onrsp qry order return nullptr"<<endl;
		// 	return;
		// }



		if (pRspInfo == nullptr)
		{
			cout<<"onrsp order return nullptr"<<endl;
			return;
		}
		
		bool bResult = pRspInfo && (pRspInfo->ErrorID != 0);
		string errormsgutf8;
		errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
		if (!bResult)
		{
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspOrderAction: OrderRef=%s, InstrumentID=%s, ActionFlag=%c.\n",
				__FILE__, __LINE__, __FUNCTION__, pInputOrderAction->OrderRef, pInputOrderAction->InstrumentID, pInputOrderAction->ActionFlag);
		}
		else
		{
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnRspOrderAction failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());

			sendGeneralMessage(to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
		}
	}

	///投资者结算结果确认响应
	void ctpbrokerage::OnRspSettlementInfoConfirm(CThostFtdcSettlementInfoConfirmField *pSettlementInfoConfirm, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspSettlementInfoConfirm, ConfirmDate=%s, ConfirmTime=%s.\n",
			__FILE__, __LINE__, __FUNCTION__, pSettlementInfoConfirm->ConfirmDate, pSettlementInfoConfirm->ConfirmTime);

		// 查询合约代码, trigger response OnRspQryInstrument
		CThostFtdcQryInstrumentField myreq = CThostFtdcQryInstrumentField();
		//int i = this->api_->ReqQryInstrument(&myreq, reqId_++);
		//PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker servers ReqQryInstrument.\n", 	__FILE__, __LINE__, __FUNCTION__);
	}

	///请求查询投资者持仓响应 (respond to requestOpenPositions)
	void ctpbrokerage::OnRspQryInvestorPosition(CThostFtdcInvestorPositionField *pInvestorPosition, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		//cout<<" on respqrtpos called"<<endl;
		if ((pRspInfo == nullptr) && (pInvestorPosition == nullptr))
		{
			cout<<"onrsp qry pos return nullptr"<<endl;
			return;
		}

		// if (pRspInfo == nullptr)
		// {
		// 	cout<<"onrsp qry pos return nullptr"<<endl;
		// 	return;
		// }
		bool bResult = (pInvestorPosition == nullptr);
		// bool bResult = pRspInfo && (pRspInfo->ErrorID != 0);

		if (!bResult){
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspQryInvestorPosition, InstrumentID=%s, InvestorID=%s, OpenAmount=%f, OpenVolume=%d, PosiDirection=%c, PositionProfit=%.2f, PositionCost=%.2f, UseMargin=%.2f, LongFrozen=%d, ShortFrozen=%d, TradingDay=%s, YdPosition=%d, last=%d\n",
				__FILE__, __LINE__, __FUNCTION__, pInvestorPosition->InstrumentID, pInvestorPosition->InvestorID, pInvestorPosition->OpenAmount, pInvestorPosition->OpenVolume,
				pInvestorPosition->PosiDirection, pInvestorPosition->PositionProfit, pInvestorPosition->PositionCost, pInvestorPosition->UseMargin,
				pInvestorPosition->LongFrozen, pInvestorPosition->ShortFrozen, pInvestorPosition->TradingDay, pInvestorPosition->YdPosition, bIsLast);

			// TODO: 针对上期所持仓的今昨分条返回（有昨仓、无今仓），读取昨仓数据
			// pInvestorPosition->YdPosition;
			// TODO: 汇总总仓, 计算持仓均价, 读取冻结

			if ((pInvestorPosition->Position != 0.0) && (pInvestorPosition->YdPosition != 0.0)){
			//if (true) {
				Position pos;
				pos._posNo = to_string(pInvestorPosition->SettlementID);
				pos._type='a';
				pos._fullsymbol = pInvestorPosition->InstrumentID;
				pos._size = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? 1 : -1) * pInvestorPosition->Position;
				pos._avgprice = pInvestorPosition->PositionCost / pInvestorPosition->Position;
				pos._openpl = pInvestorPosition->PositionProfit;
				pos._closedpl = pInvestorPosition->CloseProfit;
				pos._account = CConfig::instance().ctp_user_id;
				pos._pre_size = pInvestorPosition->YdPosition;
				pos._freezed_size = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? pInvestorPosition->LongFrozen : pInvestorPosition->ShortFrozen);
				pos._api = "CTP";
				PortfolioManager::instance().Add(pos);
				sendOpenPositionMessage(pos);
			}

		}
		else
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			cout<<" onQry Investor error "<<pRspInfo->ErrorID<<'|'<<errormsgutf8<<endl;
		}


	}

	///请求查询资金账户响应 (respond to requestAccount)
	void ctpbrokerage::OnRspQryTradingAccount(CThostFtdcTradingAccountField *pTradingAccount, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		// balance和快期中的账户可能不一样
		if ((pRspInfo == nullptr) && (pTradingAccount == nullptr))
		{
			cout<<"onrsp qry acc return nullptr"<<endl;
			return;
		}
		
		//bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		bool bResult = (pTradingAccount == nullptr);
		if (!bResult){
			double balance = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
				+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
				+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;

			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspQryTradingAccount: AccountID=%s, Available=%.2f, PreBalance=%.2f, Deposit=%.2f, Withdraw=%.2f, WithdrawQuota=%.2f, Commission=%.2f, CurrMargin=%.2f, FrozenMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f, balance=%.2f.\n",
				__FILE__, __LINE__, __FUNCTION__, pTradingAccount->AccountID, pTradingAccount->Available, pTradingAccount->PreBalance,
				pTradingAccount->Deposit, pTradingAccount->Withdraw, pTradingAccount->WithdrawQuota, pTradingAccount->Commission,
				pTradingAccount->CurrMargin, pTradingAccount->FrozenMargin, pTradingAccount->CloseProfit, pTradingAccount->PositionProfit, balance);

			PortfolioManager::instance()._account.AccountID = pTradingAccount->AccountID;
			PortfolioManager::instance()._account.PreviousDayEquityWithLoanValue = pTradingAccount->PreBalance;
			PortfolioManager::instance()._account.NetLiquidation = balance;
			PortfolioManager::instance()._account.AvailableFunds = pTradingAccount->Available;
			PortfolioManager::instance()._account.Commission = pTradingAccount->Commission;
			PortfolioManager::instance()._account.FullMaintainanceMargin = pTradingAccount->CurrMargin;
			PortfolioManager::instance()._account.RealizedPnL = pTradingAccount->CloseProfit;
			PortfolioManager::instance()._account.UnrealizedPnL = pTradingAccount->PositionProfit;

			sendAccountMessage();
		}
		else {
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			cout<<" onQry Acc error "<<'|'<<errormsgutf8<<endl;

		}

	}

	///请求查询合约响应 (respond to ReqQryInstrument)
	void ctpbrokerage::OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		// pInstrument->StrikePrice; pInstrument->EndDelivDate; pInstrument->IsTrading;
		if (pRspInfo == nullptr)
		{
			cout<<"onrsp qry instru return nullptr"<<endl;
			return;
		}
		
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspQryInstrument: InstrumentID=%s, InstrumentName=%s, ExchangeID=%s, ExchangeInstID=%s, VolumeMultiple=%d, PriceTick=%.2f, UnderlyingInstrID=%s, ProductClass=%c, ExpireDate=%s, LongMarginRatio=%.2f.\n",
			__FILE__, __LINE__, __FUNCTION__, pInstrument->InstrumentID, pInstrument->InstrumentName, pInstrument->ExchangeID, pInstrument->ExchangeInstID,
			pInstrument->VolumeMultiple, pInstrument->PriceTick, pInstrument->UnderlyingInstrID, pInstrument->ProductClass, pInstrument->ExpireDate, pInstrument->LongMarginRatio);

		string symbol = CtpSymbolToSecurityFullName(pInstrument);

		auto it = DataManager::instance().securityDetails_.find(symbol);
		if (it == DataManager::instance().securityDetails_.end()) {
			Security s;
			s.symbol = pInstrument->InstrumentName;
			s.exchange = pInstrument->ExchangeID;
			s.securityType = "FUT";
			s.multiplier = pInstrument->VolumeMultiple;
			s.localName = pInstrument->InstrumentName;
			s.ticksize = std::to_string(pInstrument->PriceTick);

			DataManager::instance().securityDetails_[symbol] = s;
		}

		sendContractMessage(symbol, pInstrument->InstrumentName, std::to_string(pInstrument->PriceTick));
	}

	///错误应答
	void ctpbrokerage::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		string errormsgutf8;
		errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
		PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnRspError: ErrorID=%d, ErrorMsg=%s.\n",
			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());

		sendGeneralMessage(string("CTP Trader Server OnRspError") +
			SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
	}

	///报单通知
	void ctpbrokerage::OnRtnOrder(CThostFtdcOrderField *pOrder) {
		// 报单回报
		// pOrder->ExchangeID		交易所编号 
		// pOrder->InstrumentID		合约代码
		// pOrder->OrderRef			报单引用
		// pOrder->Direction		买卖方向
		// pOrder->CombOffsetFlag	组合开平标志
		// pOrder->LimitPrice		价格
		// pOrder->VolumeTotalOriginal		数量
		// pOrder->VolumeTraded		今成交数量
		// pOrder->VolumeTotal		剩余数量
		// Order->OrderSysID		报单编号（判断报单是否有效）
		// pOrder->OrderStatus		报单状态
		// pOrder->InsertDate		报单日期
		// pOrder->SequenceNo		序号
		PRINT_TO_FILE("INFO:[%s,%d][%s]CTP trade server OnRtnOrder details: InstrumentID=%s, OrderRef=%s, ExchangeID=%s, InsertTime=%s, CancelTime=%s, FrontID=%d, SessionID=%d, Direction=%c, CombOffsetFlag=%s, OrderStatus=%c, OrderSubmitStatus=%c, StatusMsg=%s, LimitPrice=%f, VolumeTotalOriginal=%d, VolumeTraded=%d, OrderSysID=%s, SequenceNo=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, pOrder->InstrumentID, pOrder->OrderRef, pOrder->ExchangeID, pOrder->InsertTime, pOrder->CancelTime,
			pOrder->FrontID, pOrder->SessionID, pOrder->Direction, pOrder->CombOffsetFlag, pOrder->OrderStatus, pOrder->OrderSubmitStatus, GBKToUTF8(pOrder->StatusMsg).c_str(),
			pOrder->LimitPrice, pOrder->VolumeTotalOriginal, pOrder->VolumeTraded, pOrder->OrderSysID, pOrder->SequenceNo);	// TODO: diff between tradeid and orderref
		cout<<pOrder->StatusMsg<<" "<<GBKToUTF8(pOrder->StatusMsg).c_str()<<endl;
		// increase order_id
		int nOrderref = std::stoi(pOrder->OrderRef);
		
		shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(nOrderref);
		if (o == nullptr) {
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Broker order id is yet not tracked. OrderId= %d\n", __FILE__, __LINE__, __FUNCTION__, nOrderref);
			// create an order
			lock_guard<mutex> g(oid_mtx);
			std::shared_ptr<Order> o = make_shared<Order>();
			o->account = CConfig::instance().ctp_user_id;
			o->api = "CTP";
			o->clientOrderId = -1;
			o->fullSymbol = pOrder->InstrumentID;
			o->orderSize = (pOrder->Direction == '0'? 1 : -1) * pOrder->VolumeTotalOriginal;
			o->clientId = -1;
			o->limitPrice = pOrder->LimitPrice;
			o->stopPrice = 0.0;
			o->orderStatus = CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			// o->orderStatus = OrderStatus::OS_Acknowledged;
			o->orderFlag = CtpComboOffsetFlagToOrderFlag(pOrder->CombOffsetFlag[0]);

			o->serverOrderId = m_serverOrderId;
			o->brokerOrderId = nOrderref;
			o->createTime = ymdhmsf();
			o->orderType = OrderType::OT_Limit;					// assumed

			m_serverOrderId++;
			// m_brokerOrderId++;
			if (m_brokerOrderId <= (nOrderref + 1))
				m_brokerOrderId = nOrderref + 1;

			OrderManager::instance().trackOrder(o);
			sendOrderStatus(o->serverOrderId);
		}
		else {
			// OrderManager::instance().gotOrder(o->serverOrderId);		// order received/confirmed
			// including cancelled
			o->orderStatus = CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			o->orderFlag = CtpComboOffsetFlagToOrderFlag(pOrder->CombOffsetFlag[0]);
			o->orderNo =pOrder->OrderSysID;
			sendOrderStatus(o->serverOrderId);			// acknowledged
		}		
	}

	/// 成交通知
	void ctpbrokerage::OnRtnTrade(CThostFtdcTradeField *pTrade) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]CTP trade server OnRtnTrade details: TradeID=%s, OrderRef=%s, InstrumentID=%s, ExchangeID=%s, TradeTime=%s, OffsetFlag=%c, Direction=%c, Price=%f, Volume=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, pTrade->TradeID, pTrade->OrderRef, pTrade->InstrumentID, pTrade->ExchangeID, pTrade->TradeTime,
			pTrade->OffsetFlag, pTrade->Direction, pTrade->Price, pTrade->Volume);		// TODO: diff between tradeid and orderref

		Fill t;
		t.fullSymbol = pTrade->InstrumentID;
		t.tradetime = pTrade->TradeTime;
		t.brokerOrderId = std::stoi(pTrade->OrderRef);
		t.orderNo = pTrade->OrderSysID;
		//t.tradeId = std::stoi(pTrade->TraderID);
		t.tradeNo = pTrade->TraderID;
		t.tradePrice = pTrade->Price;
		t.tradeSize = (pTrade->Direction == THOST_FTDC_D_Buy ? 1 : -1)*pTrade->Volume;
		t.fillflag = CtpComboOffsetFlagToOrderFlag(pTrade->OffsetFlag);
		auto o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stoi(pTrade->OrderRef));
		if (o != nullptr) {
			t.serverOrderId = o->serverOrderId;
			t.clientOrderId = o->clientOrderId;
			t.brokerOrderId = o->brokerOrderId;
			t.account = o->account;
			t.api = o->api;
			o->fillNo = t.tradeNo;

			OrderManager::instance().gotFill(t);
			// sendOrderStatus(o->serverOrderId);
			sendOrderFilled(t);		// BOT SLD
		}
		else {
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]fill order id is not tracked. OrderId= %s\n", __FILE__, __LINE__, __FUNCTION__, pTrade->OrderRef);

			t.serverOrderId = -1;
			t.clientOrderId = -1;
			t.account = CConfig::instance().ctp_broker_id;
			t.api = "CTP";

			sendOrderFilled(t);		// BOT SLD
		}		
	}

	///报单录入错误回报
	void ctpbrokerage::OnErrRtnOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo) {
		string errormsgutf8;
		errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
		PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnErrRtnOrderInsert: ErrorID=%d, ErrorMsg=%s, OrderRef=%s, InstrumentID=%s, ExchangeID=%s, Direction=%c, CombOffsetFlag=%s, LimitPrice=%f, VolumeTotalOriginal=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str(),
			pInputOrder->OrderRef, pInputOrder->InstrumentID, pInputOrder->ExchangeID,
			pInputOrder->Direction, pInputOrder->CombOffsetFlag, pInputOrder->LimitPrice, pInputOrder->VolumeTotalOriginal);

		lock_guard<mutex> g(orderStatus_mtx);
		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromBrokerOrderIdAndApi(std::stoi(pInputOrder->OrderRef), "CTP");
		if (o != nullptr) {
			o->orderStatus = OS_Error;			// rejected
			sendOrderStatus(o->serverOrderId);
		}
		else {
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Broker order id is not tracked. OrderId= %s\n", __FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
		}

		sendGeneralMessage(string("CTP Trader Server OnErrRtnOrderInsert") +
			SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
	}

	///报单操作错误回报
	void ctpbrokerage::OnErrRtnOrderAction(CThostFtdcOrderActionField *pOrderAction, CThostFtdcRspInfoField *pRspInfo) {
		string errormsgutf8;
		errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
		PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnErrRtnOrderAction: ErrorID=%d, ErrorMsg=%s.\n",
			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());

		sendGeneralMessage(string("CTP Trader Server OnErrRtnOrderAction") +
			SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
	}
	////////////////////////////////////////////////////// end callback/incoming function ///////////////////////////////////////
	string ctpbrokerage::SecurityFullNameToCtpSymbol(const std::string& symbol)
	{
		vector<string> v = stringsplit(symbol, ' ');

		return v[0];
	}

	string ctpbrokerage::CtpSymbolToSecurityFullName(CThostFtdcInstrumentField * pInstrument)
	{
		char sym[128] = {};
		sprintf(sym, "%s FUT %s %i", pInstrument->InstrumentID, pInstrument->ExchangeID, pInstrument->VolumeMultiple);

		string symbol = sym;
		return symbol;
	}

	OrderStatus ctpbrokerage::CtpOrderStatusToOrderStatus(const char status) {
		if (status == THOST_FTDC_OST_AllTraded) {
			return OrderStatus::OS_Filled;
		}
		else if (status == THOST_FTDC_OST_PartTradedQueueing) {
			return OrderStatus::OS_PartiallyFilled;
		}
		else if (status == THOST_FTDC_OST_NoTradeQueueing) {
			return OrderStatus::OS_Acknowledged;
		}
		else if (status == THOST_FTDC_OST_Canceled) {
			return OrderStatus::OS_Canceled;
		}
		else if (status == THOST_FTDC_OST_Unknown) {
			return OrderStatus::OS_UNKNOWN;
		}
		else {
			return OrderStatus::OS_UNKNOWN;
		}
	}

	OrderFlag ctpbrokerage::CtpComboOffsetFlagToOrderFlag(const char flag) {
		OrderFlag f;

		switch (flag) {
			case THOST_FTDC_OF_Open:
				f = OrderFlag::OF_OpenPosition;
				break;
			case THOST_FTDC_OF_Close:
				f = OrderFlag::OF_ClosePosition;
				break;
			case THOST_FTDC_OF_ForceClose:
				f = OrderFlag::OF_ForceClose;
				break;
			case THOST_FTDC_OF_CloseToday:
				f = OrderFlag::OF_CloseToday;
				break;
			case THOST_FTDC_OF_CloseYesterday:
				f = OrderFlag::OF_CloseYesterday;
				break;
			default:
				f = OrderFlag::OF_OpenPosition;
				break;
		}
		return f;
	}

	char ctpbrokerage::OrderFlagToCtpComboOffsetFlag(const OrderFlag flag) {
		char c;

		switch (flag) {
			case OrderFlag::OF_OpenPosition:
				c = THOST_FTDC_OF_Open;	// 开仓
				break;
			case OrderFlag::OF_ClosePosition:
				c = THOST_FTDC_OF_Close;	// 平仓
				break;
			case OrderFlag::OF_ForceClose:
				c = THOST_FTDC_OF_ForceClose;	// 平仓
				break;
			case OrderFlag::OF_CloseToday:
				c = THOST_FTDC_OF_CloseToday;	// 平今
				break;
			case OrderFlag::OF_CloseYesterday:
				c = THOST_FTDC_OF_CloseYesterday;	// 平昨
				break;
			default:
				c = THOST_FTDC_OF_Open;	// 开仓
				break;
		}
		return c;
	}



}