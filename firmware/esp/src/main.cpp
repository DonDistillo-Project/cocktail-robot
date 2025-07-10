#include "Setup.hpp"
#include "esp_random.h"
#define size(x) (unsigned char)sizeof(x), x

void r(void *_)
{
    vTaskDelay(1000);

    const size_t steps = 10;
    while (1)
    {
        render_instruction(size("Dies\nIst\nEin\nTest\nLelelelsllel"));
        vTaskDelay(3000 / portTICK_PERIOD_MS);

        render_instruction(size("Test1234"));
        vTaskDelay(3000 / portTICK_PERIOD_MS);
        render_instruction(size("Hallo, das hier ist Test Nr. 3"));
        vTaskDelay(3000 / portTICK_PERIOD_MS);
        render_instruction(size("iojo123423423fsdfsdfijhiuhiuhiuhiojo123423423fsdfsdfijhiuhiuhiuhiojo123423423fsdfsdfijhiuhiuhiuh"));
        vTaskDelay(3000 / portTICK_PERIOD_MS);
        float x = (float)esp_random() / (float)UINT32_MAX * 100.0;
        for (float i = 0.0; i < x; i += x / steps)
        {
            render_scale(i, 0.8 * x);
            vTaskDelay(300);
        }
    }
}

void loop()
{
    render_recipe(size("Test\nRezept"));
    vTaskDelay(4000 / portTICK_PERIOD_MS);
    TaskHandle_t r_task;
    xTaskCreate(r, "Soos", SCREEN_RENDER_STACKSIZE, NULL, 50, &r_task);

    vTaskSuspend(NULL);
}