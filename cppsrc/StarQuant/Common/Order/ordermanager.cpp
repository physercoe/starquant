#include <Common/Order/ordermanager.h>
#include <Common/Security/portfoliomanager.h>

namespace StarQuant {
	long m_serverOrderId = 0;    // unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
	std::mutex oid_mtx;			 // mutex for increasing order id
	std::mutex orderStatus_mtx;  // mutex for changing order status

	OrderManager* OrderManager::pinstance_ = nullptr;
	mutex OrderManager::instancelock_;

	OrderManager::OrderManager() : _count(0)
	{
		// set up stocks from config
		reset();
	}

	OrderManager::~OrderManager()
	{
		// release all the orders
	}

	OrderManager& OrderManager::instance() {
		if (pinstance_ == nullptr) {
			lock_guard<mutex> g(instancelock_);
			if (pinstance_ == nullptr) {
				pinstance_ = new OrderManager();
			}
		}
		return *pinstance_;
	}

	void OrderManager::reset() {
		_orders.clear();
		_fills.clear();
		_cancels.clear();

		_count = 0;
	}

	void OrderManager::trackOrder(std::shared_ptr<Order> o)
	{
		if (o->orderSize == 0) {
			PRINT_TO_FILE("ERROR:[%s,%d][%s]%s\n", __FILE__, __LINE__, __FUNCTION__, "Incorrect OrderSize.");
			return;
		}

		auto iter = _orders.find(o->serverOrderId);
		if (iter != _orders.end())			// order exists
			return;

		_orders[o->serverOrderId] = o;		// add to map
		_cancels[o->serverOrderId] = false;
		_fills[o->serverOrderId] = 0;

		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Order is put under track. ServerOrderId=%d\n", __FILE__, __LINE__, __FUNCTION__, o->serverOrderId);
	}

	void OrderManager::gotOrder(long oid)
	{
		if (!isTracked(oid))
		{
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Order is not tracked. ServerOrderId= %d\n", __FILE__, __LINE__, __FUNCTION__, oid);
			return;
		}

		lock_guard<mutex> g(orderStatus_mtx);
		if ((_orders[oid]->orderStatus == OrderStatus::OS_NewBorn) || (_orders[oid]->orderStatus == OrderStatus::OS_Submitted))
		{
			_orders[oid]->orderStatus = OrderStatus::OS_Acknowledged;
		}
	}

	void OrderManager::gotFill(Fill& fill)
	{
		if (!isTracked(fill.serverOrderId))
		{
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Order is not tracked. ServerOrderId= %d\n", __FILE__, __LINE__, __FUNCTION__, fill.serverOrderId);
		}
		else {
			PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Order is filled. ServerOrderId=%d, price=%.2f\n", __FILE__, __LINE__, __FUNCTION__, fill.serverOrderId, fill.tradePrice);
			lock_guard<mutex> g(orderStatus_mtx);
			_orders[fill.serverOrderId]->orderStatus = OrderStatus::OS_Filled;			
			// TODO: check for partial fill

			PortfolioManager::instance().Adjust(fill);
		}
	}

	void OrderManager::gotCancel(long oid)
	{
		if (isTracked(oid))
		{
			lock_guard<mutex> g(orderStatus_mtx);
			_orders[oid]->orderStatus = OrderStatus::OS_Canceled;
			_cancels[oid] = true;
		}
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromServerOrderId(long oid) {
		if (_orders.count(oid))         // return # of matches; either 0 or 1
		{
			return _orders[oid];
		}
		return nullptr;
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromBrokerOrderId(long oid) {
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if (iterator->second->brokerOrderId == oid)
			{
				return iterator->second;
			}
		}

		return nullptr;
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromBrokerOrderIdAndApi(long oid, string acc) {
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if ((iterator->second->brokerOrderId == oid) && (iterator->second->account == acc))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}
	std::shared_ptr<Order> OrderManager::retrieveOrderFromOrderNo(string ono) {
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if ((iterator->second->orderNo == ono))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromMatchNo(string fno) {
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if ((iterator->second->fillNo == fno))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}


	vector<std::shared_ptr<Order>> OrderManager::retrieveOrder(const string& fullsymbol) {
		vector<std::shared_ptr<Order>> v;
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if (iterator->second->fullSymbol == fullsymbol)
			{
				v.push_back(iterator->second);
			}
		}

		return v;
	}

	vector<std::shared_ptr<Order>> OrderManager::retrieveNonFilledOrderPtr() {
		vector<std::shared_ptr<Order>> v;
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if (!isCompleted(iterator->first))
			{
				v.push_back(iterator->second);
			}
		}

		return v;
	}

	vector<std::shared_ptr<Order>> OrderManager::retrieveNonFilledOrderPtr(const string& fullsymbol) {
		vector<std::shared_ptr<Order>> v;
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if ((!isCompleted(iterator->first)) && (iterator->second->fullSymbol == fullsymbol))
			{
				v.push_back(iterator->second);
			}
		}

		return v;
	}

	vector<long> OrderManager::retrieveNonFilledOrderId() {
		vector<long> v;
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if (!isCompleted(iterator->first))
			{
				v.push_back(iterator->first);
			}
		}

		return v;
	}

	vector<long> OrderManager::retrieveNonFilledOrderId(const string& fullsymbol) {
		vector<long> v;
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if ((!isCompleted(iterator->first)) && (iterator->second->fullSymbol == fullsymbol))
			{
				v.push_back(iterator->first);
			}
		}

		return v;
	}

	bool OrderManager::isEmpty()
	{
		return false;
	}

	bool OrderManager::isTracked(long oid) {
		auto it = _orders.find(oid);
		return (it != _orders.end());
	}

	bool OrderManager::isFilled(long oid) { return false; }
	bool OrderManager::isCanceled(long oid) { return false; }

	bool OrderManager::isCompleted(long oid) {
		return (isFilled(oid) || isCanceled(oid));
	}

	bool OrderManager::hasPendingOrders() {
		for (auto iterator = _orders.begin(); iterator != _orders.end(); ++iterator) {
			if (!isCompleted(iterator->first))
			{
				return true;
			}
		}
		return false;
	}
}