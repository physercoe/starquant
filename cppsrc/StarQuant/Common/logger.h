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

#ifndef CPPSRC_STARQUANT_COMMON_LOGGER_H_
#define CPPSRC_STARQUANT_COMMON_LOGGER_H_

#include <Common/util.h>
#include <stdarg.h>
#include <stdio.h>
#include <time.h>
#include <log4cplus/logger.h>
#include <log4cplus/loggingmacros.h>
#include <string>
#include <memory>
#include <mutex>

#define LOG_FATAL(sqLogger, content) LOG4CPLUS_FATAL(sqLogger->getLogger(), content)
#define LOG_ERROR(sqLogger, content) LOG4CPLUS_ERROR(sqLogger->getLogger(), content)
#define LOG_INFO(sqLogger, content) LOG4CPLUS_INFO(sqLogger->getLogger(), content)
#define LOG_DEBUG(sqLogger, content) LOG4CPLUS_DEBUG(sqLogger->getLogger(), content)


using std::string;
using std::mutex;

namespace StarQuant {

#define PRINT_TO_FILE logger::instance().Printf2File
#define PRINT_TO__CONSOLE(...) do{\
printf("%s ",ymdhmsf().c_str());printf(__VA_ARGS__);\
}while (0)
#define PRINT_TO_FILE_AND_CONSOLE(...) do{\
logger::instance().Printf2File(__VA_ARGS__);\
printf("%s ",ymdhmsf().c_str());printf(__VA_ARGS__);\
}while (0)


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

class SQLogger {
 protected:
    log4cplus::Logger logger;
    SQLogger() {}
    explicit SQLogger(string name);

 public:
    inline log4cplus::Logger& getLogger() {
        return logger;
    }
    inline void fatal(const char* content) {
        LOG4CPLUS_FATAL(logger, content);
    }
    inline void error(const char* content) {
        LOG4CPLUS_ERROR(logger, content);
    }
    inline void info(const char* content) {
        LOG4CPLUS_INFO(logger, content);
    }
    inline void debug(const char* content) {
        LOG4CPLUS_DEBUG(logger, content);
    }

    static string getConfigFolder();

    // attention: return true if really configured.
    static bool doConfigure(string configureName);
    static std::shared_ptr<SQLogger> getLogger(string name);
};


}  // namespace StarQuant
#endif  // CPPSRC_STARQUANT_COMMON_LOGGER_H_
