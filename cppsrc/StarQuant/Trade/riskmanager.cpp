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


#include <Trade/riskmanager.h>
#include <Common/config.h>
#include <fmt/format.h>
#include <memory>

namespace StarQuant {
RiskManager* RiskManager::pinstance_ = nullptr;
mutex RiskManager::instancelock_;

RiskManager::RiskManager() : alive_(false) {
    // set up from config
    reset();
}

RiskManager::~RiskManager() {
}

RiskManager& RiskManager::instance() {
    if (pinstance_ == nullptr) {
        lock_guard<mutex> g(instancelock_);
        if (pinstance_ == nullptr) {
            pinstance_ = new RiskManager();
        }
    }
    return *pinstance_;
}



bool RiskManager::passOrder(std::shared_ptr<Order> o) {
    if (!alive_)
        return true;
    totalOrderCount_ += 1;
    totalOrderSize_ += abs(o->quantity_);
    orderCountPerSec_ += 1;
    bool ocok = (totalOrderCount_ <= limitOrderCount_);
    bool osok = (totalOrderSize_ <= limitOrderSize_);
    bool ospok = (abs(o->quantity_) <= limitSizePerOrder_);
    bool ocpsok = (orderCountPerSec_ <= limitOrderCountPerSec_);
    if (ocok && osok && ospok && ocpsok)
        return true;
    fmt:printf("totalcount:{},totalsize{},sizeperorder:{},countpersecond{}",
        ocok, osok, ospok, ocpsok);
    return false;
}


void RiskManager::reset() {
    alive_ = CConfig::instance().riskcheck;
    limitSizePerOrder_ = CConfig::instance().sizeperorderlimit;
    limitCashPerOrder_ = CConfig::instance().cashperorderlimit;
    limitOrderCount_ = CConfig::instance().ordercountlimit;
    limitCash_ = CConfig::instance().cashlimit;
    limitOrderSize_ = CConfig::instance().ordersizelimit;
    limitOrderCountPerSec_ = CConfig::instance().ordercountperseclimit;
}

void RiskManager::resetflow() {
    orderCountPerSec_ = 0;
}

void RiskManager::switchday() {
    totalOrderCount_ = 0;
    totalCash_ = 0.0;
    totalOrderSize_ = 0;
}

}   // namespace StarQuant

