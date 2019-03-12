#pragma once
#include "ContractCondition.h"

namespace IBOfficial {

	class TWSAPIDLLEXP VolumeCondition : public ContractCondition {
		friend OrderCondition;

		int m_volume;

	protected:
		VolumeCondition() { }

		virtual std::string valueToString() const;
		virtual void valueFromString(const std::string &v);

	public:
		static const OrderConditionType conditionType = OrderConditionType::Volume;

		int volume();
		void volume(int volume);
	};
}