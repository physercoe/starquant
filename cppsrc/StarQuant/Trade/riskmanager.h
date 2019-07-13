/*****************************************************************************
 * Copyright [2019] 
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *****************************************************************************/

#ifndef CPPSRC_STARQUANT_TRADE_RISKMANAGER_H_
#define CPPSRC_STARQUANT_TRADE_RISKMANAGER_H_

#include <Common/datastruct.h>
#include <string>
#include <sstream>
#include <map>
#include <regex>
#include <mutex>
#include <atomic>
#include <memory>

using namespace std;

namespace StarQuant {
class RiskManager {
 public:
    RiskManager();
    ~RiskManager();
    static RiskManager* pinstance_;
    static mutex instancelock_;
    static RiskManager& instance();

    bool alive_;

    // per order limit
    int32_t limitSizePerOrder_ = 100;
    double limitCashPerOrder_ = 100000;

    // total limit everyday
    int32_t limitOrderCount_ = 100;
    int32_t limitCash_ = 100000;
    int32_t limitOrderSize_ = 100;

    int32_t totalOrderCount_ = 0;
    double totalCash_ = 0;
    int32_t totalOrderSize_ = 0;

    // flow limit
    int32_t limitOrderCountPerSec_ = 10;

    int32_t orderCountPerSec_ = 0;

    // check order
    bool passOrder(std::shared_ptr<Order>);

    // reset per day, sec ...
    void reset();
    void switchday();

    void resetflow();
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_TRADE_RISKMANAGER_H_
