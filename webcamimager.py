#!/usr/bin/python -u
#@@@ ... Restart using...
# NOTE: There are still come things based on argv[0] (this_script); log, PID, image_data_file...
#   kill -9 `cat /home/pi/N/webcamimager.PID`
#   cd /home/pi/N ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/N/North N.jpg N_thumb.jpg North
#
#   kill -9 `cat /home/pi/S/webcamimager.PID`
#   cd /home/pi/S ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/S/South S.jpg S_thumb.jpg South
#
# To set the reference date back...
#     printf "20180523214508\nsnapshot-2018-05-23-21-45-08.jpg\n" > webcamimager__.dat
#
# Stop with ...
#   kill -9 `cat webcamimager.PID`
#
# Start with ...
#   nohup /usr/bin/python -u /home/pi/webcamimager.py >> /home/pi/webcamimager.log 2>&1 &
#
#    * NOTE:
#       next_image_file() could bypass some of the processing of each snapshot if
#       catching_up == True.  We DO want to handle the midnight rollover, however
#       there may not be much value in making a copy of the snapshot with the generic
#       name, creating the thumbnail, and then pushing both to the web server...
#       At least not on every iteration.  The sleep time while catching up is now 0.5.
#   Log Example:
#   .
#   2018/07/03 13:26:00 DEBUG: file # 272 of 287 (Catching up)
#   2018/07/03 13:26:00 DEBUG: Copy /home/pi/S/South/snapshot-2018-07-03-08-59-30.jpg as S.jpg
#   2018/07/03 13:26:02 DEBUG: Create thumbnail and upload to South
#   .
#   2018/07/03 13:26:04 DEBUG: file # 273 of 287 (Catching up)
#   2018/07/03 13:26:04 DEBUG: Copy /home/pi/S/South/snapshot-2018-07-03-09-01-30.jpg as S.jpg
#
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#    * NOTE: When I started this up on the North camera on Pi 03 I had to tweak / create
#            / install a few things to get going...
#       sudo apt-get install proftpd      - - - - to allow webcam to upload....
#       sudo apt-get install graphicsmagick-imagemagick-compat
#       sudo apt-get install ffmpeg       - - - - This is a fairly big package....
#       vi .ftp.credentials
#
# Need to use today's date or midnight_process() fails somewhere...
#  150  printf "20180523214508\nsnapshot-2018-05-23-21-45-08.jpg\n" > webcamimager__.dat
#  171  printf "20180616000001\nsnapshot-2018-06-16-00-00-01.jpg\n" > webcamimager__.dat
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#    * NOTE: Should look more carefully of the use of subprocess
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#
#   Images as jpg files are uploaded to a folder via ftp from the webcam.  Files
#   are name with date and time (local to the camera) in the form
#   yyyy-mm-dd-HH-MM-SS.  For example:
#
#        snapshot-2018-05-23-16-57-04.jpg
#        snapshot-2018-05-23-16-59-04.jpg
#        snapshot-2018-05-23-17-01-04.jpg
#
#        snapshot-2018-05-24-21-49-41.jpg
#        snapshot-2018-05-24-21-54-41.jpg
#        snapshot-2018-05-24-21-59-41.jpg
#
#   This script will poll for new files.
#   It can keep track of the last processed file using a stored timestamp from
#      the filename.
#   When a new file is detected, it is uploaded to the server.
#   When a day rollover is detected, the script will:
#      * Use ffmpeg to generate mp4
#      * tar up the days jpg files
#      * Create a web page to access video   <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< To be done
#      * Upload the mp4 file and web page to the server   <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< To be done
#
#   NOTE: This should be able to be run as a service. (systemctl)
#
#   NOTE: These packages are needed:
#             sudo apt-get install proftpd
#             sudo apt-get install graphicsmagick-imagemagick-compat
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
#   Considered using something to watch for directory changes.  Not sure it's
#   worth the complexity.  I think stating the direcory is inexpensive while
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
#
#   https://github.com/johnwesonga/directory-watcher/blob/master/dirwatcher.py
#
#   http://www.docmoto.com/support/advanced-topics/creating-a-folder-monitor-using-python/
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# ========================================================================================
# ========================================================================================
# ========================================================================================
# 20180702 RAD Made a stab at uploading mp4 files to the web server.  Could be broken
#              to year folders ... like arc_2018 ... but it may not be an issue...
# 20180702 RAD General cleanup...
# 20180626 RAD Getting to run this as a service.  Changed all active calls from messager()
#              to logger(). Some work on parameter parsing.
# 20180626 RAD Again convert failed to create the thumbnail from an incomplete jpg. It
#              was sleeping for 0.5 secs, but I changed to a full sec, in case the
#              the incoming FTP is "bursty."
# 20180614 RAD Ran into convert trying to create the thumbnail from an incomplete jpg.
#              Added check_stable_size() to handle this rather than a simple stat().
#              Since it is delivered asynchronously, more caution is needed.
# 20180611 RAD As luck would have it, I left a trailing blank on the tar_file name,
#              which caused the isfile() to fail last night.  The retry shut down the
#              midnight process, which is tedious, so maybe I can find a better approach.
# 20180610 RAD Ugly bug with the midnight_process(), or the call to it.  It was getting
#              last_filename passed to it, but this was only set in the first iteration
#              when is is read from a file.
# 20180604 RAD More cleanup.  Seems to be running well in my testing.  Removed a lot
#              of dead code left from watchdog.py.
# 20180603 RAD Cleaned up a bunch of stuff.
# 20180531 RAD Added gloabl catching_up, which detects when the list of files to
#              process exceeds a certain threshold (3 at this point), and reduces
#              the sleep duration during that condition.
# ========================================================================================
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
import shutil
import re

