#!/usr/bin/python -u
# @@@ ... Restart using...
#
#   kill -9 `cat ./statuscollector.PID`
#
#   nohup /usr/bin/python -u ./statuscollector.py /mnt/root/home/pi/status &
#
# ----------------------------------------------------------------------------------------
#  * NOTE: Need to limit the size of the page, and create a "previous" page if pruning...
#  * NOTE: Need forward and backward links.
#
# ----------------------------------------------------------------------------------------
#  * NOTE: Exception handling is weak / inconsistent.  Look at try - except blocks.
#  Refs:
#  https://docs.python.org/2.7/tutorial/errors.html
#  https://docs.python.org/2/library/exceptions.html
#  https://stackoverflow.com/questions/32613375/python-2-7-exception-handling-syntax
#    At the moment push_to_server() may be the best swag at it.  The connection to
#    the GoDaddy-hosted server can be flaky.  Examples:
#
# 2018/07/17 02:35:30 DEBUG: Copy /home/pi/N/North/snapshot-2018-07-17-02-35-37.jpg as N.jpg
# 2018/07/17 02:35:31 FTP Socket Error 113: No route to host
#
# ----------------------------------------------------------------------------------------
#
#   Considered using something to watch for directory changes.  Not sure it's
#   worth the complexity.  I think stat-ing the direcory is inexpensive while
#   polling.  Nevertheless, here are some references:
#
#   https://blog.philippklaus.de/2011/08/watching-directories-for-changes-using-python_-_an-overview
#   https://stackoverflow.com/questions/4708511/how-to-watch-a-directory-for-changes
#        https://github.com/seb-m/pyinotify
#   https://www.michaelcho.me/article/using-pythons-watchdog-to-monitor-changes-to-a-directory
#   http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
#   https://pypi.org/project/watchdog/0.5.4/
#   https://pypi.org/project/python-watcher/
#   https://pypi.org/project/watcher/
#   https://pypi.org/project/fs-watcher/
#   https://github.com/johnwesonga/directory-watcher/blob/master/dirwatcher.py
#   http://www.docmoto.com/support/advanced-topics/creating-a-folder-monitor-using-python/
#
# ========================================================================================
# ========================================================================================
#
#  EXTERNALIZING LOCAL SETTINGS:
#
#  exec()
#  https://docs.python.org/2.0/ref/exec.html
#
#  Best way to retrieve variable values from a text file - Python - Json
#  https://stackoverflow.com/questions/924700/best-way-to-retrieve-variable-values-from-a-text-file-python-json
#
#  https://en.wikipedia.org/wiki/YAML#Comparison_with_JSON
#  https://stackoverflow.com/questions/8525765/load-parameters-from-a-file-in-python
#  https://docs.python.org/2/library/json.html#module-json
#  https://docs.python.org/2/library/configparser.html
#
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# 20180723 RAD Hacked up webcamimager to get a start on this idea.  I have in mind to
#              collect event messages / records in a directory that can be periodically
#              stitched into a web page.  Records could be written into the directory
#              by various processes, and on different systems using FTP.
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

import ConfigParser

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
import datetime
from time import sleep
import time
import sys
from os import listdir, getpid, stat, unlink
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
from ftplib import FTP
from urllib2 import urlopen, URLError, HTTPError
import shutil
import re

import socket
import calendar

import RPi.GPIO as GPIO



# Holds the records used to build the web page.
msgqueue = {}
prev_page = ""


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
# relay_GPIO = 23
relay_GPIO = ""
relay2_GPIO = ""
webcam_ON = GPIO.HIGH
webcam_OFF = GPIO.LOW

# ========================================================================================
# ========================================================================================
# ========================================================================================
#  This needs to be parameterized if we are to support multiple web cams
#
#         work_dir = sys.argv[1]
#         main_image = sys.argv[2]
#         thumbnail_image = sys.argv[3]
#         remote_dir = sys.argv[4]
#
#  We *could* derive all of these from "South" - a single parameter.
#  But I hesitate to give up the flexibility just in case...
# ========================================================================================
# ========================================================================================
# startingpoint = sys.argv[1] if len(sys.argv) >= 2 else 'blah'
# ========================================================================================
work_dir = ""
main_image = ""
thumbnail_image = ""
remote_dir = "/home/content/b/o/b/bobdilly/html/WX"
remote_dir = "/var/chroot/home/content/92/3185192/wx"
remote_dir = ""
image_age_URL = ""

this_script = sys.argv[0]
image_data_file = re.sub('\.py', '__.dat', this_script)
logger_file = re.sub('\.py', '.log', this_script)

# Real mtime will always be larger
last_image_dir_mtime = 0.0

ftp_login = ""
ftp_password = ""
current_filename = ""

last_image_name = ""
last_timestamp = 0
last_filename = ""
catching_up = False
dot_counter = 0
sleep_for = 10

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"
wserver = "dillys.org"

# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():
	global work_dir
#	global ftp_login, ftp_password
#	global work_dir, main_image, thumbnail_image, remote_dir
#	global relay_GPIO, relay2_GPIO, webcam_ON, webcam_OFF

	if len(sys.argv) >= 2 :
		work_dir = sys.argv[1]
	else :
		log_and_message( "ERROR: working directory is a required first argument." )
		exit()

	if not os.path.isdir( work_dir ) :
		log_and_message( "ERROR: directory \"{}\" not found.".format( work_dir ) )
		exit()

	log_and_message( "DEBUG: monitoring directory \"{}\"".format( work_dir ) )



	fetch_FTP_credentials( work_dir + "/.ftp.credentials" )



	nvers = mono_version()
	log_and_message("INFO: Mono version: {}" .format( nvers ) )

	python_version = "v " + str(sys.version)
	python_version = re.sub(r'\n', r', ', python_version )
	log_and_message( "INFO: Python version: {}".format( python_version ) )

	while True:
		monitor_dir()
		sleep(sleep_for)

	exit()



# ----------------------------------------------------------------------------------------
#  Write out an events page (html table)
#
#
# ----------------------------------------------------------------------------------------
def build_events_page( msgqueue, page, prev ) :
	global work_dir
	global last_image_dir_mtime

	timestamp = datetime.datetime.now().strftime(strftime_FMT)

	FH = open( page, "w")

	FH.write( "<HEAD><TITLE>\n" )
	FH.write( "Raspberry Pi / Cumulus MX Events\n" )
	FH.write( "</TITLE></HEAD><BODY BGCOLOR=\"#555555\" TEXT=\"#FFFFFF\" LINK=\"#FFFF00\" VLINK=\"#FFBB00\" ALINK=\"#FFAAFF\"><H1 ALIGN=center>\n" )
	FH.write( "Raspberry Pi / Cumulus MX Events\n" )
	FH.write( "</H1>\n" )
	FH.write( "\n" )
	FH.write( "\n" )
