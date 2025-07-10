#pragma once
#define SETUP_SCREEN

#include "ModuleSettings.hpp"
#include <Arduino.h>

#include <SPI.h>
#include <DEV_Config.h>

#define SUCCESS_POPUP_DURATION 1000 / portTICK_PERIOD_MS
#define ERROR_POPUP_DURATION 1000 / portTICK_PERIOD_MS

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
#include <freertos/task.h>
#include <freertos/queue.h>

#include "Modules/Serial.hpp"

typedef enum RenderMessageType
{
    RENDER_MSG_RECIPE,
    RENDER_MSG_INSTRUCTION,
    RENDER_MSG_SUCCESS,
    RENDER_MSG_ERROR,
    RENDER_VAL_SCALE,
} RenderMessageType;

typedef struct RenderMessageTextData
{
    unsigned char len;
    char *text;
} RenderMessageTextData;

typedef RenderMessageTextData RecipeData;
typedef RenderMessageTextData InstructionData;
typedef RenderMessageTextData SuccessData;
typedef RenderMessageTextData ErrorData;

typedef struct
{
    double value;
    double target;
} ScaleData;

typedef struct RenderMessage
{
    RenderMessageType type;
    union
    {
        RecipeData recipe;
        InstructionData instruction;
        SuccessData success;
        ErrorData error;
        ScaleData scale;
    } data;

} RenderMessage;

RenderMessageTextData alloc_message_text_data(unsigned char len, const char *text)
{
    RenderMessageTextData data{.len = len, .text = (char *)malloc(sizeof(char) * len + 1)};
    for (size_t i = 0; i < len; i++)
    {
        data.text[i] = text[i];
    }
    data.text[len] = 0; // Add an extra 0 just in case

    return data;
}

typedef struct
{
    unsigned int x;
    unsigned int y;
} Position;

typedef struct
{
    unsigned int left;
    unsigned int top;
    unsigned int right;
    unsigned int bottom;
} Box;

const Box shrink_box(const Box box, unsigned int pixels)
{
    return Box{.left = box.left + pixels, .top = box.top + pixels, .right = box.right - pixels, .bottom = box.bottom - pixels};
}

void print_box(const Box *box)
{
    printf("left: %d, top: %d, right: %d, bottom: %d\n", box->left, box->top, box->right, box->bottom);
}

void draw_string_in_box(UWORD Xstart, UWORD Ystart, const char *pString,
                        const sFONT *Font, UWORD Color_Background, UWORD Color_Foreground, const Box *box)
{
    UWORD Xpoint = Xstart;
    UWORD Ypoint = Ystart;

    unsigned int box_width = box->right - box->left;
    unsigned int box_height = box->bottom - box->top;

    if (Xstart > box_width + box->left || Ystart > box_height + box->top)
    {
        Debug("Paint_DrawString_EN Input exceeds the normal display range:\n");
        printf("Box: ");
        print_box(box);

        printf("Xstart: %d, Ystart: %d\n", Xstart, Ystart);
        return;
    }

    while (*pString != '\0')
    {
        if (*pString == '\n')
        {
            Xpoint = Xstart;
            Ypoint += Font->Height;

            pString++;
            continue;
        }

        // if X direction filled , reposition to(Xstart,Ypoint),Ypoint is Y direction plus the Height of the character
        if ((Xpoint + Font->Width) > box_width + box->left)
        {
            Xpoint = Xstart;
            Ypoint += Font->Height;
        }

        // If the Y direction is full, reposition to(Xstart, Ystart)
        if ((Ypoint + Font->Height) > box_height + box->top)
        {
            Xpoint = Xstart;
            Ypoint = Ystart;
        }
        Paint_DrawChar(Xpoint, Ypoint, *pString, Font, Color_Background, Color_Foreground);

        // The next character of the address
        pString++;

        // The next word of the abscissa increases the font of the broadband
        Xpoint += Font->Width;
    }
}
void draw_string_rel_box(const char *pString, const sFONT *Font, UWORD Color_Background, UWORD Color_Foreground, const Box *box, unsigned int offset_x = 0, unsigned int offset_y = 0)
{
    draw_string_in_box(offset_x + box->left, offset_y + box->top, pString, Font, Color_Background, Color_Foreground, box);
}