import socket
import calendar



import RPi.GPIO as GPIO
relay_GPIO = 17

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
# ========================================================================================
work_dir = ""
main_image = ""
thumbnail_image = ""
remote_dir = ""

# startingpoint = sys.argv[1] if len(sys.argv) >= 2 else 'blah'

# ========================================================================================
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
sleep_for = 5

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
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
	global ftp_login
	global ftp_password
	global work_dir, main_image, thumbnail_image, remote_dir

	# Could do this where globals are declared, but logger() isn't yet available...
	if len(sys.argv) >= 2 :
		work_dir = sys.argv[1]
		logger( "INFO: arg 1 = \"{}\" (work_dir)".format(work_dir) )
	else :
		logger( "INFO: work_dir (default) = \"{}\"".format(work_dir) )
		work_dir = "South"

	if len(sys.argv) >= 3 :
		main_image = sys.argv[2]
		logger( "INFO: arg 2 = \"{}\" (main_image)".format(main_image) )
	else :
		logger( "INFO: main_image (default) = \"{}\"".format(main_image) )
		main_image = "S.jpg"

	if len(sys.argv) >= 4 :
		thumbnail_image = sys.argv[3]
		logger( "INFO: arg 3 = \"{}\" (thumbnail_image)".format(thumbnail_image) )
	else :
		logger( "INFO: thumbnail_image (default) = \"{}\"".format(thumbnail_image) )
		thumbnail_image = "S_thumb.jpg"

	if len(sys.argv) >= 5 :
		remote_dir = sys.argv[4]
		logger( "INFO: arg 4 = \"{}\" (remote_dir)".format(remote_dir) )
	else :
		logger( "INFO: remote_dir (default) = \"{}\"".format(remote_dir) )
		remote_dir = "South"

	setup_gpio( GPIO.HIGH )

	fetch_FTP_credentials( work_dir + "/.ftp.credentials" )
	nvers = mono_version()
	messager("INFO: Mono version: {}" .format( nvers ) )
	logger("INFO: Mono version: {}" .format( nvers ) )

	python_version = "v " + str(sys.version)
	python_version = re.sub(r'\n', r', ', python_version )
	messager( "INFO: Python version: {}".format( python_version ) )
	logger( "INFO: Python version: {}".format( python_version ) )

	while True:
		next_image_file()

		if catching_up :
			duration = 0.5
		else :
			duration = sleep_for
#DEBUG#		messager( "DEBUG: Sleep {} sec.".format(duration) )
		sleep(duration)

	exit()



# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# Clean up any GPIO configs - typically on exit.
#
# ----------------------------------------------------------------------------------------
def destroy():
	##DEBUG## ___print "\nShutting down..."
	logger("Shutting down...\n")
	GPIO.output(relay_GPIO, GPIO.HIGH)
	GPIO.cleanup()

