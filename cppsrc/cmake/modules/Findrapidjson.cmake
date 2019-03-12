foreach(opt RAPIDJSON_INCLUDEDIR RAPIDJSON_USE_SSE2 RAPIDJSON_USE_SSE42)
  if(${opt} AND DEFINED ENV{${opt}} AND NOT ${opt} STREQUAL "$ENV{${opt}}")
    message(WARNING "Conflicting ${opt} values: ignoring environment variable and using CMake cache entry.")
  elseif(DEFINED ENV{${opt}} AND NOT ${opt})
    set(${opt} "$ENV{${opt}}")
  endif()
endforeach()

find_path(
  RAPIDJSON_INCLUDE_DIRS
  NAMES rapidjson/rapidjson.h
  PATHS ${RAPIDJSON_INCLUDEDIR}
  DOC "Include directory for the rapidjson library."
)

mark_as_advanced(RAPIDJSON_INCLUDE_DIRS)

if(RAPIDJSON_INCLUDE_DIRS)
  set(RAPIDJSON_FOUND TRUE)
endif()

mark_as_advanced(RAPIDJSON_FOUND)

if(RAPIDJSON_USE_SSE42)
  set(RAPIDJSON_CXX_FLAGS "-DRAPIDJSON_SSE42")
  if(MSVC)
    set(RAPIDJSON_CXX_FLAGS "${RAPIDJSON_CXX_FLAGS} /arch:SSE4.2")
  else()
    set(RAPIDJSON_CXX_FLAGS "${RAPIDJSON_CXX_FLAGS} -msse4.2")
  endif()
else()
  if(RAPIDJSON_USE_SSE2)
    set(RAPIDJSON_CXX_FLAGS "-DRAPIDJSON_SSE2")
    if(MSVC)
      set(RAPIDJSON_CXX_FLAGS "${RAPIDJSON_CXX_FLAGS} /arch:SSE2")
    else()
      set(RAPIDJSON_CXX_FLAGS "${RAPIDJSON_CXX_FLAGS} -msse2")
    endif()
  endif()
endif()

mark_as_advanced(RAPIDJSON_CXX_FLAGS)

if(RAPIDJSON_FOUND)
  if(NOT rapidjson_FIND_QUIETLY)
    message(STATUS "Found rapidjson header files in ${RAPIDJSON_INCLUDE_DIRS}")
    if(DEFINED RAPIDJSON_CXX_FLAGS)
      message(STATUS "Found rapidjson C++ extra compilation flags: ${RAPIDJSON_CXX_FLAGS}")
    endif()
  endif()
elseif(rapidjson_FIND_REQUIRED)
    message(FATAL_ERROR "Could not find rapidjson")
else()
  message(STATUS "Optional package rapidjson was not found")
endif()
