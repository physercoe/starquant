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

#ifndef CPPSRC_STARQUANT_DATA_DATAMANAGER_H_
#define CPPSRC_STARQUANT_DATA_DATAMANAGER_H_

#include <Common/datastruct.h>
#include <Data/tickwriter.h>
#include <string>
#include <sstream>
#include <map>
#include <regex>

// #define CEREAL_RAPIDJSON_NAMESPACE creal_rapidjson
// #include <cereal/types/unordered_map.hpp>
// #include <cereal/types/memory.hpp>
// #include <cereal/archives/json.hpp>
// #include <cereal/types/vector.hpp>
// #include <cereal/types/string.hpp>
// #include <cereal/types/map.hpp>


using std::string;

namespace StarQuant
{
/// DataManager
/// 1. provide latest full tick price info  -- DataBoard Service
/// 2. record data
class DataManager {
 public:
    static DataManager* pinstance_;
    static mutex instancelock_;
    static DataManager& instance();

    TickWriter recorder_;
    uint64_t count_ = 0;
    bool contractUpdated_ = false;
    bool saveSecurityFile_ = false;
    std::map<std::string, Security> securityDetails_;  // ctpsymbol to security
    std::map<string, Tick> orderBook_;
    std::map<string, string> ctp2Full_;
    std::map<string, string> full2Ctp_;
    //std::map<string, BarSeries> _5s;
    //std::map<string, BarSeries> _15s;
    // std::map<string, BarSeries> _60s;
    //std::map<string, BarSeries> _1d;

    DataManager();
    ~DataManager();
    void reset();
    void rebuild();
    void updateOrderBook(const Tick& k) { orderBook_[k.fullSymbol_] = k;}
    void updateOrderBook(const Fill& fill);
    void saveSecurityToFile();
    void loadSecurityFile();
};
}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_DATA_DATAMANAGER_H_
