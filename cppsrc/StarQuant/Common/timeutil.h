#ifndef _StarQuant_Common_TimeUtil_H
#define _StarQuant_Common_TimeUtil_H

#include <chrono> //for msleep
#include <thread> //for msleep
#include <ctime>
#include <mutex>
#include <sstream>
#include <iterator>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/local_time/local_time_types.hpp>
#include <boost/date_time/local_time/local_time_io.hpp>

#include <Common/config.h>

using std::string;
using std::vector;
using std::pair;
using std::mutex;
using std::set;
using std::locale;
using boost::posix_time::ptime;

namespace StarQuant {
#ifdef __linux__
#define LOCALTIME_S(x,y) localtime_r(y,x)
#else
#define LOCALTIME_S(x,y) localtime_s(x,y)
#endif
#define DATE_FORMAT "%Y-%m-%d"
#define DATE_FORMAT_CLEAN  "%4d-%02d-%02d"
#define DATE_TIME_FORMAT "%Y-%m-%d %H:%M:%S"
#define DATE_TIME_FORMAT_CLEAN  "%4d-%02d-%02d %02d:%02d:%02d"

#define TIMEZONE_STRING(s) #s
#define NYC_TZ_OFFSET -04
#define NYC_TZ_STR "UTC" TIMEZONE_STRING(NYC_TZ_OFFSET) ":00:00"

	string ymd();
	string ymdhms();
	string ymdhmsf();
	string ymdhmsf6();
	string hmsf();
	int hmsf2inttime(string hmsf);

	void msleep(uint64_t _ms);
	string nowMS();

	string ptime2str(const ptime& pt);
	time_t str2time_t(const string& s);
	string time_t2str(time_t tt);
	time_t ptime2time(ptime t);

	int tointdate();
	int tointtime();
	int tointdate(time_t time);
	int tointtime(time_t time);
	int inttimetointtimespan(int time);							// convert to # of seconds
	int inttimespantointtime(int timespan);						// # of seconds to int time
	int inttimeadd(int firsttime, int timespaninseconds);		// in seconds
	int inttimediff(int firsttime, int latertime);				// in seconds
	int64_t string2unixtimems(const string& s);
}

#endif   // _StarQuant_Common_TimeUtil_H
