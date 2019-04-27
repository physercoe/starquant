
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
        + SERIALIZATION_SEPARATOR + to_string(data_.ticksize_)
        + SERIALIZATION_SEPARATOR + to_string(data_.multiplier_);
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
        + SERIALIZATION_SEPARATOR + ymdhmsf();
    return s;
}

string FillMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR +	std::to_string(data_.serverOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.clientOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.brokerOrderID_)
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

string OrderMsg::serialize(){
    string sprice = "0.0";
    if (data_.orderType_ == OrderType::OT_Limit){
        sprice = std::to_string(data_.limitPrice_);
    }else if (data_.orderType_ == OrderType::OT_StopLimit){
        sprice = std::to_string(data_.stopPrice_);
    }
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.serverOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.clientOrderID_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.brokerOrderID_)
        + SERIALIZATION_SEPARATOR + data_.fullSymbol_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.orderSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.orderFlag_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.orderType_)
        + SERIALIZATION_SEPARATOR + sprice
        + SERIALIZATION_SEPARATOR + std::to_string(data_.filledSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.avgFilledPrice_)
        + SERIALIZATION_SEPARATOR + data_.createTime_
        + SERIALIZATION_SEPARATOR + data_.cancelTime_
        + SERIALIZATION_SEPARATOR + data_.account_
        + SERIALIZATION_SEPARATOR + data_.api_
        + SERIALIZATION_SEPARATOR + data_.tag_
        + SERIALIZATION_SEPARATOR + data_.orderNo_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.orderStatus_)   
        + SERIALIZATION_SEPARATOR + ymdhms();				
    return str;
}

void OrderMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    destination_ = v[0];
    source_ = v[1];
    data_.clientID_ = stoi(v[1]);
    data_.clientOrderID_ = stol(v[4]);
    data_.orderType_ = static_cast<OrderType>(stoi(v[5]));
    data_.fullSymbol_ = v[6];
    data_.orderSize_ = stoi(v[7]);
    if (data_.orderType_ == OrderType::OT_Limit){
        data_.limitPrice_ = stof(v[8]);
    }else if (data_.orderType_ == OrderType::OT_StopLimit){
        data_.stopPrice_ = stof(v[8]);
    }
    data_.orderFlag_ = static_cast<OrderFlag>(stoi(v[9]));
    data_.tag_ = v[10];
}

std::shared_ptr<Order> OrderMsg::toPOrder(){
    std::shared_ptr<Order> o = make_shared<Order>();
    o->serverOrderID_ = data_.serverOrderID_;
    o->brokerOrderID_ = data_.brokerOrderID_;
    o->createTime_ = data_.createTime_;
    o->orderStatus_ = data_.orderStatus_;
    o->clientID_ = data_.clientID_;
    o->clientOrderID_ = data_.clientOrderID_;
    o->orderType_ = data_.orderType_;
    o->fullSymbol_ = data_.fullSymbol_;
    o->orderSize_ = data_.orderSize_ ;
    o->limitPrice_ = data_.limitPrice_;
    o->stopPrice_ = data_.stopPrice_ ;
    o->orderFlag_ = data_.orderFlag_;
    o->tag_ =  data_.tag_;
    return o;
}



string PosMsg::serialize(){
    string str =  destination_ 
        + SERIALIZATION_SEPARATOR + source_
        + SERIALIZATION_SEPARATOR + to_string(msgtype_)
        + SERIALIZATION_SEPARATOR + data_.type_
        + SERIALIZATION_SEPARATOR + data_.account_
        + SERIALIZATION_SEPARATOR + data_.posNo_
        + SERIALIZATION_SEPARATOR + data_.openOrderNo_
        + SERIALIZATION_SEPARATOR + data_.openapi_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.openClientID_)
        + SERIALIZATION_SEPARATOR + data_.closeOrderNo_			
        + SERIALIZATION_SEPARATOR + data_.closeapi_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.closeClientID_)									
        + SERIALIZATION_SEPARATOR + data_.fullSymbol_
        + SERIALIZATION_SEPARATOR + std::to_string(data_.avgPrice_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.size_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.preSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.freezedSize_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.closedpl_)
        + SERIALIZATION_SEPARATOR + std::to_string(data_.openpl_)
        + SERIALIZATION_SEPARATOR + ymdhmsf();
    return str;
}

void OrderActionMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);
    data_.clientID_ = stoi(v[3]);
    data_.clientOrderID_ = stol(v[4]);
    data_.serverOrderID_ = stol(v[5]);
}

void SubscribeMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);    
    for (int i = 3; i < v.size(); i++)
        data_.push_back(v[i]);

}

void UnSubscribeMsg::deserialize(const string& msgin){
    vector<string> v = stringsplit(msgin,SERIALIZATION_SEPARATOR);    
    for (int i = 3; i < v.size(); i++)
        data_.push_back(v[i]);

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


