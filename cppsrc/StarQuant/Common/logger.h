#ifndef _StarQuant_Common_Logger_H_
#define _StarQuant_Common_Logger_H_

#include <stdarg.h>
#include <stdio.h>
#include <time.h>
#include <mutex>

#include <log4cplus/logger.h>
#include <log4cplus/loggingmacros.h>

#define LOG_FATAL(sqLogger, content) LOG4CPLUS_FATAL(sqLogger->getLogger(), content)
#define LOG_ERROR(sqLogger, content) LOG4CPLUS_ERROR(sqLogger->getLogger(), content)
#define LOG_INFO(sqLogger, content) LOG4CPLUS_INFO(sqLogger->getLogger(), content)
#define LOG_DEBUG(sqLogger, content) LOG4CPLUS_DEBUG(sqLogger->getLogger(), content)

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

	class SQLogger 
	{
		protected:
    		log4cplus::Logger logger;
		protected:
			SQLogger() {};
			SQLogger(string name);

	public:

		inline log4cplus::Logger& getLogger(){
			return logger;
		}
		inline void fatal(const char* content){
			LOG4CPLUS_FATAL(logger, content);
		}
		inline void error(const char* content){
			LOG4CPLUS_ERROR(logger, content);
		}
		inline void info(const char* content){
			LOG4CPLUS_INFO(logger, content);
		}
		inline void debug(const char* content){
			LOG4CPLUS_DEBUG(logger, content);
		}

		static string getConfigFolder();

		// attention: return true if really configured.
		static bool doConfigure(string configureName);

		static std::shared_ptr<SQLogger> getLogger(string name);

	};
	


}
#endif
