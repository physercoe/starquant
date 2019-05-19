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
		fillID_ = 0;
		init();
	}

	PaperTDEngine::~PaperTDEngine() {
		if (estate_ != STOP)
			stop();

	}

	void PaperTDEngine::init(){
		name_ = "PAPER.TD";
		if(logger == nullptr){
			logger = SQLogger::getLogger("TDEngine.Paper");
		}
		if (messenger_ == nullptr){
			messenger_ = std::make_unique<CMsgqEMessenger>(name_, CConfig::instance().SERVERSUB_URL);	
			msleep(100);
		}	
		estate_ = DISCONNECTED;		
		auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_ENGINE_STATUS,
						to_string(estate_));
		messenger_->send(pmsgs);
		LOG_DEBUG(logger,"Paper TD inited");
	}
	void PaperTDEngine::stop(){
		estate_  = EState::STOP;
		auto pmsgs = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_ENGINE_STATUS,
						to_string(estate_));
		messenger_->send(pmsgs);
		LOG_DEBUG(logger,"Paper TD stoped");	

	}

	void PaperTDEngine::start(){
		while(estate_ != EState::STOP){
			auto pmsgin = messenger_->recv();
			bool processmsg = ((pmsgin != nullptr) && ( startwith(pmsgin->destination_,DESTINATION_ALL) || (startwith(pmsgin->destination_,name_) )));
			// if (pmsgin == nullptr || !startwith(pmsgin->destination_, name_) )
			// 	continue;
			if (processmsg){
				switch (pmsgin->msgtype_)
				{
					case MSG_TYPE_ENGINE_CONNECT:
						if (connect()){
							auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
								MSG_TYPE_INFO_ENGINE_TDCONNECTED,"PAPER TD Connected.");
							messenger_->send(pmsgout,1);
							
						}
						break;
					case MSG_TYPE_ENGINE_DISCONNECT:
						disconnect();
						break;
					case MSG_TYPE_ORDER_PAPER:
					case MSG_TYPE_ORDER:
						if (estate_ == LOGIN_ACK){
							auto pmsgin2 = static_pointer_cast<PaperOrderMsg>(pmsgin);
							insertOrder(pmsgin2);
						}
						else{
							LOG_DEBUG(logger,"PAPER_TD is not connected,can not insert order!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								"Paper Td is not connected,can not insert order!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_CANCEL_ORDER:
						if (estate_ == LOGIN_ACK){
							auto pmsgin2 = static_pointer_cast<OrderActionMsg>(pmsgin);
							cancelOrder(pmsgin2);
						}
						else{
							LOG_DEBUG(logger,"PAPER_TD is not connected,can not cancel order!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								"Paper Td is not connected,can not cancel order!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_QRY_POS:
						if (estate_ == LOGIN_ACK){
							queryPosition(pmsgin);
						}
						else{
							LOG_DEBUG(logger,"PAPER_TD is not connected,can not qry pos!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								"PAPER TD  is not connected,can not qry pos!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_QRY_ACCOUNT:
						if (estate_ == LOGIN_ACK){
							queryAccount(pmsgin);
						}
						else{
							LOG_DEBUG(logger,"PAPER_TD is not connected,can not qry acc!");
							auto pmsgout = make_shared<ErrorMsg>(pmsgin->source_, name_,
								MSG_TYPE_ERROR_ENGINENOTCONNECTED,
								"paper Td is not connected,can not qry acc!");
							messenger_->send(pmsgout);
						}
						break;
					case MSG_TYPE_ENGINE_STATUS:
						{
							auto pmsgout = make_shared<InfoMsg>(pmsgin->source_, name_,
								MSG_TYPE_ENGINE_STATUS,
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
							LOG_DEBUG(logger,"PAPER_TD return test msg!");
						}
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

	void PaperTDEngine::processbuf(){

	}
	void PaperTDEngine::timertask(){
		
	}
	bool PaperTDEngine::connect(){
		msleep(1000);
		estate_ = LOGIN_ACK;
		auto pmsg = make_shared<InfoMsg>(DESTINATION_ALL, name_,
							MSG_TYPE_ENGINE_STATUS,
							to_string(estate_));
		messenger_->send(pmsg);
		return true;
	}

	bool PaperTDEngine::disconnect(){
		msleep(1000);
		estate_ = DISCONNECTED;
		auto pmsg = make_shared<InfoMsg>(DESTINATION_ALL, name_,
						MSG_TYPE_ENGINE_STATUS,
						to_string(estate_));
		messenger_->send(pmsg);
		return true;
	}


	void PaperTDEngine::insertOrder(shared_ptr<PaperOrderMsg> pmsg){
		lock_guard<mutex> g(oid_mtx);
		pmsg->data_.serverOrderID_ = m_serverOrderId++;
		pmsg->data_.brokerOrderID_ = m_brokerOrderId_++;
		pmsg->data_.orderNo_ = string("PAPER.TD-") + to_string(pmsg->data_.brokerOrderID_);
		pmsg->data_.localNo_ = pmsg->data_.orderNo_;
		pmsg->data_.createTime_ = ymdhmsf();
		pmsg->data_.orderStatus_ = OrderStatus::OS_Submitted;
		pmsg->data_.price_ = pmsg->data_.limitPrice_;
		pmsg->data_.quantity_ = pmsg->data_.orderSize_;
		pmsg->data_.flag_ = pmsg->data_.orderFlag_;

		auto o = static_pointer_cast<PaperOrder>(pmsg->toPOrder());
		OrderManager::instance().trackOrder(o);
		// begin simulate trade, now only support L1
		if (DataManager::instance().orderBook_.find(o->fullSymbol_) != DataManager::instance().orderBook_.end()){
			double lastprice = DataManager::instance().orderBook_[o->fullSymbol_].price_;
			double lastaskprice1 = DataManager::instance().orderBook_[o->fullSymbol_].askPrice_[0];
			double lastbidprice1 = DataManager::instance().orderBook_[o->fullSymbol_].bidPrice_[0];
			long lastasksize1 = DataManager::instance().orderBook_[o->fullSymbol_].askSize_[0];
			long lastbidsize1 = DataManager::instance().orderBook_[o->fullSymbol_].bidSize_[0];
			auto pmsgfill = make_shared<FillMsg>();
			pmsgfill->destination_ = pmsg->source_;
			pmsgfill->source_ = name_;
			pmsgfill->data_.fullSymbol_ = o->fullSymbol_;
			pmsgfill->data_.tradeTime_ = ymdhmsf();
			pmsgfill->data_.orderNo_ = o->orderNo_;
			pmsgfill->data_.serverOrderID_ = o->serverOrderID_;
			pmsgfill->data_.clientOrderID_ = o->clientOrderID_;
			pmsgfill->data_.brokerOrderID_ = o->brokerOrderID_;
			pmsgfill->data_.tradeId_ = fillID_++;
			pmsgfill->data_.tradeNo_ = to_string(pmsgfill->data_.tradeId_);
			pmsgfill->data_.account_ = o->account_;     
			pmsgfill->data_.api_ = o->api_;   

			if (o->orderType_ == OrderType::OT_Market){
				pmsgfill->data_.fillFlag_ = o->orderFlag_;
				if (o->orderSize_ > 0){
					pmsgfill->data_.tradePrice_ = lastaskprice1;
					pmsgfill->data_.tradeSize_ = o->orderSize_ < lastasksize1 ? o->orderSize_ : lastasksize1;
				}
				else
				{
					pmsgfill->data_.tradePrice_ = lastbidprice1;
					pmsgfill->data_.tradeSize_ = (-1)*o->orderSize_ < lastasksize1 ? o->orderSize_ : lastasksize1*(-1);
				}
			}
			else if(o->orderType_ == OrderType::OT_Limit){
				if (o->orderSize_ > 0){
					if (o->limitPrice_ >= lastaskprice1){
						if (lastprice < lastaskprice1){
							pmsgfill->data_.tradePrice_ = lastaskprice1;
						}
						else if (lastprice > o->limitPrice_)
						{
							pmsgfill->data_.tradePrice_ = o->limitPrice_;
						}
						else
						{
							pmsgfill->data_.tradePrice_ = lastprice;
						}
						pmsgfill->data_.tradeSize_ = o->orderSize_ < lastasksize1 ? o->orderSize_ : lastasksize1;
						pmsgfill->data_.fillFlag_ = o->orderFlag_;
					}
					else
					{
						lock_guard<mutex> gs(orderStatus_mtx);
						o->orderStatus_ = OrderStatus::OS_Error;
						auto pos = make_shared<OrderStatusMsg>(pmsg->source_,name_);
						pos->set(o);
						// auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
						// 	MSG_TYPE_ERROR_INSERTORDER,
						// 	to_string(o->clientOrderID_));
						messenger_->send(pos);
						LOG_INFO(logger,"Paper TD cannot deal due to price is below ask price");
						return;
					}
				}
				else
				{
					if (o->limitPrice_ <= lastbidprice1){
						if (lastprice > lastbidprice1){
							pmsgfill->data_.tradePrice_ = lastbidprice1;
						}
						else if (lastprice < o->limitPrice_)
						{
							pmsgfill->data_.tradePrice_ = o->limitPrice_;
						}
						else
						{
							pmsgfill->data_.tradePrice_ = lastprice;
						}
						pmsgfill->data_.tradeSize_ = (-1)*o->orderSize_ < lastbidsize1 ? o->orderSize_ : (-1)*lastbidsize1;
						pmsgfill->data_.fillFlag_ = o->orderFlag_;
					}
					else
					{
						lock_guard<mutex> gs(orderStatus_mtx);
						o->orderStatus_ = OrderStatus::OS_Error;
						auto pos = make_shared<OrderStatusMsg>(pmsg->source_,name_);
						pos->set(o);						
						// auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
						// 	MSG_TYPE_ERROR_INSERTORDER,
						// 	to_string(o->clientOrderID_));
						messenger_->send(pos);	
						LOG_INFO(logger,"Paper TD cannot deal due to price is above bid price");
						return;
					}
				}				
			}
			else if (o->orderType_ == OrderType::OT_StopLimit){
				lock_guard<mutex> gs(orderStatus_mtx);				
				o->orderStatus_ = OrderStatus::OS_Error;
				auto pos = make_shared<OrderStatusMsg>(pmsg->source_,name_);
				pos->set(o);	
				// auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
				// 	MSG_TYPE_ERROR_INSERTORDER,
				// 	to_string(o->clientOrderID_));
				messenger_->send(pos);
				LOG_ERROR(logger,"Paper TD donot support stop order yet");
				return;				
			}
			OrderManager::instance().gotFill(pmsgfill->data_);	
			lock_guard<mutex> gs(orderStatus_mtx);					
			o->orderStatus_ = OrderStatus::OS_Filled;
			o->tradedvol_ = pmsgfill->data_.tradeSize_;
			auto pos = make_shared<OrderStatusMsg>(pmsg->source_,name_);
			pos->set(o);
			messenger_->send(pos);
			messenger_->send(pmsgfill);
			LOG_INFO(logger,name_<<" Fill Order: clientorderid ="<<o->clientOrderID_<<"fullsymbol = "<<o->fullSymbol_);
		}
		else
		{
			lock_guard<mutex> gs(orderStatus_mtx);
			o->orderStatus_ = OrderStatus::OS_Error;
			auto pos = make_shared<OrderStatusMsg>(pmsg->source_,name_);
			pos->set(o);	
			// auto pmsgout = make_shared<ErrorMsg>(pmsg->source_, name_,
			// 	MSG_TYPE_ERROR_INSERTORDER,
			// 	to_string(o->clientOrderID_));
			messenger_->send(pos);
			LOG_ERROR(logger,"Paper TD order insert error: due to DM dont have markets info");
			return;
		}

	}
	
	void PaperTDEngine::cancelOrder(shared_ptr<OrderActionMsg> pmsg){
		LOG_INFO(logger,name_<<" don't support cancelorder yet!");
	}
	
	// 查询账户
	void PaperTDEngine::queryAccount(shared_ptr<MsgHeader> pmsg) {
	}
   /// 查询pos
	void PaperTDEngine::queryPosition(shared_ptr<MsgHeader> pmsg) {
	}

}