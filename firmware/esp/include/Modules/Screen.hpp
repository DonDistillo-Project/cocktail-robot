#pragma once
#define SETUP_SCREEN

#include "ModuleSettings.hpp"
#include <Arduino.h>

#include <SPI.h>
#include <DEV_Config.h>

#undef DEV_CS_PIN
#define DEV_CS_PIN SCREEN_CS_PIN

#undef DEV_DC_PIN
#define DEV_DC_PIN SCREEN_DC_PIN

#undef DEV_RST_PIN
#define DEV_RST_PIN SCREEN_RST_PIN

#undef DEV_BL_PIN
#define DEV_BL_PIN SCREEN_BL_PIN

#include <LCD_Driver.h>
#include <GUI_Paint.h>

void SetupScreen()
{
    Config_Init(SCREEN_CLK_PIN, SCREEN_DIN_PIN);
    LCD_Init();
    LCD_Clear(WHITE);
    LCD_SetBacklight(100);
}