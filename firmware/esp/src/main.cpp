#include "Setup/Setup.hpp"

#include "Setup/Serial.hpp"
#include "Setup/FS.hpp"
#include "Setup/WiFi.hpp"
// #include "Setup/Scale.hpp"
#include "Setup/Mic.hpp"
#include "Setup/Speaker.hpp"

#include <lwip/sockets.h>
static int audio_sock;
bool writing;
bool reading;
TaskHandle_t write_handle = NULL;
TaskHandle_t read_handle = NULL;

void write_task(void*client_socketp){
    Serial.printf("started write task \n");

    Serial.flush();
    size_t bytes_left = 0;
    size_t bytes_written = 0;

    int16_t speaker_buf[64];
    speaker_buf[0] = 18;

    size_t offset = 0;

    int client_socket = *((int*)(client_socketp));

    while(writing){
        bytes_left = read(client_socket, speaker_buf, sizeof(speaker_buf));

        while (bytes_left % 2 != 0)
            bytes_left += read(client_socket, ((int8_t *)speaker_buf) + bytes_left, 1);
        offset = 0;
        while (bytes_left > 0)
        {   
            i2s_write(SPEAKER_I2S_NUM, ((int8_t*)speaker_buf) + offset, bytes_left, &bytes_written, portMAX_DELAY);
            bytes_left -= bytes_written;
            offset += bytes_written;
        }
    }
}

void read_task(void*client_socketf){
    Serial.printf("started read task \n");

    size_t bytes_left = 0;
    size_t bytes_written = 0;

    int16_t buf[64];
    buf[0] = 17;

    size_t offset = 0;

    int client_socket = *((int*)(client_socketf));

    while(reading){
        i2s_read(MIC_I2S_NUM, &buf, sizeof(buf), &bytes_left, portMAX_DELAY);

        size_t offset = 0;
        while (bytes_left > 0)
        {   
            bytes_written = write(client_socket, ((int8_t*)buf) + offset, bytes_left);
            bytes_left -= bytes_written;
            offset += bytes_written;
        }
    }
}

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

    Serial.printf("%s\n", WiFi.localIP().toString().c_str());

    audio_sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(4321);

    bind(audio_sock, (struct sockaddr *)&addr, sizeof(addr));
    listen(audio_sock, 2);
}

void loop()
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

    reading = 1;
    writing = 1;

    xTaskCreate(
        write_task,
        "writing task",
        10000,
        (void*)(&client_socket),
        1,
        &write_handle
    );

    xTaskCreate(
        read_task,
        "read_task",
        10000,
        &client_socket,
        2,
        &read_handle
    );

    while (1)
    {
        sleep(1);
        //todo: do stuff

    }
}