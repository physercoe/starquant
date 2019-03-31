#include <mutex>
#include <boost/locale.hpp>
#include <boost/algorithm/algorithm.hpp>

#include <Trade/order.h>
#include <Trade/orderstatus.h>
#include <Trade/ordertype.h>
#include <Trade/fill.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
#include <Data/datamanager.h>
#include <Common/logger.h>
#include <Common/util.h>
#include <Engine/CtpTDEngine.h>

using namespace std;
namespace StarQuant
{
	//extern std::atomic<bool> gShutdown;

	CtpTDEngine::CtpTDEngine() 
		: needauthentication_(false)
		, needsettlementconfirm_(true)
		, issettleconfirmed_(false)
		, m_brokerOrderId_(0)
		, reqId_(0)
		, orderRef_(0)
		, frontID_(0)
		, sessionID_(0)
	{
		init();
	}

	CtpTDEngine::~CtpTDEngine() {
		stop();
	}

	void CtpTDEngine::init(){
		if (IEngine::msgq_send_ == nullptr){
			IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		}
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
		}	
		name_ = "CTP_TD";
		ctpacc_ = CConfig::instance()._apimap["CTP"];
		string path = CConfig::instance().logDir() + "/ctp/";
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);
		///创建TraderApi
		this->api_ = CThostFtdcTraderApi::CreateFtdcTraderApi(path.c_str());
		///注册回调接口
		this->api_->RegisterSpi(this);
		if (CConfig::instance().ctp_auth_code == "NA") {
			needauthentication_ = false;
		}
		else {
			needauthentication_ = true;
		}
	}
	void CtpTDEngine::stop(){
		int tmp = disconnect();
		estate_  = EState::STOP;
		if (api_ != NULL){
			this->api_->RegisterSpi(NULL);
			this->api_->Release();
			this->api_ = NULL;
		}
	}

	void CtpTDEngine::start(){
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
				case MSG_TYPE_ORDER:
					if (estate_ == LOGIN_ACK){
						PRINT_TO_FILE_AND_CONSOLE("INFO[%s,%d][%s]receive order: %s\n", __FILE__, __LINE__, __FUNCTION__, msgin.c_str());
						insertOrder(v);
					}
					else{
						cout<<"CTP_TD is not connected,can not place order! "<<endl;
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
						cout<<"CTP_TD is not connected,can not cancel order! "<<endl;
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
						cout<<"CTP_TD is not connected,can not cancel order! "<<endl;
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
						cout<<"CTP_TD is not connected,can not cancel order! "<<endl;
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

	bool CtpTDEngine::connect(){
		THOST_TE_RESUME_TYPE privatetype = THOST_TERT_QUICK;// THOST_TERT_RESTART，THOST_TERT_RESUME, THOST_TERT_QUICK
		THOST_TE_RESUME_TYPE publictype = THOST_TERT_QUICK;// THOST_TERT_RESTART，THOST_TERT_RESUME, THOST_TERT_QUICK
		int error;
		int count = 0;// count numbers of tries, two many tries ends
		string ctp_td_address = ctpacc_.td_ip + ":" + to_string(ctpacc_.td_port);	
		CThostFtdcReqUserLoginField loginField = CThostFtdcReqUserLoginField();
		while (estate_ != LOGIN_ACK){
			switch (estate_){
				case DISCONNECTED:
					this->api_->SubscribePrivateTopic(privatetype);
					this->api_->SubscribePublicTopic(publictype);
					this->api_->RegisterFront((char*)ctpacc_.auth_code.c_str());
					this->api_->Init();
					estate_ = CONNECTING;
					PRINT_TO_FILE("INFO:[%s,%d][%s]CTP_TD register front!\n", __FILE__, __LINE__, __FUNCTION__);
					count++;
					break;
				case CONNECTING:
					msleep(100);
					break;
				case CONNECT_ACK:
					if(needauthentication_){
						PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp td authenticating ...\n", __FILE__, __LINE__, __FUNCTION__);
						CThostFtdcReqAuthenticateField authField;
						strcpy(authField.UserID, ctpacc_.userid.c_str());
						strcpy(authField.BrokerID, ctpacc_.brokerid.c_str());
						strcpy(authField.AuthCode, ctpacc_.auth_code.c_str());
						strcpy(authField.UserProductInfo, ctpacc_.productinfo.c_str());
						error = this->api_->ReqAuthenticate(&authField, reqId_++);
						count++;
						estate_ = AUTHENTICATING;
						if (error != 0){
							cout<<"Ctp td  authenticate  error "<<error<<endl;
							estate_ = CONNECT_ACK;
							msleep(1000);
						}
					}
					break;
				case AUTHENTICATING:
					msleep(100);
					break;
				case AUTHENTICATE_ACK:
					PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp td logining ...\n", __FILE__, __LINE__, __FUNCTION__);
					strcpy(loginField.BrokerID, ctpacc_.brokerid.c_str());
					strcpy(loginField.UserID, ctpacc_.userid.c_str());
					strcpy(loginField.Password, ctpacc_.password.c_str());
					error = this->api_->ReqUserLogin(&loginField, reqId_++);
					count++;
					estate_ = EState::LOGINING;
					if (error != 0){
						cout<<"Ctp TD login error "<<error<<endl;
						estate_ = EState::AUTHENTICATE_ACK;
						msleep(1000);
					}
					break;
				case LOGINING:
					msleep(100);
					break;
				default:
					break;
			}
			if(count >15){
				cout<<"too many tries fails, give up connecting"<<endl;
				//estate_ = EState::DISCONNECTED;
				return false;
			}			
		}
		return true;
	}

	bool CtpTDEngine::disconnect(){
		if(estate_ == LOGIN_ACK){
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td logouting ...\n", __FILE__, __LINE__, __FUNCTION__);
			CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();
			strcpy(logoutField.BrokerID, ctpacc_.brokerid.c_str());
			strcpy(logoutField.UserID, ctpacc_.userid.c_str());
			int error = this->api_->ReqUserLogout(&logoutField, reqId_++);
			estate_ = EState::LOGOUTING;
			if (error != 0){
				cout<<"ctp td logout error "<<error<<endl;//TODO: send error msg to client
				return false;
			}
			return true;
		}
		else{
			cout<<"ctp td is not connected(logined), can not disconnect! "<<endl;
			return false;
		}

	}


	void CtpTDEngine::insertOrder(const vector<string>& v){
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
		// begin call api's insert order		 TODO:加入不同订单类型
		CThostFtdcInputOrderField orderfield = CThostFtdcInputOrderField();
		string ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(o->fullSymbol);
		strcpy(orderfield.InstrumentID, ctpsym.c_str());
		orderfield.VolumeTotalOriginal = std::abs(o->orderSize);
		orderfield.OrderPriceType = o->orderType == OrderType::OT_Market ? THOST_FTDC_OPT_AnyPrice : THOST_FTDC_OPT_LimitPrice;
		orderfield.LimitPrice = o->orderType == OrderType::OT_Market ? 0.0 : o->limitPrice;
		orderfield.Direction = o->orderSize > 0 ? THOST_FTDC_D_Buy : THOST_FTDC_D_Sell;
		orderfield.CombOffsetFlag[0] = OrderFlagToCtpComboOffsetFlag(o->orderFlag);
		strcpy(orderfield.OrderRef, to_string(o->serverOrderId).c_str());
		strcpy(orderfield.InvestorID, ctpacc_.userid.c_str());
		strcpy(orderfield.UserID, ctpacc_.userid.c_str());
		strcpy(orderfield.BrokerID, ctpacc_.brokerid.c_str());
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
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Placing Order clientorderId=%ld: fullSymbol=%s\n", __FILE__, __LINE__, __FUNCTION__, o->clientOrderId, o->fullSymbol.c_str());
			lock_guard<mutex> g(orderStatus_mtx);
		int i = api_->ReqOrderInsert(&orderfield, reqId_++);
		o->orderStatus = OrderStatus::OS_Submitted;
		if (i != 0){
			cout<<"Ctp TD order insert error "<<i<<endl;
			o->orderStatus = OrderStatus::OS_Error;
			//sendOrderStatus(order->serverOrderId);
		}
		//sendOrderStatus(order->serverOrderId);
	}
	
	void CtpTDEngine::cancelOrder(const vector<string>& v){
		CThostFtdcInputOrderActionField myreq = CThostFtdcInputOrderActionField();
		int source = stoi(v[1]);
		long clientorderid = stol(v[3]);
		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromSourceAndClientOrderId(source,clientorderid);
		if (o != nullptr){
			string ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(o->fullSymbol);
			strcpy(myreq.InstrumentID, ctpsym.c_str());
			//strcpy(myreq.ExchangeID, o->.c_str());			// TODO: check the required field
			strcpy(myreq.OrderRef, to_string(o->serverOrderId).c_str());
			myreq.FrontID = frontID_;
			myreq.SessionID = sessionID_;
			myreq.ActionFlag = THOST_FTDC_AF_Delete;
			strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
			strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
			//myreq.OrderActionRef = int(m_brokerOrderId_++);//TODO: int <-> long is unsafe, use another way
			int i = this->api_->ReqOrderAction(&myreq, reqId_++);
			if (i != 0){
				cout<<"Ctp TD cancle order error "<<i<<endl;
			}
		}
		else{
			cout<<"ordermanager cannot find order!"<<endl;
		}

	}

	void CtpTDEngine::cancelOrder(int oid) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order m_orderId=%ld\n", __FILE__, __LINE__, __FUNCTION__, (long)oid);
		CThostFtdcInputOrderActionField myreq = CThostFtdcInputOrderActionField();
		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
		if (o != nullptr){
			string ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(o->fullSymbol);
			strcpy(myreq.InstrumentID, ctpsym.c_str());
			//strcpy(myreq.ExchangeID, o->.c_str());
			strcpy(myreq.OrderRef, to_string(o->brokerOrderId).c_str());
			myreq.FrontID = frontID_;
			myreq.SessionID = sessionID_;
			myreq.ActionFlag = THOST_FTDC_AF_Delete;
			strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
			strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
			int i = this->api_->ReqOrderAction(&myreq, reqId_++);
			if (i != 0){
				cout<<"Ctp TD cancle order error "<<i<<endl;
			}
		}
		else{
			cout<<"ordermanager cannot find order!"<<endl;
		}
	}

	void CtpTDEngine::cancelOrders(const string& symbol) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Cancel Order symbol=%s\n", __FILE__, __LINE__, __FUNCTION__, symbol.c_str());
	}

	// 查询账户
	void CtpTDEngine::queryAccount() {
		CThostFtdcQryTradingAccountField myreq = CThostFtdcQryTradingAccountField();
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		int error = api_->ReqQryTradingAccount(&myreq, reqId_++);			// return 0 = 发送投资者资金账户查询请求失败
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td requests account information.\n", __FILE__, __LINE__, __FUNCTION__);
		if (error != 0){
			cout<<"Ctp td qry acc error "<<error<<endl;
		}
	}

	void CtpTDEngine::queryOrder(const string& msgorder_){
	}

	/// 查询账户， trigger onRspQryInvestorPosition
	void CtpTDEngine::queryPosition() {
		CThostFtdcQryInvestorPositionField myreq = CThostFtdcQryInvestorPositionField();
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		int error = this->api_->ReqQryInvestorPosition(&myreq, reqId_++);		
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker requests open positions.\n", __FILE__, __LINE__, __FUNCTION__);
		if (error != 0){
			cout<<"trade qry pos error "<<error<<endl;
		}
	}

	////////////////////////////////////////////////////// begin callback/incoming function ///////////////////////////////////////
	///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
	void CtpTDEngine::OnFrontConnected() {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td frontend connected; Continue to login.\n", __FILE__, __LINE__, __FUNCTION__);
		cout<< "Ctp TD front connected "<<endl;
		estate_ = CONNECT_ACK;
		reqId_ = 0;
	}

	void CtpTDEngine::OnFrontDisconnected(int nReason) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp td disconnected, nReason=%d.\n", __FILE__, __LINE__, __FUNCTION__, nReason);
		estate_ = DISCONNECTED;
	}
	///心跳超时警告。当长时间未收到报文时，该方法被调用。
	void CtpTDEngine::OnHeartBeatWarning(int nTimeLapse) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp brokerage heartbeat overtime error, nTimeLapse=%d.\n", __FILE__, __LINE__, __FUNCTION__, nTimeLapse);
	}
	///客户端认证响应
	void CtpTDEngine::OnRspAuthenticate(CThostFtdcRspAuthenticateField *pRspAuthenticateField, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td authentication failed. \n", __FILE__, __LINE__, __FUNCTION__);
		}
		else{
			estate_ = AUTHENTICATE_ACK;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp TD authenticated. Continue to log in.\n", __FILE__, __LINE__, __FUNCTION__);
		}
	}
	/// 登录请求响应
	void CtpTDEngine::OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0)
		{
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );  
			cout<<"login error: "<< errormsgutf8 <<endl;
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server user login failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
		}
		else{
			frontID_ = pRspUserLogin->FrontID;
			sessionID_ = pRspUserLogin->SessionID;
			cout<<"Ctp TD logged in "<<endl;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td server user logged in, TradingDay=%s, LoginTime=%s, BrokerID=%s, UserID=%s, frontID=%d, sessionID=%d, MaxOrderRef=%s\n.",
				__FILE__, __LINE__, __FUNCTION__,
				pRspUserLogin->TradingDay, pRspUserLogin->LoginTime, pRspUserLogin->BrokerID, pRspUserLogin->UserID, pRspUserLogin->FrontID, pRspUserLogin->SessionID, pRspUserLogin->MaxOrderRef);
			if(needsettlementconfirm_){
				// 投资者结算结果确认
				CThostFtdcSettlementInfoConfirmField myreq = CThostFtdcSettlementInfoConfirmField();
				strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
				strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
				int error = api_->ReqSettlementInfoConfirm(&myreq, reqId_++);
				if (error != 0){
					cout<<"Error: Ctp TD settlement confirming error "<<error<<endl;
				}
				cout<<"Ctp TD settlement confirming "<<endl;			
				PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp TD settlement info comfirming.\n", __FILE__, __LINE__, __FUNCTION__);
			}
			else{
				estate_ = LOGIN_ACK;
			}

		}
	}
	///投资者结算结果确认响应
	void CtpTDEngine::OnRspSettlementInfoConfirm(CThostFtdcSettlementInfoConfirmField *pSettlementInfoConfirm, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );  
			cout<<"Settlement confirm error: "<< errormsgutf8 <<endl;
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp Td settlement confirm failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
		}
		else{
			estate_ = LOGIN_ACK;
			issettleconfirmed_ = true;
			cout<<"Settlement confirmed "<<endl;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspSettlementInfoConfirm, ConfirmDate=%s, ConfirmTime=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pSettlementInfoConfirm->ConfirmDate, pSettlementInfoConfirm->ConfirmTime);
		}
	}
	///登出请求响应
	void CtpTDEngine::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
 		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server user logout failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
			//sendGeneralMessage(string("CTP Trader Server OnRspUserLogout error:") +
			//	SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
		}
		else{
			estate_ = CONNECT_ACK;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td Logout, BrokerID=%s, UserID=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pUserLogout->BrokerID, pUserLogout->UserID);
		}
	}

	///报单录入请求响应(参数不通过)
	void CtpTDEngine::OnRspOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult)
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp Td OnRspOrderInsert: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td OnRspOrderInsert: OrderRef=%s, InstrumentID=%s, LimitPrice=%.2f, VolumeTotalOriginal=%d, Direction=%c.\n",
				__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef, pInputOrder->InstrumentID, pInputOrder->LimitPrice, pInputOrder->VolumeTotalOriginal, pInputOrder->Direction);
			lock_guard<mutex> g(orderStatus_mtx);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pInputOrder->OrderRef));
			if (o != nullptr) {
				o->orderStatus = OS_Error;		
				//sendOrderStatus(o->serverOrderId);
				//sendGeneralMessage(string("CTP Trade Server OnRspOrderInsert:") +
					//SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
			}
			else {
				PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]ctp Trade server OnRspOrderInsert cant find order : OrderRef=%s\n",
					__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
			}
		}
		else
		{
			lock_guard<mutex> g(orderStatus_mtx);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pInputOrder->OrderRef));
			if (o != nullptr) {
				o->orderStatus = OS_Error;			// rejected ?
				//sendOrderStatus(o->serverOrderId);
				//sendGeneralMessage(string("CTP Trader Server OnRspOrderInsert error:") +
				//	SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
			}
			else {
				PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]tp broker server OnRspOrderInsert cant find order : OrderRef=%s\n",
					__FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
			}			
		}
	}
	///报单操作请求响应(参数不通过)	// 撤单错误（柜台）
	void CtpTDEngine::OnRspOrderAction(CThostFtdcInputOrderActionField *pInputOrderAction, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult)
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnRspOrderAction failed: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspOrderAction: OrderRef=%s, InstrumentID=%s, ActionFlag=%c.\n",
				__FILE__, __LINE__, __FUNCTION__, pInputOrderAction->OrderRef, pInputOrderAction->InstrumentID, pInputOrderAction->ActionFlag);
		}
		else
		{
			cout<<"OnRspOrderAction error = 0"<<endl;
			//sendGeneralMessage(to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
		}
	}
	///请求查询投资者持仓响应
	// TODO: 针对上期所持仓的今昨分条返回（有昨仓、无今仓），读取昨仓数据
	// TODO: 汇总总仓, 计算持仓均价, 读取冻结
	void CtpTDEngine::OnRspQryInvestorPosition(CThostFtdcInvestorPositionField *pInvestorPosition, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult){
			if(pInvestorPosition == nullptr){
				cout<<"qry pos return nullptr"<<endl;
				return;
			}
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspQryInvestorPosition, InstrumentID=%s, InvestorID=%s, OpenAmount=%f, OpenVolume=%d, PosiDirection=%c, PositionProfit=%.2f, PositionCost=%.2f, UseMargin=%.2f, LongFrozen=%d, ShortFrozen=%d, TradingDay=%s, YdPosition=%d, last=%d\n",
				__FILE__, __LINE__, __FUNCTION__, pInvestorPosition->InstrumentID, pInvestorPosition->InvestorID, pInvestorPosition->OpenAmount, pInvestorPosition->OpenVolume,
				pInvestorPosition->PosiDirection, pInvestorPosition->PositionProfit, pInvestorPosition->PositionCost, pInvestorPosition->UseMargin,
				pInvestorPosition->LongFrozen, pInvestorPosition->ShortFrozen, pInvestorPosition->TradingDay, pInvestorPosition->YdPosition, bIsLast);
			if ((pInvestorPosition->Position != 0.0) && (pInvestorPosition->YdPosition != 0.0)){
				Position pos;
				pos._posNo = to_string(pInvestorPosition->SettlementID);
				pos._type = 'a';
				pos._fullsymbol = CConfig::instance().CtpSymbolToSecurityFullName(pInvestorPosition->InstrumentID);
				pos._size = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? 1 : -1) * pInvestorPosition->Position;
				pos._avgprice = pInvestorPosition->PositionCost / pInvestorPosition->Position;
				pos._openpl = pInvestorPosition->PositionProfit;
				pos._closedpl = pInvestorPosition->CloseProfit;
				pos._account = ctpacc_.id;
				pos._pre_size = pInvestorPosition->YdPosition;
				pos._freezed_size = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? pInvestorPosition->LongFrozen : pInvestorPosition->ShortFrozen);
				pos._api = name_;
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
				cout<<"Ctp TD send postion msg:"<<msg<<endl;
				lock_guard<mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msg);
			}
		}
		else
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			cout<<"Ctp Td Qry pos error "<<pRspInfo->ErrorID<<":"<<errormsgutf8<<endl;
		}
	}
	///请求查询资金账户响应 
	void CtpTDEngine::OnRspQryTradingAccount(CThostFtdcTradingAccountField *pTradingAccount, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult){
			if(pTradingAccount == nullptr){
				cout<<"Ctp Td qry acc return nullptr"<<endl;
				return;
			}
			double balance = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
				+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
				+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp broker server OnRspQryTradingAccount: AccountID=%s, Available=%.2f, PreBalance=%.2f, Deposit=%.2f, Withdraw=%.2f, WithdrawQuota=%.2f, Commission=%.2f, CurrMargin=%.2f, FrozenMargin=%.2f, CloseProfit=%.2f, PositionProfit=%.2f, balance=%.2f.\n",
				__FILE__, __LINE__, __FUNCTION__, pTradingAccount->AccountID, pTradingAccount->Available, pTradingAccount->PreBalance,
				pTradingAccount->Deposit, pTradingAccount->Withdraw, pTradingAccount->WithdrawQuota, pTradingAccount->Commission,
				pTradingAccount->CurrMargin, pTradingAccount->FrozenMargin, pTradingAccount->CloseProfit, pTradingAccount->PositionProfit, balance);
			AccountInfo accinfo;	
			accinfo.AccountID = pTradingAccount->AccountID;
			accinfo.PreviousDayEquityWithLoanValue = pTradingAccount->PreBalance;
			accinfo.NetLiquidation = balance;
			accinfo.AvailableFunds = pTradingAccount->Available;
			accinfo.Commission = pTradingAccount->Commission;
			accinfo.FullMaintainanceMargin = pTradingAccount->CurrMargin;
			accinfo.RealizedPnL = pTradingAccount->CloseProfit;
			accinfo.UnrealizedPnL = pTradingAccount->PositionProfit;
			PortfolioManager::instance().accinfomap_[ctpacc_.id] = accinfo;
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
			cout<<"Ctp Td send account fund msg "<<msg<<endl;
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
		else {
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			cout<<"Ctp Td Qry Acc error "<<':'<<errormsgutf8<<endl;
		}
	}
	///请求查询合约响应
	void CtpTDEngine::OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		// pInstrument->StrikePrice; pInstrument->EndDelivDate; pInstrument->IsTrading;
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			cout<<"Ctp Td Qry Instrument error "<<':'<<errormsgutf8<<endl;
		}
		else{
			if(pInstrument == nullptr){
				cout<<"Ctp Td qry Instrument return nullptr"<<endl;
				return;
			}
			PRINT_TO_FILE("INFO:[%s,%d][%s]Ctp Td OnRspQryInstrument: InstrumentID=%s, InstrumentName=%s, ExchangeID=%s, ExchangeInstID=%s, VolumeMultiple=%d, PriceTick=%.2f, UnderlyingInstrID=%s, ProductClass=%c, ExpireDate=%s, LongMarginRatio=%.2f.\n",
				__FILE__, __LINE__, __FUNCTION__, pInstrument->InstrumentID, pInstrument->InstrumentName, pInstrument->ExchangeID, pInstrument->ExchangeInstID,
				pInstrument->VolumeMultiple, pInstrument->PriceTick, pInstrument->UnderlyingInstrID, pInstrument->ProductClass, pInstrument->ExpireDate, pInstrument->LongMarginRatio);
			string symbol = boost::to_upper_copy(string(pInstrument->InstrumentName));
			auto it = DataManager::instance().securityDetails_.find(symbol);
			if (it == DataManager::instance().securityDetails_.end()) {
				Security s;
				s.symbol = pInstrument->InstrumentName;
				s.exchange = pInstrument->ExchangeID;
				s.securityType = "F";
				s.multiplier = pInstrument->VolumeMultiple;
				//s.localName = pInstrument->InstrumentName;
				s.ticksize = std::to_string(pInstrument->PriceTick);
				DataManager::instance().securityDetails_[symbol] = s;
			}
			string msg = "0"
				+ SERIALIZATION_SEPARATOR + name_
				+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RSP_CONTRACT)
				+ SERIALIZATION_SEPARATOR + pInstrument->InstrumentName
				+ SERIALIZATION_SEPARATOR + std::to_string(pInstrument->PriceTick)
				+ SERIALIZATION_SEPARATOR + to_string(pInstrument->VolumeMultiple);
			cout << "Ctp td send contract msg:"<<msg<<endl;
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
	}
	///错误应答
	void CtpTDEngine::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if(pRspInfo == nullptr)
			return;
		string errormsgutf8;
		errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
		PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp td server OnRspError: ErrorID=%d, ErrorMsg=%s.\n",
			__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
