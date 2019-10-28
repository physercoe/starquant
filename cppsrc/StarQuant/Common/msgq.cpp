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

#include <Common/msgq.h>
#include <Common/logger.h>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/datastruct.h>
#include <string.h>
#ifdef _WIN32
#include <nanomsg/src/nn.h>
#include <nanomsg/src/pair.h>
#include <nanomsg/src/pubsub.h>
#include <nanomsg/src/pipeline.h>
#else
#include <nanomsg/nn.h>
#include <nanomsg/pair.h>
#include <nanomsg/pubsub.h>
#include <nanomsg/pipeline.h>
// #include <zmq.h>
#endif
#include <iostream>
#include <cassert>

namespace StarQuant {

CMsgq::CMsgq(MSGQ_PROTOCOL protocol, string url) {
    protocol_ = protocol;
    url_ = url;
    logger = SQLogger::getLogger("SYS");
}

IMessenger::IMessenger() {
    logger = SQLogger::getLogger("SYS");
}

CMsgqNanomsg::CMsgqNanomsg(MSGQ_PROTOCOL protocol, string url, bool binding)
    : CMsgq(protocol, url) {
    endpoint_ = url;
    if (protocol_ == MSGQ_PROTOCOL::PAIR) {
        sock_ = nn_socket(AF_SP, NN_PAIR);
        assert(sock_ >= 0);
        int32_t to = 100;
        assert(nn_setsockopt(sock_, NN_SOL_SOCKET, NN_RCVTIMEO, &to, sizeof(to)) >= 0);

        if (binding) {
            eid_ = nn_bind(sock_, endpoint_.c_str());
        } else {
            eid_ = nn_connect(sock_, endpoint_.c_str());
        }
    } else if (protocol_ == MSGQ_PROTOCOL::PUB) {
        sock_ = nn_socket(AF_SP, NN_PUB);
        assert(sock_ >= 0);
        int32_t sndbuff = 1024*1024*256;
        assert(nn_setsockopt(sock_, NN_SOL_SOCKET, NN_SNDBUF, &sndbuff, sizeof(sndbuff)) >=0 );
        eid_ = nn_bind(sock_, endpoint_.c_str());
    } else if (protocol_ == MSGQ_PROTOCOL::SUB) {
        sock_ = nn_socket(AF_SP, NN_SUB);
        assert(sock_ >= 0);
        int32_t to = 100;
        assert(nn_setsockopt(sock_, NN_SOL_SOCKET, NN_RCVTIMEO, &to, sizeof(to)) >= 0);
        nn_setsockopt(sock_, NN_SUB, NN_SUB_SUBSCRIBE, "", 0);  // subscribe to topic
        eid_ = nn_connect(sock_, endpoint_.c_str());
    } else if (protocol_ == MSGQ_PROTOCOL::PUSH) {
        sock_ = nn_socket(AF_SP, NN_PUSH);
        assert(sock_ >= 0);
        eid_ = nn_connect(sock_, endpoint_.c_str());
    } else if (protocol_ == MSGQ_PROTOCOL::PULL) {
        sock_ = nn_socket(AF_SP, NN_PULL);
        assert(sock_ >= 0);
        eid_ = nn_bind(sock_, endpoint_.c_str());
    }

    if (eid_ < 0 || sock_ < 0) {
        LOG_ERROR(logger, "Nanomsg connect sock " << endpoint_ << "error");
    }
}

std::mutex CMsgqEMessenger::sendlock_;
std::unique_ptr<CMsgq> CMsgqEMessenger::msgq_send_;

CMsgqEMessenger::CMsgqEMessenger(string name, string url_send) {
    name_ = name;
    if (msgq_recv_ == nullptr) {
        msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, url_send);
    }
}

CMsgqEMessenger::CMsgqEMessenger(string url_send) {
    if (msgq_recv_ == nullptr) {
        msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, url_send);
    }
}

