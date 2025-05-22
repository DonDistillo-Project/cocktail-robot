#pragma once

#include <Arduino.h>
#include <exception>
#include <WString.h>

#define FS_REFORMAT_ON_FAIL true

#define WIFI_FS_DIR "/wifi/"
#define WIFI_SSID_FILE "/wifi/ssid"
#define WIFI_PASS_FILE "/wifi/pass"
#define WIFI_RETRY_TIMES 20
#define WIFI_RETRY_DELAY 1000

#define SERIAL_BAUD 9600
#define SERIAL_TIMEOUT 10000

class SetupError : public std::exception
{
protected:
    String mMessage;

public:
    SetupError(const char *msg) : mMessage(String(msg)) {}

    const char *what() const throw()
    {
        return mMessage.c_str();
    }
};