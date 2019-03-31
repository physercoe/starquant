#ifndef _StarQuant_Common_DataManager_H_
#define _StarQuant_Common_DataManager_H_

#include <string>
#include <sstream>
#include <map>
#include <regex>

//#include <Common/Data/datatype.h>
#include <Data/tick.h>
#include <Data/barseries.h>
#include <Data/security.h>

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
	/// 2. provide bar series		-- Bar Service
	class DataManager {
	public:
		std::unique_ptr<CMsgq> msgq_pub_;

		static DataManager* pinstance_;
		static mutex instancelock_;
		static DataManager& instance();
		//atomic<uint64_t> count_ = { 0 };
		uint64_t count_ = 0;

		std::map<string, Tick_L5> _latestmarkets;
		//std::map<string, BarSeries> _5s;
		//std::map<string, BarSeries> _15s;
		std::map<string, BarSeries> _60s;
		//std::map<string, BarSeries> _1d;
		std::map<std::string, Security> securityDetails_;

		DataManager();
		~DataManager();
		void reset();
		void rebuild();
		void SetTickValue(Tick& k);
	};
}

#endif // _StarQuant_Common_DataManager_H_
