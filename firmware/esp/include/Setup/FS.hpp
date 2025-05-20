#ifndef SETUP_FS
#define SETUP_FS

#include <FS.h>
#include <LittleFS.h>

void setupFS()
{
#ifdef SETUP_SERIAL
    Serial.println("Setting up LittleFS");
#endif
    if (!LittleFS.begin(true))
    {
#ifdef SETUP_SERIAL
        Serial.println("Could not mount LittleFS; Flash reformatted");
#endif
    }
};

#endif