# ----------------------------------------------------------------------------------------
# Set up the GPIO.
# Caller can specify the initial state.
#
# ----------------------------------------------------------------------------------------
def setup_gpio( initial_state ):
	GPIO.setwarnings(False)
	#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	GPIO.setmode(GPIO.BCM)
	## GPIO.setup(relay_GPIO, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(relay_GPIO, GPIO.OUT, initial=initial_state)

# ----------------------------------------------------------------------------------------
# Cycle the power on the relay / GPIO.
# The off time can be specified.  Here in secs.
#
# ----------------------------------------------------------------------------------------
def power_cycle( interval ):
	### sleep(1)

	logger( '...open relay contacts.')
	GPIO.output(relay_GPIO, GPIO.LOW)

	sleep( interval )

	logger('...close relay contacts.')
	GPIO.output(relay_GPIO, GPIO.HIGH)




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
	tar_file = arc_dir + "/arc-" + date_string + ".tgz"

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



	ffmpeg_failed = generate_video(date_string)



#@@@
	if not ffmpeg_failed :
		mp4_file = arc_dir + "/" + date_stamp + ".mp4"
		push_to_server( mp4_file, remote_dir, wserver )


	if tar_size <= 5000000 :
		logger( "WARNING: Tar is too small to justify deleting jpg files." )

	# Could also check if ffmpeg worked ... but if we have a good tar file ...
	if tar_size > 5000000 and not ffmpeg_failed and not tar_failed :
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
def generate_video(date_string) :
	global work_dir

	ffmpeg_status = True

	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
	yyyy = re.sub(r'(....).*', r'\1', date_string)

	arc_dir = work_dir + '/arc_' + yyyy

	mp4_file = arc_dir + "/" + date_stamp + ".mp4"

	# https://stackoverflow.com/questions/82831/how-to-check-whether-a-file-exists?rq=1
	if os.path.isfile( mp4_file ) :
		logger( "WARNING: {} already exists and will be deleted.".format ( mp4_file ) )
		unlink( mp4_file )

	logger( "DEBUG: Creating mp4 file" + mp4_file )

	cat_cmd = r"cat {}/snapshot-{}*.jpg".format( work_dir, date_string )
	logger( "DEBUG: cat_cmd = \"{}\"".format( cat_cmd ) )

	ffmpeg_opts = "-f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 "
	logger( "DEBUG: ffmpeg_opts = \"{}\"".format( ffmpeg_opts ) )

	ffmpeg_cmd = cat_cmd + r" | ffmpeg " + ffmpeg_opts + mp4_file
	logger( "DEBUG: ffmpeg_cmd = \"{}\"".format( ffmpeg_cmd ) )

	logger( "DEBUG: calling = wait_ffmpeg()" )
	wait_ffmpeg()

	logger( "DEBUG: Creating mp4 using cmd: " + ffmpeg_cmd )
	try:
		convert = subprocess.check_output(ffmpeg_cmd , shell=True)
		ffmpeg_status = False
	except :
###	except CalledProcessError, EHandle:
		logger( "ERROR: Unexpected ERROR in ffmpeg: {}".format( sys.exc_info()[0] ) )
		ffmpeg_status = True

	if len(convert) > 0 :
		logger( "DEBUG: convert returned data: \"" + convert + "\"" )

	if ffmpeg_status :
		logger( "WARNING: ffmpeg failed." )

	return ffmpeg_status


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
	arc_dir = work_dir + '/arc_' + yyyy
	image_index = arc_dir + '/index-' + date_string + ".txt"
	tar_file = arc_dir + "/arc-" + date_string + ".tgz"


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
def next_image_file() :
	global work_dir
	global last_timestamp
	global last_filename
	global last_image_dir_mtime
	global catching_up
	global current_filename

	# Should only ever happen at startup...
	if last_timestamp == 0 :
		last_timestamp = int(get_stored_ts())
		last_filename = get_stored_filename()


	# --------------------------------------------------------------------------------
	#  Check the modification time on the image directory.
	#  If it hasn't changed since our last check, just return() now.
	# --------------------------------------------------------------------------------
	image_dir_mtime = stat( work_dir ).st_mtime

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
		log_string('.')
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
	#    We found a new, unprocedded file (same if as breaks out of loop above)
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
			log_string( "\n" )
			logger( "DEBUG: file # {} of {} (Catching up)".format( line, file_list_len ) )
			catching_up = True
		else :
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Progress indicator Ending
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			log_string( "||\n" )
###			print "||"

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

		if jpg_size < 500 :
			log_string( "\n" )
