#ifndef __StarQuant_Data_TickReader_H__
#define __StarQuant_Data_TickReader_H__

#include <condition_variable>
#include <mutex>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/timeutil.h>
#include <Common/getRealTime.h>

using std::mutex;

//////////////////////////////////////////////////////////////////////////
// tick reader
//////////////////////////////////////////////////////////////////////////
namespace StarQuant
{
	struct TimeAndMsg {
		uint64_t t;
		string msg;
	};

	// vector<TimeAndMsg> readreplayfile(const string& filetoreplay) {
	// 	ifstream f(filetoreplay);
	// 	vector<TimeAndMsg> lines;
	// 	string x;
	// 	while (f.is_open() && f.good()) {
	// 		getline(f, x);
	// 		if (!x.empty()) {
	// 			vector<string> tmp = stringsplit(x, '@');
	// 			if (tmp.size() == 2) {
	// 				TimeAndMsg tam = { (uint64_t)atoll(tmp[0].c_str()), tmp[1] };
	// 				lines.push_back(tam);
	// 			}
	// 		}
	// 	}
	// 	return lines;
	// }
	vector<string> readreplayfile(const string& filetoreplay) {
		ifstream f(filetoreplay);
		vector<string> lines;
		string x;
		while (f.is_open() && f.good()) {
			getline(f, x);
			if (!x.empty()) {
				vector<string> tmp = stringsplit(x, '@');
				if (tmp.size() == 2) {
					string tam = tmp[1] ;
					tam.erase(0,1);
					lines.push_back(tam);
				}
			}
		}
		return lines;
	}






}

#endif
