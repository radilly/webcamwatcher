#!/usr/bin/python -u
#
# ----------------------------------------------------------------------------------------
#
# This is meant to be hard-wired to inititalize GPIOs we will use on a particular
# pi - generally at boot-up - so that we take them out of a "floating" state.
#
# 03/05/19  Since going to a remote power-cycling model for resetting webcams, I
#           noticed that the LEDs on the relay module are dimly lit after a reboot.
#           Since we don't touch the releays until a problem is detected (remotely),
#           there is no particular the initial state shouldbe set - unless we do
#           it intentionally.
#
#
# ========================================================================================
#
# NOTE: Not clear we want this to generate any output.  Maybe printing a small
#       confirmation of task completed would be useful if this is run by systemd.
#
#
#
#
# ========================================================================================
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# Set up the list of GPIOs to initialize.
# NOTE: this could be a command line list...
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
IO_List = [
	23,
	24,
	]


import datetime
import sys
import os
import re

from time import sleep
import RPi.GPIO as GPIO



# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# For active-low circuits, the thinking is somewhat upside down.
# We define these variable to make the action a little more intuitive for coding.
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
relay__ON = GPIO.LOW
relay__OFF = GPIO.HIGH

this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( os.getcwd(), re.sub('^\./', '', this_script) )

logger_file = re.sub('\.py', '.log', this_script)

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"


# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():

	setup_gpio()



# ----------------------------------------------------------------------------------------
# Set up the GPIO.
# Caller can specify the initial state.
#
# NOTE: For the SunFounder module, if we don't set the 2nd GPIO high it seems to
#       "float", so the LED for relay 2 comes on dimly.  This is a little "cleaner."
# ----------------------------------------------------------------------------------------
def setup_gpio():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
###	GPIO.setmode(GPIO.BOARD)
	
	for IO in IO_List :
		GPIO.setup( IO, GPIO.OUT, initial=relay__OFF)




# ----------------------------------------------------------------------------------------
# Cycle the power on the relay / GPIO.
# The off time can be specified.  Here in secs.
#
# From a quick test, the (South) RSX-3211 webam seems to take around 32 secs to reboot.
# ----------------------------------------------------------------------------------------
def power_cycle( relay_GPIO, interval ):
	logger( '...open relay contacts.')
	GPIO.output(relay_GPIO, relay__ON)

	sleep( interval )

	logger('...close relay contacts.')
	GPIO.output(relay_GPIO, relay__OFF)




# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)
	return

	FH = open(logger_file, "a")
	FH.write( "{} {}\n".format( timestamp, message) )
	FH.close

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)


# ----------------------------------------------------------------------------------------
#
#  Probably not needed for this.
#
#
#
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	main()

	GPIO.cleanup()

	exit()
