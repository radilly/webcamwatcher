#!/usr/bin/python -u
# @@@ ... 
# 
#    Intended to be run from cron
#
#       */5 * * * * /home/pi/webcamwatcher/pinger.py
#
# ========================================================================================
#
# 20201014 RAD Coded this up for checking for hosted server outages.  Not sure how
#              valid it is. Regularly sees "subprocess.CalledProcessError"
#
# ========================================================================================

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#  https://docs.python.org/2/library/subprocess.html
#  https://pypi.org/project/subprocess32/
#  http://www.pythonforbeginners.com/os/subprocess-for-system-administrators
#  https://pythonspot.com/python-subprocess/
#  http://stackabuse.com/pythons-os-and-subprocess-popen-commands/
#  https://stackoverflow.com/questions/40222793/python-subprocess-check-output-stderr-usage
#
#  Both of these are used, but probabably not very well
#      subprocess.check_call()
#      subprocess.check_output()
#
#  This seemed to do what I usually want.  The shell=True clause is not used, but ...?
#      convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT )
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import subprocess
# check_output
# check_call


# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
import datetime
import sys
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#  In this code I use os.path.isfile() in a few places.  Actually os.path.exists() might
#  be a better choice for the way I use it, however may be affected by permissions. I was
#  trying to figure out if there is a better, more specific way to import this, but did
#  not find a definitive answer.
#
#   https://docs.python.org/2/library/os.path.html
#   https://docs.python.org/2/tutorial/modules.html#packages
#   http://thomas-cokelaer.info/tutorials/python/module_os.html
#   http://effbot.org/librarybook/os-path.htm
#   https://stackoverflow.com/questions/2724348/should-i-use-import-os-path-or-import-os
#
# from os.path import isfile
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import os
from urllib2 import urlopen, URLError, HTTPError
import re



this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( os.getcwd(), re.sub('^\./', '', this_script) )

logger_file = re.sub('\.py', '.log', this_script)



# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"
WEB_URL = "http://dilly.family/wx"




# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():

#   --- dilly.family ping statistics ---
#   1 packets transmitted, 1 received, 0% packet loss, time 0ms
#   rtt min/avg/max/mdev = 87.728/87.728/87.728/0.000 ms

	output = "|"
	convert = ""
	convert_cmd = ['/bin/ping',
			"-c",
			"1",
			"dilly.family" ]
	try :
		response = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT )
	except:
		logger( "ERROR: Unexpected ERROR in ping: {}".format( sys.exc_info()[0] ) )
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		for line in sys.exc_info :
			logger( line )
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		logger( "ERROR: Unexpected ERROR in ping: {}".format( sys.exc_info() ) )
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Generally nothing, unless -verbose is used...
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#	if len(response) > 0 :
#		logger( "WARNING: ping returned data: \"{}\"".format( response ) )
#	else :
#		logger( "DEBUG: response returned data: \"{}\"".format( response ) )


	line = re.split('\n', response)
	# tok = re.split(' *', line[0])
#	while line < len( file_list ) :
#		if "snapshot-" not in file_list[line] :
#			file_list.pop(line)
#		else :
#			line += 1

	for lll in line :
		if "icmp_seq" in lll :
#			print lll
			output = output + lll + "|"
		if "packets" in lll :
#			print lll
			output = output + lll + "|"
#---#		if "rtt min" in lll :
#			print lll
#---#			output = output + lll + "|"

		# parameter[p]=parameter[p].split("#",1)[0].strip() # To get rid of inline comments

	logger( output )

	exit();


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


