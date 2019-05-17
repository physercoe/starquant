#ifndef __StarQuant_Common_Datastruct_H_
#define __StarQuant_Common_Datastruct_H_

#include <string>
#include <mutex>
#include <memory>
#include <vector>
#include <atomic>

#include <APIs/Ctp/ThostFtdcUserApiDataType.h>
#include <APIs/Ctp/ThostFtdcUserApiStruct.h>


using namespace std;


#if defined(_WIN32) || defined(_WIN64)
#ifdef DLL_EXPORT
#define DLL_EXPORT_IMPORT  __declspec(dllexport)   // export DLL information
#else
#define DLL_EXPORT_IMPORT  __declspec(dllimport)   // import DLL information
#endif
#else
#define DLL_EXPORT_IMPORT
#endif

namespace StarQuant {

// macro definations used 

#define SERIALIZATION_SEPARATOR '|'
#define RELAY_DESTINATION '@'
#define DESTINATION_ALL "*"
#define DESTINATION_SEPARATOR '.'
#define COMMODITY_SEPARATOR '&'

enum CurrencyType {
    USD,
    AUD,
    CAD,
    CHF,
    EUR,
    GBP,
    HKD,
    JPY,
    MXN,
    NZD,
    SEK
};
enum SymbolType {
    ST_Full = 0,
    ST_Ctp = 1
};
const std::string CurrencyTypeString[] = {
    "USD",
    "AUD",
    "CAD",
    "CHF",
    "EUR",
    "GBP",
    "HKD",
    "JPY",
    "MXN",
    "NZD",
    "SEK"
};
enum OrderType {
    OT_Market = 0,				// market
    OT_MarketOnClose,
    OT_Limit = 2,				// limit
    OT_LimitOnClose,
    OT_PeggedToMarket,
    OT_Stop = 5,				// stop
    OT_StopLimit = 6,			// stop limit
    OT_TrailingStop = 7,		// traiing stop
    OT_Relative,
    OT_VolumeWeightedAveragePrice,
    OT_TrailingStopLimit,
    OT_Volatility,
    OT_None,
    OT_Empty,
    OT_Default,
    OT_Scale,
    OT_MarketIfTouched,
    OT_LimitIfTouched,
    OT_OptExec,
    OT_OptAbandon,
    OT_Reqquot,
    OT_Rspquot,
    OT_Swap
};

enum OrderStatus {
    OS_UNKNOWN = 0,		// Unknown
    OS_NewBorn = 1,			// NewBorn
    OS_PendingSubmit = 2,   
    OS_Submitted = 3,			// submitted
    OS_Acknowledged = 4,		// acknowledged
    OS_Queued =5,
    OS_PartiallyFilled = 6,		// PartiallyFilled
    OS_Filled = 7,				// Filled
    OS_PendingCancel = 8 ,
    OS_PendingModify =9 ,
    OS_Canceled = 10,			// Canceled
    OS_LeftDelete = 11,
    OS_Suspended = 12,
    OS_ApiPending = 13,
    OS_ApiCancelled = 14,
    OS_Fail =15,                 //指令失败
    OS_Deleted =16,             
    OS_Effect = 17,             //已生效-询价成功
    OS_Apply = 18,              //已申请-行权，弃权等申请成功
    OS_Error = 19,
    OS_Trig =20,
    OS_Exctrig=21
};

enum OrderFlag {			// for CTP,tap offset flag
    OF_None = -1,
    OF_OpenPosition = 0,
    OF_ClosePosition = 1,
    OF_CloseToday = 2,
    OF_CloseYesterday = 3,
    OF_ForceClose = 4,
    OF_ForceOff = 5,
    OF_LocalForceClose = 6
};

const std::string OrderStatusString[] = {
    "Unknown",
    "NewBorn",
    "PendingSubmit",
    "Submitted",
    "Acknowledged",
    "Queued",
    "PartiallyFilled",
    "Filled",
    "PendingCancel",
    "PendingModify",
    "Canceled",
    "LeftDelete",
    "Suspended",
    "ApiPending",
    "ApiCancelled",
    "Fail",
    "Deleted",
    "Effect",
    "Apply",
    "Error",
    "Trigerrring",
    "ExcTriggering",
    "None"
};

enum class MSGQ : uint8_t {
	NANOMSG = 0, ZMQ, KAFKA, WEBSOCKET
};

enum class MSGQ_PROTOCOL : uint8_t {
	PAIR = 0, REQ, REP, PUB, SUB, PUSH,PULL
};
// -----------------------------msg type for interprocess communication-----------------
enum MSG_TYPE : int32_t {
  //  10* datatype same as ticktype 
    // furtures
    MSG_TYPE_TICK = 1000,
    MSG_TYPE_TICK_L1 = 1001,
    MSG_TYPE_TICK_L5 = 1002,
    MSG_TYPE_TICK_L10 = 1003,
    MSG_TYPE_TICK_L20 = 1004,
    MSG_TYPE_BAR = 1010,    
    MSG_TYPE_BAR_1MIN = 1011,
    MSG_TYPE_BAR_5MIN = 1012,
    MSG_TYPE_BAR_15MIN = 1013,
    MSG_TYPE_BAR_1HOUR = 1014,
    MSG_TYPE_BAR_1DAY = 1015,
    MSG_TYPE_BAR_1WEEK = 1016,
    MSG_TYPE_BAR_1MON = 1017,
    // stock 
    MSG_TYPE_STOCK_TICK = 1020,	
    MSG_TYPE_STOCK_BAR = 1021,
    // others
    MSG_TYPE_Trade =1060,
    MSG_TYPE_Bid = 1061,
    MSG_TYPE_Ask = 1062,
    MSG_TYPE_Full = 1063,
    MSG_TYPE_BidPrice = 1064,
    MSG_TYPE_BidSize = 1065,
    MSG_TYPE_AskPrice = 1066,
    MSG_TYPE_AskSize = 1067,
    MSG_TYPE_TradePrice = 1068,
    MSG_TYPE_TradeSize = 1069,
    MSG_TYPE_OpenPrice = 1070,
    MSG_TYPE_HighPrice = 1071,
    MSG_TYPE_LowPrice = 1072,
    MSG_TYPE_ClosePrice = 1073,
    MSG_TYPE_Volume = 1074,
    MSG_TYPE_OpenInterest = 1075,
    MSG_TYPE_Hist =1076,
  // 	11* sys control
    MSG_TYPE_ENGINE_STATUS = 1101,
    MSG_TYPE_ENGINE_START = 1111,
    MSG_TYPE_ENGINE_STOP = 1112,
    MSG_TYPE_ENGINE_RESET = 1113,
    MSG_TYPE_ENGINE_CONNECT = 1120,
    MSG_TYPE_ENGINE_DISCONNECT = 1121,
    MSG_TYPE_SWITCH_TRADING_DAY = 1141,
  //  12* strategy
    MSG_TYPE_STRATEGY_STATUS = 1200,
    MSG_TYPE_STRATEGY_ADD = 1210,
    MSG_TYPE_STRATEGY_INIT = 1211,
    MSG_TYPE_STRATEGY_INIT_ALL = 1212,
    MSG_TYPE_STRATEGY_START = 1213,
    MSG_TYPE_STRATEGY_START_ALL = 1214,    
    MSG_TYPE_STRATEGY_STOP = 1215,
    MSG_TYPE_STRATEGY_STOP_ALL = 1216,    
    MSG_TYPE_STRATEGY_EDIT = 1220,
    MSG_TYPE_STRATEGY_REMOVE = 1221,
    MSG_TYPE_STRATEGY_REMOVE_DUPLICATE =1222,
    MSG_TYPE_STRATEGY_RTN_REMOVE = 1223,
    MSG_TYPE_STRATEGY_GET_DATA = 1230,
    MSG_TYPE_STRATEGY_RTN_DATA = 1231,
    MSG_TYPE_STRATEGY_GET_CLASS_NAME = 1232,
    MSG_TYPE_STRATEGY_RTN_CLASS_NAME = 1233,
    MSG_TYPE_STRATEGY_GET_CLASS_PARAMETERS = 1234,
    MSG_TYPE_STRATEGY_RTN_CLASS_PARAMETERS = 1235,
    MSG_TYPE_STRATEGY_GET_PARAMETERS = 1234,
    MSG_TYPE_STRATEGY_RTN_PARAMETERS = 1235,   
  //  13*  task 
    MSG_TYPE_TIMER = 1301,
    MSG_TYPE_TASK_START = 1310,
    MSG_TYPE_TASK_STOP = 1311,
  //  20* engine requests
    // md request
    MSG_TYPE_SUBSCRIBE_MARKET_DATA = 2001,
    MSG_TYPE_SUBSCRIBE_L2_MD = 2002,
    MSG_TYPE_SUBSCRIBE_INDEX = 2003,
    MSG_TYPE_SUBSCRIBE_ORDER_TRADE = 2004,
    MSG_TYPE_UNSUBSCRIBE = 2011,
    // td request 
    MSG_TYPE_QRY_COMMODITY = 2021,	
    MSG_TYPE_QRY_CONTRACT   = 2022,
    MSG_TYPE_QRY_POS       = 2023,
    MSG_TYPE_QRY_ACCOUNT   = 2024,
    MSG_TYPE_ORDER         = 2030,  //insert order
    MSG_TYPE_ORDER_PAPER = 2031,
    MSG_TYPE_ORDER_CTP = 2032,
    MSG_TYPE_ORDER_CTP_PARKED = 2033,
    MSG_TYPE_ORDER_TAP = 2034,
    MSG_TYPE_ORDER_XTP = 2035,
    MSG_TYPE_ORDER_ACTION  = 2040,  //cancel order
    MSG_TYPE_CANCEL_ORDER = 2041,
    MSG_TYPE_CANCEL_ALL = 2042,
    MSG_TYPE_ORDER_ACTION_CTP = 2043,
    MSG_TYPE_ORDER_ACTION_TAP = 2044,
    MSG_TYPE_ORDER_ACTION_XTP =2045,
  // 25* engine callback    
    //call back
    MSG_TYPE_RSP_POS       = 2500,
    MSG_TYPE_RTN_ORDER     = 2510, //order status
    MSG_TYPE_RTN_ORDER_CTP     = 2511, 
    MSG_TYPE_RTN_ORDER_TAP     = 2512, 
    MSG_TYPE_RTN_ORDER_XTP     = 2513, 
    MSG_TYPE_RTN_TRADE     = 2520,
    MSG_TYPE_RTN_TRADE_CTP     = 2521,
    MSG_TYPE_RTN_TRADE_TAP     = 2522,
    MSG_TYPE_RTN_TRADE_XTP     = 2523,
    MSG_TYPE_RSP_ACCOUNT   = 2530,
    MSG_TYPE_RSP_CONTRACT   = 2540,
    MSG_TYPE_RSP_COMMODITY   = 2541,

