#ifndef __StarQuant_Data_Bar_H_
#define __StarQuant_Data_Bar_H_

#include <string>
#include <regex>

#include <Common/config.h>
#include <Data/tick.h>
#define CEREAL_RAPIDJSON_NAMESPACE creal_rapidjson
#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>

using namespace std;

namespace StarQuant {
	struct Bar {
		Bar();
		Bar(const string& s);
		~Bar() {}

		string fullsymbol_;
		int interval_;				// in seconds
		int barstarttime_;			// hhmmss 24hours, e.g. 232020; 12020
		int barorderinaday_;		// 0 = first bar, 1 = second bar of the day
		double open_;
		double high_;
		double low_;
		double close_;
		double volume_;
		double avgprice_;
		int tradesinbar_;

		bool isValid();
		void setBarStartTime();

		template<class Archive>
		void serialize(Archive & ar) {
			ar(CEREAL_NVP(fullsymbol_),
				cereal::make_nvp("O", open_),
				cereal::make_nvp("H", high_),
				cereal::make_nvp("L", low_),
				cereal::make_nvp("C", close_),
				cereal::make_nvp("V", volume_)
			);
		}

		inline string serialize() const {
			string s;
			s = to_string(MSG_TYPE_BAR_15MIN)  //TODO: distiguish different bar 
				+ SERIALIZATION_SEPARATOR + fullsymbol_ 
				+ SERIALIZATION_SEPARATOR + to_string(interval_)
				+ SERIALIZATION_SEPARATOR + to_string(barorderinaday_)
				+ SERIALIZATION_SEPARATOR + to_string(open_)
				+ SERIALIZATION_SEPARATOR + to_string(high_)
				+ SERIALIZATION_SEPARATOR + to_string(low_)
				+ SERIALIZATION_SEPARATOR + to_string(close_)
				+ SERIALIZATION_SEPARATOR + to_string(volume_);
			return s;
		}

		string toJson(const std::regex& p) {
			std::stringstream ss;
			{
				cereal::JSONOutputArchive oarchive(ss);
				oarchive(cereal::make_nvp("bar", *this));
			}
			string r = regex_replace(ss.str(), p, "$1");
			return r;
		}
	};
}

#endif  // __StarQuant_Common_Bar_H_