#	FH.write( "<p><a href=\"NOTES.html\">My Notes</a>\n" )
#	FH.write( "\t&nbsp; &nbsp; &nbsp; - &nbsp; &nbsp; &nbsp;\n" )
#	FH.write( "\t<a href=\"events.html\">Pi Events</a>\n" )
#	FH.write( "\t&nbsp; &nbsp; &nbsp; - &nbsp; &nbsp; &nbsp;\n" )
#	FH.write( "\t<a href=\"status.html\">Pi Status</a>\n" )
#	FH.write( "\n" )
#	FH.write( "\n" )
#	FH.write( "<P><A HREF=\"events_20180630_22.html\"> Previous Log </A>\n" )
#	FH.write( "\n" )
	FH.write( "<CENTER>\n" )
	FH.write( "<TABLE BORDER=1>\n" )
	FH.write( "<TR><TH> Timestamp </TH><TH> Description </TH><TH> ID </TH></TR>\n" )
	FH.write( "\n" )

	for dkey in reversed(sorted(msgqueue.keys())) :
		FH.write( "<!-- ----------- {} ---------- -->\n".format( dkey ) )
		for jjj in range( len(msgqueue[ dkey ] ) ) :
			FH.write( msgqueue[ dkey ][jjj] )

	FH.write( "</TABLE>\n" )
	FH.write( "</CENTER>\n" )
	FH.write( "\n<P> &nbsp;\n" )

	# --------------------------------------------------------------------------------
	#  This is a placeholder.  prev, if any, will be the target page name.
	#
	#  Here we need to find the most recent chunk of history.
	# --------------------------------------------------------------------------------
	if len( prev ) > 0 :
		FH.write( "<P><A HREF=\"{}\"> Previous records </A>".format( prev ) )


	FH.write( "\n<P ALIGN=CENTER> Updated &nbsp; {}\n".format( timestamp ) )
	FH.write( "\n<P> &nbsp;\n" )
	FH.write( "\n\n" )

	FH.close

	return


# ----------------------------------------------------------------------------------------
#  This deals with the log getting too long.  >= 200 records.
#  We will chop in in half
#
#  - Find record 101.  We want to split at this record.
#  - Write from record 101 on to a file named "{}_event_status.html".format( ts ).
#     ts is the integer part of filename ts that will be first in this file.
#
#
#
# ----------------------------------------------------------------------------------------
def prune_msgqueue( ) :
	global work_dir
	global msgqueue
	global prev_page

	prevqueue = {}
	moving = False

	log_and_message( "DEBUG: in prune_msgqueue( )" )

#	return


	iii = 0
	for dkey in reversed(sorted(msgqueue.keys())) :
		iii += 1
		if iii == 101 :
			moving = True
			ts = re.sub(r'\.[0-9]+\.txt.*', r'', dkey)
			proposed_prev_page = "{}/{}_event_status.html".format( work_dir, ts )
			proposed_pp_short = "{}_event_status.html".format( ts )

		if moving :
			prevqueue[ dkey ] = msgqueue.pop( dkey )
			log_and_message( "DEBUG: prevqueue #={}".format( len(prevqueue) ) )
			unlink( "{}/{}".format( work_dir, dkey ) )

	build_events_page( prevqueue, proposed_pp_short, prev_page )

	push_to_server( proposed_prev_page, remote_dir, wserver )

	prev_page = proposed_pp_short

	return



# ----------------------------------------------------------------------------------------
#  Find the next "unprocessed" image file ... if any
#
#  Note: Would do well to break this up a little.
#
# ----------------------------------------------------------------------------------------
#  This is a section of the nohup.out file with some DEBUG statements still in place
#  06/01/2018 after the script has been running about 24 hours. There are 4 iterations
#  through the main loop below. The first and the last are the same, #1 and #4.
#
#  #1 & #4 - This case should be the least expensive type of interation. We cheat a
#       little to keep the code simple.  We're still polling, but the mtime of a
#       Unix directory (modification time) changes when a new file is written.  So we
#       only need to stat() the directory and see if the mtime changed since the last
#       check.  If the mtime is the same we just return and go back to sleep.
#       Note: There are several Python ways to wait for a directory change, e.q.
#       a file added to trigger some action.  It is interesting and effecient I
#       expect, but involves a callback and is a little complicated.
#
#  #2 - This is the periodic image processing. At present the web cam ftps a jpg
#       to the Pi every 5 minutes.  We basically upload 2 files to the hosted web
#       server, a copy of the latest image with a generic name, and a thumbnail
#       version created with "convert," which is part of imagemagick.  With the
#       sleep time at 30 seconds this fires about every 10 iterations when the
#       processing is "caught up."
#
#  #3 - This is a non-image-processing iteration. It's an artifact of the capability
#       to go into "catchup mode."  In this mode we process the backlog of files
#       which can build up while this script is *not* running.  Note that the
#       folder mtime has changed so we ran through the list of files in the folder
#       and got to the last one without find a new file.  The mtime changed because
#       of thumbnail generation which keeps is in a #2 type cycle until we hit
#       the end of the list of files.
#       Note: Consider the midnight case - when, if the tar goes well, all the
#       files in it are deleted, i.e. the number of files drops.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  1 .     .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
#    DEBUG: os.stat("South").st_mtime = 1527888257.13   Saved = 1527888257.13
#    DEBUG: bypass reading the directory... #2 directory mtime is unchanged.
#    2018/06/01 21:28:48 DEBUG: Sleep seconds = 30
#  2 .     .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
#    DEBUG: os.stat("South").st_mtime = 1527888554.81   Saved = 1527888257.13
#    DEBUG: last processed last_timestamp = 20180601172410
#    DEBUG: write ./webcamimager__.dat
#    2018/06/01 21:29:18 DEBUG: Make copy of image file South/snapshot-2018-06-01-17-29-10.jpg as NW.jpg
#    2018/06/01 21:29:18 DEBUG: Upload to server directory  South
#    2018/06/01 21:29:20 DEBUG: Create thumbnail South/NW_thumb.jpg
#    2018/06/01 21:29:20 DEBUG: Upload thumbnail South/NW_thumb.jpg  to server directory  South
#    DEBUG: day = 01
#    2018/06/01 21:29:21 DEBUG: Sleep seconds = 30
#  3 .     .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
#    DEBUG: os.stat("South").st_mtime = 1527888560.51   Saved = 1527888554.81
#    DEBUG: last processed last_timestamp = 20180601172910
#    2018/06/01 21:29:51 DEBUG: line # = 222   file_list_len = 222  (End of list.)
#    2018/06/01 21:29:51 DEBUG: Sleep seconds = 30
#  4 .     .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
#    DEBUG: os.stat("South").st_mtime = 1527888560.51   Saved = 1527888560.51
#    DEBUG: bypass reading the directory... #2 directory mtime is unchanged.
#    2018/06/01 21:30:21 DEBUG: Sleep seconds = 30
#    .
# ----------------------------------------------------------------------------------------
def monitor_dir() :
	global work_dir

	global msgqueue
	global prev_page

	global last_image_dir_mtime
	global last_timestamp


	global last_filename
	global catching_up
	global current_filename
	global dot_counter




# @@@
	# --------------------------------------------------------------------------------
	#  Check the modification time on the image directory.
	#  If it hasn't changed since our last check, just return() now.
	# --------------------------------------------------------------------------------
	image_dir_mtime = stat( work_dir ).st_mtime
	log_and_message( "DEBUG: image_dir_mtime = {}".format( image_dir_mtime ) )

	log_and_message( "INFO: Waiting a directory change" )
	while image_dir_mtime <= last_image_dir_mtime :
		log_string( "." )
		sys.stdout.write( "." )
		dot_counter += 1
		if ( dot_counter % 60 ) == 0 :
			log_and_message( "msgqueue #={}".format( len(msgqueue) ) )
