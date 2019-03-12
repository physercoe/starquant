#include <Common/Security/position.h>
#include <Common/Util/util.h>
#include <Common/Util/calc.h>
#include <Common/Logger/logger.h>

namespace StarQuant {
	double Position::Adjust(Fill& fill) {
		PRINT_TO_FILE_AND_CONSOLE("INFO:[%s,%d][%s]Position is adjusted. ServerOrderId=%d, price=%.2f\n", 
			__FILE__, __LINE__, __FUNCTION__, fill.serverOrderId, fill.tradePrice);

		if (fill.fullSymbol != _fullsymbol)
		{
			PRINT_TO_FILE_AND_CONSOLE("ERROR:[%s,%d][%s]Position adjustment failed because adjustment symbol did not match position symbol\n", 
				__FILE__, __LINE__, __FUNCTION__);
			return 0.0;
		}

		double pl = 0;
		if (fill.tradeSize != 0)
		{
			bool oldside = (_size > 0);
			pl = Calc::ClosePL(*this, fill);
			if (_size == 0) _avgprice = fill.tradePrice; // if we're leaving flat just copy price
			else if (((fill.tradeSize > 0) && _size > 0) || ((fill.tradeSize < 0) && _size < 0)) // sides match, new average price
				_avgprice = ((_avgprice * _size) + (fill.tradePrice * fill.tradeSize)) / (fill.tradeSize + _size);
			_size += fill.tradeSize; // next, adjust the size
			if (oldside != (_size > 0)) _avgprice = fill.tradePrice; // if side doesn't change, so is the (remaining) average price. Otherwise flip to fill's average price
			if (_size == 0) _avgprice = 0; // if we're flat after adjusting, size price back to zero
			_closedpl += pl; // update running closed pl

			return pl;
		}

		_openpl = Calc::OpenPL(fill.tradePrice, _avgprice, _size);		// TODO: add multiplier

		return pl;
	}

	void Position::updatepnl(double mp) {
		_openpl = 0;			// calculate _openpl
	}

	void Position::report() {
		//PRINT_TO_FILE("INFO:[%s,%d][%s]Portfolio:nlc=%.4f,cashRemaining=%.4f,myInv=%.4f,lcc=%.4f,unrPNL=%.4f\n", 
		//	__FILE__, __LINE__, __FUNCTION__, nlc, cR, inve, lcc, uPNL);
	}
}