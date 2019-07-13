#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include <Engine/TapMDEngine.h>
#include <APIs/Tap/TapQuoteAPI.h>
#include <Common/util.h>
#include <Common/logger.h>
#include <Data/tick.h>
#include <Common/timeutil.h>



using namespace std;

namespace StarQuant
{
    //extern std::atomic<bool> gShutdown;
    TapMDEngine::TapMDEngine()
        : sessionId_(0)
    {
        init();
    }

    TapMDEngine::~TapMDEngine() {
        stop();
    }

    void TapMDEngine::init(){
        if (msgq_recv_ == nullptr){
            msgq_recv_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERSUB_URL);	
        }	
        // 创建Tap目录
        name_ = "TAP_MD";
        tapacc_ = CConfig::instance()._accmap["TAP"];
        string path = CConfig::instance().logDir() + "/Tap/";
        boost::filesystem::path dir(path.c_str());
        boost::filesystem::create_directory(dir);

        TAPIINT32 iResult = TAPIERROR_SUCCEED;
        TapAPIApplicationInfo stAppInfo;
        string authencode = tapacc_.auth_code;
        strcpy(stAppInfo.AuthCode, authencode.c_str());
        strcpy(stAppInfo.KeyOperationLogPath, path.c_str());
    //    SetTapQuoteAPIDataPath("./data");
        // 创建API对象
        this->api_ = CreateTapQuoteAPI(&stAppInfo, iResult);
        if (NULL == this->api_ ){
            cout << "Error: create tap Quote API fail，err num is ：" << iResult <<endl;
        }
        this->api_->SetAPINotify(this);
    }

    void TapMDEngine::stop(){
        int32_t tmp = disconnect();
        int32_t count = 0;
        while( estate_ != DISCONNECTED){
            msleep(100);
            count++;
            if(count > 20)
                break;
        }
        estate_ = EState::STOP; 
        if (api_ != NULL) {
            FreeTapQuoteAPI(this->api_);
            this->api_ = NULL;
        }
    }

    bool TapMDEngine::connect()
    {
        TAPIINT32 iErr = TAPIERROR_SUCCEED;
        TapAPIQuoteLoginAuth stLoginAuth;
        memset(&stLoginAuth, 0, sizeof(stLoginAuth));
        APIStrncpy(stLoginAuth.UserNo, tapacc_.userid.c_str());
        APIStrncpy(stLoginAuth.Password, tapacc_.password.c_str());
        stLoginAuth.ISModifyPassword = APIYNFLAG_NO;
        stLoginAuth.ISDDA = APIYNFLAG_NO;
        int32_t count = 0;
        while(estate_ != EState::LOGIN_ACK){
            switch(estate_){
                case EState::DISCONNECTED:
                    //设定服务器IP、端口
                    iErr = this->api_->SetHostAddress(tapacc_.md_ip.c_str(), tapacc_.md_port);
                    if(TAPIERROR_SUCCEED != iErr) {
                        std::cout << "tap md SetHostAddress Error:" << iErr <<endl;
                    }
                    iErr = this->api_->Login(&stLoginAuth);
                    estate_ = CONNECTING;
                    count++;
                    if(TAPIERROR_SUCCEED != iErr) {
                        cout << "tap md connect Error:" << iErr <<endl;
                        estate_ = EState::DISCONNECTED;
                        break;
                    }
                    PRINT_TO_FILE("INFO:[%s,%d][%s]Tap Md logining...!\n", __FILE__, __LINE__, __FUNCTION__);
                    break;
                case EState::CONNECTING:
                    msleep(500);
                    break;
                case EState::CONNECT_ACK:
                    PRINT_TO_FILE("INFO:[%s,%d][%s]Tap Md logined, waiting api ready ...\n", __FILE__, __LINE__, __FUNCTION__);
                    estate_ = EState::LOGINING;
                    break;
                case EState::LOGINING:
                    msleep(500);
                    break;
                default:
                    msleep(100);
                    break;
            }
            if(count >5){
                cout<<"too many tries fails, give up connecting"<<endl;
                //estate_ = EState::DISCONNECTED;
                return false;
            }
        }
        return true;	
    }

    bool TapMDEngine::disconnect() {
        if (estate_ == LOGIN_ACK){
            PRINT_TO_FILE("INFO:[%s,%d][%s]Tap Md disconnecting ...\n", __FILE__, __LINE__, __FUNCTION__);
            estate_ = EState::LOGOUTING;
            this->api_->Disconnect();
            return true;
        }
        else{
            cout<<"Tap md is not connected(logined), can not disconnect! "<<endl;
            return true;
        }
    }

    void TapMDEngine::start(){
        while(estate_ != EState::STOP){
            string msgin = msgq_recv_->recmsg(1);
            if (msgin.empty())
                continue;
            MSG_TYPE msgintype = MsgType(msgin);
            vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
            if (v[0] != name_) //filter message according to its destination
                continue;			
            bool tmp;
            switch (msgintype)
            {
                case MSG_TYPE_ENGINE_CONNECT:
                    tmp = connect();
                    break;
                case MSG_TYPE_ENGINE_DISCONNECT:
                    tmp = disconnect();
                    break;
                case MSG_TYPE_SUBSCRIBE_MARKET_DATA:
                    if (estate_ == LOGIN_ACK){
                        subscribe(v[2]);
                    }
                    else{
                        cout<<"md is not connected,can not subscribe! "<<endl;
                        string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"md is not connected,can not subscribe";
                        lock_guard<std::mutex> g(IEngine::sendlock_);
                        IEngine::msgq_send_->sendmsg(msgout);
                    }
                    break;
                case MSG_TYPE_UNSUBSCRIBE:
                    if (estate_ == LOGIN_ACK){
                        unsubscribe(v[2]);
                    }
                    else{
                        cout<<"md is not connected,can not unsubscribe! "<<endl;
                        string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"md is not connected,can not unsubscribe";
                        lock_guard<std::mutex> g(IEngine::sendlock_);
                        IEngine::msgq_send_->sendmsg(msgout);
                    }
                        break;
                case MSG_TYPE_QRY_CONTRACT: case MSG_TYPE_QRY_COMMODITY:
                    if (estate_ == LOGIN_ACK){
                        query(msgintype,v[2]);
                    }
                    else{
                        cout<<"md is not connected,can not query! "<<endl;
                        string msgout = to_string(MSG_TYPE_ERROR) + SERIALIZATION_SEPARATOR +"md is not connected,can not query";
                        lock_guard<std::mutex> g(IEngine::sendlock_);
                        IEngine::msgq_send_->sendmsg(msgout);
                    }
                    break;					
                case MSG_TYPE_ENGINE_STATUS:
                    {
                        string msgout = to_string(MSG_TYPE_ENGINE_STATUS) + SERIALIZATION_SEPARATOR + to_string(estate_);
                        lock_guard<std::mutex> g(IEngine::sendlock_);
                        IEngine::msgq_send_->sendmsg(msgout);
                    }
                    break;
                default:
                    break;
            }
        }
    }

