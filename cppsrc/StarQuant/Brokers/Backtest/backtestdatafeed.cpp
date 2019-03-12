#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>

#include <Brokers/Backtest/backtestdatafeed.h>
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

	backtestdatafeed::backtestdatafeed() {
		/* initialize random seed: */
		srand(time(NULL));
	}

	backtestdatafeed::~backtestdatafeed() {
	}

	// start http request thread
	bool backtestdatafeed::connectToMarketDataFeed()
	{
		return true;
	}

	// stop http request thread
	void backtestdatafeed::disconnectFromMarketDataFeed() {
	}

	// is http request thread running ?
	bool backtestdatafeed::isConnectedToMarketDataFeed() const {
		return (!gShutdown);				// automatic disconnect when shutdown
	}

	void backtestdatafeed::processMarketMessages() {
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

	void backtestdatafeed::subscribeMarketData() {
		_mkstate = MK_REQREALTIMEDATAACK;
	}

	void backtestdatafeed::unsubscribeMarketData(TickerId reqId) {
	}

	void backtestdatafeed::subscribeMarketDepth() {
	}

	void backtestdatafeed::unsubscribeMarketDepth(TickerId reqId) {
	}

	void backtestdatafeed::subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH) {

	}

	void backtestdatafeed::unsubscribeRealTimeBars(TickerId tickerId) {

	}

	void backtestdatafeed::requestContractDetails() {
	}

	void backtestdatafeed::requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH) {

	}

	void backtestdatafeed::requestMarketDataAccountInformation(const string& account)
	{
		if (_mkstate <= MK_REQREALTIMEDATA)
			_mkstate = MK_REQREALTIMEDATA;
	}

	////////////////////////////////////////////////////// worker function ///////////////////////////////////////
	void backtestdatafeed::Thread_GetQuoteLoop()
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