void draw_box(const Box *box, UWORD Color, DOT_PIXEL Line_width, DRAW_FILL Filled)
{
    Paint_DrawRectangle(box->left, box->top, box->right, box->bottom, Color, Line_width, Filled);
}
const unsigned int PopUpMargin = 20;
const unsigned int PopUpBorderSize = 3;
const Box PopUpBorderBox = {.left = PopUpMargin, .top = PopUpMargin, .right = LCD_WIDTH - PopUpMargin, .bottom = LCD_HEIGHT - PopUpMargin};
const Box PopUpBox = shrink_box(PopUpBorderBox, PopUpBorderSize);

const sFONT *RecipeHeaderFont = &Font8;
const Box RecipeHeaderBox = {.left = 5, .top = 2, .right = LCD_WIDTH - 5, .bottom = RecipeHeaderFont->Height * (unsigned int)2};

const sFONT *RecipeFont = &Font20;
const unsigned int RecipeLines = 2;
const Box RecipeBox = {.left = RecipeHeaderBox.left, .top = RecipeHeaderBox.bottom, .right = RecipeHeaderBox.right, RecipeHeaderBox.bottom + RecipeLines * RecipeFont->Height};

const sFONT *InstructionFont = &Font16;
const unsigned int InstructionLines = 8;
const unsigned int InstructionBoxBorderSize = 2;
const Box InstructionBorderBox = {.left = RecipeBox.left, .top = RecipeBox.bottom + InstructionBoxBorderSize, .right = RecipeBox.right, .bottom = RecipeBox.bottom + InstructionLines * InstructionFont->Height + 2 * InstructionBoxBorderSize};
const Box InstructionBox = shrink_box(InstructionBorderBox, InstructionBoxBorderSize);

const sFONT *ProgressStringFont = &Font16;
const unsigned int ProgressStringPadding = 6;
const Box ProgressStringBox = {.left = InstructionBorderBox.left, .top = InstructionBorderBox.bottom + ProgressStringPadding, .right = InstructionBorderBox.right, .bottom = InstructionBorderBox.bottom + ProgressStringPadding + ProgressStringFont->Height};

const unsigned int ProgressBarBorderSize = 2;

const Box ProgressBarBorderBox = {.left = ProgressStringBox.left + ProgressBarBorderSize, .top = ProgressStringBox.bottom + ProgressBarBorderSize, .right = ProgressStringBox.right - ProgressBarBorderSize, .bottom = LCD_HEIGHT - ProgressBarBorderSize};
const Box ProgressBarBox = shrink_box(ProgressBarBorderBox, ProgressBarBorderSize);

const double ProgressBarMaxPercentage = 1.2;
const unsigned int ProgressBarWidth = ProgressBarBox.right - ProgressBarBox.left;
const unsigned int ProgressBarTargetWidth = 4;
const unsigned int ProgressBarTargetCenter = ProgressBarBox.left + ProgressBarWidth / ProgressBarMaxPercentage;

const Position get_text_size(const char *str, const sFONT *font, unsigned int x_limit = LCD_WIDTH)
{
    unsigned int x_limit_rounded_down = x_limit - x_limit % font->Width;
    char *str_i = (char *)str;
    unsigned int line_count = 1;
    unsigned int chars_without_nl = 0;
    unsigned int max_chars_without_nl = 0;
    unsigned int len = 0;
    while (*str_i != '\0')
    {
        if (*str_i == '\n')
        {
            line_count++;
            max_chars_without_nl = max(max_chars_without_nl, chars_without_nl);
            chars_without_nl = 0;
        }
        else
        {
            chars_without_nl++;
            len++;
        }
        str_i++;
    }
    max_chars_without_nl = max(max_chars_without_nl, chars_without_nl);

    unsigned int max_width = min(max_chars_without_nl * font->Width, x_limit_rounded_down);
    unsigned int height = (line_count + len * font->Width / x_limit_rounded_down) * font->Height;

    return Position{
        .x = max_width, .y = height};
}

const Position get_text_size(const char *str, const sFONT *font, const Box *box)
{
    return get_text_size(str, font, box->right - box->left);
}

void draw_string_centered(const char *str, const Box *box, const sFONT *font, uint16_t bg, uint16_t fg)
{
    Position text_size = get_text_size(str, font, box);
    Position box_center{
        .x = (box->left + box->right) / 2,
        .y = (box->top + box->bottom) / 2,
    };

    draw_string_in_box(box_center.x - text_size.x / 2, box_center.y - text_size.y / 2, str, font, bg, fg, box);
}

/* AAAAAAAAAAAAAAAAAAAAAAAAAAAa */
int prev_value_x = 0;
int prev_overflow_x = 0;
bool base_layout_drawn = false;
unsigned int last_instruction_height = 0;