  //	31*: info class msg, mainly about sys
    MSG_TYPE_INFO   = 3100,
    MSG_TYPE_INFO_ENGINE_MDCONNECTED = 3101,
    MSG_TYPE_INFO_ENGINE_MDDISCONNECTED = 3102,
    MSG_TYPE_INFO_ENGINE_TDCONNECTED = 3103,
    MSG_TYPE_INFO_ENGINE_TDDISCONNECTED = 3104,
    MSG_TYPE_INFO_HEARTBEAT_WARNING = 3105,
    MSG_TYPE_INFO_ENGINE_STATUS = 3106,
  //	34*:error class msg
    MSG_TYPE_ERROR = 3400,
    MSG_TYPE_ERROR_ENGINENOTCONNECTED = 3401,
    MSG_TYPE_ERROR_SUBSCRIBE = 3402,
    MSG_TYPE_ERROR_INSERTORDER = 3403,
    MSG_TYPE_ERROR_CANCELORDER = 3404,
    MSG_TYPE_ERROR_ORGANORDER = 3405, //order is not tracted by order manager
    MSG_TYPE_ERROR_QRY_ACC = 3406,
    MSG_TYPE_ERROR_QRY_POS = 3407,
    MSG_TYPE_ERROR_QRY_CONTRACT = 3408,
    MSG_TYPE_ERROR_CONNECT = 3409,  //login fail
    MSG_TYPE_ERROR_DISCONNECT = 3410,
    MSG_TYPE_ERROR_NOACCOUNT = 3411,
  //  40*: test class msg
    MSG_TYPE_TEST = 4000,

