#include <Data/bar.h>
#include <Common/timeutil.h>

namespace StarQuant
{
	Bar::Bar() {
		interval_ = 300;         // 5 mins = 300s

		open_ = 0;
		high_ = 0;
		low_ = 0;
		close_ = 0;
		volume_ = 0;
		tradesinbar_ = 0;
	}

	Bar::Bar(const string& s) : fullsymbol_(s) {
		interval_ = 300;         // 5 mins = 300s

		open_ = 0;
		high_ = 0;
		low_ = 0;
		close_ = 0;
		volume_ = 0;
		tradesinbar_ = 0;
	}

	bool Bar::isValid()
	{
		return (high_ >= low_) && (open_ != 0) && (close_ != 0);
	}

	void Bar::setBarStartTime()
	{
		int time_target = barorderinaday_ * interval_;		// in seconds
		barstarttime_ = inttimespantointtime(time_target);
	}
}
