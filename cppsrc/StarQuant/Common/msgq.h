#ifndef _StarQuant_Common_Msgq_H_
#define _StarQuant_Common_Msgq_H_

#include <mutex>
#include <memory>
#include <string>
#include <Common/logger.h>
#include <Common/datastruct.h>
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
	class IMessenger{
		protected:
			std::shared_ptr<SQLogger> logger;		
		public:
			string name_;
			IMessenger();
			virtual ~IMessenger(){};

			virtual void send(std::shared_ptr<MsgHeader> pmsg,int mode = 0) = 0;
			virtual std::shared_ptr<MsgHeader> recv(int mode = 0) =0;
			virtual void relay() = 0;
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

	//  CMsgq Engine messenger, for md and td engine use, send and recv msg using different port
	class CMsgqEMessenger : public IMessenger {
		private: 
			std::unique_ptr<CMsgq> msgq_recv_;
		public:
			static mutex sendlock_;
			static std::unique_ptr<CMsgq> msgq_send_;

			CMsgqEMessenger(string url_recv);
			CMsgqEMessenger(string name, string url_recv);
			virtual ~CMsgqEMessenger(){};
			virtual void send(shared_ptr<MsgHeader> pmsg,int mode = 0) ;
			virtual shared_ptr<MsgHeader> recv(int mode = 0) ;
			virtual void relay(){};
	};
// nanomsg relay messenger, for trading engine use 
	class CMsgqRMessenger : public IMessenger {
		private: 
			std::unique_ptr<CMsgq> msgq_recv_;
				
		public:
			CMsgqRMessenger(string url_recv);
			virtual ~CMsgqRMessenger(){};

			static mutex sendlock_;
			static std::unique_ptr<CMsgq> msgq_send_;
			static void Send(std::shared_ptr<MsgHeader> pmsg,int mode = 0);
			

			virtual void send(std::shared_ptr<MsgHeader> pmsg,int mode = 0);
			virtual std::shared_ptr<MsgHeader> recv(int mode = 0) {return nullptr;};
			virtual void relay() ;

	};
}

#endif  // _StarQuant_Common_Msgq_H_
