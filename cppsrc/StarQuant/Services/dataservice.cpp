#include <atomic>
#include <Services/dataservice.h>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/timeutil.h>
#include <Common/logger.h>
//#include <Common/Data/datatype.h>
#include <Data/datamanager.h>
#include <Data/tickwriter.h>
#include <Data/tickreader.h>


//#include <Strategy/strategyFactory.h>

using namespace std;

namespace StarQuant
{
	extern std::atomic<bool> gShutdown;
	atomic<uint64_t> MICRO_SERVICE_NUMBER(0);

	void DataBoardService() {
		try {
			std::unique_ptr<CMsgq> msgq_sub_;
			msgq_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERPUB_URL, false);
			while (!gShutdown) {
				string msg = msgq_sub_->recmsg(0);
				if (!msg.empty()) {

					vector<string> vs = stringsplit(msg, SERIALIZATION_SEPARATOR);
					//cout<<"Databoad rec msg size:"<<vs.size()<<endl;
					if ((MSG_TYPE)(atoi(vs[0].c_str())) == MSG_TYPE::MSG_TYPE_Trade)	// Always Tick; actual contents are determined by MSG_TYPE
					{
						Tick k;
						k.fullsymbol_ = vs[1];
						k.time_ = vs[2];					//atoi(vs[1].c_str());
						k.price_ = atof(vs[3].c_str());
						k.size_ = atoi(vs[4].c_str());
						k.depth_ = 1;

						if (DataManager::instance()._latestmarkets.find(k.fullsymbol_) != DataManager::instance()._latestmarkets.end()) {
							//cout<<"Databoard latest price:"<<k.price_<<" Datatype:"<<k.msgtype_<<endl;
							DataManager::instance().SetTickValue(k);
							// PRINT_TO_FILE("ERROR:[%s,%d][%s]%s.\n", __FILE__, __LINE__, __FUNCTION__, buf);
						}
						//cout<<"Databoard latest price:"<<k.fullsymbol_.length()<<DataManager::instance()._latestmarkets[k.fullsymbol_].price_<<endl;
					}
					else if ((MSG_TYPE)(atoi(vs[0].c_str())) == MSG_TYPE::MSG_TYPE_TICK_L1)		// Always Tick; actual contents are determined by MSG_TYPE
					{
						Tick_L1 k;
						k.fullsymbol_ = vs[1];
						k.time_ = vs[2];
						k.price_ = atof(vs[3].c_str());
						k.size_ = atoi(vs[4].c_str());
						k.depth_ = 1;
						k.bidprice_L1_ = atoi(vs[5].c_str());
						k.bidsize_L1_ = atoi(vs[6].c_str());
						k.askprice_L1_ = atoi(vs[7].c_str());
						k.asksize_L1_ = atoi(vs[8].c_str());
						k.open_interest = atoi(vs[9].c_str());
						k.open_ = atoi(vs[10].c_str());
						k.high_ = atoi(vs[11].c_str());
						k.low_ = atoi(vs[12].c_str());
						k.pre_close_ = atoi(vs[13].c_str());
						k.upper_limit_price_ = atoi(vs[14].c_str());
						k.lower_limit_price_ = atoi(vs[15].c_str());

						if (DataManager::instance()._latestmarkets.find(k.fullsymbol_) != DataManager::instance()._latestmarkets.end()) {
							DataManager::instance().SetTickValue(k);
							// PRINT_TO_FILE("ERROR:[%s,%d][%s]%s.\n", __FILE__, __LINE__, __FUNCTION__, buf);
						}
						
					}
					else if ((MSG_TYPE)(atoi(vs[0].c_str())) == MSG_TYPE::MSG_TYPE_TICK_L5)		// Always Tick; actual contents are determined by MSG_TYPE
					{
						Tick_L5 k;
						k.fullsymbol_ = vs[1];
						k.time_ = vs[2];
						k.price_ = atof(vs[3].c_str());
						k.size_ = atoi(vs[4].c_str());
						k.depth_ = 5;
						k.bidprice_L1_ = atoi(vs[5].c_str());
						k.bidsize_L1_ = atoi(vs[6].c_str());
						k.askprice_L1_ = atoi(vs[7].c_str());
						k.asksize_L1_ = atoi(vs[8].c_str());
						k.bidprice_L2_ = atoi(vs[9].c_str());
						k.bidsize_L2_ = atoi(vs[10].c_str());
						k.askprice_L2_ = atoi(vs[11].c_str());
						k.asksize_L2_ = atoi(vs[12].c_str());
						k.bidprice_L3_ = atoi(vs[13].c_str());
						k.bidsize_L3_ = atoi(vs[14].c_str());
						k.askprice_L3_ = atoi(vs[15].c_str());
						k.asksize_L3_ = atoi(vs[16].c_str());
						k.bidprice_L4_ = atoi(vs[17].c_str());
						k.bidsize_L4_ = atoi(vs[18].c_str());
						k.askprice_L4_ = atoi(vs[19].c_str());
						k.asksize_L4_ = atoi(vs[20].c_str());
						k.bidprice_L5_ = atoi(vs[21].c_str());
						k.bidsize_L5_ = atoi(vs[22].c_str());
						k.askprice_L5_ = atoi(vs[23].c_str());
						k.asksize_L5_ = atoi(vs[24].c_str());
						k.open_interest = atoi(vs[25].c_str());
						k.open_ = atoi(vs[26].c_str());
						k.high_ = atoi(vs[27].c_str());
						k.low_ = atoi(vs[28].c_str());
						k.pre_close_ = atoi(vs[29].c_str());
						k.upper_limit_price_ = atoi(vs[30].c_str());
						k.lower_limit_price_ = atoi(vs[31].c_str());
						if (DataManager::instance()._latestmarkets.find(k.fullsymbol_) != DataManager::instance()._latestmarkets.end()) {
							DataManager::instance().SetTickValue(k);
							// PRINT_TO_FILE("ERROR:[%s,%d][%s]%s.\n", __FILE__, __LINE__, __FUNCTION__, buf);
						}
					}
				}
				//TODO: adding trig event,sigal other thread to continue
			}
		}
		catch (exception& e) {
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]%s.\n", __FILE__, __LINE__, __FUNCTION__, e.what());
		}
		catch (...) {
		}
		PRINT_TO_FILE("INFO:[%s,%d][%s]disconnect from market data feed.\n", __FILE__, __LINE__, __FUNCTION__);
	}

	void BarAggregatorServcie() {
		// TODO: separate from DataBoardService
	}

	void TickRecordingService() {
		std::unique_ptr<CMsgq> msgq_sub_;
		msgq_sub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::SUB, CConfig::instance().SERVERPUB_URL, false);
		string ymdstr = ymd();
		string fname = CConfig::instance().dataDir() + "/marketdata-" + ymdstr + ".txt";
		FILE* fp = fopen(fname.c_str(), "a+");
		TickWriter fwriter;
		fwriter.fp = fp;
		char *buf = nullptr;
		if (fp) {
			while (!gShutdown) {
				string msg = msgq_sub_->recmsg(0);

				if (!msg.empty())
					fwriter.put(msg);
					//fwriter.insertdb(msg);
			}
		}
		//PRINT_TO_FILE("INFO:[%s,%d][%s]recording service stopped: %s\n", __FILE__, __LINE__, __FUNCTION__);
	}

	void TickReplayService(const std::string& filetoreplay,int tickinterval)
	{
		std::unique_ptr<CMsgq> msgq_pub_;
		msgq_pub_ = std::make_unique<CMsgqNanomsg>(MSGQ_PROTOCOL::PUB, CConfig::instance().MKT_DATA_PUBSUB_PORT);
		uint64_t curt = 0;
		uint64_t logt = 0;
		//vector<TimeAndMsg> lines = readreplayfile(filetoreplay);
		vector<string> lines = readreplayfile(filetoreplay);
		int i = 0, sz = lines.size();
		while (!gShutdown && i++ < sz) {
//			logt = lines[i].t;
//			curt = getMicroTime();
//			static uint64_t diff = curt - logt;      //89041208806
			// while (!gShutdown && (diff + logt > curt)) {
			// 	curt = getMicroTime();
			// }
//			string& msg = lines[i].msg;
			string& msg =lines[i];
			//cout<< "REPLAY data:"<<msg<<endl;
			msgq_pub_->sendmsg(msg);
			msleep(tickinterval);
		}
		msleep(2000);
		PRINT_TO_FILE("INFO:[%s,%d][%s]replay service stopped: %s\n", __FILE__, __LINE__, __FUNCTION__);
	}
}
