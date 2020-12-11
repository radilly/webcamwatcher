#!/usr/bin/python3 -u
#
# Script to operate an output pin on a Raspberry Pi
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
def setup_gpio( IO ):
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)

#DEBUG#	messager("DEBUG: Setting up GPIO {}".format( IO ) )

	GPIO.setup( IO, GPIO.OUT )


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

	if len(sys.argv) < 3 :
		messager( "ERROR: Syntax: nn state\n   where nn is BCM (not pin) I/O number\n         state is \"high\" or \"low\"" )
		exit()

	relay_GPIO = int( sys.argv[1] )
	state_txt = sys.argv[2]

	setup_gpio( relay_GPIO )

	if "hi" in state_txt :
		relay_state = GPIO.HIGH
#DEBUG#		messager("DEBUG: Setting GPIO {} HIGH.".format( relay_GPIO ) )
	elif "lo" in state_txt :
		relay_state = GPIO.LOW
#DEBUG#		messager("DEBUG: Setting GPIO {} LOW.".format( relay_GPIO ) )
	else :
		relay_state = GPIO.LOW
		messager("ERROR: Invalid state specified: \"{}\"".format( state_txt ) )

	messager("INFO: GPIO.output( {} , {} )".format( relay_GPIO, relay_state ) )
	GPIO.output( relay_GPIO, relay_state )

	exit()
	exit()
	exit()
