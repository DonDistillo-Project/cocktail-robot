#pragma once
#define SETUP_I2C

#include "ModuleSettings.hpp"

#include <Wire.h>

int setupI2C()
{
    Wire.begin(21, 22);

    uint8_t error, address;
    int device_count = 0;

#ifdef SETUP_SERIAL
    Serial.println("Starting I2C Scan");
#endif
    for (address = 1; address < 127; address++)
    {
        Wire.beginTransmission(address);
        error = Wire.endTransmission();

        if (error == 0)
        {
#ifdef SETUP_SERIAL
            Serial.print("I2C device found at address ");
            Serial.print(address);
            Serial.println(".");
#endif
        }
        if (error == 4)
        {
#ifdef SETUP_SERIAL
            Serial.print("I2C error at address ");
            Serial.print(address);
            Serial.println(".");
#endif
        }
#ifdef SETUP_SERIAL
        Serial.print(address);
        Serial.print(" - ");
        Serial.println(error);
#endif
    }
#ifdef SETUP_SERIAL
    Serial.println("Scan complete");
#endif
}
