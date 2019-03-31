#include <Common/heartbeat.h>
#include <Common/util.h>

namespace StarQuant
{
	bool CHeartbeat::heartbeat(int interval) {
		time_t tmp = time(0);
		if (tmp > last_time && (tmp - last_time) % interval == 0) {
			last_time = tmp + 1;
			return true;
		}
		return true;
	}
}