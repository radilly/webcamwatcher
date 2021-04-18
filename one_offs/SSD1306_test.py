#!/usr/bin/python3 -u

# From: https://github.com/adafruit/Adafruit_CircuitPython_SSD1306

# Basic example of clearing and drawing pixels on a SSD1306 OLED display.
# This example and library is meant to work with Adafruit CircuitPython API.
# Author: Tony DiCola
# License: Public Domain

# Import all board pins.
from board import SCL, SDA
import busio

# Import the SSD1306 module.
import adafruit_ssd1306


# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
# Alternatively you can change the I2C address of the device with an addr parameter:
#display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x31)

# Clear the display.  Always call show after changing pixels to make the display
# update visible!
display.fill(0)

display.show()

exit()

# Set a pixel in the origin 0,0 position.
display.pixel(0, 0, 1)
# Set a pixel in the middle 64, 16 position.
display.pixel(64, 16, 1)
# Set a pixel in the opposite 127, 31 position.
display.pixel(127, 31, 1)
display.show()

exit()

# ========================================================================================
#   https://learn.adafruit.com/ssd1306-oled-displays-with-raspberry-pi-and-beaglebone-black/usage
#   replaced by
#   https://learn.adafruit.com/monochrome-oled-breakouts/python-wiring
#   https://learn.adafruit.com/monochrome-oled-breakouts/python-setup
#   https://learn.adafruit.com/monochrome-oled-breakouts/python-usage-2
#
#   https://github.com/adafruit/Adafruit_CircuitPython_SSD1306
#   If needed: sudo apt install python3-pip
#
#   sudo pip3 install adafruit-circuitpython-ssd1306
#
#
#
#   vi SSD1306_test.py
#   chmod +x  SSD1306_test.py
#
#   May net be needed: sudo apt-get install python3-pil
#
#   sudo apt-get install -y python-smbus
#   sudo i2cdetect -y 1
#
#   sudo raspi-config
#   Ref: https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c
#    3 Interface Options    Configure connections to peripherals 
#        P5 I2C         Enable/disable automatic loading of I2C kernel module
#            Would you like the ARM I2C interface to be enabled?
#
#   ./SSD1306_test2.py 
#   sudo i2cdetect -y 1
# ========================================================================================


