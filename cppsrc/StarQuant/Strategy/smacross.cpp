#include <Strategy/smacross.h>

namespace StarQuant
{
	void SmaCross::initialize() {
		order_time = -10;
		buy_sell = true;
		ordercount = 0;
		sid = 1;
	}
	
	void SmaCross::OnTick(Tick& k) {
		tickarray.push_back(k);
		//printf("SMA strat OnTick: [%s]\n", k.fullsymbol_.c_str());
//		if (hmsf2inttime(k.time_) - order_time > 1000) {
			/*auto o = std::make_shared<Order>();
			o->orderType = "LMT";
			o->fullSymbol = "IF1710";
			o->orderSize = buy_sell ? 2 : -2;
			o->limitPrice = 3868.00;

			buy_sell = !buy_sell;
			order_time = k.time_;
			SendOrder(o);*/
//		}
		
		if( ordercount <= 4){

			if ((k.price_ < 16000) &&(buy_sell)) {
				auto o = std::make_shared<Order>();
				o->orderType = OrderType::OT_Market;
				o->fullSymbol = k.fullsymbol_;
				o->orderSize = 1;
				o->orderFlag = OrderFlag:: OF_OpenPosition;
				o->source = sid;
				//order_time = k.time_;
				SendOrder(o);
				ordercount++;
				buy_sell = false;
				return;

				// auto o_stop = std::make_shared<Order>();
				// o_stop->orderType = "STPLMT";
				// o_stop->fullSymbol = k.fullsymbol_;
				// o_stop->orderSize = -1;
				// o_stop->stopPrice = 15550;
				// o_stop->orderFlag = OrderFlag:: OF_ClosePosition;
				// //order_time = k.time_;
				// SendOrder(o_stop);			
				// ordercount++;
				// buy_sell = true;


			}
			if ((k.price_ > 15700) &&(! buy_sell)) {
			auto o_close = std::make_shared<Order>();
			o_close->source = sid;
			o_close->orderType = OrderType::OT_Market;
			o_close->fullSymbol = k.fullsymbol_;
			o_close->orderSize = -1;
			o_close->orderFlag = OrderFlag:: OF_ClosePosition;
			SendOrder(o_close);
			ordercount++;
			buy_sell = true;
			return;


			}
		}








	}

	void SmaCross::OnGeneralMessage(string& msg) {
		printf("SMA strat general msg: [%s]\n", msg.c_str());
	}
}
