/*****************************************************************************
 * Copyright [2019] 
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *****************************************************************************/
#ifndef CPPSRC_STARQUANT_COMMON_UTIL_H_
#define CPPSRC_STARQUANT_COMMON_UTIL_H_

#include <inttypes.h>
#include <sstream>
#include <iterator>
#include <atomic>
#include <chrono>  // for msleep
#include <thread>  // for msleep
#include <ctime>
#include <mutex>
#include <set>
#include <vector>
#include <string>
#include <boost/date_time/posix_time/ptime.hpp>
#include <boost/date_time/local_time/local_time_types.hpp>
#include <boost/date_time/local_time/local_time_io.hpp>

using std::string;
using std::vector;
using std::pair;
using std::mutex;
using std::set;
using std::locale;
using boost::posix_time::ptime;


namespace StarQuant {
// macros

#define PRINT_SHUTDOWN_MESSAGE \
printf("\n Thank you for using Star Quant. Goodbye! \n");

#if defined(_WIN32) || defined(_WIN64)
#include <Windows.h>

#elif defined(__unix__) || defined(__unix) || defined(unix) || (defined(__APPLE__) && defined(__MACH__))
#include <unistd.h>  /* POSIX flags */
#include <time.h>  /* clock_gettime(), time() */
#include <sys/time.h>  /* gethrtime(), gettimeofday() */

#if defined(__MACH__) && defined(__APPLE__)
#include <mach/mach.h>
#include <mach/mach_time.h>
#endif

#else
#error "Unable to define getRealTime( ) for an unknown OS."
#endif

#define __MILLI_MULTIPLE__ 1000
#define __MICRO_MULTIPLE__ 1000000
#define __NANOO_MULTIPLE__ 1000000000



#ifdef __linux__
#define LOCALTIME_S(x, y) localtime_r(y, x)
#else
#define LOCALTIME_S(x, y) localtime_s(x, y)
#endif
#define DATE_FORMAT "%Y-%m-%d"
#define DATE_FORMAT_COMPACT "%Y%m%d"
#define DATE_FORMAT_CLEAN  "%4d-%02d-%02d"
#define DATE_TIME_FORMAT "%Y-%m-%d %H:%M:%S"
#define DATE_TIME_FORMAT_CLEAN  "%4d-%02d-%02d %02d:%02d:%02d"

#define TIMEZONE_STRING(s) #s
#define NYC_TZ_OFFSET -04
#define NYC_TZ_STR "UTC" TIMEZONE_STRING(NYC_TZ_OFFSET) ":00:00"


#define EPSILON (1e-6)
#define DOUBLEMAX (1e16)  // 一亿亿, 2018年A股总市值不到50万亿



// console ,control related
    // std::atomic<bool>* setconsolecontrolhandler(void);
    // int32_t check_gshutdown(bool force = true);

// except signal
#include <setjmp.h>
#include <string.h>

struct Except_frame {
    jmp_buf env;
    int32_t flag;
    void clear() {
        flag = 0;
        bzero(env, sizeof(env));
    }
    bool isDef() {
        return flag;
    }
    Except_frame() {
    clear();
    }
};
void errorDump();
void recvSignal(int32_t sig);

void ConsoleControlHandler(int32_t sig);


// string related

vector<string> stringsplit(const string &s, char delim);
bool startwith(const string&, const string&);
bool endwith(const std::string &str, const std::string &suffix);
string extractExchangeID(const std::string& fullsym);
uint16_t extractPort(const std::string& address);
string extractIp(const std::string& address);
string UTF8ToGBK(const std::string & strUTF8);
string GBKToUTF8(const std::string & strGBK);

// numerical
double rounded(double x, int32_t n = 3);

inline bool is_greater(double x, double y) {
    return std::isgreater(x - y, EPSILON);
}

inline bool is_less(double x, double y) {
    return std::isless(x - y, EPSILON * -1);
}

inline bool is_equal(double x, double y) {
    return std::abs(x - y) <= EPSILON * std::abs(x);
}

inline bool is_greater_equal(double x, double y) {
    return is_greater(x, y) || is_equal(x, y);
}

inline bool is_less_equal(double x, double y) {
    return is_less(x, y) || is_equal(x, y);
}

inline bool is_zero(double x) {
    return is_equal(x, 0.0);
}

inline bool is_too_large(double x) {
    return is_greater(x, DOUBLEMAX);
}


// time related

uint64_t getMicroTime();
int32_t getMilliSeconds();
string ymd();
string ymdcompact();
string ymdhms();
string ymdhmsf();
string ymdhmsf6();
string hmsf();
int32_t hmsf2inttime(string hmsf);

void msleep(uint64_t _ms);
string nowMS();

string ptime2str(const ptime& pt);
time_t str2time_t(const string& s);
string time_t2str(time_t tt);
time_t ptime2time(ptime t);

int32_t tointdate();
int32_t tointtime();
int32_t tointdate(time_t time);
int32_t tointtime(time_t time);
int32_t inttimetointtimespan(int32_t time);  // convert to # of seconds
int32_t inttimespantointtime(int32_t timespan);  // # of seconds to int32_t time
int32_t inttimeadd(int32_t firsttime, int32_t timespaninseconds);  // in seconds
int32_t inttimediff(int32_t firsttime, int32_t latertime);  // in seconds
int64_t string2unixtimems(const string& s);


}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_COMMON_UTIL_H_
