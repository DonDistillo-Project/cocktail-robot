#ifndef SETUP_SERIAL
#define SETUP_SERIAL

#include "Setup.hpp"

void setupSerial(unsigned long baud = SERIAL_BAUD, unsigned long timeout = SERIAL_TIMEOUT)
{
    Serial.begin(baud);
    Serial.setTimeout(timeout);
    delay(250);
    Serial.println("Serial Setup Complete");
}
#endif