////////////////////////////////////////////////////// outgoing function ///////////////////////////////////////

    void TapMDEngine::subscribe(const string& symbol) {
    //	cout<<"begin subscribeMarketdata"<<endl;
        TAPIINT32 iErr = TAPIERROR_SUCCEED;
        vector<string> v = stringsplit(symbol, ' ');
        TapAPIContract stContract1;
        memset(&stContract1, 0, sizeof(stContract1));

        APIStrncpy(stContract1.Commodity.ExchangeNo, v[0].c_str());
    //		APIStrncpy(stContract1.Commodity.CommodityType, v[1].c_str());
        stContract1.Commodity.CommodityType = v[1][0];
        APIStrncpy(stContract1.Commodity.CommodityNo, v[2].c_str());
        APIStrncpy(stContract1.ContractNo1, v[3].c_str());
        stContract1.CallOrPutFlag1 = TAPI_CALLPUT_FLAG_NONE;
        stContract1.CallOrPutFlag2 = TAPI_CALLPUT_FLAG_NONE;
        stContract_ = stContract1;

        iErr = this->api_->SubscribeQuote(&sessionId_, &stContract_);
        if(TAPIERROR_SUCCEED != iErr) {
            std::cout << "SubscribeQuote Error:" << iErr <<endl;
            return;
        }

    }

    void TapMDEngine::unsubscribe(const string& symbol) {
        TAPIINT32 iErr = TAPIERROR_SUCCEED;
        vector<string> v = stringsplit(symbol, ' ');
        TapAPIContract stContract1;
        memset(&stContract1, 0, sizeof(stContract1));

        APIStrncpy(stContract1.Commodity.ExchangeNo, v[0].c_str());
    //		APIStrncpy(stContract1.Commodity.CommodityType, v[1].c_str());
        stContract1.Commodity.CommodityType = v[1][0];
        APIStrncpy(stContract1.Commodity.CommodityNo, v[2].c_str());
        APIStrncpy(stContract1.ContractNo1, v[3].c_str());
        stContract1.CallOrPutFlag1 = TAPI_CALLPUT_FLAG_NONE;
        stContract1.CallOrPutFlag2 = TAPI_CALLPUT_FLAG_NONE;
        stContract_ = stContract1;

        iErr = this->api_->UnSubscribeQuote(&sessionId_, &stContract_);
        if(TAPIERROR_SUCCEED != iErr) {
            std::cout << "UnSubscribeQuote Error:" << iErr <<endl;
            return;
        }
        
    }
    void TapMDEngine::query(const MSG_TYPE & _type,const string& symbol)
    {
        //TODO: add qry commodity and contract
        switch (_type)
        {
            case MSG_TYPE::MSG_TYPE_QRY_CONTRACT:
                // this->api_->QryContract()
                break;
            default:
                break;
        }	
    }

