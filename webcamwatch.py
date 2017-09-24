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
# ========================================================================================

import urllib
import re
import datetime
import RPi.GPIO as GPIO
from time import sleep
import sys
from os import getpid

Relay_channel = [17]
sleep_for = 300
sleep_on_recycle = 600 - sleep_for
log_stride = 12

# ----------------------------------------------------------------------------------------
# See https://www.sunfounder.com/modules/input-module/relay/2-channel-dc-5v-relay-module-with-optocoupler-low-level-trigger-expansion-board-for-arduino-uno-r3-mega-2560-1280-dsp-arm-pic-avr-stm32-raspberry-pi.html
# a and http://wiki.sunfounder.cc/index.php?title=2_Channel_5V_Relay_Module
# ----------------------------------------------------------------------------------------
def setup():
	GPIO.setwarnings(False)
	#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	#  systemd logs this on restart...
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: /home/pi/webcamwatch.py:40: RuntimeWarning: This channel is already in use, continuing anyway.  Use GPIO.setwarnings(False) to disable warnings.
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: GPIO.setup(17, GPIO.OUT, initial=GPIO.HIGH)
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: /home/pi/webcamwatch.py:41: RuntimeWarning: This channel is already in use, continuing anyway.  Use GPIO.setwarnings(False) to disable warnings.
	#  Aug 30 13:11:50 raspberrypi_02 webcamwatch.py[14590]: GPIO.setup(18, GPIO.OUT, initial=GPIO.HIGH)
	#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
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

# ----------------------------------------------------------------------------------------
def power_cycle():
	##DEBUG## ___print '...Relay channel %d on' % 1
	##DEBUG## ___print '...open leftmost pair of connectors.'
	logger( '...open leftmost pair of connectors.')
	GPIO.output(17, GPIO.LOW)
	sleep(5)
	##DEBUG## ___print '...Relay channel %d off' % 1
	##DEBUG## ___print '...close leftmost pair of connectors.'
	logger('...close leftmost pair of connectors.')
	GPIO.output(17, GPIO.HIGH)

# ----------------------------------------------------------------------------------------
def destroy():
	##DEBUG## ___print "\nShutting down..."
	logger("Shutting down...\n")
	GPIO.output(17, GPIO.HIGH)
	GPIO.cleanup()

# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
	FH = open("./webcamwatch.txt", "a")
	FH.write(timestamp + " " + message + "\n")
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
# ----------------------------------------------------------------------------------------
def camera_down():
	iii = 0
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
	if 0 == iii % log_stride:
		logger(words[0] + " " + words[2])
	iii += 1

	##### interval = int(result.group(1))
	interval = int(words[0])
	if interval > 3000:
		power_cycle()
		logger(words[0] + " " + words[2] + " power cycled")
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
	iii = 0
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

