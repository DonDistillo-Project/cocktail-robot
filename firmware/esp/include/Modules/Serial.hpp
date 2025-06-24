#pragma once
#define SETUP_SERIAL

#include "ModuleSettings.hpp"

#include <Arduino.h>

static int setupSerial()
{
    Serial.begin(SERIAL_BAUD);
    Serial.setTimeout(SERIAL_TIMEOUT);
    delay(250);
    Serial.println("Serial Setup Complete");

    return 0;
}
