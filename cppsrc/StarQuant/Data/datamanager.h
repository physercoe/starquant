#ifndef _StarQuant_Data_DataManager_H_
#define _StarQuant_Data_DataManager_H_

#include <string>
#include <sstream>
#include <map>
#include <regex>

//#include <Common/Data/datatype.h>
#include <Data/tick.h>
#include <Data/barseries.h>
#include <Data/security.h>
#include <Data/tickwriter.h>
#include <Trade/fill.h>
#define CEREAL_RAPIDJSON_NAMESPACE creal_rapidjson
#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>

#ifdef _WIN32
#include <nanomsg/src/nn.h>
#include <nanomsg/src/pubsub.h>
#else
#include <nanomsg/nn.h>
#include <nanomsg/pubsub.h>
#endif

using std::string;

namespace StarQuant
{
	/// DataManager
	/// 1. provide latest full tick price info  -- DataBoard Service
	/// 2. record data
	class DataManager {
	public:
		// std::unique_ptr<CMsgq> msgq_pub_;

		static DataManager* pinstance_;
		static mutex instancelock_;
		static DataManager& instance();

		TickWriter recorder_;
		uint64_t count_ = 0;
		std::map<std::string, Security> securityDetails_;
		std::map<string, Tick_L5> orderBook_;
		//std::map<string, BarSeries> _5s;
		//std::map<string, BarSeries> _15s;
		// std::map<string, BarSeries> _60s;
		//std::map<string, BarSeries> _1d;

		DataManager();
		~DataManager();
		void reset();
		void rebuild();
		void updateOrderBook(const Tick_L1& k);
		void updateOrderBook(const Tick_L5& k);
		// void updateOrderBook(const Tick_L20& k);
		void updateOrderBook(const Fill& fill);
	};
}

#endif // _StarQuant_Data_DataManager_H_
