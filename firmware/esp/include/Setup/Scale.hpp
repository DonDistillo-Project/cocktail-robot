#ifndef SETUP_SCALE
#define SETUP_SCALE
#include "Setup.hpp"

double scale_linear_factor = SCALE_LIN_FAC;
double scale_offset = SCALE_START_OFFSET;

double readScaleRaw()
{
    unsigned long count;
    unsigned char i;
    bool Flag = 0;

    digitalWrite(SCALE_DAT_PIN, HIGH);
    delayMicroseconds(1);

    digitalWrite(SCALE_CLK_PIN, LOW);
    delayMicroseconds(1);

    count = 0;
    while (digitalRead(SCALE_DAT_PIN))
        ;
    for (i = 0; i < 24; i++)
    {
        digitalWrite(SCALE_CLK_PIN, HIGH);
        delayMicroseconds(1);
        count = count << 1;
        digitalWrite(SCALE_CLK_PIN, LOW);
        delayMicroseconds(1);
        if (digitalRead(SCALE_DAT_PIN))
            count++;
    }
    digitalWrite(SCALE_CLK_PIN, HIGH);
    count ^= 0x800000;
    delayMicroseconds(1);
    digitalWrite(SCALE_CLK_PIN, LOW);
    delayMicroseconds(1);

    return static_cast<double>(count);
}

void setScaleOffset()
{
    scale_offset = (double)readScaleRaw();
}

double getScaleWeight()
{
    return scale_linear_factor * (readScaleRaw() - scale_offset);
}

void setupScale()
{
    pinMode(SCALE_CLK_PIN, OUTPUT);
    pinMode(SCALE_DAT_PIN, INPUT);
}
#endif