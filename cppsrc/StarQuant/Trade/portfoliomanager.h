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

#ifndef CPPSRC_STARQUANT_TRADE_PORTFOLIOMANAGER_H_
#define CPPSRC_STARQUANT_TRADE_PORTFOLIOMANAGER_H_


#include <Common/datastruct.h>
#include <assert.h>
#include <string>
#include <numeric>
#include <mutex>
#include <regex>
#include <atomic>
#include <map>
#include <memory>

using namespace std;

namespace StarQuant {
class PortfolioManager {
 public:
    PortfolioManager();
    ~PortfolioManager();
    static PortfolioManager* pinstance_;
    static mutex instancelock_;
    static PortfolioManager& instance();
    // atomic<uint64_t> _count = { 0 };
    uint64_t _count = 0;
    AccountInfo account_;
    map<string, AccountInfo> accinfomap_;     // accname->acc
    map<string, std::shared_ptr<Position> > positions_;  // poskey ->pos
    double cash_;

    void reset();
    void rebuild();

    void Add(std::shared_ptr<Position> ppos);
    double Adjust(const Fill& fill);
    std::shared_ptr<Position> retrievePosition(const string& key);
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_TRADE_PORTFOLIOMANAGER_H_
