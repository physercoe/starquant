#ifndef _StarQuant_Engine_TradingEngine_H_
#define _StarQuant_Engine_TradingEngine_H_

#include <thread>
#include <memory>
#include <Common/config.h>
#include <Engine/IEngine.h>
#include <Engine/CtpMDEngine.h>
#include <Engine/CtpTDEngine.h>
using namespace std;

namespace StarQuant
{
	void startengine(shared_ptr<IEngine> pe);

	class DLL_EXPORT_IMPORT tradingengine {
		RUN_MODE mode = RUN_MODE::TRADE_MODE; //RUN_MODE::REPLAY_MODE;
//		RUN_MODE mode = RUN_MODE::RECORD_MODE; //RUN_MODE::REPLAY_MODE;
		BROKERS _broker = BROKERS::PAPER;
		vector<std::thread*> threads_;
		//thread* tmd;
		//thread* ttd;
		vector<std::shared_ptr<IEngine>> pengines_; 
		//std::shared_ptr<IEngine> ctpmdengine;
		//std::shared_ptr<IEngine> ctptdengine;
		//CtpTDEngine ctptdengine;
		// CtpMDEngine ctpmdengine;  
		// CtpTDEngine ctptdengine;
		// TapMDEngine tapmdengine;  
		// TapTDEngine taptdengine;
		// std::unique_ptr<CMsgq> client_msg_pair_;
		// std::shared_ptr<CMsgq> md_msg_pub_;
		std::shared_ptr<SQLogger> logger;
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
