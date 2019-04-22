#include <vector>
#include <Data/datamanager.h>
#include <Trade/portfoliomanager.h>
#include <Common/datastruct.h>

namespace StarQuant {
	DataManager* DataManager::pinstance_ = nullptr;
	mutex DataManager::instancelock_;

	DataManager::DataManager() : count_(0)
	{
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



	void DataManager::updateOrderBook(const Fill& fill){
	//assume only price change
		if (orderBook_.find(fill.fullSymbol_) != orderBook_.end()){
			orderBook_[fill.fullSymbol_].price_ = fill.tradePrice_;
			orderBook_[fill.fullSymbol_].size_ = fill.tradeSize_;
		}
		else
		{
			Tick newk;
			newk.depth_ = 0;
			newk.price_ = fill.tradePrice_;
			newk.size_ = fill.tradeSize_;
			orderBook_[fill.fullSymbol_] = newk;
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
		// 	//PortfolioManager::instance().positions_[sym].
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

