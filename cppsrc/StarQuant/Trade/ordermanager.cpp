#include <Trade/ordermanager.h>
#include <Trade/portfoliomanager.h>
#include <Common/logger.h>
#include <Common/datastruct.h>
namespace StarQuant {

	//extern long m_serverOrderId ;    // unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
	//extern std::mutex oid_mtx;			 // mutex for increasing order id
	//extern std::mutex orderStatus_mtx;  // mutex for changing order status

	OrderManager* OrderManager::pinstance_ = nullptr;
	mutex OrderManager::instancelock_;

	OrderManager::OrderManager() : _count(0)
	{
		// set up stocks from config
		reset();
		logger = SQLogger::getLogger("SYS");
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
		orders_.clear();
		fills_.clear();
		cancels_.clear();

		_count = 0;
	}

	void OrderManager::trackOrder(std::shared_ptr<Order> o)
	{
		if (o->orderSize_ == 0) {
			LOG_ERROR(logger,"Incorrect OrderSize.");			
			return;
		}

		auto iter = orders_.find(o->serverOrderID_);
		if (iter != orders_.end())			// order exists
			return;

		orders_[o->serverOrderID_] = o;		// add to map
		cancels_[o->serverOrderID_] = false;
		fills_[o->serverOrderID_] = 0;
		LOG_INFO(logger,"Order is put under track. ServerOrderId="<<o->serverOrderID_);
	}

	void OrderManager::gotOrder(long oid)
	{
		if (!isTracked(oid))
		{
			LOG_ERROR(logger,"Order is not tracked. ServerOrderId= "<<oid);
			return;
		}

		lock_guard<mutex> g(orderStatus_mtx);
		if ((orders_[oid]->orderStatus_ == OrderStatus::OS_NewBorn) || (orders_[oid]->orderStatus_ == OrderStatus::OS_Submitted))
		{
			orders_[oid]->orderStatus_ = OrderStatus::OS_Acknowledged;
		}
	}

	void OrderManager::gotFill(Fill& fill)
	{
		if (!isTracked(fill.serverOrderID_))
		{
			LOG_ERROR(logger,"Order is not tracked. ServerOrderId= "<<fill.serverOrderID_);			
		}
		else {
			LOG_INFO(logger,"Order is filled. ServerOrderId="<<fill.serverOrderID_<<"price = "<<fill.tradePrice_);
			lock_guard<mutex> g(orderStatus_mtx);
			orders_[fill.serverOrderID_]->orderStatus_ = OrderStatus::OS_Filled;			
			// TODO: check for partial fill
			PortfolioManager::instance().Adjust(fill);
		}
	}

	void OrderManager::gotCancel(long oid)
	{
		if (isTracked(oid))
		{
			lock_guard<mutex> g(orderStatus_mtx);
			orders_[oid]->orderStatus_ = OrderStatus::OS_Canceled;
			cancels_[oid] = true;
		}
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromServerOrderId(long oid) {
		if (orders_.count(oid))         // return # of matches; either 0 or 1
		{
			return orders_[oid];
		}
		return nullptr;
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromBrokerOrderId(long oid) {
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if (iterator->second->brokerOrderID_ == oid)
			{
				return iterator->second;
			}
		}

		return nullptr;
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromBrokerOrderIdAndApi(long oid, string acc) {
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if ((iterator->second->brokerOrderID_ == oid) && (iterator->second->account_ == acc))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}
	std::shared_ptr<Order> OrderManager::retrieveOrderFromSourceAndClientOrderId(int source, long oid) {
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if ((iterator->second->clientOrderID_ == oid) && (iterator->second->clientID_ == source))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}



	std::shared_ptr<Order> OrderManager::retrieveOrderFromOrderNo(string ono) {
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if ((iterator->second->orderNo_ == ono))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}

	std::shared_ptr<Order> OrderManager::retrieveOrderFromMatchNo(string fno) {
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if ((iterator->second->fillNo_ == fno))
			{
				return iterator->second;
			}
		}

		return nullptr;
	}


	vector<std::shared_ptr<Order>> OrderManager::retrieveOrder(const string& fullsymbol) {
		vector<std::shared_ptr<Order>> v;
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if (iterator->second->fullSymbol_ == fullsymbol)
			{
				v.push_back(iterator->second);
			}
		}

		return v;
	}

	vector<std::shared_ptr<Order>> OrderManager::retrieveNonFilledOrderPtr() {
		vector<std::shared_ptr<Order>> v;
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if (!isCompleted(iterator->first))
			{
				v.push_back(iterator->second);
			}
		}

		return v;
	}

	vector<std::shared_ptr<Order>> OrderManager::retrieveNonFilledOrderPtr(const string& fullsymbol) {
		vector<std::shared_ptr<Order>> v;
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if ((!isCompleted(iterator->first)) && (iterator->second->fullSymbol_ == fullsymbol))
			{
				v.push_back(iterator->second);
			}
		}

		return v;
	}

	vector<long> OrderManager::retrieveNonFilledOrderId() {
		vector<long> v;
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if (!isCompleted(iterator->first))
			{
				v.push_back(iterator->first);
			}
		}

		return v;
	}

	vector<long> OrderManager::retrieveNonFilledOrderId(const string& fullsymbol) {
		vector<long> v;
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if ((!isCompleted(iterator->first)) && (iterator->second->fullSymbol_ == fullsymbol))
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
		auto it = orders_.find(oid);
		return (it != orders_.end());
	}

	bool OrderManager::isFilled(long oid) { return false; }
	bool OrderManager::isCanceled(long oid) { return false; }

	bool OrderManager::isCompleted(long oid) {
		return (isFilled(oid) || isCanceled(oid));
	}

	bool OrderManager::hasPendingOrders() {
		for (auto iterator = orders_.begin(); iterator != orders_.end(); ++iterator) {
			if (!isCompleted(iterator->first))
			{
				return true;
			}
		}
		return false;
	}
}