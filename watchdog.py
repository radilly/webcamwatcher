#!/usr/bin/python

# This is a first hack to see if I can prove the concept of, basically a
# watchdog running on a Pi that will detect when images stopped uploading
# from my webcam, and then power-cycle the sucker.
#
# Posted on this to http://sandaysoft.com/forum/viewtopic.php?f=27&t=16448
#
# Invoke with ...  python -u ./webcamwatch.py 2>&1 | tee -a webcamwatch.txt
#       The -u should bypass any I/O caching
#
# https://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
# Inverted signals to use the NC side of the relay...
#
# https://stackoverflow.com/questions/21662783/linux-tee-is-not-working-with-python
# The -u option works fine.  However, sys.stdout.flush() wouldn't depend on
# the command line.  My concern though, on a Pi, is that without buffering
# you're going to hammer the SD Card over time.  Buffering might help, or
# reducing the output.
#
# ========================================================================================
# 20170712 RAD Want this to run silently (eventually), but log periodically soas
#              not to hammer the SD card.
# 20170822 RAD Posted to http://sandaysoft.com/forum/viewtopic.php?f=27&t=16448
#              about this project because I'm not sure I yet have a handle on what
#              to track.  Others may have ideas and be interested...
# ========================================================================================
#
#
#
#  https://stackoverflow.com/questions/21535467/querying-process-load-in-python
#
#  I noticed 10-12 active processes at one point when Cumulus was sluggish...
#
#
# ========================================================================================

import urllib
import re
import datetime
import RPi.GPIO as GPIO
from time import sleep
import sys

Relay_channel = [17]
sleep_for = 300
sleep_for = 24
sleep_on_recycle = 600
log_stride = 12

last_secs = 999999

### /home/pi/Cumulus_MX/DataStopped.sh
data_stop_file = "/home/pi/Cumulus_MX/web/DataStoppedT.txttmp"

def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(17, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(18, GPIO.OUT, initial=GPIO.HIGH)
	'''
	print "|=====================================================|"
	print "|         2-Channel High trigger Relay Sample         |"
	print "|-----------------------------------------------------|"
	print "|                                                     |"
	print "|          Turn 2 channels on off in orders           |"
	print "|                                                     |"
	print "|                    17 ===> IN2                      |"
	print "|                    18 ===> IN1                      |"
	print "|                                                     |"
	print "|                                           SunFounder|"
	print "|=====================================================|"
	'''

def power_cycle():
	##DEBUG## print '...Relay channel %d on' % 1
	##DEBUG## print '...open leftmost pair of connectors.'
	logger( '...open leftmost pair of connectors.')
	GPIO.output(17, GPIO.LOW)
	sleep(5)
	##DEBUG## print '...Relay channel %d off' % 1
	##DEBUG## print '...close leftmost pair of connectors.'
	logger('...close leftmost pair of connectors.')
	GPIO.output(17, GPIO.HIGH)

def destroy():
	##DEBUG## print "\nShutting down..."
	logger("Shutting down...\n")
	GPIO.output(17, GPIO.HIGH)
	GPIO.cleanup()

def logger(message):
	timestamp = datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
	FH = open("./webcamwatch.txt", "a")
	FH.write(timestamp + " " + message)
	FH.close

# ------------------------------------------------------------------------
# See if CumulusMX detected that the data from the Weather Station has
# stopped.
#   1 ==> data has stopped
#   0 ==> OK
#
# ------------------------------------------------------------------------
def ws_data_stopped():
	FH = open(data_stop_file, "r")
	data_status = int( FH.readline() )
	FH.close
	return data_status

# ------------------------------------------------------------------------
# Code on the server records checksum of the past 10 values of
#   1 ==> data has stopped
#   0 ==> OK
#
# ------------------------------------------------------------------------
def server_stalled():
	response = urllib.urlopen('http://dillys.org/wx/WS_Updates.txt')
	content = response.read()
	result = re.search('(\d*)', content)
	# The file contains at least a trailing newline ... I've not looked
	words = re.split(' +', content)
	unique_count = int(result.group(1))
	##_DEBUG_## print "wx/WS_Updates.txt = " + str( unique_count )
	if unique_count < 3 :
		return 1
	else:
		return 0


# ------------------------------------------------------------------------
def realtime_stalled():
	global last_secs
	response = urllib.urlopen('http://dillys.org/wx/realtime.txt')
	content = response.read()
	words = re.split(' +', content)

	#  -----------------------------------------------------
	#  20170815 14:38:55 Zulu
	#  server_stalled() = 0
	#  ws_data_stopped = 0
	#  Traceback (most recent call last):
  	#  File "./watchdog.py", line 166, in <module>
    	#  main()
  	#  File "./watchdog.py", line 156, in main
    	#  realtime_stalled()
  	#  File "./watchdog.py", line 124, in realtime_stalled
    	#  timestamp = words[1]
	#  IndexError: list index out of range
	#       *** File may not have been completely written
	#  -----------------------------------------------------
	if (len(words)) < 2 :
		timestamp = "00:00:00"
	else:
		timestamp = words[1]
	########## print timestamp
	words = re.split(':', timestamp)
	seconds = int(words[2]) + 60 * (int(words[1]) + (60 * int(words[0])))
	diff_secs = seconds - last_secs
	if diff_secs > 200 :
		status = "NOT UPDATED"
	else:
		status = "ok"
	print "  {}    {}    {}   {}".format(timestamp,seconds,diff_secs,status)
	last_secs = seconds

def dummy():
	response = urllib.urlopen('http://dillys.org/wx/realtime.txt')
	content = response.read()
	result = re.search('(\d*)', content)
	# The file contains at least a trailing newline ... I've not looked
	words = re.split(' +', content)
	unique_count = int(result.group(1))
	##_DEBUG_## print "wx/WS_Updates.txt = " + str( unique_count )
	if unique_count < 3 :
		return 1
	else:
		return 0


def main():
	iii = 0
	### logger("Staring " + sys.argv[0] + "\n")
	while True:
		print datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S Zulu") + \
		"    server_stalled() = " + str( server_stalled()) + \
		"    ws_data_stopped = " + str( ws_data_stopped() )
		############################################################
		###  print datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S Zulu")
		###  print "server_stalled() = " + str( server_stalled())
		###  print "ws_data_stopped = " + str( ws_data_stopped() )
		############################################################

		realtime_stalled()

		iii += 1

		sleep(sleep_for)

if __name__ == '__main__':
###	setup()
	print "Monitoring 'http://dillys.org/wx/WS_Updates.txt'"
	try:
		main()
	except KeyboardInterrupt:
		timestamp = datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
		print "\n" + timestamp + "  good bye"
#		destroy()

