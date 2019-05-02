#ifndef _StarQuant_Engine_PaperTDEngine_H_
#define _StarQuant_Engine_PaperTDEngine_H_

#include <mutex>
#include <Common/datastruct.h>
#include <Common/config.h>
#include <Engine/IEngine.h>



using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{

	class PaperTDEngine : public IEngine {
	public:
		string name_;
		long m_brokerOrderId_;
		long fillID_;

		PaperTDEngine();
		~PaperTDEngine();

		virtual void init();
		virtual void start();
		virtual void stop();
		virtual bool connect() ;
		virtual bool disconnect() ;
		
		void processbuf();
		void timertask();

		void insertOrder(shared_ptr<PaperOrderMsg> pmsg);
		void cancelOrder(shared_ptr<OrderActionMsg> pmsg);
		void queryAccount(shared_ptr<MsgHeader> pmsg);
		void queryPosition(shared_ptr<MsgHeader> pmsg);
		
	};
}

#endif
