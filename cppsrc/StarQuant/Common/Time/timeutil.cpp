#include <Common/Util/util.h>
#include <Common/Time/timeutil.h>
#include <Common/Logger/logger.h>
#include <Common/Util/util.h>
#include <boost/date_time.hpp>
#include <boost/date_time/local_time/local_time.hpp>
#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>
#include <chrono>
#include <thread>
#include <fstream>

using namespace boost::posix_time;
using namespace boost::local_time;
using namespace std;

namespace StarQuant {

	string ymd() {
		char buf[128] = { 0 };
		const size_t sz = sizeof("0000-00-00");
		{
			time_t timer;
			struct tm* tm_info;
			time(&timer);
			tm_info = localtime(&timer);
			strftime(buf, sz, DATE_FORMAT, tm_info);
		}
		return string(buf);
	}

	string ymdhms() {
		char buf[128] = { 0 };
		const size_t sz = sizeof("0000-00-00 00-00-00");
		{
			time_t timer;
			time(&timer);
			struct tm* tm_info = localtime(&timer);
			strftime(buf, sz, DATE_TIME_FORMAT, tm_info);
		}
		return string(buf);
	}

	string ymdhmsf() {
		std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
		std::chrono::system_clock::duration tp = now.time_since_epoch();
		tp -= std::chrono::duration_cast<std::chrono::seconds>(tp);
		time_t tt = std::chrono::system_clock::to_time_t(now);
		
		// tm t = *gmtime(&tt);
		 tm t = *localtime(&tt);
		
		char buf[64];
		std::sprintf(buf, "%04u-%02u-%02u %02u:%02u:%02u.%03u", t.tm_year + 1900,
			t.tm_mon + 1, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec,
			static_cast<unsigned>(tp / std::chrono::milliseconds(1)));

		return string(buf);
	}
	string ymdhmsf6() {
		std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
		std::chrono::system_clock::duration tp = now.time_since_epoch();
		tp -= std::chrono::duration_cast<std::chrono::seconds>(tp);
		time_t tt = std::chrono::system_clock::to_time_t(now);
		
		// tm t = *gmtime(&tt);
		 tm t = *localtime(&tt);
		
		char buf[64];
		std::sprintf(buf, "%04u-%02u-%02u %02u:%02u:%02u.%06u", t.tm_year + 1900,
			t.tm_mon + 1, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec,
			static_cast<unsigned>(tp / std::chrono::microseconds(1)));

		return string(buf);
	}




	string hmsf() {
		std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
		std::chrono::system_clock::duration tp = now.time_since_epoch();
		tp -= std::chrono::duration_cast<std::chrono::seconds>(tp);
		time_t tt = std::chrono::system_clock::to_time_t(now);

		// tm t = *gmtime(&tt);			// utc
		tm t = *localtime(&tt);

		char buf[64];
		std::sprintf(buf, "%02u:%02u:%02u.%03u", t.tm_hour, t.tm_min, t.tm_sec,
			static_cast<unsigned>(tp / std::chrono::milliseconds(1)));

		return string(buf);
	}

	int hmsf2inttime(string hmsf) {
		return std::stoi(hmsf.substr(0, 2)) * 10000 + std::stoi(hmsf.substr(3, 2)) * 100 + std::stoi(hmsf.substr(6, 2));
	}

	void msleep(uint64_t _ms) {
		if (_ms == 0) { return; }
		this_thread::sleep_for(chrono::milliseconds(_ms));
	}

	string nowMS() {
		char buf[128] = {};
#ifdef __linux__
		struct timespec ts = { 0,0 };
		struct tm tm = {};
		char timbuf[64] = {};
		clock_gettime(CLOCK_REALTIME, &ts);
		time_t tim = ts.tv_sec;
		localtime_r(&tim, &tm);
		strftime(timbuf, sizeof(timbuf), "%F %T", &tm);
		snprintf(buf, 128, "%s.%03d", timbuf, (int)(ts.tv_nsec / 1000000));
#else
		SYSTEMTIME SystemTime;
		GetLocalTime(&SystemTime);
		sprintf(buf, "%04u-%02u-%02u %02u:%02u:%02u.%03u",
			SystemTime.wYear, SystemTime.wMonth, SystemTime.wDay,
			SystemTime.wHour, SystemTime.wMinute, SystemTime.wSecond, SystemTime.wMilliseconds);
#endif
		return buf;
	}

