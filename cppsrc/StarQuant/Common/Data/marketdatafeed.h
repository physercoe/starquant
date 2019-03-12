#ifndef _StarQuant_Data_MarketDataFeed_H_
#define _StarQuant_Data_MarketDataFeed_H_
#include <Common/config.h>
#include <Common/Time/heartbeat.h>
#include <Common/Time/getRealTime.h>		// struct timeval
#include <Common/Data/datatype.h>
#include <Common/Security/security.h>
#include <Common/Msgq/msgq.h>

using std::string;
using std::vector;
using std::pair;

namespace StarQuant
{
	typedef long TickerId;			// every subscription has a ticker id
	enum MKState {				// market data state
		MK_DISCONNECTED,
		MK_CONNECTED,
		MK_ACCOUNT,				// market data account vs brokerage account
		MK_ACCOUNTACK,
		MK_REQCONTRACT,			// TODO: delete request contract and Ack
		MK_REQCONTRACT_ACK,
		MK_REQREALTIMEDATA,
		MK_REQREALTIMEDATAACK,
		MK_STOP
	};

	///market data's category
	/// - tick data
	/// - real time bar data
	/// - market depth
	enum MKDMODECAT {
		TICKBAR = 0, DEPTH
	};

	class marketdatafeed : public CHeartbeat {			// do not use virtual public, see diamond problem
	protected:
		struct timeval timeout;
		std::unique_ptr<CMsgq> msgq_pub_;

	public:
		//vector<string> accounts;
		MKState _mkstate;
		MKDMODECAT _mode;

		marketdatafeed();
		~marketdatafeed();

		virtual void processMarketMessages();
		virtual bool connectToMarketDataFeed() = 0;
		virtual void disconnectFromMarketDataFeed() = 0;
		virtual bool isConnectedToMarketDataFeed() const = 0;

		//https://www.interactivebrokers.com/en/software/api/apiguide/tables/generic_tick_types.htm
		virtual void subscribeMarketData() = 0;
		virtual void unsubscribeMarketData(TickerId reqId) = 0;
		virtual void subscribeMarketDepth() = 0;
		virtual void unsubscribeMarketDepth(TickerId reqId) = 0;
		virtual void subscribeRealTimeBars(TickerId id, const Security& contract, int barSize, const string& whatToShow, bool useRTH) = 0;
		virtual void unsubscribeRealTimeBars(TickerId tickerId) = 0;
		virtual void requestContractDetails() = 0;
		virtual void requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH) = 0;
		virtual void requestMarketDataAccountInformation(const string& account) = 0;
	};
}

#endif		// _StarQuant_Data_MarketDataFeed_H_