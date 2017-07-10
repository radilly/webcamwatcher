#!/usr/bin/python

# This is a first hack to see if I can prove the concept of, basically a
# watchdog running on a Pi that will detect when images stopped uploading
# from my webcam, and then power-cycle the sucker.
#
# https://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
# Inverted signals to use the NC side of the relay...
#

import urllib
import re
import RPi.GPIO as GPIO
from time import sleep

Relay_channel = [17]
sleep_for = 150

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
	print '...Relay channel %d on' % 1
	print '...open leftmost pair of connectors.'
	GPIO.output(17, GPIO.LOW)
	sleep(2.5)
	print '...Relay channel %d off' % 1
	print '...close leftmost pair of connectors.'
	GPIO.output(17, GPIO.HIGH)

def destroy():
	print "\nShutting down..."
	GPIO.output(17, GPIO.HIGH)
	GPIO.cleanup()

def main():
	while True:
		response = urllib.urlopen('http://dillys.org/wx/N_Since_Updated.txt')
		content = response.read()
		result = re.search('(\d*) .*', content)
		result = re.search('(\d*) .* ([0-9:]*)_UTC.*', content)
		## print result.group(1)
		words = re.split(' +', content)
		## print result.group(1), words[2]
		print result.group(1), result.group(2), " UTC"
		interval = int(result.group(1))
		## print content
		if interval > 3000:
			power_cycle()
			# The the cam time to reset, and the webserver crontab to fire
			sleep(600)
		sleep(sleep_for)

if __name__ == '__main__':
	setup()
	try:
		main()
	except KeyboardInterrupt:
		destroy()

