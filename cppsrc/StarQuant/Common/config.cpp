#include <fstream>
#include <boost/program_options.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/filesystem.hpp>
#include <Common/config.h>
//#include <Common/Util/util.h>
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
		string path = boost::filesystem::current_path().string() + "/config_server.yaml";
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
		_config_dir = boost::filesystem::current_path().string();
		_log_dir = config["log_dir"].as<std::string>();
		_data_dir = config["data_dir"].as<std::string>();
		boost::filesystem::path log_path(logDir());
		boost::filesystem::create_directory(log_path);
		boost::filesystem::path data_path(dataDir());
		boost::filesystem::create_directory(data_path);


		const string msgq = config["msgq"].as<std::string>();
		// if (msgq == "zmq")
		// 	_msgq = MSGQ::ZMQ;
		// else if (msgq == "kafka")
		// 	_msgq = MSGQ::KAFKA;
		// else
		// 	_msgq = MSGQ::NANOMSG;
		_msgq = MSGQ::NANOMSG;
		
		// TODO: support multiple accounts; currently only the last account loop counts
		const std::vector<string> accounts = config["accounts"].as<std::vector<string>>();
		for (auto s : accounts) {
			const string broker = config[s]["broker"].as<std::string>();
			if (broker == "IB") {
				_broker = BROKERS::IB;
				account = s;
				ib_port = config[s]["port"].as<long>();
			}
			
			else if (broker == "CTP") {
				_broker = BROKERS::CTP;
				account = s;
				brokerapi ="CTP";
				ctp_broker_id = config[s]["brokerid"].as<std::string>();
				ctp_user_id = config[s]["userid"].as<std::string>();;
				ctp_password = config[s]["password"].as<std::string>();
				ctp_auth_code = config[s]["auth_code"].as<std::string>();
				ctp_user_prod_info = config[s]["user_prod_info"].as<std::string>();
				ctp_data_address = config[s]["md_address"].as<std::string>();
				ctp_broker_address = config[s]["td_address"].as<std::string>();
			}
			else if (broker == "TAP") {
				_broker = BROKERS::TAP;
				account = s;
				brokerapi = "TAP";
				tap_sessionid = config[s]["sessionid"].as<unsigned int>();
				std::cout<<tap_sessionid;
				//tap_broker_id = config[s]["broker"].as<std::string>();
				//tap_user_id = s;
				tap_password = config[s]["password"].as<std::string>();
				tap_user_name = config[s]["user_name"].as<std::string>();
				tap_auth_code = config[s]["auth_code"].as<std::string>();
				tap_user_prod_info = config[s]["user_prod_info"].as<std::string>();
				tap_data_address = config[s]["md_address"].as<std::string>();
				tap_broker_address = config[s]["td_address"].as<std::string>();
				tap_data_ip = config[s]["md_ip"].as<std::string>();
				tap_data_port = config[s]["md_port"].as<unsigned short>();
				tap_broker_ip = config[s]["td_ip"].as<std::string>();
				tap_broker_port = config[s]["td_port"].as<unsigned short>();				
				
			}			
			else if (broker == "SINA")
				_broker = BROKERS::SINA;
			else
				_broker = BROKERS::PAPER;


			securities.clear();
			const std::vector<string> tickers = config[s]["tickers"].as<std::vector<string>>();
			for (auto s : tickers)
			{
				securities.push_back(s);
			}
		}
	}

	string CConfig::configDir()
	{
		//return boost::filesystem::current_path().string();
		return _config_dir;
	}

	string CConfig::logDir()
	{
		//boost::filesystem::path full_path = boost::filesystem::current_path() / "log";
		//return full_path.string();
		return _log_dir;
	}

	string CConfig::dataDir()
	{
		//boost::filesystem::path full_path = boost::filesystem::current_path() / "data";
		//return full_path.string();
		return _data_dir;
	}
}
