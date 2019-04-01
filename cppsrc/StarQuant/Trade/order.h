#ifndef _StarQuant_Trade_Order_H_
#define _StarQuant_Trade_Order_H_

#include <string>
#include <sstream>
#include <cfloat>
#include <regex>

#include <Common/config.h>
#include <Trade/orderstatus.h>
#include <Trade/ordertype.h>
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
		int clientId;
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


		string serialize() {
			string sprice = "0.0";
			if (orderType == OrderType::OT_Limit){
				sprice = std::to_string(limitPrice);
			}else if (orderType == OrderType::OT_StopLimit){
				sprice = std::to_string(stopPrice);
			}
			string str = std::to_string(clientId) //msg destination
				+ SERIALIZATION_SEPARATOR + api //msg source
				+ SERIALIZATION_SEPARATOR + std::to_string(MSG_TYPE::MSG_TYPE_RTN_ORDER)  //CConfig::instance().order_status_msg
				+ SERIALIZATION_SEPARATOR + std::to_string(serverOrderId)
				+ SERIALIZATION_SEPARATOR + std::to_string(clientOrderId)
				+ SERIALIZATION_SEPARATOR + std::to_string(brokerOrderId)
				+ SERIALIZATION_SEPARATOR + fullSymbol
				+ SERIALIZATION_SEPARATOR + std::to_string(orderSize)
				+ SERIALIZATION_SEPARATOR + std::to_string(orderFlag)
				+ SERIALIZATION_SEPARATOR + std::to_string(static_cast<int>(orderType))
				+ SERIALIZATION_SEPARATOR + sprice
				+ SERIALIZATION_SEPARATOR + std::to_string(filledSize)
				+ SERIALIZATION_SEPARATOR + std::to_string(avgFilledPrice)
				+ SERIALIZATION_SEPARATOR + createTime
				+ SERIALIZATION_SEPARATOR + cancelTime
				+ SERIALIZATION_SEPARATOR + account
				+ SERIALIZATION_SEPARATOR + std::to_string(source)
				+ SERIALIZATION_SEPARATOR + api
				+ SERIALIZATION_SEPARATOR + tag
				+ SERIALIZATION_SEPARATOR + orderNo
				+ SERIALIZATION_SEPARATOR + std::to_string(orderStatus);
			return str;
		}


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
