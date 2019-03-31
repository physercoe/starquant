#ifndef _StarQuant_Data_BarInterval_H_
#define _StarQuant_Data_BarInterval_H_

namespace StarQuant {
	enum BarInterval {
		BI_CustomVol = -3,
		BI_CustomTicks = -2,
		BI_CustomTime = -1,
		BI_Second = 1,
		BI_Minute = 60,
		BI_FiveMin = 300,
		BI_FifteenMin = 900,
		BI_ThirtyMin = 1800,
		BI_Hour = 3600,
		BI_Day = 86400
	};
}

#endif