#			log_string( "\n" )
#			sys.stdout.write( "\n" )
		sleep(sleep_for)
		image_dir_mtime = stat( work_dir ).st_mtime

# Messages should be named     time.time() + ".txt"
#
#	reversed(sorted(msgqueue.keys()))

	file_list = listdir( work_dir )
	file_list_len = len( file_list )
	file_list.sort()

	for iii in range( file_list_len ) :
		filename = file_list[ iii ]

		if len( prev_page ) < 5 :
			if re.match('[0-9]{8,15}_event_status.html', filename, flags=re.I) :
				found_prev_page = filename
				log_and_message( "DEBUG: found_prev_page set to {}".format( prev_page ) )

		# ------------------------------------------------------------------------
		#  Check the file to make sure its a msg we want to process.
		# ------------------------------------------------------------------------
		if not re.match('[0-9]{8,15}\.[0-9]+.txt$', filename, flags=re.I) :
			log_and_message( "DEBUG: skipping {}".format( filename ) )
			continue



		# ------------------------------------------------------------------------
		#
		#  NOTE: The test below
		#           if filename > last_timestamp :
		#  SHOULD use ts.  Of course last_timestamp should then also get a float...
		#
		# ------------------------------------------------------------------------
		ts = float(re.sub(r'\.txt.*', r'', filename))
		log_and_message( "DEBUG: ts = {}".format( ts ) )

		try :
			for_test =  msgqueue[ filename ]
###			log_and_message( "DEBUG: Already in msgqueue..." )
		except KeyError:
###			log_and_message( "DEBUG: Not found in msgqueue..." )
			# Necessary when above is commented out...
			pass

		#
		if filename > last_timestamp :
			FH = open( "{}/{}".format( work_dir, filename ), "r" )
			content = FH.readlines()
			FH.close
			msgqueue[ filename ] = content
			log_and_message( "DEBUG: {} added to msgqueue #={}".format( filename, len(msgqueue) ) )
#DEBUG#			log_and_message( msgqueue[ filename ] )
#DEBUG#			for jjj in range( len(msgqueue[ filename ] ) ) :
#DEBUG#				sys.stdout.write( "{}:  {}".format( jjj, msgqueue[ filename ][jjj] ) )
#	exit()

	last_image_dir_mtime = image_dir_mtime
	last_timestamp = filename

	events_page = "{}/event_status.html".format( work_dir )

	if len(msgqueue) >= 200 :
		prune_msgqueue( )

	if len( prev_page ) < 5 :
		prev_page = found_prev_page

	build_events_page( msgqueue, events_page, prev_page )

	push_to_server( events_page, remote_dir, wserver )

	return



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#|||
#|||
#||| Note: this comparision is just not working correctly
#||| Note: This may thwart the desire to all this script to "catch up" when we have a list of unprocessed snapshots.
#|||       Though maybe, since we always make one pass through the files at start up, if we write a thumbnail,
#|||       that will change the directory mtime, and that will trigger one more. ..... might be OK.
#|||
#||| The intent here, is to detect when the directory has change, i.e. mtime of the folder is updated.
#|||
#|||	print "DEBUG: os.stat(\"{}\").st_mtime = {}   Saved = {}".format(work_dir, image_dir_mtime, last_image_dir_mtime)
#|||	if image_dir_mtime <> last_image_dir_mtime :
#|||		print "DEBUG: bypass reading the directory... #1"
#|||		last_image_dir_mtime = image_dir_mtime
#|||		return

	if image_dir_mtime - last_image_dir_mtime == 0.0 :
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Progress indicator
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		log_string( '.' )
		dot_counter += 1
		last_image_dir_mtime = image_dir_mtime
		return

	last_image_dir_mtime = image_dir_mtime

###	print "DEBUG: last processed last_timestamp = " + last_timestamp
###	print "DEBUG: last processed filename = " + last_filename

	date_string = re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename)
###	print "DEBUG: date_string = " + date_string

	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
###	print "DEBUG: date_stamp = " + date_stamp

	last_day_code = re.sub(r'^......(..)....*', r'\1', str(last_timestamp))
###	print "DEBUG: last processed day code = " + last_day_code

	# --------------------------------------------------------------------------------
	#  Look for the most recent *unprocessed* snapshot image file.
	#  We look through all files, and examine the name-embedded timestamp by
	#  converting it to an integer to see if it is greater than the one saved
	#  from the last image processed.
	# --------------------------------------------------------------------------------
	file_list = listdir( work_dir )
	file_list_len = len( file_list )
	file_list.sort()

	digit_string = ""
	next_timestamp = 0
	line = 0
	#######################  current_filename = ""
	while next_timestamp <= last_timestamp :
		line += 1
		if line >= file_list_len :
#DEBUG#			messager( "DEBUG: file # {} of {} (last)".format( line, file_list_len ) )
			if catching_up :
				catching_up = False
				logger( "INFO: Catch-up mode off" )
			break

		if "snapshot" in file_list[line] :
			# snapshot-2018-05-23-16-57-04.jpg
			tok = re.split('-', re.sub('\.jpg', '', file_list[line]) )

			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			# May happen when webcam power-cycles, but NTP hasn't synched yet...
			# -rw-r--r-- 1 pi pi 44070 Jul 11 06:19 N/North/snapshot-1969-12-31-19-02-00.jpg
			# Because of the timezone, this is before the start of the Unix epoch!!!
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			if int(tok[1]) < 2000 :
				log_string( "||  ({})\n".format( dot_counter ) )
				dot_counter = 0
###				old_file = work_dir + '/' + file_list[line]
				old_file = file_list[line]
				logger( "WARNING: Probably webcam reboot: old file! {}".format( old_file ) )
				unlink( "{}/{}".format(work_dir, old_file ) )

			digit_string = tok[1]
			for iii in range(2, 7) :
				digit_string = digit_string + tok[iii]

			day_code = tok[3]
			next_timestamp = int(digit_string)


###			print "DEBUG: digit_string = " + digit_string
			if next_timestamp > last_timestamp :
				current_filename = file_list[line]
###				print "DEBUG: found new image file = {}".format( next_timestamp )
				break

	# --------------------------------------------------------------------------------
	#  Ended loop above for 1 of 2 reasons:
	#    We found a new, unprocessed file (same if as breaks out of loop above)
	#  ... or
	#    We ran through the snapshot files and did not find one with a newer
	#       timestamp in the name.
	# --------------------------------------------------------------------------------
	if next_timestamp > last_timestamp :
