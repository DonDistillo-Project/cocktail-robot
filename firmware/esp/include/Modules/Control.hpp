#pragma once

#define SETUP_CTRL_SOCK

#include "ModuleSettings.hpp"
#include "Modules/Scale.hpp"

#include "Modules/WiFi.hpp"
#include "lwip/sockets.h"
#include <freertos/task.h>

static int ctrl_sock;
int ctrl_client_sock;

TaskHandle_t ctrl_loop_handle = NULL;
TaskHandle_t ctrl_main_task = NULL;

void ctrl_error()
{
    printf("Notifying main task of CTRL exit\n");
    xTaskNotifyGive(ctrl_main_task);
    vTaskDelete(xTaskGetCurrentTaskHandle());
}

typedef enum InfIDs
{
    startRecipe,
    doStep,
    finishRecipe,
    abortRecipe,
    zeroScale,
} InfIDs;

typedef enum OutfIDs
{
    notifyWeight,
} OutfIDs;

int receiveAll(void *buf, size_t len)
{
    size_t bytes_left = len;
    ssize_t bytes_transferred = 0;
    size_t offset = 0;

    while (bytes_left > 0)
    {
        bytes_transferred = lwip_read(ctrl_client_sock, buf, bytes_left);

        if (bytes_transferred <= 0)
        {
            return bytes_transferred;
        }

        bytes_left -= bytes_transferred;
        offset += bytes_transferred;
    }
    return offset;
}
int receiveByte(void *byte)
{
    return lwip_read(ctrl_client_sock, byte, 1);
}

int sendAll(void *buf, size_t len)
{
    size_t bytes_left = len;
    ssize_t bytes_transferred = 0;
    size_t offset = 0;

    while (bytes_left > 0)
    {
        bytes_transferred = lwip_write(ctrl_client_sock, buf, bytes_left);

        if (bytes_transferred <= 0)
        {
            return bytes_transferred;
        }

        bytes_left -= bytes_transferred;
        offset += bytes_transferred;
    }
    return offset;
}

int sendByte(char byte)
{
    return lwip_write(ctrl_client_sock, &byte, 1);
}

void runStep(double stable_offset, double delta_target, unsigned char instruction_len, char *instruction)
{
    // Currently ignored.
}

void runRecipe(unsigned char recipe_name_len, char *recipe_name)
{

    struct pollfd pfd{
        .fd = ctrl_client_sock,
        .events = POLLIN | POLLOUT,
        .revents = 0,
    };

    char fID = -1;
    double current_scale_weight;

    while (1)
    {
        pfd.revents = 0;
        if (lwip_poll(&pfd, 1, CTRL_SCALE_POLL_MS) > 0)
        {
            if (pfd.revents & POLLIN)
            {
                // New data for us to read

                // Read fID, guaranteed to read one byte if there are no errors!
                if (receiveByte(&fID) != 1)
                {
                    printf("Error while receiving fID\n");
                    return ctrl_error();
                }

                switch (fID)
                {
                case InfIDs::startRecipe:
                    printf("Can not start new recipe while currently running recipe\n");
                    return ctrl_error();
                    break;
                case InfIDs::doStep:
                    printf("Doing recipe step\n");

                    struct doStepArgs
                    {
                        double stable_offset;
                        double delta_target;
                        unsigned char instruction_len;
                        char instruction[256];
                    } args;

                    if (receiveAll(&args.stable_offset, sizeof(double)) != sizeof(double))
                    {
                        printf("Error while receiving doStep arguments\n");
                        return ctrl_error();
                    }

                    if (receiveAll(&args.delta_target, sizeof(double)) != sizeof(double))
                    {
                        printf("Error while receiving doStep arguments\n");
                        return ctrl_error();
                    }

                    if (receiveByte(&args.instruction_len) != 1)
                    {
                        printf("Error while receiving doStep instruction len\n");
                        return ctrl_error();
                    }

                    if (receiveAll(args.instruction, args.instruction_len) != args.instruction_len)
                    {
                        printf("Error while receiving doStep instruction string\n");
                        return ctrl_error();
                    }

                    runStep(args.stable_offset, args.delta_target, args.instruction_len, args.instruction);

                    break;
                case InfIDs::finishRecipe:
                    printf("Finishing recipe\n");
                    // TODO: Do something
                    return;
                case InfIDs::abortRecipe:
                    printf("Aborting recipe\n");
                    // TODO: Do something
                    return;

                default:
                    printf("Error: Unrecognized fID: %d\n", fID);
                    return ctrl_error();
                }
            }

            if (pfd.revents & POLLOUT)
            {
                if (sendByte(OutfIDs::notifyWeight) != 1)
                {
                    printf("Error while sending notifyWeight fID\n");
                    return ctrl_error();
                }
                current_scale_weight = getScaleWeight();
                if (sendAll(&current_scale_weight, sizeof(double)) != sizeof(double))
                {
                    printf("Error while sending notifyWeight data\n");
                    return ctrl_error();
                }
            }
        }
        vTaskDelay(CTRL_SCALE_POLL_MS / portTICK_PERIOD_MS);
    }
}

void ctrl_loop(void *client_socketp)
{
    size_t bytes_left = 0;
    ssize_t bytes_transferred = 0;
    size_t offset = 0;

    ctrl_client_sock = *((int *)(client_socketp));

    unsigned char recipe_name_len = 0;
    char recipe_name[256];
    bool currently_mixing = false;

    while (1)
    {
        char fID = -1;

        // Wait for startRecipe fID, guaranteed to read one byte if there are no errors!
        if (receiveByte(&fID) != 1)
        {
            printf("Error while receiving initial fID: %d\n", fID);
            return ctrl_error();
        }

        if (fID != InfIDs::startRecipe)
        {
            printf("Received %d as finitial fID - This is invalid\n");
            return ctrl_error();
        }

        // Wait for startRecipe recipe_name_len, guaranteed to read one byte if there are no errors!
        if (receiveByte(&recipe_name_len) != 1)
        {
            printf("Error while receiving recipe_name_len\n");
            return ctrl_error();
        }

        // Wait for startRecipe recipe_name
        if (receiveAll(recipe_name, recipe_name_len) <= 0)
        {
            printf("Error while receiving recipe_name\n");
            return ctrl_error();
        }

        runRecipe(recipe_name_len, recipe_name);
    }
}

int ctrlSockAccept()
{
    sockaddr client_addr;
    size_t client_addr_len;
    int client_socket;

    if ((client_socket = accept(ctrl_sock, (struct sockaddr *)&client_addr, &client_addr_len)) < 0)
    {
        perror("accept");
        exit(EXIT_FAILURE);
    }

    xTaskCreate(
        ctrl_loop,
        "ctrl_loop",
        CTRL_STACKSIZE,
        (void *)(&client_socket),
        CTRL_SEND_PRIO,
        &ctrl_loop_handle);

    ctrl_main_task = xTaskGetCurrentTaskHandle();
    return 0;
}

int SetupCtrlSock()
{
    ctrl_sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = CTRL_ADDR;
    addr.sin_port = htons(CTRL_PORT);

    bind(ctrl_sock, (struct sockaddr *)&addr, sizeof(addr));
    listen(ctrl_sock, CTRL_BACKLOG);
    return 0;
}