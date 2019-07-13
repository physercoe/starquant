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
#ifndef CPPSRC_STARQUANT_ENGINE_IENGINE_H_
#define CPPSRC_STARQUANT_ENGINE_IENGINE_H_

#include <Common/msgq.h>
#include <Common/logger.h>
#include <memory>


namespace StarQuant
{
// Engine state
enum EState :int32_t {
    DISCONNECTED = 0,           // initial state is disconnected
    CONNECTING,
    CONNECT_ACK,           // ctp: front end is  connected; tap:  logined
    AUTHENTICATING,
    AUTHENTICATE_ACK,  // ctp trade authencated
    LOGINING,
    LOGIN_ACK,             // logined for ctp, for tap api is ready to do things
    LOGOUTING,
    STOP                   // for engine stop
};

// Interface class: base engine for td and md engine
class IEngine {
 public:
    // static mutex sendlock_;  // msg send lock_
    // static std::unique_ptr<CMsgq> msgq_send_;  //for md and td messenge to client, all engine share same msgq, usually publish mode
    // std::unique_ptr<CMsgq> msgq_recv_;  //each engine has its own msgq, usually subscribe mode
    std::atomic<EState> estate_;
    std::unique_ptr<IMessenger> messenger_;

    IEngine();
    virtual ~IEngine();

    virtual void init();
    virtual void start();
    virtual void stop();
    virtual bool connect() = 0;
    virtual bool disconnect() = 0;
 protected:
    std::shared_ptr<SQLogger> logger;
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_ENGINE_IENGINE_H_
