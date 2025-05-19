#ifndef SETUP_FS
#define SETUP_FS

#include "FS.h"
#include <LittleFS.h>

void setupFS()
{
    Serial.println("Setting up LittleFS");

    if (!LittleFS.begin(true))
    {
        Serial.println("Could not mount LittleFS; Flash reformatted");
    }
};

#endif