	time_t ptime2time(ptime t) {
		static ptime epoch(boost::gregorian::date(1970, 1, 1));
		time_duration::sec_type x = (t - epoch).total_seconds() - 3600 * NYC_TZ_OFFSET;
		//hours(4).total_seconds() = 3600 * 4
		// ... check overflow here ...
		return time_t(x);
	}

	string ptime2str(const ptime& pt) {
		time_zone_ptr tz_cet(new boost::local_time::posix_time_zone(NYC_TZ_STR));
		local_date_time dt_with_zone(pt, tz_cet); //glocale::instance()._ny_tzone);
#if 1
		tm _t = to_tm(dt_with_zone);
		char buf[32] = { 0 };
		strftime(buf, 32, DATE_TIME_FORMAT, &_t);
		return buf;
#else
												  //using stringstream only for logging
		stringstream strm;
		strm.imbue(*glocale::instance()._s_loc);
		strm << dt_with_zone;
		//strm << pt;
		return strm.str();
#endif
	}


	//http://stackoverflow.com/questions/4461586/how-do-i-convert-boostposix-timeptime-to-time-t
	time_t str2time_t(const string& s) {
		ptime pt(time_from_string(s));
		return ptime2time(pt);
	}

	string time_t2str(time_t tt) {
		ptime pt = from_time_t(tt);
		// return ptime2str(pt);
		return to_simple_string(pt);
	}

	int tointdate() {
		time_t current_time;
		time(&current_time);
		return tointdate(current_time);
	}

	int tointtime() {
		time_t current_time;
		time(&current_time);
		return tointtime(current_time);
	}

	int tointdate(time_t time) {
		struct tm timeinfo;
		LOCALTIME_S(&timeinfo, &time);

		return ((timeinfo.tm_year + 1900) * 10000) + ((timeinfo.tm_mon + 1) * 100) + timeinfo.tm_mday;
	}

	int tointtime(time_t time) {
		//std::time_t rawtime;
		//std::tm* timeinfo;
		//char queryTime[80];
		//std::time(&rawtime);
		//timeinfo = std::localtime(&rawtime);
		//std::strftime(queryTime, 80, "%Y%m%d %H:%M:%S", timeinfo);
		struct tm timeinfo;
		LOCALTIME_S(&timeinfo, &time);

		return (timeinfo.tm_hour * 10000) + (timeinfo.tm_min * 100) + (timeinfo.tm_sec);
	}

	// convert to # of seconds
	int inttimetointtimespan(int time) {
		int s1 = time % 100;
		int m1 = ((time - s1) / 100) % 100;
		int h1 = (int)((time - (m1 * 100) - s1) / 10000);

		return h1 * 3600 + m1 * 60 + s1;
	}

	// # of seconds to int time
	int inttimespantointtime(int timespan) {
		int hour = timespan / 3600;
		int second = timespan % 3600;
		int minute = second / 60;
		second = second % 60;
		return (hour * 10000 + minute * 100 + second);
	}

	// adds inttime and int timespan (in seconds).  does not rollover 24hr periods.
	int inttimeadd(int firsttime, int timespaninseconds)
	{
		int s1 = firsttime % 100;
		int m1 = ((firsttime - s1) / 100) % 100;
		int h1 = (int)((firsttime - m1 * 100 - s1) / 10000);
		s1 += timespaninseconds;
		if (s1 >= 60)
		{
			m1 += (int)(s1 / 60);
			s1 = s1 % 60;
		}
		if (m1 >= 60)
		{
			h1 += (int)(m1 / 60);
			m1 = m1 % 60;
		}
		int sum = h1 * 10000 + m1 * 100 + s1;
		return sum;
	}

	int inttimediff(int firsttime, int latertime)
	{
		int span1 = inttimetointtimespan(firsttime);
		int span2 = inttimetointtimespan(latertime);
		return span2 - span1;
	}




	int64_t string2unixtimems(const string& s)
	{
		struct tm tm_;
		int64_t unixtimems;
		int year, month, day, hour, minute,second,millisec;
		sscanf(s.c_str(),"%d-%d-%d %d:%d:%d.%d", &year, &month, &day, &hour, &minute, &second,&millisec);
		tm_.tm_year  = year-1900;
		tm_.tm_mon   = month-1;
		tm_.tm_mday  = day;
		tm_.tm_hour  = hour;
		tm_.tm_min   = minute;
		tm_.tm_sec   = second;
		tm_.tm_isdst = 0;

		time_t t_ = mktime(&tm_);
		unixtimems = t_*1000+millisec;
		return unixtimems;


	}



 


}