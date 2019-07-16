#!/usr/bin/python -u
#
# Script to operate a relay - for the moment controlling a rope light on our deck.
#
#
# ========================================================================================
# 20190716 RAD Cleaned up and checked into git.
#
# 20180728 RAD Hacked webcamimager.py 
#
# ========================================================================================

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .


# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
import datetime
from time import sleep
import sys
from os import getpid
import re

import RPi.GPIO as GPIO

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#  NOTE: The relay GPIO port should be externalized.  NOW HARD-WIRED FOR South camera.
#
#  NOTE: For the SunFounder Relay Module, there's sort of a double negative at work.
#     It is active low, so by default you might think GPIO.LOW.
#
#     But ... We are using the NC contacts of the relay so that, with the module
#     unpowered, the webcam gets power.  Power-cycling means energizing the relay
#     briefly by driving the input pin low.
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

relay_GPIO = 18
webcam_ON = GPIO.HIGH
webcam_OFF = GPIO.LOW

this_script = sys.argv[0]
logger_file = re.sub('\.py', '.log', this_script)

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"



# ========================================================================================

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
	GPIO.setup(relay_GPIO, GPIO.OUT, initial=webcam_ON)



# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# NOTE: Most of the call to messager() should be converted to logger() at some point.
#       especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)

	FH = open(logger_file, "a")
	FH.write( "{} {}\n".format( timestamp, message) )
	FH.close

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
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def log_and_message(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)

	FH = open(logger_file, "a")
	FH.write( "{} {}\n".format( timestamp, message) )
	FH.close








# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def parse_state( state_txt ) :

	relay_state = webcam_OFF

	if "off" in state_txt :
		relay_state = webcam_OFF
		logger("INFO: Turning relay off." )
	elif "on" in state_txt :
		relay_state = webcam_ON
		logger("INFO: Turning relay on." )
	else :
		relay_state = webcam_ON
		logger("INFO: State given is \"{}\".  Defaulting to turning relay on." )

	return relay_state


# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
	#### This might be useful...
	#### if sys.argv[1] = "stop"
	log_string( "\n\n" )
	logger("INFO: Starting {}   PID={}".format( this_script,getpid() ) )

	setup_gpio()

	if len(sys.argv) < 2 :
		relay_state = webcam_OFF
		logger("INFO: Turning relay off." )
	elif "txt" in sys.argv[1] :

		FH = open(sys.argv[1], "r")
		content = FH.readlines()
		FH.close
		for iii in range( len(content) ) :
			## line = re.split(' \n', content[iii] )
			line = content[iii].strip("\n")
			logger("INFO: read \"{}\".".format( line ) )

			if r'#' in line :
				continue

			tok = re.split(' *', line)
			if len(tok) < 2 :
				continue

			relay_state = parse_state( tok[0] )
			GPIO.output( relay_GPIO, relay_state )

			logger("INFO: sleep {} sec.".format( tok[1] ) )
			sleep( float( tok[1] ) )

	else :
		relay_state = parse_state( sys.argv[1] )
		GPIO.output( relay_GPIO, relay_state )



	exit()
	exit()

