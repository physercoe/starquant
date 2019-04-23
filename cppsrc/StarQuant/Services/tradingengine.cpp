#include <future>
#include <atomic>
#include <fstream>
#include <iostream>
#include <string>
#include <pthread.h> 
#include <signal.h>
#include <functional>

#include <Services/tradingengine.h>
#include <Common/datastruct.h>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/logger.h>
#include <Data/datamanager.h>
#include <Engine/IEngine.h>
#include <Engine/CtpMDEngine.h>
#include <Engine/CtpTDEngine.h>
// #include <Engine/TapMDEngine.h>
// #include <Engine/TapTDEngine.h>
#include <Engine/PaperTDEngine.h>
#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
//#include <Services/Strategy/strategyservice.h>
#include <Services/dataservice.h>



namespace StarQuant
{
	//std::atomic<bool> gShutdown{ false };

	// extern std::atomic<bool> gShutdown;



	extern atomic<uint64_t> MICRO_SERVICE_NUMBER;
	std::atomic<bool> gShutdown = false;


	void startengine(shared_ptr<IEngine> pe){
		pe->start();
	}
	tradingengine::tradingengine() {
		CConfig::instance();
		DataManager::instance();
		OrderManager::instance();
		PortfolioManager::instance();
		_broker = CConfig::instance()._broker;
		mode = CConfig::instance()._mode;
		if(logger == nullptr){
			logger = SQLogger::getLogger("SYS");
		}
		// if (IEngine::msgq_send_ == nullptr){
		// 	IEngine::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		// }
		if (CMsgqEMessenger::msgq_send_ == nullptr){
		 	CMsgqEMessenger::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERPUB_URL);
		}		
		LOG_DEBUG(logger,CConfig::instance().SERVERPULL_URL);

		//msg_pull_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PULL, CConfig::instance().SERVERPULL_URL);
		//msg_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERSUB_URL);
		//client_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().API_PORT);
		//md_msg_pub_=  std::make_shared<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().API_ZMQ_DATA_PORT,false);
		msg_relay_ = std::make_unique<CMsgqRMessenger>(CConfig::instance().SERVERPULL_URL,CConfig::instance().SERVERSUB_URL);
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

	void tradingengine::ConsoleControlHandler(int sig) {
		gShutdown = true;
		PRINT_SHUTDOWN_MESSAGE;
		//throw runtime_error("crl c");
	}

	// std::atomic<bool>* tradingengine::setconsolecontrolhandler(void) {
	// 	signal(SIGINT, ConsoleControlHandler);
	// 	signal(SIGPWR, ConsoleControlHandler);
	// 	return &gShutdown;
	// }

	int tradingengine::check_gshutdown(bool force) {		
		signal(SIGINT, tradingengine::ConsoleControlHandler);
		signal(SIGPWR, tradingengine::ConsoleControlHandler);
		//atomic_bool* g = setconsolecontrolhandler();
		while (!gShutdown) {
			msleep(1 * 1000);
		}
		// ctrl-c
		if (force) {
			throw runtime_error("Throw an exception to trigger shutdown");
		}
		return 0;
	}



	int tradingengine::run() {
		if (gShutdown)
			return 1;
		try {
			auto fu1 = async(launch::async, std::bind(&tradingengine::check_gshutdown,this,std::placeholders::_1), true);
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
					// std::shared_ptr<IEngine> tapmdengine = make_shared<TapMDEngine>();
					// std::shared_ptr<IEngine> taptdengine = make_shared<TapTDEngine>();
					// threads_.push_back(new std::thread(startengine,tapmdengine));
					// threads_.push_back(new std::thread(startengine,taptdengine));
					// pengines_.push_back(tapmdengine);
					// pengines_.push_back(taptdengine);		
				}
				if (CConfig::instance()._loadapi["XTP"]){
				}
				if (CConfig::instance()._loadapi["PAPER"]){
					std::shared_ptr<IEngine> papertdengine = make_shared<PaperTDEngine>();
					threads_.push_back(new std::thread(startengine,papertdengine));
					pengines_.push_back(papertdengine);
				}				
			}
			else {
				LOG_ERROR(logger,"Mode doesn't exist,exit.");				
				return 1;
			}
			// set thread affinity
			//engine thread
			if (CConfig::instance().cpuaffinity){
				int num_cpus = std::thread::hardware_concurrency();
				for (int i = 0; i< threads_.size();i ++){
					cpu_set_t cpuset;
					CPU_ZERO(&cpuset);
					CPU_SET(i%num_cpus,&cpuset);
					int rc = pthread_setaffinity_np(threads_[i]->native_handle(),sizeof(cpu_set_t),&cpuset);
					if (rc != 0) {
						std::cerr << "Error calling pthread_setaffinity_np: " << rc << "\n";
					}
				}
				//main thread
				cpu_set_t cpuset;
				CPU_ZERO(&cpuset);
				CPU_SET(threads_.size()%num_cpus,&cpuset);
				int rc = pthread_setaffinity_np(pthread_self(),sizeof(cpu_set_t),&cpuset);
					if (rc != 0) {
						std::cerr << "Error calling pthread_setaffinity_np: " << rc << "\n";
				}	
			}
			while(!gShutdown){
				msg_relay_->relay();
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
