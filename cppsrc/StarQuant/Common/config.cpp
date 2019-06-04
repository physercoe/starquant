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
//  reset maps
		_gatewaymap.clear();

// 读入合约相关信息数据，
		std::lock_guard<mutex> g(readlock_);
		
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
		autoconnect = config["autoconnect"].as<bool>();
		autoqry = config["autoqry"].as<bool>();
		_mongodbaddr = config["dbaddr"].as<std::string>();
		_mongodbname = config["dbname"].as<std::string>();

		SERVERPUB_URL = config["serverpub_url"].as<std::string>();
		SERVERSUB_URL = config["serversub_url"].as<std::string>();
		SERVERPULL_URL = config["serverpull_url"].as<std::string>();

		// read gateway info
		const std::vector<string> gws = config["gateway"].as<std::vector<string>>();
		for (auto s : gws){
			struct Gateway gw;
			gw.id = s;
			gw.intid = config[s]["intid"].as<int>();
			gw.api = config[s]["api"].as<std::string>();
			gw.brokerid = config[s]["brokerid"].as<std::string>();
			auto mdips = config[s]["md_ip"].as<std::vector<string>>();
			gw.md_ip.assign(mdips.begin(),mdips.end());
			auto tdips = config[s]["td_ip"].as<std::vector<string>>();
			gw.td_ip.assign(tdips.begin(),tdips.end());
			gw.md_port = config[s]["md_port"].as<uint16_t>();
			gw.td_port = config[s]["td_port"].as<uint16_t>();
			gw.userid = config[s]["userid"].as<std::string>();
			gw.password = config[s]["password"].as<std::string>();
			gw.auth_code = config[s]["auth_code"].as<std::string>();
			gw.productinfo = config[s]["user_prod_info"].as<std::string>();
			gw.appid = config[s]["appid"].as<std::string>();
			gw.publicstream = config[s]["publicstream"].as<std::string>();
			gw.privatestream = config[s]["privatestream"].as<std::string>();
			_gatewaymap[s] = gw;
		}		

		// read risk info
		riskcheck = config["risk"]["check"].as<bool>();
		sizeperorderlimit = config["risk"]["sizeperorder"].as<int>();
		cashperorderlimit = config["risk"]["cashperorder"].as<double>();
		ordercountlimit = config["risk"]["ordercount"].as<int>();
		cashlimit = config["risk"]["cash"].as<double>();
		ordersizelimit = config["risk"]["ordersize"].as<int>();
		ordercountperseclimit = config["risk"]["ordercountpersec"].as<int>();
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
