// pass through all the data types
// take trade price and trade size, aggregate into bars and then propogate
#ifndef _StarQuant_Common_DataType_H_
#define _StarQuant_Common_DataType_H_

#include <string>

namespace StarQuant {
	enum DataType : int {
		DT_Trade = 0,			// DT_TradePrice + DT_TradeSize
		DT_Bid = 1,
		DT_Ask = 2,
		DT_Full = 3,
		DT_BidPrice = 4,
		DT_BidSize = 5,
		DT_AskPrice = 6,
		DT_AskSize = 7,
		DT_TradePrice = 8,
		DT_TradeSize = 9,
		DT_OpenPrice = 10,
		DT_HighPrice = 11,
		DT_LowPrice = 12,
		DT_ClosePrice = 13,
		DT_Volume = 14,
		DT_OpenInterest = 15,
		DT_Bar = 16,
		DT_Account = 17,
		DT_Position = 18
	};

	/// xxxTypeString is the string name of xxxType
	const std::string DataTypeString[] = {
		"BidSize",
		"BidPrice",
		"AskPrice",
		"AskSize",
		"TradePrice",
		"TradeSize",
		"OpenPrice",
		"HighPrice",
		"LowPrice",
		"ClosePrice",
		"Volume",
		"OpenInterest",
		"Bar",
		"Account",
		"Position",
		"OrderId"
	};
}

#endif  // _StarQuant_Common_DataType_H_