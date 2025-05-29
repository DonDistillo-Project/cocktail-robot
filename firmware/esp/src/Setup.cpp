#include "Setup/Setup.hpp"

#include "Setup/Serial.hpp"
#include "Setup/FS.hpp"
#include "Setup/WiFi.hpp"

void setup()
{
#ifdef SETUP_SERIAL
    setupSerial();
#endif
#ifdef SETUP_FS
    setupFS();
#endif
#ifdef SETUP_WIFI
    setupWifi();
#endif
}