#ifndef _StarQuant_Services_DataService_H_
#define _StarQuant_Services_DataService_H_

#include <memory>
#include <Common/config.h>
#include <Common/Data/marketdatafeed.h>

namespace StarQuant
{

	void MarketDataService(std::shared_ptr<marketdatafeed>, int);
	void DataBoardService();
	void BarAggregatorServcie();
	void TickRecordingService();
	void TickReplayService(const std::string& filetoreplay,int tickinterval=0);
}

#endif