/////////////////////////////////////////////// end of outgoing functions ///////////////////////////////////////

////////////////////////////////////////////////////// incoming function ///////////////////////////////////////

    void TAP_CDECL TapMDEngine::OnRspLogin(TAPIINT32 errorCode, const TapAPIQuotLoginRspInfo *info)
    {
        if(TAPIERROR_SUCCEED == errorCode) {
            estate_ = CONNECT_ACK;	
            cout << "TAP行情登录成功，等待行情API初始化..." << endl;
            PRINT_TO_FILE("INFO:[%s,%d][%s]Tap md is logined.\n", __FILE__, __LINE__, __FUNCTION__);
        } else {
            estate_ = DISCONNECTED;	
            cout << "TAP行情登录失败，错误码:" << errorCode << endl;
            PRINT_TO_FILE("INFO:[%s,%d][%s] Tap md login failed, errorcode: %d .\n", __FILE__, __LINE__, __FUNCTION__,errorCode);
        }
    }

    void TAP_CDECL TapMDEngine::OnAPIReady()
    {
        estate_ = EState::LOGIN_ACK;
        cout << "TAP行情API初始化完成" << endl;
        PRINT_TO_FILE("INFO:[%s,%d][%s]Tap md api is ready.\n", __FILE__, __LINE__, __FUNCTION__);
    }

    void TAP_CDECL TapMDEngine::OnDisconnect(TAPIINT32 reasonCode)
    {
        estate_ = EState::DISCONNECTED;
        cout << "TAP行情API断开,断开原因:"<<reasonCode << endl;
        PRINT_TO_FILE("INFO:[%s,%d][%s]Tap md disconnected, reasoncode: %d.\n", __FILE__, __LINE__, __FUNCTION__,reasonCode);
    }

    void TAP_CDECL TapMDEngine::OnRspChangePassword(TAPIUINT32 sessionID, TAPIINT32 errorCode)
    {
        cout << __FUNCTION__ << " is called." << endl;
    }

    void TAP_CDECL TapMDEngine::OnRspQryExchange(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIExchangeInfo *info)
    {
        cout << __FUNCTION__ << " is called." << endl;
    }

    void TAP_CDECL TapMDEngine::OnRspQryCommodity(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteCommodityInfo *info)
    {
        cout << __FUNCTION__ << " is called." << endl;
        cout << info->CommodityEngName<<" "<<info->ContractSize<<endl;
    }

    void TAP_CDECL TapMDEngine::OnRspQryContract(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteContractInfo *info)
    {
        cout << __FUNCTION__ << " is called." << endl;
        cout << info->ContractName<<" "<<info->ContractExpDate<<" "<<endl;
    }

    void TAP_CDECL TapMDEngine::OnRtnContract(const TapAPIQuoteContractInfo *info)
    {
        cout << __FUNCTION__ << " is called." << endl;
    }

    void TAP_CDECL TapMDEngine::OnRspSubscribeQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIQuoteWhole *info)
    {
        if (TAPIERROR_SUCCEED == errorCode)
        {
            cout << "行情订阅成功 ";
            if (NULL != info)
            {
                cout << info->DateTimeStamp << " "
                    << info->TradingState<< " "
                    << info->Contract.Commodity.ExchangeNo << " "
                    << info->Contract.Commodity.CommodityType << " "
                    << info->Contract.Commodity.CommodityNo << " "
                    << info->Contract.ContractNo1 << " "
                    << info->QLastPrice<<" "
                    <<info->QBidPrice[0]<<" "
                    <<info->QAskPrice[0]<<" "
                    <<info->QBidPrice[1]<<" "
                    <<info->QAskPrice[1]<<" "
                    <<info->QBidPrice[2]<<" "
                    <<info->QAskPrice[2]<<" "
                    <<info->QBidPrice[3]<<" "
                    <<info->QAskPrice[3]<<" "
                    <<info->QBidPrice[4]<<" "
                    <<info->QAskPrice[4]<<" "
                    // ...
                    <<endl;
        //         string ticker= info->Contract.Commodity.ExchangeNo;
        // 		ticker +=" ";
        // 		ticker +=info->Contract.Commodity.CommodityType;
        // 		ticker +=" ";
        // 		ticker +=info->Contract.Commodity.CommodityNo;
        // 		ticker +=" ";
        // 		ticker +=info->Contract.ContractNo1;

        // 		Tick_L5 k;

        // 		k.time_ = ymdhms();
        // 		k.msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L5;
        // 		k.fullsymbol_ = ticker;
        // 		k.price_ = info->QLastPrice;
        // 		k.size_ = info->QTotalQty;			// not valid without volume
        // //		k.bidprice_L1_ = info->;
        //		k.bidsize_L1_ = info->BidVolume1;
        //		k.askprice_L1_ = info->AskPrice1;
        //		k.asksize_L1_ = info->AskVolume1;
        //		k.open_interest = info->OpenInterest;
        //		k.open_ = info->OpenPrice;
        //		k.high_ = info->HighestPrice;
        //		k.low_ = info->LowestPrice;
        //		k.pre_close_ = info->PreClosePrice;
        //		k.upper_limit_price_ = info->UpperLimitPrice;
        //		k.lower_limit_price_ = info->LowerLimitPrice;
                
        //		msgq_pub_->sendmsg(k.serialize());
            }

        } else{
            cout << "行情订阅失败，错误码：" << errorCode <<endl;
        }
    }

    void TAP_CDECL TapMDEngine::OnRspUnSubscribeQuote(TAPIUINT32 sessionID, TAPIINT32 errorCode, TAPIYNFLAG isLast, const TapAPIContract *info)
    {
        cout << __FUNCTION__ << " is called." << endl;
    }

    void TAP_CDECL TapMDEngine::OnRtnQuote(const TapAPIQuoteWhole *info)
    {
        if (NULL != info)
        {
            cout << "行情更新:"<<"tick time"
                << info->DateTimeStamp <<" rec time"<<ymdhmsf()
                << info->Contract.Commodity.ExchangeNo << " "
                << info->Contract.Commodity.CommodityType << " "
                << info->Contract.Commodity.CommodityNo << " "
                << info->Contract.ContractNo1 << " "
                << info->QLastPrice<<" "
                << info->QOpeningPrice<<" "
                <<info->QPositionQty<<" "
                <<info->QBidPrice[0]<<" "
                <<info->QAskPrice[0]<<" "
                // ...
                <<endl;

            string ticker= info->Contract.Commodity.ExchangeNo;
            ticker += " ";
            ticker += info->Contract.Commodity.CommodityType;
            ticker += " ";
            ticker += info->Contract.Commodity.CommodityNo;
            ticker += " ";
            ticker += info->Contract.ContractNo1;

            Tick_L5 k;
    //		k.time_ = hmsf();
            k.time_ = info->DateTimeStamp;
            k.msgtype_ = MSG_TYPE::MSG_TYPE_TICK_L5;
            k.fullsymbol_ = ticker;
            k.price_ = info->QLastPrice;
            k.size_ = info->QLastQty;			// not valid without volume
            k.depth_ = 5;
            k.bidprice_L1_ = info->QBidPrice[0];
            k.bidsize_L1_ = info->QBidQty[0];
            k.askprice_L1_ = info->QAskPrice[0];
            k.asksize_L1_ = info->QAskQty[0];
            k.bidprice_L2_ = info->QBidPrice[1];
            k.bidsize_L2_ = info->QBidQty[1];
            k.askprice_L2_ = info->QAskPrice[1];
            k.asksize_L2_ = info->QAskQty[1];
            k.bidprice_L3_ = info->QBidPrice[2];
            k.bidsize_L3_ = info->QBidQty[2];
            k.askprice_L3_ = info->QAskPrice[2];
            k.asksize_L3_ = info->QAskQty[2];		
            k.bidprice_L4_ = info->QBidPrice[3];
            k.bidsize_L4_ = info->QBidQty[3];
            k.askprice_L4_ = info->QAskPrice[3];
            k.asksize_L4_ = info->QAskQty[3];	
            k.bidprice_L5_ = info->QBidPrice[4];
            k.bidsize_L5_ = info->QBidQty[4];
            k.askprice_L5_ = info->QAskPrice[4];
            k.asksize_L5_ = info->QAskQty[4];	
            k.open_interest = info->QPositionQty;
            k.open_ = info->QOpeningPrice;
            k.high_ = info->QHighPrice;
            k.low_ = info->QLowPrice;
            k.pre_close_ = info->QPreClosingPrice;
            k.upper_limit_price_ = info->QLimitUpPrice;
            k.lower_limit_price_ = info->QLimitDownPrice;
            
            lock_guard<mutex> g(IEngine::sendlock_);
            IEngine::msgq_send_->sendmsg(k.serialize());
        }
    }

}
