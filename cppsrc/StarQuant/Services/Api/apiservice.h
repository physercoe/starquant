#ifndef __StarQuant_Engine_ApiService_H__
#define __StarQuant_Engine_ApiService_H__

#include <Common/config.h>
#include <Common/Msgq/msgq.h>

using std::string;

namespace StarQuant
{
	class ApiServer {
	private:
		std::unique_ptr<CMsgq> client_msg_pair_;
		std::unique_ptr<CMsgq> client_data_pub_;
		std::unique_ptr<CMsgq> market_data_sub_;

		std::unique_ptr<CMsgq> brokerage_msg_pair_;
		std::unique_ptr<CMsgq> bar_msg_sub_;

		void onClientMessage();
		void onServerMessage();
		void onDataMessage();

	public:
		ApiServer();
		~ApiServer();
		void run();
	};

	// microservice, here represented as a thread
	void ApiService();
}

#endif
