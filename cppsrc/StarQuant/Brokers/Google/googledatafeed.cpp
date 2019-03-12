#include <boost/asio.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/assign/list_inserter.hpp>
#include <boost/date_time/gregorian/gregorian.hpp>

#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <sstream>
#include <mutex>

#include <Brokers/Google/googledatafeed.h>
#include <Common/Util/util.h>
#include <Common/Order/orderstatus.h>
#include <Common/Logger/logger.h>
#include <Common/Data/datamanager.h>
#include <Common/Order/ordermanager.h>

#include <rapidjson/document.h>



using namespace std;
using boost::asio::ip::tcp;

namespace StarQuant
{
	extern std::atomic<bool> gShutdown;

	googledatafeed::googledatafeed() {	
		//ptickthread = make_shared<thread>([this] { Thread_GetQuoteLoop(); });
	}

	googledatafeed::~googledatafeed() {
		/*if (ptickthread->joinable()) {
			ptickthread->join();
		}*/
	}

	// start http request thread
	bool googledatafeed::connectToMarketDataFeed()
	{
		return true;
	}

	// stop http request thread
	void googledatafeed::disconnectFromMarketDataFeed() {
	}

	// is http request thread running ?
	bool googledatafeed::isConnectedToMarketDataFeed() const {
		return (!gShutdown);				// automatic disconnect when shutdown
	}

	void googledatafeed::processMarketMessages() {
		if (!heatbeat(5)) {
			disconnectFromMarketDataFeed();
			return;
		}

		switch (_mkstate) {
		case MK_ACCOUNT:
			requestMarketDataAccountInformation(CConfig::instance().account);
			break;
		case MK_REQREALTIMEDATA:
			subscribeMarketData();
			break;
		case MK_REQREALTIMEDATAACK:
			Thread_GetQuoteLoop();
			break;
		}
	}

	void googledatafeed::subscribeMarketData() {
		ostringstream os;
		//os << "/finance/info?q=" << "SPY,AAPL,VXX";
		for (auto &s : CConfig::instance().securities)
		{
			auto sv = stringsplit(s, ' ');
			if (sv[0].substr(0, 2) == "sh")
				continue;
			
			os << sv[0] << ",";			// TODO: it ends with ","
		}
		_path = "/finance/info?q=" + os.str();

		_mkstate = MK_REQREALTIMEDATAACK;
	}

	void googledatafeed::unsubscribeMarketData(TickerId reqId) {
	}

	void googledatafeed::subscribeMarketDepth() {
	}

	void googledatafeed::unsubscribeMarketDepth(TickerId reqId) {
	}

	void googledatafeed::subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH) {

	}

	void googledatafeed::unsubscribeRealTimeBars(TickerId tickerId) {

	}

	void googledatafeed::requestContractDetails() {
	}

	void googledatafeed::requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH) {
	}

	void googledatafeed::requestMarketDataAccountInformation(const string& account)
	{
		if (_mkstate <= MK_REQREALTIMEDATA)
			_mkstate = MK_REQREALTIMEDATA;
	}

	////////////////////////////////////////////////////// worker function ///////////////////////////////////////
	void googledatafeed::Thread_GetQuoteLoop()
	{
		std::string res = "";

		while (!gShutdown) {
			try {
				boost::asio::io_service io_service;

				// Get a list of endpoints corresponding to the server name.
				tcp::resolver resolver(io_service);
				tcp::resolver::query query(_host, "http");
				tcp::resolver::iterator endpoint_iterator = resolver.resolve(query);
				tcp::resolver::iterator end;

				// Try each endpoint until we successfully establish a connection.
				tcp::socket socket(io_service);
				boost::system::error_code error = boost::asio::error::host_not_found;
				while (error && endpoint_iterator != end) {
					socket.close();
					socket.connect(*endpoint_iterator++, error);
				}

				if (error) { throw boost::system::system_error(error); }

				// Form the request. We specify the "Connection: close" header so that the server will close the socket 
				// after transmitting the response. This will allow us to treat all data up until the EOF as the content.
				boost::asio::streambuf request;
				std::ostream request_stream(&request);
				request_stream << "GET " << _path << " HTTP/1.0\r\n";
				request_stream << "Host: " << _host << "\r\n";
				request_stream << "Accept: */*\r\n";
				request_stream << "Connection: close\r\n\r\n";

				// Send the request.
				boost::asio::write(socket, request);

				// Read the response status line.
				boost::asio::streambuf response;
				boost::asio::read_until(socket, response, "\r\n");

				// Check that response is OK.
				std::istream response_stream(&response);

				std::string http_version;
				response_stream >> http_version;

				unsigned int status_code;
				response_stream >> status_code;

				std::string status_message;
				std::getline(response_stream, status_message);
				if (!response_stream || http_version.substr(0, 5) != "HTTP/") {
					std::cout << "Invalid response\n";
				}
				if (status_code != 200) {
					std::cout << "Response returned with status code " << status_code << "\n";
				}

				// Read the response headers, which are terminated by a blank line.
				boost::asio::read_until(socket, response, "\r\n\r\n");

				// Write whatever content we already have to output.
				if (response.size() > 0) {
					std::ostringstream oss;
					oss << &response;
					res = oss.str();
				}

				//std::cout << res << std::endl;

				// Read until EOF, writing data to output as we go.
				while (boost::asio::read(socket, response, boost::asio::transfer_at_least(1), error)) {
					//std::cout << &response; // don't want to print just return
					std::ostringstream oss;
					oss << &response;
					res += oss.str();
				}

				if (error != boost::asio::error::eof) { throw boost::system::system_error(error); }
				
				//std::size_t data_start_pos = res.find("//");
				//std::string data_all = res.substr(data_start_pos + 3);
				//std::cout << data_all << std::endl;

				// split string
				std::vector<string> strs;
				boost::split(strs, res, boost::is_any_of("}"));

				std::vector<string> strs2;
				for (string& s : strs)
				{
					boost::split(strs2, s, boost::is_any_of("{"));
					if (strs2.size() > 1) {
						rapidjson::Document d;
						d.Parse(("{"+strs2[1]+"}").c_str());

						rapidjson::Value& s = d["id"];
						Tick k;
						k.time_ = hmsf();
						s = d["t"];
						k.fullsymbol_ = s.GetString();
						k.fullsymbol_ = k.fullsymbol_ + " STK SMART";
						k.datatype_ = DataType::DT_Trade;
						s = d["l"];
						k.price_ = atof(s.GetString());
						k.size_ = 100;
						msgq_pub_->sendmsg(k.serialize());

						msleep(50);
					}		
				}
			}
			catch (std::exception& e) {
				std::cout << "Exception: " << e.what() << "\n";
			}

			msleep(1000);
		}
	}
}