#include <Strategy/strategybase.h>
#include <Common/config.h>
#include <Common/timeutil.h>
#include <Trade/ordermanager.h>

namespace StarQuant {
	extern std::atomic<bool> gShutdown;
	int StrategyBase::m_orderId=0;
	StrategyBase::StrategyBase()
	{
		
		// if (CConfig::instance()._msgq == MSGQ::ZMQ) {
		// 	//msgq_pair_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT);
		// 	msgq_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT);
		// 	msgq_sub_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::SUB, CConfig::instance().MKT_DATA_PUBSUB_PORT, false);
		// }
		// else {
		// 	msgq_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT);
		// 	msgq_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().MKT_DATA_PUBSUB_PORT, false);
		// }

		//m_orderId = 0;
	}

	StrategyBase::~StrategyBase() {
	}

	void StrategyBase::initialize() {
		msleep(2000);
		initialized = true;
	}

	void StrategyBase::reset() {
	}

	void StrategyBase::teardown() {
		initialized = false;
	}

	// ************  Incoming Message Handers ********************//

	// ************ End Incoming Message Handers ********************//

	// ************  Outgoing Methods ********************//
	void StrategyBase::SendOrder(std::shared_ptr<Order> o)
	{
//TODO：根据订单类型发送相关信息，如限价单需要有价格信息
		lock_guard<mutex> g(oid_mtx);

		o->createTime = time(nullptr);
		o->orderStatus_ = OrderStatus::OS_NewBorn;
		o->clientOrderId = m_orderId;
		//o->serverOrderId= m_serverOrderId;
		// increase order id
		m_orderId++; 
		//OrderManager::instance().trackOrder(o);  

		string s;
		string s_price = "0.0";
		if (o->orderType == OrderType::OT_Limit){
			s_price = to_string(o->limitPrice);
		}else if (o->orderType == OrderType::OT_StopLimit){
			s_price =to_string(o->stopPrice);
		}
		s = to_string(MSG_TYPE::MSG_TYPE_ORDER) //CConfig::instance().new_order_msg
		+ SERIALIZATION_SEPARATOR + CConfig::instance().account
		+ SERIALIZATION_SEPARATOR + to_string(o->source)
		+ SERIALIZATION_SEPARATOR + to_string(o->clientOrderId)
		+ SERIALIZATION_SEPARATOR + to_string(static_cast<int>(o->orderType))
		+ SERIALIZATION_SEPARATOR + o->fullSymbol
		+ SERIALIZATION_SEPARATOR + to_string(o->orderSize)
		+ SERIALIZATION_SEPARATOR + s_price
		+ SERIALIZATION_SEPARATOR + to_string(static_cast<int>(o->orderFlag))
		+ SERIALIZATION_SEPARATOR + o->tag;
		msgstobrokerage.push(s);
//		msgq_pair->sendmsg(s)

	}

	void StrategyBase::SendOrderCancel(long oid)
	{
		// TODO: put it into order process queue
		string msg = to_string(MSG_TYPE::MSG_TYPE_CANCEL_ORDER)// CConfig::instance().cancel_order_msg
			+ SERIALIZATION_SEPARATOR + std::to_string(oid);

		msgstobrokerage.push(msg);
		//msgq_pair->sendmq(msg);
	}

	void StrategyBase::SendSubscriptionRequest()
	{

	}

	void StrategyBase::SendHistoricalBarRequest()
	{

	}

	void StrategyBase::SendGeneralInformation()
	{

	}

	void StrategyBase::SendLog()
	{

	}

	// ************  End Outgoing Methods ********************//
}