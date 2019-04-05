#ifndef __StarQuant_Data_Tick_H_
#define __StarQuant_Data_Tick_H_

#include <string>
#include <Common/config.h>
//#include <Common/Data/datatype.h>
using namespace std;

namespace StarQuant {
	class DLL_EXPORT_IMPORT Tick {
	public:
		Tick() 	: fullsymbol_("")
			, time_("")
			, msgtype_(MSG_TYPE::MSG_TYPE_Trade)
			, price_(0.0)
			, size_(0)
			, depth_(1)		// default is L1 or 1
			, source_("0")
			, destination_("0")
		{
		}

		Tick(const string& s) :fullsymbol_(s) {}
		~Tick() {
		}

		string fullsymbol_;
		string time_;
		MSG_TYPE msgtype_;
		double price_;
		int size_;
		int depth_;
		string source_;
		string destination_;

		virtual string serialize() const;
	};


	class DLL_EXPORT_IMPORT Tick_L1 : public Tick {
	public:
		Tick_L1() : Tick()
			, bidprice_L1_(0.0)
			, bidsize_L1_(0)
			, askprice_L1_(0.0)
			, asksize_L1_(0)
			, open_interest(0)
			, open_(0.0)
			, high_(0.0)
			, low_(0.0)
			, pre_close_(0.0)
			, upper_limit_price_(0.0)
			, lower_limit_price_(0.0)
		{
			msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L1;
			depth_ = 1;
		}

		Tick_L1(const string& s) : Tick(s) {}
		~Tick_L1() {}

		// assuming base Tick class stores trade/last data
		// here it adds bid/ask data
		double bidprice_L1_;
		int bidsize_L1_;
		double askprice_L1_;
		int asksize_L1_;
		int open_interest;
		double open_;
		double high_;
		double low_;
		double pre_close_;
		double upper_limit_price_;
		double lower_limit_price_;

		virtual string serialize() const;		// overriding
	};


	class DLL_EXPORT_IMPORT Tick_L5 : public Tick {
	public:
		Tick_L5() : Tick()
			, bidprice_L1_(0.0)
			, bidsize_L1_(0)
			, askprice_L1_(0.0)
			, asksize_L1_(0)
			, bidprice_L2_(0.0)
			, bidsize_L2_(0)
			, askprice_L2_(0.0)
			, asksize_L2_(0)
			, bidprice_L3_(0.0)
			, bidsize_L3_(0)
			, askprice_L3_(0.0)
			, asksize_L3_(0)
			, bidprice_L4_(0.0)
			, bidsize_L4_(0)
			, askprice_L4_(0.0)
			, asksize_L4_(0)
			, bidprice_L5_(0.0)
			, bidsize_L5_(0)
			, askprice_L5_(0.0)
			, asksize_L5_(0)
			, open_interest(0)
			, open_(0.0)
			, high_(0.0)
			, low_(0.0)
			, pre_close_(0.0)
			, upper_limit_price_(0.0)
			, lower_limit_price_(0.0)
		{
			msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L5;
			depth_ = 5;
		}

		Tick_L5(const string& s) : Tick(s) {}
		~Tick_L5() {}
		double bidprice_L1_;
		int bidsize_L1_;
		double askprice_L1_;
		int asksize_L1_;
		double bidprice_L2_;
		int bidsize_L2_;
		double askprice_L2_;
		int asksize_L2_;
		double bidprice_L3_;
		int bidsize_L3_;
		double askprice_L3_;
		int asksize_L3_;
		double bidprice_L4_;
		int bidsize_L4_;
		double askprice_L4_;
		int asksize_L4_;
		double bidprice_L5_;
		int bidsize_L5_;
		double askprice_L5_;
		int asksize_L5_;				
		int open_interest;
		double open_;
		double high_;
		double low_;
		double pre_close_;
		double upper_limit_price_;
		double lower_limit_price_;

		virtual string serialize() const;		// overriding
	};
}

#endif  // __StarQuant_Common_Tick_H_
