include_directories(${StarQuantCpp_SOURCE_DIR}/StarQuant)
set(StarQuantCppSrc
  ./Common/msgq.cpp
  ./Common/consolecontrolhandler.cpp
  ./Common/timeutil.cpp
  ./Common/getRealTime.cpp
  ./Common/heartbeat.cpp
  ./Common/logger.cpp
  ./Common/config.cpp
  ./Common/util.cpp
  ./Data/datamanager.cpp
  ./Data/tick.cpp
  ./Data/barseries.cpp
  ./Data/bar.cpp
  ./Trade/calc.cpp
  ./Trade/marginmanager.cpp
  ./Trade/riskmanager.cpp
  ./Trade/ordermanager.cpp
  ./Trade/orderstatus.cpp
  ./Trade/portfoliomanager.cpp
  ./Trade/position.cpp
  ./Engine/IEngine.cpp
  ./Engine/CtpMDEngine.cpp
  ./Engine/CtpTDEngine.cpp
  ./Engine/TapMDEngine.cpp
  ./Engine/TapTDEngine.cpp
  ./Services/dataservice.cpp
  ./Services/starquant_.cpp
  ./Services/tradingengine.cpp
   )

add_library(starquant SHARED ${StarQuantCppSrc})
set_target_properties(starquant  PROPERTIES COMPILE_FLAGS "-fPIC")
target_link_libraries(starquant  ${Boost_LIBRARIES} ${PYTHON_LIBRARY} ${MONGOC_LIBRARIES} yaml-cpp LinuxDataCollect thosttraderapi thostmduserapi TapQuoteAPI TapTradeAPI  nanomsg pthread dl util m)
set(SQSERVER_SRC  ./Services/sqserver.cpp )
add_executable(sqserver ${SQSERVER_SRC})
TARGET_LINK_LIBRARIES(sqserver starquant)