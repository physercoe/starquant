#include <fstream>
#include <boost/program_options.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/filesystem.hpp>
#include <boost/algorithm/string.hpp>
#include <cctype>

#include <Common/config.h>
#include <Common/util.h>
#include <Common/datastruct.h>
#include <yaml-cpp/yaml.h>

namespace bpt = boost::property_tree;
namespace bpo = boost::program_options;
namespace fs = boost::filesystem;

namespace StarQuant {
	CConfig* CConfig::pinstance_ = nullptr;
	mutex CConfig::instancelock_;

	CConfig::CConfig() {
		_loadapi["CTP"] = false;
		_loadapi["TAP"] = false;
		_loadapi["IB"] = false;
		_loadapi["SINA"] = false;
		_loadapi["GOOGLE"] = false;
		_loadapi["PAPER"] = false;
		_loadapi["XTP"] = false;
		readConfig();
	}

	CConfig& CConfig::instance() {
		if (pinstance_ == nullptr) {
			std::lock_guard<mutex> g(instancelock_);
			if (pinstance_ == nullptr) {
				pinstance_ = new CConfig();
			}
		}
		return *pinstance_;
	}

	void CConfig::readConfig()
	{
#ifdef _DEBUG
		std::printf("Current path is : %s\n", boost::filesystem::current_path().string().c_str());
#endif
// 读入合约相关信息数据，TODO:从 md qry得到相关数据
		string contractpath = boost::filesystem::current_path().string() + "/etc/contract.yaml";
		YAML::Node contractinfo = YAML::LoadFile(contractpath);
		//std::cout<<contractinfo[0].  as<std::string>();
		for (YAML::const_iterator exch = contractinfo.begin();exch != contractinfo.end();exch++)
		{
			string exchange = 	exch->first.as<std::string>();
			for (YAML::const_iterator cont = exch->second.begin();cont != exch->second.end();cont++)
			{
				string contract = cont->first.as<std::string>();
				string instrument = cont->second["ctpsymbol"].as<std::string>();
				string fullsym = exchange + " " + cont->second["type"].as<std::string>() + " " + contract;
				instrument2sec[instrument] = fullsym ;
				sec2instrument[fullsym] = instrument;							
			}

		}


		string path = boost::filesystem::current_path().string() + "/etc/config_server.yaml";
		YAML::Node config = YAML::LoadFile(path);
		string configmode = config["mode"].as<std::string>();
		if (configmode =="record")
			_mode = RUN_MODE::RECORD_MODE;
		else if (configmode == "replay"){
			_mode = RUN_MODE::REPLAY_MODE;
			_tickinterval =config["tickinterval"].as<int>();
			_brokerdelay = config["brokerdelay"].as<int>();
			filetoreplay = config["filetoreplay"].as<std::string>();
		}
		_config_dir = boost::filesystem::current_path().string() + "/etc/";
		_log_dir = config["log_dir"].as<std::string>();
		_data_dir = config["data_dir"].as<std::string>();
		boost::filesystem::path log_path(logDir());
		boost::filesystem::create_directory(log_path);
		boost::filesystem::path data_path(dataDir());
		boost::filesystem::create_directory(data_path);
		logconfigfile_ = boost::filesystem::current_path().string() + "/etc/config_log";
		// const string msgq = config["msgq"].as<std::string>();
		// _msgq = MSGQ::NANOMSG;
		cpuaffinity = config["cpuaffinity"].as<bool>();
		_mongodbaddr = config["dbaddr"].as<std::string>();
		_mongodbname = config["dbname"].as<std::string>();
		 
		SERVERPUB_URL = config["serverpub_url"].as<std::string>();
		SERVERSUB_URL = config["serversub_url"].as<std::string>();
		SERVERPULL_URL = config["serverpull_url"].as<std::string>();
		
		const std::vector<string> apis = config["apis"].as<std::vector<string>>();
		for (auto s : apis){
			_loadapi[s] = true;
			struct Account acc;
			acc.id = s;
			acc.apitype = config[s]["api"].as<std::string>();
			acc.brokerid = config[s]["brokerid"].as<std::string>();
			acc.md_ip = config[s]["md_ip"].as<std::string>();
			acc.md_port = config[s]["md_port"].as<uint16_t>();
			acc.td_ip = config[s]["td_ip"].as<std::string>();
			acc.td_port = config[s]["td_port"].as<uint16_t>();
			acc.userid = config[s]["userid"].as<std::string>();
			acc.password = config[s]["password"].as<std::string>();
			acc.auth_code = config[s]["auth_code"].as<std::string>();
			acc.productinfo = config[s]["user_prod_info"].as<std::string>();
			acc.intid = config[s]["intid"].as<int>();
			_apimap[s] = acc;
		}
	}

	string CConfig::configDir()
	{
		//return boost::filesystem::current_path().string();
		return _config_dir;
	}

	string CConfig::logDir()
	{
		return _log_dir;
	}

	string CConfig::dataDir()
	{
		return _data_dir;
	}

	string CConfig::SecurityFullNameToCtpSymbol(const std::string& symbol) {
		vector<string> v = stringsplit(symbol, ' ');
		string tmp = v[0] + " " + v[1] + " " + v[2];
		string ctbticker = sec2instrument[tmp] + v[3];
		return ctbticker;
	}

	string CConfig::CtpSymbolToSecurityFullName(const std::string& symbol) {
		string fullsymbol;
		string num = symbol;
		string alpha = symbol;
		num.erase(std::remove_if(num.begin(),num.end(),&::isalpha),num.end());
		alpha.erase(std::remove_if(alpha.begin(),alpha.end(),&::isdigit),alpha.end());
		string tmp = instrument2sec[alpha];
		fullsymbol = tmp + " " + num;
		return fullsymbol;
	}
	







}
