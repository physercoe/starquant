#include <vector>
#include <fstream>
#include <boost/algorithm/algorithm.hpp>
#include <yaml-cpp/yaml.h>
#include <fmt/format.h>

#include <Data/datamanager.h>
#include <Trade/portfoliomanager.h>
#include <Common/datastruct.h>



namespace StarQuant {
    DataManager* DataManager::pinstance_ = nullptr;
    mutex DataManager::instancelock_;

    DataManager::DataManager() : count_(0)
    {
        loadSecurityFile();
    }

    DataManager::~DataManager()
    {
    }

    DataManager& DataManager::instance() {
        if (pinstance_ == nullptr) {
            lock_guard<mutex> g(instancelock_);
            if (pinstance_ == nullptr) {
                pinstance_ = new DataManager();
            }
        }
        return *pinstance_;
    }



    void DataManager::updateOrderBook(const Fill& fill){
    //assume only price change
        if (orderBook_.find(fill.fullSymbol_) != orderBook_.end()){
            orderBook_[fill.fullSymbol_].price_ = fill.tradePrice_;
            orderBook_[fill.fullSymbol_].size_ = fill.tradeSize_;
        }
        else
        {
            Tick newk;
            newk.depth_ = 0;
            newk.price_ = fill.tradePrice_;
            newk.size_ = fill.tradeSize_;
            orderBook_[fill.fullSymbol_] = newk;
        }
    }

    void DataManager::loadSecurityFile(){
        try{
            string contractpath = boost::filesystem::current_path().string() + "/etc/ctpcontract.yaml";
            YAML::Node contractinfo = YAML::LoadFile(contractpath);
            for (YAML::const_iterator symsec = contractinfo.begin();symsec != contractinfo.end(); symsec++)
            {
                auto sym = symsec->first.as<std::string>();
                auto securities = symsec->second;
                Security sec;
                sec.symbol_ = securities["symbol"].as<std::string>(); 
                sec.exchange_ = securities["exchange"].as<std::string>();
                sec.securityType_ = securities["product"].as<char>();
                sec.multiplier_ = securities["size"].as<int>();
                sec.localName_ = securities["name"].as<std::string>();
                sec.ticksize_ = securities["pricetick"].as<double>();
                sec.postype_ = securities["positiontype"].as<char>() ;
                sec.longMarginRatio_ = securities["long_margin_ratio"].as<double>();
                sec.shortMarginRatio_ = securities["short_margin_ratio"].as<double>();
                sec.underlyingSymbol_ = securities["option_underlying"].as<std::string>();
                sec.optionType_ = securities["option_type"].as<char>();
                sec.strikePrice_ = securities["option_strike"].as<double>();
                sec.expiryDate_ = securities["option_expiry"].as<std::string>();
                sec.fullSymbol_ =  securities["full_symbol"].as<std::string>();
                securityDetails_[sym] = sec;
                ctp2Full_[sym] = sec.fullSymbol_;
                full2Ctp_[sec.fullSymbol_] = sym;
            }
            //back up 
            std::ofstream fout("etc/ctpcontract.yaml.bak");
            fout<< contractinfo;
        }
        catch(exception &e){
            fmt::print("Read contract exception:{}.",e.what());
        }
        catch(...){
            fmt::print("Read contract error!");
        }
    }

