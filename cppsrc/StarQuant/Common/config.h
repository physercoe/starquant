#ifndef __StarQuant_Common_Config__
#define __StarQuant_Common_Config__

#include <inttypes.h>
#include <cmath>
#include <mutex>
#include <atomic>
#include <string>
#include <memory>
#include <vector>
#include <set>
#include <queue>
#include <map>
#include <list>
#include <deque>
#include <algorithm>
#include <fstream>
#include <sstream>

#include <boost/filesystem.hpp>

#define CEREAL_RAPIDJSON_NAMESPACE creal_rapidjson
#include <cereal/types/unordered_map.hpp>
#include <cereal/types/memory.hpp>
#include <cereal/archives/json.hpp>
#include <cereal/types/vector.hpp>
#include <cereal/types/string.hpp>
#include <cereal/types/map.hpp>

#include <Common/logger.h>
#include <Common/timeutil.h>
#include <Common/msgq.h>

#if defined(_WIN32) || defined(_WIN64)
#ifdef DLL_EXPORT
#define DLL_EXPORT_IMPORT  __declspec(dllexport)   // export DLL information
#else
#define DLL_EXPORT_IMPORT  __declspec(dllimport)   // import DLL information
#endif
#else
#define DLL_EXPORT_IMPORT
#endif

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include<WinSock2.h>
#else
#include <unistd.h>
#endif

using std::vector;
using std::string;
using std::set;
using std::mutex;
using std::map;
using std::atomic_int;

//http://google-styleguide.googlecode.com/svn/trunk/cppguide.xml

namespace StarQuant {

#define SERIALIZATION_SEPARATOR '|'

#define PRINT_TO_FILE logger::instance().Printf2File

#define PRINT_TO__CONSOLE(...) do{\
printf("%s ",ymdhmsf().c_str());printf(__VA_ARGS__);\
}while (0)

#define PRINT_TO_FILE_AND_CONSOLE(...) do{\
logger::instance().Printf2File(__VA_ARGS__);\
printf("%s ",ymdhmsf().c_str());printf(__VA_ARGS__);\
}while (0)




#define PRINT_SHUTDOWN_MESSAGE printf("\n Thank you for using Star Quant. Goodbye! \n");

	enum class RUN_MODE :uint8_t {
		TRADE_MODE = 0, RECORD_MODE, REPLAY_MODE
	};

	enum class BROKERS : uint8_t {
		IB = 0, CTP, GOOGLE, SINA, PAPER,TAP
	};

// -----------------------------msg type for interprocess communication-----------------
	enum MSG_TYPE : int32_t {
//  10* datatype same as ticktype 
		MSG_TYPE_TICK_L1 = 1000,
		MSG_TYPE_TICK_L5 = 1001,
		MSG_TYPE_TICK_L10 = 1002,
		MSG_TYPE_TICK_L20 = 1003,
		MSG_TYPE_BAR_1MIN = 1011,
		MSG_TYPE_BAR_5MIN = 1012,
		MSG_TYPE_BAR_15MIN = 1013,
		MSG_TYPE_BAR_1HOUR = 1014,
		MSG_TYPE_BAR_1DAY = 1015,
		MSG_TYPE_BAR_1WEEK = 1016,
		MSG_TYPE_BAR_1MON = 1017,	
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
		MSG_TYPE_ENGINE_CONNECT = 1120,
		MSG_TYPE_ENGINE_DISCONNECT = 1121,
		MSG_TYPE_SWITCH_TRADING_DAY = 1141,

//  12* strategy
		MSG_TYPE_STRATEGY_START = 1210,
		MSG_TYPE_STRATEGY_END = 1211,

//  13*  tast 
        MSG_TYPE_TIMER = 1301,
		MSG_TYPE_TASK_START = 1310,
		MSG_TYPE_TASK_STOP = 1311,

//  20* engine action
		// request
		MSG_TYPE_SUBSCRIBE_MARKET_DATA = 2001,
		MSG_TYPE_SUBSCRIBE_L2_MD = 2002,
		MSG_TYPE_SUBSCRIBE_INDEX = 2003,
		MSG_TYPE_SUBSCRIBE_ORDER_TRADE = 2004,
		MSG_TYPE_UNSUBSCRIBE = 2011,
		MSG_TYPE_QRY_COMMODITY = 2021,	
		MSG_TYPE_QRY_CONTRACT   = 2022,
		MSG_TYPE_QRY_POS       = 2023,
		MSG_TYPE_QRY_ACCOUNT   = 2024,
		MSG_TYPE_ORDER         = 2031,  //insert order
		MSG_TYPE_ORDER_ACTION  = 2032,  //cancel order
		MSG_TYPE_CANCEL_ORDER = 2033,
		MSG_TYPE_CANCEL_ALL = 2039,
		//call back
		MSG_TYPE_RSP_POS       = 2051,
		MSG_TYPE_RTN_ORDER     = 2052, //order status
		MSG_TYPE_RTN_TRADE     = 2053,
		MSG_TYPE_RSP_ACCOUNT   = 2054,
		MSG_TYPE_RSP_CONTRACT   = 2055,

//	31*: info class msg, mainly about sys
		MSG_TYPE_INFO   = 3100,
		MSG_TYPE_INFO_ENGINE_MDCONNECTED = 3101,
		MSG_TYPE_INFO_ENGINE_MDDISCONNECTED = 3102,
		MSG_TYPE_INFO_ENGINE_TDCONNECTED = 3103,
		MSG_TYPE_INFO_ENGINE_TDDISCONNECTED = 3104,
		MSG_TYPE_INFO_HEARTBEAT_WARNING =3105,

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

//  40*: test class msg
		MSG_TYPE_TEST = 4000
	};

