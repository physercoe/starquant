#include <Common/config.h>
#include <Data/tick.h>

namespace StarQuant
{
	string Tick::serialize() const
	{
		// TODO: which one is more efficient?
		//char msg[128] = {};
		//sprintf(msg, "%s|%d|%.2f", fullsymbol_.c_str(), msgtype_, price_, size_, depth_);
		//return msg;

		string s;
		s = to_string(msgtype_) 
			+ SERIALIZATION_SEPARATOR +	fullsymbol_ 
			+ SERIALIZATION_SEPARATOR + time_
			+ SERIALIZATION_SEPARATOR + to_string(price_)
			+ SERIALIZATION_SEPARATOR + to_string(size_);
		return s;
	}


	string Tick_L1::serialize() const
	{

		string s;
		s = to_string(msgtype_)
			+ SERIALIZATION_SEPARATOR +	fullsymbol_
			+ SERIALIZATION_SEPARATOR + time_
			+ SERIALIZATION_SEPARATOR + to_string(price_)
			+ SERIALIZATION_SEPARATOR + to_string(size_)
			+ SERIALIZATION_SEPARATOR + to_string(bidprice_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(bidsize_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(askprice_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(asksize_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(open_interest)
			+ SERIALIZATION_SEPARATOR + to_string(open_)
			+ SERIALIZATION_SEPARATOR + to_string(high_)
			+ SERIALIZATION_SEPARATOR + to_string(low_)
			+ SERIALIZATION_SEPARATOR + to_string(pre_close_)
			+ SERIALIZATION_SEPARATOR + to_string(upper_limit_price_)
			+ SERIALIZATION_SEPARATOR + to_string(lower_limit_price_);
		return s;
	}




	string Tick_L5::serialize() const
	{

		string s;
		s = to_string(msgtype_)
			+ SERIALIZATION_SEPARATOR +	fullsymbol_
			+ SERIALIZATION_SEPARATOR + time_
			+ SERIALIZATION_SEPARATOR + to_string(price_)
			+ SERIALIZATION_SEPARATOR + to_string(size_)
			+ SERIALIZATION_SEPARATOR + to_string(bidprice_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(bidsize_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(askprice_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(asksize_L1_)
			+ SERIALIZATION_SEPARATOR + to_string(bidprice_L2_)
			+ SERIALIZATION_SEPARATOR + to_string(bidsize_L2_)
			+ SERIALIZATION_SEPARATOR + to_string(askprice_L2_)
			+ SERIALIZATION_SEPARATOR + to_string(asksize_L2_)
			+ SERIALIZATION_SEPARATOR + to_string(bidprice_L3_)
			+ SERIALIZATION_SEPARATOR + to_string(bidsize_L3_)
			+ SERIALIZATION_SEPARATOR + to_string(askprice_L3_)
			+ SERIALIZATION_SEPARATOR + to_string(asksize_L3_)	
			+ SERIALIZATION_SEPARATOR + to_string(bidprice_L4_)
			+ SERIALIZATION_SEPARATOR + to_string(bidsize_L4_)
			+ SERIALIZATION_SEPARATOR + to_string(askprice_L4_)
			+ SERIALIZATION_SEPARATOR + to_string(asksize_L4_)		
			+ SERIALIZATION_SEPARATOR + to_string(bidprice_L5_)
			+ SERIALIZATION_SEPARATOR + to_string(bidsize_L5_)
			+ SERIALIZATION_SEPARATOR + to_string(askprice_L5_)
			+ SERIALIZATION_SEPARATOR + to_string(asksize_L5_)											
			+ SERIALIZATION_SEPARATOR + to_string(open_interest)
			+ SERIALIZATION_SEPARATOR + to_string(open_)
			+ SERIALIZATION_SEPARATOR + to_string(high_)
			+ SERIALIZATION_SEPARATOR + to_string(low_)
			+ SERIALIZATION_SEPARATOR + to_string(pre_close_)
			+ SERIALIZATION_SEPARATOR + to_string(upper_limit_price_)
			+ SERIALIZATION_SEPARATOR + to_string(lower_limit_price_);

		return s;
	}
}
