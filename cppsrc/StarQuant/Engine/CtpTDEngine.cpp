#include <mutex>
#include <boost/locale.hpp>
#include <boost/algorithm/algorithm.hpp>

#include <Common/datastruct.h>
#include <Common/logger.h>
#include <Common/util.h>
#include <Common/msgq.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
#include <Data/datamanager.h>
#include <Engine/CtpTDEngine.h>

using namespace std;
namespace StarQuant
{
	//extern std::atomic<bool> gShutdown;

	CtpTDEngine::CtpTDEngine(const string& acc) 
		: needauthentication_(false)
		, needsettlementconfirm_(true)
		, issettleconfirmed_(false)
		, m_brokerOrderId_(0)
		, reqId_(0)
		, orderRef_(0)
		, frontID_(0)
		, sessionID_(0)
		, apiinited_(false)
		, inconnectaction_(false)
		, autoconnect_(false)
		, autoqry_(false)
		, timercount_(0)
	{
		name_ = string("CTP") + DESTINATION_SEPARATOR + "TD" + DESTINATION_SEPARATOR + acc;
		init();
	}

	CtpTDEngine::~CtpTDEngine() {
		if (estate_ != STOP)
			stop();
		releaseapi();
	}

	void CtpTDEngine::releaseapi(){	
		if (api_ != nullptr){
			this->api_->RegisterSpi(nullptr);
			if (apiinited_)
				this->api_->Release();// api must init() or will segfault
			this->api_ = nullptr;
		}		
	}

	void CtpTDEngine::reset(){
		disconnect();
		releaseapi();
		CConfig::instance().readConfig();
		init();	
		LOG_DEBUG(logger,name_ <<" reset");	
	}	

	void CtpTDEngine::init(){
		if(logger == nullptr){
			logger = SQLogger::getLogger("TDEngine.CTP");
		}
		if (messenger_ == nullptr){
			messenger_ = std::make_unique<CMsgqEMessenger>(name_, CConfig::instance().SERVERSUB_URL);	
			msleep(100);
		}
		string acc = accAddress(name_);	
		ctpacc_ = CConfig::instance()._accmap[acc];
		string path = CConfig::instance().logDir() + "/ctp/td/" + acc;
		boost::filesystem::path dir(path.c_str());
		boost::filesystem::create_directory(dir);
		this->api_ = CThostFtdcTraderApi::CreateFtdcTraderApi(path.c_str());
		this->api_->RegisterSpi(this);
		if (ctpacc_.auth_code == "NA" || ctpacc_.auth_code.empty() ) {
			needauthentication_ = false;
		}
		else {
			needauthentication_ = true;
		}
		estate_ = DISCONNECTED;
		auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
		messenger_->send(pmsgs);
		apiinited_ = false;
		autoconnect_ = CConfig::instance().autoconnect;
		autoqry_ = CConfig::instance().autoqry;
		LOG_DEBUG(logger, name_ <<" inited, api version:"<<this->api_->GetApiVersion());
	}
	void CtpTDEngine::stop(){
		int tmp = disconnect();
		estate_  = EState::STOP;
		auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
		messenger_->send(pmsgs);
		LOG_DEBUG(logger, name_ <<" stoped");	

	}

