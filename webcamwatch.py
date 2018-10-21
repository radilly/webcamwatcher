#!/usr/bin/python

# This is a first hack to see if I can prove the concept of, basically a
# watchdog running on a Pi that will detect when images stopped uploading
# from my webcam, and then power-cycle the sucker.
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
# I've been thinking about separating the part that does the power-cycling, and the
# part which does the monitoring.  This is partly because I swapped locations of 2 Pis
# but not the attached webcams.
#
#
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
# Invoke with ...  python -u ./webcamwatch.py 2>&1 | tee -a webcamwatch.txt
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
# 20181018 RAD Turns out using the IP address only works for GoDaddy FTP, but not for
#              HTTP.  Also moved the weather station receiver to the master bedroom,
#              because the RF kept dropping. (Now at South webcam.)
# 20180707 RAD Cleaned up the webcam checking code, here and on the virtual web
#              server.  camera_down() is somewhat cleaned up, though at present
#              it is pretty hard-wired for the North cam.
# 20180118 RAD Added "global restart_file" to setup().  "sudo journalctl -u wxwatchdog"
#              was needed to see "IOError: [Errno 2] No such file or directory: ''",
#              that filename wasn't being setup. This in turn caused the service
#              to attempt many restarts.
# 20170711 RAD Wired up the relay board to AC and got this working with the hardware
#              by overwriting N_Since_Updated.txt to trip the power cycle.
#
# 20170712 RAD Want this to run silently (eventually), but log periodically soas
#              bot to hammer the SD card.
# 20170830 RAD Changes based on systemd experience, typically on restart. There's a
#              GPIO (warning only), and a failure in trying to read the file on the
#              web server which I wrapped in a try block...
# 20170830 RAD Moved code to camera_down() to make it easier to integrate into the
#              watchdog.py script which checks a number of other things.  Not
#              clear combining these makes sense because they will drive different
#              actions.  Although both look at the web server, the actions here
#              have nothing to do with Cumulus MX.
# 20171003 RAD Mounted WX components to backing board and changed up the GPIO
#              usage.  17 and 18 were move to 20 and 21 respectively.  (These
#              are not dual-purpose pins, and who knows what we'll need later.
# ========================================================================================

# import urllib
# https://docs.python.org/2/howto/urllib2.html
# https://docs.python.org/2/library/urllib2.html
from urllib2 import urlopen, URLError, HTTPError

import re
import datetime
import time
import RPi.GPIO as GPIO
from time import sleep
import sys
from os import getpid

webcam_channel = 21
sleep_for = 120
sleep_on_recycle = 300 ; # Leave time for the server side to pick it up...
log_stride = 2
log_file = ""
restart_file = ""
check_counter = 0

# Suggestion of GoDaddy support...
# image_age_URL = 'http://50.62.26.1/wx/North/N_age.txt'
# image_age_URL = 'http://dillys.org/wx/North/N_age.txt'
image_age_URL = 'http://dillys.org/wx/South/S_age.txt'

# ----------------------------------------------------------------------------------------
# See https://www.sunfounder.com/modules/input-module/relay/2-channel-dc-5v-relay-module-with-optocoupler-low-level-trigger-expansion-board-for-arduino-uno-r3-mega-2560-1280-dsp-arm-pic-avr-stm32-raspberry-pi.html
# a and http://wiki.sunfounder.cc/index.php?title=2_Channel_5V_Relay_Module
# ----------------------------------------------------------------------------------------
def setup():
	global log_file
	global restart_file
	GPIO.setwarnings(False)
	#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	#  systemd logs this on restart...
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: /home/pi/webcamwatch.py:40: RuntimeWarning: This channel is already in use, continuing anyway.  Use GPIO.setwarnings(False) to disable warnings.
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: GPIO.setup(17, GPIO.OUT, initial=GPIO.HIGH)
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: /home/pi/webcamwatch.py:41: RuntimeWarning: This channel is already in use, continuing anyway.  Use GPIO.setwarnings(False) to disable warnings.
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: GPIO.setup(18, GPIO.OUT, initial=GPIO.HIGH)
	#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(20, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(21, GPIO.OUT, initial=GPIO.HIGH)
	'''
	print "|=====================================================|"
	print "|         2-Channel High trigger Relay Sample         |"
	print "|-----------------------------------------------------|"
	print "|                                                     |"
	print "|          Turn 2 channels on off in orders           |"
	print "|                                                     |"
	print "|                    21 ===> IN2                      |"
	print "|                    18 ===> IN1                      |"
	print "|                                                     |"
	print "|                                           SunFounder|"
	print "|=====================================================|"
	'''

	log_file = sys.argv[0]
	log_file = re.sub('\.py', '.log', log_file)

	restart_file = sys.argv[0]
	restart_file = re.sub('\.py', '.html', restart_file)