#DEBUG#		print "DEBUG: Earliest unprocessed image file is " + file_list[line]
		source_file = work_dir + '/' + file_list[line]
		target_file = work_dir + '/' + main_image

		# ------------------------------------------------------------------------
		# If we have a backlog of at least 3 files (might no be snapshots),
		# shorten the sleep time
		# ------------------------------------------------------------------------
		if (file_list_len - line) > 3 :
			log_string( "  ({})\n".format( dot_counter ) )
			dot_counter = 0
			logger( "DEBUG: file # {} of {} (Catching up)".format( line, file_list_len ) )
			logger( "DEBUG: skipping file {} processing".format( file_list[line] ) )
			catching_up = True
		else :
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Progress indicator Ending
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			log_string( "||  ({})\n".format( dot_counter ) )
			dot_counter = 0

		# ------------------------------------------------------------------------
		#  This is a strange failure mode of the web cam...    06/02/2018
		#   -rw-r--r--  1 pi pi    11576 Jun  2 01:44 snapshot-2018-06-02-01-44-13.jpg
		#   -rw-r--r--  1 pi pi    11555 Jun  2 01:49 snapshot-2018-06-02-01-49-13.jpg
		#   -rw-r--r--  1 pi pi        0 Jun  2 01:54 snapshot-2018-06-02-01-54-13.jpg
		#   -rw-r--r--  1 pi pi        0 Jun  2 01:59 snapshot-2018-06-02-01-59-13.jpg
		#
		# ------------------------------------------------------------------------
		#  2018/06/20 10:55:57 DEBUG: Create thumbnail and upload to South
		#  ......................2018/06/20 10:57:54 ...open relay contacts.
		#  2018/06/20 10:57:59 ...close relay contacts.
		#
		#  2018/06/20 10:57:59 WARNING: Skipping image file ......-57-56.jpg size = 0
		#  rm /home/pi/South/snapshot-2018-06-20-06-57-56.jpg
		#  .....||
		#  2018/06/20 10:58:35 DEBUG: Copy ......-58-32.jpg as S.jpg
		# ------------------------------------------------------------------------

		if catching_up :
			jpg_size = stat( source_file ).st_size
		else :
			jpg_size = check_stable_size( source_file )


		# ------------------------------------------------------------------------
		# This is used when I need to test a software change on a second Pi for
		# processing webcam images.  Yesterday I used this when I was building
		# a larger SD card for 2 purposes:
		# * To (briefly) test that this script would run (all prereqs met)
		# * To accumulate the full days images to support midnight processing
		# ------------------------------------------------------------------------
		# push_to_test(source_file, work_dir)
		# logger( "DEBUG: FTP'ing {} to Pi 03 {}".format( source_file, work_dir ) )


		if jpg_size < 500 :
			log_string( "    ({})\n".format( dot_counter ) )
			dot_counter = 0
			power_cycle( 5 )
			logger( "WARNING: Skipping image file {} size = {}".format( source_file, jpg_size ) )

			try:
				subprocess.check_output("rm {}/{}".format( work_dir, file_list[line] ), shell=True)
			except :
				logger( "ERROR: Unexpected ERROR in rm: {}".format( sys.exc_info()[0] ) )
			store_file_data ( next_timestamp, file_list[line] )
			last_timestamp = next_timestamp
			# ----------------------------------------------------------------
			#  As above, there were a stack of 0-length images.  We want to get
			#  through them quickly.  The folder is "touched" so that mtime
			#  changes or we'd have to wait for the next image to be FTP'ed.
			# ----------------------------------------------------------------
			subprocess.check_output( ['/usr/bin/touch', work_dir] )
			return



		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# ------------------------------------------------------------------------
		#  This is pretty much untested.  And may cause DST issues...
		#    though we attempt to use UTC...
		# ------------------------------------------------------------------------
		#  This probably needs to go.  I copied camera_down() here from
		#  webcamwatch.py which goes out to the web server and checks the age
		#  of the last image uploaded when the cron process fires.  That script
		#  runs on a pi without the camera actually attached so we need something
		#  that acquires remote data.  Here we have dot_counter which can do
		#  the age check locally.  Still, it might be useful at this point to
		#  make sure the web server is being updated.
		#
		#
		#
		# ------------------------------------------------------------------------
		# Returns current UTC time
		epoch_now = int( time.time() )
		# This should be the file modification tim in UTC time
		epoch_file = int(stat(work_dir + '/' + current_filename).st_mtime)

###		print "DEBUG: epoch_now = {}".format( epoch_now )
###		print "DEBUG: epoch_file = {}".format( epoch_file )
###		print "DEBUG: File age = {}  catching_up = {}".format( epoch_now - epoch_file, catching_up )

		if not catching_up and ( epoch_now - epoch_file > 600 ) :
			power_cycle( 5 )

		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################
		# NOTE ###################################################################





		if not catching_up :
			logger( "DEBUG: Processing {}".format( source_file ) )
###			logger( "DEBUG: Copy {} as {}".format( source_file, main_image ) )

			shutil.copy2( source_file, target_file )
			push_to_server( target_file, remote_dir, wserver )

			thumbnail_file = work_dir + '/' + thumbnail_image

			convert = ""
#DEBUG#		messager( "DEBUG: Create thumbnail {} and upload to {}".format(thumbnail_file, remote_dir ) )
###			logger( "DEBUG: Create thumbnail and upload to {}".format( remote_dir ) )
			convert_cmd = ['/usr/bin/convert',
					work_dir + '/' + main_image,
					'-resize', '30%',
					thumbnail_file ]
			try :
				convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT )
				subprocess.check_output( ['/usr/bin/touch', work_dir] )
			except:
				logger( "ERROR: Unexpected ERROR in convert: {}".format( sys.exc_info()[0] ) )

			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			# Generally nothing, unless -verbose is used...
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			if len(convert) > 0 :
				logger( "DEBUG: convert returned data: \"" + convert + "\"" )

			push_to_server( thumbnail_file, remote_dir, wserver )
		else :
			# Necessary to keep "processing"
			subprocess.check_output( ['/usr/bin/touch', work_dir] )


		store_file_data( next_timestamp, file_list[line] )
		last_timestamp = next_timestamp

#DEBUG#		print "DEBUG: day = " + tok[3]
		if last_day_code != day_code :
			logger( "INFO: MIDNIGHT ROLLOVER!" )
			logger( "INFO: MIDNIGHT ROLLOVER!" )
			logger( "INFO: MIDNIGHT ROLLOVER!" )
			logger( "INFO: MIDNIGHT ROLLOVER!" )
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			# snapshot-2018-05-23-16-57-04.jpg
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			midnight_process(re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename))


#DEBUG#		messager( "DEBUG: last_filename = {} current_filename = {}".format( last_filename, current_filename ) )

		# First '.' right after processing is done...
		log_string( '.' )
		dot_counter += 1
		last_filename = current_filename


# ----------------------------------------------------------------------------------------
# Read the config file, and set global variables based on it.
#
# NOTE: While the flexibility to override any global may have some benefits, it's not
#       clear this shouldn't be limited to specific variables.  We do some verification
#       of the values, and in fact some of these are required or we fail to run.
# ----------------------------------------------------------------------------------------
def read_config( config_file ) :
	global work_dir, main_image, thumbnail_image, remote_dir
	global ftp_login, ftp_password
	global relay_GPIO, relay2_GPIO, webcam_ON, webcam_OFF