###			print ""
			power_cycle( 5 )
			logger( "WARNING: Skipping image file {} size = {}".format( source_file, jpg_size ) )
			#  These lines can be used as a shell script...
###			print "rm {}/{}".format( work_dir, file_list[line] )

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

		# ------------------------------------------------------------------------
		#  This is pretty much untested.  And may cause DST issues...
		#    though we attempt to use UTC...
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





		logger( "DEBUG: Copy {} as {}".format( source_file, main_image ) )

		shutil.copy2( source_file, target_file )
		push_to_server( target_file, remote_dir, wserver )

		thumbnail_file = work_dir + '/' + thumbnail_image

		convert = ""
#DEBUG#		messager( "DEBUG: Create thumbnail {} and upload to {}".format(thumbnail_file, remote_dir ) )
		logger( "DEBUG: Create thumbnail and upload to {}".format( remote_dir ) )
		convert_cmd = ['/usr/bin/convert',
				work_dir + '/' + main_image,
				'-resize', '30%',
				thumbnail_file ]
		try :
			convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT )
			subprocess.check_output( ['/usr/bin/touch', work_dir] )
		except:
			logger( "ERROR: Unexpected ERROR in convert: {}".format( sys.exc_info()[0] ) )

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Generally nothing, unless -verbose is used...
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if len(convert) > 0 :
			logger( "DEBUG: convert returned data: \"" + convert + "\"" )

		push_to_server( thumbnail_file, remote_dir, wserver )

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
		log_string('.')
###		sys.stdout.write('.')
###		sys.stdout.flush()
		last_filename = current_filename


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
		logger( "DEBUG: check_stable_size wait #{}.  {} bytes.".format(iii+1, file_size) )
		sleep( 1 )

	return  last_size



# ----------------------------------------------------------------------------------------
#  Build a list of the dark image files - the nighttime images.
#  These are images we want to delect if we want to generate an mp4 which just
#  covers first light to dusk using ffmpeg, which is more interesting than nighttime.
#
#
#  Could build an array with array.append() - but for not output a file...
#
# ----------------------------------------------------------------------------------------
def daylight_image_list( date_string, working_dir ) :
	# Oddly, North and South cameras would want different thresholds
	threshold = 13500

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	file_list = listdir( working_dir )
	file_list_len = len( file_list )
	file_list.sort()

	image_index = arc_dir + '/index_to_remove-' + date_string + ".txt"
	FH = open(image_index, "w")

	look_for = "snapshot-" + date_string
	logger( "DEBUG: look_for = {}.".format( look_for ) )

	found = 0

	for iii in range(0, file_list_len ) :
		logger( "DEBUG: file[{}] = {}.".format( iii, file_list[iii] ) )
		if look_for in file_list[iii] :
			file_size = stat( working_dir + '/' + file_list[iii] ).st_size
			logger( "DEBUG: file {} is {} bytes.".format( file_list[iii], file_size ) )
			if file_size > threshold :
				break
			FH.write( working_dir + "/" + file_list[iii] + "\n" )
			found += 1



	for iii in range(file_list_len - 1, -1, -1):
		logger( "DEBUG: file[{}] = {}.".format( iii, file_list[iii] ) )
		if look_for in file_list[iii] :
			file_size = stat( working_dir + '/' + file_list[iii] ).st_size
			logger( "DEBUG: file {} is {} bytes.".format( file_list[iii], file_size ) )
			if file_size > threshold :
				break
			FH.write( working_dir + "/" + file_list[iii] + "\n" )
			found += 1

	FH.close

	logger( "DEBUG: {} items found for index file.".format( found ) )

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

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)


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
	for iii in range(5) :
		try :
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
			ftp = FTP( server )
			ftp.login( ftp_login, ftp_password )
#DEBUG#			messager( "DEBUG: FTP remote cd to {}".format( remote_path ) )
			ftp.cwd( remote_path )
