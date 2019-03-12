#include <Common/Util/util.h>
#include <Common/Data/barseries.h>
#include <Common/Data/datamanager.h>

namespace StarQuant
{
	// it seems that std::map<>::operator[] requires a default constructor
	BarSeries::BarSeries()
	{
	}

	BarSeries::BarSeries(string sym, int interval)
		: fullsymbol(sym), interval_(interval)
	{

	}

	BarSeries::~BarSeries()
	{

	}

	void BarSeries::resize(int len)
	{
		bars_.resize(len);
	}

	int BarSeries::getBarOrder(int time)
	{
		// get time elapsed to this point
		int elap = inttimetointtimespan(time);

		// get seconds per bar
		int secperbar = interval_;
		// get number of this bar in the day for this interval
		int bcount = (int)((double)elap / secperbar);
		return bcount;
	}

	bool BarSeries::newTick(const Tick& k)
	{
		if (fullsymbol == "")
			fullsymbol = k.fullsymbol_;

		if (fullsymbol != k.fullsymbol_)
			return false;			// invalid tick

		if ((k.datatype_ != DataType::DT_Trade) && ((k.datatype_ != DataType::DT_Full)))		// at this time only consier trade
			return false;

		int lastbarorder = 0;
		if (!bars_.empty())
			lastbarorder = bars_.back().barorderinaday_;
		if (bars_.empty() || (getBarOrder(hmsf2inttime(k.time_)) != lastbarorder))		// new bar
		{
			Bar newBar;
			newBar.fullsymbol_ = fullsymbol;

			newBar.open_ = k.price_;
			newBar.high_ = k.price_;
			newBar.low_ = k.price_;
			newBar.close_ = k.price_;
			newBar.avgprice_ = k.price_;
			newBar.volume_ = k.size_;

			newBar.tradesinbar_ = 1;
			newBar.interval_ = this->interval_;
			newBar.barorderinaday_ = getBarOrder(hmsf2inttime(k.time_));
			newBar.setBarStartTime();

			// broadcast
			if (!bars_.empty())
				DataManager::instance().msgq_pub_->sendmsg(bars_.back().serialize());

			bars_.push_back(newBar);
		}
		else      // consolidate to existing bar
		{
			bars_.back().tradesinbar_++;
			bars_.back().volume_ += k.size_;

			//if (bars_.back().open_ == 0) bars_.back().open_ = k.price_;
			//if (bars_.back().high_ == 0) bars_.back().high_ = k.price_;
			//if (bars_.back().low_ == 0) bars_.back().low_ = k.price_;
			if (k.price_ > bars_.back().high_) bars_.back().high_ = k.price_;
			if (k.price_ < bars_.back().low_) bars_.back().low_ = k.price_;
			bars_.back().close_ = k.price_;
		}
		return true;
	}

	bool BarSeries::addBar(const string& s)
	{
		vector<string> vs = stringsplit(s, ':');
		if (vs.size() != 6) {
			return false;
		}
		else {
			Bar newBar;
			newBar.fullsymbol_ = fullsymbol;

			newBar.open_ = atof(vs[0].c_str());
			newBar.high_ = atof(vs[1].c_str());
			newBar.low_ = atof(vs[2].c_str());
			newBar.close_ = atof(vs[3].c_str());
			newBar.avgprice_ = atof(vs[4].c_str());
			newBar.volume_ = atof(vs[5].c_str());

			newBar.tradesinbar_ = 0;
			newBar.barorderinaday_ = 0;
			newBar.barstarttime_ = 0;

			bars_.push_back(newBar);
		}
		return true;
	}

	string BarSeries::getLastUpdate(string name)
	{
		char buf[256] = {};
		snprintf(buf, 1024,
			"{\"%s\":{\"symbol\":\"%s\",\"w\":%.3f,\"v\":%u}}",
			name.c_str(), fullsymbol.c_str(), bars_.back().avgprice_, (uint32_t)bars_.back().volume_);
		return string(buf);
	}

	string BarSeries::serialize() const
	{
		// TODO: + operator is more efficient
		ostringstream os;
		os << CConfig::instance().bar_msg 
			<< SERIALIZATION_SEPARATOR << fullsymbol 
			<< SERIALIZATION_SEPARATOR << to_string(interval_);

		for (auto it = bars_.begin(); it != bars_.end(); ++it)
		{
			// t, o, h, l, c, v
			os << SERIALIZATION_SEPARATOR << to_string(it->barstarttime_)
				<< SERIALIZATION_SEPARATOR << to_string(it->open_)
				<< SERIALIZATION_SEPARATOR << to_string(it->high_)
				<< SERIALIZATION_SEPARATOR << to_string(it->low_)
				<< SERIALIZATION_SEPARATOR << to_string(it->close_)
				<< SERIALIZATION_SEPARATOR << to_string(it->volume_);
		}

		return os.str();
	}
}