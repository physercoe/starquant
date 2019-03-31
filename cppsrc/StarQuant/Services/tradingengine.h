#ifndef _StarQuant_Engine_TradingEngine_H_
#define _StarQuant_Engine_TradingEngine_H_

#include <thread>
#include <memory>
#include <Common/config.h>
#include <Engine/IEngine.h>
#include <Engine/CtpMDEngine.h>
#include <Engine/CtpTDEngine.h>
#include <Engine/TapMDEngine.h>
#include <Engine/TapTDEngine.h>

using namespace std;

namespace StarQuant
{
	class DLL_EXPORT_IMPORT tradingengine {
		RUN_MODE mode = RUN_MODE::TRADE_MODE; //RUN_MODE::REPLAY_MODE;
//		RUN_MODE mode = RUN_MODE::RECORD_MODE; //RUN_MODE::REPLAY_MODE;
		BROKERS _broker = BROKERS::PAPER;
		vector<std::thread> threads_;
		vector<std::shared_ptr<IEngine>> pengines_; 
		// CtpMDEngine ctpmdengine;  
		// CtpTDEngine ctptdengine;
		// TapMDEngine tapmdengine;  
		// TapTDEngine taptdengine;
		// shared_ptr<marketdatafeed> pmkdata_ib;
		// shared_ptr<brokerage> pbrokerage_ib;
		// shared_ptr<marketdatafeed> pmkdata_ctp;
		// shared_ptr<brokerage> pbrokerage_ctp;
		// shared_ptr<marketdatafeed> pmkdata_tap;
		// shared_ptr<brokerage> pbrokerage_tap;
		// shared_ptr<marketdatafeed> pmkdata_xtp;
		// shared_ptr<brokerage> pbrokerage_xtp;
		// shared_ptr<marketdatafeed> pmkdata_sina;
		// shared_ptr<brokerage> pbrokerage_sina;
		// shared_ptr<marketdatafeed> pmkdata_google;
		// shared_ptr<brokerage> pbrokerage_google;

		// std::unique_ptr<CMsgq> client_msg_pair_;
		// std::shared_ptr<CMsgq> md_msg_pub_;

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
