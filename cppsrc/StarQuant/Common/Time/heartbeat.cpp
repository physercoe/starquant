#include <Common/Time/heartbeat.h>
#include <Common/Util/util.h>

namespace StarQuant
{
	bool CHeartbeat::heatbeat(int interval) {
		time_t tmp = time(0);
		if (tmp > last_time && (tmp - last_time) % interval == 0) {
			last_time = tmp + 1;
			return true;
		}
		return true;
	}
}