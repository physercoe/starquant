#include <Common/msgq.h>
#include <Common/logger.h>
#include <Common/config.h>
#include <Common/timeutil.h>

#include <cassert>
#include <string.h>
#ifdef _WIN32
#include <nanomsg/src/nn.h>
#include <nanomsg/src/pair.h>
#else
#include <nanomsg/nn.h>
#include <nanomsg/pair.h>
// #include <zmq.h>
#endif

namespace StarQuant {




	
	CMsgq::CMsgq(MSGQ_PROTOCOL protocol, string url) {
		protocol_ = protocol;
		url_ = url;
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
		if (eid_ < 0 || sock_ < 0) {
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Unable to connect to message queue: %s,%d\n", __FILE__, __LINE__, __FUNCTION__, url.c_str(), binding);
		}
	}

	CMsgqNanomsg::~CMsgqNanomsg()
	{
		nn_shutdown(sock_, eid_);
		nn_close(sock_);
	}

	void CMsgqNanomsg::sendmsg(const string& msg) {
		// if (!msg.empty()) 
		int bytes = nn_send(sock_, msg.c_str(), msg.size() + 1, 0);			// TODO: size or size+1

		/*if (bytes != msg.size()){
			PRINT_TO_FILE("INFO:[%s,%d][%s]NANOMSG ERROR, %s\n", __FILE__, __LINE__, __FUNCTION__, msg.c_str());
		}*/
	}

	void CMsgqNanomsg::sendmsg(const char* msg) {
		int bytes = nn_send(sock_, msg, strlen(msg) + 1, 0);
	}

	string CMsgqNanomsg::recmsg(int blockingflags) {
		char* buf = nullptr;
		int bytes = nn_recv(sock_, &buf, NN_MSG, blockingflags);		//NN_DONTWAIT

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
	void CMsgqZmq::sendmsg(const string& msg) {
		// int bytes = zmq_send(socket_, msg.c_str(), msg.size() + 1, 0);		// TODO: size or size+1
	}

	void CMsgqZmq::sendmsg(const char* msg) {
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