void CMsgqEMessenger::send(shared_ptr<MsgHeader> Msg, int32_t mode) {
    string msgout = Msg->serialize();
    lock_guard<std::mutex> g(CMsgqEMessenger::sendlock_);
    CMsgqEMessenger::msgq_send_->sendmsg(msgout, mode);
}

shared_ptr<MsgHeader> CMsgqEMessenger::recv(int32_t mode) {
    string msgin = msgq_recv_->recmsg(mode);
    if (msgin.empty())
        return nullptr;
    // LOG_DEBUG(logger, name_ <<" recv msg:"<<msgin);
    try {
        string des;
        string src;
        string stype;
        stringstream ss(msgin);
        getline(ss, des, SERIALIZATION_SEPARATOR);
        getline(ss, src, SERIALIZATION_SEPARATOR);
        getline(ss, stype, SERIALIZATION_SEPARATOR);
        MSG_TYPE mtype = MSG_TYPE(stoi(stype));
        std::shared_ptr<MsgHeader> pheader;
        switch (mtype) {
            case MSG_TYPE_ORDER:
                pheader = make_shared<OrderMsg>();
                pheader->msgtype_ = MSG_TYPE_ORDER;
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_ORDER_CTP:
                pheader = make_shared<CtpOrderMsg>();
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_ORDER_PAPER:
                pheader = make_shared<PaperOrderMsg>();
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_SUBSCRIBE_MARKET_DATA:
                pheader = make_shared<SubscribeMsg>(des, src);
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_UNSUBSCRIBE:
                pheader = make_shared<UnSubscribeMsg>(des, src);
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_ORDER_ACTION:
            case MSG_TYPE_CANCEL_ORDER:
                pheader = make_shared<OrderActionMsg>();
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_CANCEL_ALL:
                pheader = make_shared<CancelAllMsg>();
                pheader->deserialize(msgin);
                break;
            case MSG_TYPE_QRY_CONTRACT:
                pheader = make_shared<QryContractMsg>(des, src);
                pheader->deserialize(msgin);
                break;
            default:
                pheader = make_shared<MsgHeader>(des, src, mtype);
                break;
        }
        return pheader;
    }
    catch (std::exception& e) {
        LOG_ERROR(logger, e.what() << " [orignial msg:" << msgin << "]");
        return nullptr;
    }
    catch(...) {
        LOG_ERROR(logger, "MSGQ cannot deserialize msg:" << msgin);
        return nullptr;
    }
}


std::mutex CMsgqRMessenger::sendlock_;
std::unique_ptr<CMsgq> CMsgqRMessenger::msgq_send_;

void CMsgqRMessenger::Send(shared_ptr<MsgHeader> Msg, int32_t mode) {
    string msgout = Msg->serialize();
    lock_guard<std::mutex> g(CMsgqRMessenger::sendlock_);
    CMsgqRMessenger::msgq_send_->sendmsg(msgout, mode);
}

CMsgqRMessenger::CMsgqRMessenger(string url_recv) {
    msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PULL, url_recv);
    // msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, url_send);
}

void CMsgqRMessenger::send(shared_ptr<MsgHeader> Msg, int32_t mode) {
    string msgout = Msg->serialize();
    lock_guard<std::mutex> g(CMsgqRMessenger::sendlock_);
    CMsgqRMessenger::msgq_send_->sendmsg(msgout, mode);
}


void CMsgqRMessenger::relay() {
    string msgpull = msgq_recv_->recmsg(0);
    if (msgpull.empty())
        return;
    // cout<<"recv msg at"<<ymdhmsf6();
    // 特殊标志，表明消息让策略进程收到
    if (msgpull[0] == RELAY_DESTINATION) {
        lock_guard<std::mutex> g(CMsgqEMessenger::sendlock_);
        // 将消息发回，让策略进程收到
        CMsgqEMessenger::msgq_send_->sendmsg(msgpull);
    } else {
        lock_guard<std::mutex> g(CMsgqRMessenger::sendlock_);
        // 转发消息到各个engine
        CMsgqRMessenger::msgq_send_->sendmsg(msgpull);
    }
}





