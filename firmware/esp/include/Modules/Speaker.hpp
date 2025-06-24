#pragma once
#define SETUP_SPEAKER

#include "ModuleSettings.hpp"

#include <driver/i2s.h>

int16_t speaker_buffer[SPEAKER_DMA_BUF_LEN];

int SetupSpeaker()
{
    int ret;
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = SPEAKER_SR,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = (i2s_comm_format_t)(I2S_COMM_FORMAT_STAND_I2S),
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = SPEAKER_DMA_BUF_COUNT,
        .dma_buf_len = SPEAKER_DMA_BUF_LEN};

    i2s_pin_config_t pin_config = {
        .bck_io_num = GPIO_NUM_13,
        .ws_io_num = GPIO_NUM_15,
        .data_out_num = GPIO_NUM_8,
        .data_in_num = -1};

    if ((ret = i2s_driver_install(SPEAKER_I2S_NUM, &i2s_config, 0, NULL)) != ESP_OK)
    {
        return ret;
    }
    if ((ret = i2s_set_pin(SPEAKER_I2S_NUM, &pin_config)) != ESP_OK)
    {
        return ret;
    }
    if ((ret = i2s_zero_dma_buffer(SPEAKER_I2S_NUM)) != ESP_OK)
    {
        return ret;
    };

    return 0;
}

size_t writeSpeaker(int16_t *buf = speaker_buffer, size_t buf_size = sizeof(speaker_buffer))
{
    size_t bytes_written;
    i2s_write(SPEAKER_I2S_NUM, &buf, buf_size, &bytes_written, portMAX_DELAY);
    return bytes_written;
}
