#ifndef _StarQuant_Strategy_SmaCross_H_
#define _StarQuant_Strategy_SmaCross_H_

#include <Strategy/strategybase.h>
#include <atomic>

namespace StarQuant {
	class SmaCross : public StrategyBase {
		public:
			virtual void initialize();
			virtual void OnTick(Tick& k);
			virtual void OnGeneralMessage(string& msg);
		private:
			int order_time;
			bool buy_sell;
			vector<Tick> tickarray;
			int ordercount;
			int sid;
	};
}


#endif
