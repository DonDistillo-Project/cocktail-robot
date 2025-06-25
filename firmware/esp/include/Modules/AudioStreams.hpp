#pragma once

#define SETUP_AUDIO_STREAM

#include "ModuleSettings.hpp"

#include "Modules/WiFi.hpp"

#include "freertos/semphr.h"
#include "lwip/sockets.h"

static int audio_sock;

TaskHandle_t write_handle = NULL;
TaskHandle_t read_handle = NULL;
TaskHandle_t main_task = NULL;

void sock2speaker(void *client_socketp)
{
    Serial.printf("started write task \n");

    Serial.flush(); // ACHTUNG: LOAD BEARING FLUSH ???

    ssize_t bytes_left = 0;
    size_t bytes_written = 0;

    int16_t speaker_buf[SPEAKER_DMA_BUF_LEN];

    size_t offset = 0;

    int client_socket = *((int *)(client_socketp));

    while (1)
    {
        bytes_left = read(client_socket, speaker_buf, sizeof(speaker_buf));
        if (bytes_left <= 0)
        {
            printf("Read failed: %i - Connection closed \n", bytes_left);
            i2s_zero_dma_buffer(SPEAKER_I2S_NUM);
            xTaskNotifyGive(main_task);

            vTaskDelete(xTaskGetCurrentTaskHandle());

            return;
        }
        while (bytes_left % 2 != 0)
            bytes_left += read(client_socket, ((int8_t *)speaker_buf) + bytes_left, 1);
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
    Serial.printf("started read task \n");
    Serial.flush();

    size_t bytes_left = 0;
    ssize_t bytes_written = 0;

    int16_t buf[MIC_DMA_BUF_LEN];

    size_t offset = 0;

    int client_socket = *((int *)(client_socketf));

    while (1)
    {
        i2s_read(MIC_I2S_NUM, &buf, sizeof(buf), &bytes_left, portMAX_DELAY);

        size_t offset = 0;
        while (bytes_left > 0)
        {
            bytes_written = write(client_socket, ((int8_t *)buf) + offset, bytes_left);
            if (bytes_written <= 0)
            {
                printf("Write failed: %i - Connection closed \n", bytes_written);
                i2s_zero_dma_buffer(SPEAKER_I2S_NUM);
                xTaskNotifyGive(main_task);

                vTaskDelete(xTaskGetCurrentTaskHandle());

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

    xTaskCreate(
        sock2speaker,
        "sock2speaker",
        STREAMS_STACKSIZE,
        (void *)(&client_socket),
        STREAMS_SPEAKER_PRIO,
        &write_handle);

    xTaskCreate(
        mic2sock,
        "mic2sock",
        STREAMS_STACKSIZE,
        &client_socket,
        STREAMS_MIC_PRIO,
        &read_handle);

    main_task = xTaskGetCurrentTaskHandle();

    return 0;
}

int audioStreamWait()
{
    printf("Waiting for Tasks to finish\n");
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    printf("Tasks finished\n");
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
