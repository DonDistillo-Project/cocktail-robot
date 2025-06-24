#pragma once

#define SETUP_AUDIO_STREAM

#include "ModuleSettings.hpp"

#include "Modules/WiFi.hpp"
#include "Modules/Mic.hpp"
#include "Modules/Speaker.hpp"

#include "freertos/semphr.h"
#include "lwip/sockets.h"

static int audio_sock;
static bool audio_connected = false;

TaskHandle_t sock2speakerTask = NULL;
TaskHandle_t mic2sockTask = NULL;

void sock2speaker(void *client_socketp)
{
#ifdef SETUP_SERIAL
    Serial.printf("started write task \n");
#endif

#ifdef SETUP_SERIAL
    Serial.flush();
#endif
    size_t bytes_left = 0;
    size_t bytes_written = 0;

    int16_t speaker_buf[SPEAKER_DMA_BUF_LEN];

    size_t offset = 0;

    int client_socket = *((int *)(client_socketp));
    i2s_zero_dma_buffer(SPEAKER_I2S_NUM);
    while (audio_connected)
    {
        bytes_left = read(client_socket, speaker_buf, sizeof(speaker_buf));

        while (bytes_left % 2 != 0)
            bytes_left += read(client_socket, ((int8_t *)speaker_buf) + bytes_left, 1);

        if (bytes_left == 0)
        {
            audio_connected = false;
            printf("RECEIVED 0 BYTES\n");
            return;
        }

        offset = 0;
        while (bytes_left > 0)
        {
            i2s_write(SPEAKER_I2S_NUM, ((int8_t *)speaker_buf) + offset, bytes_left, &bytes_written, portMAX_DELAY);
            bytes_left -= bytes_written;
            offset += bytes_written;
        }
    }
}

void mic2sock(void *client_socketf)
{
#ifdef SETUP_SERIAL
    Serial.printf("started read task \n");
#endif

    size_t bytes_left = 0;
    size_t bytes_written = 0;

    int16_t buf[MIC_DMA_BUF_LEN];

    size_t offset = 0;

    int client_socket = *((int *)(client_socketf));

    while (audio_connected)
    {
        i2s_read(MIC_I2S_NUM, &buf, sizeof(buf), &bytes_left, portMAX_DELAY);

        offset = 0;
        while (bytes_left > 0)
        {
            bytes_written = write(client_socket, ((int8_t *)buf) + offset, bytes_left);
            if (bytes_written == 0)
            {
                audio_connected = false;
                printf("RECEIVED 0 BYTES\n");

                return;
            }
            bytes_left -= bytes_written;
            offset += bytes_written;
        }
    }
}

int audioStreamAccept()
{
    sockaddr client_addr;
    size_t client_addr_len;
    int client_socket;
    if ((client_socket = accept(audio_sock, (struct sockaddr *)&client_addr,
                                &client_addr_len)) < 0)
    {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    printf("connected\n");

    audio_connected = true;

    xTaskCreate(
        sock2speaker,
        "Sock2SpeakerTask",
        STREAMS_STACKSIZE,
        &client_socket,
        STREAMS_SPEAKER_PRIO,
        &sock2speakerTask);

    xTaskCreate(
        mic2sock,
        "Mic2SockTask",
        STREAMS_STACKSIZE,
        &client_socket,
        STREAMS_MIC_PRIO,
        &mic2sockTask);
    return 0;
}

int SetupAudioStreams()
{
    audio_sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = STREAMS_ADDR;
    addr.sin_port = htons(STREAMS_PORT);

    bind(audio_sock, (struct sockaddr *)&addr, sizeof(addr));
    listen(audio_sock, STREAMS_BACKLOG);

    return 0;
};
