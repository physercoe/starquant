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

#ifndef CPPSRC_STARQUANT_TRADE_ORDERMANAGER_H_
#define CPPSRC_STARQUANT_TRADE_ORDERMANAGER_H_

#include <Common/datastruct.h>
#include <Common/logger.h>
#include <string>
#include <map>
#include <mutex>
#include <atomic>

using namespace std;

namespace StarQuant {
    //extern int64_t m_serverOrderId;	  // unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
    //extern std::mutex oid_mtx;  // mutex for increasing order id; defined in ordermanager.cpp
    //extern std::mutex orderStatus_mtx;  // mutex for changing order status; defined in ordermanager.cpp


class OrderManager {
 public:
    OrderManager();
    ~OrderManager();  // release all the orders
    static OrderManager* pinstance_;
    static mutex instancelock_;
    static OrderManager& instance();

    // std::atomic_int _count = { 0 };
    std::shared_ptr<SQLogger> logger;
    int32_t _count = 0;
    std::map<int64_t, std::shared_ptr<Order>> orders_;
    std::map<int64_t, int64_t> fills_;       // signed filled size
    std::map<int64_t, bool> cancels_;    // if cancelled
    mutex wlock;
    void reset();

    void trackOrder(std::shared_ptr<Order> o);  // put order under track
    void gotOrder(int64_t oid);  // order acknowledged
    void gotFill(const Fill& fill);
    void gotCancel(int64_t oid);
    std::shared_ptr<Order> retrieveOrderFromServerOrderId(int64_t oid);
    std::shared_ptr<Order> retrieveOrderFromSourceAndClientOrderId(int32_t source, int64_t oid);
    std::shared_ptr<Order> retrieveOrderFromOrderNo(const string& ono);
    std::shared_ptr<Order> retrieveOrderFromAccAndBrokerOrderId(const string& acc, int32_t oid);		
    std::shared_ptr<Order> retrieveOrderFromAccAndLocalNo(const string& acc, const string& ono);
    // std::shared_ptr<Order> retrieveOrderFromMatchNo(string fno);
    vector<std::shared_ptr<Order>> retrieveOrder(const string& fullsymbol);
    vector<std::shared_ptr<Order>> retrieveNonFilledOrderPtr();
    vector<std::shared_ptr<Order>> retrieveNonFilledOrderPtr(const string& fullsymbol);
    vector<int64_t> retrieveNonFilledOrderId();
    vector<int64_t> retrieveNonFilledOrderId(const string& fullsymbol);

    bool isEmpty();
    bool isTracked(int64_t oid);
    bool isCompleted(int64_t oid);  // either filled or canceled
    bool hasPendingOrders();  // is all orders either filled or canceled?
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_TRADE_ORDERMANAGER_H_
