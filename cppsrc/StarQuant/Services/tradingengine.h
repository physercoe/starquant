#ifndef _StarQuant_Engine_TradingEngine_H_
#define _StarQuant_Engine_TradingEngine_H_

#include <atomic>
#include <thread>
#include <memory>
#include <Common/datastruct.h>
#include <Engine/IEngine.h>
using namespace std;

namespace StarQuant
{
    void startengine(shared_ptr<IEngine> pe);



    class DLL_EXPORT_IMPORT tradingengine {
        RUN_MODE mode = RUN_MODE::TRADE_MODE; //RUN_MODE::REPLAY_MODE;
        BROKERS _broker = BROKERS::PAPER;
        vector<std::thread*> threads_;
        vector<std::shared_ptr<IEngine>> pengines_; 
        std::unique_ptr<IMessenger> msg_relay_;
        std::shared_ptr<SQLogger> logger;

    public:



        //std::atomic<bool>* setconsolecontrolhandler(void);
        //setconsolecontrolhandler(void)
        int cronjobs(bool force = true);

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
