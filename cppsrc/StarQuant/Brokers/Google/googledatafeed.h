#ifndef _StarQuant_Brokers_GoogleDataFeed_H_
#define _StarQuant_Brokers_GoogleDataFeed_H_

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

	class googledatafeed : public marketdatafeed {
	public:
		googledatafeed();
		~googledatafeed();

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
		//string host = R"(https://finance.google.com/finance/info?q=AAPL,EXC)";       // url+symbol
		string _host = "www.google.com";
		string _path = "/finance/info?q=AAPL,EXC";
		void Thread_GetQuoteLoop();
		//std::shared_ptr<std::thread> ptickthread;
	};
}

#endif