//		sendGeneralMessage(string("CTP Trader Server OnRspError") +
//			SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR + errormsgutf8);
	}
	///报单通知
	void CtpTDEngine::OnRtnOrder(CThostFtdcOrderField *pOrder) {
		if(pOrder == nullptr){
			cout<<"Ctp td onRtnOrder return nullptr"<<endl;
			return;
		}
		// pOrder->ExchangeID		交易所编号 
		// pOrder->InstrumentID		合约代码
		// pOrder->OrderRef			报单引用
		// pOrder->Direction		买卖方向
		// pOrder->CombOffsetFlag	组合开平标志
		// pOrder->LimitPrice		价格
		// pOrder->VolumeTotalOriginal		数量
		// pOrder->VolumeTraded		今成交数量
		// pOrder->VolumeTotal		剩余数量
		// Order->OrderSysID		报单编号（交易所的）
		// pOrder->OrderStatus		报单状态
		// pOrder->InsertDate		报单日期
		// pOrder->SequenceNo		序号
		PRINT_TO_FILE("INFO:[%s,%d][%s]CTP trade server OnRtnOrder details: InstrumentID=%s, OrderRef=%s, ExchangeID=%s, InsertTime=%s, CancelTime=%s, FrontID=%d, SessionID=%d, Direction=%c, CombOffsetFlag=%s, OrderStatus=%c, OrderSubmitStatus=%c, StatusMsg=%s, LimitPrice=%f, VolumeTotalOriginal=%d, VolumeTraded=%d, OrderSysID=%s, SequenceNo=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, pOrder->InstrumentID, pOrder->OrderRef, pOrder->ExchangeID, pOrder->InsertTime, pOrder->CancelTime,
			pOrder->FrontID, pOrder->SessionID, pOrder->Direction, pOrder->CombOffsetFlag, pOrder->OrderStatus, pOrder->OrderSubmitStatus, GBKToUTF8(pOrder->StatusMsg).c_str(),
			pOrder->LimitPrice, pOrder->VolumeTotalOriginal, pOrder->VolumeTraded, pOrder->OrderSysID, pOrder->SequenceNo);	// TODO: diff between tradeid and orderref
		cout<<"CTP trade server OnRtnOrder Status msg: "<<GBKToUTF8(pOrder->StatusMsg)<<endl;
		long nOrderref = std::stol(pOrder->OrderRef);
		shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(nOrderref);
		if (o == nullptr) {			// create an order
			PRINT_TO_FILE_AND_CONSOLE("Warning:[%s,%d][%s]Ctp return an untracted order", __FILE__, __LINE__, __FUNCTION__);
			lock_guard<mutex> g(oid_mtx);
			std::shared_ptr<Order> o = make_shared<Order>();
			o->account = ctpacc_.id;
			o->api = "others";
			o->fullSymbol = CConfig::instance().CtpSymbolToSecurityFullName(pOrder->InstrumentID);
			o->orderSize = (pOrder->Direction == '0'? 1 : -1) * pOrder->VolumeTotalOriginal;
			o->limitPrice = pOrder->LimitPrice;
			o->stopPrice = 0.0;
			o->orderStatus = CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			o->orderFlag = CtpComboOffsetFlagToOrderFlag(pOrder->CombOffsetFlag[0]);
			o->orderNo = pOrder->OrderSysID;
			o->serverOrderId = m_serverOrderId++;
			o->createTime = ymdhmsf();
			o->orderType = OrderType::OT_Limit;					// assumed
			OrderManager::instance().trackOrder(o);
			string msg = o->serialize() 
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
			cout<<"Ctp td send orderestatus msg:"<<msg<<endl;
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
		else {
			o->orderStatus = CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			o->orderFlag = CtpComboOffsetFlagToOrderFlag(pOrder->CombOffsetFlag[0]);
			o->orderNo = pOrder->OrderSysID;
			string msg = o->serialize() 
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
			cout<<"Ctp td send orderestatus msg:"<<msg<<endl;
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}		
	}
	/// 成交通知
	void CtpTDEngine::OnRtnTrade(CThostFtdcTradeField *pTrade) {
		if(pTrade == nullptr){
			cout<<"Ctp td onRtnTrade return nullptr"<<endl;
			return;
		}
		PRINT_TO_FILE("INFO:[%s,%d][%s]CTP trade server OnRtnTrade details: TradeID=%s, OrderRef=%s, InstrumentID=%s, ExchangeID=%s, TradeTime=%s, OffsetFlag=%c, Direction=%c, Price=%f, Volume=%d.\n",
			__FILE__, __LINE__, __FUNCTION__, pTrade->TradeID, pTrade->OrderRef, pTrade->InstrumentID, pTrade->ExchangeID, pTrade->TradeTime,
			pTrade->OffsetFlag, pTrade->Direction, pTrade->Price, pTrade->Volume);		// TODO: diff between tradeid and orderref
		Fill t;
		t.fullSymbol = CConfig::instance().CtpSymbolToSecurityFullName(pTrade->InstrumentID);
		t.tradetime = pTrade->TradeTime;
		t.serverOrderId = std::stoi(pTrade->OrderRef);
		t.orderNo = pTrade->OrderSysID;
		//t.tradeId = std::stoi(pTrade->TraderID);
		t.tradeNo = pTrade->TradeID;
		t.tradePrice = pTrade->Price;
		t.tradeSize = (pTrade->Direction == THOST_FTDC_D_Buy ? 1 : -1)*pTrade->Volume;
		t.fillflag = CtpComboOffsetFlagToOrderFlag(pTrade->OffsetFlag);
		auto o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pTrade->OrderRef));
		if (o != nullptr) {
			t.clientOrderId = o->clientOrderId;
			t.brokerOrderId = o->brokerOrderId;
			t.account = o->account;
			t.clientId = o->clientId;
			t.source = o->source;
			t.api = o->api;
			o->fillNo = t.tradeNo;
			OrderManager::instance().gotFill(t);
			// sendOrderStatus(o->serverOrderId);
			string msg = t.serialize()
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
			cout<<"Ctp td send fill msg:"<<msg<<endl;
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
		else {
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]fill order id is not tracked. OrderId= %s\n", __FILE__, __LINE__, __FUNCTION__, pTrade->OrderRef);
			t.clientId = o->clientId;
			t.api = "others";
			t.account = ctpacc_.id;
			string msg = t.serialize()
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
			cout<<"Ctp td send fill msg:"<<msg<<endl;
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}		
	}
	///报单录入错误回报
	void CtpTDEngine::OnErrRtnOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			if (pInputOrder == nullptr){
				cout<< "ctp td OnErrRtnOrderInsert return nullptr"<<endl;
				return;
			}
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp broker server OnErrRtnOrderInsert: ErrorID=%d, ErrorMsg=%s, OrderRef=%s, InstrumentID=%s, ExchangeID=%s, Direction=%c, CombOffsetFlag=%s, LimitPrice=%f, VolumeTotalOriginal=%d.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str(),
				pInputOrder->OrderRef, pInputOrder->InstrumentID, pInputOrder->ExchangeID,
				pInputOrder->Direction, pInputOrder->CombOffsetFlag, pInputOrder->LimitPrice, pInputOrder->VolumeTotalOriginal);
			lock_guard<mutex> g(orderStatus_mtx);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pInputOrder->OrderRef));
			if (o != nullptr) {
				o->orderStatus = OS_Error;			// rejected
				string msg = o->serialize() 
					+ SERIALIZATION_SEPARATOR + ymdhmsf();
				cout<<"Ctp td return order insert error: "<<msg<<endl;
				lock_guard<mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msg);
			}
			else {
				PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]order id is not tracked. OrderId= %s\n", __FILE__, __LINE__, __FUNCTION__, pInputOrder->OrderRef);
			}
		}
		else{
			cout<<"ctp td OnErrRtnOrderInsert return no error"<<endl;
		}		
	}

	///撤单操作错误回报,TODO:考虑撤单的信息反馈给client，目前只是返回日志
	void CtpTDEngine::OnErrRtnOrderAction(CThostFtdcOrderActionField *pOrderAction, CThostFtdcRspInfoField *pRspInfo) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			PRINT_TO_FILE("ERROR:[%s,%d][%s]Ctp td OnErrRtnOrderAction: ErrorID=%d, ErrorMsg=%s.\n",
				__FILE__, __LINE__, __FUNCTION__, pRspInfo->ErrorID, errormsgutf8.c_str());
			string msg = "0"
				+ SERIALIZATION_SEPARATOR + name_
				+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE_INFO)
				+ SERIALIZATION_SEPARATOR + "CTP Trader Server OnErrRtnOrderAction"
				+ SERIALIZATION_SEPARATOR + to_string(pRspInfo->ErrorID)
				+ SERIALIZATION_SEPARATOR + errormsgutf8
				+ SERIALIZATION_SEPARATOR + ymdhmsf();
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
		else{
			cout<<"ctp td OnErrRtnOrderAction return no error"<<endl;
		}
	}
	////////////////////////////////////////////////////// end callback/incoming function ///////////////////////////////////////

	OrderStatus CtpTDEngine::CtpOrderStatusToOrderStatus(const char status) {
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

	OrderFlag CtpTDEngine::CtpComboOffsetFlagToOrderFlag(const char flag) {
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

	char CtpTDEngine::OrderFlagToCtpComboOffsetFlag(const OrderFlag flag) {
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