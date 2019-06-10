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
        int limitSizePerOrder_ = 100;
        double limitCashPerOrder_ = 100000;

        // total limit everyday
        int limitOrderCount_ = 100;
        int limitCash_ = 100000;
        int limitOrderSize_ = 100;

        int totalOrderCount_ = 0;
        double totalCash_ = 0;
        int totalOrderSize_ = 0;

        //flow limit 
        int limitOrderCountPerSec_ = 10;

        int orderCountPerSec_ = 0;

        //check order
        bool passOrder(std::shared_ptr<Order>);

        // reset per day, sec ...
        void reset();
        void switchday();

        void resetflow();

    };
}

#endif // _StarQuant_Common_RiskManager_H_