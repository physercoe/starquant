#ifndef _StarQuant_Trade_OrderManager_H_
#define _StarQuant_Trade_OrderManager_H_
#include <string>
#include <map>
#include <mutex>
#include <atomic>
#include <Common/datastruct.h>
#include <Common/logger.h>

using namespace std;

namespace StarQuant {
	//extern long m_serverOrderId;				// unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
	//extern std::mutex oid_mtx;					// mutex for increasing order id; defined in ordermanager.cpp
	//extern std::mutex orderStatus_mtx;			// mutex for changing order status; defined in ordermanager.cpp

	// TODO: maintain order book
	class OrderManager {
	public:
		OrderManager();
		~OrderManager();				// release all the orders
		static OrderManager* pinstance_;
		static mutex instancelock_;
		static OrderManager& instance();

		//std::atomic_int _count = { 0 };
		std::shared_ptr<SQLogger> logger;
		int _count = 0;
		std::map<long, std::shared_ptr<Order>> orders_;
		std::map<long, long> fills_;       // signed filled size
		std::map<long, bool> cancels_;    // if cancelled
		mutex wlock;
		void reset();

		void trackOrder(std::shared_ptr<Order> o);		// put order under track
		void gotOrder(long oid);						// order acknowledged
		void gotFill(Fill& fill);
		void gotCancel(long oid);
		std::shared_ptr<Order> retrieveOrderFromServerOrderId(long oid);
		std::shared_ptr<Order> retrieveOrderFromBrokerOrderId(long oid);
		std::shared_ptr<Order> retrieveOrderFromBrokerOrderIdAndApi(long oid, string acc);
		std::shared_ptr<Order> retrieveOrderFromSourceAndClientOrderId(int source, long oid);
		std::shared_ptr<Order> retrieveOrderFromOrderNo(string ono);
		std::shared_ptr<Order> retrieveOrderFromMatchNo(string fno);
		vector<std::shared_ptr<Order>> retrieveOrder(const string& fullsymbol);
		vector<std::shared_ptr<Order>> retrieveNonFilledOrderPtr();
		vector<std::shared_ptr<Order>> retrieveNonFilledOrderPtr(const string& fullsymbol);
		vector<long> retrieveNonFilledOrderId();
		vector<long> retrieveNonFilledOrderId(const string& fullsymbol);

		bool isEmpty();
		bool isTracked(long oid);
		bool isFilled(long oid);
		bool isCanceled(long oid);
		bool isCompleted(long oid);		// either filled or canceled
		bool hasPendingOrders();		// is all orders either filled or canceled?
	};
}

#endif  // _StarQuant_Common_OrderManager_H_