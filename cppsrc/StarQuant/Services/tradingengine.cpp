#include <future>
#include <atomic>
#include <fstream>
#include <iostream>
#include <string>

#include <Services/tradingengine.h>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/logger.h>
#include <Data/datamanager.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
//#include <Services/Strategy/strategyservice.h>
#include <Services/dataservice.h>



namespace StarQuant
{
	extern std::atomic<bool> gShutdown;
	extern atomic<uint64_t> MICRO_SERVICE_NUMBER;

	tradingengine::tradingengine() {
		CConfig::instance();
		DataManager::instance();
		OrderManager::instance();
		PortfolioManager::instance();
		// TODO: check if there is an StarQuant instance running already
		_broker = CConfig::instance()._broker;
		mode = CConfig::instance()._mode;

		//client_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().API_PORT);
		//md_msg_pub_=  std::make_shared<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().API_ZMQ_DATA_PORT,false);
	}

	tradingengine::~tradingengine() {
		for (auto e: pengines_){
			while ( (e != nullptr) && (e->estate_ != STOP) ){
				msleep(100);
			}
		}
		// while ((pbrokerage_ib && pbrokerage_ib->isConnectedToBrokerage()) || (pmkdata_ib && pmkdata_ib->isConnectedToMarketDataFeed())) {
		// 	msleep(100);
		// }
		// while ((pbrokerage_ctp && pbrokerage_ctp->isConnectedToBrokerage()) || (pmkdata_ctp && pmkdata_ctp->isConnectedToMarketDataFeed())) {
		// 	msleep(100);
		// }
		// while ((pbrokerage_tap && pbrokerage_tap->isConnectedToBrokerage()) || (pmkdata_tap && pmkdata_tap->isConnectedToMarketDataFeed())) {
		// 	msleep(100);
		// }
		// while ((pbrokerage_xtp && pbrokerage_xtp->isConnectedToBrokerage()) || (pmkdata_xtp && pmkdata_xtp->isConnectedToMarketDataFeed())) {
		// 	msleep(100);
		// }

		while (MICRO_SERVICE_NUMBER > 0) {
			msleep(100);
		}
		if (CConfig::instance()._msgq == MSGQ::NANOMSG)
			nn_term();
		for (auto& t : threads_){
			if (t.joinable())
				t.join();
		}
		PRINT_TO_FILE("INFO:[%s,%d][%s]Exit trading engine.\n", __FILE__, __LINE__, __FUNCTION__);
	}

	int tradingengine::run() {
		if (gShutdown)
			return 1;
		try {
			auto fu1 = async(launch::async, check_gshutdown, true);
			if (mode == RUN_MODE::RECORD_MODE) {
				printf("RECORD_MODE\n");
				//threads_.push_back(new thread(TickRecordingService));
				}
			else if (mode == RUN_MODE::REPLAY_MODE) {
				printf("REPLAY_MODE\n");
				// threads_.push_back(new thread(TickReplayService, CConfig::instance().filetoreplay,CConfig::instance()._tickinterval));
				// threads_.push_back(new thread(DataBoardService));
				// //threads_.push_back(new thread(StrategyManagerService));
			}
			else if (mode == RUN_MODE::TRADE_MODE) {
				printf("TRADE_MODE\n");
				//threads_.push_back(new thread(TickRecordingService));
				if (CConfig::instance()._loadapi["CTP"]){
					std::shared_ptr<IEngine> ctpmdengine = make_shared<CtpMDEngine>();
					std::shared_ptr<IEngine> ctptdengine = make_shared<CtpTDEngine>();
					threads_.push_back(std::thread(&CtpMDEngine::start,ctpmdengine));
					threads_.push_back(std::thread(&CtpTDEngine::start,ctptdengine));
					pengines_.push_back(ctpmdengine);
					pengines_.push_back(ctptdengine);
					//threads_.push_back(std::thread(&CtpTDEngine::start,std::ref(ctptdengine)));
				}
				if (CConfig::instance()._loadapi["TAP"]){
					std::shared_ptr<IEngine> tapmdengine = make_shared<TapMDEngine>();
					std::shared_ptr<IEngine> taptdengine = make_shared<TapTDEngine>();
					threads_.push_back(std::thread(&TapMDEngine::start,tapmdengine));
					threads_.push_back(std::thread(&TapTDEngine::start,taptdengine));
					pengines_.push_back(tapmdengine);
					pengines_.push_back(taptdengine);		
				}
				if (CConfig::instance()._loadapi["XTP"]){
				}
			}
			else {
				PRINT_TO_FILE("EXIT:[%s,%d][%s]Mode %d doesn't exist.\n", __FILE__, __LINE__, __FUNCTION__, mode);
				return 1;
			}
			fu1.get(); //block here
			for (auto e: pengines_){
				e->stop();
			}
		}
		catch (exception& e) {
			printf("Thanks for using StarQuant. GoodBye: %s\n", e.what());
		}
		catch (...) {
			printf("StarQuant terminated in error!\n");
		}
		return 0;
	}

	bool tradingengine::live() const {
		return gShutdown == true;
	}
}
