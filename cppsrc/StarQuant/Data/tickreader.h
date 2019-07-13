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

#ifndef CPPSRC_STARQUANT_DATA_TICKREADER_H_
#define CPPSRC_STARQUANT_DATA_TICKREADER_H_

#include <Common/util.h>
#include <condition_variable>
#include <mutex>
#include <string>
#include <vector>


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
                string tam = tmp[1];
                tam.erase(0, 1);
                lines.push_back(tam);
            }
        }
    }
    return lines;
}






}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_DATA_TICKREADER_H_
