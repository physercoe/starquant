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
		if (estate_ != STOP)
			stop();
		if (api_ != nullptr){
			this->api_->RegisterSpi(nullptr);
			this->api_->Release();// api must init() or will segfault
			this->api_ = nullptr;
		}		
	}

	void CtpTDEngine::init(){
		// if (IEngine::msgq_send_ == nullptr){
		// 	IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		// }
		if(logger == nullptr){
			logger = SQLogger::getLogger("TDEngine.CTP");
		}
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
		}
		name_ = "CTP_TD";
		ctpacc_ = CConfig::instance()._apimap["CTP"];
		string path = CConfig::instance().logDir() + "/ctp/td";
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);
		this->api_ = CThostFtdcTraderApi::CreateFtdcTraderApi(path.c_str());
		this->api_->RegisterSpi(this);
		if (ctpacc_.auth_code == "NA") {
			needauthentication_ = false;
		}
		else {
			needauthentication_ = true;
		}
		THOST_TE_RESUME_TYPE privatetype = THOST_TERT_QUICK;// THOST_TERT_RESTART，THOST_TERT_RESUME, THOST_TERT_QUICK
		THOST_TE_RESUME_TYPE publictype = THOST_TERT_QUICK;// THOST_TERT_RESTART，THOST_TERT_RESUME, THOST_TERT_QUICK
		string ctp_td_address = ctpacc_.td_ip + ":" + to_string(ctpacc_.td_port);			
		this->api_->SubscribePrivateTopic(privatetype);
		this->api_->SubscribePublicTopic(publictype);
		this->api_->RegisterFront((char*)ctp_td_address.c_str());
		this->api_->Init();
		estate_ = CONNECTING;
		LOG_DEBUG(logger,"CTP TD inited");
	}
	void CtpTDEngine::stop(){
		int tmp = disconnect();
		estate_  = EState::STOP;
		LOG_DEBUG(logger,"CTP TD stoped");	

	}

	void CtpTDEngine::start(){
		while(estate_ != EState::STOP){
			string msgin = msgq_recv_->recmsg(0);
			if (msgin.empty())
				continue;
			MSG_TYPE msgintype = MsgType(msgin);
			vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);			
			if (v[0] != name_) //filter message according to its destination
				continue;
			LOG_DEBUG(logger,"CTP TD recv msg:"<<msgin );
			bool tmp;
			switch (msgintype)
			{
				case MSG_TYPE_ENGINE_CONNECT:
					if (connect()){
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_INFO_ENGINE_TDCONNECTED);
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_ENGINE_DISCONNECT:
					tmp = disconnect();
					break;
				case MSG_TYPE_ORDER:
					if (estate_ == LOGIN_ACK){
						insertOrder(v);
					}
					else{
						LOG_DEBUG(logger,"CTP_TD is not connected,can not insert order!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "ctp td is not connected,can not insert order";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_CANCEL_ORDER:
					if (estate_ == LOGIN_ACK){
						cancelOrder(v);
					}
					else{
						LOG_DEBUG(logger,"CTP_TD is not connected,can not cancel order!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "ctp td is not connected,can not cancel order";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_QRY_POS:
					if (estate_ == LOGIN_ACK){
						queryPosition(v[1]);//TODO:区分不同来源，回报中添加目的地信息
					}
					else{
						LOG_DEBUG(logger,"CTP_TD is not connected,can not qry pos!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "ctp td is not connected,can not qry pos";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_QRY_ACCOUNT:
					if (estate_ == LOGIN_ACK){
						queryAccount(v[1]);
					}
					else{
						LOG_DEBUG(logger,"CTP_TD is not connected,can not qry acc!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "ctp td is not connected,can not qry acc";
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
						LOG_DEBUG(logger,"CTP_TD return test msg!");
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
		while (estate_ != LOGIN_ACK && estate_ != STOP){
			switch (estate_){
				case DISCONNECTED:
					// this->api_->SubscribePrivateTopic(privatetype);
					// this->api_->SubscribePublicTopic(publictype);
					// this->api_->RegisterFront((char*)ctp_td_address.c_str());
					// this->api_->Init();
					// //this->api_->Join();
					// estate_ = CONNECTING;
					// LOG_INFO(logger,"CTP_TD register Front!");
					// count++;
					break;
				case CONNECTING:
					msleep(100);
					break;
				case CONNECT_ACK:
					if(needauthentication_){
						LOG_INFO(logger,"CTP_TD authenticating ...");
						CThostFtdcReqAuthenticateField authField;
						strcpy(authField.UserID, ctpacc_.userid.c_str());
						strcpy(authField.BrokerID, ctpacc_.brokerid.c_str());
						strcpy(authField.AuthCode, ctpacc_.auth_code.c_str());
						strcpy(authField.UserProductInfo, ctpacc_.productinfo.c_str());
						error = this->api_->ReqAuthenticate(&authField, reqId_++);
						count++;
						estate_ = AUTHENTICATING;
						if (error != 0){
							LOG_ERROR(logger,"Ctp td  authenticate  error");
							estate_ = CONNECT_ACK;
							msleep(1000);
						}
					}
					else{
						estate_ = AUTHENTICATE_ACK;
					}
					break;
				case AUTHENTICATING:
					msleep(100);
					break;
				case AUTHENTICATE_ACK:
					LOG_INFO(logger,"Ctp td logining ...");
					strcpy(loginField.BrokerID, ctpacc_.brokerid.c_str());
					strcpy(loginField.UserID, ctpacc_.userid.c_str());
					strcpy(loginField.Password, ctpacc_.password.c_str());
					error = this->api_->ReqUserLogin(&loginField, reqId_++);
					count++;
					estate_ = EState::LOGINING;
					if (error != 0){
						LOG_ERROR(logger,"Ctp TD login error:"<<error);
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
				LOG_ERROR(logger,"too many tries fails, give up connecting");
				//estate_ = EState::DISCONNECTED;
				return false;
			}			
		}
		return true;
	}

	bool CtpTDEngine::disconnect(){
		if(estate_ == LOGIN_ACK){
			LOG_INFO(logger,"Ctp Td logouting ..");
			CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();
			strcpy(logoutField.BrokerID, ctpacc_.brokerid.c_str());
			strcpy(logoutField.UserID, ctpacc_.userid.c_str());
			int error = this->api_->ReqUserLogout(&logoutField, reqId_++);
			estate_ = EState::LOGOUTING;
			if (error != 0){
				LOG_ERROR(logger,"ctp td logout error:"<<error);//TODO: send error msg to client
				return false;
			}
			return true;
		}
		else{
			LOG_DEBUG(logger,"ctp td is not connected(logined), cannot disconnect!");
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

		o->api = name_;// = name_;	
		o->source = stoi(v[1]);
		o->clientId = stoi(v[1]);
		o->account = ctpacc_.userid;
		o->clientOrderId = stol(v[4]);
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
		LOG_INFO(logger,"Insert Order: clientorderid ="<<o->clientOrderId<<"fullsymbol = "<<o->fullSymbol);
		lock_guard<mutex> gs(orderStatus_mtx);
		int i = api_->ReqOrderInsert(&orderfield, reqId_++);
		o->orderStatus = OrderStatus::OS_Submitted;
		if (i != 0){
			o->orderStatus = OrderStatus::OS_Error;
			//send error msg
			string msgout = v[1]+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
				+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
				+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
				+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
				+ to_string(i) + SERIALIZATION_SEPARATOR
				+ "ReqOrderinsert return != 0";
			lock_guard<std::mutex> ge(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp TD order insert error: "<<i);
		}
		//send OrderStatus
		lock_guard<std::mutex> ge(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(o->serialize());
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
				string msgout = v[1]+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_CANCELORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ to_string(i) + SERIALIZATION_SEPARATOR
					+ "cancelorder return != 0";
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"Ctp TD cancle order error "<<i);
				return;
			}
			// send cancel info through orderstatus
			lock_guard<mutex> g2(orderStatus_mtx);
			o->orderStatus = OrderStatus::OS_PendingCancel;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(o->serialize());
		}
		else{
			string msgout = v[1]+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
				+ v[1] + SERIALIZATION_SEPARATOR 
				+ v[3];
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"cancel order ordermanager cannot find order!");
		}

	}
	
	void CtpTDEngine::cancelOrder(long oid,const string& source) {
		LOG_INFO(logger,"Cancel Order serverorderid = "<<oid);		
		CThostFtdcInputOrderActionField myreq = CThostFtdcInputOrderActionField();
		std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
		if (o != nullptr){
			string ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(o->fullSymbol);
			strcpy(myreq.InstrumentID, ctpsym.c_str());
			//strcpy(myreq.ExchangeID, o->.c_str());
			strcpy(myreq.OrderRef, to_string(o->serverOrderId).c_str());
			myreq.FrontID = frontID_;
			myreq.SessionID = sessionID_;
			myreq.ActionFlag = THOST_FTDC_AF_Delete;
			strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
			strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
			int i = this->api_->ReqOrderAction(&myreq, reqId_++);
			if (i != 0){
				string msgout = source + SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_CANCELORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ to_string(i) + SERIALIZATION_SEPARATOR
					+ "cancelorder return != 0";
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"Ctp TD cancle order error "<<i);
				return;
			}
			lock_guard<mutex> g2(orderStatus_mtx);
			o->orderStatus = OrderStatus::OS_PendingCancel;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(o->serialize());
		}
		else{
			string msgout = source + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
				+ source + SERIALIZATION_SEPARATOR 
				+ to_string(oid);
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Cancel Order ordermanager cannot find order!");
		}
	}

	void CtpTDEngine::cancelOrders(const string& symbol,const string& source) {		
	}

	// 查询账户
	void CtpTDEngine::queryAccount(const string& source) {
		CThostFtdcQryTradingAccountField myreq = CThostFtdcQryTradingAccountField();
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		int error = api_->ReqQryTradingAccount(&myreq, reqId_++);
		LOG_INFO(logger,"Ctp Td requests account information");			
		if (error != 0){
			string msgout = source + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_QRY_ACC );
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp td qry acc error "<<error);
		}
	}

	void CtpTDEngine::queryOrder(const string& msgorder_,const string& source){
	}

	/// 查询pos
	void CtpTDEngine::queryPosition(const string& source) {
		CThostFtdcQryInvestorPositionField myreq = CThostFtdcQryInvestorPositionField();
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		int error = this->api_->ReqQryInvestorPosition(&myreq, reqId_++);
		LOG_INFO(logger,"Ctp td requests positions");		
		if (error != 0){
			string msgout = source + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_QRY_POS );
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp td qry pos error "<<error);
		}
	}
	////////////////////////////////////////////////////// begin callback/incoming function ///////////////////////////////////////
	///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
	void CtpTDEngine::OnFrontConnected() {
		LOG_INFO(logger,"Ctp Td frontend connected");
		estate_ = CONNECT_ACK;
		reqId_ = 0;
	}

	void CtpTDEngine::OnFrontDisconnected(int nReason) {
		string msgout = "0"+ SERIALIZATION_SEPARATOR 
			+ name_ + SERIALIZATION_SEPARATOR 
			+ to_string(MSG_TYPE_INFO_ENGINE_TDDISCONNECTED);
		lock_guard<std::mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msgout);
		LOG_INFO(logger,"Ctp td disconnected, nReason="<<nReason);
		estate_ = DISCONNECTED;

	}
	///心跳超时警告。当长时间未收到报文时，该方法被调用。
	void CtpTDEngine::OnHeartBeatWarning(int nTimeLapse) {
		string msgout = "0"+ SERIALIZATION_SEPARATOR 
			+ name_ + SERIALIZATION_SEPARATOR 
			+ to_string(MSG_TYPE_INFO_HEARTBEAT_WARNING);
		lock_guard<std::mutex> g(IEngine::sendlock_);
		IEngine::msgq_send_->sendmsg(msgout);
		LOG_INFO(logger,"Ctp td heartbeat overtime error, nTimeLapse="<<nTimeLapse);
	}
	///客户端认证响应
	void CtpTDEngine::OnRspAuthenticate(CThostFtdcRspAuthenticateField *pRspAuthenticateField, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_CONNECT) ;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp Td authentication failed.");
		}
		else{
			estate_ = AUTHENTICATE_ACK;
			LOG_INFO(logger,"Ctp TD authenticated.");			
		}
	}
	/// 登录请求响应
	void CtpTDEngine::OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0)
		{
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_CONNECT) ;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			LOG_ERROR(logger,"Ctp td login failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8);  
		}
		else{
			frontID_ = pRspUserLogin->FrontID;
			sessionID_ = pRspUserLogin->SessionID;
			LOG_INFO(logger,"Ctp Td server user logged in,"
							<<"TradingDay="<<pRspUserLogin->TradingDay
							<<" LoginTime="<<pRspUserLogin->LoginTime
							<<" frontID="<<pRspUserLogin->FrontID
							<<" sessionID="<<pRspUserLogin->SessionID
							<<" MaxOrderRef="<<pRspUserLogin->MaxOrderRef
			);
			if(needsettlementconfirm_ && !issettleconfirmed_){
				// 投资者结算结果确认
				CThostFtdcSettlementInfoConfirmField myreq = CThostFtdcSettlementInfoConfirmField();
				strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
				strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
				int error = api_->ReqSettlementInfoConfirm(&myreq, reqId_++);
				if (error != 0){
					string msgout = "0"+ SERIALIZATION_SEPARATOR 
						+ name_ + SERIALIZATION_SEPARATOR 
						+ to_string(MSG_TYPE_ERROR_CONNECT) ;
					lock_guard<std::mutex> g(IEngine::sendlock_);
					IEngine::msgq_send_->sendmsg(msgout);
					LOG_ERROR(logger,"Ctp TD settlement confirming error");
				}
				LOG_INFO(logger,"Ctp TD settlement confirming...");
			}
			else{
				estate_ = LOGIN_ACK;
			}

		}
	}
	///投资者结算结果确认响应
	void CtpTDEngine::OnRspSettlementInfoConfirm(CThostFtdcSettlementInfoConfirmField *pSettlementInfoConfirm, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_CONNECT) ;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			LOG_ERROR(logger,"Settlement confirm error: "<<"ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8); 
		}
		else{
			estate_ = LOGIN_ACK;
			issettleconfirmed_ = true;
			LOG_INFO(logger,"Ctp td Settlement confirmed.ConfirmDate="<<pSettlementInfoConfirm->ConfirmDate<<"ConfirmTime="<<pSettlementInfoConfirm->ConfirmTime);
		}
	}
	///登出请求响应
	void CtpTDEngine::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
 		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_DISCONNECT) ;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);			 
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			LOG_ERROR(logger,"Ctp td logout failed: "<<"ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8); 
		}
		else{
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_INFO_ENGINE_TDDISCONNECTED) ;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);	
			estate_ = CONNECT_ACK;
			LOG_INFO(logger,"Ctp Td Logout,BrokerID="<<pUserLogout->BrokerID<<" UserID="<<pUserLogout->UserID);
		}
	}

	///报单录入请求响应(参数不通过)
	void CtpTDEngine::OnRspOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult)
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pInputOrder->OrderRef));
			if (o != nullptr) {
				lock_guard<mutex> g(orderStatus_mtx);
				o->orderStatus = OS_Error;	
				string msgout = to_string(o->source)+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR
					+ errormsgutf8;
				lock_guard<std::mutex> g2(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);  //send error msg
				IEngine::msgq_send_->sendmsg(o->serialize());	//send order status		
			}
			else {//not record this order yet
				string msgout = "0"+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
					+ "0"  + SERIALIZATION_SEPARATOR 
					+ pInputOrder->OrderRef;
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"onRspOrder Insert, OrderManager cannot find order,OrderRef="<<pInputOrder->OrderRef);
			}
			LOG_ERROR(logger,"Ctp Td OnRspOrderInsert: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8
				<<"[OrderRef="<<pInputOrder->OrderRef
				<<"InstrumentID="<<pInputOrder->InstrumentID
				<<"LimitPrice="<<pInputOrder->LimitPrice
				<<"VolumeTotalOriginal="<<pInputOrder->VolumeTotalOriginal
				<<"Direction="<<pInputOrder->Direction<<"]"
			);
		}
		else //unknown yet, can this happen?
		{
		}
	}
	///报单操作请求响应(参数不通过)	// 撤单错误（柜台）
	void CtpTDEngine::OnRspOrderAction(CThostFtdcInputOrderActionField *pInputOrderAction, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult)
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			long oid = std::stol(pInputOrderAction->OrderRef);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
			if (o != nullptr) {
				string msgout = to_string(o->source) + SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_CANCELORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR
					+ errormsgutf8;
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"Ctp TD OnRsp cancel order error:"<<pRspInfo->ErrorID<<errormsgutf8);
			}
			else
			{
				string msgout = "0"+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
					+ "0"  + SERIALIZATION_SEPARATOR 
					+ pInputOrderAction->OrderRef;
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"OnRspOrderAction OrderManager cannot find order,OrderRef="<<pInputOrderAction->OrderRef);
			}
			LOG_ERROR(logger,"Ctp Td OnRspOrderAction: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8
				<<"[OrderRef="<<pInputOrderAction->OrderRef
				<<"InstrumentID="<<pInputOrderAction->InstrumentID
				<<"ActionFlag="<<pInputOrderAction->ActionFlag<<"]"
			);
		}
		else
		{
		}
	}
	///请求查询投资者持仓响应
	// TODO: 针对上期所持仓的今昨分条返回（有昨仓、无今仓），读取昨仓数据
	// TODO: 汇总总仓, 计算持仓均价, 读取冻结
	void CtpTDEngine::OnRspQryInvestorPosition(CThostFtdcInvestorPositionField *pInvestorPosition, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult){
			if(pInvestorPosition == nullptr){
				LOG_INFO(logger,"ctp on qry pos return nullptr");
				return;
			}
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
				LOG_DEBUG(logger,"Ctp TD send postion msg:"<<msg);
				lock_guard<mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msg);
			}
			LOG_INFO(logger,"Ctp broker server OnRspQryInvestorPosition:"
				<<"InstrumentID="<<pInvestorPosition->InstrumentID
				<<"InvestorID="<<pInvestorPosition->InvestorID
				<<"OpenAmount="<<pInvestorPosition->OpenAmount
				<<"OpenVolume="<<pInvestorPosition->OpenVolume
				<<"PosiDirection="<<pInvestorPosition->PosiDirection
				<<"PositionProfit="<<pInvestorPosition->PositionProfit
				<<"PositionCost="<<pInvestorPosition->PositionCost
				<<"UseMargin="<<pInvestorPosition->UseMargin
				<<"LongFrozen="<<pInvestorPosition->LongFrozen
				<<"ShortFrozen="<<pInvestorPosition->ShortFrozen
				<<"TradingDay="<<pInvestorPosition->TradingDay
				<<"YdPosition="<<pInvestorPosition->YdPosition
				<<"islast="<<bIsLast		
			);			
		}
		else
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string msgout = "0" + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_QRY_POS);
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp Td Qry pos error, errorID="<<pRspInfo->ErrorID<<" ErrorMsg:"<<errormsgutf8);
		}
	}
	///请求查询资金账户响应 
	void CtpTDEngine::OnRspQryTradingAccount(CThostFtdcTradingAccountField *pTradingAccount, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult){
			if(pTradingAccount == nullptr){
				LOG_INFO(logger,"Ctp Td qry acc return nullptr");
				return;
			}
			double balance = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
				+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
				+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;
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
			LOG_DEBUG(logger,"Ctp Td send account fund msg "<<msg);
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
			LOG_INFO(logger,"Ctp td OnRspQryTradingAccount:"
				<<"AccountID="<<pTradingAccount->AccountID
				<<"Available="<<pTradingAccount->Available
				<<"PreBalance="<<pTradingAccount->PreBalance
				<<"Deposit="<<pTradingAccount->Deposit
				<<"Withdraw="<<pTradingAccount->Withdraw
				<<"WithdrawQuota="<<pTradingAccount->WithdrawQuota
				<<"Commission="<<pTradingAccount->Commission
				<<"CurrMargin="<<pTradingAccount->CurrMargin
				<<"FrozenMargin="<<pTradingAccount->FrozenMargin
				<<"CloseProfit="<<pTradingAccount->CloseProfit
				<<"PositionProfit="<<pTradingAccount->PositionProfit
				<<"Balance="<<balance
			);
		}
		else {			
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string msgout = "0" + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_QRY_ACC );
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp Td Qry Acc error:"<<errormsgutf8);
		}
	}
	///请求查询合约响应
	void CtpTDEngine::OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		// pInstrument->StrikePrice; pInstrument->EndDelivDate; pInstrument->IsTrading;
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string msgout = "0" + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_QRY_CONTRACT );
			lock_guard<std::mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Ctp Td Qry Instrument error:"<<errormsgutf8);
		}
		else{
			if(pInstrument == nullptr){
				LOG_INFO(logger,"Ctp Td qry Instrument return nullptr");
				return;
			}
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
			LOG_DEBUG(logger,"Ctp td send contract msg:"<<msg);
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
						LOG_INFO(logger,"Ctp Td OnRspQryInstrument:"
				<<"InstrumentID="<<pInstrument->InstrumentID
				<<"InstrumentName="<<pInstrument->InstrumentName
				<<"ExchangeID="<<pInstrument->ExchangeID
				<<"ExchangeInstID="<<pInstrument->ExchangeInstID
				<<"PriceTick="<<pInstrument->PriceTick
				<<"VolumeMultiple="<<pInstrument->VolumeMultiple
				<<"UnderlyingInstrID="<<pInstrument->UnderlyingInstrID
				<<"ProductClass="<<pInstrument->ProductClass
				<<"ExpireDate="<<pInstrument->ExpireDate
				<<"LongMarginRatio="<<pInstrument->LongMarginRatio
			);
		}
	}
	///错误应答
	void CtpTDEngine::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string msgout = "0" + SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR
				+ to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR
				+ errormsgutf8;
			lock_guard<std::mutex> g(IEngine::sendlock_);
			LOG_ERROR(logger,"Ctp td server OnRspError: ErrorID="<<pRspInfo->ErrorID <<"ErrorMsg="<<errormsgutf8);
		}
	}
	///报单通知
	void CtpTDEngine::OnRtnOrder(CThostFtdcOrderField *pOrder) {
		if(pOrder == nullptr){
			LOG_INFO(logger,"Ctp td onRtnOrder return nullptr");
			return;
		}
		long nOrderref = std::stol(pOrder->OrderRef);
		shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(nOrderref);
		if (o == nullptr) {			// create an order
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
			string msg = o->serialize() ;
			lock_guard<mutex> g2(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);			
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
				+ "0"  + SERIALIZATION_SEPARATOR 
				+ pOrder->OrderRef;
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"OnRtnOrder OrderManager cannot find orderref:"<<pOrder->OrderRef);	
			LOG_DEBUG(logger,"Ctp td send orderestatus msg:"<<msg);
		}
		else {
			o->orderStatus = CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			o->orderFlag = CtpComboOffsetFlagToOrderFlag(pOrder->CombOffsetFlag[0]);
			o->orderNo = pOrder->OrderSysID;
			string msg = o->serialize() ;
			LOG_DEBUG(logger,"Ctp td send orderestatus msg:"<<msg);	
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);

		}
		LOG_INFO(logger,"CTP trade server OnRtnOrder details:"
			<<"InstrumentID="<<pOrder->InstrumentID
			<<"OrderRef="<<pOrder->OrderRef
			<<"ExchangeID="<<pOrder->ExchangeID
			<<"InsertTime="<<pOrder->InsertTime
			<<"CancelTime="<<pOrder->CancelTime
			<<"FrontID="<<pOrder->FrontID
			<<"SessionID="<<pOrder->SessionID
			<<"Direction="<<pOrder->Direction
			<<"CombOffsetFlag="<<pOrder->CombOffsetFlag
			<<"OrderStatus="<<pOrder->OrderStatus
			<<"OrderSubmitStatus="<<pOrder->OrderSubmitStatus
			<<"StatusMsg="<<GBKToUTF8(pOrder->StatusMsg)
			<<"LimitPrice="<<pOrder->LimitPrice
			<<"VolumeTotalOriginal="<<pOrder->VolumeTotalOriginal
			<<"VolumeTraded="<<pOrder->VolumeTraded
			<<"OrderSysID="<<pOrder->OrderSysID
			<<"SequenceNo="<<pOrder->SequenceNo
		);		
	}
	/// 成交通知
	void CtpTDEngine::OnRtnTrade(CThostFtdcTradeField *pTrade) {
		if(pTrade == nullptr){
			LOG_INFO(logger,"Ctp td onRtnTrade return nullptr");
			return;
		}
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
			string msg = t.serialize();
			LOG_DEBUG(logger,"Ctp td send fill msg:"<<msg);
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
		}
		else {
			t.api = "others";
			t.account = ctpacc_.id;
			string msg = t.serialize();
			lock_guard<mutex> g(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msg);
			string msgout = "0"+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
				+ "0"  + SERIALIZATION_SEPARATOR 
				+ pTrade->OrderRef;
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_DEBUG(logger,"Ctp td send fill msg:"<<msg);
			LOG_ERROR(logger,"OnRtnTrade ordermanager cannot find orderref"<<pTrade->OrderRef);
		}	
		LOG_INFO(logger,"CTP trade server OnRtnTrade details:"
			<<"TradeID="<<pTrade->TradeID
			<<"OrderRef="<<pTrade->OrderRef
			<<"InstrumentID="<<pTrade->InstrumentID
			<<"ExchangeID="<<pTrade->ExchangeID
			<<"TradeTime="<<pTrade->TradeTime
			<<"OffsetFlag="<<pTrade->OffsetFlag
			<<"Direction="<<pTrade->Direction
			<<"Price="<<pTrade->Price
			<<"Volume="<<pTrade->Volume
		);	
	}
	///交易所报单录入错误回报
	void CtpTDEngine::OnErrRtnOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			if (pInputOrder == nullptr){
				LOG_INFO(logger,"ctp td OnErrRtnOrderInsert return nullptr");
				return;
			}			
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pInputOrder->OrderRef));
			if (o != nullptr) {
				lock_guard<mutex> g(orderStatus_mtx);
				o->orderStatus = OS_Error;			// rejected
				string msg = o->serialize();
				lock_guard<mutex> g2(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msg);  //send orderstatus
				string msgout = to_string(o->source)+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR
					+ errormsgutf8;
				IEngine::msgq_send_->sendmsg(msgout); //send error_insert order msg
				LOG_DEBUG(logger,"Ctp td send order insert error: "<<msg);
			}
			else {
				string msgout = "0"+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
					+ "0"  + SERIALIZATION_SEPARATOR 
					+ pInputOrder->OrderRef;
				lock_guard<mutex> g(IEngine::sendlock_);	
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"OnErrRtnOrderInsert ordermanager cannot find orderref:"<<pInputOrder->OrderRef);
			}
			LOG_ERROR(logger,"CTP td OnErrRtnOrderinsert:"
				<<"ErrorMsg:"<<errormsgutf8
				<<"InstrumentID="<<pInputOrder->InstrumentID
				<<"OrderRef="<<pInputOrder->OrderRef
				<<"ExchangeID="<<pInputOrder->ExchangeID
				<<"Direction="<<pInputOrder->Direction
				<<"CombOffsetFlag="<<pInputOrder->CombOffsetFlag
				<<"LimitPrice="<<pInputOrder->LimitPrice
				<<"VolumeTotalOriginal="<<pInputOrder->VolumeTotalOriginal
			);
		}
		else{
			//cout<<"ctp td OnErrRtnOrderInsert return no error"<<endl;
		}		
	}

	///交易所撤单操作错误回报
	void CtpTDEngine::OnErrRtnOrderAction(CThostFtdcOrderActionField *pOrderAction, CThostFtdcRspInfoField *pRspInfo) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			long oid = std::stol(pOrderAction->OrderRef);
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
			if (o != nullptr) {
				string msgout = to_string(o->source) + SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_CANCELORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ to_string(pRspInfo->ErrorID) + SERIALIZATION_SEPARATOR
					+ errormsgutf8;
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
			}
			else
			{
				string msgout = "0"+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_ORGANORDER ) + SERIALIZATION_SEPARATOR
					+ "0"  + SERIALIZATION_SEPARATOR 
					+ pOrderAction->OrderRef;
				lock_guard<std::mutex> g(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"OnErrRtnOrderAction OrderManager cannot find order,OrderRef="<<pOrderAction->OrderRef);
			}
			LOG_ERROR(logger,"Ctp td OnErrRtnOrderAction: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8);
		}
		else{
			//cout<<"ctp td OnErrRtnOrderAction return no error"<<endl;
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