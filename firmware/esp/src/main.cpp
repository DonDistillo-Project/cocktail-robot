#include "Setup.hpp"

void loop()
{

    audioStreamAccept();

    while (true)
    {
        Serial.println("Running\n");
        sleep(10);
    }
}