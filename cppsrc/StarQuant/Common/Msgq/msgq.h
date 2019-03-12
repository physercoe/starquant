#ifndef _StarQuant_Common_Msgq_H_
#define _StarQuant_Common_Msgq_H_

#include <string>
#include <Common/config.h>
#ifdef _WIN32
#include <nanomsg/src/nn.h>
#include <nanomsg/src/pubsub.h>
#else
#include <nanomsg/nn.h>
#include <nanomsg/pubsub.h>
#endif

//#include <zmq.h>

using namespace std;

namespace StarQuant {
	class CMsgq {
	protected:
		MSGQ_PROTOCOL protocol_;
		string port_;
	public:
		CMsgq(MSGQ_PROTOCOL protocol, string port);
		virtual void sendmsg(const string& str) = 0;
		virtual void sendmsg(const char* str) = 0;
		virtual string recmsg(int blockingflags = 1) = 0;
	};

	class CMsgqNanomsg : public CMsgq {
	private:
		int sock_ = -1;
		int eid_ = 0;
		string endpoint_;
	public:
		CMsgqNanomsg(MSGQ_PROTOCOL protocol, string port, bool binding=true);
		~CMsgqNanomsg();

		void sendmsg(const string& str);
		void sendmsg(const char* str);
		string recmsg(int blockingflags = 1);
	};

	class CMsgqZmq : public CMsgq {
	private:
		void* context_;
		void* socket_;
		string endpoint_;
		int rc_;
		char buf_[256];
	public:
		CMsgqZmq(MSGQ_PROTOCOL protocol, string port, bool binding = true);
		~CMsgqZmq();

		void sendmsg(const string& str);
		void sendmsg(const char* str);
		string recmsg(int blockingflags = 1);
	};
}

#endif  // _StarQuant_Common_Msgq_H_
