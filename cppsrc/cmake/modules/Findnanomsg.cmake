 ################################################################################

MESSAGE(STATUS "Looking for nanomsg...")

find_path(NANOMSG_INCLUDE_DIR NAMES nanomsg/nn.h
  HINTS ${NANOMSG_DIR}/include
  HINTS ${AlFa_DIR}/include
  HINTS ${SIMPATH}/include
  DOC   "Path to nanomsg include header files."
)

find_library(NANOMSG_LIBRARY_SHARED NAMES libnanomsg.dylib libnanomsg.so
  HINTS ${NANOMSG_DIR}/lib
  HINTS ${AlFa_DIR}/lib
  HINTS ${SIMPATH}/lib
  DOC   "Path to libnanomsg.dylib libnanomsg.so."
)

if(NANOMSG_INCLUDE_DIR AND NANOMSG_LIBRARY_SHARED)
  set(NANOMSG_FOUND true)
else(NANOMSG_INCLUDE_DIR AND NANOMSG_LIBRARY_SHARED)
  set(NANOMSG_FOUND false)
endif(NANOMSG_INCLUDE_DIR AND NANOMSG_LIBRARY_SHARED)

if(NANOMSG_FOUND)
  set(NANOMSG_LIBRARIES "${NANOMSG_LIBRARY_SHARED}")
  if(NOT NANOMSG_FIND_QUIETLY)
    message(STATUS "Looking for nanomsg... - found ${NANOMSG_LIBRARIES}")
  endif(NOT NANOMSG_FIND_QUIETLY)

  add_library(nanomsg SHARED IMPORTED)
  set_target_properties(nanomsg PROPERTIES
    IMPORTED_LOCATION ${NANOMSG_LIBRARY_SHARED}
    INTERFACE_INCLUDE_DIRECTORIES ${NANOMSG_INCLUDE_DIR}
  )
else(NANOMSG_FOUND)
  if(NOT NANOMSG_FIND_QUIETLY)
    if(NANOMSG_FIND_REQUIRED)
      message(FATAL_ERROR "Looking for nanomsg... - Not found")
    else(NANOMSG_FIND_REQUIRED)
      message(STATUS "Looking for nanomsg... - Not found")
    endif(NANOMSG_FIND_REQUIRED)
  endif(NOT NANOMSG_FIND_QUIETLY)
endif(NANOMSG_FOUND)

mark_as_advanced(NANOMSG_INCLUDE_DIR NANOMSG_LIBRARIES NANOMSG_LIBRARY_SHARED)
