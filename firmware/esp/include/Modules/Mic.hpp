#pragma once
#define SETUP_MIC

#include "ModuleSettings.hpp"

#include <driver/i2s.h>

int16_t mic_buffer[MIC_DMA_BUF_LEN];

int SetupMic()
{
    int ret;
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = MIC_SR,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = MIC_DMA_BUF_COUNT,
        .dma_buf_len = MIC_DMA_BUF_LEN,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0,
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = MIC_I2S_SCK,
        .ws_io_num = MIC_I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = MIC_I2S_SD,
    };

    if ((ret = i2s_driver_install(MIC_I2S_NUM, &i2s_config, 0, NULL)) != ESP_OK)
    {
        return ret;
    }

    if ((ret = i2s_set_pin(MIC_I2S_NUM, &pin_config)) != ESP_OK)
    {
        return ret;
    }

    return 0;
}

size_t readMic(int16_t *buf = mic_buffer, size_t buf_size = sizeof(mic_buffer))
{
    size_t bytes_read;
    i2s_read(MIC_I2S_NUM, &buf, buf_size, &bytes_read, portMAX_DELAY);
    return bytes_read;
}
