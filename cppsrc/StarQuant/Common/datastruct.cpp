
#include <string>
#include <Common/util.h>
#include <Common/datastruct.h>
using namespace std;

namespace StarQuant {

long m_serverOrderId = 0;    // unique order id on server side defined in ordermanager.cpp. Every broker has its own id;
std::mutex oid_mtx;			 // mutex for increasing order id
std::mutex orderStatus_mtx;  // mutex for changing order status

MSG_TYPE MsgType(const string& msg){
    string header;
    stringstream ss(msg);
    getline(ss,header,SERIALIZATION_SEPARATOR);
    getline(ss,header,SERIALIZATION_SEPARATOR);
    getline(ss,header,SERIALIZATION_SEPARATOR);
    MSG_TYPE msgtype_ = MSG_TYPE(atoi(header.c_str()));
    return msgtype_;
}

string accAddress(const string& msg){
    string acc;
    stringstream ss(msg);
    getline(ss,acc,DESTINATION_SEPARATOR);
    getline(ss,acc,DESTINATION_SEPARATOR);
    getline(ss,acc,DESTINATION_SEPARATOR);    
    return acc;
}

string TickMsg::serialize(){
    string ba; //bid ask price and size
    for (int i = 0;i < data_.depth_;i++){
        ba = ba 
            + SERIALIZATION_SEPARATOR + to_string(data_.bidPrice_[i])
            + SERIALIZATION_SEPARATOR + to_string(data_.bidSize_[i])
            + SERIALIZATION_SEPARATOR + to_string(data_.askPrice_[i])
            + SERIALIZATION_SEPARATOR + to_string(data_.askSize_[i]);
    }
    string s;
    s = destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	data_.fullSymbol_
        + SERIALIZATION_SEPARATOR + data_.time_
        + SERIALIZATION_SEPARATOR + to_string(data_.price_)
        + SERIALIZATION_SEPARATOR + to_string(data_.size_)
        + ba
        + SERIALIZATION_SEPARATOR + to_string(data_.openInterest_)
        + SERIALIZATION_SEPARATOR + to_string(data_.open_)
        + SERIALIZATION_SEPARATOR + to_string(data_.high_)
        + SERIALIZATION_SEPARATOR + to_string(data_.low_)
        + SERIALIZATION_SEPARATOR + to_string(data_.preClose_)
        + SERIALIZATION_SEPARATOR + to_string(data_.upperLimitPrice_)
        + SERIALIZATION_SEPARATOR + to_string(data_.lowerLimitPrice_);
    return s;
}

string SecurityMsg::serialize(){
    string s;
    s = destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	data_.symbol_
        + SERIALIZATION_SEPARATOR +	data_.exchange_
        + SERIALIZATION_SEPARATOR +	data_.localName_
        + SERIALIZATION_SEPARATOR +	data_.securityType_
        + SERIALIZATION_SEPARATOR + to_string(data_.multiplier_)
        + SERIALIZATION_SEPARATOR + to_string(data_.ticksize_)
        + SERIALIZATION_SEPARATOR + data_.postype_
        + SERIALIZATION_SEPARATOR + to_string(data_.longMarginRatio_)
        + SERIALIZATION_SEPARATOR + to_string(data_.shortMarginRatio_)
        + SERIALIZATION_SEPARATOR + data_.underlyingSymbol_
        + SERIALIZATION_SEPARATOR + data_.optionType_
        + SERIALIZATION_SEPARATOR + to_string(data_.strikePrice_)
        + SERIALIZATION_SEPARATOR + data_.expiryDate_ ;
       
    return s;
}

string AccMsg::serialize(){
    string s;
    s = destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	data_.accountID_
        + SERIALIZATION_SEPARATOR + to_string(data_.previousDayEquityWithLoanValue_)
        + SERIALIZATION_SEPARATOR + to_string(data_.netLiquidation_)
        + SERIALIZATION_SEPARATOR + to_string(data_.availableFunds_)
        + SERIALIZATION_SEPARATOR + to_string(data_.commission_)        
        + SERIALIZATION_SEPARATOR + to_string(data_.fullMaintainanceMargin_)
        + SERIALIZATION_SEPARATOR + to_string(data_.realizedPnL_)
        + SERIALIZATION_SEPARATOR + to_string(data_.unrealizedPnL_)
        + SERIALIZATION_SEPARATOR + to_string(data_.balance_)
        + SERIALIZATION_SEPARATOR + to_string(data_.frozen_)
        + SERIALIZATION_SEPARATOR + ymdhmsf();
    return s;
}

string FillMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	std::to_string(data_.serverOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.clientOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.clientID_)
        + SERIALIZATION_SEPARATOR + data_.localNo_
        + SERIALIZATION_SEPARATOR + data_.orderNo_
        + SERIALIZATION_SEPARATOR + data_.tradeNo_
        + SERIALIZATION_SEPARATOR + data_.tradeTime_
        + SERIALIZATION_SEPARATOR + data_.fullSymbol_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.tradePrice_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.tradeSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(static_cast<int>(data_.fillFlag_))
        + SERIALIZATION_SEPARATOR + std::to_string(data_.commission_)
        + SERIALIZATION_SEPARATOR + data_.account_
        + SERIALIZATION_SEPARATOR + data_.api_
        + SERIALIZATION_SEPARATOR + ymdhms();				
    return str;
}



void OrderMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];
    data_.api_ = v[3];
    data_.account_ = v[4];
    data_.clientID_ = stoi(v[5]);
    data_.clientOrderID_ = stol(v[6]);
    data_.tag_ = v[7];
    // data_.clientID_ = stoi(v[1]);
    // data_.clientOrderID_ = stol(v[4]);
    // data_.orderType_ = static_cast<OrderType>(stoi(v[5]));
    // data_.fullSymbol_ = v[6];
    // data_.orderSize_ = stoi(v[7]);
    // if (data_.orderType_ == OrderType::OT_Limit){
    //     data_.limitPrice_ = stof(v[8]);
    // }else if (data_.orderType_ == OrderType::OT_StopLimit){
    //     data_.stopPrice_ = stof(v[8]);
    // }
    // data_.orderFlag_ = static_cast<OrderFlag>(stoi(v[9]));
    // data_.tag_ = v[10];
}

std::shared_ptr<Order> OrderMsg::toPOrder(){
    std::shared_ptr<Order> o = make_shared<Order>();
    o->api_ = data_.api_;
    o->account_ = data_.account_;    
    o->clientID_ = data_.clientID_;
    o->clientOrderID_ = data_.clientOrderID_;
    o->tag_ =  data_.tag_;

    o->fullSymbol_ = data_.fullSymbol_; 
    o->price_ = data_.price_;
    o->quantity_ = data_.quantity_;
    o->tradedvol_ = data_.tradedvol_;
    o->flag_ = data_.flag_;   
    o->serverOrderID_ = data_.serverOrderID_;
    o->brokerOrderID_ = data_.brokerOrderID_;
    o->orderNo_ = data_.orderNo_;
    o->localNo_ = data_.localNo_;
    o->createTime_ = data_.createTime_;
    o->updateTime_ = data_.updateTime_;
    o->orderStatus_ = data_.orderStatus_;

    return o;
}

void PaperOrderMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];
    data_.api_ = v[3];
    data_.account_ = v[4];
    data_.clientID_ = stoi(v[5]);
    data_.clientOrderID_ = stol(v[6]);
    data_.tag_ = v[7];

    data_.orderType_ = static_cast<OrderType>(stoi(v[8]));
    data_.fullSymbol_ = v[9];
    data_.orderFlag_ = static_cast<OrderFlag>(stoi(v[10]));
    data_.orderSize_ = stoi(v[11]);
    data_.limitPrice_ = stof(v[12]);
    data_.stopPrice_ = stof(v[13]);
}

std::shared_ptr<Order> PaperOrderMsg::toPOrder(){
    auto o = make_shared<PaperOrder>();
    o->api_ = data_.api_;
    o->account_ = data_.account_;    
    o->clientID_ = data_.clientID_;
    o->clientOrderID_ = data_.clientOrderID_;
    o->tag_ =  data_.tag_;
    o->fullSymbol_ = data_.fullSymbol_;
    o->price_ = data_.price_;
    o->quantity_ = data_.quantity_;
    o->tradedvol_ = data_.tradedvol_;
    o->flag_ = data_.flag_;       
    o->serverOrderID_ = data_.serverOrderID_;
    o->brokerOrderID_ = data_.brokerOrderID_;
    o->orderNo_ = data_.orderNo_;
    o->localNo_ = data_.localNo_;
    o->createTime_ = data_.createTime_;
    o->updateTime_ = data_.updateTime_;
    o->orderStatus_ = data_.orderStatus_;

    o->orderType_ = data_.orderType_;
    o->orderSize_ = data_.orderSize_ ;
    o->limitPrice_ = data_.limitPrice_;
    o->stopPrice_ = data_.stopPrice_ ;
    o->orderFlag_ = data_.orderFlag_;

    return o;
}


void CtpOrderMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];
    data_.api_ = v[3];
    data_.account_ = v[4];
    data_.clientID_ = stoi(v[5]);
    data_.clientOrderID_ = stol(v[6]);
    data_.tag_ = v[7];

    data_.orderField_ = {};
    strcpy(data_.orderField_.InstrumentID,v[8].c_str());
    data_.orderField_.OrderPriceType = v[9][0];
    data_.orderField_.Direction = v[10][0];
    strcpy(data_.orderField_.CombOffsetFlag,v[11].c_str());
    strcpy(data_.orderField_.CombHedgeFlag,v[12].c_str());
    data_.orderField_.LimitPrice = stof(v[13]);
    data_.orderField_.VolumeTotalOriginal = stoi(v[14]);
    data_.orderField_.TimeCondition = v[15][0];
    strcpy(data_.orderField_.GTDDate,v[16].c_str());
    data_.orderField_.VolumeCondition = v[17][0];
    data_.orderField_.MinVolume = stoi(v[18]);
    data_.orderField_.ContingentCondition = v[19][0];
    data_.orderField_.StopPrice = stof(v[20]);
    data_.orderField_.ForceCloseReason = v[21][0];
    data_.orderField_.IsAutoSuspend = stoi(v[22]);
    data_.orderField_.UserForceClose = stoi(v[23]);
    data_.orderField_.IsSwapOrder = stoi(v[24]);
    strcpy(data_.orderField_.BusinessUnit,v[25].c_str());
    strcpy(data_.orderField_.CurrencyID,v[26].c_str());   

}

std::shared_ptr<Order> CtpOrderMsg::toPOrder(){
    std::shared_ptr<CtpOrder> o = make_shared<CtpOrder>();
    o->api_ = data_.api_;
    o->account_ = data_.account_;    
    o->clientID_ = data_.clientID_;
    o->clientOrderID_ = data_.clientOrderID_;
    o->tag_ =  data_.tag_;
    o->fullSymbol_ = data_.fullSymbol_;
    o->price_ = data_.price_;
    o->quantity_ = data_.quantity_;
    o->tradedvol_ = data_.tradedvol_;
    o->flag_ = data_.flag_;          
    o->serverOrderID_ = data_.serverOrderID_;
    o->brokerOrderID_ = data_.brokerOrderID_;
    o->orderNo_ = data_.orderNo_;
    o->localNo_ = data_.localNo_;
    o->createTime_ = data_.createTime_;
    o->updateTime_ = data_.updateTime_;
    o->orderStatus_ = data_.orderStatus_;
    memcpy(&o->orderField_, &data_.orderField_,sizeof(CThostFtdcInputOrderField));
    //return static_pointer_cast<Order>(o);
    return o;
}


void CtpParkedOrderMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];
    data_.api_ = v[3];
    data_.account_ = v[4];
    data_.clientID_ = stoi(v[5]);
    data_.clientOrderID_ = stol(v[6]);
    data_.tag_ = v[7];

    data_.parkedOrderField_ = {};
    strcpy(data_.parkedOrderField_.InstrumentID,v[8].c_str());
    data_.parkedOrderField_.OrderPriceType = v[9][0];
    data_.parkedOrderField_.Direction = v[10][0];
    strcpy(data_.parkedOrderField_.CombOffsetFlag,v[11].c_str());
    strcpy(data_.parkedOrderField_.CombHedgeFlag,v[12].c_str());
    data_.parkedOrderField_.LimitPrice = stof(v[13]);
    data_.parkedOrderField_.VolumeTotalOriginal = stoi(v[14]);
    data_.parkedOrderField_.TimeCondition = v[15][0];
    strcpy(data_.parkedOrderField_.GTDDate,v[16].c_str());
    data_.parkedOrderField_.VolumeCondition = v[17][0];
    data_.parkedOrderField_.MinVolume = stoi(v[18]);
    data_.parkedOrderField_.ContingentCondition = v[19][0];
    data_.parkedOrderField_.StopPrice = stof(v[20]);
    data_.parkedOrderField_.ForceCloseReason = v[21][0];
    data_.parkedOrderField_.IsAutoSuspend = stoi(v[22]);
    data_.parkedOrderField_.UserForceClose = stoi(v[23]);
    data_.parkedOrderField_.IsSwapOrder = stoi(v[24]);
    strcpy(data_.parkedOrderField_.BusinessUnit,v[25].c_str());
    strcpy(data_.parkedOrderField_.CurrencyID,v[26].c_str());   

}

