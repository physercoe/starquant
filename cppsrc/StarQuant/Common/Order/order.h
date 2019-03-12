#ifndef _StarQuant_Common_Order_H_
#define _StarQuant_Common_Order_H_

#include <string>
#include <sstream>
#include <cfloat>
#include <regex>
#include <Common/Order/orderstatus.h>
#include <Common/Order/ordertype.h>
#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>

using std::string;

namespace StarQuant
{
	struct Order {
		Order()
			: serverOrderId(-1)
			, clientOrderId(-1)
			, brokerOrderId(-1)
			, permId(-1)
			, clientId(0)
			, orderNo("")              //for Tap use
			, createTime("")
			, cancelTime("")
			, fullSymbol("")
			, account("")
			, api("")
			, source(-1)
			, tag("")
			, orderType(OrderType::OT_Market)
			//, ORDERTYPE(OrderType::OT_Market)            //新的枚举变量，暂时保留原来上面的string变量（其他broker可能会用到）
			, orderStatus(OrderStatus::OS_UNKNOWN)
			, orderFlag(OrderFlag::OF_OpenPosition)
			, orderSize(0)
			, fillNo("")
			, filledSize(0)
			, lastFilledPrice(0.0f)
			, avgFilledPrice(0.0f)
			, limitPrice(0.0f)			// DBL_MAX
			, stopPrice(0.0f)
			, trailPrice(0.0f)
			, trailingPercent(0.0f)
			, timeInForce("")
			, outsideRegularTradingHour(false)
			, hidden(false)
			, allOrNone(false)
		{
		}

		long serverOrderId;
		long clientOrderId;
		long brokerOrderId;
		long clientId;
		long permId;				// for IB use
		string orderNo;
		string createTime;
		string cancelTime;
		string fullSymbol;
		string account;
		string api;						// IB, ctp etc
		int source;						// sid, get from client; -1=mannual
		string tag;                     // used for mark 
		OrderType orderType;						// MKT, LMT, STP, STPLMT, etc
		//OrderType ORDERTYPE;
		OrderStatus orderStatus;				// OS_NEWBORN, etc
		OrderFlag orderFlag;
		long orderSize;
		string fillNo;					// < 0 = short, order size != trade size
		long filledSize;
		double lastFilledPrice;
		double avgFilledPrice;
		double limitPrice;
		double stopPrice;
		double trailPrice;
		double trailingPercent;
		string timeInForce;
		bool outsideRegularTradingHour;
		bool hidden;
		bool allOrNone;

		template<class Archive>
		void serialize(Archive & ar) {
			ar(cereal::make_nvp("serverorderid", serverOrderId),
				cereal::make_nvp("clientorderid", clientOrderId),
				cereal::make_nvp("brokerorderid", brokerOrderId),
				cereal::make_nvp("sym", fullSymbol),
				cereal::make_nvp("type", orderType),
				cereal::make_nvp("size", orderSize),
				cereal::make_nvp("s", orderStatus),
				cereal::make_nvp("lp", limitPrice),
				cereal::make_nvp("sp", stopPrice),
				cereal::make_nvp("tp", trailPrice),
				cereal::make_nvp("lfp", lastFilledPrice),
				cereal::make_nvp("f", filledSize),
				cereal::make_nvp("c", createTime)
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

	struct MarketOrder : Order
	{
		MarketOrder() : Order()
		{
			limitPrice = 0;
			stopPrice = 0;
			trailPrice = 0;
		}
	};

	struct LimitOrder : Order
	{
		LimitOrder(double lp) : Order()
		{
			limitPrice = lp;
			stopPrice = 0;
			trailPrice = 0;
		}
	};

	struct StopOrder : Order
	{
		StopOrder(double sp) : Order()
		{
			limitPrice = 0;
			stopPrice = sp;
			trailPrice = 0;
		}
	};

	struct StopLimitOrder : Order
	{
		StopLimitOrder(double lp, double sp) : Order()
		{
			limitPrice = lp;
			stopPrice = sp;
			trailPrice = 0;
		}
	};

	struct TrailingStopOrder : Order
	{
		TrailingStopOrder(double tp) : Order()
		{
			limitPrice = 0;
			stopPrice = 0;
			trailPrice = tp;
		}
	};
}

#endif // _StarQuant_Common_Order_H_
