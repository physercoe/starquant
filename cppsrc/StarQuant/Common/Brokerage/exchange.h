// TODO:	add margin requirements
//			add trading date/time
#ifndef _StarQuant_Common_Exchange_H_
#define _StarQuant_Common_Exchange_H_

#include <string>
using namespace std;

namespace StarQuant {
	enum Exchange {
		NYSE,
		HKSE,
		SSE,		// Shanghai Stock Exchange
		SZSE,		// Shenzhen Stock Exchange
		CFFEX,		// China Financial Futures Exchagne (CFFEX)
		SHFE,		// Shanghai Futurs Exchange
		FOREX
	};

	string openTime(const string& asofdate, Exchange exchange = Exchange::SSE);
	string closeTime(const string& asofdate, Exchange exchange = Exchange::SSE);
}

#endif  // _StarQuant_Common_Exchange_H_