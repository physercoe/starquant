#ifndef _StarQuant_Brokers_IBBrokerage_H_
#define _StarQuant_Brokers_IBBrokerage_H_
#include <Brokers/IB/Official/EWrapper.h>
#include <Brokers/IB/Official/EReaderOSSignal.h>
#include <Brokers/IB/Official/EClientSocket.h>
#include <Brokers/IB/Official/EReader.h>
#include <Brokers/IB/Official/Contract.h>
#include <Brokers/IB/Official/Order.h>
#include <Brokers/IB/Official/Execution.h>
#include <Brokers/IB/Official/OrderState.h>

#include <Common/config.h>
#include <Common/Brokerage/brokerage.h>
#include <Common/Data/marketdatafeed.h>
#include <mutex>
#include <string>
#include <memory>

using std::mutex;
using std::string;
using std::list;
using std::vector;
using namespace IBOfficial;

namespace StarQuant
{
	class IBOfficial::EReaderOSSignal;
	class IBOfficial::EClientSocket;
	class IBOfficial::EReader;
	class brokerage;
	class marketdatafeed;
	class IBBrokerage : public IBOfficial::EWrapper, public brokerage, public marketdatafeed
	{
	public:
		IBBrokerage();
		~IBBrokerage();
		int _nServerVersion;

	public: 
		// outgoing
		//********************************************************************************//
		// brokerate part
		virtual void processBrokerageMessages();
		// let brokerage depend on marketdatafeed, that is
		// brokerage doesn't really connect; it relays to marekt data
		virtual bool connectToBrokerage();
		virtual void disconnectFromBrokerage();
		virtual bool isConnectedToBrokerage() const;

		virtual void placeOrder(std::shared_ptr<Order> o);
		virtual void requestNextValidOrderID();

		// TODO: move them to OrderManagement; only cancelOrder is necessary
		virtual void cancelOrder(int oid);
		virtual void cancelOrders(const string& symbol);
		virtual void cancelOrder(const string& ono);
		virtual void cancelAllOrders();

		//https://www.interactivebrokers.com/en/software/api/apiguide/java/reqaccountupdates.htm
		// subscribe = true
		virtual void requestBrokerageAccountInformation(const string& account_);
		virtual void requestOpenOrders(const string& account_);
		virtual void requestOpenPositions(const string& account_);

		/*Modifying an Order
		To modify an order using the API, resubmit the order you want to modify using the same order
		id, but with the price or quantity modified as required. Only certain fields such as price or
		quantity can be altered using this method. If you want to change the order type or action, you
		will have to cancel the order and submit a new order.
		*/
		void modifyOrder_SameT(uint64_t oid, double price, int quantity);

		//https://www.interactivebrokers.com/en/software/api/apiguide/c/exerciseoptions.htm
		/*void exerciseOptions(TickerId id, const Contract &contract,
			int exerciseAction, int exerciseQuantity, const std::string &account,
			int override);*/

		/*Call this function to request the open orders that were placed from this client.
		Each open order will be fed back through the openOrder() and orderStatus() functions on the EWrapper.

		Note: The client with a clientId of 0 will also receive the TWS-owned open orders.
		These orders will be associated with the client and a new orderId will be generated.
		This association will persist over multiple API and TWS sessions.*/
		void requestOpenOrders();
		/*Call this function to request the open orders placed from all clients and also from TWS.
		Each open order will be fed back through the openOrder() and orderStatus() functions on the EWrapper.
		Note:  No association is made between the returned orders and the requesting client.*/
		void reqAllOpenOrders();
		/*Call this function to request that newly created TWS orders be implicitly associated with the client.
		When a new TWS order is created, the order will be associated with the client,
		and fed back through the openOrder() and orderStatus() functions on the EWrapper.
		Note:  This request can only be made from a client with clientId of 0.
		If set to TRUE, newly created TWS orders will be implicitly associated with the client.
		If set to FALSE, no association will be made.*/
		void reqAutoOpenOrders(bool);

		// end of brokerage part
		//********************************************************************************//

		//********************************************************************************//
		// market data part
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
		virtual void requestHistoricalData(string fullsymbol, string enddate, string duration, string barsize, string useRTH);
		virtual void requestMarketDataAccountInformation(const string& account);
		// end of market data part
		//********************************************************************************//

	public:
		// events from EWrapper
		void tickPrice(TickerId tickerId, TickType field, double price, int canAutoExecute);
		void tickSize(TickerId tickerId, TickType field, int size);
		void tickOptionComputation(TickerId tickerId, TickType tickType, double impliedVol, double delta,
			double optPrice, double pvDividend, double gamma, double vega, double theta, double undPrice) {}
		void tickGeneric(TickerId tickerId, TickType tickType, double value) {}
		void tickString(TickerId tickerId, TickType tickType, const std::string& value) {}
		void tickEFP(TickerId tickerId, TickType tickType, double basisPoints, const std::string& formattedBasisPoints,
			double totalDividends, int holdDays, const std::string& futureExpiry, double dividendImpact, double dividendsToExpiry) {}
		
