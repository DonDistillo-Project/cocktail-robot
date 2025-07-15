#pragma once

#define SETUP_CTRL_SOCK
#define PYTHON_NAN (double)-10000

#include "ModuleSettings.hpp"
#include "Modules/Scale.hpp"
#include "Modules/Screen.hpp"

#include "Modules/WiFi.hpp"
#include "lwip/sockets.h"
#include <freertos/task.h>

static int ctrl_sock;
int ctrl_client_sock;

TaskHandle_t ctrl_loop_handle = NULL;
TaskHandle_t ctrl_main_task = NULL;

bool scale_enabled = false;
double scale_target = -1.0;

void ctrl_error() {
  printf("Notifying main task of CTRL exit\n");
  xTaskNotifyGive(ctrl_main_task);
  vTaskSuspend(NULL);
}

typedef enum InfIDs {
  startRecipe,
  doStep,
  finishRecipe,
  abortRecipe,
  zeroScale,
} InfIDs;

typedef enum OutfIDs {
  notifyWeight,
} OutfIDs;

int receiveAll(void *buf, size_t len) {
  size_t bytes_left = len;
  ssize_t bytes_transferred = 0;
  size_t offset = 0;

  while (bytes_left > 0) {
    bytes_transferred = lwip_read(ctrl_client_sock, buf, bytes_left);

    if (bytes_transferred <= 0) {
      return bytes_transferred;
    }

    bytes_left -= bytes_transferred;
    offset += bytes_transferred;
  }
  return offset;
}
int receiveByte(void *byte) { return lwip_read(ctrl_client_sock, byte, 1); }

int sendAll(void *buf, size_t len) {
  size_t bytes_left = len;
  ssize_t bytes_transferred = 0;
  size_t offset = 0;

  while (bytes_left > 0) {
    bytes_transferred = lwip_write(ctrl_client_sock, buf, bytes_left);

    if (bytes_transferred <= 0) {
      return bytes_transferred;
    }

    bytes_left -= bytes_transferred;
    offset += bytes_transferred;
  }
  return offset;
}

int sendByte(char byte) { return lwip_write(ctrl_client_sock, &byte, 1); }

void _zeroScale() { setScaleOffset(); }

void _doStep(double stable_offset, double delta_target,
             unsigned char instruction_len, char *instruction) {
  if (delta_target != PYTHON_NAN) {
    scale_enabled = true;
    scale_target = delta_target;

    // printf("stable_offset: %lf, PYTHON_NAN: %f\n", stable_offset,
    // PYTHON_NAN);
    if (stable_offset != PYTHON_NAN) {
      _zeroScale();
      // scale_offset = stable_offset; // Set scale offset
    } else {
      _zeroScale();
    }
    render_scale(getScaleWeight(), delta_target);
  } else {
    scale_enabled = false;
    render_scale(0, 0);
  }

  render_instruction(instruction_len, instruction);
}

void _finishRecipe() { render_success(STR_AND_LEN("Recipe finished")); }
void _abortRecipe() { render_error(STR_AND_LEN("Recipe aborted")); }

