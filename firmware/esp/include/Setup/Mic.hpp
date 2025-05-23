#ifndef SETUP_MIC
#define SETUP_MIC

#define MIC_I2S_NUM I2S_NUM_0

#include "Setup.hpp"

#include <driver/i2s.h>

int32_t mic_buffer[64];

void SetupMic()
{
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = MIC_SR,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
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

    i2s_driver_install(MIC_I2S_NUM, &i2s_config, 0, NULL);
    i2s_set_pin(MIC_I2S_NUM, &pin_config);
}

size_t readMic(int32_t *buf = mic_buffer, size_t buf_size = sizeof(mic_buffer))
{
    size_t bytes_read;
    i2s_read(MIC_I2S_NUM, &mic_buffer, sizeof(mic_buffer), &bytes_read, portMAX_DELAY);
    return bytes_read;
}

#endif