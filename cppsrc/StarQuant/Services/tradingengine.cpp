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
#include <Engine/IEngine.h>
#include <Engine/CtpMDEngine.h>
#include <Engine/CtpTDEngine.h>
#include <Engine/TapMDEngine.h>
#include <Engine/TapTDEngine.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
//#include <Services/Strategy/strategyservice.h>
#include <Services/dataservice.h>



namespace StarQuant
{
	extern std::atomic<bool> gShutdown;
	extern atomic<uint64_t> MICRO_SERVICE_NUMBER;

	void startengine(shared_ptr<IEngine> pe){
		pe->start();
	}
	tradingengine::tradingengine() {
		CConfig::instance();
		//cout<<"config done "<<endl;
		DataManager::instance();
		OrderManager::instance();
		PortfolioManager::instance();
		// TODO: check if there is an StarQuant instance running already
		_broker = CConfig::instance()._broker;
		mode = CConfig::instance()._mode;
		if(logger == nullptr){
			logger = SQLogger::getLogger("SYS");
		}
		if (IEngine::msgq_send_ == nullptr){
			IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		}
		//CtpTDEngine ctptdengine;
		//cout<<"trading engine inited "<<endl;
		//client_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().API_PORT);
		//md_msg_pub_=  std::make_shared<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().API_ZMQ_DATA_PORT,false);
	}

	tradingengine::~tradingengine() {		
		for (auto& e: pengines_){
			while ( (e != nullptr) && (e->estate_ != STOP) ){
				e->stop();
				msleep(100);
			}
		}
		while (MICRO_SERVICE_NUMBER > 0) {
			msleep(100);
		}
		if (CConfig::instance()._msgq == MSGQ::NANOMSG)
			nn_term();
		for (thread* t : threads_){
			if (t->joinable()){
				t->join();
				delete t;
			}	
		}
		LOG_DEBUG(logger,"Exit trading engine");		
	}

	int tradingengine::run() {
		if (gShutdown)
			return 1;
		try {
			auto fu1 = async(launch::async, check_gshutdown, true);
			if (mode == RUN_MODE::RECORD_MODE) {
				LOG_INFO(logger,"RECORD_MODE");
				//threads_.push_back(new thread(TickRecordingService));
				}
			else if (mode == RUN_MODE::REPLAY_MODE) {
				LOG_INFO(logger,"REPLAY_MODE");
				// threads_.push_back(new thread(TickReplayService, CConfig::instance().filetoreplay,CConfig::instance()._tickinterval));
				// threads_.push_back(new thread(DataBoardService));
				// //threads_.push_back(new thread(StrategyManagerService));
			}
			else if (mode == RUN_MODE::TRADE_MODE) {
				LOG_INFO(logger,"TRADE_MODE");
					//threads_.push_back(new thread(TickRecordingService));
				if (CConfig::instance()._loadapi["CTP"]){
					std::shared_ptr<IEngine> ctpmdengine = make_shared<CtpMDEngine>();
					std::shared_ptr<IEngine> ctptdengine = make_shared<CtpTDEngine>();
					threads_.push_back(new std::thread(startengine,ctpmdengine));
					threads_.push_back(new std::thread(startengine,ctptdengine));
					pengines_.push_back(ctpmdengine);
					pengines_.push_back(ctptdengine);
				}
				if (CConfig::instance()._loadapi["TAP"]){
					std::shared_ptr<IEngine> tapmdengine = make_shared<TapMDEngine>();
					std::shared_ptr<IEngine> taptdengine = make_shared<TapTDEngine>();
					threads_.push_back(new std::thread(startengine,tapmdengine));
					threads_.push_back(new std::thread(startengine,taptdengine));
					pengines_.push_back(tapmdengine);
					pengines_.push_back(taptdengine);		
				}
				if (CConfig::instance()._loadapi["XTP"]){
				}
			}
			else {
				LOG_ERROR(logger,"Mode doesn't exist,exit.");				
				return 1;
			}
			fu1.get(); 
		}
		catch (exception& e) {
			LOG_DEBUG(logger,e.what());
		}
		catch (...) {
			LOG_ERROR(logger,"StarQuant terminated in error!");
		}
		for (const auto& e: pengines_){
			e->stop();
		}
		return 0;
	}

	bool tradingengine::live() const {
		return gShutdown == true;
	}
}
