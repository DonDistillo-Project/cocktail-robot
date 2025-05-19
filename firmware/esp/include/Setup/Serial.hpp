#ifndef SETUP_SERIAL
#define SETUP_SERIAL

#include <Arduino.h>

void setupSerial(unsigned long baud = 9600, unsigned long timeout = 10000)
{
    Serial.begin(baud);
    Serial.setTimeout(timeout);
    Serial.println("Serial Setup Complete");
}
#endif