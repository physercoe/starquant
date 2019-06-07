#ifndef _StarQuant_Engine_TapMDEngine_H_
#define _StarQuant_Engine_TapMDEngine_H_

#include <mutex>
#include <Common/config.h>
#include <Engine/IEngine.h>
#include <APIs/Tap/TapQuoteAPI.h>
#include <APIs/Tap/TapAPIError.h>

using std::mutex;
using std::string;
using std::list;
using std::vector;

namespace StarQuant
{

class TapMDEngine : public IEngine, ITapQuoteAPINotify {
public:
    string name_;
    Gateway tapacc_;
    TapMDEngine();
    ~TapMDEngine();

    virtual void init();
    virtual void start();
    virtual void stop();
    virtual bool connect() ;
    virtual bool disconnect() ;
    
    void subscribe(const string& symbol) ;
    void unsubscribe(const string& symbol) ; 
    void query(const MSG_TYPE & _type,const string& symbol);

public:
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
    uint32_t sessionId_;
    ITapQuoteAPI* api_;	
    TapAPIContract stContract_;	

};
}
template<size_t size> inline void APIStrncpy(char (&Dst)[size], const char* source)
{
#ifdef _WIN32
    strncpy_s(Dst, source, sizeof(Dst) - 1);
#else  
    strncpy(Dst, source, sizeof(Dst));
    //Dst[size] = '\0';
#endif
}
#endif