# ----------------------------------------------------------------------------------------
def power_cycle():
	##DEBUG## ___print '...Relay channel %d on' % 1
	##DEBUG## ___print '...open leftmost pair of connectors.'
	logger( '...open leftmost pair of connectors.')
	GPIO.output(webcam_channel, GPIO.LOW)
	sleep(5)
	##DEBUG## ___print '...Relay channel %d off' % 1
	##DEBUG## ___print '...close leftmost pair of connectors.'
	logger('...close leftmost pair of connectors.')
	GPIO.output(webcam_channel, GPIO.HIGH)

# ----------------------------------------------------------------------------------------
def destroy():
	##DEBUG## ___print "\nShutting down..."
	logger("Shutting down...\n")
	GPIO.output(webcam_channel, GPIO.HIGH)
	GPIO.cleanup()

# ----------------------------------------------------------------------------------------
def logger(message):
	global log_file
	timestamp = datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
	FH = open(log_file, "a")
	FH.write(timestamp + " " + message + "\n")
	FH.close

# ----------------------------------------------------------------------------------------
# This prints just a symbol or two - for a progress indicator.
#
# ----------------------------------------------------------------------------------------
def log_string(text):
	FH = open(log_file, "a")
	FH.write( text )
	FH.close

# ----------------------------------------------------------------------------------------
def log_restart(message):
	global restart_file
	timestamp = datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S %z")
	FH = open(restart_file, "a")
	FH.write("<TR><TD> " + timestamp + " </TD><TD> " + message + "</TD></TR>\n")
	FH.close

# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
	print timestamp + " " + message


# ----------------------------------------------------------------------------------------
def write_pid_file():
	PID = str(getpid()) + "\n"
	pid_file = sys.argv[0]
	pid_file = re.sub('\.py', '.PID', pid_file)

	FH = open(pid_file, "w")
	FH.write(PID)
	FH.close

# ----------------------------------------------------------------------------------------
#  Check webcam status by fetching a control file from the hosted web-server.
#  The file just contains a number - the number of seconds between the time of
#  last writing the generically-named full-size image file, e.g. N.jpg by FTP,
#  an the current time.  Since cron_10_min.sh runs every 5 minutes
#
#   Can verify with: curl http://dillys.org/wx/North/N_age.txt
#
#  20180705 - Since moving most of the web cam image processing to the Pi, cron_10_min.sh
#  was seriously chopped down.  I also deleted a lof of the control files, including the
#  one this routine was looking at.  Oopps.  Looking at this routine, I decided it was
#  too complicated.
#
#  20180415 - Camera didn't stop, but was uploading some garbage periodically.
#  This file gets an epoch timestamp written to it when we've seen a number of 0-length
#  or rather short images uploaded from the webcam within a certain period.
#		response = urllib.urlopen('http://dillys.org/wx/N_cam_reboot_request.txt')
#
# ----------------------------------------------------------------------------------------
def camera_down():
	global check_counter

	try:

#DEBUG#		logger("DEBUG: reading: \"{}\"".format( image_age_URL ) )
		response = urlopen( image_age_URL )
		age = response.read()
#DEBUG#		logger("DEBUG: image age read from web: \"{}\"".format( age ) )
		# ------------------------------------------------------------------
		# The file contains at least a trailing newline ... I've not looked
		#   "545   1504095902   12:25:02_UTC "
		#
		# systemd seems to complain about urlopen failing in restart...
		#     Maybe content = "0 0 00:00:00_UTC" if urlopen fails??
		# ------------------------------------------------------------------
	except:
		age = "0"
		logger("WARNING: Assumed image age: {}".format( age ) )

	age = int( age.rstrip() )
	##DEBUG## ___print words[0], words[2]

	# Periodically put a record into the log for reference.
	if 0 == (check_counter % log_stride) :
		logger("INFO: image age: {}".format( age ) )

	check_counter += 1

	# ================================================================================
	#
	# ================================================================================
	if age > 600 :
		logger("WARNING: image age: {}".format( age ) )
		power_cycle()
		log_restart( "webcam power-cycled, interval: {}".format( age ) )
		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.
		sleep(sleep_on_recycle)
		return 1
	else:
		return 0


# ----------------------------------------------------------------------------------------
#
#
#
# ----------------------------------------------------------------------------------------
def main():
	##DEBUG## ___print "Starting " + sys.argv[0] + "\n"
	log_string( "\n\n\n\n" )
	logger("Starting " + sys.argv[0] +  "  PID=" + str(getpid()))
	messager("Starting " + sys.argv[0] +  "  PID=" + str(getpid()))
	write_pid_file()
	while True:
		camera_down()
		sleep(sleep_for)

# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
	setup()
	try:
		main()
	except KeyboardInterrupt:
		destroy()

