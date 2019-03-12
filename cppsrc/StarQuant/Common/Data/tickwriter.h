#ifndef __StarQuant_Common_TickWriter_H__
#define __StarQuant_Common_TickWriter_H__

#include <condition_variable>
#include <mutex>
#include <Common/config.h>
#include <Common/Time/timeutil.h>
#include <Common/Time/getRealTime.h>

using std::mutex;

//////////////////////////////////////////////////////////////////////////
// tick recorder
//////////////////////////////////////////////////////////////////////////
namespace StarQuant
{
	struct TickWriter {
		int bufSize;
		FILE* fp = nullptr;
		int count = 0; //length of string in the buffer
		char* head = nullptr; // = raiibuf.get();

		TickWriter() {
			bufSize = 1024;
			head = new char[bufSize];
		}

		~TickWriter() {
			if (fp) {
				fwrite(head, sizeof(char), count, fp);
				fflush(fp);
				fclose(fp);
			}
			delete[] head;
		}

		void put(const string& _str) {
			if (!_str.empty()) {
				char tmp[512] = {};
				//sprintf(tmp, "%lu@%s\n", getMicroTime(), _str.c_str());
				sprintf(tmp, "%s @%s\n", ymdhmsf().c_str(), _str.c_str());
				uint32_t strsize = strlen(tmp); // + 1;
				uint32_t required_buffer_len = count + strsize;

				if (required_buffer_len > bufSize) {
					size_t r = fwrite(head, sizeof(char), count, fp);
					//printf("write files\n");
					if (r == count) {
						memcpy(head, tmp, strsize * sizeof(char));
						count = strsize;
						fflush(fp);
						return;
					}
					else {
						//error
						//http://www.cplusplus.com/reference/cstdio/fwrite/
					}
				}
				memcpy(head + count, tmp, strsize * sizeof(char));
				count = required_buffer_len;
			}
		}
	};
}

#endif