CMsgqNanomsg::~CMsgqNanomsg() {
    nn_shutdown(sock_, eid_);
    nn_close(sock_);
}

void CMsgqNanomsg::sendmsg(const string& msg, int32_t dontwait) {
    int32_t bytes = nn_send(sock_, msg.c_str(), msg.size() + 1, dontwait);

    if (bytes != msg.size()+1) {
        LOG_ERROR(logger, "Nanomsg " << endpoint_ << " send msg error, return:" << bytes);
    }
}

void CMsgqNanomsg::sendmsg(const char* msg, int32_t dontwait) {
    int32_t bytes = nn_send(sock_, msg, strlen(msg) + 1, dontwait);
}

string CMsgqNanomsg::recmsg(int32_t dontwait) {
    char* buf = nullptr;
    int32_t bytes = nn_recv(sock_, &buf, NN_MSG, dontwait);

    if (bytes > 0 && buf != nullptr) {
        string msg(buf, bytes);
        buf != nullptr && nn_freemsg(buf);
        return msg;
    } else {
        return string();
    }
}

CMsgqZmq::CMsgqZmq(MSGQ_PROTOCOL protocol, string port, bool binding)
    : CMsgq(protocol, port) {
    // if (protocol_ == MSGQ_PROTOCOL::PAIR)
    // {
    // 	context_ = zmq_ctx_new();
    // 	socket_ = zmq_socket(context_, ZMQ_PAIR);

    // 	if (binding) {
    // 		endpoint_ = "tcp://*:" + port;
    // 		rc_ = zmq_bind(socket_, endpoint_.c_str());
    // 	}
    // 	else {
    // 		endpoint_ = "tcp://localhost:" + port;
    // 		rc_ = zmq_connect(socket_, endpoint_.c_str());
    // 	}			
    // }
    // else if (protocol_ == MSGQ_PROTOCOL::PUB) {
    // 	context_ = zmq_ctx_new();
    // 	socket_ = zmq_socket(context_, ZMQ_PUB);

    // 	endpoint_ = "tcp://*:" + port;
    // 	rc_ = zmq_bind(socket_, endpoint_.c_str());
    // }
    // else if (protocol_ == MSGQ_PROTOCOL::SUB) {
    // 	context_ = zmq_ctx_new();
    // 	socket_ = zmq_socket(context_, ZMQ_SUB);

    // 	endpoint_ = "tcp://localhost:" + port;
    // 	rc_ = zmq_connect(socket_, endpoint_.c_str());
    // }
}

CMsgqZmq::~CMsgqZmq() {
    // rc_ = zmq_unbind(socket_, endpoint_.c_str());
    // zmq_close(socket_);
    // zmq_ctx_shutdown(context_);
    // zmq_term(context_);
    // zmq_ctx_destroy(context_);
}

// zmq doesn't have global nn_term(), has to be set non-blocking, ZMQ_DONTWAIT
void CMsgqZmq::sendmsg(const string& msg, int32_t dontwait) {
    // int32_t bytes = zmq_send(socket_, msg.c_str(), msg.size() + 1, 0);
}

void CMsgqZmq::sendmsg(const char* msg, int32_t dontwait) {
    // int32_t bytes = zmq_send(socket_, msg, strlen(msg)+1, 0);
}

string CMsgqZmq::recmsg(int32_t blockingflags) {
    // int32_t bytes = zmq_recv(socket_, buf_, 1024, blockingflags);//ZMQ_NOBLOCK

    // if (bytes > 0) {
    // 	buf_[bytes] = '\0';
    // 	string msg(buf_);
    // 	return msg;
    // }
    // else {
    // 	return string();
    // }
}

mutex MsgCenter::msglock_;
std::unique_ptr<CMsgq> MsgCenter:: msgq_pub_;
}  // namespace StarQuant
