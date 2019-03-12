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

#include <Brokers/Sina/sinadatafeed.h>
#include <Common/Util/util.h>
#include <Common/Order/orderstatus.h>
#include <Common/Logger/logger.h>
#include <Common/Data/datamanager.h>
#include <Common/Order/ordermanager.h>

class price_;
using namespace std;
using boost::asio::ip::tcp;

namespace StarQuant
{
	extern std::atomic<bool> gShutdown;

	sinadatafeed::sinadatafeed() {
	}

	sinadatafeed::~sinadatafeed() {
	}

	// start http request thread
	bool sinadatafeed::connectToMarketDataFeed()
	{
		return true;
	}

	// stop http request thread
	void sinadatafeed::disconnectFromMarketDataFeed() {
	}

	// is http request thread running ?
	bool sinadatafeed::isConnectedToMarketDataFeed() const {
		return (!gShutdown);				// automatic disconnect when shutdown
	}

	void sinadatafeed::processMarketMessages() {
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

	void sinadatafeed::subscribeMarketData() {
		ostringstream os;
		//os << "/finance/info?q=" << "SPY,AAPL,VXX";
		for (auto &s : CConfig::instance().securities)
		{
			auto sv = stringsplit(s, ' ');
			if (sv[0].substr(0, 2) == "sh")
				os << sv[0] << ",";			// TODO: it ends with ","
		}
		//_path = "/list=" + os.str();  // hard code path for now
        
        pricemap["usr_spy"] = 0.0;
        pricemap["usr_aapl"] = 0.0;
        pricemap["usr_amzn"] = 0.0;
        pricemap["usr_tsla"] = 0.0;
        pricemap["usr_googl"] = 0.0;
        pricemap["usr_fb"] = 0.0;
        pricemap["usr_bidu"] = 0.0;
        pricemap["usr_baba"] = 0.0;
        pricemap["usr_gs"] = 0.0;
        pricemap["usr_jpm"] = 0.0;
        pricemap["sh600028"] = 0.0;
        pricemap["sh601857"] = 0.0;
        pricemap["sh600036"] = 0.0;
        pricemap["sh601668"] = 0.0;
        pricemap["sh601988"] = 0.0;
        pricemap["sh601166"] = 0.0;
        pricemap["sh601377"] = 0.0;
        pricemap["sh600958"] = 0.0;
        
		_mkstate = MK_REQREALTIMEDATAACK;
	}

	void sinadatafeed::unsubscribeMarketData(TickerId reqId) {
	}

	void sinadatafeed::subscribeMarketDepth() {
	}

	void sinadatafeed::unsubscribeMarketDepth(TickerId reqId) {
	}

	void sinadatafeed::subscribeRealTimeBars(TickerId id, const Security& security, int barSize, const string& whatToShow, bool useRTH) {

	}

	void sinadatafeed::unsubscribeRealTimeBars(TickerId tickerId) {

	}

	void sinadatafeed::requestContractDetails() {
	}

	void sinadatafeed::requestHistoricalData(string contract, string enddate, string duration, string barsize, string useRTH) {

	}

	void sinadatafeed::requestMarketDataAccountInformation(const string& account)
	{
		if (_mkstate <= MK_REQREALTIMEDATA)
			_mkstate = MK_REQREALTIMEDATA;
	}

	////////////////////////////////////////////////////// worker function ///////////////////////////////////////
	void sinadatafeed::Thread_GetQuoteLoop()
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

				//std::cout << res << std::endl;

				if (error != boost::asio::error::eof) { throw boost::system::system_error(error); }

				// split string
				std::vector<string> strs;
				boost::split(strs, res, boost::is_any_of("\n"));
				//cout << "* size of the vector: " << strs.size() << endl;
				for (size_t i = 0; i < strs.size(); i++) {
					if (strs[i].find("var") != std::string::npos)
					{
						std::size_t pos1 = strs[i].find("_str_");
						std::size_t pos2 = strs[i].find("=");
						std::string symbol = strs[i].substr(pos1 + 5, pos2 - pos1 - 5);

						std::vector<string> str2;
						boost::split(str2, strs[i], boost::is_any_of(","));
						//cout << "symbol = " << symbol << " price = " << price << endl;
                        
						Tick k;
						k.time_ = hmsf();
						k.datatype_ = DataType::DT_Trade;
                        
                        string price;
                        if (symbol.substr(0, 3) == "usr") {
                            price = str2[1];
                            k.fullsymbol_ = boost::to_upper_copy<std::string>(symbol.substr(4)) + " STK SMART";
                        }
                        else {
                            price = str2[3];
                            k.fullsymbol_ = symbol;
                        }
                    
                        double price_tmp = atof(price.c_str());
                        if (price_tmp == pricemap[symbol]) {
                            pricemap[symbol] = price_tmp - 0.01;
                            k.price_ = price_tmp - 0.01;
                        }
                        else {
                            pricemap[symbol] = price_tmp;
                            k.price_ = price_tmp;
                        }
                        
						k.size_ = 100;			// TODO: use actual size
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