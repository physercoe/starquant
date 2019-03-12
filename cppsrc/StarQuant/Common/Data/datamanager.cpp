#include <vector>
#include <Common/Data/datamanager.h>
#include <Common/Security/portfoliomanager.h>
#include <Common/Util/util.h>

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
		
		msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT);
		// construct map for data storage
		rebuild();
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

	void DataManager::SetTickValue(Tick& k) {
		PRINT_TO_FILE("INFO:[%s,%d][%s]%s, %.2f\n", __FILE__, __LINE__, __FUNCTION__, k.fullsymbol_.c_str(), k.price_);		// for debug
		//cout<<"settickvalue ktype: "<<k.datatype_<<" price"<<k.price_<<endl;
		if (k.datatype_ == DataType::DT_Bid) {
			_latestmarkets[k.fullsymbol_].bidprice_L1_ = k.price_;
			_latestmarkets[k.fullsymbol_].bidsize_L1_ = k.size_;
		}
		else if (k.datatype_ == DataType::DT_Ask ){
			_latestmarkets[k.fullsymbol_].askprice_L1_ = k.price_;
			_latestmarkets[k.fullsymbol_].asksize_L1_ = k.size_;
		}
		else if (k.datatype_ == DataType::DT_Trade) {
			_latestmarkets[k.fullsymbol_].price_ = k.price_;
			_latestmarkets[k.fullsymbol_].size_ = k.size_;

			//_5s[k.fullsymbol_].newTick(k);				// if it doesn't exist, operator[] creates a new element with default constructor
			//_15s[k.fullsymbol_].newTick(k);
			_60s[k.fullsymbol_].newTick(k);
			//PortfolioManager::instance()._positions[sym].
		}
		else if (k.datatype_ == DataType::DT_Full) {
			//_latestmarkets[k.fullsymbol_] = dynamic_cast<FullTick&>(k);		// default assigement shallow copy
			_latestmarkets[k.fullsymbol_].price_ = k.price_;
			_latestmarkets[k.fullsymbol_].size_ = k.size_;
			//cout<<"settickvalue price"<<_latestmarkets[k.fullsymbol_].price_<<endl;
			_60s[k.fullsymbol_].newTick(k);
		}
	}

	void DataManager::reset() {
		_latestmarkets.clear();
		//_5s.clear();
		//_15s.clear();
		_60s.clear();
		//_1d.clear();

		securityDetails_.clear();
		count_ = 0;
	}

	void DataManager::rebuild() {
		for (auto& s : CConfig::instance().securities) {
			FullTick k;
			k.fullsymbol_ = s;
			_latestmarkets[s] = k;

			//_5s[s].fullsymbol = s; _5s[s].interval_ = 5;
			//_15s[s].fullsymbol = s; _15s[s].interval_ = 15;
			_60s[s].fullsymbol = s; _60s[s].interval_ = 60;
			//_1d[s].fullsymbol = s; _1d[s].interval_ = 24 * 60 * 60;
		}
	}
}