# 	# https://docs.python.org/2/library/configparser.html
	config = ConfigParser.RawConfigParser()
	# This was necessary to avoid folding variable names to all lowercase.
	# https://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
	config.optionxform = str
	config.read( config_file )
	#print config.getboolean('Settings','bla') # Manual Way to acess them

	# https://stackoverflow.com/questions/924700/best-way-to-retrieve-variable-values-from-a-text-file-python-json
	parameter=dict(config.items("webcamimager"))
	for p in parameter:
		parameter[p]=parameter[p].split("#",1)[0].strip() # To get rid of inline comments
###		print p
###		print parameter[p]

	globals().update(parameter)  #Make them availible globally


###	print "."
###	messager( "INFO: work_dir = \"{}\"".format(work_dir) )
###	messager( "INFO: main_image = \"{}\"".format(main_image) )
###	messager( "INFO: thumbnail_image = \"{}\"".format(thumbnail_image) )
###	messager( "INFO: remote_dir = \"{}\"".format(remote_dir) )
###	print "."
###	messager( "INFO: relay_GPIO = \"{}\"".format( relay_GPIO ) )
###	print "."



	if not os.path.exists( work_dir ) :
		log_and_message( "ERROR: work_dir, \"{}\" not found.".format( work_dir ) )
		exit()

	if not re.match('.+\.jpg$', main_image, flags=re.I) :
		log_and_message( "ERROR: main_image, \"{}\" not ending in .jpg.".format( main_image ) )
		exit()

	if not re.match('.+\.jpg$', thumbnail_image, flags=re.I) :
		log_and_message( "ERROR: thumbnail_image, \"{}\" not ending in .jpg.".format( main_image ) )
		exit()


	if not os.path.isfile( work_dir + "/.ftp.credentials" ) :
		log_and_message( "ERROR: work_dir, \"{}\" suspect.  {} not found.".format( work_dir + "/.ftp.credentials" ) )
		exit()


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Check the FTP credentials we read.
	#
	#  See push_to_server() which tries this in a loop... To handle GoDaddy outages.
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	fetch_FTP_credentials( work_dir + "/.ftp.credentials" )

	try :
		ftp = FTP( wserver, ftp_login, ftp_password )
	except Exception as problem :
		log_and_message( "ERROR: Unexpected ERROR in FTP connect: {}".format( sys.exc_info()[0] ) )
		log_and_message( "ERROR: FTP (connect): {}".format( problem ) )

	try :
		ftp.cwd( remote_dir )
	except :
		log_and_message( "ERROR: Unexpected ERROR in FTP cwd: {}".format( sys.exc_info()[0] ) )
		log_and_message( "ERROR: remote_dir = \"{}\" is likely bad.".format(remote_dir) )

	try :
		ftp.quit()
	except :
		log_and_message( "ERROR: Unexpected ERROR in FTP quit: {}".format( sys.exc_info()[0] ) )
		log_and_message( "ERROR: remote_dir = \"{}\" is likely bad.".format(remote_dir) )
		exit()

	try:

#DEBUG#		logger("DEBUG: reading: \"{}\"".format( image_age_URL ) )
		response = urlopen( image_age_URL )
#DEBUG#		logger("DEBUG: image age read from web: \"{}\"".format( age ) )
	except:
		log_and_message( "ERROR: Unexpected ERROR in urlopen: {}".format( sys.exc_info()[0] ) )
		log_and_message( "ERROR: image_age_URL = \"{}\" is likely bad.".format(image_age_URL) )

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# We could handle these more generally.  If a value contains digits, convert to
	# int().  If digits and a '.', use float().
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if len(relay_GPIO) > 0 :
		relay_GPIO = int( relay_GPIO )

	if len(relay2_GPIO) > 0 :
		relay2_GPIO = int( relay2_GPIO )

# ----------------------------------------------------------------------------------------
#  This pushes the specified file to the (hosted) web server via FTP.
#
#
#  FTP User: camdilly
#  FTP PWD: /home/content/b/o/b/bobdilly/html/WX
#
#  https://pythonspot.com/en/ftp-client-in-python/
#  https://docs.python.org/2/library/ftplib.html
# ----------------------------------------------------------------------------------------
def push_to_server(local_file, remote_path, server) :
	global ftp_login
	global ftp_password

	log_and_message( "DEBUG: local_file = {}   remote_path = {}   server = {}".format( local_file, remote_path, server ) )

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)
	else :
		local_file_bare = local_file


	log_and_message( "DEBUG: local_file_bare = {}".format( local_file_bare ) )

	# --------------------------------------------------------------------------------
	#  Ran into a case where the first FTP command failed...
	#
	#
	#       File "./webcamimager.py", line 492, in push_to_server
	#         ftp = FTP('dillys.org')
	#       File "/usr/lib/python2.7/ftplib.py", line 120, in __init__
	#         self.connect(host)
	#       File "/usr/lib/python2.7/ftplib.py", line 135, in connect
	#         self.sock = socket.create_connection((self.host, self.port), self.timeout)
	#       File "/usr/lib/python2.7/socket.py", line 575, in create_connection
	#         raise err
	#     socket.error: [Errno 110] Connection timed out
	#
	# See https://stackoverflow.com/questions/567622/is-there-a-pythonic-way-to-try-something-up-to-a-maximum-number-of-times
	# --------------------------------------------------------------------------------
	for iii in range(8) :
		if iii > 1 :
		# Not on first iteration.  The increase the sleep time with each iteration.
			sleep( iii * 3 )


		try :
			# ----------------------------------------------------------------
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
			#
			# Ref: https://docs.python.org/2/library/ftplib.html
			# NOTE: The login/user, and password could be given here...
			#     FTP([host[, user[, passwd[, acct[, timeout]]]]])
			#
			# ----------------------------------------------------------------
			ftp = FTP( server, ftp_login, ftp_password )
		except Exception as problem :
			logger( "ERROR: FTP (connect): {}".format( problem ) )
			continue


###		try :
###			ftp.login( ftp_login, ftp_password )


		log_and_message( "DEBUG: remote_path = {}".format( remote_path ) )


		if len( remote_path ) > 0 :
			try :
#DEBUG#				logger( "DEBUG: FTP remote cd to {}".format( remote_path ) )
				ftp.cwd( remote_path )
			except Exception as problem :
				logger( "ERROR: ftp.cwd {}".format( problem ) )
				continue


		try :
#DEBUG#			logger( "DEBUG: FTP STOR {} to  {}".format( local_file_bare, local_file) )
			ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
		except Exception as problem :
			logger( "ERROR: ftp.storbinary {}".format( problem ) )
			continue


		ftp.quit()
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Yes, that's a return that's not at the funtion end
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		return

##### -----------------------------------------------------------------------------
##### Example output.  Good message, but I had all the ftp commands in the same try
##### block so I don't know which call actually failed.
##### 2018/07/17 02:35:31 FTP Socket Error 113: No route to host
#####
#####		except socket.error, e :
#####			iii += 1
#####			logger( "FTP Socket Error {}: {}".format( e.args[0], e.args[1]) )
#####			for jjj in range(0, len(e.args)) :
#####				logger( "    {}",format( e.args[jjj] ) )
#####			# Increase the sleep time with each iteration
#####			sleep( iii * 3 )
##### -----------------------------------------------------------------------------

