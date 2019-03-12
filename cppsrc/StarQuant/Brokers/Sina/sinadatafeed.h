#ifndef _StarQuant_Brokers_SinaDataFeed_H_
#define _StarQuant_Brokers_SinaDataFeed_H_

#include <mutex>
#include <Common/config.h>
#include <Common/Data/marketdatafeed.h>
#include <map>
#include <string>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
	struct Security;

	class sinadatafeed : public marketdatafeed {
	public:
		sinadatafeed();
		~sinadatafeed();

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
        std::map<std::string, double> pricemap;
		//string host = R"(http://hq.sinajs.cn/list=sh600000,sh600333)";       // url+symbol
		string _host = "hq.sinajs.cn";
		string _path = "/list=usr_spy,usr_aapl,usr_amzn,usr_tsla,usr_googl,usr_fb,usr_bidu,usr_baba,usr_gs,usr_jpm,sh600028,sh601857,sh600036,sh601668,sh601988,sh601166,sh601377,sh600958";			// TODO: not hard coded; get from subscription
		void Thread_GetQuoteLoop();
	};
}

#endif // _StarQuant_Brokers_SinaDataFeed_H_