std::shared_ptr<Order> CtpParkedOrderMsg::toPOrder(){
    auto o = make_shared<CtpParkedOrder>();
    o->api_ = data_.api_;
    o->account_ = data_.account_;    
    o->clientID_ = data_.clientID_;
    o->clientOrderID_ = data_.clientOrderID_;
    o->tag_ =  data_.tag_;
    o->fullSymbol_ = data_.fullSymbol_;
    o->price_ = data_.price_;
    o->quantity_ = data_.quantity_;
    o->tradedvol_ = data_.tradedvol_;
    o->flag_ = data_.flag_;          
    o->serverOrderID_ = data_.serverOrderID_;
    o->brokerOrderID_ = data_.brokerOrderID_;
    o->orderNo_ = data_.orderNo_;
    o->localNo_ = data_.localNo_;
    o->createTime_ = data_.createTime_;
    o->updateTime_ = data_.updateTime_;
    o->orderStatus_ = data_.orderStatus_;
    memcpy(&o->parkedOrderField_, &data_.parkedOrderField_,sizeof(CThostFtdcParkedOrderField));
    //return static_pointer_cast<Order>(o);
    return o;
}



void OrderStatusMsg::set(std::shared_ptr<Order> po){
    //data_ = *po;
    data_.api_ = po->api_;
    data_.account_ = po->account_;    
    data_.clientID_ = po->clientID_;
    data_.clientOrderID_ = po->clientOrderID_;
    data_.tag_ =  po->tag_;
    data_.fullSymbol_ = po->fullSymbol_;
    data_.price_ = po->price_;
    data_.quantity_ = po->quantity_;
    data_.tradedvol_ = po->tradedvol_;
    data_.flag_ = po->flag_;       
    data_.serverOrderID_ = po->serverOrderID_;
    data_.brokerOrderID_ = po->brokerOrderID_;
    data_.orderNo_ = po->orderNo_;
    data_.localNo_ = po->localNo_;
    data_.createTime_ = po->createTime_;
    data_.updateTime_ = po->updateTime_;
    data_.orderStatus_ = po->orderStatus_;

}


string OrderStatusMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR + data_.api_  
        + SERIALIZATION_SEPARATOR + data_.account_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.clientID_) 
        + SERIALIZATION_SEPARATOR + std::to_string(data_.clientOrderID_) 
        + SERIALIZATION_SEPARATOR + data_.tag_
        + SERIALIZATION_SEPARATOR + data_.fullSymbol_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.price_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.quantity_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.tradedvol_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.flag_)                             
        + SERIALIZATION_SEPARATOR + std::to_string(data_.serverOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.brokerOrderID_)
        + SERIALIZATION_SEPARATOR + data_.orderNo_
        + SERIALIZATION_SEPARATOR + data_.localNo_
        + SERIALIZATION_SEPARATOR + data_.createTime_
        + SERIALIZATION_SEPARATOR + data_.updateTime_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.orderStatus_);   
    return str;

}


string PosMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR + data_.key_
        + SERIALIZATION_SEPARATOR + data_.account_
        + SERIALIZATION_SEPARATOR + data_.api_
        + SERIALIZATION_SEPARATOR + data_.fullSymbol_
        + SERIALIZATION_SEPARATOR + data_.type_							
        + SERIALIZATION_SEPARATOR + std::to_string(data_.avgPrice_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.size_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.preSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.freezedSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.closedpl_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.openpl_) 
        + SERIALIZATION_SEPARATOR + ymdhmsf();
    return str;
}

void PosMsg::set(std::shared_ptr<Position> pp){
    //data_ = *pp;
    data_.key_ = pp->key_;
    data_.account_ = pp->account_;
    data_.api_ = pp->api_;
    data_.fullSymbol_ = pp->fullSymbol_;
    data_.avgPrice_ = pp->avgPrice_;
    data_.size_ = pp->size_;
    data_.preSize_ = pp->preSize_;
    data_.freezedSize_ = pp->freezedSize_;
    data_.openpl_ = pp->openpl_;
    data_.closedpl_ = pp->closedpl_;
    data_.type_ = pp->type_;
    data_.posNo_ = pp->posNo_;
}



void OrderActionMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];
    data_.clientID_ = stoi(v[3]);
    data_.clientOrderID_ = stol(v[4]);
    data_.serverOrderID_ = stol(v[5]);
}

void SubscribeMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];  
    symtype_ = SymbolType(stoi(v[3]));  
    for (int i = 4; i < v.size(); i++)
        data_.push_back(v[i]);

}

void UnSubscribeMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR); 
    destination_ = v[0];
    source_ = v[1];
    symtype_ = SymbolType(stoi(v[3]));     
    for (int i = 4; i < v.size(); i++)
        data_.push_back(v[i]);

}

void QryContractMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];     
    symtype_ = SymbolType(stoi(v[3]));     
    data_ = v[4];

}


string ErrorMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	data_
        + SERIALIZATION_SEPARATOR + ymdhms();				
    return str;
}

string InfoMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	data_
        + SERIALIZATION_SEPARATOR + ymdhms();				
    return str;
}




}


