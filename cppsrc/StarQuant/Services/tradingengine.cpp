#include <future>
#include <atomic>
#include <Services/tradingengine.h>
#include <Common/config.h>
#include <Common/Util/util.h>
#include <Common/Logger/logger.h>
#include <Common/Data/datamanager.h>
#include <Common/Order/ordermanager.h>
#include <Common/Security/portfoliomanager.h>
#include <Services/Strategy/strategyservice.h>
#include <Services/Data/dataservice.h>
#include <Services/Brokerage/brokerageservice.h>
#include <Services/Api/apiservice.h>
//#include <Services/Interface/api_ws.h>

#include <fstream>
#include <iostream>
#include <string>

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
	}

	tradingengine::~tradingengine() {
		while ((pbrokerage && pbrokerage->isConnectedToBrokerage()) || (pmkdata && pmkdata->isConnectedToMarketDataFeed())) {
			msleep(100);
		}

		while (MICRO_SERVICE_NUMBER > 0) {
			msleep(100);
		}

		if (CConfig::instance()._msgq == MSGQ::NANOMSG)
			nn_term();
		else if (CConfig::instance()._msgq == MSGQ::ZMQ)
			;

		//printf("waiting for threads joined...\n");
		for (thread* t : threads) {
			if (t->joinable()) {
				t->join();
				delete t;
			}
		}

		//delete pmkdata;
		//delete pbrokerage;
		PRINT_TO_FILE("INFO:[%s,%d][%s]Exit trading engine.\n", __FILE__, __LINE__, __FUNCTION__);
	}

	int tradingengine::run() {
		if (gShutdown)
			return 1;
		try {
			auto fu1 = async(launch::async, check_gshutdown, true);

			if (mode == RUN_MODE::RECORD_MODE) {
				printf("RECORD_MODE\n");
				if (_broker == BROKERS::IB)
				{
					pmkdata = make_shared<IBBrokerage>();
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
				}
				else if (_broker == BROKERS::SINA)
				{
					pmkdata = make_shared<sinadatafeed>();
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
				}
			}
			else if (mode == RUN_MODE::REPLAY_MODE) {
				printf("REPLAY_MODE\n");
				threads.push_back(new thread(TickReplayService, CConfig::instance().filetoreplay,CConfig::instance()._tickinterval));
				threads.push_back(new thread(DataBoardService));
				pbrokerage = make_shared<paperbrokerage>(CConfig::instance()._brokerdelay);
				threads.push_back(new thread(BrokerageService, pbrokerage, 0));
					
				//threads.push_back(new thread(StrategyManagerService));
			}
			else if (mode == RUN_MODE::TRADE_MODE) {
				printf("TRADE_MODE\n");
				if (_broker == BROKERS::IB)
				{
					std::shared_ptr<IBBrokerage> tmp = std::make_shared<IBBrokerage>();
					pmkdata = tmp;
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
					pbrokerage = tmp;
					//pbrokerage = std::dynamic_pointer_cast<ibbrokerage>(pmkdata);		// dynamic_pointer_cast has issue about std::
					threads.push_back(new thread(BrokerageService, pbrokerage, 0));
				}
				else if (_broker == BROKERS::CTP)
				{
					pmkdata = make_shared<ctpdatafeed>();
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
					pbrokerage = make_shared<ctpbrokerage>();
					threads.push_back(new thread(BrokerageService, pbrokerage, 0));
					//threads.push_back(new thread(StrategyManagerService));
				}
				else if (_broker == BROKERS::TAP)
				{
					pmkdata = make_shared<Tapdatafeed>();
                    threads.push_back(new thread(MarketDataService, pmkdata, CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
					pbrokerage = make_shared<Tapbrokerage>();
					threads.push_back(new thread(BrokerageService, pbrokerage, 0));
					//threads.push_back(new thread(StrategyManagerService));



				}
				else if (_broker == BROKERS::SINA)
				{
					pmkdata = make_shared<sinadatafeed>();
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
					pbrokerage = make_shared<paperbrokerage>();
					threads.push_back(new thread(BrokerageService, pbrokerage, 0));
				}
				else if (_broker == BROKERS::GOOGLE)
				{
					pmkdata = make_shared<googledatafeed>();
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
					pbrokerage = make_shared<paperbrokerage>();
					threads.push_back(new thread(BrokerageService, pbrokerage, 0));
				}
				else if (_broker == BROKERS::PAPER)
				{
					pmkdata = make_shared<sinadatafeed>();
					threads.push_back(new thread(MarketDataService, pmkdata,
						CConfig::instance().ib_client_id++));
					threads.push_back(new thread(TickRecordingService));
					pbrokerage = make_shared<paperbrokerage>();
					threads.push_back(new thread(BrokerageService, pbrokerage, 0));
				}
			}
			else {
				PRINT_TO_FILE("EXIT:[%s,%d][%s]Mode %d doesn't exist.\n", __FILE__, __LINE__, __FUNCTION__, mode);
				return 1;
			}

			if (CConfig::instance()._msgq == MSGQ::NANOMSG) {
				// threads.push_back(new thread(ApiService));				// communicate with outside client monitor
			}
			// It seems that zmq interferes with interactive brokers
			//		triggering error code 509: Exception caught while reading socket - Resource temporarily unavailable
			//		so internally nanomsg is used.
			//		Zmq add a tick data relay service in ApiService class
			else if (CConfig::instance()._msgq == MSGQ::ZMQ) {
				//threads.push_back(new thread(ApiService));
			}
			else {
				//threads.push_back(new thread(Thread_API_WS));				// communicate with outside client monitor
			}

			//threads.push_back(new thread(DataBoardService));	// update databoard
			//threads.push_back(new thread(StrategyManagerService));

			fu1.get(); //block here
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
