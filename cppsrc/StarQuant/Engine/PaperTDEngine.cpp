#include <mutex>
#include <boost/locale.hpp>
#include <boost/algorithm/algorithm.hpp>

#include <Common/datastruct.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
#include <Data/datamanager.h>
#include <Common/logger.h>
#include <Common/util.h>
#include <Engine/PaperTDEngine.h>

using namespace std;
namespace StarQuant
{
	//extern std::atomic<bool> gShutdown;

	PaperTDEngine::PaperTDEngine() 
	{
		m_brokerOrderId_ = 0;
		init();
	}

	PaperTDEngine::~PaperTDEngine() {
		if (estate_ != STOP)
			stop();

	}

	void PaperTDEngine::init(){
		if(logger == nullptr){
			logger = SQLogger::getLogger("TDEngine.Paper");
		}
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
		}
		name_ = "PAPER_TD";
		estate_ = CONNECTING;
		LOG_DEBUG(logger,"Paper TD inited");
	}
	void PaperTDEngine::stop(){
		estate_  = EState::STOP;
		LOG_DEBUG(logger,"Paper TD stoped");	

	}

	void PaperTDEngine::start(){
		while(estate_ != EState::STOP){
			string msgin = msgq_recv_->recmsg(0);
			if (msgin.empty())
				continue;
			MSG_TYPE msgintype = MsgType(msgin);
			vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);			
			if (v[0] != name_) //filter message according to its destination
				continue;
			LOG_DEBUG(logger,"Paper TD recv msg:"<<msgin );
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
						LOG_DEBUG(logger,"Paper_TD is not connected,can not insert order!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "Paper td is not connected,can not insert order";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_CANCEL_ORDER:
					if (estate_ == LOGIN_ACK){
						if (v[1] == "0")  //cancel order by serveroid from gui(0)
							cancelOrder(stol(v[3]),0);
						else
							cancelOrder(v); //cancel order according to sid and clientorderid
					}
					else{
						LOG_DEBUG(logger,"Paper_TD is not connected,can not cancel order!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "Paper td is not connected,can not cancel order";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_QRY_POS:
					if (estate_ == LOGIN_ACK){
						queryPosition(v[1]);//TODO:区分不同来源，回报中添加目的地信息
					}
					else{
						LOG_DEBUG(logger,"Paper_TD is not connected,can not qry pos!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "Paper td is not connected,can not qry pos";
						lock_guard<std::mutex> g(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
					}
					break;
				case MSG_TYPE_QRY_ACCOUNT:
					if (estate_ == LOGIN_ACK){
						queryAccount(v[1]);
					}
					else{
						LOG_DEBUG(logger,"Paper_TD is not connected,can not qry acc!");
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_ENGINENOTCONNECTED) 	+ SERIALIZATION_SEPARATOR 
							+ "Paper td is not connected,can not qry acc";
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
						LOG_DEBUG(logger,"Paper_TD return test msg!");
					}
					break;
				default:
					break;
			}
		}
	}

	bool PaperTDEngine::connect(){
		msleep(1000);
		estate_ = LOGIN_ACK;
		return true;
	}

	bool PaperTDEngine::disconnect(){
		msleep(1000);
		estate_ = DISCONNECTED;
		return true;
	}


	void PaperTDEngine::insertOrder(const vector<string>& v){
		std::shared_ptr<Order> o = make_shared<Order>();
		lock_guard<mutex> g(oid_mtx);
		o->serverOrderId = m_serverOrderId++;
		o->brokerOrderId = m_brokerOrderId_++;
		o->createTime = ymdhmsf();	
		o->orderStatus_ = OrderStatus::OS_NewBorn;	
		o->api = name_;// = name_;	
		o->source = stoi(v[1]);
		o->clientId = stoi(v[1]);		
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
		// begin simulate trade, now only support L1
		if (DataManager::instance().orderBook_.find(o->fullSymbol) != DataManager::instance().orderBook_.end()){
			double lastprice = DataManager::instance().orderBook_[o->fullSymbol].price_;
			double lastaskprice1 = DataManager::instance().orderBook_[o->fullSymbol].askprice_L1_;
			double lastbidprice1 = DataManager::instance().orderBook_[o->fullSymbol].bidprice_L1_;
			long lastasksize1 = DataManager::instance().orderBook_[o->fullSymbol].asksize_L1_;
			long lastbidsize1 = DataManager::instance().orderBook_[o->fullSymbol].bidsize_L1_;
			Fill fill;
			fill.fullSymbol = o->fullSymbol;
			fill.tradetime = ymdhmsf();
			fill.serverOrderId = o->serverOrderId;
			fill.clientOrderId = o->clientOrderId;
			fill.brokerOrderId = o->brokerOrderId;
			fill.tradeId = o->brokerOrderId;
			fill.account_ = o->account_;     
			fill.api_ = o->api_;   
			if (o->orderType == OrderType::OT_Market){
				fill.fillflag = o->orderFlag;
				if (o->orderSize > 0){
					fill.tradePrice = lastaskprice1;
					fill.tradeSize = o->orderSize < lastasksize1 ? o->orderSize : lastasksize1;
				}
				else
				{
					fill.tradePrice = lastbidprice1;
					fill.tradeSize = (-1)*o->orderSize < lastasksize1 ? o->orderSize : lastasksize1*(-1);
				}
			}
			else if(o->orderType == OrderType::OT_Limit){
				if (o->orderSize > 0){
					if (o->limitPrice >= lastaskprice1){
						if (lastprice < lastaskprice1){
							fill.tradePrice = lastaskprice1;
						}
						else if (lastprice > o->limitPrice)
						{
							fill.tradePrice = o->limitPrice;
						}
						else
						{
							fill.tradePrice = lastprice;
						}
						fill.tradeSize = o->orderSize < lastasksize1 ? o->orderSize : lastasksize1;
						fill.fillflag = o->orderFlag;
					}
					else
					{
						lock_guard<mutex> gs(orderStatus_mtx);
						o->orderStatus_ = OrderStatus::OS_Error;
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
							+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
							+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
							+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
							+ "9999" + SERIALIZATION_SEPARATOR
							+ "Paper TD cannot deal due to price is below ask price, waiting order is not supported yet";
						lock_guard<std::mutex> ge(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
						LOG_ERROR(logger,"Paper TD cannot deal due to price is below ask price");
						return;
					}

				}
				else
				{
					if (o->limitPrice <= lastbidprice1){
						if (lastprice > lastbidprice1){
							fill.tradePrice = lastbidprice1;
						}
						else if (lastprice < o->limitPrice)
						{
							fill.tradePrice = o->limitPrice;
						}
						else
						{
							fill.tradePrice = lastprice;
						}
						fill.tradeSize = (-1)*o->orderSize < lastbidsize1 ? o->orderSize : (-1)*lastbidsize1;
						fill.fillflag = o->orderFlag;
					}
					else
					{
						lock_guard<mutex> gs(orderStatus_mtx);
						o->orderStatus_ = OrderStatus::OS_Error;
						string msgout = v[1]+ SERIALIZATION_SEPARATOR 
							+ name_ + SERIALIZATION_SEPARATOR 
							+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
							+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
							+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
							+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
							+ "9999" + SERIALIZATION_SEPARATOR
							+ "Paper TD cannot deal due to price is above bid price, waiting order is not supported yet";
						lock_guard<std::mutex> ge(IEngine::sendlock_);
						IEngine::msgq_send_->sendmsg(msgout);
						LOG_ERROR(logger,"Paper TD cannot deal due to price is above bid price");
						return;
					}
				}				


			}
			else if (o->orderType == OrderType::OT_StopLimit){
				lock_guard<mutex> gs(orderStatus_mtx);				
				o->orderStatus_ = OrderStatus::OS_Error;
				string msgout = v[1]+ SERIALIZATION_SEPARATOR 
					+ name_ + SERIALIZATION_SEPARATOR 
					+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
					+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
					+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
					+ "9999" + SERIALIZATION_SEPARATOR
					+ "Paper TD donot support stop order yet";
				lock_guard<std::mutex> ge(IEngine::sendlock_);
				IEngine::msgq_send_->sendmsg(msgout);
				LOG_ERROR(logger,"Paper TD donot support stop order yet");
				return;				
			}
			OrderManager::instance().gotFill(fill);	
			lock_guard<mutex> gs(orderStatus_mtx);					
			o->orderStatus_ = OrderStatus::OS_Filled;		
			LOG_INFO(logger,"Order filled by paper td,  Order: clientorderid ="<<o->clientOrderId<<"fullsymbol = "<<o->fullSymbol);
			lock_guard<std::mutex> ge(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(o->serialize());
			IEngine::msgq_send_->sendmsg(fill.serialize());
		}
		else
		{
			lock_guard<mutex> gs(orderStatus_mtx);
			o->orderStatus_ = OrderStatus::OS_Error;
			string msgout = v[1]+ SERIALIZATION_SEPARATOR 
				+ name_ + SERIALIZATION_SEPARATOR 
				+ to_string(MSG_TYPE_ERROR_INSERTORDER) + SERIALIZATION_SEPARATOR
				+ to_string(o->serverOrderId) + SERIALIZATION_SEPARATOR
				+ to_string(o->clientOrderId) + SERIALIZATION_SEPARATOR
				+ to_string(o->brokerOrderId) + SERIALIZATION_SEPARATOR  
				+ "9999" + SERIALIZATION_SEPARATOR
				+ "Paper TD cannot insert order due to DM dont have markets info";
			lock_guard<std::mutex> ge(IEngine::sendlock_);
			IEngine::msgq_send_->sendmsg(msgout);
			LOG_ERROR(logger,"Paper TD order insert error: due to DM dont have markets info");
			return;
		}

	}
	
	void PaperTDEngine::cancelOrder(const vector<string>& v){
		LOG_INFO(logger,"Paper td dont support cancelorder yet!");
	}
	
	void PaperTDEngine::cancelOrder(long oid,const string& source) {
		LOG_INFO(logger,"Paper td dont support cancelorder yet!");		
	}

	void PaperTDEngine::cancelOrders(const string& symbol,const string& source) {		
	}

	// 查询账户
	void PaperTDEngine::queryAccount(const string& source) {
	}

	void PaperTDEngine::queryOrder(const string& msgorder_,const string& source){
	}

	/// 查询pos
	void PaperTDEngine::queryPosition(const string& source) {
	}




}