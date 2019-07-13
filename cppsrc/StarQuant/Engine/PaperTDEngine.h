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

#ifndef CPPSRC_STARQUANT_ENGINE_PAPERTDENGINE_H_
#define CPPSRC_STARQUANT_ENGINE_PAPERTDENGINE_H_

#include <Common/datastruct.h>
#include <Common/config.h>
#include <Engine/IEngine.h>

#include <memory>
#include <string>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{

class PaperTDEngine : public IEngine {
 public:
    string name_;
    int64_t m_brokerOrderId_;
    int64_t fillID_;

    PaperTDEngine();
    ~PaperTDEngine();

    virtual void init();
    virtual void start();
    virtual void stop();
    virtual bool connect();
    virtual bool disconnect();

    void processbuf();
    void timertask();

    void insertOrder(shared_ptr<PaperOrderMsg> pmsg);
    void cancelOrder(shared_ptr<OrderActionMsg> pmsg);
    void queryAccount(shared_ptr<MsgHeader> pmsg);
    void queryPosition(shared_ptr<MsgHeader> pmsg);
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_ENGINE_PAPERTDENGINE_H_