###		except :
###			messager( "ERROR: Unexpected ERROR in FTP: {}".format( sys.exc_info()[0] ) )
###			iii += 1
###			# Increase the sleep time with each iteration
###			sleep(iii)
#CHECK#		except socket.error, e :
#CHECK#			iii += 1
#CHECK#			print "FTP Socket Error %d: %s" % (e.args[0], e.args[1])
#CHECK#			for jjj in range(0, len(e.args) - 1) :
#CHECK#				print "    {}",format( e.args[jjj] )
			# Increase the sleep time with each iteration
#CHECK#			sleep(iii)
	return


# ----------------------------------------------------------------------------------------
#  Read the ftp_credentials_file and store the credentials for later usage.
#
#  FTP User: camdilly
#  FTP PWD: /home/content/b/o/b/bobdilly/html/WX
# ----------------------------------------------------------------------------------------
def fetch_FTP_credentials( ftp_credentials_file ) :
	global ftp_login
	global ftp_password

	FH = open(ftp_credentials_file, "r")
	response = FH.readlines()
	FH.close

	ftp_login = response[0].strip("\n")
	ftp_password = response[1].strip("\n")

	###print "DEBUG: ftp_login = " + ftp_login + "    ftp_password = " + ftp_password



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
# Write the PID of this Python script to a .PID file by the name name.
# This gets run at script start-up.
# ----------------------------------------------------------------------------------------
def write_pid_file():
	PID = str(getpid()) + "\n"
	pid_file = sys.argv[0]
	pid_file = re.sub('\.py', '.PID', pid_file)

	FH = open(pid_file, "w")
	FH.write(PID)
	FH.close


# ----------------------------------------------------------------------------------------
#  Fetch the version of mono
#
# ----------------------------------------------------------------------------------------
def mono_version():
###	global data

	try :
		response = subprocess.check_output(["/usr/bin/mono", "-V"])
		line = re.split('\n', response)
		tok = re.split(' *', line[0])
		version = tok[4]
	except:
		logger( "WARNING: From mono version check: {}".format( sys.exc_info()[0] ) )
		version = "Not found"

###	data['mono_version'] = version
	return version








# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#  Wait for ffmpeg (to complete)
#
#
# ----------------------------------------------------------------------------------------
def wait_ffmpeg() :
	delay_secs = 10
	# Total wait approximately 3 * 35 = 105 sec (15 sec shy of 2 minutes)

	for iii in range(35) :
#		messager( "DEBUG: iteration {}".format( iii ) )
		try:
			response = subprocess.check_output(["/bin/ps", "-ef"])
			line = re.split('\n', response)
		except :
			logger( "ERROR: Unexpected ERROR in ps -ef: {}".format( sys.exc_info()[0] ) )
			line = []


		for jjj in range( len(line) ) :
			if "ffmpeg" in line[jjj] :
				logger( "DEBUG: #{} delay {} sec: '{}'".format( iii, iii * delay_secs, line[jjj] ) )
				sleep( delay_secs )
				break

#		messager( "DEBUG: jjj+1 = {}  len(line) = {}".format( jjj + 1, len(line) ) )
		if jjj + 1 >= len(line) :
			return



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
#	global check_counter

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
#	##DEBUG## ___print words[0], words[2]
#
#	# Periodically put a record into the log for reference.
#	if 0 == (check_counter % log_stride) :
#		logger("INFO: image age: {}".format( age ) )
#
#	check_counter += 1

	# ================================================================================
	#
	# ================================================================================
	if age > 420 :
		logger("WARNING: image age: {}".format( age ) )
		power_cycle(5)
#		log_restart( "webcam power-cycled, interval: {}".format( age ) )
		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.
		sleep(2)
#		sleep(sleep_on_recycle)
		return 1
	else:
		return 0



# ----------------------------------------------------------------------------------------
# TEST Support
#
# 
# ----------------------------------------------------------------------------------------
def push_to_test(source_file, remote_path) :
#      source_file = work_dir + '/' + file_list[line]
	server = "192.168.1.152"
	login = "pi"
	password = "password"

	if re.search('/', source_file) :
		local_file_bare = re.sub(r'.*/', r'', source_file)

	# --------------------------------------------------------------------------------
	#
	# See https://stackoverflow.com/questions/567622/is-there-a-pythonic-way-to-try-something-up-to-a-maximum-number-of-times
	# --------------------------------------------------------------------------------
	for iii in range(8) :
		try :
			ftp = FTP( server )
			ftp.login( login, password )
			ftp.cwd( remote_path )
			ftp.storbinary('STOR ' +  local_file_bare, open(source_file, 'rb'))
			ftp.quit()
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			# Yes, that's a return that's not at the funtion end
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			return
		except socket.error, e :
			iii += 1
			print "FTP Socket Error %d: %s" % (e.args[0], e.args[1])
			for jjj in range(0, len(e.args) - 1) :
				print "    {}".format( e.args[jjj] )
			# Increase the sleep time with each iteration
			sleep(iii)
	return



# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
#  A single stat() may not be enough.  It is possible that the files is in the
#  process of being written.  In the message below we had determined that the file
#  was at least 500 bytes.  The final size was 118090. When I ran the cobert by hand...
#   /usr/bin/convert South/snapshot-2018-06-14-12-37-03.jpg -resize 30% South/SSS_thumb.jpg
#  it worked fine, so it seems convert tried to read an incomplete file.
#
#  So let's make sure the size in the same on 2 checks in a row...
#
#
#   2018/06/14 16:37:09 DEBUG: convert returned data: "convert: Premature end of JPEG file
#      `South/S.jpg' @ warning/jpeg.c/JPEGWarningHandler/352.
#
# ----------------------------------------------------------------------------------------
def check_stable_size( filename ) :

	last_size = -1
	for iii in range(15) :
		file_size = stat( filename ).st_size
		if file_size == last_size :
			break

		last_size = file_size
		if iii > 0 :
			logger( "DEBUG: check_stable_size wait #{}.  {} bytes.".format(iii+1, file_size) )
		sleep( 2 )

	return last_size



# ----------------------------------------------------------------------------------------
#  Find image from the morning and make a thumbnail of it to represent the daily video.
#  Looks for the first image with hour > 7, i.e. around the 8 o'clock hour.
#
#  date_string example = "2018-07-04" - i.e. the date part of a snapshot file.
# ----------------------------------------------------------------------------------------
def daily_thumbnail( date_string, working_dir ) :
	morning_image = ""
	thumbnail_file = ""

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	file_list = listdir( working_dir )
	file_list_len = len( file_list )
	file_list.sort()

	look_for = "snapshot-" + date_string
###	logger( "DEBUG: look_for = {}.".format( look_for ) )

	found = 0

	for iii in range(0, file_list_len ) :
###		logger( "DEBUG: file[{}] = {}.".format( iii, file_list[iii] ) )
		if look_for in file_list[iii] :
			#   snapshot-2018-07-04-13-16-34.jpg
			#                       ^^
			hh = re.sub(r'.*snapshot-....-..-..-(..).*', r'\1', file_list[iii] )
###			logger( "DEBUG: hh = {}.".format( hh ) )

			if int(hh) > 7 :
