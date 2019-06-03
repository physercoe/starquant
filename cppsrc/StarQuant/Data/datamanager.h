#ifndef _StarQuant_Data_DataManager_H_
#define _StarQuant_Data_DataManager_H_

#include <string>
#include <sstream>
#include <map>
#include <regex>

#include <Common/datastruct.h>
#include <Data/tickwriter.h>

#define CEREAL_RAPIDJSON_NAMESPACE creal_rapidjson
#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>


using std::string;

namespace StarQuant
{
	/// DataManager
	/// 1. provide latest full tick price info  -- DataBoard Service
	/// 2. record data
	class DataManager {
	public:


		static DataManager* pinstance_;
		static mutex instancelock_;
		static DataManager& instance();

		TickWriter recorder_;
		uint64_t count_ = 0;
		bool contractUpdated_ = false;

		std::map<std::string, Security> securityDetails_; //ctpsymbol to security
		std::map<string, Tick> orderBook_;
		std::map<string,string> ctp2Full_;
		std::map<string,string> full2Ctp_;
		//std::map<string, BarSeries> _5s;
		//std::map<string, BarSeries> _15s;
		// std::map<string, BarSeries> _60s;
		//std::map<string, BarSeries> _1d;

		DataManager();
		~DataManager();
		void reset();
		void rebuild();
		void updateOrderBook(const Tick& k){ orderBook_[k.fullSymbol_] = k;};
		void updateOrderBook(const Fill& fill);
		void saveSecurityToFile();
	};
}

#endif // _StarQuant_Data_DataManager_H_