  //  9* base/header
    MSG_TYPE_BASE = 9
};

MSG_TYPE MsgType(const string& str);
string accAddress(const string& str);

enum class RUN_MODE :uint8_t {
    TRADE_MODE = 0, RECORD_MODE, REPLAY_MODE
};

enum class BROKERS : uint8_t {
    IB = 0, CTP, GOOGLE, SINA, PAPER,TAP
};



struct Gateway{
    string id;
    string api;
    int32_t intid;
    string brokerid;
    string userid;
    string password;
    string auth_code;
    string productinfo;
    string md_ip;
    uint16_t md_port;
    string td_ip;
    uint16_t td_port;
    string appid;
    string publicstream;
    string privatestream;
};

class MsgHeader{
    public:
        string destination_;
        string source_;
        MSG_TYPE msgtype_;
        
        MsgHeader(){}
        MsgHeader(string des, string sour, MSG_TYPE mt_)
        {
            destination_ = des;
            source_ = sour;
            msgtype_ = mt_;
        };
        virtual ~MsgHeader(){};

        virtual string serialize() {            
            string tmp = destination_ 
            + SERIALIZATION_SEPARATOR + source_
            + SERIALIZATION_SEPARATOR + to_string(msgtype_);
            return tmp;
        };
        virtual void deserialize(const string& msgin) {};
};

class DLL_EXPORT_IMPORT Tick{
    public:
        Tick() { }
        ~Tick(){ }