	void CtpTDEngine::start(){
		while(estate_ != EState::STOP){
			auto pmsgin = messenger_->recv(1);
			bool processmsg = ((pmsgin != nullptr) && ( startwith(pmsgin->destination_,DESTINATION_ALL) || (pmsgin->destination_ == name_ )));
			// if (pmsgin == nullptr || (pmsgin->destination_ != name_  && ! startwith(pmsgin->destination_,DESTINATION_ALL) ) )
			// 	continue;
			if (processmsg){
				switch (pmsgin->msgtype_)
				{
					case MSG_TYPE_ENGINE_CONNECT:
						if (connect()){
							auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
								MSG_TYPE_INFO_ENGINE_TDCONNECTED, name_ + "logined,ready to request.");
							messenger_->send(pmsgout,1);
						}
						break;
					case MSG_TYPE_ENGINE_DISCONNECT:
						disconnect();
						break;
					case MSG_TYPE_ORDER_CTP:
						if (pmsgin->destination_ != name_)
							break;
						if (estate_ == LOGIN_ACK){
							insertOrder(static_pointer_cast<CtpOrderMsg>(pmsgin));
						}
						else{
							LOG_DEBUG(logger,name_ <<" is not connected,can not insert order!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								name_+ " is not connected,can not insert order!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_CANCEL_ORDER:
					case MSG_TYPE_ORDER_ACTION:
					case MSG_TYPE_ORDER_ACTION_CTP:
						if (pmsgin->destination_ != name_)
							break;				
						if (estate_ == LOGIN_ACK){
							cancelOrder(static_pointer_cast<OrderActionMsg>(pmsgin));
						}
						else{
							LOG_DEBUG(logger,name_ <<" is not connected,can not cancel order!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								name_ + " is not connected,can not cancel order!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_QRY_POS:
						if (pmsgin->destination_ != name_)
							break;				
						if (estate_ == LOGIN_ACK){
							queryPosition(pmsgin);
						}
						else{
							LOG_DEBUG(logger,name_ <<" is not connected,can not qry pos!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								name_ + " is not connected,can not qry pos!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_QRY_ACCOUNT:
						if (pmsgin->destination_ != name_)
							break;				
						if (estate_ == LOGIN_ACK){
							queryAccount(pmsgin);
						}
						else{
							LOG_DEBUG(logger,name_ <<" is not connected,can not qry acc!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								name_ + " is not connected,can not qry acc!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_QRY_CONTRACT:
						if (pmsgin->destination_ != name_)
							break;				
						if (estate_ == LOGIN_ACK){
							queryContract(static_pointer_cast<QryContractMsg>(pmsgin));
						}
						else{
							LOG_DEBUG(logger,name_ <<" is not connected,can not qry contract!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								name_ + " is not connected,can not qry contract!");
							messenger_->send(pmsgout);
						}
						break;				
					case MSG_TYPE_ENGINE_STATUS:
						{
							auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
								MSG_TYPE_INFO_ENGINE_STATUS,
								to_string(estate_));
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_TEST:
						{						
							auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
								MSG_TYPE_TEST,
								"test");
							messenger_->send(pmsgout);
							LOG_DEBUG(logger,name_ <<" return test msg!");
						}
						break;
					case MSG_TYPE_SWITCH_TRADING_DAY:
						switchday();
						break;	
					case MSG_TYPE_ENGINE_RESET:
						reset();
						break;
					case MSG_TYPE_TIMER:
						timertask();
						break;											
					default:
						processbuf();
						break;
				}
			}
			else{
				processbuf();
			}

		}
	}

	bool CtpTDEngine::connect(){
		inconnectaction_ = true;
		THOST_TE_RESUME_TYPE privatetype = THOST_TERT_QUICK;// THOST_TERT_RESTART，THOST_TERT_RESUME, THOST_TERT_QUICK
		THOST_TE_RESUME_TYPE publictype = THOST_TERT_QUICK;// THOST_TERT_RESTART，THOST_TERT_RESUME, THOST_TERT_QUICK
		int error;
		int count = 0;// count numbers of tries, two many tries ends
		string ctp_td_address = ctpacc_.td_ip + ":" + to_string(ctpacc_.td_port);	
		CThostFtdcReqUserLoginField loginField = CThostFtdcReqUserLoginField();
		while (estate_ != LOGIN_ACK && estate_ != STOP){
			switch (estate_){
				case DISCONNECTED:
					if (!apiinited_){
						this->api_->SubscribePrivateTopic(privatetype);
						this->api_->SubscribePublicTopic(publictype);
						this->api_->RegisterFront((char*)ctp_td_address.c_str());
						this->api_->Init();	
						apiinited_ = true;					
					}
					estate_ = CONNECTING;
					{auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
					messenger_->send(pmsgs);}
					LOG_INFO(logger,name_ <<" api inited, connect Front!");
					count++;
					break;
				case CONNECTING:
					msleep(1000);
					count++;
					break;
				case CONNECT_ACK:
					if(needauthentication_){
						CThostFtdcReqAuthenticateField authField;
						strcpy(authField.UserID, ctpacc_.userid.c_str());
						strcpy(authField.BrokerID, ctpacc_.brokerid.c_str());
						strcpy(authField.AuthCode, ctpacc_.auth_code.c_str());
						strcpy(authField.UserProductInfo,ctpacc_.productinfo.c_str());
						strcpy(authField.AppID, ctpacc_.appid.c_str());
						LOG_INFO(logger,name_ <<" authenticating :"
							<<authField.UserID<<"|"
							<<authField.BrokerID<<"|"
							<<authField.AuthCode<<"|"
							<<authField.AppID<<".");
						error = this->api_->ReqAuthenticate(&authField, reqId_++);
						count++;
						estate_ = AUTHENTICATING;
						if (error != 0){
							LOG_ERROR(logger,name_ <<" authenticate  error");
							estate_ = CONNECT_ACK;
							msleep(1000);
						}
					}
					else{
						estate_ = AUTHENTICATE_ACK;
					}
					{auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
					messenger_->send(pmsgs);}
					break;
				case AUTHENTICATING:
					msleep(100);
					break;
				case AUTHENTICATE_ACK:
					LOG_INFO(logger,name_ <<" logining ...");
					strcpy(loginField.BrokerID, ctpacc_.brokerid.c_str());
					strcpy(loginField.UserID, ctpacc_.userid.c_str());
					strcpy(loginField.Password, ctpacc_.password.c_str());
					strcpy(loginField.UserProductInfo, ctpacc_.productinfo.c_str());
					error = this->api_->ReqUserLogin(&loginField, reqId_++);
					// cout<< loginField.BrokerID <<loginField.UserID <<loginField.Password;
					count++;
					estate_ = EState::LOGINING;					
					if (error != 0){
						LOG_ERROR(logger,name_ <<" login error:"<<error);
						estate_ = EState::AUTHENTICATE_ACK;
						msleep(1000);
					}
					{auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
								MSG_TYPE_INFO_ENGINE_STATUS,
								to_string(estate_));
					messenger_->send(pmsgs);}
					break;
				case LOGINING:
					count++;
					msleep(500);
					break;
				default:
					break;
			}
			if(count > 20){
				LOG_ERROR(logger,name_ <<" too many tries fails, give up connecting");
				//estate_ = EState::DISCONNECTED;
				inconnectaction_ = false;
				return false;
			}			
		}
		inconnectaction_ = false;
		return true;
	}

	bool CtpTDEngine::disconnect(){
		inconnectaction_ = true;
		if(estate_ == LOGIN_ACK){
			LOG_INFO(logger,name_ <<" logouting ..");
			CThostFtdcUserLogoutField logoutField = CThostFtdcUserLogoutField();
			strcpy(logoutField.BrokerID, ctpacc_.brokerid.c_str());
			strcpy(logoutField.UserID, ctpacc_.userid.c_str());
			int error = this->api_->ReqUserLogout(&logoutField, reqId_++);
			estate_ = EState::LOGOUTING;
			if (error != 0){
				LOG_ERROR(logger,name_ <<" logout error:"<<error);//TODO: send error msg to client
				return false;
			}
			return true;
		}
		else{
			LOG_DEBUG(logger,name_ <<" is not connected(logined), cannot disconnect!");
			return false;
		}

	}

	void CtpTDEngine::switchday(){
		issettleconfirmed_ = false;
		LOG_DEBUG(logger,name_ <<" switch day reset settleconfirmed!");
	}

	void CtpTDEngine::timertask(){
		timercount_++;
		// // send status every second 
		// auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
		// 	MSG_TYPE_ENGINE_STATUS,
		// 	to_string(estate_));
		// messenger_->send(pmsgout);

		//auto qyr pos and acc
		if (estate_ == LOGIN_ACK && autoqry_ ){
			if (timercount_ %2 == 0){
				auto pmsgout = make_shared<MsgHeader>(name_,name_,MSG_TYPE_QRY_ACCOUNT);
				queryAccount(pmsgout);
			}
			else{
				auto pmsgout = make_shared<MsgHeader>(name_,name_,MSG_TYPE_QRY_POS);
				queryPosition(pmsgout);
			}
		}

	}

	void CtpTDEngine::processbuf(){
		// reserverd for future use,such as local condition order, algo-trading etc.
	}


	void CtpTDEngine::insertOrder(shared_ptr<CtpOrderMsg> pmsg){
		strcpy(pmsg->data_.orderField_.OrderRef, to_string(orderRef_++).c_str());
		strcpy(pmsg->data_.orderField_.InvestorID, ctpacc_.userid.c_str());
		strcpy(pmsg->data_.orderField_.UserID, ctpacc_.userid.c_str());
		strcpy(pmsg->data_.orderField_.BrokerID, ctpacc_.brokerid.c_str());
		int error = api_->ReqOrderInsert(&(pmsg->data_.orderField_), reqId_++);
		lock_guard<mutex> gs(orderStatus_mtx);
		pmsg->data_.orderStatus_ = OrderStatus::OS_Submitted;
		lock_guard<mutex> g(oid_mtx);
		pmsg->data_.serverOrderID_ = m_serverOrderId++;
		pmsg->data_.brokerOrderID_ = m_brokerOrderId_++;
		pmsg->data_.localNo_ = to_string(frontID_) + "-" + to_string(sessionID_) + "-" + to_string(orderRef_) ;
		pmsg->data_.createTime_ = ymdhmsf();			
		pmsg->data_.fullSymbol_ = CConfig::instance().CtpSymbolToSecurityFullName(pmsg->data_.orderField_.InstrumentID);
		pmsg->data_.price_ = pmsg->data_.orderField_.LimitPrice;
		int dir_ = pmsg->data_.orderField_.Direction != THOST_FTDC_D_Sell ? 1:-1 ;
		pmsg->data_.quantity_ = dir_ * pmsg->data_.orderField_.VolumeTotalOriginal;
		pmsg->data_.flag_ = CtpComboOffsetFlagToOrderFlag(pmsg->data_.orderField_.CombOffsetFlag[0]);
		pmsg->data_.tag_ = pmsg->data_.tag_ 
			+ "h" + pmsg->data_.orderField_.CombHedgeFlag
			+ "p" + pmsg->data_.orderField_.OrderPriceType
			+ "c" + pmsg->data_.orderField_.ContingentCondition + "-" + to_string(pmsg->data_.orderField_.StopPrice)
			+ "t" + pmsg->data_.orderField_.TimeCondition
			+ "v" + pmsg->data_.orderField_.VolumeCondition;
		LOG_INFO(logger, name_<<"Insert Order: clientorderid ="<<pmsg->data_.clientOrderID_<<" FullSymbol = "<<pmsg->data_.fullSymbol_);				
		std::shared_ptr<Order> o = pmsg->toPOrder();
		OrderManager::instance().trackOrder(o);		
		if (error != 0){
			o->orderStatus_ = OrderStatus::OS_Error;
			pmsg->data_.orderStatus_ = OrderStatus::OS_Error;
			//send error msg
			auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				MSG_TYPE_ERROR_INSERTORDER,
				to_string(o->clientOrderID_));
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_<<" insertOrder error: "<<error);
		}
		//send OrderStatus
		auto pmsgout = make_shared<OrderStatusMsg>(pmsg->source_,name_);
		pmsgout->set(o);
		messenger_->send(pmsgout);

		//CThostFtdcInputOrderField orderfield = {}
		//memcpy(&orderfield,&pmsg->orderField_,sizeof(CThostFtdcInputOrderField));
		//CThostFtdcInputOrderField();

		// string ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(pmsg->data_.fullSymbol_);
		// strcpy(orderfield.InstrumentID, ctpsym.c_str());
		// orderfield.VolumeTotalOriginal = std::abs(pmsg->data_.orderSize_);
		// orderfield.OrderPriceType = pmsg->data_.orderType_ == OrderType::OT_Market ? THOST_FTDC_OPT_AnyPrice : THOST_FTDC_OPT_LimitPrice;
		// orderfield.LimitPrice = pmsg->data_.orderType_ == OrderType::OT_Market ? 0.0 : pmsg->data_.limitPrice_;
		// orderfield.Direction = pmsg->data_.orderSize_ > 0 ? THOST_FTDC_D_Buy : THOST_FTDC_D_Sell;
		// orderfield.CombOffsetFlag[0] = OrderFlagToCtpComboOffsetFlag(pmsg->data_.orderFlag_);
		// strcpy(orderfield.OrderRef, to_string(pmsg->data_.serverOrderID_).c_str());
		// strcpy(orderfield.InvestorID, ctpacc_.userid.c_str());
		// strcpy(orderfield.UserID, ctpacc_.userid.c_str());
		// strcpy(orderfield.BrokerID, ctpacc_.brokerid.c_str());
		// orderfield.CombHedgeFlag[0] = THOST_FTDC_HF_Speculation;			// 投机单
		// orderfield.ContingentCondition = THOST_FTDC_CC_Immediately;		// 立即发单
		// orderfield.ForceCloseReason = THOST_FTDC_FCC_NotForceClose;		// 非强平
		// orderfield.IsAutoSuspend = 0;									// 非自动挂起
		// orderfield.UserForceClose = 0;									// 非用户强平
		// orderfield.TimeCondition = THOST_FTDC_TC_GFD;					// 今日有效
		// orderfield.VolumeCondition = THOST_FTDC_VC_AV;					// 任意成交量
		// orderfield.MinVolume = 1;										// 最小成交量为1
		// // TODO: 判断FAK和FOK
		// //orderfield.OrderPriceType = THOST_FTDC_OPT_LimitPrice;
		// //orderfield.TimeCondition = THOST_FTDC_TC_IOC;
		// //orderfield.VolumeCondition = THOST_FTDC_VC_CV;				// FAK; FOK uses THOST_FTDC_VC_AV



	}

	void CtpTDEngine::cancelOrder(shared_ptr<OrderActionMsg> pmsg){
		CThostFtdcInputOrderActionField myreq = CThostFtdcInputOrderActionField();
		string oref;
		int ofront;
		int osess;
		long coid = pmsg->data_.clientOrderID_;
		string ctpsym;
		std::shared_ptr<Order> o;
		if (pmsg->data_.serverOrderID_ < 0){
			o = OrderManager::instance().retrieveOrderFromSourceAndClientOrderId(pmsg->data_.clientID_, pmsg->data_.clientOrderID_);
		}
		else
		{
			o = OrderManager::instance().retrieveOrderFromServerOrderId(pmsg->data_.serverOrderID_);
		}
		if (o != nullptr){
			vector<string> locno = stringsplit(o->localNo_,'-');
			ofront = stoi(locno[0]);
			osess = stoi(locno[1]);
			oref = locno[2];
			ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(o->fullSymbol_);
		}
		else
		{
			auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				MSG_TYPE_ERROR_ORGANORDER,
				to_string(o->clientOrderID_));
			messenger_->send(pmsgout);
			LOG_ERROR(logger,"cancel order ordermanager cannot find order!");
			return;
		}		
		strcpy(myreq.InstrumentID, ctpsym.c_str());
		//strcpy(myreq.ExchangeID, o->.c_str());			// TODO: check the required field
		strcpy(myreq.OrderRef, oref.c_str());
		myreq.FrontID = ofront;
		myreq.SessionID = osess;
		myreq.ActionFlag = THOST_FTDC_AF_Delete;
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		myreq.OrderActionRef = m_brokerOrderId_++;
		int i = this->api_->ReqOrderAction(&myreq, reqId_++);
		if (i != 0){
			auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				MSG_TYPE_ERROR_CANCELORDER,
				to_string(o->clientOrderID_));
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_<<" cancle order error "<<i);
			return;
		}
		lock_guard<mutex> g2(orderStatus_mtx);
		o->orderStatus_ = OrderStatus::OS_PendingCancel;
		o->updateTime_ = ymdhmsf();
		auto pmsgout = make_shared<OrderStatusMsg>(pmsg->source_,name_);
		pmsgout->set(o);
		messenger_->send(pmsgout);

	}
	
	// 查询账户
	void CtpTDEngine::queryAccount(shared_ptr<MsgHeader> pmsg) {
		CThostFtdcQryTradingAccountField myreq = CThostFtdcQryTradingAccountField();
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		int error = api_->ReqQryTradingAccount(&myreq, reqId_++);
		LOG_INFO(logger,name_ <<" requests account information");			
		if (error != 0){
			auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				MSG_TYPE_ERROR_QRY_ACC,
				"Ctp td qry acc error");
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_ <<" qry acc error "<<error);
		}
	}
	/// 查询pos
	void CtpTDEngine::queryPosition(shared_ptr<MsgHeader> pmsg) {
		CThostFtdcQryInvestorPositionField myreq = CThostFtdcQryInvestorPositionField();
		strcpy(myreq.InvestorID, ctpacc_.userid.c_str());
		strcpy(myreq.BrokerID, ctpacc_.brokerid.c_str());
		int error = this->api_->ReqQryInvestorPosition(&myreq, reqId_++);
		LOG_INFO(logger,name_ <<" requests positions");		
		if (error != 0){
			auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				MSG_TYPE_ERROR_QRY_POS,
				"Ctp td qry pos error");
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_ <<" qry pos error "<<error);
		}
	}


	void CtpTDEngine::queryContract(shared_ptr<QryContractMsg> pmsg){
		CThostFtdcQryInstrumentField req = {0};
		string ctpsym = pmsg->data_;
		if (pmsg->symtype_ == ST_Full) 
			ctpsym = CConfig::instance().SecurityFullNameToCtpSymbol(pmsg->data_);
		strcpy(req.InstrumentID, ctpsym.c_str());
		int error = this->api_->ReqQryInstrument(&req,reqId_++);
		if (error != 0){
			auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				MSG_TYPE_ERROR_QRY_CONTRACT,
				"Ctp td qry contract error");
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_ <<" qry pos contract "<<error);
		}
	}	
	////////////////////////////////////////////////////// begin callback/incoming function ///////////////////////////////////////
	///当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
	void CtpTDEngine::OnFrontConnected() {
		LOG_INFO(logger,name_ <<" front connected.");
		estate_ = CONNECT_ACK;
		reqId_ = 0;
		auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
		messenger_->send(pmsgs);
		//autologin
		if (autoconnect_ && !inconnectaction_ ){
			std::shared_ptr<InfoMsg> pmsg = make_shared<InfoMsg>(name_,name_,MSG_TYPE_ENGINE_CONNECT,name_ + "front connected.");
			CMsgqRMessenger::Send(pmsg);
		}
			
	}

	void CtpTDEngine::OnFrontDisconnected(int nReason) {
		estate_ = CONNECTING;
		reqId_ ++;
		// every 1 min login once
		if (reqId_ % 4000 == 0){
			auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
			messenger_->send(pmsgs);
			reqId_ = 1;
			string sout("Ctp td disconnected, nReason=");
			sout += to_string(nReason);
			auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_INFO_ENGINE_TDDISCONNECTED,
				sout);
			messenger_->send(pmsgout);
			LOG_INFO(logger, name_ <<" disconnected, nReason="<<nReason);
		}
	}
	///心跳超时警告。当长时间未收到报文时，该方法被调用。
	void CtpTDEngine::OnHeartBeatWarning(int nTimeLapse) {
		string sout("Ctp td heartbeat overtime error, nTimeLapse=");
		sout += to_string(nTimeLapse);
		auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
			MSG_TYPE_INFO_HEARTBEAT_WARNING,
			sout);
		messenger_->send(pmsgout);		
		LOG_INFO(logger,name_ <<" heartbeat overtime error, nTimeLapse="<<nTimeLapse);
	}
	///客户端认证响应
	void CtpTDEngine::OnRspAuthenticate(CThostFtdcRspAuthenticateField *pRspAuthenticateField, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string sout("Ctp Td authentication failed");
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_CONNECT,
				sout);
			messenger_->send(pmsgout);				
			LOG_ERROR(logger,name_ <<" authentication failed."<<pRspInfo->ErrorID<<errormsgutf8);
		}
		else{
			estate_ = AUTHENTICATE_ACK;
			auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
			messenger_->send(pmsgs);
			LOG_INFO(logger,name_ <<" authenticated.");			
		}
	}
	/// 登录请求响应
	void CtpTDEngine::OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0)
		{
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string sout("Ctp td login failed: ErrorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_CONNECT,
				sout);
			messenger_->send(pmsgout);	
			LOG_ERROR(logger,name_ <<" login failed: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8);  
		}
		else{
			frontID_ = pRspUserLogin->FrontID;
			sessionID_ = pRspUserLogin->SessionID;
			orderRef_ = stoi(pRspUserLogin->MaxOrderRef) + 1;
			LOG_INFO(logger,name_ <<" user logged in,"
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
					string sout("Ctp TD settlement confirming error");
					auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_ERROR_CONNECT,
						sout);
					LOG_ERROR(logger,name_ <<" settlement confirming error");
				}
				LOG_INFO(logger,name_ <<" settlement confirming...");
			}
			else{
				estate_ = LOGIN_ACK;
				auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
				messenger_->send(pmsgs);
			}

		}
	}
	///投资者结算结果确认响应
	void CtpTDEngine::OnRspSettlementInfoConfirm(CThostFtdcSettlementInfoConfirmField *pSettlementInfoConfirm, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;			
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			string sout("Ctp TD settlement confirming error, ErrorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_CONNECT,
				sout);	
			LOG_ERROR(logger,name_ <<" Settlement confirm error: "<<"ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8); 
		}
		else{
			estate_ = LOGIN_ACK;
			auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
			messenger_->send(pmsgs);
			issettleconfirmed_ = true;
			LOG_INFO(logger,name_ <<" Settlement confirmed.ConfirmDate="<<pSettlementInfoConfirm->ConfirmDate<<"ConfirmTime="<<pSettlementInfoConfirm->ConfirmTime);
		}
	}
	///登出请求响应
	void CtpTDEngine::OnRspUserLogout(CThostFtdcUserLogoutField *pUserLogout, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
 		if (pRspInfo != nullptr && pRspInfo->ErrorID != 0){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" ); 
			string sout("Ctp td logout failed: ErrorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_CONNECT,
				sout);
			LOG_ERROR(logger,name_ <<" logout failed: "<<"ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8); 
		}
		else{
			string sout("Ctp td logouted");
			auto pmsgout = make_shared<InfoMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_INFO_ENGINE_TDDISCONNECTED,
				sout);
			messenger_->send(pmsgout);
			estate_ = CONNECTING;
			auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_INFO_ENGINE_STATUS,
						to_string(estate_));
			messenger_->send(pmsgs);
			LOG_INFO(logger,name_ <<" Logout,BrokerID="<<pUserLogout->BrokerID<<" UserID="<<pUserLogout->UserID);
		}
	}

	///报单录入请求响应(参数不通过)
	void CtpTDEngine::OnRspOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult)
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string oref = to_string(frontID_) + "-" + to_string(sessionID_) + "-" + pInputOrder->OrderRef;
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromAccAndLocalNo(ctpacc_.id,oref);
			if (o != nullptr) {
				lock_guard<mutex> g(orderStatus_mtx);
				o->orderStatus_ = OS_Error;
				o->updateTime_ = ymdhmsf();	
				auto pmsgout = make_shared<ErrorMsg>(to_string(o->clientID_), name_,
					MSG_TYPE_ERROR_INSERTORDER,
					to_string(o->clientOrderID_));
				messenger_->send(pmsgout);
				auto pmsgout2 = make_shared<OrderStatusMsg>(to_string(o->clientID_),name_);
				pmsgout2->set(o);
				messenger_->send(pmsgout2);
		
			}
			else {//not record this order yet
				auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
					MSG_TYPE_ERROR_ORGANORDER,
					pInputOrder->OrderRef);
				messenger_->send(pmsgout);
				LOG_ERROR(logger,name_ <<" onRspOrder Insert, OrderManager cannot find order,OrderRef="<<pInputOrder->OrderRef);
			}
			LOG_ERROR(logger,name_ <<" OnRspOrderInsert: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8
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
			string localno = to_string(pInputOrderAction->FrontID) + "-" + to_string(pInputOrderAction->SessionID)
				+ "-" + pInputOrderAction->OrderRef;
			//std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromServerOrderId(oid);
			auto o = OrderManager::instance().retrieveOrderFromAccAndLocalNo(ctpacc_.id,localno);
			if (o != nullptr) {
				auto pmsgout = make_shared<ErrorMsg>(to_string(o->clientID_), name_,
					MSG_TYPE_ERROR_CANCELORDER,
					to_string(o->clientOrderID_));
				messenger_->send(pmsgout);
				LOG_ERROR(logger,name_ <<" OnRsp cancel order error:"<<pRspInfo->ErrorID<<errormsgutf8);
			}
			else
			{
				auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
					MSG_TYPE_ERROR_ORGANORDER,
					localno);
				messenger_->send(pmsgout);
				LOG_ERROR(logger,name_ <<" OnRspOrderAction OrderManager cannot find order,localNo="<<localno);
			}
			LOG_ERROR(logger,name_ <<" OnRspOrderAction: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8
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
	void CtpTDEngine::OnRspQryInvestorPosition(CThostFtdcInvestorPositionField *pInvestorPosition, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult){
			if(pInvestorPosition == nullptr){
				LOG_DEBUG(logger,name_ <<" onRspQrypos return nullptr.");
				return;
			}			
			string fullsym = CConfig::instance().CtpSymbolToSecurityFullName(pInvestorPosition->InstrumentID);
			string exchid = stringsplit(fullsym,' ')[0];
			string key = ctpacc_.userid + "." + fullsym + "." + pInvestorPosition->PosiDirection;
			
			// auto pos = PortfolioManager::instance().retrievePosition(key);
			std::shared_ptr<Position> pos;
			if (posbuffer_.find(key) == posbuffer_.end() ){
				pos = std::make_shared<Position>();
				pos->key_ = key;
				pos->account_ = ctpacc_.userid;
				pos->fullSymbol_ = fullsym;
				pos->api_ = name_;
				posbuffer_[key] = pos;
			}else
			{
				pos = posbuffer_[key];
			}
			int dirsign =  pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? 1 : -1;
			if (exchid == "SHFE"){
				if ((pInvestorPosition->YdPosition != 0 ) && (pInvestorPosition->TodayPosition == 0))
					pos->preSize_ = dirsign * pInvestorPosition->Position;
			}else{
				pos->preSize_ = dirsign *(pInvestorPosition->Position - pInvestorPosition->TodayPosition);
			}
			double cost = pos->avgPrice_ * abs(pos->size_);
			pos->size_ += dirsign * pInvestorPosition->Position;
			pos->openpl_ += pInvestorPosition->PositionProfit;
			if (pos->size_ != 0){
				cost += pInvestorPosition->PositionCost;
				pos->avgPrice_ = cost /abs(pos->size_);
			}
			if (pos->size_ > 0){
				pos->freezedSize_ -= pInvestorPosition->ShortFrozen;
			}
			else{
				pos->freezedSize_ += pInvestorPosition->LongFrozen;
			}
			pos->closedpl_ += pInvestorPosition->CloseProfit;
			if (bIsLast){
				auto pmsg = make_shared<PosMsg>(DESTINATION_ALL,name_);
				pmsg->set(pos);				
				messenger_->send(pmsg);
				PortfolioManager::instance().Add(pos);
				posbuffer_.erase(key);
			}
			// if ((pInvestorPosition->Position != 0.0) && (pInvestorPosition->YdPosition != 0.0)){
			// 	auto pmsg = make_shared<PosMsg>();
			// 	pmsg->destination_ = DESTINATION_ALL;
			// 	pmsg->source_ = name_;
			// 	// pmsg->data_.posNo_ = to_string(pInvestorPosition->SettlementID);
			// 	pmsg->data_.type_ = 'a';
			// 	pmsg->data_.fullSymbol_ = CConfig::instance().CtpSymbolToSecurityFullName(pInvestorPosition->InstrumentID);
			// 	pmsg->data_.size_ = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? 1 : -1) * pInvestorPosition->Position;
			// 	pmsg->data_.avgPrice_ = pInvestorPosition->PositionCost / pInvestorPosition->Position;
			// 	pmsg->data_.openpl_ = pInvestorPosition->PositionProfit;
			// 	pmsg->data_.closedpl_ = pInvestorPosition->CloseProfit;
			// 	pmsg->data_.account_ = ctpacc_.userid;
			// 	pmsg->data_.preSize_ = pInvestorPosition->YdPosition;
			// 	pmsg->data_.freezedSize_ = (pInvestorPosition->PosiDirection == THOST_FTDC_PD_Long ? pInvestorPosition->LongFrozen : pInvestorPosition->ShortFrozen);
			// 	pmsg->data_.api_ = "CTP";				
			// 	messenger_->send(pmsg);
			// 	PortfolioManager::instance().Add(pmsg->toPos());
			// }
			LOG_INFO(logger,name_ <<" OnRspQryInvestorPosition:"
				<<" InstrumentID="<<pInvestorPosition->InstrumentID
				<<" InvestorID="<<pInvestorPosition->InvestorID
				<<" Position="<<pInvestorPosition->Position
				<<" OpenAmount="<<pInvestorPosition->OpenAmount
				<<" OpenVolume="<<pInvestorPosition->OpenVolume
				<<" PosiDirection="<<pInvestorPosition->PosiDirection
				<<" PositionProfit="<<pInvestorPosition->PositionProfit
				<<" PositionCost="<<pInvestorPosition->PositionCost
				<<" UseMargin="<<pInvestorPosition->UseMargin
				<<" LongFrozen="<<pInvestorPosition->LongFrozen
				<<" ShortFrozen="<<pInvestorPosition->ShortFrozen
				<<" TradingDay="<<pInvestorPosition->TradingDay
				<<" YdPosition="<<pInvestorPosition->YdPosition
				<<" islast="<<bIsLast		
			);			
		}
		else
		{
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string sout("Ctp Td Qry pos error, errorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;			
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_QRY_POS,
				sout);
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_ <<" Qry pos error, errorID="<<pRspInfo->ErrorID<<" ErrorMsg:"<<errormsgutf8);
		}
	}
	///请求查询资金账户响应 
        // ("BrokerID", c_char * 11),	# 经纪公司代码 
        // ("InvestorID", c_char * 19),	# 投资者代码 
        // ("PreMortgage", c_double),	# 上次质押金额 
        // ("PreCredit", c_double),	# 上次信用额度 
        // ("PreDeposit", c_double),	# 上次存款额 
        // ("preBalance", c_double),	# 上次结算准备金 
        // ("PreMargin", c_double),	# 上次占用的保证金 
        // ("Deposit", c_double),	# 入金金额 
        // ("Withdraw", c_double),	# 出金金额 
        // ("FrozenMargin", c_double),	# 冻结的保证金（报单未成交冻结的保证金） 
        // ("FrozenCash", c_double),	# 冻结的资金（报单未成交冻结的总资金） 
        // ("FrozenCommission", c_double),	# 冻结的手续费（报单未成交冻结的手续费） 
        // ("CurrMargin", c_double),	# 当前保证金总额 
        // ("CashIn", c_double),	# 资金差额 
        // ("Commission", c_double),	# 手续费 
        // ("CloseProfit", c_double),	# 平仓盈亏 
        // ("PositionProfit", c_double),	# 持仓盈亏 
        // ("Balance", c_double),	# 结算准备金 
        // ("Available", c_double),	# 可用资金 
        // ("WithdrawQuota", c_double),	# 可取资金 
        // ("Reserve", c_double),	# 基本准备金 
        // ("TradingDay", c_char * 9),	# 交易日 
        // ("Credit", c_double),	# 信用额度 
        // ("Mortgage", c_double),	# 质押金额 
        // ("ExchangeMargin", c_double),	# 交易所保证金 
        // ("DeliveryMargin", c_double),	# 投资者交割保证金 
        // ("ExchangeDeliveryMargin", c_double),	# 交易所交割保证金 
        // ("ReserveBalance", c_double),	# 保底期货结算准备金 
        // ("Equity", c_double),	# 当日权益 
        // ("MarketValue", c_double),	# 账户市值 	
	void CtpTDEngine::OnRspQryTradingAccount(CThostFtdcTradingAccountField *pTradingAccount, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (!bResult){
			if(pTradingAccount == nullptr){
				LOG_INFO(logger,name_ <<" qry acc return nullptr");
				return;
			}
			double netLiquidation = pTradingAccount->PreBalance - pTradingAccount->PreCredit - pTradingAccount->PreMortgage
				+ pTradingAccount->Mortgage - pTradingAccount->Withdraw + pTradingAccount->Deposit
				+ pTradingAccount->CloseProfit + pTradingAccount->PositionProfit + pTradingAccount->CashIn - pTradingAccount->Commission;
			auto pmsg = make_shared<AccMsg>();
			pmsg->destination_ = DESTINATION_ALL;
			pmsg->source_ = name_;
			pmsg->data_.accountID_ = pTradingAccount->AccountID;
			pmsg->data_.previousDayEquityWithLoanValue_ = pTradingAccount->PreBalance;
			pmsg->data_.netLiquidation_ = netLiquidation;
			pmsg->data_.availableFunds_ = pTradingAccount->Available;
			pmsg->data_.commission_ = pTradingAccount->Commission;
			pmsg->data_.fullMaintainanceMargin_ = pTradingAccount->CurrMargin;
			pmsg->data_.realizedPnL_ = pTradingAccount->CloseProfit;
			pmsg->data_.unrealizedPnL_ = pTradingAccount->PositionProfit;
			pmsg->data_.frozen_ = pTradingAccount->FrozenMargin + pTradingAccount->FrozenCash + pTradingAccount->FrozenCommission;
			pmsg->data_.balance_ = pTradingAccount->Balance;
			messenger_->send(pmsg);
			PortfolioManager::instance().accinfomap_[ctpacc_.userid] = pmsg->data_;
			LOG_INFO(logger,name_ <<" OnRspQryTradingAccount:"
				<<" AccountID="<<pTradingAccount->AccountID
				<<" Available="<<pTradingAccount->Available
				<<" PreBalance="<<pTradingAccount->PreBalance
				<<" Deposit="<<pTradingAccount->Deposit
				<<" Withdraw="<<pTradingAccount->Withdraw
				<<" WithdrawQuota="<<pTradingAccount->WithdrawQuota
				<<" Commission="<<pTradingAccount->Commission
				<<" CurrMargin="<<pTradingAccount->CurrMargin
				<<" FrozenMargin="<<pTradingAccount->FrozenMargin
				<<" CloseProfit="<<pTradingAccount->CloseProfit
				<<" PositionProfit="<<pTradingAccount->PositionProfit
				<<" Balance="<<pTradingAccount->Balance
			);
		}
		else {			
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string sout("Ctp Td Qry acc error, errorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_QRY_ACC,
				sout);
			messenger_->send(pmsgout);
			LOG_ERROR(logger,name_ <<" Qry Acc error:"<<errormsgutf8);
		}

	}
	///请求查询合约响应
	void CtpTDEngine::OnRspQryInstrument(CThostFtdcInstrumentField *pInstrument, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		// pInstrument->StrikePrice; pInstrument->EndDelivDate; pInstrument->IsTrading;
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string sout("Ctp Td Qry Instrument error, errorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_QRY_CONTRACT,
				sout);
			messenger_->send(pmsgout);			
			LOG_ERROR(logger,name_ <<" Qry Instrument error:"<<errormsgutf8);
		}
		else{
			if(pInstrument == nullptr){
				LOG_INFO(logger,name_ <<" qry Instrument return nullptr");
				return;
			}
			auto pmsg = make_shared<SecurityMsg>();
			pmsg->destination_ = DESTINATION_ALL;
			pmsg->source_ = name_;
			pmsg->data_.symbol_ = pInstrument->InstrumentID;			
			pmsg->data_.exchange_ = pInstrument->ExchangeID;
			pmsg->data_.securityType_ = pInstrument->ProductClass ;
			pmsg->data_.multiplier_ = pInstrument->VolumeMultiple;
			pmsg->data_.localName_ = GBKToUTF8(pInstrument->InstrumentName);
			pmsg->data_.ticksize_ = pInstrument->PriceTick;			
			if (pInstrument->ProductClass == THOST_FTDC_PC_Options ){
				pmsg->data_.underlyingSymbol_ = pInstrument->UnderlyingInstrID ;
				pmsg->data_.optionType_ = pInstrument->OptionsType;
				pmsg->data_.strikePrice_ = pInstrument->StrikePrice;
				pmsg->data_.expiryDate_ = pInstrument-> ExpireDate;
			}
			
			messenger_->send(pmsg);
			// string symbol = boost::to_upper_copy(string(pInstrument->InstrumentName));
			
			string symbol = pInstrument->InstrumentID;
			auto it = DataManager::instance().securityDetails_.find(symbol);
			if (it == DataManager::instance().securityDetails_.end()) {
				DataManager::instance().securityDetails_[symbol] = pmsg->data_;
			}			
			LOG_INFO(logger,name_ <<" OnRspQryInstrument:"
				<<" InstrumentID="<<pInstrument->InstrumentID
				<<" InstrumentName="<<GBKToUTF8(pInstrument->InstrumentName)
				<<" ExchangeID="<<pInstrument->ExchangeID
				<<" ExchangeInstID="<<pInstrument->ExchangeInstID
				<<" PriceTick="<<pInstrument->PriceTick
				<<" VolumeMultiple="<<pInstrument->VolumeMultiple
				<<" UnderlyingInstrID="<<pInstrument->UnderlyingInstrID
				<<" ProductClass="<<pInstrument->ProductClass
				<<" ExpireDate="<<pInstrument->ExpireDate
				<<" LongMarginRatio="<<pInstrument->LongMarginRatio
			);
		}
	}
	///错误应答
	void CtpTDEngine::OnRspError(CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if (bResult){
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string sout("Ctp td server OnRspError: ErrorID=");
			sout += to_string(pRspInfo->ErrorID) + "ErrorMsg=" + errormsgutf8;			
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR,
				sout);
			LOG_ERROR(logger,name_ <<" server OnRspError: ErrorID="<<pRspInfo->ErrorID <<"ErrorMsg="<<errormsgutf8);
		}
	}
	///报单通知
	void CtpTDEngine::OnRtnOrder(CThostFtdcOrderField *pOrder) {
		if(pOrder == nullptr){
			LOG_INFO(logger,name_ <<" onRtnOrder return nullptr");
			return;
		}
		string localno = to_string(pOrder->FrontID) + "-" + to_string(pOrder->SessionID) + "-" + pOrder->OrderRef ;
		//long nOrderref = std::stol(pOrder->OrderRef);
		//bool isotherorder = (pOrder->FrontID != frontID_) || (pOrder->SessionID != sessionID_) ; 
		shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromAccAndLocalNo(ctpacc_.id,localno);
		if ( o == nullptr) {			// create an order
			lock_guard<mutex> g(oid_mtx);
			o = make_shared<Order>();
			o->api_ = "UNKNOWN";
			o->account_ = ctpacc_.id;    
			o->fullSymbol_ = CConfig::instance().CtpSymbolToSecurityFullName(pOrder->InstrumentID);
			o->price_ = pOrder->LimitPrice;
			int dir_ = pOrder->Direction != THOST_FTDC_D_Sell ? 1:-1 ;
			o->quantity_ = dir_ * pOrder->VolumeTotalOriginal ;
			o->tradedvol_ = dir_ * pOrder->VolumeTraded ;
			o->flag_ = CtpComboOffsetFlagToOrderFlag(pOrder->CombOffsetFlag[0]);
			o->tag_ = string("") 
				+ "h" + pOrder->CombHedgeFlag
				+ "p" + pOrder->OrderPriceType
				+ "c" + pOrder->ContingentCondition + "-" + to_string(pOrder->StopPrice)
				+ "t" + pOrder->TimeCondition
				+ "v" + pOrder->VolumeCondition;
			o->serverOrderID_ = m_serverOrderId++;
			o->brokerOrderID_ = m_brokerOrderId_++;
			o->orderNo_ = pOrder->OrderSysID;
			o->localNo_ = localno;
			o->createTime_ = string(pOrder->InsertDate) + string(pOrder->InsertTime);
			o->updateTime_ = ymdhmsf();
			o->orderStatus_ =CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			OrderManager::instance().trackOrder(o);
			auto pmsgout = make_shared<OrderStatusMsg>(DESTINATION_ALL,name_);
			pmsgout->set(o);
			messenger_->send(pmsgout);	
			auto pmsgout2 = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_ORGANORDER,
				localno);
			messenger_->send(pmsgout2);
			LOG_ERROR(logger,name_ <<" OnRtnOrder OrderManager cannot find LocalNo:"<<localno);	
		}
		else {
			o->orderStatus_ = CtpOrderStatusToOrderStatus(pOrder->OrderStatus);
			o->orderNo_ = pOrder->OrderSysID;
			o->updateTime_ = ymdhmsf();
			auto pmsgout = make_shared<OrderStatusMsg>(to_string(o->clientID_),name_);
			pmsgout->set(o);
			messenger_->send(pmsgout);
		}
		LOG_INFO(logger,name_ <<" OnRtnOrder details:"
			<<" InstrumentID="<<pOrder->InstrumentID
			<<" OrderRef="<<pOrder->OrderRef
			<<" ExchangeID="<<pOrder->ExchangeID
			<<" InsertTime="<<pOrder->InsertTime
			<<" CancelTime="<<pOrder->CancelTime
			<<" FrontID="<<pOrder->FrontID
			<<" SessionID="<<pOrder->SessionID
			<<" Direction="<<pOrder->Direction
			<<" CombOffsetFlag="<<pOrder->CombOffsetFlag
			<<" OrderStatus="<<pOrder->OrderStatus
			<<" OrderSubmitStatus="<<pOrder->OrderSubmitStatus
			<<" StatusMsg="<<GBKToUTF8(pOrder->StatusMsg)
			<<" LimitPrice="<<pOrder->LimitPrice
			<<" VolumeTotalOriginal="<<pOrder->VolumeTotalOriginal
			<<" VolumeTraded="<<pOrder->VolumeTraded
			<<" OrderSysID="<<pOrder->OrderSysID
			<<" SequenceNo="<<pOrder->SequenceNo
		);		
	}
	/// 成交通知
	void CtpTDEngine::OnRtnTrade(CThostFtdcTradeField *pTrade) {
		if(pTrade == nullptr){
			LOG_INFO(logger,name_ <<" onRtnTrade return nullptr");
			return;
		}
		auto pmsg = make_shared<FillMsg>();
		pmsg->destination_ = DESTINATION_ALL;
		pmsg->source_ = name_;
		pmsg->data_.fullSymbol_ = CConfig::instance().CtpSymbolToSecurityFullName(pTrade->InstrumentID);
		pmsg->data_.tradeTime_ = pTrade->TradeTime;
		//pmsg->data_.serverOrderID_ = std::stol(pTrade->OrderRef);
		pmsg->data_.orderNo_ = pTrade->OrderSysID;
		//pmsg->data_.tradeId = std::stoi(pTrade->TraderID);
		pmsg->data_.tradeNo_ = pTrade->TradeID;
		pmsg->data_.tradePrice_ = pTrade->Price;
		pmsg->data_.tradeSize_ = (pTrade->Direction == THOST_FTDC_D_Buy ? 1 : -1)*pTrade->Volume;
		pmsg->data_.fillFlag_ = CtpComboOffsetFlagToOrderFlag(pTrade->OffsetFlag);
		//auto o = OrderManager::instance().retrieveOrderFromServerOrderId(std::stol(pTrade->OrderRef));

		string localno = to_string(frontID_) + "-" + to_string(sessionID_) + "-" + pTrade->OrderRef;		
		auto o = OrderManager::instance().retrieveOrderFromAccAndLocalNo(ctpacc_.id,localno);
		auto o2 = OrderManager::instance().retrieveOrderFromOrderNo(pTrade->OrderSysID);
		//bool islocalorder = ( (o != nullptr) && !(o2 != nullptr && o2->localNo_ != localno) );
		if (o2 != nullptr) {
			pmsg->data_.serverOrderID_ = o2->serverOrderID_;
			pmsg->data_.clientOrderID_ = o2->clientOrderID_;
			pmsg->data_.brokerOrderID_ = o2->brokerOrderID_;
			pmsg->data_.localNo_ = o2->localNo_;
			pmsg->data_.account_ = o2->account_;
			pmsg->data_.clientID_ = o2->clientID_;
			pmsg->data_.api_ = o2->api_;
			//o->fillNo_ = pTrade->TradeID;
			OrderManager::instance().gotFill(pmsg->data_);
			messenger_->send(pmsg);
			auto pmsgos = make_shared<OrderStatusMsg>(to_string(o2->clientID_),name_);
			pmsgos->set(o2);
			messenger_->send(pmsgos);				
		}
		else if (o != nullptr) {
			pmsg->data_.serverOrderID_ = o->serverOrderID_;
			pmsg->data_.clientOrderID_ = o->clientOrderID_;
			pmsg->data_.brokerOrderID_ = o->brokerOrderID_;
			pmsg->data_.localNo_ = localno;
			pmsg->data_.account_ = o->account_;
			pmsg->data_.clientID_ = o->clientID_;
			pmsg->data_.api_ = o->api_;
			//o->fillNo_ = pTrade->TradeID;
			OrderManager::instance().gotFill(pmsg->data_);
			messenger_->send(pmsg);	
			auto pmsgos = make_shared<OrderStatusMsg>(to_string(o->clientID_),name_);
			pmsgos->set(o);
			messenger_->send(pmsgos);		
		}
		else {
			pmsg->data_.api_ = "UNKONWN";
			pmsg->data_.account_ = ctpacc_.userid;
			messenger_->send(pmsg);
			auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
				MSG_TYPE_ERROR_ORGANORDER,
				pTrade->OrderSysID);
			messenger_->send(pmsgout);			
			LOG_ERROR(logger,name_ <<" OnRtnTrade ordermanager cannot find orderNo:"<<pTrade->OrderSysID);
		}	
		LOG_INFO(logger,name_ <<" OnRtnTrade details:"
			<<" TradeID="<<pTrade->TradeID
			<<" OrderRef="<<pTrade->OrderRef
			<<" InstrumentID="<<pTrade->InstrumentID
			<<" ExchangeID="<<pTrade->ExchangeID
			<<" TradeTime="<<pTrade->TradeTime
			<<" OffsetFlag="<<pTrade->OffsetFlag
			<<" Direction="<<pTrade->Direction
			<<" Price="<<pTrade->Price
			<<" Volume="<<pTrade->Volume
		);	
	}
	///交易所报单录入错误回报
	void CtpTDEngine::OnErrRtnOrderInsert(CThostFtdcInputOrderField *pInputOrder, CThostFtdcRspInfoField *pRspInfo) {
		bool bResult = (pRspInfo != nullptr) && (pRspInfo->ErrorID != 0);
		if(bResult){
			if (pInputOrder == nullptr){
				LOG_INFO(logger,name_ <<" OnErrRtnOrderInsert return nullptr");
				return;
			}			
			string errormsgutf8;
			errormsgutf8 =  boost::locale::conv::between( pRspInfo->ErrorMsg, "UTF-8", "GB18030" );
			string localno = to_string(frontID_) + "-" + to_string(sessionID_) + "-" + pInputOrder->OrderRef;
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromAccAndLocalNo(ctpacc_.id,localno);
			if (o != nullptr) {
				lock_guard<mutex> g(orderStatus_mtx);
				o->orderStatus_ = OS_Error;			// rejected
				o->updateTime_ = ymdhmsf();
				auto pmsgout = make_shared<ErrorMsg>(to_string(o->clientID_), name_,
					MSG_TYPE_ERROR_INSERTORDER,
					to_string(o->clientOrderID_));
				messenger_->send(pmsgout);

				auto pmsgout2 = make_shared<OrderStatusMsg>(to_string(o->clientID_),name_);
				pmsgout2->set(o);
				messenger_->send(pmsgout2);	
			}
			else {
				auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
					MSG_TYPE_ERROR_ORGANORDER,
					pInputOrder->OrderRef);
				messenger_->send(pmsgout);			
				LOG_ERROR(logger,name_ <<" OnErrRtnOrderInsert ordermanager cannot find orderref:"<<pInputOrder->OrderRef);
			}
			LOG_ERROR(logger,name_ <<" OnErrRtnOrderinsert:"
				<<" ErrorMsg:"<<errormsgutf8
				<<" InstrumentID="<<pInputOrder->InstrumentID
				<<" OrderRef="<<pInputOrder->OrderRef
				<<" ExchangeID="<<pInputOrder->ExchangeID
				<<" Direction="<<pInputOrder->Direction
				<<" CombOffsetFlag="<<pInputOrder->CombOffsetFlag
				<<" LimitPrice="<<pInputOrder->LimitPrice
				<<" VolumeTotalOriginal="<<pInputOrder->VolumeTotalOriginal
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
			string localno = to_string(pOrderAction->FrontID) + "-" + to_string(pOrderAction->SessionID) + "-" + pOrderAction->OrderRef;
			std::shared_ptr<Order> o = OrderManager::instance().retrieveOrderFromAccAndLocalNo(ctpacc_.id,localno);
			if (o != nullptr) {
				auto pmsgout = make_shared<ErrorMsg>(to_string(o->clientID_), name_,
					MSG_TYPE_ERROR_CANCELORDER,
					to_string(o->clientOrderID_));
				messenger_->send(pmsgout);	
			}
			else
			{
				auto pmsgout = make_shared<ErrorMsg>(DESTINATION_ALL, name_,
					MSG_TYPE_ERROR_ORGANORDER,
					pOrderAction->OrderRef);
				messenger_->send(pmsgout);
				LOG_ERROR(logger,name_ <<" OnErrRtnOrderAction OrderManager cannot find order,OrderRef="<<localno);
			}
			LOG_ERROR(logger,name_ <<" OnErrRtnOrderAction: ErrorID="<<pRspInfo->ErrorID<<"ErrorMsg="<<errormsgutf8);
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