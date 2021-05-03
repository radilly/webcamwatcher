#!/usr/bin/python3 -u
#
# Script to read a button / switch state
#
# If needed (Raspberry OS Lite versions), install rpi.gpio (for python3)
#  https://www.raspberrypi-spy.co.uk/2012/05/install-rpi-gpio-python-library/
#
#
#
#
#  https://www.caretech.io/2018/01/20/using-the-rpi-gpio-module-with-python-3/
#
#      sudo apt install python3-rpi.gpio
#
#
#
# ========================================================================================
# 20201204 RAD Gutted unused code from this, which was hacked from light_timer.py.
#
# ========================================================================================

import datetime
import sys
### >>> import re

import RPi.GPIO as GPIO

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
### >>> this_script = sys.argv[0]
### >>> logger_file = re.sub('\.py', '.log', this_script)

strftime_FMT = "%Y/%m/%d %H:%M:%S"



# ----------------------------------------------------------------------------------------
# Set up the GPIO.
# Caller can specify the initial state.
#
# NOTE: For the SunFounder module, if we don't set the 2nd GPIO high it seems to
#       "float", so the LED for relay 2 comes on dimly.  This is a little "cleaner."
# ----------------------------------------------------------------------------------------
def setup_gpio( IO_number ):
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)

#DEBUG#	messager("DEBUG: Setting up GPIO {}".format( IO_number ) )

	# GPIO.setup( IO_number, GPIO.OUT )
	# https://raspberrypihq.com/use-a-push-button-with-raspberry-pi-gpio/
	GPIO.setup( IO_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)


# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print( "{} {}".format( timestamp, message ) )


# ----------------------------------------------------------------------------------------
#
#
#
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	if len(sys.argv) < 2 :
		messager( "ERROR: Syntax: nn \n   where nn is BCM (not pin) I/O number" )
		# messager( "ERROR: Syntax: nn state\n   where nn is BCM (not pin) I/O number\n         state is \"high\" or \"low\"" )
		exit()

	# relay_GPIO = int( sys.argv[1] )
	gpio_number = int( sys.argv[1] )
#@@@#	state_txt = sys.argv[2]

	setup_gpio( gpio_number )

if GPIO.input( gpio_number ):
	print("Pin {} is HIGH".format( gpio_number ) )
else:
	print("Pin {} is LOW".format( gpio_number ) )

	exit()
	exit()
	exit()


#@@@#	if "hi" in state_txt :
#@@@#		relay_state = GPIO.HIGH
#DEBUG#		messager("DEBUG: Setting GPIO {} HIGH.".format( relay_GPIO ) )
#@@@#	elif "lo" in state_txt :
#@@@#		relay_state = GPIO.LOW
#DEBUG#		messager("DEBUG: Setting GPIO {} LOW.".format( relay_GPIO ) )
#@@@#	else :
#@@@#		relay_state = GPIO.LOW
#@@@#		messager("ERROR: Invalid state specified: \"{}\"".format( state_txt ) )

#@@@#	messager("INFO: GPIO.output( {} , {} )".format( relay_GPIO, relay_state ) )
	GPIO.output( gpio_number, relay_state )

	exit()
	exit()
	exit()