//------------------------------end msg type ---------------------------


// ------accunt struc-------
	struct Account{
		string id;
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
		string apitype;
	};


	class CConfig {
		static CConfig* pinstance_;
		static mutex instancelock_;

		CConfig();
	public:
		RUN_MODE _mode = RUN_MODE::TRADE_MODE;
		BROKERS _broker = BROKERS::PAPER;
		string brokerapi ="none";
		MSGQ _msgq = MSGQ::NANOMSG;
		int _tickinterval =0;
		int _brokerdelay = 0;
		static CConfig& instance();
		map<string,Account> _apimap;

		void readConfig();

		string _config_dir;
		string _log_dir;
		string _data_dir;
		string configDir();
		string logDir();
		string dataDir();
		string logconfigfile_;

		map<string,bool> _loadapi;

		string SecurityFullNameToCtpSymbol(const std::string& symbol);
		string CtpSymbolToSecurityFullName(const std::string& symbol);

		/******************************************* Brokerage ***********************************************/
		
		string ib_host = "127.0.0.1";
		uint64_t ib_port = 7496;
		atomic_int ib_client_id;

		string account = "default";
		string filetoreplay = "";

		string ctp_broker_id = "";
		string ctp_user_id = "";
		string ctp_password = "";
		string ctp_auth_code = "";
		string ctp_user_prod_info = "";
		string ctp_data_address = "";
		string ctp_broker_address = "";
		
		uint32_t tap_sessionid=0;
		string tap_broker_id = "";
		string tap_user_id = "";
		string tap_user_name ="";
		string tap_password = "";
		string tap_auth_code = "";
		string tap_user_prod_info = "";
		string tap_data_address = "";
		string tap_data_ip = "";
		uint16_t tap_data_port = 0;
		string tap_broker_address = "";	
		string tap_broker_ip = "";
		uint16_t tap_broker_port = 0;
			
		/**************************************** End of Brokeragee ******************************************/
		/****************************************Securities List *************************************/
		vector<string> securities;  //full symbol
		map<string,string> instrument2sec; //instrument id to full symbol map
		map<string,string> sec2instrument; //symbol to ctp instrument

		/****************************************End of Securities List *************************************/

		/**************************************** Database info ******************************************/
		string _mongodbaddr = "mongodb://localhost:27017";
		string _mongodbname = "";
		//vector<string> 
		/**************************************** End of Database ******************************************/

		/******************************************* Message Queue ***********************************************/
		string SERVERPUB_URL = "tcp://localhost:55555";  //to all clients
		string SERVERSUB_URL = "tcp://localhost:55556";  // pub the requests to engines(which subscribe)
		string SERVERPULL_URL = "tcp://localhost:55557"; //listen all the requests from clients


		string MKT_DATA_PUBSUB_PORT = "55555";				// market/tick data
		string BROKERAGE_PAIR_PORT = "55556";				// brokerage order, account, etc
		string BAR_AGGREGATOR_PUBSUB_PORT = "ipc://bar";		// bar from aggregation service
		string API_PORT = "55558";							// client port
		string API_ZMQ_DATA_PORT = "55559";					// client port
				
		string tick_msg = "k";
		string last_price_msg = "p";
		string last_size_msg = "z";
		string bar_msg = "b";
		string new_order_msg = "o";
		string cancel_order_msg = "c";
		string order_status_msg = "s";
		string fill_msg = "f";				// including partial fill
		string close_all_msg = "a";
		string position_msg = "n";
		string account_msg = "u";		// user
		string contract_msg = "r";
		string hist_msg = "h";
		string general_msg = "m";
		string test_msg = "e";		// echo

		/**************************************** End of Message Queue ******************************************/
	};
}

#endif	// __StarQuant_Common_Config__
