#ifndef _StarQuant_Trade_Trade_H_
#define _StarQuant_Trade_Trade_H_

#include <string>
#include <sstream>
#include <cfloat>
#include <regex>
#include <Common/config.h>
#include <Trade/orderstatus.h>
#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>

using std::string;

namespace StarQuant
{
	struct Fill {
		Fill()
			: serverOrderId(-1)
			, clientOrderId(-1)
			, brokerOrderId(-1)
			, tradeId(-1)
			, clientId(0)
			, orderNo("")               //for TAP use
			, tradeNo("")
			, tradetime("")
			, fullSymbol("")
			, account("")
			, fillflag(OrderFlag::OF_OpenPosition)
			, api("")
			, source(-1)
			, currency("")
			, tradePrice(0.0)				// DBL_MAX
			, tradeSize(0)
			, commission(0.0)				// DBL_MAX
		{
		}

		long serverOrderId;
		long clientOrderId;
		long brokerOrderId;
		long tradeId;
		long clientId;
		string orderNo;
		string tradeNo;
		string tradetime;
		string fullSymbol;
		string account;
		OrderFlag fillflag;
		string api;						// IB, ctp etc
		int source;						// sid, get from client; 0=mannual
		string currency;
		double tradePrice;
		int tradeSize;					// < 0 = short, order size != trade size
		double commission;

		template<class Archive>
		void serialize(Archive & ar) {
			ar(cereal::make_nvp("serverorderid", serverOrderId),
				cereal::make_nvp("clientorderid", clientOrderId),
				cereal::make_nvp("brokerorderid", brokerOrderId),
				cereal::make_nvp("tradeid", tradeId),
				cereal::make_nvp("sym", fullSymbol),
				cereal::make_nvp("price", tradePrice),
				cereal::make_nvp("size", tradeSize),
				cereal::make_nvp("time", tradetime)
			);
		}

		string serialize() {
			string str =  to_string(clientId)
				+ SERIALIZATION_SEPARATOR + api
				+ SERIALIZATION_SEPARATOR + to_string(MSG_TYPE::MSG_TYPE_RTN_TRADE)                 
				+ SERIALIZATION_SEPARATOR +	std::to_string(serverOrderId)
				+ SERIALIZATION_SEPARATOR + std::to_string(clientOrderId)
				+ SERIALIZATION_SEPARATOR + std::to_string(brokerOrderId)
				+ SERIALIZATION_SEPARATOR + orderNo
				+ SERIALIZATION_SEPARATOR + tradeNo
				+ SERIALIZATION_SEPARATOR + tradetime
				+ SERIALIZATION_SEPARATOR + fullSymbol
				+ SERIALIZATION_SEPARATOR + std::to_string(tradePrice)
				+ SERIALIZATION_SEPARATOR + std::to_string(tradeSize)
				+ SERIALIZATION_SEPARATOR + std::to_string(static_cast<int>(fillflag))
				+ SERIALIZATION_SEPARATOR + std::to_string(commission)
				+ SERIALIZATION_SEPARATOR + account
				+ SERIALIZATION_SEPARATOR + api
				+ SERIALIZATION_SEPARATOR + std::to_string(source);				
			return str;
		}

		string toJson(const std::regex& p) {
			std::stringstream ss;
			{
				cereal::JSONOutputArchive oarchive(ss);
				oarchive(cereal::make_nvp("trade", *this));
			}
			return regex_replace(ss.str(), p, "$1");
		}
	};
}

#endif // _StarQuant_Common_Trade_H_
