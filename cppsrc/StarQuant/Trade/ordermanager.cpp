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

#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
#include <Common/logger.h>
#include <Common/datastruct.h>
namespace StarQuant {
    // extern int64_t m_serverOrderId ;    // unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
    // extern std::mutex oid_mtx;			 // mutex for increasing order id
    // extern std::mutex orderStatus_mtx;  // mutex for changing order status

OrderManager* OrderManager::pinstance_ = nullptr;
mutex OrderManager::instancelock_;

OrderManager::OrderManager() : _count(0) {
    // set up stocks from config
    reset();
    logger = SQLogger::getLogger("SYS");
}

OrderManager::~OrderManager() {
    // release all the orders
}

OrderManager& OrderManager::instance() {
    if (pinstance_ == nullptr) {
        lock_guard<mutex> g(instancelock_);
        if (pinstance_ == nullptr) {
            pinstance_ = new OrderManager();
        }
    }
    return *pinstance_;
}

void OrderManager::reset() {
    orders_.clear();
    fills_.clear();
    cancels_.clear();

    _count = 0;
}

void OrderManager::trackOrder(std::shared_ptr<Order> o) {
    // if (o->orderSize_ == 0) {
    //  LOG_ERROR(logger, "Incorrect OrderSize.");
    //  return;
    // }

    auto iter = orders_.find(o->serverOrderID_);
    if (iter != orders_.end())  // order exists
        return;

    orders_[o->serverOrderID_] = o;  // add to map
    cancels_[o->serverOrderID_] = false;
    fills_[o->serverOrderID_] = 0;
    LOG_INFO(logger, "Order is put under track. ServerOrderId=" << o->serverOrderID_);
}

void OrderManager::gotOrder(int64_t oid) {
    if (!isTracked(oid)) {
        LOG_ERROR(logger, "Order is not tracked. ServerOrderId= " << oid);
        return;
    }

    lock_guard<mutex> g(orderStatus_mtx);
    if ((orders_[oid]->orderStatus_ == OrderStatus::OS_NewBorn)
        || (orders_[oid]->orderStatus_ == OrderStatus::OS_Submitted)) {
        orders_[oid]->orderStatus_ = OrderStatus::OS_Acknowledged;
    }
}

void OrderManager::gotFill(const Fill& fill) {
    if (!isTracked(fill.serverOrderID_)) {
        LOG_ERROR(logger, "Order is not tracked. ServerOrderId= " << fill.serverOrderID_);
    } else {
        LOG_INFO(logger,"Order is filled. ServerOrderId="<<fill.serverOrderID_<<"price = "<<fill.tradePrice_);
        lock_guard<mutex> g(orderStatus_mtx);
        orders_[fill.serverOrderID_]->orderStatus_ = OrderStatus::OS_Filled;
        orders_[fill.serverOrderID_]->updateTime_ = ymdhmsf();
        // TODO: check for partial fill
        PortfolioManager::instance().Adjust(fill);
    }
}

void OrderManager::gotCancel(int64_t oid) {
    if (isTracked(oid)) {
        lock_guard<mutex> g(orderStatus_mtx);
        orders_[oid]->orderStatus_ = OrderStatus::OS_Canceled;
        orders_[oid]->updateTime_ = ymdhmsf();
        cancels_[oid] = true;
    }
}

std::shared_ptr<Order> OrderManager::retrieveOrderFromServerOrderId(int64_t oid) {
    if (orders_.count(oid)) {
        return orders_[oid];
    }
    return nullptr;
}
std::shared_ptr<Order> OrderManager::retrieveOrderFromSourceAndClientOrderId(int32_t source, int64_t oid) {
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if ((iterator->second->clientOrderID_ == oid) && (iterator->second->clientID_ == source)) {
            return iterator->second;
        }
    }

    return nullptr;
}

std::shared_ptr<Order> OrderManager::retrieveOrderFromOrderNo(const string& ono) {
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if ((iterator->second->orderNo_ == ono)) {
            return iterator->second;
        }
    }

    return nullptr;
}

std::shared_ptr<Order> OrderManager::retrieveOrderFromAccAndBrokerOrderId(const string& acc, int32_t oid) {
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if ((iterator->second->brokerOrderID_ == oid) && (iterator->second->account_ == acc)) {
            return iterator->second;
        }
    }
    return nullptr;
}




std::shared_ptr<Order> OrderManager::retrieveOrderFromAccAndLocalNo(const string& acc, const string& ono) {
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if ((iterator->second->localNo_ == ono) && (iterator->second->account_ == acc)) {
            return iterator->second;
        }
    }
    return nullptr;
}

// std::shared_ptr<Order> OrderManager::retrieveOrderFromMatchNo(string fno) {
// 	for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
// 		if ((iterator->second->fillNo_ == fno))
// 		{
// 			return iterator->second;
// 		}
// 	}

// 	return nullptr;
// }


vector<std::shared_ptr<Order>> OrderManager::retrieveOrder(const string& fullsymbol) {
    vector<std::shared_ptr<Order>> v;
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if (iterator->second->fullSymbol_ == fullsymbol) {
            v.push_back(iterator->second);
        }
    }

    return v;
}

vector<std::shared_ptr<Order>> OrderManager::retrieveNonFilledOrderPtr() {
    vector<std::shared_ptr<Order>> v;
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if (isActiveOS(iterator->second->orderStatus_)) {
            v.push_back(iterator->second);
        }
    }

    return v;
}

vector<std::shared_ptr<Order>> OrderManager::retrieveNonFilledOrderPtr(const string& fullsymbol) {
    vector<std::shared_ptr<Order>> v;
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if ( isActiveOS(iterator->second->orderStatus_)  && (iterator->second->fullSymbol_ == fullsymbol)) {
            v.push_back(iterator->second);
        }
    }

    return v;
}

vector<int64_t> OrderManager::retrieveNonFilledOrderId() {
    vector<int64_t> v;
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if (isActiveOS(iterator->second->orderStatus_)) {
            v.push_back(iterator->first);
        }
    }

    return v;
}

vector<int64_t> OrderManager::retrieveNonFilledOrderId(const string& fullsymbol) {
    vector<int64_t> v;
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if ((isActiveOS(iterator->second->orderStatus_)) && (iterator->second->fullSymbol_ == fullsymbol)) {
            v.push_back(iterator->first);
        }
    }

    return v;
}

bool OrderManager::isEmpty() {
    return orders_.empty();
}

bool OrderManager::isTracked(int64_t oid) {
    auto it = orders_.find(oid);
    return (it != orders_.end());
}


bool OrderManager::isCompleted(int64_t oid) {
    if (isTracked(oid)) {
        return isActiveOS(orders_[oid]->orderStatus_);
    } else {
        LOG_ERROR(logger, "Order is not tracked. ServerOrderId= " << oid);
        return true;
    }
}

bool OrderManager::hasPendingOrders() {
    for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
        if (isActiveOS(iterator->second->orderStatus_)) {
            return true;
        }
    }
    return false;
}

}  // namespace StarQuant
