#!/usr/bin/python -u
# 
# This script is meant to be called from webcamimager.py via ssh so that a remote
# power cycle can be accomodated.  For a local power cycle, it appears using the
# loopback ip will work - 127.0.0.1.
#
# ----------------------------------------------------------------------------------------
# NOTE: Some pages on shh'ing commands...
#
# https://stackoverflow.com/questions/373639/running-interactive-commands-in-paramiko
# https://stackoverflow.com/questions/3586106/perform-commands-over-ssh-with-python
# https://stackoverflow.com/questions/1233655/what-is-the-simplest-way-to-ssh-using-python/1233872#1233872
# https://stackoverflow.com/questions/32476093/native-ssh-in-python
# https://www.tutorialspoint.com/What-is-the-simplest-way-to-SSH-using-Python
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# ========================================================================================
# ========================================================================================
# 20190601 RAD Minor cleanup of unused stuff.
# 20190216 RAD Didin't seem to work quite right, and no logging occurred.
#              Took a stab at cleaning this up.
# 20181020 RAD Hacked webcamimager.py into this simpe script.
#              .
#
# ========================================================================================
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

import datetime
from time import sleep
import sys
from os import getpid
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import re

import RPi.GPIO as GPIO
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
#  NOTE: For the SunFounder Relay Module, there's sort of a double negative at work.
#     It is active low, so by default you might think GPIO.LOW.
#
#     But ... We are using the NC contacts of the relay so that, with the module
#     unpowered, the webcam gets power.  Power-cycling means energizing the relay
#     briefly by driving the input pin low.
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# relay_GPIO = 23
relay_GPIO = ""
webcam_ON = GPIO.HIGH
webcam_OFF = GPIO.LOW

this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( getcwd(), re.sub('^\./', '', this_script) )

logger_file = re.sub('\.py', '.log', this_script)

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"

# See https://pinout.xyz/resources/raspberry-pi-pinout.png
Good_BCM_Pins = [
	0,   #  0
	0,   #  1
	0,   #  2
	0,   #  3
	1,   #  4
	1,   #  5
	1,   #  6
	0,   #  7
	0,   #  8
	0,   #  9
	0,   # 10
	0,   # 11
	1,   # 12
	1,   # 13
	0,   # 14
	0,   # 15
	1,   # 16
	1,   # 17
	1,   # 18
	0,   # 19
	0,   # 20
	0,   # 21
	1,   # 22
	1,   # 23
	1,   # 24
	1,   # 25
	1,   # 26
	1,   # 27
	0,   # 28
	0,   # 29
	]



# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():
	global relay_GPIO

	if len(sys.argv) >= 2 :
		relay_GPIO = int( sys.argv[1] )
	else :
		log_and_message( "ERROR: GPIO BCM number is a required first argument." )
		exit()

	if Good_BCM_Pins [ relay_GPIO ] < 1 :
		log_and_message( "ERROR: BCM pin number {} is not valid.  See https://pinout.xyz/resources/raspberry-pi-pinout.png.".format( relay_GPIO ) )
		exit()

	setup_gpio()

	power_cycle( 5 )

	exit()



# ----------------------------------------------------------------------------------------
# Set up the GPIO.
# Caller can specify the initial state.
#
# NOTE: For the SunFounder module, if we don't set the 2nd GPIO high it seems to
#	"float", so the LED for relay 2 comes on dimly.  This is a little "cleaner."
#
# NOTE: See https://pinout.xyz/ for GPIO numbering systems
# ----------------------------------------------------------------------------------------
def setup_gpio():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(relay_GPIO, GPIO.OUT, initial=webcam_ON)

# ----------------------------------------------------------------------------------------
# Cycle the power on the relay / GPIO.
# The off time can be specified.  Here in secs.
#
# From a quick test, the (South) RSX-3211 webam seems to take around 32 secs to reboot.
# ----------------------------------------------------------------------------------------
def power_cycle( interval ):
	log_and_message( '...open relay contacts on BCM pin {}'.format( relay_GPIO ) )
	GPIO.output(relay_GPIO, webcam_OFF)

	sleep( interval )

	log_and_message('...close relay contacts on BCM pin {}'.format( relay_GPIO ) )
	GPIO.output(relay_GPIO, webcam_ON)

# ----------------------------------------------------------------------------------------
# Clean up any GPIO configs - typically on exit.
#
# ----------------------------------------------------------------------------------------
def destroy_gpio():
	logger("Shutting down...\n")
	GPIO.output(relay_GPIO, webcam_ON)
	GPIO.cleanup()



# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# NOTE: Most of the call to messager() should be converted to logger() at some point.
#	especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)

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
# Print and log the message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def log_and_message(message):

	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)

	FH = open(logger_file, "a")
	FH.write( "{} {}\n".format( timestamp, message) )
	FH.close

	return


# ----------------------------------------------------------------------------------------
# This prints just a symbol or two - for a progress indicator.
#
#		sys.stdout.write('.')
#		sys.stdout.flush()
# ----------------------------------------------------------------------------------------
def log_string(text):
	FH = open(logger_file, "a")
	FH.write( text )
	FH.close


# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

#	log_string( "\n\n\n\n" )
#	log_and_message("INFO: Starting {}   PID={}".format( this_script, getpid() ) )

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
		log_string( "\n" )
		logger("  Good bye from " + this_script)

	exit()

