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
#include <Trade/riskmanager.h>
//#include <Services/Strategy/strategyservice.h>
#include <Services/dataservice.h>



namespace StarQuant
{

    extern std::atomic<bool> gShutdown;
    extern Except_frame g_except_stack;


    extern atomic<uint64_t> MICRO_SERVICE_NUMBER;



    void startengine(shared_ptr<IEngine> pe){
        pe->start();
    }

    tradingengine::tradingengine() {
        CConfig::instance();
        DataManager::instance();
        OrderManager::instance();
        PortfolioManager::instance();
        RiskManager::instance();
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
            msleep(100);
        }
        if (CMsgqRMessenger::msgq_send_ == nullptr){
             CMsgqRMessenger::msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().SERVERSUB_URL);
            msleep(100);
        }				
        msg_relay_ = std::make_unique<CMsgqRMessenger>(CConfig::instance().SERVERPULL_URL);
        msleep(100);
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
            else{
                // pthread_cancel(t->native_handle());
                // delete t;
            }	
        }
        LOG_DEBUG(logger,"Exit trading engine");		
    }


    int tradingengine::cronjobs(bool force) {	
    //set console handler		
        signal(SIGINT, ConsoleControlHandler);
        signal(SIGPWR, ConsoleControlHandler);

        time_t timer;
        struct tm tm_info;
        
    //cronjobs:
    //check gshutdown
        while (!gShutdown) {
            msleep(1 * 1000);
    // switch day, at 20:30 everyday,  reset td engine, needconfirmation
            time(&timer);
            tm_info = *localtime(&timer);            
            // at weekend do nothing 0=sunday 6=saturday
            if ((tm_info.tm_wday == 0) || (tm_info.tm_wday == 6)){
                continue;
            } 
            if (tm_info.tm_hour == 20 && tm_info.tm_min == 30 && tm_info.tm_sec == 0){
                std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_SWITCH_TRADING_DAY);
                msg_relay_->send(pmsg);
                RiskManager::instance().switchday();
            }
    // auto connect at 8:45, 1:15, 20:45
            if (tm_info.tm_hour == 8 && tm_info.tm_min == 45 && tm_info.tm_sec == 0){
                std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_ENGINE_CONNECT);
                msg_relay_->send(pmsg);
            }
            if (tm_info.tm_hour == 13 && tm_info.tm_min == 15 && tm_info.tm_sec == 0){
                std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_ENGINE_CONNECT);
                msg_relay_->send(pmsg);
            }
            if (tm_info.tm_hour == 20 && tm_info.tm_min == 45 && tm_info.tm_sec == 0){

                std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_ENGINE_CONNECT);
                msg_relay_->send(pmsg);
            }
    // auto reset at 16:00 ,2:35
            if (tm_info.tm_hour == 16 && tm_info.tm_min == 0 && tm_info.tm_sec == 0){
                std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_ENGINE_RESET);
                msg_relay_->send(pmsg);
            }
            if (tm_info.tm_hour == 2 && tm_info.tm_min == 35 && tm_info.tm_sec == 0){
                std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_ENGINE_RESET);
                msg_relay_->send(pmsg);
            }
    // send timer msg to all engine		
            std::shared_ptr<MsgHeader> pmsg = make_shared<MsgHeader>(DESTINATION_ALL,"0",MSG_TYPE_TIMER);
            msg_relay_->send(pmsg);
    //flow count reset
            RiskManager::instance().resetflow();


        }
        // ctrl-c
        if (force) {
            throw runtime_error("ctrl-c triggered shutdown");
        }
        return 0;
    }



    int tradingengine::run() {
        if (gShutdown)
            return 1;
        // sigsegv sig backtrace
        g_except_stack.flag = sigsetjmp(g_except_stack.env,1);
        if (!g_except_stack.isDef()){
            signal(SIGSEGV,recvSignal);
            try {
                auto fu1 = async(launch::async, std::bind(&tradingengine::cronjobs,this,std::placeholders::_1), true);
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
                    for (auto iter = CConfig::instance()._gatewaymap.begin(); iter != CConfig::instance()._gatewaymap.end(); iter++){
                        if (iter->second.api == "CTP.TD"){
                            std::shared_ptr<IEngine> ctptdengine = make_shared<CtpTDEngine>(iter->first);
                            threads_.push_back(new std::thread(startengine,ctptdengine));
                            pengines_.push_back(ctptdengine);						
                        }
                        else if (iter->second.api == "CTP.MD"){
                            std::shared_ptr<IEngine> ctpmdengine = make_shared<CtpMDEngine>();
                            pengines_.push_back(ctpmdengine);
                            threads_.push_back(new std::thread(startengine,ctpmdengine));					
                        }
                        else if (iter->second.api == "PAPER.TD"){
                            std::shared_ptr<IEngine> papertdengine = make_shared<PaperTDEngine>();
                            threads_.push_back(new std::thread(startengine,papertdengine));
                            pengines_.push_back(papertdengine);				
                        }
                        else if (iter->second.api == "TAP.TD"){
                            //  TODO: finish later
                        }					
                        else if (iter->second.api == "TAP.MD"){
                            //  TODO: finish later
                        }
                        else{
                            LOG_INFO(logger,"API not supported ,ignore it!");
                        }	
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
                LOG_INFO(logger,e.what());
            }
            catch (...) {
                LOG_ERROR(logger,"StarQuant terminated in error!");
            }
        }
        else
        {
            //g_except_stack.clear();
            signal(SIGSEGV,SIG_IGN);
            LOG_ERROR(logger,"StarQuant terminated by SEGSEGV!");
            exit(0);
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
