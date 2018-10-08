#!/usr/bin/python -u
#
# ----------------------------------------------------------------------------------------
#
#  This is a little tester for Pi relay modules.
#
# 09/28/18 - Coded this for a 4 relay module, active low, using board pin numbering...
#     4 - VCC, 5V rail
#     7 - output to relay 1
#     9 - ground
#    11 - output to relay 2
#    13 - output to relay 3
#    15 - output to relay 4
#
# ========================================================================================

import datetime
import sys
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
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

	if len(sys.argv) >= 2 :
		config_file = sys.argv[1]

	setup_gpio()

	sleep(2)

	while True:

		power_cycle( 13, 5 )

		GPIO.output( 7, relay__ON)
		sleep(2)
		GPIO.output(11, relay__ON)
		sleep(2)
		GPIO.output(13, relay__ON)
		sleep(2)
		GPIO.output(15, relay__ON)
		sleep(2)

		GPIO.output( 7, relay__OFF)
		sleep(2)
		GPIO.output(11, relay__OFF)
		sleep(2)
		GPIO.output(13, relay__OFF)
		sleep(2)
		GPIO.output(15, relay__OFF)
		sleep(2)

	exit()


# ----------------------------------------------------------------------------------------
# Set up the GPIO.
# Caller can specify the initial state.
#
# NOTE: For the SunFounder module, if we don't set the 2nd GPIO high it seems to
#       "float", so the LED for relay 2 comes on dimly.  This is a little "cleaner."
# ----------------------------------------------------------------------------------------
def setup_gpio():
	GPIO.setwarnings(False)
#	GPIO.setmode(GPIO.BCM)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup( 7, GPIO.OUT, initial=relay__OFF)
	GPIO.setup(11, GPIO.OUT, initial=relay__OFF)
	GPIO.setup(13, GPIO.OUT, initial=relay__OFF)
	GPIO.setup(15, GPIO.OUT, initial=relay__OFF)

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
# Clean up any GPIO configs - typically on exit.
#
# ----------------------------------------------------------------------------------------
def destroy_gpio():
	logger("Shutting down...\n")
	GPIO.output( 7, relay__OFF)
	GPIO.output(11, relay__OFF)
	GPIO.output(13, relay__OFF)
	GPIO.output(15, relay__OFF)
	GPIO.cleanup()



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
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	messager("INFO: Starting {}   PID={}".format( this_script, os.getpid() ) )

	try:
		main()

	# --------------------------------------------------------------------------------
	# Probably should handle external signals.  I manually use kill -9 (SIGKILL)
	#   https://www.cyberciti.biz/faq/unix-kill-command-examples/
	# Not sure what systemctl uses...
	# --------------------------------------------------------------------------------
	except KeyboardInterrupt:
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Progress indicator Ending
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		logger("  Good bye from " + this_script)
		destroy_gpio()

	exit()