xQueueHandle render_queue;
xTaskHandle render_task;

void _render_base_layout()
{
    if (base_layout_drawn)
    {
        printf("Not rendering Base Layout, as it has already been drawn\n");
        return;
    }
    const char recipe_header[] = "Current Recipe:";
    draw_string_centered(recipe_header, &RecipeHeaderBox, RecipeHeaderFont, BLACK, WHITE);

    // Draw Scale Outline
    draw_box(&ProgressBarBorderBox, WHITE, (DOT_PIXEL)ProgressBarBorderSize, DRAW_FILL_EMPTY);

    // Draw Target Line
    Paint_DrawRectangle(ProgressBarTargetCenter - ProgressBarTargetWidth / 2, ProgressBarBox.top, ProgressBarTargetCenter + ProgressBarTargetWidth / 2, ProgressBarBox.bottom, BLUE, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL_FULL);

    // Draw Instruction Seperator
    draw_box(&InstructionBorderBox, GRAYBLUE, DOT_PIXEL::DOT_PIXEL_2X2, DRAW_FILL::DRAW_FILL_EMPTY);

    base_layout_drawn = true;
}

void _clear_layout()
{
    Paint_Clear(BLACK);
    base_layout_drawn = false;
}

void _render_recipe(RecipeData recipe)
{
    printf("Rendering Recipe: %s\n", recipe.text);
    _render_base_layout();
    draw_string_rel_box(recipe.text, RecipeFont, BLACK, WHITE, &RecipeBox);
}
void _render_instruction(InstructionData instruction)
{
    printf("Rendering Instruction: %s\n", instruction.text);

    Box clear_box = {.left = InstructionBox.left, .top = InstructionBox.top, .right = InstructionBox.right, .bottom = InstructionBox.top + last_instruction_height};
    draw_box(&clear_box, BLACK, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL::DRAW_FILL_FULL);

    draw_string_rel_box(instruction.text, InstructionFont, BLACK, WHITE, &InstructionBox);
    last_instruction_height = get_text_size(instruction.text, InstructionFont, &InstructionBox).y;
}
void _render_success(SuccessData success)
{
    printf("Rendering Success: %s\n", success.text);
    draw_box(&PopUpBorderBox, GBLUE, (DOT_PIXEL)PopUpBorderSize, DRAW_FILL::DRAW_FILL_EMPTY);
    draw_box(&PopUpBox, GREEN, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL::DRAW_FILL_FULL);
    draw_string_rel_box(success.text, &Font24, GBLUE, BLACK, &PopUpBox);

    vTaskDelay(SUCCESS_POPUP_DURATION);
    _clear_layout();
}
void _render_error(ErrorData error)
{
    printf("Rendering Error: %s\n", error.text);
    draw_box(&PopUpBorderBox, GRED, (DOT_PIXEL)PopUpBorderSize, DRAW_FILL::DRAW_FILL_EMPTY);
    draw_box(&PopUpBox, RED, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL::DRAW_FILL_FULL);
    draw_string_rel_box(error.text, &Font24, BRED, BLACK, &PopUpBox);

    vTaskDelay(ERROR_POPUP_DURATION);
    _clear_layout();
}
void _render_scale(ScaleData scale)
{
    printf("Rendering Scale: %.1f - %.1f\n", scale.value, scale.target);
    char scale_buf[30];

    size_t scale_buf_len = sprintf(scale_buf, "%4.1fg / %4.1fg", scale.value, scale.target);

    double fill_percent = scale.value / scale.target;
    double bar_width = ProgressBarBox.right - ProgressBarBox.left;

    double target_width = bar_width / ProgressBarMaxPercentage - ProgressBarTargetWidth / 2;
    double overflow_width = bar_width - target_width - ProgressBarTargetWidth / 2;

    int target_start = ProgressBarBox.left;
    int target_end = target_start + target_width;

    int overflow_start = target_end + ProgressBarTargetWidth;
    int overflow_end = ProgressBarBox.right;

    prev_value_x = max(target_start, prev_value_x);
    prev_overflow_x = max(overflow_start, prev_overflow_x);

    draw_string_centered(
        scale_buf,
        &ProgressStringBox,
        &Font16,
        BLACK,
        WHITE);

    int value_x = min(target_start + (int)(fill_percent * target_width), target_end);
    int overflow_x = max(min(overflow_start + (int)(((fill_percent - 1.0) / (ProgressBarMaxPercentage - 1.0)) * overflow_width), overflow_end), overflow_start);

    if (value_x > prev_value_x) // Fill up green bar to current level
    {
        // Extend green bar for current value
        Paint_DrawRectangle(prev_value_x, ProgressBarBox.top, value_x, ProgressBarBox.bottom, GREEN, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL_FULL);
    }

    if (overflow_x > prev_overflow_x)
    {
        // Extend overflow bar
        Paint_DrawRectangle(prev_overflow_x, ProgressBarBox.top, overflow_x, ProgressBarBox.bottom, RED, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL_FULL);
    }

    if (overflow_x < prev_overflow_x)
    {
        // Shrink overflow bar
        Paint_DrawRectangle(overflow_x, ProgressBarBox.top, prev_overflow_x, ProgressBarBox.bottom, BLACK, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL_FULL);
    }

    if (value_x < prev_value_x)
    {
        // Clear green bar for smaller current value
        Paint_DrawRectangle(value_x, ProgressBarBox.top, prev_value_x, ProgressBarBox.bottom, BLACK, DOT_PIXEL::DOT_PIXEL_1X1, DRAW_FILL_FULL);
    }

    printf("Done Rendering Scale\n");
    prev_value_x = value_x;
    prev_overflow_x = overflow_x;
}

