// this is the format of naming the file and ifndef
// 
#ifndef _StarQuant_Common_AccountInfo_H_
#define _StarQuant_Common_AccountInfo_H_

#include <sstream>
#include <regex>
#include <Common/config.h>

namespace StarQuant
{
	struct AccountInfo {
	public:
		string AccountID;
		string AccountType;				//INDIVIDUAL
		
		double AvailableFunds = 0.0;
		double NetLiquidation = 0.0;

		double EquityWithLoanValue = 0.0;
		double PreviousDayEquityWithLoanValue = 0.0;

		double FullInitialMargin = 0.0;
		double FullMaintainanceMargin = 0.0;
		double Commission = 0.0;

		double BuyingPower = 0.0;
		double CashBalance = 0.0;

		double RealizedPnL = 0.0;
		double UnrealizedPnL = 0.0;

		template<class Archive>
		void serialize(Archive & ar) {
			ar(CEREAL_NVP(AccountID), CEREAL_NVP(AccountType),
				CEREAL_NVP(AvailableFunds), CEREAL_NVP(NetLiquidation),
				CEREAL_NVP(EquityWithLoanValue), CEREAL_NVP(PreviousDayEquityWithLoanValue),
				CEREAL_NVP(FullInitialMargin), CEREAL_NVP(FullMaintainanceMargin),
				CEREAL_NVP(BuyingPower), CEREAL_NVP(CashBalance),
				CEREAL_NVP(RealizedPnL), CEREAL_NVP(UnrealizedPnL));
		}

		string toJson(const std::regex* p) {
			std::stringstream ss;
			{
				cereal::JSONOutputArchive oarchive(ss);
				oarchive(cereal::make_nvp("accountinfo", *this));
			}
			string r = ss.str();
			if (p && !r.empty()) {
				string r = regex_replace(r, *p, "$1");
			}
			return r;
		}

		void setvalue(const string &key, const string &val, const string &currency) {
			if ((key == "AccountID") || (key == "AccountCode")) {
				AccountID = val;
			}
			else if (key == "AccountType") {
				AccountType = val;
			}
			else if (key == "AvailableFunds")  {				// available
				AvailableFunds = atof(val.c_str());
			}
			else if (key == "NetLiquidation") {				// balance
				NetLiquidation = atof(val.c_str());
			}
			else if (key == "EquityWithLoanValue") {
				EquityWithLoanValue = atof(val.c_str());
			}
			else if (key == "PreviousDayEquityWithLoanValue") {
				PreviousDayEquityWithLoanValue = atof(val.c_str());
			}
			else if (key == "FullInitialMargin") {
				FullInitialMargin = atof(val.c_str());
			}
			else if (key == "FullMaintainanceMargin") {			// margin
				FullMaintainanceMargin = atof(val.c_str());
			}
			else if (key == "BuyingPower") {
				BuyingPower = atof(val.c_str());
			}
			else if (key == "CashBalance") {
				CashBalance = atof(val.c_str());
			}
			else if (key == "RealizedPnL") {					// profit
				RealizedPnL = atof(val.c_str());
			}
			else if (key == "UnrealizedPnL") {					// profit
				UnrealizedPnL = atof(val.c_str());
			}
		}
	};
}

#endif // _StarQuant_Common_AccountInfo_H_
