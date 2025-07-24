#pragma once

#define SETUP_FS

#include "ModuleSettings.hpp"

#include <FS.h>
#include <LittleFS.h>

int setupFS(bool reformat_on_fail = FS_REFORMAT_ON_FAIL)
{
#ifdef SETUP_SERIAL
    Serial.println("Setting up LittleFS");
#endif
    if (!LittleFS.begin(reformat_on_fail))
    {
#ifdef SETUP_SERIAL
        Serial.println("Could not mount LittleFS; Flash reformatted");
#endif
        return -1;
    }
    return 0;
};
