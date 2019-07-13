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

#ifndef CPPSRC_STARQUANT_SERVICES_TRADINGENGINE_H_
#define CPPSRC_STARQUANT_SERVICES_TRADINGENGINE_H_

#include <Common/datastruct.h>
#include <Engine/IEngine.h>
#include <atomic>
#include <thread>
#include <memory>
#include <vector>

using namespace std;

namespace StarQuant {
void startengine(shared_ptr<IEngine> pe);

class DLL_EXPORT_IMPORT tradingengine {
    RUN_MODE mode = RUN_MODE::TRADE_MODE;  // RUN_MODE::REPLAY_MODE;
    BROKERS _broker = BROKERS::PAPER;
    vector<std::thread*> threads_;
    vector<std::shared_ptr<IEngine>> pengines_;
    std::unique_ptr<IMessenger> msg_relay_;
    std::shared_ptr<SQLogger> logger;

 public:
    // std::atomic<bool>* setconsolecontrolhandler(void);
    // setconsolecontrolhandler(void)
    int32_t cronjobs(bool force = true);

    int32_t run();
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

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_SERVICES_TRADINGENGINE_H_

