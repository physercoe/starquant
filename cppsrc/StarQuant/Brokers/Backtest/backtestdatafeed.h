#ifndef _StarQuant_Brokers_BacktestDataFeed_H_
#define _StarQuant_Brokers_BacktestDataFeed_H_

#include <mutex>
#include <Common/config.h>
#include <Common/Data/marketdatafeed.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
	struct Security;

	class backtestdatafeed : public marketdatafeed {
	public:
		backtestdatafeed();
		~backtestdatafeed();

		virtual void processMarketMessages();
		virtual bool connectToMarketDataFeed();
		virtual void disconnectFromMarketDataFeed();
		virtual bool isConnectedToMarketDataFeed() const;

		virtual void subscribeMarketData();
		virtual void unsubscribeMarketData(TickerId reqId);
		virtual void subscribeMarketDepth();
		virtual void unsubscribeMarketDepth(TickerId reqId);
		virtual void subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH);
		virtual void unsubscribeRealTimeBars(TickerId tickerId);
		virtual void requestContractDetails();
		virtual void requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH);
		virtual void requestMarketDataAccountInformation(const string& account);

	public:
		// events

	private:
		void Thread_GetQuoteLoop();
	};
}

#endif
