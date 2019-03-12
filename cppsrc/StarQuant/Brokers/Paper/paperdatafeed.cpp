#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>

#include <Brokers/Paper/paperdatafeed.h>
#include <Common/Util/util.h>
#include <Common/Order/orderstatus.h>
#include <Common/Logger/logger.h>
#include <Common/Data/datamanager.h>
#include <Common/Order/ordermanager.h>

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

using namespace std;

namespace StarQuant
{
	extern std::atomic<bool> gShutdown;

	paperdatafeed::paperdatafeed() {
		/* initialize random seed: */
		srand(time(NULL));
	}

	paperdatafeed::~paperdatafeed() {
	}

	// start http request thread
	bool paperdatafeed::connectToMarketDataFeed()
	{
		return true;
	}

	// stop http request thread
	void paperdatafeed::disconnectFromMarketDataFeed() {
	}

	// is http request thread running ?
	bool paperdatafeed::isConnectedToMarketDataFeed() const {
		return (!gShutdown);				// automatic disconnect when shutdown
	}

	void paperdatafeed::processMarketMessages() {
		if (!heatbeat(5)) {
			disconnectFromMarketDataFeed();
			return;
		}

		switch (_mkstate) {
		case MK_ACCOUNT:
			requestMarketDataAccountInformation(CConfig::instance().account);
			break;
		case MK_REQREALTIMEDATA:
			subscribeMarketData();
			break;
		case MK_REQREALTIMEDATAACK:
			Thread_GetQuoteLoop();
			break;
		}
	}

	void paperdatafeed::subscribeMarketData() {
		_mkstate = MK_REQREALTIMEDATAACK;
	}

	void paperdatafeed::unsubscribeMarketData(TickerId reqId) {
	}

	void paperdatafeed::subscribeMarketDepth() {
	}

	void paperdatafeed::unsubscribeMarketDepth(TickerId reqId) {
	}

	void paperdatafeed::subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH) {

	}

	void paperdatafeed::unsubscribeRealTimeBars(TickerId tickerId) {

	}

	void paperdatafeed::requestContractDetails() {
	}

	void paperdatafeed::requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH) {

	}

	void paperdatafeed::requestMarketDataAccountInformation(const string& account)
	{
		if (_mkstate <= MK_REQREALTIMEDATA)
			_mkstate = MK_REQREALTIMEDATA;
	}

	////////////////////////////////////////////////////// worker function ///////////////////////////////////////
	void paperdatafeed::Thread_GetQuoteLoop()
	{
		std::string res = "";

		while (!gShutdown) {
			try {
				for (auto &s : CConfig::instance().securities)
				{
					Tick k;
					k.time_ = hmsf();
					k.fullsymbol_ = s;
					k.datatype_ = DataType::DT_Trade;
					k.price_ = (rand() % 100 + 1000) / 10.0;
					k.size_ = 100;
					msgq_pub_->sendmsg(k.serialize());
					msleep(200);
				}
			}
			catch (std::exception& e) {
				std::cout << "Exception: " << e.what() << "\n";
			}

			msleep(2000);
		}
	}
}