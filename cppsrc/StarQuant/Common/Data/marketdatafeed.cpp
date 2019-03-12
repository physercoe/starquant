#include <mutex>
#include <Common/config.h>
#include <Common/Logger/logger.h>
#include <Common/Util/util.h>
#include <Common/Time/timeutil.h>
#include <Common/Data/datatype.h>
#include <Common/Data/datamanager.h>
#include <Common/Data/marketdatafeed.h>

using namespace std;
namespace StarQuant
{
	marketdatafeed::marketdatafeed() :
		_mkstate(MK_DISCONNECTED), _mode(TICKBAR) {
		timeout.tv_sec = 0;
		timeout.tv_usec = 0;
		last_time = time(0);

		// message queue factory
		// if (CConfig::instance()._msgq == MSGQ::ZMQ) {
		// 	//msgq_pub_ = std::make_unique<CMsgqZmq>(MSGQ_PROTOCOL::PUB, CConfig::instance().MKT_DATA_PUBSUB_PORT);
		// 	msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().MKT_DATA_PUBSUB_PORT);
		// }
		// else {
		// 	msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().MKT_DATA_PUBSUB_PORT,false);
		// }
		msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().MKT_DATA_PUBSUB_PORT,false);
	}

	marketdatafeed::~marketdatafeed() {
		
	}

	void marketdatafeed::processMarketMessages() {
		if (!heatbeat(5)) {
			disconnectFromMarketDataFeed();
			return;
		}
		switch (_mkstate) {
		case MK_ACCOUNT:
			requestMarketDataAccountInformation(CConfig::instance().account);
			break;
		case MK_ACCOUNTACK:
			break;
		case MK_REQCONTRACT:
			requestContractDetails();
			break;
		case MK_REQCONTRACT_ACK:
			break;
			//case MK_REQHISTBAR:
			//  requestHistData();
			//  break;
		case MK_REQREALTIMEDATA:
			if (_mode == TICKBAR) {
				subscribeMarketData();
			}
			else if (_mode == DEPTH) {
				subscribeMarketDepth();
			}
			break;
		case MK_REQREALTIMEDATAACK:
			break;
		case MK_STOP:
			disconnectFromMarketDataFeed();
			break;
		}
	}
}