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
#ifndef CPPSRC_STARQUANT_COMMON_CONFIG_H_
#define CPPSRC_STARQUANT_COMMON_CONFIG_H_

#include <Common/datastruct.h>
#include <inttypes.h>
#include <cmath>
#include <mutex>
#include <atomic>
#include <string>
#include <memory>
#include <vector>
#include <set>
#include <queue>
#include <map>
#include <list>
#include <deque>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <boost/filesystem.hpp>
// #define CEREAL_RAPIDJSON_NAMESPACE creal_rapidjson
// #include <cereal/types/unordered_map.hpp>
// #include <cereal/types/memory.hpp>
// #include <cereal/archives/json.hpp>
// #include <cereal/types/vector.hpp>
// #include <cereal/types/string.hpp>
// #include <cereal/types/map.hpp>


#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include<WinSock2.h>
#else
#include <unistd.h>
#endif

using std::vector;
using std::string;
using std::set;
using std::mutex;
using std::map;
using std::atomic_int;



namespace StarQuant {
class CConfig {
    static CConfig* pinstance_;
    static mutex instancelock_;

    CConfig();

 public:
    RUN_MODE _mode = RUN_MODE::TRADE_MODE;
    BROKERS _broker = BROKERS::PAPER;
    MSGQ _msgq = MSGQ::NANOMSG;
    int32_t _tickinterval = 0;
    int32_t _brokerdelay = 0;
    static CConfig& instance();
    map<string, Gateway> _gatewaymap;
    mutex readlock_;
    void readConfig();

    string _config_dir;
    string _log_dir;
    string _data_dir;
    string configDir();
    string logDir();
    string dataDir();
    string logconfigfile_;

    /*************Securities List ****************/
    vector<string> securities;  // full symbol
    map<string, string> instrument2sec;  // instrument id to full symbol map
    map<string, string> sec2instrument;  // symbol to ctp instrument
    string SecurityFullNameToCtpSymbol(const std::string& symbol);
    string CtpSymbolToSecurityFullName(const std::string& symbol);
    /********End of Securities List ************/

    /******************* Database info ***************/
    string _mongodbaddr = "mongodb://localhost:27017";
    string _mongodbname = "";

    string filetoreplay;
    /************* End of Database **********************/

    /*************** Message Queue ******************/
    // to all clients
    string SERVERPUB_URL = "tcp://localhost:55555";
    // pub the requests to engines(which subscribe)
    string SERVERSUB_URL = "tcp://localhost:55556";
    // listen all the requests from clients
    string SERVERPULL_URL = "tcp://localhost:55557";
    bool cpuaffinity = false;
    /******************** Message Queue **********/

    /************************auto task*****************/
    bool autoconnect = true;
    bool autoqry = false;

    /*********Risk setting**************/
    bool riskcheck = false;
    int32_t sizeperorderlimit = 0;
    double cashperorderlimit = 0.0;
    int32_t ordercountlimit = 0;
    double cashlimit = 0.0;
    int32_t ordersizelimit = 0;
    int32_t ordercountperseclimit = 0;
    /***********End Risk setting*********/
};
}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_COMMON_CONFIG_H_
