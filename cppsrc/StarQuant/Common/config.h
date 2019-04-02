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

	// enum class MSGQ : uint8_t {
	// 	NANOMSG = 0, ZMQ, KAFKA, WEBSOCKET
	// };

	// enum class MSGQ_PROTOCOL : uint8_t {
	// 	PAIR = 0, REQ, REP, PUB, SUB, PIPELINE
	// };
// -----------------------------msg type for interprocess communication-----------------
	enum MSG_TYPE : int32_t {
		PYTHON_OBJ = 0,
// 10 - 19 strategy
		MSG_TYPE_STRATEGY_START = 10,
		MSG_TYPE_STRATEGY_END = 11,
		MSG_TYPE_TRADE_ENGINE_LOGIN = 12, // 
		MSG_TYPE_TRADE_ENGINE_ACK = 13, // 
		MSG_TYPE_STRATEGY_POS_SET = 14, // 
// 20 - 29 service
		MSG_TYPE_PAGED_START = 20,
		MSG_TYPE_PAGED_END = 21,
// 30 - 49 control
		MSG_TYPE_TD_ENGINE_OPEN = 30,
		MSG_TYPE_TD_ENGINE_CLOSE = 31,
		MSG_TYPE_MD_ENGINE_OPEN = 32,
		MSG_TYPE_MD_ENGINE_CLOSE = 33,

		MSG_TYPE_SWITCH_TRADING_DAY = 48,
		MSG_TYPE_STRING_COMMAND = 49,
// 50 - 89 utilities
		MSG_TYPE_TIME_TICK = 50,
		MSG_TYPE_SUBSCRIBE_MARKET_DATA = 51,
		MSG_TYPE_SUBSCRIBE_L2_MD = 52,
		MSG_TYPE_SUBSCRIBE_INDEX = 53,
		MSG_TYPE_SUBSCRIBE_ORDER_TRADE = 54,
		MSG_TYPE_UNSUBSCRIBE = 55,
		MSG_TYPE_ENGINE_STATUS = 60,


// 90 - 99 memory alert
		MSG_TYPE_MEMORY_FROZEN = 90, // UNLESS SOME MEMORY UNLOCK, NO MORE LOCKING		

//  100-199 market MSG
		MSG_TYPE_TICK_L1 = 100,
		MSG_TYPE_TICK_L5 = 101,
		MSG_TYPE_TICK_L10 = 102,
		MSG_TYPE_TICK_L20 = 103,
		MSG_TYPE_BAR_1MIN = 111,
		MSG_TYPE_BAR_5MIN = 112,
		MSG_TYPE_BAR_15MIN = 113,
		MSG_TYPE_BAR_1HOUR = 114,
		MSG_TYPE_BAR_1DAY = 115,
		MSG_TYPE_BAR_1WEEK = 116,
		MSG_TYPE_BAR_1MON = 117,
	
		MSG_TYPE_Trade =160,
		MSG_TYPE_Bid = 161,
		MSG_TYPE_Ask = 162,
		MSG_TYPE_Full = 163,
		MSG_TYPE_BidPrice = 164,
		MSG_TYPE_BidSize = 165,
		MSG_TYPE_AskPrice = 166,
		MSG_TYPE_AskSize = 167,
		MSG_TYPE_TradePrice = 168,
		MSG_TYPE_TradeSize = 169,
		MSG_TYPE_OpenPrice = 170,
		MSG_TYPE_HighPrice = 171,
		MSG_TYPE_LowPrice = 172,
		MSG_TYPE_ClosePrice = 173,
		MSG_TYPE_Volume = 174,
		MSG_TYPE_OpenInterest = 175,
		MSG_TYPE_Hist =176,

//  200-299 broker msg	
		MSG_TYPE_QRY_POS       = 201,
		MSG_TYPE_RSP_POS       = 202,
		MSG_TYPE_ORDER         = 204,
		MSG_TYPE_RTN_ORDER     = 205,
		MSG_TYPE_RTN_TRADE     = 206,
		MSG_TYPE_ORDER_ACTION  = 207,
		MSG_TYPE_QRY_ACCOUNT   = 208,
		MSG_TYPE_RSP_ACCOUNT   = 209,
		MSG_TYPE_QRY_CONTRACT   = 210,
		MSG_TYPE_RSP_CONTRACT   = 211,
		MSG_TYPE_CANCEL_ORDER = 212,
		MSG_TYPE_CANCEL_ALL = 213,
		MSG_TYPE_QRY_COMMODITY = 220,
			
//	300-399 general ,log, etc msg

		MSG_TYPE_INFO   = 300,
		MSG_TYPE_ERROR = 301,
		MSG_TYPE_WARNING = 302,
		MSG_TYPE_NOTIFY = 303,

//  400-499 test msg
		MSG_TYPE_TEST = 400
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
		string SERVERPUB_URL = "tcp://localhost:55555";
		string SERVERSUB_URL = "tcp://localhost:55556";
	
		string MKT_DATA_PUBSUB_PORT = "55555";				// market/tick data
		string BROKERAGE_PAIR_PORT = "55556";				// brokerage order, account, etc
		string BAR_AGGREGATOR_PUBSUB_PORT = "55557";		// bar from aggregation service
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
