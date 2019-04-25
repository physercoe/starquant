#include <Common/msgq.h>
#include <Common/logger.h>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/datastruct.h>

#include <cassert>
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

namespace StarQuant {




	
	CMsgq::CMsgq(MSGQ_PROTOCOL protocol, string url) {
		protocol_ = protocol;
		url_ = url;
		logger = SQLogger::getLogger("SYS");
	}

	IMessenger::IMessenger(){
		logger = SQLogger::getLogger("SYS");
	}

	CMsgqNanomsg::CMsgqNanomsg(MSGQ_PROTOCOL protocol, string url, bool binding)
		: CMsgq(protocol, url) {
#ifdef _DEBUG
		std::printf("nanomsg protocol: %d  port %s  binding: %d\n", protocol, port.c_str(), binding);
#endif
		endpoint_ = url;
		if (protocol_ == MSGQ_PROTOCOL::PAIR)
		{
			sock_ = nn_socket(AF_SP, NN_PAIR);
			assert(sock_ >= 0);
			int to = 100;
			assert(nn_setsockopt(sock_, NN_SOL_SOCKET, NN_RCVTIMEO, &to, sizeof(to)) >= 0);

			if (binding) {
				eid_ = nn_bind(sock_, endpoint_.c_str());
			}
			else {
				eid_ = nn_connect(sock_, endpoint_.c_str());
			}
		}
		else if (protocol_ == MSGQ_PROTOCOL::PUB) {
			sock_ = nn_socket(AF_SP, NN_PUB);
			assert(sock_ >= 0);
			eid_ = nn_bind(sock_, endpoint_.c_str());
		}
		else if (protocol_ == MSGQ_PROTOCOL::SUB) {
			sock_ = nn_socket(AF_SP, NN_SUB);
			assert(sock_ >= 0);
			int to = 100;
			assert(nn_setsockopt(sock_, NN_SOL_SOCKET, NN_RCVTIMEO, &to, sizeof(to)) >= 0);
			nn_setsockopt(sock_, NN_SUB, NN_SUB_SUBSCRIBE, "", 0);		// subscribe to topic
			eid_ = nn_connect(sock_, endpoint_.c_str());
		}
		else if (protocol_ == MSGQ_PROTOCOL::PUSH){
			sock_ = nn_socket(AF_SP, NN_PUSH);
			assert(sock_ >= 0);
			eid_ = nn_connect(sock_, endpoint_.c_str());
		}
		else if (protocol_ == MSGQ_PROTOCOL::PULL)
		{
			sock_ = nn_socket(AF_SP, NN_PULL);
			assert(sock_ >= 0);
			eid_ = nn_bind(sock_, endpoint_.c_str());
		}
		
		if (eid_ < 0 || sock_ < 0) {
			LOG_ERROR(logger,"Nanomsg connect sock "<<endpoint_<<"error");
			//PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Unable to connect to message queue: %s,%d\n", __FILE__, __LINE__, __FUNCTION__, url.c_str(), binding);
		}
	}

	std::mutex CMsgqEMessenger::sendlock_;
	std::unique_ptr<CMsgq> CMsgqEMessenger::msgq_send_;

