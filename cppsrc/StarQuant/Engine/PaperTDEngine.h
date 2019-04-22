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

		PaperTDEngine();
		~PaperTDEngine();

		virtual void init();
		virtual void start();
		virtual void stop();
		virtual bool connect() ;
		virtual bool disconnect() ;

		void insertOrder(shared_ptr<OrderMsg> pmsg);
		void cancelOrder(shared_ptr<OrderActionMsg> pmsg);
		void queryAccount(shared_ptr<MsgHeader> pmsg);
		// void queryOrder(const string& msgorder_,const string& source);
		void queryPosition(shared_ptr<MsgHeader> pmsg);
		
		void insertOrder(const vector<string>& msgv);
		void cancelOrder(const vector<string>& msgv);
		void cancelOrder(long oid,const string& source );
		void cancelOrders(const string & ono,const string& source);
		void queryAccount(const string& source);
		void queryOrder(const string& msgorder_,const string& source);
		void queryPosition(const string& source);

	};
}

#endif
