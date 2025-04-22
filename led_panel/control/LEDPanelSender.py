import numpy as np
import serial
import time

MG_BYTE = 0xAA
CMD_CLEAR_SCREEN = 0x01
CMD_SET_BRIGHTNESS = 0x02
CMD_DISPLAY_IMG = 0x03
CMD_PUT_PIXEL = 0x04

# Display resolution
WIDTH = 64
HEIGHT = 32

def color565(r, g, b):
    """
    Convert 8-bit RGB888 to RGB565
    """
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

class LEDPanelSender:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial(self.port, self.baudrate, timeout=1)

    def __del__(self):
        if self.serial and self.serial.is_open:
            self.serial.close()

    def send_image(self, img: np.ndarray):
        """
        Send a 64x32 RGB image (as a numpy array) to the ESP32.
        """
        if img.shape != (HEIGHT, WIDTH, 3):
            raise ValueError(f"Image must be shape ({HEIGHT}, {WIDTH}, 3)")

        # Send start byte and command
        self.serial.write(bytes([MG_BYTE, CMD_DISPLAY_IMG]))

        # Send image pixel by pixel (little-endian RGB565)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = img[y, x]
                rgb565 = color565(r, g, b)
                # Little endian: low byte first
                self.serial.write(bytes([rgb565 & 0xFF, (rgb565 >> 8) & 0xFF]))

        time.sleep(0.5)

    def clear_screen(self):
        """
        Send command to clear the screen.
        """
        self.serial.write(bytes([MG_BYTE, CMD_CLEAR_SCREEN]))
        time.sleep(0.1)

    def set_brightness(self, brightness: int):
        """
        Set brightness level (0-255).
        """
        brightness = max(0, min(255, brightness))
        self.serial.write(bytes([MG_BYTE, CMD_SET_BRIGHTNESS, brightness]))
        time.sleep(0.1)

    def put_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """
        Set a single pixel to a specific RGB color.
        """
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            raise ValueError("Pixel coordinates out of bounds")

        rgb565 = color565(r, g, b)
        self.serial.write(bytes([MG_BYTE, CMD_PUT_PIXEL, x, y, rgb565 & 0xFF, (rgb565 >> 8) & 0xFF]))
        time.sleep(0.01)

# Example usage:
if __name__ == "__main__":
    # Create a test image (black with red pixel grid)
    image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    for y in range(0, HEIGHT, 4):
        for x in range(0, WIDTH, 4):
            image[y, x] = [255, 0, 0]

    sender = LEDPanelSender(port="/dev/ttyUSB0")
    sender.clear_screen()
    sender.set_brightness(128)
    sender.send_image(image)
    sender.put_pixel(10, 10, 0, 255, 0)  # Example: set pixel (10, 10) to green