        string fullSymbol_;
        string time_;
        double price_ = 0.0;
        int size_ = 0;
        int depth_ = 1;
        double bidPrice_[20] = {0.0};
        int bidSize_[20] = {0};
        double askPrice_[20] = {0.0};
        int askSize_[20]= {0};
        int openInterest_ = 0;
        double open_ = 0.0;
        double high_ = 0.0;
        double low_ = 0.0;
        double preClose_ = 0.0;
        double upperLimitPrice_ = 0.0;
        double lowerLimitPrice_ = 0.0;       
};

class DLL_EXPORT_IMPORT TickMsg: public MsgHeader{
public:
    TickMsg() :MsgHeader(),data_()
    {
        msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L1;
    }
    ~TickMsg() {}

    Tick data_;

    virtual string serialize();
    // virtual void deserialize(const string& msgin);
};

class DLL_EXPORT_IMPORT Security{
    public:
        Security() {}
        ~Security(){}
    
    string fullSymbol_;
    string symbol_;
    char securityType_;
    string exchange_;
    string contractNo_;
    int multiplier_ = 0;
    string localName_;	// Unicode; e.g., in Chinese or French
    string currency_;
    double ticksize_ = 0.0;
    double longMarginRatio_ = 0.0;		
    double shortMarginRatio_ = 0.0;
    char postype_ = '2';

    // Options
    string underlyingSymbol_;
    char optionType_ ;
    double strikePrice_ = 0.0;
    char strikeMode_ ;
    char strikeType_ ;
    char applyType_;
    string expiryDate_;
		
};

class DLL_EXPORT_IMPORT SecurityMsg: public MsgHeader{
public:
    SecurityMsg() 	:MsgHeader(),data_()
    {
        msgtype_ = MSG_TYPE::MSG_TYPE_RSP_CONTRACT;
    }
    ~SecurityMsg() {}

    Security data_;

    virtual string serialize() ;
    // virtual void deserialize(const string& msgin);
};

class AccountInfo {
public:
    AccountInfo(){}
    ~AccountInfo(){}

    string accountID_;
    string accountType_;				//INDIVIDUAL
    double availableFunds_ = 0.0;
    double netLiquidation_ = 0.0;
    double equityWithLoanValue_ = 0.0;
    double previousDayEquityWithLoanValue_ = 0.0;
    double fullInitialMargin_ = 0.0;
    double fullMaintainanceMargin_ = 0.0;
    double commission_ = 0.0;
    double buyingPower_ = 0.0;
    double cashBalance_ = 0.0;
    double realizedPnL_ = 0.0;
    double unrealizedPnL_ = 0.0;
    double frozen_ = 0.0;
    double balance_ = 0.0;
    
};

class DLL_EXPORT_IMPORT AccMsg: public MsgHeader{
public:
    AccMsg() :MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_RSP_ACCOUNT;
    }
    ~AccMsg() {}

    AccountInfo data_;

    virtual string serialize();
    // virtual void deserialize(const string& msgin);
};


class DLL_EXPORT_IMPORT Fill {
public:
    Fill() { }
    ~Fill(){}

    long serverOrderID_ = -1;        //local server id
    long clientOrderID_ = -1;
    long brokerOrderID_ = -1;
    long tradeId_ = -1;              //local id
    int clientID_ = 0;             // sid, get from client; 0=mannual
    string orderNo_;            //exchange id
    string localNo_;
    string tradeNo_;            //exchange id  
    string tradeTime_;
    string fullSymbol_;
    string account_;
    OrderFlag fillFlag_ = OrderFlag::OF_OpenPosition;
    string api_;						// IB, ctp etc
    string currency_;                  
    double tradePrice_ = 0.0;
    int tradeSize_ = 0;					// < 0 = short, order size != trade size
    double commission_ = 0.0;
};

