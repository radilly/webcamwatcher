#!/usr/bin/python

# This is a first hack to see if I can prove the concept of, basically a
# watchdog running on a Pi that will detect when images stopped uploading
# from my webcam, and then power-cycle the sucker.
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
#              watchdog.py script which chancks a number of other things.  Not
#              clear combining these makes sense because they will drive different
#              actions.  Although both look at the web server, the actions here
#              have nothing to do with Cumulus MX.
# 20171003 RAD Mounted WX components to backing board and changed up the GPIO
#              usage.  17 and 18 were move to 20 and 21 respectively.  (These
#              are not dual-purpose pins, and who knows what we'll need later.
# ========================================================================================

import urllib
import re
import datetime
import time
import RPi.GPIO as GPIO
from time import sleep
import sys
from os import getpid

webcam_channel = 21
sleep_for = 300
sleep_on_recycle = 600 - sleep_for
log_stride = 6
log_file = ""
restart_file = ""
iii = 0

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
#  Check web cam status.
#
#
#  20180415 - Camera didn't stop, but was uploading some garbage periodically.
#  This file gets an epoch timestamp written to it when we've seen a number of 0-length
#  or rather short images uploaded from the webcam within a certain period.
#		response = urllib.urlopen('http://dillys.org/wx/N_cam_reboot_request.txt')
#
# ----------------------------------------------------------------------------------------
def camera_down():
	global iii
	NOW_SECS = int(time.time())
	try:
		response = urllib.urlopen('http://dillys.org/wx/N_Since_Updated.txt')
		content = response.read()
		# ------------------------------------------------------------------
		# The file contains at least a trailing newline ... I've not looked
		#   "545   1504095902   12:25:02_UTC "
		#
		# systemd seems to complain about urlopen failing in restart...
		#     Maybe content = "0 0 00:00:00_UTC" if urlopen fails??
		# ------------------------------------------------------------------
	except:
		content = "0 0 00:00:00_UTC "
		print "DEBUG: content = \"" + content + "\""

	words = re.split(' +', content)
	##DEBUG## ___print words[0], words[2]

	# Periodically put a record into the log for reference.
	if 0 == (iii % log_stride) :
		# logger("INFO: interval: " + words[0] + "  timestamp: " + words[2] + "  DEBUG: iii=" + str(iii) )
		logger("INFO: interval: " + words[0] + "  timestamp: " + words[2] )

	iii += 1

	##### interval = int(result.group(1))
	interval = int(words[0])
	# 20171106 - Adjusted the web cam clock for DST which tripped the old
	#            limit of 3000 secs.  4200 allows for 1 hour + 10 minutes
	#            or approximately 2 additional uploads.
	# ================================================================================
	#
	#  It might be desirable to break up the sleep_on_recycle or something
	#  so that we do more logging when the camera is not updating. This is
	#  a log fragment from when the script was failing on restart.
	#
	#     20180116 15:10:00 INFO: interval: 316  timestamp: 15:05:02_UTC
	#     20180116 16:10:03 INFO: interval: 314  timestamp: 16:10:01_UTC
	#     20180116 17:10:05 INFO: interval: 3615  timestamp: 17:05:02_UTC
	#     20180116 17:20:26 Starting /mnt/root/home/pi/webcamwatch.py  PID=11850
	#     20180116 17:20:26 INFO: interval: 4514  timestamp: 17:20:01_UTC
	#     20180116 17:20:47 Starting /mnt/root/home/pi/webcamwatch.py  PID=11857
	#     20180116 17:20:47 INFO: interval: 4514  timestamp: 17:20:01_UTC
	#
	# ================================================================================
	if interval > 4200:
		power_cycle()
		logger("WARNING: interval: " + words[0] + "  timestamp: " + words[2])
		log_restart( "webcam power-cycled, interval: " + words[0] )
		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.
		sleep(sleep_on_recycle)
		return 1
	else:
		return 0


# ----------------------------------------------------------------------------------------
def main():
	##DEBUG## ___print "Starting " + sys.argv[0] + "\n"
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

