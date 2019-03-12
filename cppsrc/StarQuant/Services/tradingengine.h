#ifndef _StarQuant_Engine_TradingEngine_H_
#define _StarQuant_Engine_TradingEngine_H_

#include <thread>
#include <memory>
#include <Common/config.h>
#include <Common/Brokerage/brokerage.h>
#include <Brokers/Sina/sinadatafeed.h>
#include <Brokers/Google/googledatafeed.h>
#include <Brokers/Paper/paperdatafeed.h>
#include <Brokers/Ctp/ctpdatafeed.h>
#include <Brokers/Tap/tapdatafeed.h>
#include <Brokers/Paper/paperbrokerage.h>
#include <Brokers/Ctp/ctpbrokerage.h>
#include <Brokers/Tap/tapbrokerage.h>
#include <Brokers/IB/ibbrokerage.h>
#include <Common/Data/marketdatafeed.h>

using namespace std;

namespace StarQuant
{
	class DLL_EXPORT_IMPORT tradingengine {
		RUN_MODE mode = RUN_MODE::TRADE_MODE; //RUN_MODE::REPLAY_MODE;
//		RUN_MODE mode = RUN_MODE::RECORD_MODE; //RUN_MODE::REPLAY_MODE;
		BROKERS _broker = BROKERS::GOOGLE;
//		BROKERS _broker = BROKERS::TAP;
		shared_ptr<marketdatafeed> pmkdata;
		shared_ptr<brokerage> pbrokerage;

		vector<thread*> threads;

	public:

		int run();
		bool live() const;

		tradingengine();
		~tradingengine();

		// https://mail.python.org/pipermail/cplusplus-sig/2004-July/007472.html
		// http://stackoverflow.com/questions/10142417/boostpython-compilation-fails-because-copy-constructor-is-private
		// For Boost::Python
		tradingengine(tradingengine&&) = delete;
		tradingengine(const tradingengine&) = delete;
		tradingengine& operator=(tradingengine&&) = delete;
		tradingengine& operator=(const tradingengine&) = delete;
	};
}

#endif // _StarQuant_Engine_TradingEngine_H_
