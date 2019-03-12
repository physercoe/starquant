#ifndef _StarQuant_Brokers_TapDataFeed_H_
#define _StarQuant_Brokers_TapDataFeed_H_

#include <mutex>
#include <Common/config.h>
#include <Common/Data/marketdatafeed.h>
#include <Brokers/Tap/TapQuoteAPI.h>
#include <Brokers/Tap/TapAPIError.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{
struct Security;

class Tapdatafeed : public marketdatafeed, ITapQuoteAPINotify {
public:
	Tapdatafeed();
	~Tapdatafeed();
//jiekou hanshu
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
	
//	void SetAPI(ITapQuoteAPI* pAPI);
//	void SetContact(TapAPIContract st,int idnum);
//	void RunTest();
//	static void * thread_run(void * tmp);
//huidiao hanshu	
	//对ITapQuoteAPINotify的实现
	virtual void TAP_CDECL OnRspLogin(TAPIINT32 errorCode, const TapAPIQuotLoginRspInfo *info);
	virtual void TAP_CDECL OnAPIReady();
	virtual void TAP_CDECL OnDisconnect(TAPIINT32 reasonCode);
	virtual void TAP_CDECL OnRspChangePassword(TAPIUINT32 sessionID, TAPIINT32 errorCode);
	virtual void TAP_CDECL OnRspQryExchange(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIExchangeInfo *info);
	virtual void TAP_CDECL OnRspQryCommodity(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteCommodityInfo *info);
	virtual void TAP_CDECL OnRspQryContract(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteContractInfo *info);
	virtual void TAP_CDECL OnRtnContract(const TapAPIQuoteContractInfo *info);
	virtual void TAP_CDECL OnRspSubscribeQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteWhole *info);
	virtual void TAP_CDECL OnRspUnSubscribeQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIContract *info);
	virtual void TAP_CDECL OnRtnQuote(const TapAPIQuoteWhole *info);


	
	
	
private:
	bool isConnected_;
	int loginReqId_;
	ITapQuoteAPI* api_;		// TODO: change it to unique_ptr
//	ITapQuoteAPI* m_pAPI;
	TapAPIContract stContract;
	TAPIUINT32	m_uiSessionID;
//	SimpleEvent m_Event;
	bool		IsAPIReady;
	int myID;
//	string SecurityFullNameToTapSymbol(const std::string& symbol);
//	string TapSymbolToSecurityFullName(const std::string& symbol);
};
}
template<size_t size> inline void APIStrncpy(char (&Dst)[size], const char* source)
{
#ifdef WIN32
    strncpy_s(Dst, source, sizeof(Dst) - 1);
#endif
    
#ifdef linux
    strncpy(Dst, source, sizeof(Dst));
    //Dst[size] = '\0';
#endif
}
#endif
