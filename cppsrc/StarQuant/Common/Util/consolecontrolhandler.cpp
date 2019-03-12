#include <Common/Util/util.h>
#include <Common/Util/consolecontrolhandler.h>

namespace StarQuant
{
	std::atomic<bool> gShutdown{ false };

#if defined(_WIN64) || defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
	BOOL CtrlHandler(DWORD fdwCtrlType) {
		switch (fdwCtrlType) {
			case CTRL_C_EVENT:
			case CTRL_CLOSE_EVENT:
				PRINT_SHUTDOWN_MESSAGE;
				gShutdown = true;
				return(TRUE);

			case CTRL_BREAK_EVENT:
			case CTRL_LOGOFF_EVENT:
			case CTRL_SHUTDOWN_EVENT:
				PRINT_SHUTDOWN_MESSAGE;
				gShutdown = true;
				return FALSE;

			default:
				return FALSE;
		}
	}

	std::atomic<bool>* setconsolecontrolhandler(void) {
		bool b = SetConsoleCtrlHandler((PHANDLER_ROUTINE)CtrlHandler, TRUE);
		if (!b) {
			printf("\nERROR: Could not set control handler");
		}
		return &gShutdown;
	}

#elif defined(__linux__)
#include <signal.h>
	void ConsoleControlHandler(int sig) {
		gShutdown = true;
		PRINT_SHUTDOWN_MESSAGE;
	}

	std::atomic<bool>* setconsolecontrolhandler(void) {
		signal(SIGINT, ConsoleControlHandler);
		signal(SIGPWR, ConsoleControlHandler);
		return &gShutdown;
	}

#endif
}