#include <atomic>
#include <assert.h>
#include <Common/Logger/logger.h>
#include <Common/Util/util.h>
#include <Common/Data/datamanager.h>
#include <Common/Order/ordermanager.h>
#include <Services/Api/apiservice.h>

#ifdef _WIN32
#include <nanomsg/src/reqrep.h>
#include <nanomsg/src/pair.h>
#include <nanomsg/src/ws.h>
#else
#include <nanomsg/reqrep.h>
#include <nanomsg/pair.h>
#include <nanomsg/ws.h>
#endif

namespace StarQuant
{
	extern std::atomic<bool> gShutdown;

	ApiServer::ApiServer() {
		// message queue factory
		// if (CConfig::instance()._msgq == MSGQ::ZMQ) {
		// 	client_msg_pair_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::PAIR, CConfig::instance().API_PORT);
		// 	client_data_pub_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::PUB, CConfig::instance().API_ZMQ_DATA_PORT);
		// 	market_data_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().MKT_DATA_PUBSUB_PORT, false);

		// 	//brokerage_msg_pair_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT, false);
		// 	//bar_msg_sub_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::SUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT, false);
		// 	brokerage_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT, false);
		// 	bar_msg_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT, false);
		// }
		// else {
		// 	client_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().API_PORT);
		// 	client_data_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().API_ZMQ_DATA_PORT);
		// 	market_data_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().MKT_DATA_PUBSUB_PORT, false);
		// 	brokerage_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT, false);
		// 	bar_msg_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT, false);
		// }
		client_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().API_PORT);
		client_data_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().API_ZMQ_DATA_PORT);
		market_data_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().MKT_DATA_PUBSUB_PORT, false);
		brokerage_msg_pair_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PAIR, CConfig::instance().BROKERAGE_PAIR_PORT, false);
		bar_msg_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().BAR_AGGREGATOR_PUBSUB_PORT, false);



	}

	ApiServer::~ApiServer() {
		PRINT_TO_FILE("INFO:[%s,%d][%s] %s\n", __FILE__, __LINE__, __FUNCTION__, "api service stopped.");
	}

	// 1. read from client
	// 2. relay new bar		// TODO: should it be here?
	// 3. relay brokerage message
	void ApiServer::run() {
		PRINT_TO_FILE("INFO:[%s,%d][%s]api server started.\n", __FILE__, __LINE__, __FUNCTION__);

		while (!gShutdown) {
			onClientMessage();					// 1. read from client
			onServerMessage();					// 2. relay brokerage message
			
//			if ((CConfig::instance()._msgq == MSGQ::ZMQ))
			onDataMessage();					// 3. relay new bar

			msleep(10);
		}
	}

	void ApiServer::onClientMessage() {
		string msgin = client_msg_pair_->recmsg(1);

		if (msgin.empty())
		{
			return;
		}
		//cout<<"api server rec clinet msg:"<<msgin<<endl;
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]client msgin: %s\n", __FILE__, __LINE__, __FUNCTION__, msgin.c_str());

		if (startwith(msgin, CConfig::instance().new_order_msg)) {
			brokerage_msg_pair_->sendmsg(msgin);
		}
		else if (startwith(msgin, CConfig::instance().cancel_order_msg)) {
			brokerage_msg_pair_->sendmsg(msgin);		// passthrough
		}
		else if (startwith(msgin, CConfig::instance().order_status_msg)) {
			string msgout;
			vector<string> v = stringsplit(msgin, SERIALIZATION_SEPARATOR);
			if (v.size() == 2) {
				long oid = stol(v[1]);

				//TODO send message back 
			}
		}
		else if (startwith(msgin, CConfig::instance().hist_msg)) {
			brokerage_msg_pair_->sendmsg(msgin);		// passthrough
		}
		else if (startwith(msgin, CConfig::instance().last_price_msg)) {
			vector<string> v = stringsplit(msgin, SERIALIZATION_SEPARATOR);		// 'p'|sym
			string sym = v[1];
			char msg[128] = {};
			double value = DataManager::instance()._latestmarkets[sym].price_;
			sprintf(msg, "p|%s|%d|%.2f", sym.c_str(), DataType::DT_TradePrice, value);

			client_msg_pair_->sendmsg(msg);
		}
		else if (startwith(msgin, CConfig::instance().last_size_msg)) {
			vector<string> v = stringsplit(msgin, SERIALIZATION_SEPARATOR);		// 'z'|sym
			string sym = v[1];
			char msg[128] = {};
			double value = DataManager::instance()._latestmarkets[sym].size_;
			sprintf(msg, "z|%s|%d|%.2f", sym.c_str(), DataType::DT_TradeSize, value);

			client_msg_pair_->sendmsg(msg);
		}
		else if (startwith(msgin, CConfig::instance().bar_msg)) {
			vector<string> v = stringsplit(msgin, SERIALIZATION_SEPARATOR);		// 'bx'|sym
			string sym = v[1];
			string msg;
			
			msg = DataManager::instance()._60s[sym].serialize();

			client_msg_pair_->sendmsg(msg);
		}
		else if (msgin == CConfig::instance().close_all_msg) {
			brokerage_msg_pair_->sendmsg(msgin);		// passthrough
		}
	}


	void ApiServer::onServerMessage() {
		string msg = brokerage_msg_pair_->recmsg();
		
		if (!msg.empty()) {
			//cout<<"api rec msg:"<<msg<<endl;
			client_msg_pair_->sendmsg(msg);		// passthrough
		}
	}

	void ApiServer::onDataMessage() {
		string msg = market_data_sub_->recmsg(0);
		if (!msg.empty()) {
			//cout<<"api server relay datamsg: "<<msg<<endl;
			client_data_pub_->sendmsg(msg);		// passthrough
		}
	}

	// microservice
	void ApiService() {
		ApiServer server;
		server.run();
	}
}