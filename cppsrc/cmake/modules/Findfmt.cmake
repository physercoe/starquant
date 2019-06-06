# - Try to find fmt source lib
#
# Once done this will define
#  fmt_FOUND - System has args
#  fmt_INCLUDE_DIRS - The args include directories

include(FindPackageHandleStandardArgs)
# Find include files
find_path(
	FMT_INCLUDE_DIR
	NAMES fmt/format.h
	PATHS
		/usr/include
		/usr/local/include
		/sw/include
		/opt/local/include
	DOC "The directory where fmt/format.h resides")
# Find library files
find_library(
	FMT_LIBRARY
	NAMES fmt
	PATHS
		/usr/lib64
		/usr/lib
		/usr/lib/x86_64-linux-gnu
		/usr/local/lib64
		/usr/local/lib
		/sw/lib
		/opt/local/lib
	DOC "The fmt library")

# handle the QUIETLY and REQUIRED arguments and set LIBXML2_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args(fmt DEFAULT_MSG
        FMT_INCLUDE_DIR FMT_LIBRARY
        )
if (FMT_FOUND)
	message (STATUS "fmt_LIBRARIES = ${FMT_LIBRARY}")
	set(FMT_INCLUDE_DIRS ${FMT_INCLUDE_DIR} )
	set(FMT_LIBRARIES ${FMT_LIBRARY} )
	mark_as_advanced(FMT_INCLUDE_DIR FMT_LIBRARY)
endif()

