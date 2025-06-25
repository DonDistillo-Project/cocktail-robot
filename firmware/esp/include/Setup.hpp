#pragma once

#include "Modules.hpp"

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
#ifdef SETUP_SCALE
    setupScale();
#endif
#ifdef SETUP_MIC
    SetupMic();
#endif
#ifdef SETUP_SPEAKER
    SetupSpeaker();
#endif
    #ifdef SETUP_AUDIO_STREAM
        SetupAudioStreams();
    #endif
}