#include "Setup.hpp"
#include "esp_random.h"
#define size(x) (unsigned char)sizeof(x), x

// void r(void *_)
// {
//     vTaskDelay(1000);

//     const size_t steps = 10;
//     while (1)
//     {
//         render_instruction(size("Dies\nIst\nEin\nTest\nLelelelsllel"));
//         vTaskDelay(3000 / portTICK_PERIOD_MS);

//         render_instruction(size("Test1234"));
//         vTaskDelay(3000 / portTICK_PERIOD_MS);
//         render_instruction(size("Hallo, das hier ist Test Nr. 3"));
//         vTaskDelay(3000 / portTICK_PERIOD_MS);
//         render_instruction(size("iojo123423423fsdfsdfijhiuhiuhiuhiojo123423423fsdfsdfijhiuhiuhiuhiojo123423423fsdfsdfijhiuhiuhiuh"));
//         vTaskDelay(3000 / portTICK_PERIOD_MS);
//         float x = (float)esp_random() / (float)UINT32_MAX * 100.0;
//         for (float i = 0.0; i < x; i += x / steps)
//         {
//             render_scale(i, 0.8 * x);
//             vTaskDelay(300);
//         }
//     }
// }

void loop()
{
    printf("Waiting for audio Stream\n");
    audioStreamAccept();
    printf("Audio stream socket connected\n");

    // render_success(size("Audio Stream Socket Connected"));

    printf("Waiting for control socket connection\n");
    ctrlSockAccept();
    printf("Control socket connected\n");

    // render_success(size("Control Socket Connected"));

    printf("Waiting for Tasks to finish\n");
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // vTaskDelete(ctrl_loop_handle);
    vTaskDelete(write_handle);
    vTaskDelete(read_handle);
}