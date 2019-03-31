#ifndef _StarQuant_Common_CurrencyType_H_
#define _StarQuant_Common_CurrencyType_H_

#include <string>

namespace StarQuant {
	enum CurrencyType {
		USD,
		AUD,
		CAD,
		CHF,
		EUR,
		GBP,
		HKD,
		JPY,
		MXN,
		NZD,
		SEK
	};

	const std::string CurrencyTypeString[] = {
		"USD",
		"AUD",
		"CAD",
		"CHF",
		"EUR",
		"GBP",
		"HKD",
		"JPY",
		"MXN",
		"NZD",
		"SEK"
	};
}

#endif  // _StarQuant_Common_CurrencyType_H_