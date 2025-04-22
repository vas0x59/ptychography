#include <Arduino.h>
#include <ESP32-HUB75-VirtualMatrixPanel_T.hpp>

#define PANEL_RES_X 64
#define PANEL_RES_Y 32

#define RL1 16
#define GL1 0
#define BL1 15
#define RL2 17
#define GL2 4
#define BL2 2
#define CH_A 33
#define CH_B 25
#define CH_C 26
#define CH_D 27
#define CH_E -1  
#define CLK 18
#define LAT 5
#define OE  32

#define MG_BYTE 0xAA

enum Command {
  CMD_CLEAR_SCREEN = 0x01,
  CMD_SET_BRIGHTNESS = 0x02,
  CMD_DISPLAY_IMG = 0x03,
  CMD_PUT_PIXEL = 0x04
}

MatrixPanel_I2S_DMA *dma_display = nullptr;

struct CustomMirrorScanTypeMapping {

  static VirtualCoords apply(VirtualCoords coords, int pixel_base) {
    // coords.x = coords.x % 16 + (coords.x / 16) * 32 + 16 * (1 - (coords.y / 8) % 2);
    // coords.y = (coords.y / 16) * 8 + coords.y % 8;
    int16_t x = coords.x;
    int16_t y = coords.y;

    coords.x = (x & 15) + ((x >> 4) << 5) + (1 ^ ((y >> 3) & 1)) << 4;
    coords.y = ((y >> 4) << 3) + (y & 7);

    return coords;
  }
};

VirtualMatrixPanel_T<CHAIN_NONE, CustomMirrorScanTypeMapping>* virtualDisp = nullptr;

void cmd_clear_screen() {
  virtualDisp->clearScreen();
}

void cmd_set_brightness() {
  uint8_t b = Serial.read();
  dma_display->setBrightness8(b);
}

void cmd_display_img() {
  for (int y = 0; y < virtualDisp->height(); y++) {
    for (int x = 0; x < virtualDisp->width(); x++) {
      uint8_t lowByte = Serial.read();       // Least significant byte
      uint8_t highByte = Serial.read();      // Most significant byte

      uint16_t value = (highByte << 8) | lowByte;
      virtualDisp->drawPixel(x, y, value);
    }
  }
}

void cmd_put_pixel() {
  uint8_t x = Serial.read();
  uint8_t y = Serial.read();
  uint8_t lowByte = Serial.read();       // Least significant byte
  uint8_t highByte = Serial.read();      // Most significant byte

  uint16_t value = (highByte << 8) | lowByte;
  virtualDisp->drawPixel(x, y, value);
}


void setup() {
  Serial.begin(115200);
  HUB75_I2S_CFG::i2s_pins _pins={RL1, GL1, BL1, RL2, GL2, BL2, CH_A, CH_B, CH_C, CH_D, CH_E, LAT, OE, CLK};

  HUB75_I2S_CFG mxconfig(
    PANEL_RES_X*2,               
    PANEL_RES_Y/2, 
    1, 
    _pins     
  );

  mxconfig.i2sspeed = HUB75_I2S_CFG::HZ_10M;
  mxconfig.clkphase = false;

  dma_display = new MatrixPanel_I2S_DMA(mxconfig);
  dma_display->begin();
  dma_display->setBrightness8(20); //0-255
  dma_display->clearScreen();

  virtualDisp = new VirtualMatrixPanel_T<CHAIN_NONE, CustomMirrorScanTypeMapping>(1, 1, PANEL_RES_X, PANEL_RES_Y); 
  virtualDisp->setDisplay(*dma_display);
  virtualDisp->clearScreen();

  for (int y = 0; y < virtualDisp->height(); y++) {
    for (int x = 0; x < virtualDisp->width(); x++) {

    uint16_t color = virtualDisp->color444(0, 10, 0);
    if (x % 4 == 3 && y % 4 == 3)
      virtualDisp->drawPixel(x, y, color);
      
    }
  }

}

void loop() {
  if (Serial.available() >= 2) {
    if (Serial.read() == MG_BYTE) {
      uint8_t cmd = Serial.read();
      switch (cmd) {
        case CMD_CLEAR_SCREEN:
          cmd_clear_screen();
          break;
        case CMD_SET_BRIGHTNESS:
          cmd_set_brightness();
          break;
        case CMD_DISPLAY_IMG:
          cmd_display_img();
          break;
        case CMD_PUT_PIXEL:
          cmd_put_pixel();
          break;
        default:
          break;
      }
    }
  }
}
