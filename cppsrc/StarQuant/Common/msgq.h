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

#ifndef CPPSRC_STARQUANT_COMMON_MSGQ_H_
#define CPPSRC_STARQUANT_COMMON_MSGQ_H_


#include <Common/logger.h>
#include <Common/datastruct.h>
#ifdef _WIN32
#include <nanomsg/src/nn.h>
#include <nanomsg/src/pubsub.h>
#else
#include <nanomsg/nn.h>
#include <nanomsg/pubsub.h>
#endif
#include <mutex>
#include <memory>
#include <string>
// #include <zmq.h>

using namespace std;

namespace StarQuant {
class IMessenger{
 protected:
    std::shared_ptr<SQLogger> logger;
 public:
    string name_;
    IMessenger();
    virtual ~IMessenger() {}

    virtual void send(std::shared_ptr<MsgHeader> pmsg, int32_t mode = 0) = 0;
    virtual std::shared_ptr<MsgHeader> recv(int32_t mode = 0) = 0;
    virtual void relay() = 0;
};


class CMsgq {
 protected:
    MSGQ_PROTOCOL protocol_;
    string url_;
    std::shared_ptr<SQLogger> logger;
 public:
    CMsgq(MSGQ_PROTOCOL protocol, string url);
    virtual ~CMsgq() {}
    virtual void sendmsg(const string& str, int32_t dontwait = 1) = 0;
    virtual void sendmsg(const char* str, int32_t dontwait = 1) = 0;
    virtual string recmsg(int32_t blockingflags = 1) = 0;
};

class CMsgqNanomsg : public CMsgq {
 private:
    int32_t sock_ = -1;
    int32_t eid_ = 0;
    string endpoint_;
 public:
    CMsgqNanomsg(MSGQ_PROTOCOL protocol, string url, bool binding = true);
    ~CMsgqNanomsg();

    virtual void sendmsg(const string& str, int32_t dontwait = 1);
    virtual void sendmsg(const char* str, int32_t dontwait = 1);
    virtual string recmsg(int32_t blockingflags = 1);
};

class CMsgqZmq : public CMsgq {
 private:
    void* context_;
    void* socket_;
    string endpoint_;
    int32_t rc_;
    char buf_[256];
 public:
    CMsgqZmq(MSGQ_PROTOCOL protocol, string url, bool binding = true);
    ~CMsgqZmq();

    virtual void sendmsg(const string& str, int32_t dontwait = 1);
    virtual void sendmsg(const char* str, int32_t dontwait = 1);
    virtual string recmsg(int32_t blockingflags = 1);
};
class MsgCenter{
 public:
    static mutex msglock_;
    static std::unique_ptr<CMsgq> msgq_pub_;
    MsgCenter();
    ~MsgCenter();
};

// CMsgq Engine messenger
// for md and td engine use, send and recv msg using different port
class CMsgqEMessenger : public IMessenger {
 private:
    std::unique_ptr<CMsgq> msgq_recv_;
 public:
    static mutex sendlock_;
    static std::unique_ptr<CMsgq> msgq_send_;

    explicit CMsgqEMessenger(string url_recv);
    CMsgqEMessenger(string name, string url_recv);
    virtual ~CMsgqEMessenger() {}

    virtual void send(shared_ptr<MsgHeader> pmsg, int32_t mode = 0);
    virtual shared_ptr<MsgHeader> recv(int32_t mode = 0);
    virtual void relay() {}
};
// nanomsg relay messenger, for trading engine use
class CMsgqRMessenger : public IMessenger {
 private:
    std::unique_ptr<CMsgq> msgq_recv_;

 public:
    explicit CMsgqRMessenger(string url_recv);
    virtual ~CMsgqRMessenger() {}

    static mutex sendlock_;
    static std::unique_ptr<CMsgq> msgq_send_;
    static void Send(std::shared_ptr<MsgHeader> pmsg, int32_t mode = 0);


    virtual void send(std::shared_ptr<MsgHeader> pmsg, int32_t mode = 0);
    virtual std::shared_ptr<MsgHeader> recv(int32_t mode = 0) {return nullptr;}
    virtual void relay();
};

}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_COMMON_MSGQ_H_
