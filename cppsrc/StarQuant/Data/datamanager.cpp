#include <vector>
#include <Data/datamanager.h>
#include <Trade/portfoliomanager.h>
#include <Common/util.h>

namespace StarQuant {
	DataManager* DataManager::pinstance_ = nullptr;
	mutex DataManager::instancelock_;

	DataManager::DataManager() : count_(0)
	{
		// message queue factory
		// if (CConfig::instance()._msgq == MSGQ::ZMQ) {
		// 	//msgq_pub_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::PUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT);
		// 	msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT);
		// }
		// else {
		// 	msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT);
		// }
		// msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT);
		// construct map for data storage
		// rebuild();
	}

	DataManager::~DataManager()
	{

	}

	DataManager& DataManager::instance() {
		if (pinstance_ == nullptr) {
			lock_guard<mutex> g(instancelock_);
			if (pinstance_ == nullptr) {
				pinstance_ = new DataManager();
			}
		}
		return *pinstance_;
	}


	void DataManager::updateOrderBook(const Tick_L1& k){
			Tick_L5 newk;
			newk.depth_ = 1;
			newk.fullsymbol_ = k.fullsymbol_;
			newk.time_ = k.time_;
			newk.price_ = k.price_;
			newk.size_ = k.size_;
			newk.bidprice_L1_ = k.bidprice_L1_;
			newk.bidsize_L1_ = k.bidsize_L1_;
			newk.askprice_L1_ = k.askprice_L1_;
			newk.asksize_L1_ = k.asksize_L1_;
			newk.open_interest = k.open_interest;
			newk.open_ = k.open_;
			newk.high_ = k.high_;
			newk.low_ = k.low_;
			newk.pre_close_ = k.pre_close_;
			newk.upper_limit_price_ = k.upper_limit_price_;
			newk.lower_limit_price_ = k.lower_limit_price_;
			orderBook_[k.fullsymbol_] = newk;
	}
	void DataManager::updateOrderBook(const Tick_L5& k){
			orderBook_[k.fullsymbol_] = k;
			// Tick_L5 newk;
			// newk.depth_ = 5;
			// newk.fullsymbol_ = k.fullsymbol_;
			// newk.time_ = k.time_;
			// newk.price_ = k.price_;
			// newk.size_ = k.size_;
			// newk.bidprice_L1_ = k.bidprice_L1_;
			// newk.bidsize_L1_ = k.bidsize_L1_;
			// newk.askprice_L1_ = k.askprice_L1_;
			// newk.asksize_L1_ = k.asksize_L1_;
			// newk.bidprice_L2_ = k.bidprice_L2_;
			// newk.bidsize_L2_ = k.bidsize_L2_;
			// newk.askprice_L2_ = k.askprice_L2_;
			// newk.asksize_L2_ = k.asksize_L2_;
			// newk.bidprice_L3_ = k.bidprice_L3_;
			// newk.bidsize_L3_ = k.bidsize_L3_;
			// newk.askprice_L3_ = k.askprice_L3_;
			// newk.asksize_L3_ = k.asksize_L3_;
			// newk.bidprice_L4_ = k.bidprice_L4_;
			// newk.bidsize_L4_ = k.bidsize_L4_;
			// newk.askprice_L4_ = k.askprice_L4_;
			// newk.asksize_L4_ = k.asksize_L4_;
			// newk.bidprice_L5_ = k.bidprice_L5_;
			// newk.bidsize_L5_ = k.bidsize_L5_;
			// newk.askprice_L5_ = k.askprice_L5_;
			// newk.asksize_L5_ = k.asksize_L5_;
			// newk.open_interest = k.open_interest;
			// newk.open_ = k.open_;
			// newk.high_ = k.high_;
			// newk.low_ = k.low_;
			// newk.pre_close_ = k.pre_close_;
			// newk.upper_limit_price_ = k.upper_limit_price_;
			// newk.lower_limit_price_ = k.lower_limit_price_;
			// orderBook_[k.fullsymbol_] = newk;
	}