void _startRecipe(unsigned char recipe_name_len, char *recipe_name) {
  scale_enabled = false;

  render_recipe(recipe_name_len, recipe_name);

  struct pollfd pfd{
      .fd = ctrl_client_sock,
      .events = POLLIN | POLLOUT,
      .revents = 0,
  };

  unsigned char fID = 254;
  double current_scale_weight;
  while (1) {
    pfd.revents = 0;
    if (lwip_poll(&pfd, 1, CTRL_SCALE_POLL_MS) > 0) {
      if (pfd.revents & POLLIN) {
        // New data for us to read

        // Read fID, guaranteed to read one byte if there are no errors!
        if (receiveByte(&fID) != 1) {
          printf("Error while receiving fID\n");
          return ctrl_error();
        }

        switch (fID) {
        case InfIDs::startRecipe:
          printf("Can not start new recipe while currently running recipe\n");
          return ctrl_error();
          break;
        case InfIDs::doStep:
          printf("Doing recipe step\n");

          struct doStepArgs {
            double stable_offset;
            double delta_target;
            unsigned char instruction_len;
            char instruction[256];
          } args;

          if (receiveAll(&args.stable_offset, sizeof(double)) !=
              sizeof(double)) {
            printf("Error while receiving doStep arguments\n");
            return ctrl_error();
          }

          if (receiveAll(&args.delta_target, sizeof(double)) !=
              sizeof(double)) {
            printf("Error while receiving doStep arguments\n");
            return ctrl_error();
          }

          if (receiveByte(&args.instruction_len) != 1) {
            printf("Error while receiving doStep instruction len\n");
            return ctrl_error();
          }

          if (receiveAll(args.instruction, args.instruction_len) !=
              args.instruction_len) {
            printf("Error while receiving doStep instruction string\n");
            return ctrl_error();
          }

          _doStep(args.stable_offset, args.delta_target, args.instruction_len,
                  args.instruction);

          break;
        case InfIDs::zeroScale:
          _zeroScale();
          break;
        case InfIDs::finishRecipe:
          printf("Finishing recipe\n");
          _finishRecipe();
          return;
        case InfIDs::abortRecipe:
          printf("Aborting recipe\n");
          _abortRecipe();
          return;
        default:
          printf("Error: Unrecognized fID: %d\n", fID);
          return ctrl_error();
        }
      }

      if (pfd.revents & POLLOUT) {
        if (sendByte(OutfIDs::notifyWeight) != 1) {
          printf("Error while sending notifyWeight fID\n");
          return ctrl_error();
        }
        current_scale_weight = getScaleWeight();
        printf("Sending Scale val: %lf\n", current_scale_weight);

        if (sendAll(&current_scale_weight, sizeof(double)) != sizeof(double)) {
          printf("Error while sending notifyWeight data\n");
          return ctrl_error();
        }

        if (scale_enabled) {
          render_scale(current_scale_weight, scale_target);
        }
      }
    }
    vTaskDelay(CTRL_SCALE_POLL_MS / portTICK_PERIOD_MS);
  }
}

void ctrl_loop(void *_) {
  size_t bytes_left = 0;
  ssize_t bytes_transferred = 0;
  size_t offset = 0;

  unsigned char recipe_name_len = 0;
  char recipe_name[256];
  bool currently_mixing = false;

  while (1) {
    int error = -1;
    char fID = -1;

    // Wait for startRecipe fID, guaranteed to read one byte if there are no
    // errors!
    if ((error = receiveByte(&fID)) != 1) {
      printf("Error while receiving initial fID: %d - %d\n", error, errno);
      return ctrl_error();
    }

    if (fID != InfIDs::startRecipe) {
      printf("Received %d as finitial fID - This is invalid\n");
      return ctrl_error();
    }

    // Wait for startRecipe recipe_name_len, guaranteed to read one byte if
    // there are no errors!
    if (receiveByte(&recipe_name_len) != 1) {
      printf("Error while receiving recipe_name_len\n");
      return ctrl_error();
    }

    // Wait for startRecipe recipe_name
    if (receiveAll(recipe_name, recipe_name_len) <= 0) {
      printf("Error while receiving recipe_name\n");
      return ctrl_error();
    }

    _startRecipe(recipe_name_len, recipe_name);
  }
}

int ctrlSockAccept() {
  sockaddr client_addr;
  size_t client_addr_len;

  if ((ctrl_client_sock = accept(ctrl_sock, (struct sockaddr *)&client_addr,
                                 &client_addr_len)) < 0) {
    perror("accept");
    exit(EXIT_FAILURE);
  }

  xTaskCreate(ctrl_loop, "ctrl_loop", CTRL_STACKSIZE, NULL, CTRL_PRIO,
              &ctrl_loop_handle);

  ctrl_main_task = xTaskGetCurrentTaskHandle();
  return 0;
}

int SetupCtrlSock() {
  ctrl_sock = socket(AF_INET, SOCK_STREAM, 0);
  sockaddr_in addr;
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = CTRL_ADDR;
  addr.sin_port = htons(CTRL_PORT);

  bind(ctrl_sock, (struct sockaddr *)&addr, sizeof(addr));
  listen(ctrl_sock, CTRL_BACKLOG);
  return 0;
}