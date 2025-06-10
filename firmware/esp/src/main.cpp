#include "Setup/Setup.hpp"

#include "Setup/Serial.hpp"
#include "Setup/FS.hpp"
#include "Setup/WiFi.hpp"
// #include "Setup/Scale.hpp"
#include "Setup/Mic.hpp"
// #include "Setup/Speaker.hpp"

#include <lwip/sockets.h>
int audio_sock;
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

    size_t bytes_left = 0;
    size_t offset = 0;
    size_t bytes_written = 0;
    while (1)
    {
        // Serial.println("READING MIC");
        bytes_left = readMic();

        while (bytes_left > 0)
        {
            bytes_written = write(client_socket, ((int8_t *)mic_buffer) + offset, bytes_left);
            bytes_left -= bytes_written;
            offset += bytes_written;
        }

        // bytes_left = read(client_socket, ((int8_t *)speaker_buffer), sizeof(speaker_buffer));
        // while (bytes_left % 2 != 0)
        //     bytes_left += read(client_socket, ((int8_t *)speaker_buffer) + bytes_left, 1);

        // while (bytes_left > 0)
        // {
        //     bytes_written = writeSpeaker((int16_t *)((int8_t *)speaker_buffer + offset), bytes_left);
        //     bytes_left -= bytes_written;
        //     offset += bytes_written;
        // }
    }
}