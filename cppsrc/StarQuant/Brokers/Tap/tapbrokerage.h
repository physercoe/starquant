#ifndef _StarQuant_Brokers_TapBrokerage_H_
#define _StarQuant_Brokers_TapBrokerage_H_

#include <mutex>
#include <Common/config.h>
#include <Common/Brokerage/brokerage.h>
#include <Brokers/Tap/TapTradeAPI.h>
#include <Brokers/Tap/TapAPIError.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
	struct Security;

	class Tapbrokerage : public brokerage, ITapTradeAPINotify {
	public:
		Tapbrokerage();
		~Tapbrokerage();
//本交易程序的接口函数
		virtual void processBrokerageMessages();
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
		virtual void cancelOrder(const string& ono);
		virtual void cancelOrders(const string& symbols);
		//cancelAllOrders is not reentrant!
		virtual void cancelAllOrders();

		virtual void requestBrokerageAccountInformation(const string& account_);
		virtual void requestOpenOrders(const string& account_);
		virtual void requestOpenPositions(const string& account_);

		///客户端认证请求
		void requestAuthenticate(string userid, string authcode, string brokerid, string userproductinfo);
		///用户登录请求
		void requestUserLogin();
		///用户登录请求
		void requestUserLogout();
		void requestSettlementInfoConfirm();
		// void requestAccount();		// see requestBrokerageAccountInformation
	public:
        //调用Tap API回调函数
		// Call back functions

	virtual void TAP_CDECL OnConnect();
	virtual void TAP_CDECL OnRspLogin(TAPIINT32 errorCode, const TapAPITradeLoginRspInfo *loginRspInfo);
	virtual void TAP_CDECL OnAPIReady();
	virtual void TAP_CDECL OnDisconnect(TAPIINT32 reasonCode);
	virtual void TAP_CDECL OnRspChangePassword(TAPIUINT32 sessionID, TAPIINT32 errorCode);
	virtual void TAP_CDECL OnRspSetReservedInfo(TAPIUINT32 sessionID, TAPIINT32 errorCode, const TAPISTR_50 info);
	virtual void TAP_CDECL OnRspQryAccount(TAPIUINT32 sessionID, TAPIUINT32 errorCode, TAPIYNFLAG isLast, const TapAPIAccountInfo *info);
	virtual void TAP_CDECL OnRspQryFund(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIFundData *info);
	virtual void TAP_CDECL OnRtnFund(const TapAPIFundData *info);
	virtual void TAP_CDECL OnRspQryExchange(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIExchangeInfo *info);
	virtual void TAP_CDECL OnRspQryCommodity(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPICommodityInfo *info);
	virtual void TAP_CDECL OnRspQryContract(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPITradeContractInfo *info);
	virtual void TAP_CDECL OnRtnContract(const TapAPITradeContractInfo *info);
	virtual void TAP_CDECL OnRtnOrder(const TapAPIOrderInfoNotice *info);
	virtual void TAP_CDECL OnRspOrderAction(TAPIUINT32 sessionID, TAPIUINT32 errorCode, const TapAPIOrderActionRsp *info);
	virtual void TAP_CDECL OnRspQryOrder(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIOrderInfo *info);
	virtual void TAP_CDECL OnRspQryOrderProcess(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIOrderInfo *info);
	virtual void TAP_CDECL OnRspQryFill(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIFillInfo *info);
	virtual void TAP_CDECL OnRtnFill(const TapAPIFillInfo *info);
	virtual void TAP_CDECL OnRspQryPosition(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIPositionInfo *info);
	virtual void TAP_CDECL OnRtnPosition(const TapAPIPositionInfo *info);
	virtual void TAP_CDECL OnRspQryClose(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPICloseInfo *info);
	virtual void TAP_CDECL OnRtnClose(const TapAPICloseInfo *info);
	virtual void TAP_CDECL OnRtnPositionProfit(const TapAPIPositionProfitNotice *info);
	virtual void TAP_CDECL OnRspQryDeepQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIDeepQuoteQryRsp *info);
	virtual void TAP_CDECL OnRspQryExchangeStateInfo(TAPIUINT32 sessionID,TAPIINT32 errorCode, TAPIYNFLAG isLast,const TapAPIExchangeStateInfo * info);
	virtual void TAP_CDECL OnRtnExchangeStateInfo(const TapAPIExchangeStateInfoNotice * info);
	virtual void TAP_CDECL OnRtnReqQuoteNotice(const TapAPIReqQuoteNotice *info); //V9.0.2.0 20150520
	virtual void TAP_CDECL OnRspUpperChannelInfo(TAPIUINT32 sessionID,TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIUpperChannelInfo * info);
	virtual void TAP_CDECL OnRspAccountRentInfo(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIAccountRentInfo * info);




	private:
		bool isConnected_;
		bool isLogedin_;
		bool apiisready;
		bool isAuthenticated_;
		bool requireAuthentication_;
		int reqId_;							// 操作请求编号
		int orderRef_;						// 订单编号
		int frontID_;						// 前置机编号
		unsigned int sessionID_;						// 会话编号

		ITapTradeAPI* api_;			// TODO: change it to unique_ptr

//		string SecurityFullNameToTapSymbol(const std::string& symbol);
//		string TapSymbolToSecurityFullName(CThostFtdcInstrumentField * pInstrument);
		//string UTF8ToGBK(const std::string & strUTF8);
		//string GBKToUTF8(const std::string & strGBK);
		OrderStatus TapOrderStatusToOrderStatus(const TAPIOrderStateType);
		OrderFlag TapPositionEffectToOrderFlag(const TAPIPositionEffectType flag);
		OrderType TapOrderTypeToOrderType(const TAPIOrderTypeType type);

		TAPIPositionEffectType OrderFlagToTapPositionEffect(const OrderFlag flag);
		TAPIOrderTypeType OrderTypeToTapOrderType(const OrderType type);
	};
}

#endif
