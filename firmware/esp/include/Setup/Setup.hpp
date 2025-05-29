#pragma once

#include <Arduino.h>
#include <exception>
#include <WString.h>

#define FS_REFORMAT_ON_FAIL true

#define WIFI_FS_DIR "/wifi/"
#define WIFI_SSID_FILE "/wifi/ssid"
#define WIFI_PASS_FILE "/wifi/pass"
#define WIFI_RETRY_TIMES 20
#define WIFI_RETRY_DELAY 1000

#define SERIAL_BAUD 9600
#define SERIAL_TIMEOUT 10000

#define SCALE_CLK_PIN 32
#define SCALE_DAT_PIN 33
#define SCALE_LIN_FAC 0.00253508
#define SCALE_START_OFFSET 8506971.577783272

#define MIC_I2S_SCK 26
#define MIC_I2S_WS 25
#define MIC_I2S_SD 22
#define MIC_SR 32000
#define MIC_DMA_BUF_COUNT 8
#define MIC_DMA_BUF_LEN 64

#define SPEAKER_I2S_SCK GPIO_NUM_13
#define SPEAKER_I2S_WS GPIO_NUM_15
#define SPEAKER_I2S_SD GPIO_NUM_8
#define SPEAKER_SR 48000
#define SPEAKER_DMA_BUF_COUNT 4
#define SPEAKER_DMA_BUF_LEN 1024

class SetupError : public std::exception
{
protected:
    String mMessage;

public:
    SetupError(const char *msg) : mMessage(String(msg)) {}

    const char *what() const throw()
    {
        return mMessage.c_str();
    }
};