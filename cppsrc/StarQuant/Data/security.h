#ifndef _StarQuant_Data_Security_H_
#define _StarQuant_Data_Security_H_

#include <string>
#include <sstream>
#include <regex>

#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>

using std::string;

namespace StarQuant
{
	// Full Symbol = Serialization = Symbol + Security Type + Exchange (+ Multiplier, default is 1)
	// It's the Full Symbol that is used throughout the program;
	struct Security {
		Security()
			: symbol("")
			, securityType("")
		{
		}

		Security(string sym, string sectype, string exch = "", int mply = 1)
		{
			symbol = sym;
			securityType = sectype;
			exchange = exch;
			multiplier = mply;

			right = "";
		}

		// long internalId;
		string symbol;
		string securityType;
		string exchange;
		int multiplier;
		string localName;	// Unicode; e.g., in Chinese or French
		string currency;
		string ticksize;		// ES is 0.25

		// Options
		string underlyingSymbol;
		double strike = 0.0;
		string right;		// "C" or "P" or ""
		string expiryDate;

		string fullSymbol() {
			std::stringstream ss;
			ss << symbol << " " << securityType << " " << exchange;
			if (securityType == "FUT")
				ss << " " << multiplier;

			std::string s = ss.str();
			return s;
		}

		template<class Archive>
		void serialize(Archive & ar) {
			ar(	cereal::make_nvp("sym", symbol),
				cereal::make_nvp("type", securityType),
				cereal::make_nvp("e", exchange),
				cereal::make_nvp("m", multiplier),
				cereal::make_nvp("r", right),
				cereal::make_nvp("k", strike),
				cereal::make_nvp("c", currency),
				cereal::make_nvp("t", ticksize)
			);
		}

		string toJson(const std::regex& p) {
			std::stringstream ss;
			{
				cereal::JSONOutputArchive oarchive(ss);
				oarchive(cereal::make_nvp("order", *this));
			}
			return regex_replace(ss.str(), p, "$1");
		}
	};
}

#endif // _StarQuant_Common_Security_H_
