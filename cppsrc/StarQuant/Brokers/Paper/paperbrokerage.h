#ifndef _StarQuant_Brokers_PaperBrokerage_H_
#define _StarQuant_Brokers_PaperBrokerage_H_

#include <mutex>
#include <Common/config.h>
#include <Common/Brokerage/brokerage.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
	struct Security;

	class paperbrokerage : public brokerage {
	public:
		int delaytime;
		paperbrokerage(int dtime=0);
		~paperbrokerage();

		virtual bool connectToBrokerage();
		virtual void disconnectFromBrokerage();
		virtual bool isConnectedToBrokerage() const;

		virtual void placeOrder(std::shared_ptr<Order> order);
		virtual void requestNextValidOrderID();

		// Cancel Order
		/*Use this function to cancel all open orders globally.
		It cancels both API and TWS open orders.
		If the order was created in TWS, it also gets canceled.
		If the order was initiated in the API, it also gets canceled.*/
		void reqGlobalCancel();
		virtual void cancelOrder(int oid);
		virtual void cancelOrder(const string & ono);
		virtual void cancelOrders(const string& symbol);
		//cancelAllOrders is not reentrant!
		virtual void cancelAllOrders();

		//https://www.interactivebrokers.com/en/software/api/apiguide/java/reqaccountupdates.htm
		virtual void requestBrokerageAccountInformation(const string& account_);
		virtual void requestOpenOrders(const string& account_);
		virtual void requestOpenPositions(const string& account_);
	public:

	};
}

#endif // _StarQuant_Brokers_PaperBrokerage_H_