###				logger( "DEBUG: For thumbnail file[{}] = {}.".format( iii, file_list[iii] ) )
				morning_image = working_dir + '/' + file_list[iii] 
				break

	if len(morning_image) > 0 :

		# Example: 20180523 - - - (looks like a number, but a string here.)
		date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)

		thumbnail_file = arc_dir + '/' + date_stamp + "-thumb.jpg"

		convert = ""
		logger( "DEBUG: Create thumbnail {}".format( date_stamp + "-thumb.jpg" ) )
		convert_cmd = ['/usr/bin/convert',
				morning_image,
				'-resize', '20%',
				thumbnail_file ]
		logger( "DEBUG: convert cmd = \"{}\"".format( convert_cmd ) )

		try :
			convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT )
		except:
			logger( "ERROR: Unexpected ERROR in convert: {}".format( sys.exc_info()[0] ) )

	return thumbnail_file




# ----------------------------------------------------------------------------------------
# NOTE: Under development.  Eventually just delete the files, and build another mp4.
#
#
# NOTE: What I'd like to do, ideally, is vary the length of the video based on the date.
#       In the Summer we have around 15 hours of daylight here, in Winter about 9.
#       First light is maybe 30 minutes before.  I might try to approximate this.
#       Python Astral, https://astral.readthedocs.io/en/latest/ can calulate accurately
#       but I really just want to lop off the "boring" black frames at either end of the
#       day.
#
# Also see:
#     https://www.timeanddate.com/astronomy/astronomical-twilight.html
#     http://aa.usno.navy.mil/data/docs/RS_OneYear.php
#     http://aa.usno.navy.mil/cgi-bin/aa_rstablew.pl?ID=AA&year=2018&task=0&state=PA&place=Canonsburg
#     https://michelanders.blogspot.com/2010/12/calulating-sunrise-and-sunset-in-python.html
#     https://stackoverflow.com/questions/19615350/calculate-sunrise-and-sunset-times-for-a-given-gps-coordinate-within-postgresql
#
#
#    Daylight saving time 2018 in Pennsylvania began at 2:00 AM on
#    Sunday, March 11
#    and ends at 2:00 AM on
#    Sunday, November 4
#    All times are in Eastern Time.
#
#
#
#
#  date_string example = "2018-07-04" - i.e. the date part of a snapshot file.
#  working_dir example = "/home/pi/N/North"
# ----------------------------------------------------------------------------------------
def remove_night_images( date_string, working_dir ) :

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	file_list = listdir( working_dir )
	file_list.sort()
	file_list_len = len( file_list )

#REMOVE	image_index = arc_dir + '/index_to_remove-' + date_string + ".txt"
#REMOVE	FH = open(image_index, "w")

	look_for = "snapshot-" + date_string
	logger( "DEBUG: look_for = {}.".format( look_for ) )

	kept = 0
	deleted = 0

	for iii in range(0, file_list_len ) :
		if look_for in file_list[iii] :
			# file snapshot-2018-07-05-21-04-50.jpg is 12542 bytes.
			hhmm = int( re.sub( r'.*snapshot-2...-..-..-(..)-(..).*', r'\1\2', file_list[iii] ) )
			if hhmm < 500 :
				unlink( working_dir + "/" + file_list[iii] )
				deleted += 1
			elif hhmm > 2200 :
				unlink( working_dir + "/" + file_list[iii] )
				deleted += 1
			else :
				kept += 1

	found = kept + deleted
	logger( "DEBUG: remove_night_images kept {} and deleted {} of ()".format( kept, deleted, found ) )
	return found


# ----------------------------------------------------------------------------------------
#  Build a list of the days files (used as input to tar).
#
# ----------------------------------------------------------------------------------------
def daily_image_list( date_string, working_dir ) :

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	look_for = "snapshot-" + date_string

	file_list = listdir( working_dir )
	file_list_len = len( file_list )

	image_index = arc_dir + '/index-' + date_string + ".txt"
	FH = open(image_index, "w")

	found = 0
	line = 0
	while line < file_list_len :
		if look_for in file_list[line] :
			FH.write( working_dir + "/" + file_list[line] + "\n" )
			found += 1
		line += 1

	logger( "DEBUG: {} items found for index file.".format( found ) )

	FH.close

	return found



# ========================================================================================
# ----------------------------------------------------------------------------------------
#  These routines store and fetch information we need to persist between invocations
#  of this script.  This needs to track what's already been "processed."
#
#  The variable last_timestamp is initialized to 0, but otherwise hold the ts for
#  the file last processed.
#
# ----------------------------------------------------------------------------------------
def store_file_data(ts, filename) :
	global image_data_file
#DEBUG#	messager( "DEBUG: write " + image_data_file )
	FH = open(image_data_file, "w")
	FH.write( str(ts) + "\n" )
	FH.write( filename + "\n" )
	FH.close

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_ts() :
	global image_data_file
#DEBUG#	messager( "DEBUG: read " + image_data_file )
	FH = open(image_data_file, "r")
	content = FH.readlines()
	FH.close

	ts = str(content[0].strip("\n"))
	logger( "DEBUG: Stored ts = " + ts )

	return ts

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_filename() :
	global image_data_file
#DEBUG#	messager( "DEBUG: read " + image_data_file )
	FH = open(image_data_file, "r")
	content = FH.readlines()
	FH.close

	filename = str(content[1].strip("\n"))
	logger( "DEBUG: Stored filename = " + filename )

	return filename

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
	GPIO.setup(relay2_GPIO, GPIO.OUT, initial=webcam_ON)

# ----------------------------------------------------------------------------------------
# Cycle the power on the relay / GPIO.
# The off time can be specified.  Here in secs.
#
# From a quick test, the (South) RSX-3211 webam seems to take around 32 secs to reboot.
# ----------------------------------------------------------------------------------------
def power_cycle( interval ):
	logger( '...open relay contacts.')
	GPIO.output(relay_GPIO, webcam_OFF)

	sleep( interval )

	logger('...close relay contacts.')
	GPIO.output(relay_GPIO, webcam_ON)

# ----------------------------------------------------------------------------------------
# Clean up any GPIO configs - typically on exit.
#
# ----------------------------------------------------------------------------------------
def destroy_gpio():
	##DEBUG## ___print "\nShutting down..."
	logger("Shutting down...\n")
	GPIO.output(relay_GPIO, webcam_ON)
	GPIO.cleanup()


# ----------------------------------------------------------------------------------------
#  Subsequent calls find the avergae utilization since the previous call.
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def midnight_process(date_string) :
	global work_dir
	ffmpeg_failed = True
	tar_failed = True

	logger( "DEBUG: Called midnight_process( {} )".format(date_string ) )

	# Example: 20180523 - - - (looks like a number, but a string here.)
	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = work_dir + '/arc_' + yyyy
	mp4_file = "{}/{}.mp4".format( arc_dir, date_stamp )
	tar_file = arc_dir + "/arc-" + date_string + ".tgz"