void send_render_message(RenderMessage *msg_ptr)
{
    if (pdTRUE != xQueueSend(render_queue, msg_ptr, 1000 / portTICK_PERIOD_MS))
        printf("Error: Could not add render message (type=%d) to render queue\n", msg_ptr->type);
}

void render_recipe(unsigned char recipe_name_len, const char *recipe_name)
{

    RenderMessage msg{
        .type = RenderMessageType::RENDER_MSG_RECIPE, .data = {.recipe = alloc_message_text_data(recipe_name_len, recipe_name)}};

    send_render_message(&msg);
}

void render_instruction(unsigned char instruction_len, const char *instruction)
{
    RenderMessage msg{
        .type = RenderMessageType::RENDER_MSG_INSTRUCTION, .data = {.instruction = alloc_message_text_data(instruction_len, instruction)}};

    send_render_message(&msg);
}
void render_success(unsigned char success_msg_len, const char *success_msg)
{
    RenderMessage msg{
        .type = RenderMessageType::RENDER_MSG_SUCCESS, .data = {.success = alloc_message_text_data(success_msg_len, success_msg)}};
    send_render_message(&msg);
}
void render_error(unsigned char error_msg_len, const char *error_msg)
{
    RenderMessage msg{
        .type = RenderMessageType::RENDER_MSG_ERROR, .data = {.error = alloc_message_text_data(error_msg_len, error_msg)}};
    send_render_message(&msg);
}
void render_scale(double value, double target)
{
    RenderMessage msg{
        .type = RenderMessageType::RENDER_VAL_SCALE, .data = {.scale = ScaleData{.value = value, .target = target}}};
    send_render_message(&msg);
}

void render_loop(void *_)
{
    RenderMessage msg;
    while (1)
    {
        if (pdTRUE == xQueueReceive(render_queue, (void *)&msg, portMAX_DELAY))
        {
            switch (msg.type)
            {
            case RenderMessageType::RENDER_MSG_RECIPE:
                _render_recipe(msg.data.recipe);
                free(msg.data.recipe.text);
                render_scale(0.0, 0.0);
                break;
            case RenderMessageType::RENDER_MSG_INSTRUCTION:
                _render_instruction(msg.data.instruction);
                free(msg.data.instruction.text);
                break;
            case RenderMessageType::RENDER_MSG_SUCCESS:
                _render_success(msg.data.success);
                free(msg.data.success.text);
                break;
            case RenderMessageType::RENDER_MSG_ERROR:
                _render_error(msg.data.error);
                free(msg.data.error.text);
                break;
            case RenderMessageType::RENDER_VAL_SCALE:
                _render_scale(msg.data.scale);
                break;
            }
        }
    }
    return;
}

void SetupScreen()
{
    Config_Init(SCREEN_CLK_PIN, SCREEN_DIN_PIN);
    LCD_Init();
    LCD_SetBacklight(100);
    Paint_NewImage(LCD_WIDTH, LCD_HEIGHT, 0, BLACK);

    render_queue = xQueueCreate(10, sizeof(RenderMessage));
    xTaskCreate(render_loop, "render_loop", SCREEN_RENDER_STACKSIZE, NULL, SCREEN_RENDER_PRIO, &render_task);
    char succes_msg[] = "Render Loop started";

    render_success(sizeof(succes_msg), succes_msg);
}