#DEBUG#			messager( "DEBUG: FTP STOR {} to  {}".format( local_file_bare, local_file) )
			ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
			ftp.quit()
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			# Yes, that's a return that's not at the funtion end
			# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
			return
		except socket.error, e :
			iii += 1
			logger( "FTP Socket Error {}: {}".format( e.args[0], e.args[1]) )
			for jjj in range(0, len(e.args)) :
				logger( "    {}",format( e.args[jjj] ) )
			# Increase the sleep time with each iteration
			sleep( iii * 3 )
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
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)

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
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)

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
#  Wait for ffmpeg (to complete)
#
#
# ----------------------------------------------------------------------------------------
def wait_ffmpeg() :
	delay_secs = 3
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
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
	global work_dir, main_image, thumbnail_image, remote_dir
	#### This might be useful...
	#### if sys.argv[1] = "stop"
	log_string( "\n\n\n\n" )
#	print "\n\n\n\n"
	messager("INFO: Starting " + this_script + "  PID=" + str(getpid()))
	logger("INFO: Starting " + this_script + "  PID=" + str(getpid()))


###		For testing
###	wait_ffmpeg()
###	exit()
###	daylight_image_list( "2018-06-22", "/home/pi/South" )
###	exit()

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
###		print ""
		logger("  Good bye from " + this_script)




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
#      push_to_test(source_file, "TEST")
#      messager( "DEBUG: FTP'ing {} to Pi 03 TEST".format( source_file ) )

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
#
# Variant of push_to_server(local_file, remote_path) :
def push_to_test(source_file, remote_path) :
#      source_file = work_dir + '/' + file_list[line]
       global ftp_login
       global ftp_password

       if re.search('/', source_file) :
               local_file_bare = re.sub(r'.*/', r'', source_file)

       # --------------------------------------------------------------------------------
       #
       # See https://stackoverflow.com/questions/567622/is-there-a-pythonic-way-to-try-something-up-to-a-maximum-number-of-times
       # --------------------------------------------------------------------------------
       for iii in range(5) :
               try :
                       ftp = FTP('192.168.1.152')
                       ftp.login( 'pi', 'raspberry' )
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
                               print "    {}",format( e.args[jjj] )
                       # Increase the sleep time with each iteration
                       sleep(iii)
       return

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# 06/03/2018 Midnight
#
#  ........................................
#  2018/06/04 04:03:44 DEBUG: Copy image file South/snapshot-2018-06-04-00-03-46.jpg as S.jpg and upload to South
#  2018/06/04 04:03:45 DEBUG: Create and upload thumbnail South/S_thumb.jpg to server directory South
#  INFO: MIDNIGHT ROLLOVER!
#  INFO: MIDNIGHT ROLLOVER!
#  INFO: MIDNIGHT ROLLOVER!
#  INFO: MIDNIGHT ROLLOVER!
#  2018/06/04 04:03:46 DEBUG: Creating tar file with: tar -c -T South/arc_2018/index-2018-06-03.txt -zf South/arc_2018/arc-2018-06-03.tgz
#  2018/06/04 04:03:50 DEBUG: tar file size = 15671428
#  2018/06/04 04:03:50 DEBUG: Creating mp4 fileSouth/20180603.mp4
#  2018/06/04 04:03:50 DEBUG: cat_cmd = "cat South/snapshot-2018-06-03*.jpg"
#  2018/06/04 04:03:50 DEBUG: ffmpeg_opts = "-f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 "
#  2018/06/04 04:03:50 DEBUG: ffmpeg_cmd = "cat South/snapshot-2018-06-03*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 South/20180603.mp4"
#  2018/06/04 04:03:50 DEBUG: Creating mp4 using cmd: cat South/snapshot-2018-06-03*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 South/20180603.mp4
#  ffmpeg version 3.2.10-1~deb9u1+rpt1 Copyright (c) 2000-2018 the FFmpeg developers
#    built with gcc 6.3.0 (Raspbian 6.3.0-18+rpi1) 20170516
#    configuration: --prefix=/usr --extra-version='1~deb9u1+rpt1' --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libebur128 --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libmp3lame --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-omx-rpi --enable-mmal --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libopencv --enable-libx264 --enable-shared
#    libavutil      55. 34.101 / 55. 34.101
#    libavcodec     57. 64.101 / 57. 64.101
#    libavformat    57. 56.101 / 57. 56.101
#    libavdevice    57.  1.100 / 57.  1.100
#    libavfilter     6. 65.100 /  6. 65.100
#    libavresample   3.  1.  0 /  3.  1.  0
#    libswscale      4.  2.100 /  4.  2.100
#    libswresample   2.  3.100 /  2.  3.100
#    libpostproc    54.  1.100 / 54.  1.100
#  Input #0, image2pipe, from 'pipe:':
#    Duration: N/A, bitrate: N/A
#    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 640x480, 8 fps, 8 tbr, 8 tbn, 8 tbc
#  No pixel format specified, yuvj420p for H.264 encoding chosen.
#  Use -pix_fmt yuv420p for compatibility with outdated media players.
#  [libx264 @ 0x1962db0] using cpu capabilities: ARMv6 NEON
#  [libx264 @ 0x1962db0] profile High, level 2.2
#  [libx264 @ 0x1962db0] 264 - core 148 r2748 97eaef2 - H.264/MPEG-4 AVC codec - Copyleft 2003-2016 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=6 lookahead_threads=1 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=8 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00
#  Output #0, mp4, to 'South/20180603.mp4':
#    Metadata:
#      encoder         : Lavf57.56.101
#      Stream #0:0: Video: h264 (libx264) ([33][0][0][0] / 0x0021), yuvj420p(pc), 640x480, q=-1--1, 8 fps, 16384 tbn, 8 tbc
#      Metadata:
#        encoder         : Lavc57.64.101 libx264
#      Side data:
#        cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: -1
#  Stream mapping:
#    Stream #0:0 -> #0:0 (mjpeg (native) -> h264 (libx264))
#  frame=  288 fps=9.0 q=-1.0 Lsize=    7586kB time=00:00:35.62 bitrate=1744.4kbits/s speed=1.11x
#  video:7582kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.055490%
#  [libx264 @ 0x1962db0] frame I:4     Avg QP:20.24  size: 56232
#  [libx264 @ 0x1962db0] frame P:86    Avg QP:20.98  size: 35120
#  [libx264 @ 0x1962db0] frame B:198   Avg QP:22.33  size: 22817
#  [libx264 @ 0x1962db0] consecutive B-frames:  6.2%  4.9%  4.2% 84.7%
#  [libx264 @ 0x1962db0] mb I  I16..4:  5.8% 82.0% 12.2%
#  [libx264 @ 0x1962db0] mb P  I16..4:  3.7% 51.2%  4.8%  P16..4: 15.8% 14.1%  8.4%  0.0%  0.0%    skip: 2.1%
#  [libx264 @ 0x1962db0] mb B  I16..4:  2.5% 21.6%  2.0%  B16..8: 24.1% 16.2%  6.2%  direct:21.8%  skip: 5.6%  L0:40.5% L1:33.0% BI:26.5%
#  [libx264 @ 0x1962db0] 8x8 transform intra:84.3% inter:70.2%
#  [libx264 @ 0x1962db0] coded y,uvDC,uvAC intra: 63.6% 83.5% 59.5% inter: 67.5% 78.7% 23.2%
#  [libx264 @ 0x1962db0] i16 v,h,dc,p: 44% 29% 25%  2%
#  [libx264 @ 0x1962db0] i8 v,h,dc,ddl,ddr,vr,hd,vl,hu: 22% 19% 41%  2%  3%  2%  4%  3%  4%
#  [libx264 @ 0x1962db0] i4 v,h,dc,ddl,ddr,vr,hd,vl,hu: 14% 18% 12%  7% 11%  8% 12%  7% 11%
#  [libx264 @ 0x1962db0] i8c dc,h,v,p: 54% 22% 19%  5%
#  [libx264 @ 0x1962db0] Weighted P-Frames: Y:40.7% UV:39.5%
#  [libx264 @ 0x1962db0] ref P L0: 38.3% 15.8% 19.5% 19.1%  7.3%
#  [libx264 @ 0x1962db0] ref B L0: 68.4% 24.0%  7.7%
#  [libx264 @ 0x1962db0] ref B L1: 87.4% 12.6%
#  [libx264 @ 0x1962db0] kb/s:1725.10
#  2018/06/04 04:04:22 INFO: Tar is large enough to delete jpg files.
#  2018/06/04 04:04:29 DEBUG: file # 6 of 6 (last)