		void orderStatus(OrderId orderId, const std::string& status, double filled,
			double remaining, double avgFillPrice, int permId, int parentId,
			double lastFillPrice, int clientId, const std::string& whyHeld);
		void openOrder(OrderId oid, const Contract& contract, const IBOfficial::Order& order, const OrderState& ostat);
		void openOrderEnd();
		void winError(const std::string &str, int lastError) {}
		void connectionClosed() {}
		void updateAccountValue(const std::string& key, const std::string& val,
			const std::string& currency, const std::string& accountName);
		void updatePortfolio(const Contract& contract, double position,
			double marketPrice, double marketValue, double averageCost,
			double unrealizedPNL, double realizedPNL, const std::string& accountName);
		void updateAccountTime(const std::string& timeStamp);
		void accountDownloadEnd(const std::string& accountName) {}
		void nextValidId(IBOfficial::OrderId orderId);
		void contractDetails(int reqId, const ContractDetails& contractDetails);
		void bondContractDetails(int reqId, const ContractDetails& contractDetails) {}
		void contractDetailsEnd(int reqId);
		void execDetails(int reqId, const Contract& contract, const Execution& execution);
		void execDetailsEnd(int reqId) {}
		void error(const int id, const int errorCode, const std::string errorString);
		void updateMktDepth(TickerId id, int position, int operation, int side,
			double price, int size);
		void updateMktDepthL2(TickerId id, int position, std::string marketMaker, int operation,
			int side, double price, int size);
		void updateNewsBulletin(int msgId, int msgType, const std::string& newsMessage, const std::string& originExch) {}
		void managedAccounts(const std::string& accountsList);
		void receiveFA(faDataType pFaDataType, const std::string& cxml) {}
		void historicalData(TickerId reqId, const std::string& date, double open, double high,
			double low, double close, int volume, int barCount, double WAP, int hasGaps);
		void scannerParameters(const std::string &xml) {}
		void scannerData(int reqId, int rank, const ContractDetails &contractDetails,
			const std::string &distance, const std::string &benchmark, const std::string &projection,
			const std::string &legsStr) {}
		void scannerDataEnd(int reqId) {}
		void realtimeBar(TickerId reqId, long time, double open, double high, double low, double close,
			long volume, double wap, int count);
		void currentTime(long time) {}
		void fundamentalData(TickerId reqId, const std::string& data) {}
		void deltaNeutralValidation(int reqId, const UnderComp& underComp) {}
		void tickSnapshotEnd(int reqId) {}
		void marketDataType(TickerId reqId, int marketDataType) {}
		void commissionReport(const CommissionReport &commissionReport) {}
		void position(const std::string& account, const Contract& contract, double position, double avgCost) {}
		void positionEnd() {}
		void accountSummary(int reqId, const std::string& account, const std::string& tag, const std::string& value, const std::string& curency) {}
		void accountSummaryEnd(int reqId) {}
		void verifyMessageAPI(const std::string& apiData) {}
		void verifyCompleted(bool isSuccessful, const std::string& errorText) {}
		void displayGroupList(int reqId, const std::string& groups) {}
		void displayGroupUpdated(int reqId, const std::string& contractInfo) {}
		
		void verifyAndAuthMessageAPI(const std::string& apiData, const std::string& xyzChallange) {}
		void verifyAndAuthCompleted(bool isSuccessful, const std::string& errorText) {}
		void connectAck();
		void positionMulti(int reqId, const std::string& account, const std::string& modelCode, const Contract& contract, double pos, double avgCost) {}
		void positionMultiEnd(int reqId) {}
		void accountUpdateMulti(int reqId, const std::string& account, const std::string& modelCode, const std::string& key, const std::string& value, const std::string& currency) {}
		void accountUpdateMultiEnd(int reqId) {}
		void securityDefinitionOptionalParameter(int reqId, const std::string& exchange, int underlyingConId, const std::string& tradingClass, const std::string& multiplier, std::set<std::string> expirations, std::set<double> strikes) {}
		void securityDefinitionOptionalParameterEnd(int reqId) {}
		void softDollarTiers(int reqId, const std::vector<SoftDollarTier> &tiers) {}
	private:
		//! [socket_declare]
		EReaderOSSignal m_osSignal;
		EClientSocket* const m_pClient;	// std::auto_ptr<EPosixClientSocket> m_pClient; or unique_ptr
		//! [socket_declare]
		time_t m_sleepDeadline;
		EReader *m_pReader;
		bool m_extraAuth;
		std::vector<double> lastPriceCache_;
		std::vector<double> bidPriceCache_;
		std::vector<double> askPriceCache_;

		const int BARREQUESTSTARTINGPOINT = 1000;			// reqRealTimeBars request id starting point
		// ***********************************************************************************************
		// auxiliary functions
		// ***********************************************************************************************
		void SecurityFullNameToContract(const std::string& symbol, Contract& c);
		void ContractToSecurityFullName(std::string& symbol, const Contract& c);
		void OrderToIBOfficialOrder(std::shared_ptr<Order> o, IBOfficial::Order& oib);
		string OrderTypeToIBOrderType(const StarQuant::OrderType & ot);
		StarQuant::OrderType IBOrderTypeToOrderType(const string & ibot);
	};
}

#endif // _StarQuant_Brokers_IBBrokerage_H_
