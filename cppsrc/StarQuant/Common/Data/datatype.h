// pass through all the data types
// take trade price and trade size, aggregate into bars and then propogate
#ifndef _StarQuant_Common_DataType_H_
#define _StarQuant_Common_DataType_H_

#include <string>

namespace StarQuant {
	enum DataType : int {

// tick,bar数据类型		
		DT_Tick_L1 = 0,
		DT_Tick_L5 = 1,
		DT_Tick_L20 = 2,
		DT_Bar_1min = 3,
		DT_Bar_5min = 4,
		DT_Bar_15min = 5,
		DT_Bar_1h = 6,
		DT_Bar_1d = 7,
		DT_Bar_1w = 8,
		DT_Bar_1m = 9,
		DT_Trade = 10,			
		DT_Bid = 11,
		DT_Ask = 12,
		DT_Full = 13,
		DT_BidPrice = 14,
		DT_BidSize = 15,
		DT_AskPrice = 16,
		DT_AskSize = 17,
		DT_TradePrice = 18,
		DT_TradeSize = 19,
		DT_OpenPrice = 20,
		DT_HighPrice = 21,
		DT_LowPrice = 22,
		DT_ClosePrice = 23,
		DT_Volume = 24,
		DT_OpenInterest = 25,
		DT_Bar = 26,
		DT_Account = 27,
		DT_Position = 28
	};

	/// xxxTypeString is the string name of xxxType
	const std::string DataTypeString[] = {
		"Tick_L1",
		"Tick_L5",
		"Tick_L20",
		"Bar_1min",
		"Bar_5min",
		"Bar_15min",
		"Bar_1h",
		"Bar_1d",
		"Bar_1w",
		"Bar_1m",
		"Trade",
		"Bid",
		"Ask",
		"Full",	
		"BidPrice",
		"BidSize",
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
		"Position"		
	};
}

#endif  // _StarQuant_Common_DataType_H_