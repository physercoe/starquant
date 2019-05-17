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

#include <Common/datastruct.h>

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



namespace StarQuant {
	class CConfig {
		static CConfig* pinstance_;
		static mutex instancelock_;

		CConfig();
	public:
		RUN_MODE _mode = RUN_MODE::TRADE_MODE;
		BROKERS _broker = BROKERS::PAPER;
		MSGQ _msgq = MSGQ::NANOMSG;
		int _tickinterval =0;
		int _brokerdelay = 0;
		static CConfig& instance();
		map<string,Gateway> _gatewaymap;

		mutex readlock_;
		void readConfig();

		string _config_dir;
		string _log_dir;
		string _data_dir;
		string configDir();
		string logDir();
		string dataDir();
		string logconfigfile_;


		/****************************************Securities List *************************************/
		vector<string> securities;  //full symbol
		map<string,string> instrument2sec; //instrument id to full symbol map
		map<string,string> sec2instrument; //symbol to ctp instrument
		string SecurityFullNameToCtpSymbol(const std::string& symbol);
		string CtpSymbolToSecurityFullName(const std::string& symbol);
		/****************************************End of Securities List *************************************/

		/**************************************** Database info ******************************************/
		string _mongodbaddr = "mongodb://localhost:27017";
		string _mongodbname = "";
		
		string filetoreplay;
		//vector<string> 
		/**************************************** End of Database ******************************************/

		/******************************************* Message Queue ***********************************************/
		string SERVERPUB_URL = "tcp://localhost:55555";  //to all clients
		string SERVERSUB_URL = "tcp://localhost:55556";  // pub the requests to engines(which subscribe)
		string SERVERPULL_URL = "tcp://localhost:55557"; //listen all the requests from clients
		bool cpuaffinity = false;
		/******************************************* Message Queue **********/
		

		/************************auto task*****************************/
		bool autoconnect = true;
		bool autoqry = false;




		/*****************************************Risk setting**************/
		bool riskcheck = false;
		int sizeperorderlimit = 0;
		double cashperorderlimit = 0.0;
		int ordercountlimit = 0;
		double cashlimit =0.0;
		int ordersizelimit = 0;
		int ordercountperseclimit = 0;

		/*****************************************End Risk setting**************/

		/**************************************** End of Message Queue ******************************************/
	};
}

#endif	// __StarQuant_Common_Config__