	// void DataManager::updateOrderBook(const Tick_L20& k){
	// 	orderBook_[k.fullsymbol_] = k;
	// }

	void DataManager::updateOrderBook(const Fill& fill){
	//assume only price change
		if (orderBook_.find(fill.fullSymbol) != orderBook_.end()){
			orderBook_[fill.fullSymbol].price_ = fill.tradePrice;
			orderBook_[fill.fullSymbol].size_ = fill.tradeSize;
		}
		else
		{
			Tick_L5 newk;
			newk.depth_ = 0;
			newk.price_ = fill.tradePrice;
			newk.size_ = fill.tradeSize;
			orderBook_[fill.fullSymbol] = newk;
		}
	}

	void DataManager::reset() {
		orderBook_.clear();
		//_5s.clear();
		//_15s.clear();
		// _60s.clear();
		//_1d.clear();
		securityDetails_.clear();
		count_ = 0;
	}

	void DataManager::rebuild() {
		// for (auto& s : CConfig::instance().securities) {
		// 	Tick_L5 k;
		// 	k.fullsymbol_ = s;
		// 	_latestmarkets[s] = k;

		// 	//_5s[s].fullsymbol = s; _5s[s].interval_ = 5;
		// 	//_15s[s].fullsymbol = s; _15s[s].interval_ = 15;
		// 	// _60s[s].fullsymbol = s; _60s[s].interval_ = 60;
		// 	//_1d[s].fullsymbol = s; _1d[s].interval_ = 24 * 60 * 60;
		// }
	}

	// void DataManager::SetTickValue(Tick& k) {
		// PRINT_TO_FILE("INFO:[%s,%d][%s]%s, %.2f\n", __FILE__, __LINE__, __FUNCTION__, k.fullsymbol_.c_str(), k.price_);		// for debug
		// //cout<<"settickvalue ktype: "<<k.msgtype_<<" price"<<k.price_<<endl;
		// if (k.msgtype_ == MSG_TYPE::MSG_TYPE_Bid) {
		// 	_latestmarkets[k.fullsymbol_].bidprice_L1_ = k.price_;
		// 	_latestmarkets[k.fullsymbol_].bidsize_L1_ = k.size_;
		// }
		// else if (k.msgtype_ == MSG_TYPE::MSG_TYPE_Ask ){
		// 	_latestmarkets[k.fullsymbol_].askprice_L1_ = k.price_;
		// 	_latestmarkets[k.fullsymbol_].asksize_L1_ = k.size_;
		// }
		// else if (k.msgtype_ == MSG_TYPE::MSG_TYPE_Trade) {
		// 	_latestmarkets[k.fullsymbol_].price_ = k.price_;
		// 	_latestmarkets[k.fullsymbol_].size_ = k.size_;

		// 	//_5s[k.fullsymbol_].newTick(k);				// if it doesn't exist, operator[] creates a new element with default constructor
		// 	//_15s[k.fullsymbol_].newTick(k);
		// 	_60s[k.fullsymbol_].newTick(k);
		// 	//PortfolioManager::instance()._positions[sym].
		// }
		// else if (k.msgtype_ == MSG_TYPE::MSG_TYPE_TICK_L1 || k.msgtype_ == MSG_TYPE::MSG_TYPE_TICK_L5 || k.msgtype_ == MSG_TYPE::MSG_TYPE_TICK_L20 ) {
		// 	//_latestmarkets[k.fullsymbol_] = dynamic_cast<Tick_L5&>(k);		// default assigement shallow copy
		// 	_latestmarkets[k.fullsymbol_].price_ = k.price_;
		// 	_latestmarkets[k.fullsymbol_].size_ = k.size_;
		// 	//cout<<"settickvalue price"<<_latestmarkets[k.fullsymbol_].price_<<endl;
		// 	_60s[k.fullsymbol_].newTick(k);
		// }
	// }


}

