#!/usr/bin/python -u
# 
# power_cycle.py tester
#
#
#
# ----------------------------------------------------------------------------------------
# NOTE: Some pages on ssh'ing commands...
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
# 20181025 RAD Hacked this together to test power_cycle.py
#              .
#
# ========================================================================================
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import subprocess

import datetime
import sys
from os import getpid, getcwd 
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import re


cmd = "/home/pi/webcamwatcher/power_cycle.py 24"
cmd = "ssh 192.168.1.10 /sbin/ifconfig"
cmd = "ssh 192.168.1.10 /home/pi/webcamwatcher/power_cycle.py 24"
cmd = "ssh 192.168.1.152 /home/pi/webcamwatcher/power_cycle.py 18"


this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( getcwd(), re.sub('^\./', '', this_script) )

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


	process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output,stderr = process.communicate()
	status = process.poll()
	print status
	print output
#   $ ./cycle_driver.py
#   0
#   2018/10/25 19:39:07 ...open relay contacts on BCM pin 18
#   2018/10/25 19:39:12 ...close relay contacts on BCM pin 18

	exit()


#	if len(sys.argv) >= 2 :
#		cmd = int( sys.argv[1] )
#	else :
#		log_and_message( "ERROR: GPIO BCM number is a required first argument." )
#		exit()

	exit()



# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# NOTE: Most of the call to messager() should be converted to logger() at some point.
#	especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	messager(message)
	return


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
	messager(message)
	logger(message)

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

