#ifndef _StarQuant_Common_Util_H
#define _StarQuant_Common_Util_H

#include <sstream>
#include <iterator>
//#include <future>
#include <Common/config.h>
#include <Common/logger.h>
#include <Common/getRealTime.h>

using std::string;
using std::vector;
using std::pair;

namespace StarQuant {
	int check_gshutdown(bool force = true);

	vector<string> stringsplit(const string &s, char delim);
	bool startwith(const string&, const string&);
	MSG_TYPE MsgType(const string& str);
	bool endwith(const std::string &str, const std::string &suffix);
	string UTF8ToGBK(const std::string & strUTF8);
	string GBKToUTF8(const std::string & strGBK);

	
}

#endif   // _StarQuant_Common_Util_H