# xxx
	tar_file = arc_dir + "/" + date_stamp + "_arc.tgz"

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Create tar file after some checking.
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if not os.path.exists( arc_dir ) :
		logger( "INFO: Created {}.  HAPPY NEW YEAR.".format( arc_dir) )
		os.mkdir( arc_dir, 0755 )

	if os.path.isfile( tar_file ) :
		logger( "ERROR: {} already exists.  Quitting Midnight process.".format( tar_file ) )
		return

	tar_size = tar_dailies(date_string)

	if tar_size < 0 :
		logger( "ERROR: tar_dailies() failed.  Quitting Midnight process." )
		return
	else :
		tar_failed = False


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Create thumbnail image for web pages
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	tnf = daily_thumbnail( date_string, work_dir )
	if len(tnf) > 0 :
		push_to_server( tnf, remote_dir, wserver )

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Create the full 24-hour video
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	ffmpeg_failed = generate_video( date_string, mp4_file )

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# If that succeeded, make the daylight video
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if not ffmpeg_failed :
		push_to_server( mp4_file, remote_dir, wserver )

		# Last few nights, 3 of 4 video builds seemed to end in seg faults.
		sleep( 10 )

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# To make the daylight image, delete most of the dark overnight images.
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if remove_night_images( date_string, work_dir ) < 1 :
			logger( "WARNING: Could not find images for date \"{}\"".format( date_string ) )

		mp4_file_daylight = "{}/{}_daylight.mp4".format( arc_dir, date_stamp )
		logger( "DEBUG: Building {}".format( mp4_file_daylight ) )
		ffmpeg_failed = generate_video( date_string, mp4_file_daylight )

		if not ffmpeg_failed :
			push_to_server( mp4_file_daylight, remote_dir, wserver )

	else:
		logger( "WARNING: Since building \"{}\" failed, skip daylight video build.".format( mp4_file ) )


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Cleanup the individual snapshot images for the day if things went well above...
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if tar_size <= 5000000 :
		logger( "WARNING: Tar is too small to justify deleting jpg files." )

	elif not ffmpeg_failed and not tar_failed :
		logger( "INFO: Tar is large enough to delete jpg files." )

		try:
			subprocess.check_output("rm " + work_dir + "/snapshot-" + date_string + r"*.jpg", shell=True)
		except :
			logger( "ERROR: Unexpected ERROR in rm: {}".format( sys.exc_info()[0] ) )
	else :
		logger( "WARNING: Tar is too small (or ffmpeg failed) to justify deleting jpg files." )





# ----------------------------------------------------------------------------------------
#  This handles the generate of an mp4 file
#
#  Storing 1 image every 2 minutes yields ( 60 / 2 ) * 24 = 720 frames
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def generate_video(date_string, mp4_out) :
	global work_dir

	ffmpeg_failed = True

	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
	yyyy = re.sub(r'(....).*', r'\1', date_string)

	# https://stackoverflow.com/questions/82831/how-to-check-whether-a-file-exists?rq=1
	if os.path.isfile( mp4_out ) :
		logger( "WARNING: {} already exists and will be deleted.".format ( mp4_out ) )
		unlink( mp4_out )

	logger( "DEBUG: Creating mp4 file" + mp4_out )

	cat_cmd = r"cat {}/snapshot-{}*.jpg".format( work_dir, date_string )
	logger( "DEBUG: cat_cmd = \"{}\"".format( cat_cmd ) )

	ffmpeg_opts = "-f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 "
	logger( "DEBUG: ffmpeg_opts = \"{}\"".format( ffmpeg_opts ) )

	ffmpeg_cmd = cat_cmd + r" | ffmpeg " + ffmpeg_opts + mp4_out
	logger( "DEBUG: ffmpeg_cmd = \"{}\"".format( ffmpeg_cmd ) )

	logger( "DEBUG: calling = wait_ffmpeg()" )
	wait_ffmpeg()

	log_and_message( "DEBUG: Creating mp4 using cmd: " + ffmpeg_cmd )
	ffmpeg = ""
	try:
		ffmpeg = subprocess.check_output(ffmpeg_cmd , shell=True)
		ffmpeg_failed = False
	except Exception as problem :
		log_and_message( "ERROR: Unexpected ERROR in ffmpeg: {}".format( problem ) )
		ffmpeg_failed = True
###	except CalledProcessError, EHandle:
###	except :
###		log_and_message( "ERROR: Unexpected ERROR in ffmpeg: {}".format( sys.exc_info()[0] ) )
###		ffmpeg_failed = True

	if len(ffmpeg) > 0 :
		log_and_message( "DEBUG: ffmpeg returned data: \"" + ffmpeg + "\"" )

	if ffmpeg_failed :
		logger( "WARNING: ffmpeg failed." )

	return ffmpeg_failed


# ----------------------------------------------------------------------------------------
#  This handles the tar of a daily set of image snapshots
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def tar_dailies(date_string) :
	global work_dir
	# global only technically needed if we write to variable
	tar_size = -1
	tar_failed = True

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#  Tinkered with a few ideas for tar.
	#  Could not get --directory to work as I expected from the man page.
	#  I am also a little concerned about using a wildcard with the tar command.
	#  Seems like it might be safer to build a table of files, and the -T option
	#   (as I have been doing on the hosted server).  daily_image_list() builds it.
	#
	#   tar -c -zf South/arc_2018/arc-2018-06-01.tgz -T South/arc_2018/index-2018-06-01.txt
	#   tar tzvf South/arc_2018/arc-2018-06-01.tgz | less
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
	arc_dir = work_dir + '/arc_' + yyyy
	image_index = arc_dir + '/index-' + date_string + ".txt"
	tar_file = arc_dir + "/arc-" + date_string + ".tgz"
# xxx
	tar_file = arc_dir + "/" + date_stamp + "_arc.tgz"


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#  NOTE: This is a bit draconian ... Need to think through a kinder, gentler approach
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if os.path.isfile( tar_file ) :
		logger( "ERROR: {} already exists.  Quitting tar process.".format( tar_file ) )
		return tar_size

	#
	#  The --directory flag would be elegant, if I could get it to work...
	#
	current_directory = os.getcwd()
	os.chdir( work_dir )
	

	#  Creats a list like South/arc_2018/index-2018-06-01.txt for use with -T
	nnn = daily_image_list(date_string, '.' )
	if ( nnn < 50 ) :
		logger( "WARNING: Index list looks short with {} items.".format( nn ) )
	else :
		tar_cmd = "tar -c -T " + image_index + " -zf " + tar_file

		logger( "DEBUG: Creating tar file with: " + tar_cmd )
		try:
			subprocess.check_call(tar_cmd, shell=True)
			tar_failed = False
			unlink( image_index )
		except :
			logger( "ERROR: Unexpected ERROR in tar: {}".format( sys.exc_info()[0] ) )

	try:
		tar_size = stat( tar_file ).st_size
	except :
		logger( "ERROR: Unexpected ERROR in stat: {}".format( sys.exc_info()[0] ) )
		tar_size = -1

	logger( "DEBUG: tar file size = {}".format( tar_size ) )

	os.chdir( current_directory )

	##### if not tar_failed :

	return tar_size


# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	log_string( "\n\n\n\n" )
	log_and_message("INFO: Starting {}   PID={}".format( this_script,getpid() ) )

	write_pid_file()

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


# ========================================================================================
#    * NOTE: Some Python pages I refer to
#  Regular Expressions
#  https://docs.python.org/2/library/re.html
# ========================================================================================

########################################################################################
