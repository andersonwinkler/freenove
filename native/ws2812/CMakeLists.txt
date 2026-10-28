# Freenove WS2812 shared library — sources vendored in this directory (see ORIGIN.txt).
# Links against the APT libpio package; installs under CMAKE_INSTALL_PREFIX
# (setup uses /opt/freenove/tower-cooler).

cmake_minimum_required(VERSION 3.10...3.27)
project(freenove_ws2812 C)

find_library(PIO_LIBRARY NAMES pio REQUIRED)
find_path(PIO_INCLUDE_DIR
    NAMES piolib.h pico/stdlib.h
    PATHS /usr/include/piolib
    REQUIRED)

add_library(freenove_ws2812_lib SHARED freenove_ws2812.c)
target_include_directories(freenove_ws2812_lib
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${PIO_INCLUDE_DIR})
target_link_libraries(freenove_ws2812_lib PRIVATE ${PIO_LIBRARY})

install(TARGETS freenove_ws2812_lib LIBRARY DESTINATION lib)