class DLL_EXPORT_IMPORT FillMsg: public MsgHeader{
public:
    FillMsg(): MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_RTN_TRADE;
    }
    ~FillMsg() {}

    Fill data_;

    virtual string serialize();
    // virtual void deserialize(const string& msgin);
};

extern long m_serverOrderId;    // unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
extern std::mutex oid_mtx;			 // mutex for increasing order id
extern std::mutex orderStatus_mtx;  // mutex for changing order status


class DLL_EXPORT_IMPORT Order {
public:
    Order() { }
    ~Order(){}
// request msg header
    string api_;                 // ctp, tap etc
    string account_;             // account
    int clientID_ = 0;           // client id, get from client; 0=mannual
    long clientOrderID_ = -1;       // clientside id    
    string tag_;                   // reseverd for other use
// server and callback content, for return orderstatus msg 
    string fullSymbol_;          //unique symbol for underlying commodity: exchange + type + commodityname + commodityno
	double price_ = 0.0;
    int quantity_ = 0;           //total original
    int tradedvol_ = 0;
    OrderFlag flag_ = OrderFlag::OF_OpenPosition;
    long serverOrderID_ = -1;       // orderref, unique sqserver id
    long brokerOrderID_ = -1;       // for statistical use
    string orderNo_;             //unique exchange order id,for ctp = exchangeID_+ orsysid
    string localNo_;             //unique local id ,frontid +sessionid +orderref
    string createTime_;
    string updateTime_;
    OrderStatus orderStatus_ = OrderStatus::OS_UNKNOWN;				
};

class DLL_EXPORT_IMPORT PaperOrder: public Order{
public:
    PaperOrder(){}
    ~PaperOrder(){}

    OrderType orderType_ = OrderType::OT_Market;						// MKT, LMT, STP, STPLMT, etc
    OrderFlag orderFlag_ = OrderFlag::OF_OpenPosition;
    int orderSize_ = 0;
    string fillNo_;					// < 0 = short, order size != trade size
    int filledSize_ = 0;
    double lastFilledPrice_ = 0.0;
    double avgFilledPrice_ = 0.0;
    double limitPrice_ = 0.0;
    double stopPrice_ = 0.0;
    double trailPrice_ = 0.0;
    double trailingPercent_ = 0.0;
    string timeInForce_;
    bool outsideRegularTradingHour_ = false;
    bool hidden_ = false;
    bool allOrNone_ = false;
};



class DLL_EXPORT_IMPORT CtpOrder: public Order{
public:
    CtpOrder(){}
    ~CtpOrder(){}
    // request msg data
    struct CThostFtdcInputOrderField orderField_ ;
};

class DLL_EXPORT_IMPORT CtpParkedOrder: public Order{
public:
    CtpParkedOrder(){}
    ~CtpParkedOrder(){}
    // request msg data
    struct CThostFtdcParkedOrderField parkedOrderField_ ;
};

class DLL_EXPORT_IMPORT OrderMsg: public MsgHeader{
public:
    OrderMsg(): MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_ORDER;
    }
    ~OrderMsg() {}

    Order data_;

    virtual void deserialize(const string& msgin);
    std::shared_ptr<Order> toPOrder();
};

class DLL_EXPORT_IMPORT PaperOrderMsg: public MsgHeader{
public:
    PaperOrderMsg(): MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_ORDER_PAPER;
    }
    ~PaperOrderMsg() {}

    PaperOrder data_;

    virtual void deserialize(const string& msgin);
    std::shared_ptr<Order> toPOrder();
};


class DLL_EXPORT_IMPORT CtpOrderMsg: public MsgHeader{
public:
    CtpOrderMsg(): MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_ORDER_CTP;
    }
    ~CtpOrderMsg() {}

    CtpOrder data_;

    virtual void deserialize(const string& msgin);
    std::shared_ptr<Order> toPOrder();
};


class DLL_EXPORT_IMPORT CtpParkedOrderMsg: public MsgHeader{
public:
    CtpParkedOrderMsg(): MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_ORDER_CTP;
    }
    ~CtpParkedOrderMsg() {}

    CtpParkedOrder data_;

    virtual void deserialize(const string& msgin);
    std::shared_ptr<Order> toPOrder();
};


class DLL_EXPORT_IMPORT OrderStatusMsg: public MsgHeader{
public:
    OrderStatusMsg(string des,string src): MsgHeader(des,src,MSG_TYPE::MSG_TYPE_RTN_ORDER),data_()
    {       
    }
    ~OrderStatusMsg() {}

    Order data_;
    