    void DataManager::saveSecurityToFile() {
        try{
            YAML::Node securities;
            for (auto iterator = securityDetails_.begin(); iterator != securityDetails_.end(); ++iterator) {
                auto sym = iterator->first;
                auto sec = iterator->second;
                securities[sym]["symbol"] = sec.symbol_; 
                securities[sym]["exchange"] = sec.exchange_;
                securities[sym]["product"] = sec.securityType_;
                securities[sym]["size"] = sec.multiplier_;
                securities[sym]["name"] = sec.localName_;
                securities[sym]["pricetick"] = sec.ticksize_;
                securities[sym]["positiontype"] = sec.postype_;
                securities[sym]["long_margin_ratio"] = sec.longMarginRatio_;
                securities[sym]["short_margin_ratio"] = sec.shortMarginRatio_;
                securities[sym]["option_underlying"] = sec.underlyingSymbol_;
                securities[sym]["option_type"] = sec.optionType_;
                securities[sym]["option_strike"] = sec.strikePrice_;
                securities[sym]["option_expiry"] = sec.expiryDate_;
                string fullsym;
                string type;
                string product;
                string contracno;
                int i;
                if (sec.securityType_ == '1' || sec.securityType_ == '2'){
                    for(i = 0;i<sym.size();i++){
                        if (isdigit(sym[i]))
                            break;
                    }
                    product = sym.substr(0,i);
                    contracno = sym.substr(i);
                    type = (sec.securityType_ == '1'? "F":"O");
                    fullsym = sec.exchange_ + " " + type + " " + boost::to_upper_copy(product) + " " + contracno;
                }
                else if (sec.securityType_ == '3'){
                    int pos = sym.find(" ");
                    string combo = sym.substr(pos+1);
                    int sep = combo.find("&");
                    string sym1 = combo.substr(0,sep);
                    string sym2 = combo.substr(sep+1);
                    for(i = 0;i<sym1.size();i++){
                        if (isdigit(sym1[i]))
                            break;
                    }					
                    product = sym1.substr(0,i) + "&";
                    contracno = sym1.substr(i) + "&";
                    for(i = 0;i<sym2.size();i++){
                        if (isdigit(sym2[i]))
                            break;
                    }
                    product += sym2.substr(0,i);
                    contracno += sym2.substr(i);
                    fullsym = sec.exchange_ + " " + "S" + " " + boost::to_upper_copy(product) + " " + contracno;						
                }
                else 
                {
                    fullsym = sec.exchange_ + " " + sec.securityType_ + " " + sym;	
                }
                securities[sym]["full_symbol"] = fullsym;
                ctp2Full_[sym] = fullsym;
                full2Ctp_[fullsym] = sym;
                securityDetails_[sym].fullSymbol_ = fullsym;
            }
            std::ofstream fout("etc/ctpcontract.yaml");
            fout<< securities;
        }
        catch(exception &e){
            fmt::print("Write Contract exception:{}.",e.what());
        }
        catch(...){
            fmt::print("Write Contract error!");
        }
    }



    void DataManager::reset() {
        orderBook_.clear();
        //_5s.clear();
        //_15s.clear();
        // _60s.clear();
        //_1d.clear();
        securityDetails_.clear();
        count_ = 0;
    }






    void DataManager::rebuild() {
        // for (auto& s : CConfig::instance().securities) {
        // 	Tick_L5 k;
        // 	k.fullsymbol_ = s;
        // 	_latestmarkets[s] = k;

        // 	//_5s[s].fullsymbol = s; _5s[s].interval_ = 5;
        // 	//_15s[s].fullsymbol = s; _15s[s].interval_ = 15;
        // 	// _60s[s].fullsymbol = s; _60s[s].interval_ = 60;
        // 	//_1d[s].fullsymbol = s; _1d[s].interval_ = 24 * 60 * 60;
        // }
    }

    // void DataManager::SetTickValue(Tick& k) {
        // PRINT_TO_FILE("INFO:[%s,%d][%s]%s, %.2f\n", __FILE__, __LINE__, __FUNCTION__, k.fullsymbol_.c_str(), k.price_);		// for debug
        // //cout<<"settickvalue ktype: "<<k.msgtype_<<" price"<<k.price_<<endl;
        // if (k.msgtype_ == MSG_TYPE::MSG_TYPE_Bid) {
        // 	_latestmarkets[k.fullsymbol_].bidprice_L1_ = k.price_;
        // 	_latestmarkets[k.fullsymbol_].bidsize_L1_ = k.size_;
        // }
        // else if (k.msgtype_ == MSG_TYPE::MSG_TYPE_Ask ){
        // 	_latestmarkets[k.fullsymbol_].askprice_L1_ = k.price_;
        // 	_latestmarkets[k.fullsymbol_].asksize_L1_ = k.size_;
        // }
        // else if (k.msgtype_ == MSG_TYPE::MSG_TYPE_Trade) {
        // 	_latestmarkets[k.fullsymbol_].price_ = k.price_;
        // 	_latestmarkets[k.fullsymbol_].size_ = k.size_;

        // 	//_5s[k.fullsymbol_].newTick(k);				// if it doesn't exist, operator[] creates a new element with default constructor
        // 	//_15s[k.fullsymbol_].newTick(k);
        // 	_60s[k.fullsymbol_].newTick(k);
        // 	//PortfolioManager::instance().positions_[sym].
        // }
        // else if (k.msgtype_ == MSG_TYPE::MSG_TYPE_TICK_L1 || k.msgtype_ == MSG_TYPE::MSG_TYPE_TICK_L5 || k.msgtype_ == MSG_TYPE::MSG_TYPE_TICK_L20 ) {
        // 	//_latestmarkets[k.fullsymbol_] = dynamic_cast<Tick_L5&>(k);		// default assigement shallow copy
        // 	_latestmarkets[k.fullsymbol_].price_ = k.price_;
        // 	_latestmarkets[k.fullsymbol_].size_ = k.size_;
        // 	//cout<<"settickvalue price"<<_latestmarkets[k.fullsymbol_].price_<<endl;
        // 	_60s[k.fullsymbol_].newTick(k);
        // }
    // }


}

