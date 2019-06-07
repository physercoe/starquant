#ifndef _StarQuant_Trade_RiskManager_H_
#define _StarQuant_Trade_RiskManager_H_

#include <string>
#include <sstream>
#include <map>
#include <regex>
#include <mutex>
#include <atomic>
#include <Common/datastruct.h>
using namespace std;

namespace StarQuant
{
    class RiskManager {
    public:
        RiskManager();
        ~RiskManager();				
        static RiskManager* pinstance_;
        static mutex instancelock_;
        static RiskManager& instance();

        bool alive_;

        // per order limit
        int limitSizePerOrder_;
        double limitCashPerOrder_;

        // total limit everyday
        int limitOrderCount_;
        int limitCash_;
        int limitOrderSize_;

        int totalOrderCount_;
        double totalCash_;
        int totalOrderSize_;

        //flow limit 
        int limitOrderCountPerSec_;

        int orderCountPerSec_;

        //check order
        bool passOrder(std::shared_ptr<Order>);

        // reset per day, sec ...
        void reset();
        void switchday();

        void resetflow();

    };
}

#endif // _StarQuant_Common_RiskManager_H_