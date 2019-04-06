#ifndef _StarQuant_Common_Msgq_H_
#define _StarQuant_Common_Msgq_H_

#include <mutex>
#include <memory>
#include <string>
#include <Common/logger.h>

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

enum class MSGQ : uint8_t {
	NANOMSG = 0, ZMQ, KAFKA, WEBSOCKET
};

enum class MSGQ_PROTOCOL : uint8_t {
	PAIR = 0, REQ, REP, PUB, SUB, PUSH,PULL
};

	class CMsgq {
	protected:
		MSGQ_PROTOCOL protocol_;
		string url_;
		std::shared_ptr<SQLogger> logger;
	public:
		CMsgq(MSGQ_PROTOCOL protocol, string url);
		virtual ~CMsgq(){};
		virtual void sendmsg(const string& str,int dontwait = 1) = 0;
		virtual void sendmsg(const char* str,int dontwait = 1) = 0;
		virtual string recmsg(int blockingflags = 1) = 0;
	};

	class CMsgqNanomsg : public CMsgq {
	private:
		int sock_ = -1;
		int eid_ = 0;
		string endpoint_;
	public:
		CMsgqNanomsg(MSGQ_PROTOCOL protocol, string url, bool binding=true);
		~CMsgqNanomsg();

		virtual void sendmsg(const string& str,int dontwait = 1);
		virtual void sendmsg(const char* str,int dontwait = 1);
		virtual string recmsg(int blockingflags = 1);
	};

	class CMsgqZmq : public CMsgq {
	private:
		void* context_;
		void* socket_;
		string endpoint_;
		int rc_;
		char buf_[256];
	public:
		CMsgqZmq(MSGQ_PROTOCOL protocol, string url, bool binding = true);
		~CMsgqZmq();

		virtual void sendmsg(const string& str,int dontwait = 1);
		virtual void sendmsg(const char* str,int dontwait = 1);
		virtual string recmsg(int blockingflags = 1);
	};
	class MsgCenter{
		public:
			static mutex msglock_;
			static std::unique_ptr<CMsgq> msgq_pub_;
			MsgCenter();
			~MsgCenter();

	};
}

#endif  // _StarQuant_Common_Msgq_H_