    void set(std::shared_ptr<Order> po);
    virtual string serialize();
};



class DLL_EXPORT_IMPORT Position {
public:
    Position(){}
    ~Position(){}

    string key_ = "";
    string account_ = "";
    string api_ = "";
    string fullSymbol_ = "";
    double avgPrice_ = 0;
    int size_ = 0;
    int preSize_ = 0;
    int freezedSize_ = 0;
    double openpl_ = 0;			// unrealized pnl
    double closedpl_ = 0;		// realized pnl
    char type_ ='1';             // direction
    string posNo_ = "";
    string openapi_ = "";
    string openOrderNo_ = "";
    int openClientID_ = -1;
    string closeapi_ = "";
    string closeOrderNo_ = "";
    int closeClientID_ = -1;		
};

class DLL_EXPORT_IMPORT PosMsg: public MsgHeader{
public:
    PosMsg(string des,string src): MsgHeader(des,src,MSG_TYPE_RSP_POS),data_()
    {
    }
    ~PosMsg() {}

    Position data_;

    virtual string serialize();
    // virtual void deserialize(const string& msgin);
    void set(std::shared_ptr<Position>);
};


class OrderAction {
public:
    OrderAction(){}
    ~OrderAction(){}

    int clientID_ = 0;
    long serverOrderID_ = -1;
    long clientOrderID_ = -1;
    string orderNo_;
};

class DLL_EXPORT_IMPORT OrderActionMsg: public MsgHeader{
public:
    OrderActionMsg() :MsgHeader(),data_()
    {
         msgtype_ = MSG_TYPE::MSG_TYPE_ORDER_ACTION;
    }
    OrderActionMsg(string des,string src) :MsgHeader(des,src,MSG_TYPE_ORDER_ACTION),data_()
    {

    }
    ~OrderActionMsg() {}

    OrderAction data_;

    // virtual string serialize();
    virtual void deserialize(const string& msgin);
};




class DLL_EXPORT_IMPORT SubscribeMsg: public MsgHeader{
public:
    SubscribeMsg(string des,string src) :MsgHeader(des,src,MSG_TYPE_SUBSCRIBE_MARKET_DATA),data_()
    {
    }
    SubscribeMsg():MsgHeader(),data_(){
        msgtype_ = MSG_TYPE::MSG_TYPE_SUBSCRIBE_MARKET_DATA;
    }
    ~SubscribeMsg() {}
    SymbolType symtype_;
    vector<string> data_;

    // virtual string serialize();
    virtual void deserialize(const string& msgin);
};

class DLL_EXPORT_IMPORT UnSubscribeMsg: public MsgHeader{
public:
    UnSubscribeMsg(string des,string src) :MsgHeader(des,src,MSG_TYPE_UNSUBSCRIBE),data_()
    {
    }
    UnSubscribeMsg():MsgHeader(),data_(){
        msgtype_ = MSG_TYPE::MSG_TYPE_UNSUBSCRIBE;
    }
    ~UnSubscribeMsg() {}

    SymbolType symtype_;
    vector<string> data_;

    // virtual string serialize();
    virtual void deserialize(const string& msgin);
};


class DLL_EXPORT_IMPORT QryContractMsg: public MsgHeader{
public:
    QryContractMsg(string des,string src) :MsgHeader(des,src,MSG_TYPE_QRY_CONTRACT),data_()
    {
    }
    QryContractMsg():MsgHeader(),data_(){
        msgtype_ = MSG_TYPE::MSG_TYPE_QRY_CONTRACT;
    }
    ~QryContractMsg() {}

    SymbolType symtype_;
    string data_;

    // virtual string serialize();
    virtual void deserialize(const string& msgin);
};



class DLL_EXPORT_IMPORT ErrorMsg: public MsgHeader{
public:
    ErrorMsg(string des,string src, MSG_TYPE mt, string em) :
    MsgHeader(des,src,mt)
    ,data_(em)
    {
    }
    ~ErrorMsg() {}

    string data_;

    virtual string serialize();
    // virtual void deserialize(const string& msgin);
};

class DLL_EXPORT_IMPORT InfoMsg: public MsgHeader{
public:
    InfoMsg(string des,string src, MSG_TYPE mt, string em) :
    MsgHeader(des,src,mt)
    ,data_(em)
    {
    }
    ~InfoMsg() {}

    string data_;

    virtual string serialize();
    // virtual void deserialize(const string& msgin);
};







}

#endif  // __StarQuant_Common_Datastruct_H_
