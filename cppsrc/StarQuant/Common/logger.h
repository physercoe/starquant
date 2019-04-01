#ifndef _StarQuant_Common_Logger_H_
#define _StarQuant_Common_Logger_H_

#include <stdarg.h>
#include <stdio.h>
#include <time.h>
#include <mutex>


using std::string;
using std::mutex;

namespace StarQuant
{
	class logger {
		static logger* pinstance_;
		static mutex instancelock_;

		FILE* logfile = nullptr;
		logger();
		~logger();

	public:
		static logger& instance();

		void Initialize();

		void Printf2File(const char *format, ...);
	};
}
#endif