	CMsgqEMessenger::CMsgqEMessenger(string name, string url_send)
	{
		name_ = name;
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, url_send);	
		}		
	}
	CMsgqEMessenger::CMsgqEMessenger(string url_send)
	{
		if (msgq_recv_ == nullptr){
			msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, url_send);	
		}		
	}

	void CMsgqEMessenger::send(shared_ptr<MsgHeader> Msg,int mode){
		// string msgout = Msg->destination_ 
		// 				+ SERIALIZATION_SEPARATOR + Msg->source_
		// 				+ SERIALIZATION_SEPARATOR + to_string(Msg->msgtype_)
		// 				+ Msg->serialize();
		string msgout = Msg->serialize();
		lock_guard<std::mutex> g(CMsgqEMessenger::sendlock_);
		CMsgqEMessenger::msgq_send_->sendmsg(msgout,mode);
	}

	shared_ptr<MsgHeader> CMsgqEMessenger::recv(int mode){
		string msgin = msgq_recv_->recmsg(mode);
		if (msgin.empty())
			return nullptr;
		LOG_DEBUG(logger, name_ <<" recv msg:"<<msgin);
		string des;
		string src;
		string stype;
		stringstream ss(msgin);
		getline(ss,des,SERIALIZATION_SEPARATOR);
		getline(ss,src,SERIALIZATION_SEPARATOR);
		getline(ss,stype,SERIALIZATION_SEPARATOR);
		MSG_TYPE mtype = MSG_TYPE(stoi(stype));
		std::shared_ptr<MsgHeader> pheader;
		switch (mtype)
		{
			case MSG_TYPE_ORDER:
				pheader = make_shared<OrderMsg>();
				pheader->msgtype_ = MSG_TYPE_ORDER;
				pheader->deserialize(msgin);
				break;
			case MSG_TYPE_SUBSCRIBE_MARKET_DATA:
				pheader = make_shared<SubscribeMsg>(des,src);
				pheader->deserialize(msgin);
				break;
			case MSG_TYPE_UNSUBSCRIBE:
				pheader = make_shared<UnSubscribeMsg>(des,src);
				pheader->deserialize(msgin);
				break;
			case MSG_TYPE_ORDER_ACTION:
			case MSG_TYPE_CANCEL_ORDER:	
				pheader = make_shared<OrderActionMsg>();
				pheader->deserialize(msgin);
				break;			
			default:
				pheader = make_shared<MsgHeader>(des,src,mtype);
				break;
		}
		return pheader;
	}

	
	CMsgqRMessenger::CMsgqRMessenger(string url_recv, string url_send){
		msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PULL, url_recv);
		msgq_send_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, url_send);

	}

	void CMsgqRMessenger::send(shared_ptr<MsgHeader> Msg,int mode){
		// string msgout = Msg->destination_ 
		// 				+ SERIALIZATION_SEPARATOR + Msg->source_
		// 				+ SERIALIZATION_SEPARATOR + to_string(Msg->msgtype_)
		// 				+ Msg->serialize();
		string msgout = Msg->serialize();
		msgq_send_->sendmsg(msgout,mode);

	}


	void CMsgqRMessenger::relay(){
			string msgpull = msgq_recv_->recmsg(0);
			if (msgpull.empty())
				return;
			// cout<<"recv msg at"<<ymdhmsf6();	
			if (msgpull[0] == RELAY_DESTINATION){ //特殊标志，表明消息让策略进程收到
				lock_guard<std::mutex> g(CMsgqEMessenger::sendlock_);
				CMsgqEMessenger::msgq_send_->sendmsg(msgpull);		//将消息发回，让策略进程收到			
			}
			else
			{
				msgq_send_->sendmsg(msgpull); //转发消息到各个engine
			}
	}





	CMsgqNanomsg::~CMsgqNanomsg()
	{
		nn_shutdown(sock_, eid_);
		nn_close(sock_);
	}

	void CMsgqNanomsg::sendmsg(const string& msg,int dontwait) {
		// if (!msg.empty()) 
		int bytes = nn_send(sock_, msg.c_str(), msg.size() + 1, dontwait);			// TODO: size or size+1

		if (bytes != msg.size()+1){
			LOG_ERROR(logger,"Nanomsg "<<endpoint_ <<" send msg error, return:"<<bytes);
			// PRINT_TO_FILE("INFO:[%s,%d][%s]NANOMSG ERROR, %s\n", __FILE__, __LINE__, __FUNCTION__, msg.c_str());
		}
	}

	void CMsgqNanomsg::sendmsg(const char* msg,int dontwait) {
		int bytes = nn_send(sock_, msg, strlen(msg) + 1, dontwait);
	}

	string CMsgqNanomsg::recmsg(int dontwait) {
		char* buf = nullptr;
		int bytes = nn_recv(sock_, &buf, NN_MSG, dontwait);		//NN_DONTWAIT

		if (bytes > 0 && buf != nullptr) {
			string msg(buf, bytes);
			buf != nullptr && nn_freemsg(buf);
			return msg;
		}
		else {
			return string();
		}
	}

	CMsgqZmq::CMsgqZmq(MSGQ_PROTOCOL protocol, string port, bool binding)
		: CMsgq(protocol, port) {
#ifdef _DEBUG
		std::printf("zmq protocol: %d  port %s  binding: %d\n", protocol, port.c_str(), binding);
#endif
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

	CMsgqZmq::~CMsgqZmq()
	{
		// rc_ = zmq_unbind(socket_, endpoint_.c_str());
		// zmq_close(socket_);
		// zmq_ctx_shutdown(context_);
		// zmq_term(context_);
		// zmq_ctx_destroy(context_);
	}

	// zmq doesn't have global nn_term(), has to be set non-blocking, ZMQ_DONTWAIT
	void CMsgqZmq::sendmsg(const string& msg,int dontwait) {
		// int bytes = zmq_send(socket_, msg.c_str(), msg.size() + 1, 0);		// TODO: size or size+1
	}

	void CMsgqZmq::sendmsg(const char* msg,int dontwait) {
		// int bytes = zmq_send(socket_, msg, strlen(msg)+1, 0);
	}

	string CMsgqZmq::recmsg(int blockingflags) {		
		// int bytes = zmq_recv(socket_, buf_, 1024, blockingflags);		//ZMQ_NOBLOCK

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
}
