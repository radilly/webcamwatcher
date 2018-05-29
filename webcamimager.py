#!/usr/bin/python
#
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
#     printf "20180523214508\nsnapshot-2018-05-23-21-45-08.jpg\n" > webcamimager__.dat
#
# Restart using...
#   kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u /mnt/root/home/pi/webcamimager.py >> /mnt/root/home/pi/webcamimager.log 2>&1 &
#
# Stop with ... 
#   kill -9 `cat webcamimager.PID`
#
# Start with ...
#   nohup /usr/bin/python -u /mnt/root/home/pi/webcamimager.py >> /mnt/root/home/pi/webcamimager.log 2>&1 &
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
#      * Create a web page to access video
#      * Upload the mp4 file and web page to the server
#
#   NOTE: This should be able to be run as a service. (systemctl)
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
#
#
# ========================================================================================
#              NOTE: Don't necessarily need "Cumulus MX Exception thrown (see above)"
#                    messages.  Added end message 01/08/2018.
# 20180224 RAD Had a case when the readline() in ws_data_stopped() returned ''
#              which could not be converted to an integer. Somewhat kludgy fix.
# 20170712 RAD Want this to run silently (eventually), but log periodically soas
#              not to hammer the SD card.
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

import urllib
import datetime
import time
from time import sleep
import sys
import subprocess



# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
from os import listdir
from os import getpid
import os
from ftplib import FTP
import shutil
import re


ftp_credentials_file = "/home/pi/.ftp.credentials"
ftp_login = ""
ftp_password = ""

this_script = sys.argv[0]
image_dir = "/home/pi/images"
last_image_name = ""
image_data_file = re.sub('\.py', '__.dat', this_script)
last_timestamp = 0
last_filename = ""
sleep_for = 5
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^




sleep_on_recycle = 600
# ----------------------------
#    stride    secs    minutes
#  	1	24	0.4
#       2	48	0.8
#       3	72	1.2
#       4	96	1.6
#       5	120	2
# ----------------------------
log_header_stride = 15
summary_stride = 3

last_secs = 999999          # This is a sentinel value for startup.
last_date = ""
proc_load_lim = 4.0         # See https://www.booleanworld.com/guide-linux-top-command/
mem_usage_lim = 85
ws_data_last_secs = 0       # Number of epoch secs at outage start
saved_contact_lost = -1     # Number of epoch secs when RF contact lost

BASE_DIR =              "/mnt/root/home/pi/Cumulus_MX"
data_stop_file =        BASE_DIR + "/web/DataStoppedT.txttmp"
ambient_temp_file =     BASE_DIR + "/web/ambient_tempT.txttmp"
status_page =           BASE_DIR + "/web/status.html"
events_page =           BASE_DIR + "/web/events.html"
mxdiags_dir =           BASE_DIR + "/MXdiags"

logger_file = sys.argv[0]
logger_file = re.sub('\.py', '.log', logger_file)

proc_stat_busy = -1		# Sentinal value
proc_stat_idle = -1
proc_stat_hist = []		# Holds last proc_stat_hist_n samples
proc_stat_hist_n = 10		# Control length of history array to keep

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
strftime_FMT = "%Y/%m/%d %H:%M:%S"
saved_exception_tstamp = "9999-99-9999:00:00.999:....."
saved_exception_tstamp = "X"

pcyc_holdoff_time = 0

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# This is the global data value dictionary.   This is written into by many of
# the routines which follow.
# Most of the keys map to a function name...
#
# https://www.python-course.eu/dictionaries.php
# https://docs.python.org/2/tutorial/datastructures.html#dictionaries
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
data = []
data = { 'watcher_pid' : getpid() }
data['camera_down'] = 0

data_keys = [
	"python_version",
	"webcamwatch_down"
	]
	# amb_temp   {}

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# For HTML Table-style output lines
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# https://pyformat.info/


# ----------------------------------------------------------------------------------------
# For CSV-style output line
# ----------------------------------------------------------------------------------------
#       "date-time",
CSV_keys = [
	"cmx_svc_runtime",
	"webcamwatch_down"
	]

# https://pyformat.info/
CSV_format = [
	"{:16.10f}",
	"{}",
	]

# This is used to determine which fields should trip the problem flag.
Prob_Track = [
	0,
	1,
	]


# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
def main():
	global data
	global Prob_Track

	python_version = "v " + str(sys.version)
	print "Python version = " + python_version

	push_to_server('__WORK/arc_2015/2015_missing.txt', 'North')

	exit()

	push_to_server('images/NW_thumb.jpg', 'North')

	next_image_file()
	push_image()

#####	sleep(sleep_for)


# ----------------------------------------------------------------------------------------
#  Subsequent calls find the avergae utilization since the previous call.
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def midnight_process(date_string) :
	ffmpeg_failed = False

	# Example: 20180523 - - - (looks like a number, but a string here.)
	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)

	print "DEBUG: Creating tar file"
	try:
		subprocess.check_call("tar czf images/arc-" + date_string + ".tgz images/snapshot-" + date_string + "*.jpg", shell=True)
	except :
		print "Unexpected ERROR in tar:", sys.exc_info()[0]

	tar_size = os.stat("images/arc-" + date_string + ".tgz").st_size
	print "DEBUG: taf file size = " + str(tar_size)

	# https://stackoverflow.com/questions/82831/how-to-check-whether-a-file-exists?rq=1
	if os.path.isfile("images/" + date_stamp + ".mp4") :
		print "WARNING: images/" + date_stamp + ".mp4 already exists"
		os.unlink("images/" + date_stamp + ".mp4")

	print "DEBUG: Creating mp4 file images/" + date_stamp + ".mp4"
	try:
		subprocess.check_output("cat images/snapshot-" + date_string + "*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 images/" + date_stamp + ".mp4", shell=True)
	except :
###	except CalledProcessError, EHandle:
		print "Unexpected ERROR in ffmpeg:", sys.exc_info()[0]
###		print "Unexpected ERROR in ffmpeg:", EHandle.returncode
		ffmpeg_failed = True

	if ffmpeg_failed :
		print "WARNING: ffmpeg failed."

	if tar_size <= 5000000 :
		print "WARNING: Tar is too small to justify deleting jpg files."

	# Could also check if ffmpeg worked ... but if we have a good tar file ...
	if tar_size > 5000000 :
		print "INFO: Tar is large enough to delete jpg files."

		try:
			subprocess.check_output("rm images/snapshot-" + date_string + "*.jpg", shell=True)
		except :
			print "Unexpected ERROR in rm:", sys.exc_info()[0]
	else :
		print "WARNING: Tar is too small to justify deleting jpg files."

	print "DEBUG: Exiting"
	exit()



# ----------------------------------------------------------------------------------------
#  Find the next "unprocessed" image file ... if any
#
# ----------------------------------------------------------------------------------------
def next_image_file() :

	global last_timestamp

	# Should only ever happen at startup...
	if last_timestamp == 0 :
		last_timestamp = get_stored_ts()
		last_filename = get_stored_filename()

	print "DEBUG: last processed last_timestamp = " + last_timestamp
	print "DEBUG: last processed filename = " + last_filename
	print "DEBUG: date_string = " + re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename)
	date_string = re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename)
	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
	print "DEBUG: date_stamp = " + date_stamp

	last_day_code = re.sub(r'^......(..)....*', r'\1', last_timestamp)
	print "DEBUG: last processed day code = " + last_day_code

	line = 0
	file_list = listdir( image_dir )
	file_list.sort()

	digits = 0
	while int(digits) <= int(last_timestamp) :
		line += 1
		print "DEBUG: Checking file # " + str(line) + "  " + file_list[line]

		if "snapshot" in file_list[line] :
			# snapshot-2018-05-23-16-57-04.jpg
			tok = re.split('-', re.sub('\.jpg', '', file_list[line]) )

			digits = tok[1]
			##### print "DEBUG: digits = " + digits
			for iii in range(2, 7) :
				digits = digits + tok[iii]
				##### print "DEBUG: " + str(iii) + " digits = " + digits

			day_code = tok[3]
			print "DEBUG: day = " + tok[3]
			if last_day_code != day_code :
				print "DEBUG: MIDNIGHT ROLLOVER!"
				print "DEBUG: MIDNIGHT ROLLOVER!"
				print "DEBUG: MIDNIGHT ROLLOVER!"
				print "DEBUG: MIDNIGHT ROLLOVER!"
				# snapshot-2018-05-23-16-57-04.jpg
				midnight_process(re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename))

			print "DEBUG: digits = " + digits
			if int(digits) > int(last_timestamp) :
				print "DEBUG: found new image file = " + digits
				break

###			print "DEBUG: Compare..."
###			print "DEBUG:       -  " + last_timestamp
###			print "DEBUG:       -  " + digits
			sleep(0.5)


	if int(digits) > int(last_timestamp) :
		print "DEBUG: Earliest unprocessed image file is " + file_list[line]
		store_file_data ( digits, file_list[line] )

	shutil.copy2( image_dir + '/' + file_list[line], image_dir + '/NW.jpg' )

###	convert = subprocess.check_output( ['/usr/bin/convert', 'images/NW.jpg', '-resize', '30%', 'images/NW_thumb.jpg'] )
###	convert = subprocess.check_output( ['/usr/bin/convert', 'images/NW.jpg', '-verbose', '-resize', '30%', 'images/NW_thumb.jpg', '2>&1'] )
	convert = subprocess.check_output( ['/usr/bin/convert', 'images/NW.jpg', '-verbose', '-resize', '30%', 'images/NW_thumb.jpg'] )
###	convert = re.sub('.*average: *', '', convert)
###	convert = convert.rstrip()
	messager( "DEBUG: convert data: \"" + convert + "\"" )



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
	print "DEBUG: write " + image_data_file
	FH = open(image_data_file, "w")
	FH.write( ts + "\n" )
	FH.write( filename + "\n" )
	FH.close

# ----------------------------------------------------------------------------------------
#
#@@@
# ----------------------------------------------------------------------------------------
def get_stored_ts() :
	global image_data_file
	print "DEBUG: read " + image_data_file
	FH = open(image_data_file, "r")
	content = FH.readlines()
	FH.close

	ts = str(content[0].strip("\n"))

	day_code = re.sub(r'^......(..)....*', r'\1', ts)
	print "DEBUG: read day code = " + day_code

	return ts

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_filename() :
	global image_data_file
	print "DEBUG: read " + image_data_file
	FH = open(image_data_file, "r")
	content = FH.readlines()
	FH.close

	filename = str(content[1].strip("\n"))

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
def push_to_server(local_file, remote_path) :
	global ftp_login
	global ftp_password

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)

	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	#  This should go into a separate routine, and only executed at startup
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	FH = open(ftp_credentials_file, "r")
	data = FH.readlines()
	FH.close

	ftp_login = data[0].strip("\n")
	ftp_password = data[1].strip("\n")

	###print "DEBUG: ftp_login = " + ftp_login + "    ftp_password = " + ftp_password
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


	ftp = FTP('dillys.org')
	ftp.login( ftp_login, ftp_password )

	ftp.cwd( remote_path )
	print "DEBUG: FTP PWD = " + ftp.pwd()

	ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))

	data = []
	ftp.dir(data.append)

	ftp.quit()
 
	for line in data:
		print "-", line

 
#  images/NW_thumb.jpg bobdilly@dillys.org:/home/content/b/o/b/bobdilly/html/WX


# ----------------------------------------------------------------------------------------
#
#
#  https://pythonspot.com/en/ftp-client-in-python/
#  https://docs.python.org/2/library/ftplib.html
#
#  FTP User: camdilly
#  FTP PWD: /home/content/b/o/b/bobdilly/html/WX
# ----------------------------------------------------------------------------------------
def push_image() :
	global image_data_file

	###print "DEBUG: read " + image_data_file
	FH = open(ftp_credentials_file, "r")
	data = FH.readlines()
	FH.close

	ftp_login = data[0].strip("\n")
	ftp_password = data[1].strip("\n")

	###print "DEBUG: ftp_login = " + ftp_login + "    ftp_password = " + ftp_password

	ftp = FTP('dillys.org')
	ftp.login( ftp_login, ftp_password )
	print "DEBUG: FTP PWD = " + ftp.pwd()

	ftp.retrlines('LIST')

	data = []

###	ftp.cwd('/NorthFacing/')
###	ftp.dir(data.append)



	filename = 'images/NW_thumb.jpg'
	ftp.storbinary('STOR NW_thumb.jpg', open(filename, 'rb'))


 
	ftp.quit()
 
	for line in data:
		print "-", line


#  images/NW_thumb.jpg bobdilly@dillys.org:/home/content/b/o/b/bobdilly/html/WX






# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def _____________next_image_file() :

	print "DEBUG: Earliest unprocessed image file is " + file_list[iii]

	# snapshot-2018-05-23-16-57-04.jpg
	tok = re.split('-', re.sub('\.jpg', '', file_list[iii]) )

	digits = tok[1]
	print "DEBUG: digits = " + digits
	for iii in range(2, 7) :
		digits = digits + tok[iii]
		print "DEBUG: " + str(iii) + " digits = " + digits

	print "DEBUG: digits = " + digits


#	print "get_stored_ts = " + get_stored_ts()

	store_file_data ( digits )

	print "get_stored_ts = " + get_stored_ts()

	return file_list[iii]











# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
#
#
#  To Do:
#		last_realtime() return value should be leveraged <<<  OBSOLETE???????????????
# ----------------------------------------------------------------------------------------
def main_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX():
	global data
	global Prob_Track

	python_version = "v " + str(sys.version)
	python_version = re.sub(' *\n *', '<BR>', python_version )
	python_version = re.sub(' *\(', '<BR>(', python_version )

	messager("Python version: " + str(sys.version))
	data['python_version'] = python_version

	iii = 0
	while True:
		if 0 == iii % log_header_stride:
			amb_temp()        # This won't / shouldn't change rapidly so sample periodically

			hdr = "date-time,"
			for jjj in range(0, len(CSV_keys)):
				hdr = hdr + " {},".format( CSV_keys[jjj] )

			print hdr

		# Capture the data by calling functions.  Ignore return values.
		server_stalled()
		ws_data_stopped()
		last_realtime()
		proc_load()
		proc_pct()
		mono_threads()
		mem_usage()

		CSV_rec = datetime.datetime.utcnow().strftime(strftime_FMT) + ","
		Prob_Flag = " ,"

		for jjj in range(0, len(CSV_keys)):
			format_str = " " + CSV_format[jjj] + ","
			CSV_rec = CSV_rec + format_str.format( data[CSV_keys[jjj]] )
			if Prob_Track[jjj] > 0 :
				if data[CSV_keys[jjj]] > 0 :
					Prob_Flag = " <<<<<,"

		print CSV_rec + Prob_Flag

		iii += 1
		sleep(sleep_for)






# ----------------------------------------------------------------------------------------
#  Read and parse the first line of "/proc/stat", the cpu line, and calulate the
#  average cpu utilization as a percentage.
#
#  First call is the initialization - usage since boot-up.
#  Subsequent calls find the avergae utilization since the previous call.
#
# ----------------------------------------------------------------------------------------
def proc_pct() :
	global proc_stat_busy
	global proc_stat_idle
	global proc_stat_hist
	global data

	# --------------------------------------------------------------------------------
	# Work backwards from the end of the most recent file looking for
	# one of the lines above.
	# --------------------------------------------------------------------------------

	fileHandle = open ( "/proc/stat","r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	lineList[0] = re.sub('\n', '', lineList[0])        # Remove any newline which might be left

	tok = re.split(' *', lineList[0])

	idle = int(tok[4]) + int(tok[5])
	busy = int(tok[1]) + int(tok[2]) + int(tok[3]) + int(tok[6]) + int(tok[7]) + int(tok[8])

	if proc_stat_busy < 0 :
		### print "Since last boot:  {} * 100 / {}".format( busy, idle+busy )
		### print "{:6.3f}%".format( float(busy * 100) / float(idle + busy) )
		### print "========"
		pct_util = float(busy * 100) / float(idle + busy)

	else :
		delta_busy = busy - proc_stat_busy 
		delta_idle = idle - proc_stat_idle
		timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		pct_util = float(delta_busy * 100) / float(delta_idle + delta_busy)
		### print "{} {:6.3f}%".format( timestamp, pct_util )
		# ------------------------------------------------------------------------
		# Unused for now.  Here in case we want to look at a rolling average...
		# ------------------------------------------------------------------------
		if len(proc_stat_hist) > (proc_stat_hist_n -1) :
			proc_stat_hist = proc_stat_hist[1:]
		proc_stat_hist.append( pct_util )

	proc_stat_busy = busy
	proc_stat_idle = idle
	data['proc_pct'] = pct_util
	return pct_util


# ----------------------------------------------------------------------------------------
# Count the mono threads running
# 
#  NOTE: 15 is s good number, but this seems to grow after a few weeks...
# ----------------------------------------------------------------------------------------
def mono_threads():
	global data

	PID = str( data['mono_pid'] )

	# --------------------------------------------------------------------------------
	#  This failed 01/08/18 when I restarted the "cumulusmx" service.  I reordered
	#  the calls in the do forever loop which should avoid this...
	#        Traceback (most recent call last):
	#          File "/mnt/root/home/pi/watchdog.py", line 1362, in <module>
	#            main()
	#          File "/mnt/root/home/pi/watchdog.py", line 296, in main
	#            mono_threads()
	#          File "/mnt/root/home/pi/watchdog.py", line 413, in mono_threads
	#            fileHandle = open ( "/proc/" + str(PID) + "/stat","r" )
	#        IOError: [Errno 2] No such file or directory: '/proc/540/stat'
	#
	#  We could check that we have the right process via cmdline...
	#    $ cat /proc/13899/cmdline
	#    /usr/bin/mono/mnt/root/home/pi/Cumulus_MX/CumulusMX.exe
	# --------------------------------------------------------------------------------
	fileHandle = open ( "/proc/" + str(PID) + "/stat","r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	lineList[0] = re.sub('\n', '', lineList[0])        # Remove any newline which might be left
	tok = re.split(' *', lineList[0])

	data['mono_threads'] = int(tok[19])
	return int(tok[19])


# ----------------------------------------------------------------------------------------
#
#   https://www.cyberciti.biz/faq/linux-find-out-raspberry-pi-gpu-and-arm-cpu-temperature-command/
#   https://www.raspberrypi.org/forums/viewtopic.php?t=47469
#   https://www.raspberrypi.org/forums/viewtopic.php?t=190489 - Temp and Freq !!
#   https://www.raspberrypi.org/forums/viewtopic.php?t=39953
#   https://raspberrypi.stackexchange.com/questions/56611/is-this-idle-temperature-normal-for-the-rpi-3
#
#  We could definately round this.   It appears to be quantized .... and maybe close to Farherheit
# ----------------------------------------------------------------------------------------
def read_cpu_temp():
	FH = open("/sys/class/thermal/thermal_zone0/temp", "r")
	CPU_Temp = float( FH.readline() )
	FH.close
	return CPU_Temp / 1000.0


# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# NOTE: Most of the call to messager() should be converted to logger() at some point.
#       especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)

	print timestamp + " " + message

	if 0 > 1 :
		FH = open(logger_file, "a")
		FH.write(timestamp + message + "\n")
		FH.close

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)
	print timestamp + " " + message

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
# See if CumulusMX detected that the data from the Weather Station has
# stopped.
#
# Monitor web/DataStoppedT.txt which contains only "<#DataStopped>",
# really the temp file generated with every update.  I'm not exactly sure
# what trips this flag.
#
#   1 ==> data has stopped
#   0 ==> OK
# ----------------------------------------------------------------------------------------
def ws_data_stopped():
	global data
	global ws_data_last_secs
	# Had a case where this file was empty so the string returned was "", which caused
	# a "ValueError: invalid literal for int() with base 10: ''" from readline().
	# NOTE: Here I added logic to use a -1 value, but the better answer might be
	# to try to reread the file several times, with some timeout of course.
	FH = open(data_stop_file, "r")
	text = FH.readline()
	if re.search('^[01]', text) :
		data_status = int( text )
	else:
		data_status = -1

	FH.close
	if data_status > 0 :
		if ws_data_last_secs < 1 :
			ws_data_last_secs = int( datetime.datetime.utcnow().strftime("%s") )
			# Long message the first time we see this...
			messager( "WARNING:  CumulusMX reports data_stopped (<#DataStopped> == 1).   (code 101)" )
		else:
			elapsed = int( datetime.datetime.utcnow().strftime("%s") ) -  ws_data_last_secs 
			# Short message while this status continues
			messager( "WARNING:  data_stopped ... " + str(elapsed) + " sec" )
	else:
		ws_data_last_secs = 0
	data['ws_data_stopped'] = data_status
	return data_status

# ----------------------------------------------------------------------------------------
# Code on the server records checksum of the past 12 values of realtime.txt (after
# stripping off the timestamp). WS_Updates.txt is a count of the unique checksums
# in this mini log, across the past 12 updates to realtime.txt (12 minutes).
#
# Returms:
#   1 ==> data has stopped
#   0 ==> OK
# ----------------------------------------------------------------------------------------
def server_stalled():
	global data
	# --------------------------------------------------------------------------------
	#   2017/10/11 13:01:56 GMT,  0,  0,  0,  24,   0.01,  0,  89248,  9%,  0,  0%,  46.2,  46.160,   115.1,
	#   free|945512|271656|673856|6796|55352|127056|89248|856264|102396|0|102396
	# --------------------------------------------------------------------------------
	try:
		response = urllib.urlopen('http://dillys.org/wx/WS_Updates.txt')
		content = response.read()
	except:
		print "Unexpected ERROR in server_stalled:", sys.exc_info()[0]
		content = "12"      # Assume a good answer...
	# .................................................................
	# Strip off the trailing newline which is helpf when catting on the other
	# side. This should have a value be 1 and 10 - when 10 is realy expected.
	# .................................................................
	content = content.rstrip()
	if len(content) < 1:
		messager( "DEBUG: WS_Updates.txt looks short = \"" + content.rstrip() + "\"" )

	# ...... REMOVE ...................................................
	####### result = re.search('(\d*)', content)
	####### The file contains at least a trailing newline ... I've not looked
	####### words = re.split(' +', content)
	# .................................................................
	try:
		unique_count = int(content)
		# ...... REMOVE ...........................................
		####### unique_count = int(result.group(1))
		# .........................................................
	except:
		# .........................................................
		# Big value - obvious if debugging...
		# .........................................................
		unique_count = 99
	##_DEBUG_## ___print "wx/WS_Updates.txt = " + str( unique_count )
	if unique_count < 3 :
		data['server_stalled'] = 1
		return 1
		messager( "WARNING:  unique_count =" + str(unique_count) + "; expected 12." + \
			"  realtime.txt data was not updated recently (last 45 mins)." )
	else:
		data['server_stalled'] = 0
		return 0


# ----------------------------------------------------------------------------------------
#
#     NO RETURN VALUE - Well, none that is used consistently.
#
#              Return value should be like status, 0 or 1, FALSE or TRUE
#
# ----------------------------------------------------------------------------------------
##########################################        def realtime_stalled():
def last_realtime():
	global data
	global last_secs
	global last_date
	#  ---------------------------------------------------------------------
	#  09/10/17 12:02:47 73.0 92 70.6 3.1 4.5 270 ...
	#  09/10/17 12:03:11 73.0 92 70.6 3.1 4.5 270 ...
	#  ---------------------------------------------------------------------
	try :
		response = urllib.urlopen('http://dillys.org/wx/realtime.txt')
		content = response.read()
	except:
		print "Unexpected ERROR in last_realtime:", sys.exc_info()[0]
		# --------------------------------------------------------------
		#  https://docs.python.org/2/tutorial/errors.html
		#  https://docs.python.org/2/library/sys.html
		#  https://docs.python.org/3/library/traceback.html
		#  https://docs.python.org/2/library/traceback.html
		#  
		#
		#
		#  https://stackoverflow.com/questions/8238360/how-to-save-traceback-sys-exc-info-values-in-a-variable
		# --------------------------------------------------------------
		content = "00/00/00 00:00:00 45.5 80 39.7 0.0 0.7 360 0.00 0.05 30.14 N 0 mph ..."
		messager( "DEBUG: content = \"" + content + "\" in last_realtime()" )

	words = re.split(' +', content)

	#  ---------------------------------------------------------------------
	#  20170815 14:38:55 Zulu
	#  server_stalled() = 0
	#  ws_data_stopped = 0
	#  Traceback (most recent call last):
  	#  File "./watchdog.py", line 166, in <module>
    	#  main()
  	#  File "./watchdog.py", line 156, in main
    	#  last_realtime()
  	#  File "./watchdog.py", line 124, in last_realtime
    	#  timestamp = words[1]
	#  IndexError: list index out of range
	#       *** File may not have been completely written
	#  ---------------------------------------------------------------------
	if (len(words)) < 2 :
		date_str = "00/00/00"
		timestamp = "00:00:00"
		seconds = last_secs
		diff_secs = -1
	else:
		date_str = words[0]
		ddd = re.split('/', date_str)
		timestamp = words[1]
		########## ___print timestamp
		words = re.split(':', timestamp)
		seconds = int(words[2]) + 60 * ( int(words[1]) + ( 60 * int(words[0]) ) )
		diff_secs = seconds - last_secs

	#  ---------------------------------------------------------------------
	#  date-time, server_stalled, ws_data_stopped, rf_dropped, last_realtime, proc_load, 
	#  2017/09/17 22:11:59 GMT,  0,  0,  0,  -65471,  0.0,  101244,  10%,  0,  0%,
	#  free|945512|560184|385328|6768|317368|141572|101244|844268|102396|0|102396
	#  WARNING: 65543 elapsed since realtime.txt was updated.
	#  2017/09/17 22:12:24 GMT,  0,  0,  0,  65543,  0.0,  101148,  10%,  0,  0%,
	#  free|945512|560088|385424|6768|317368|141572|101148|844364|102396|0|102396
	#  
    	#  Because above, when we get an incomplete file, lacking a timestamp
    	#  we set the time to "00:00:00" and we get a weird number for
	#  last_realtime.  The nominal value we expect is 24, or perhaps
	#  48 - 48 being the transmit interval for the remote sensors.
	#  
	#  ---------------------------------------------------------------------
	if last_secs == 999999 :
		stat_text = "ok"
		status = 0
		diff_secs = -2
	elif diff_secs > 200 :
		stat_text = "NOT UPDATED"
		status = 1
		messager( "WARNING: " + str(diff_secs) + " elapsed since realtime.txt was updated." )
	elif diff_secs < -2000 :
		stat_text = "NOT UPDATED"
		status = -1
		messager( "DEBUG: Got large negative value from record:\n\t" + content )
#		for item in content :
#			___print "    " + item
		if last_date != date_str :
			#  -----------------------------------------------------
			#  Timestamp in realtime.txt is in "local" time.
			#  -----------------------------------------------------
			messager( "DEBUG: Likely the day rolled over as save date does not match..." )
			if seconds < 300 :
				messager( "DEBUG:    ... and seconds = " + str(seconds) )
			if diff_secs == -86376 :
				messager( "DEBUG:    ... yep, the date on the Pi rolled over" )
			last_date = date_str
	else:
		stat_text = "ok"
		status = 0


	#########################  ___print "  {}    {}    {}   {}".format(timestamp,seconds,diff_secs,status)
	last_secs = seconds
	data['last_realtime'] = diff_secs
	return diff_secs       # For now we track this number. Later should return status.




# ----------------------------------------------------------------------------------------
# uptime  gives  a one line display of the following information.  The current time,
# how long the system has been running, how many users are currently logged on,  and
# the system load averages for the past 1, 5, and 15 minutes.
#   [' 08:39:19 up 3 days, 8 min,  2 users,  load average: 0.00, 0.00, 0.00\n']
#
# Could also read this from /proc/loadavg
#
# https://docs.python.org/2/library/subprocess.html
# https://docs.python.org/2/library/re.html#module-contents
# ----------------------------------------------------------------------------------------
def proc_load():
	global data
	load = subprocess.check_output('/usr/bin/uptime')
	load = re.sub('.*average: *', '', load)
	load = load.rstrip()
	# messager( "DEBUG: uptime data: \"" + load + "\"" )
	# load = re.sub(',', '', load)
	words = re.split(', ', load)
###	for iii in range(0, len(words)):
###		print "DEBUG: words[" + str(iii) + "] = \"" +  words[iii] + "\""

	cur_proc_load = float(words[0])
	proc_load_5m = float(words[1])

	if cur_proc_load > proc_load_lim :
		messager( "WARNING: \t" + \
			"proc_load_lim = " + str(proc_load_lim) + \
			"\t\t 1 minute load average = " + str(cur_proc_load) )
	data['proc_load'] = cur_proc_load
	data['proc_load_5m'] = proc_load_5m
	return cur_proc_load


	if cur_proc_load > proc_load_lim :
		messager( "WARNING: 1 minute load average = " + str(cur_proc_load) + \
			";  proc_load_lim = " + str(proc_load_lim) )
		return 1
	else:
		return 0



# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#               CURRENTLY RETURNS A STRING RATHER THAN A BINARY
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# NOTE: Data is stored into the data[] array, so this could be converted to returning
#       a binary return code.
#
# Examine the output from the free command - particularly focusing on swap usage.
# Could also read /proc/meminfo
#
# Empirically, after running about a month, it seems we start using swap a little
# at a time.  Literally a few bytes a day or half-day are added - far less than 1%
# after a week perhaps.
#
#                total       used       free     shared    buffers     cached
#   Mem:        945512     307040     638472       6768      83880     128100
#   -/+ buffers/cache:      95060     850452
#   Swap:       102396          0     102396
#
#   0  945512
#   1  311232
#   2  634280
#   3  6768
#   4  83880
#   5  128100
#   6  99252
#   7  846260
#   8  102396
#   9  0
#   10  102396
#
# See:
#   http://www.linuxatemyram.com/http://www.linuxatemyram.com/
#   http://www.linuxnix.com/find-ram-size-in-linuxunix/
#
# ----------------------------------------------------------------------------------------
def mem_usage():
	global data
	free = subprocess.check_output('/usr/bin/free')
	#                       Remove all the text portions - we want just the numbers
	free = re.sub('.*total *used *free *shared *buffers *cached\n.*Mem: *', '', free)
	free = re.sub('\n.*buffers/cache: *', ' ', free)
	free = re.sub('Swap: *', ' ', free)
	free = re.sub('\n', ' ', free)                    # Remove any newline which might be left
	free = re.sub(' +', ' ', free)                    # Reduce multiple spaces to 1
	free = re.sub(' $', '', free)                     # Trim any trailing blank
	words = re.split(' +', free)

	# free|945512|908692|36820|3732|244416|226828|437448|508064|102396|3064|99332

	if (len(words)) < 11 :
		messager( "WARNING:  Expecting 11 tokens from \"free\", but got " + str(mem_pct)  )

	### for iii in range(0, len(words)):
	### 	___print str(iii) + "  " + words[iii]

	mem_total = int(words[0])
	mem_used = int(words[1])
	mem_free = int(words[2])

	shared = words[3]
	buffers = words[4]
	cached = words[5]

	bu_ca_used = int(words[6])
	bu_ca_free = int(words[7])

	swap_total = int(words[8])
	swap_used = int(words[9])
	data['swap_used'] = swap_used
	swap_free = int(words[10])

	swap_pct = 100 * swap_used / swap_total
	data['swap_pct'] = swap_pct
	effective_used = mem_total - bu_ca_free
	data['effective_used'] = effective_used 
	mem_pct = 100 * effective_used / mem_total
	data['mem_pct'] = mem_pct
	# This was misleading...
	# mem_pct = 100 * mem_used / mem_total
	if mem_pct > mem_usage_lim :
		messager( "WARNING:  " + str(mem_pct) + "% mem in use" )

	# free = re.sub(' ', '|', free)                     # Replace each blank with a |

	cpu_temp = read_cpu_temp()
	data['cpu_temp_c'] = cpu_temp
	cpu_temp_f = ( cpu_temp * 1.8 ) + 32
	data['cpu_temp_f'] = cpu_temp_f

	return " {:6d}, {:2d}%, {:6d}, {:2d}%, {:4.1f}c, {:5.1f}f,".format(effective_used, mem_pct, swap_used, swap_pct, \
		cpu_temp, cpu_temp_f )


# ----------------------------------------------------------------------------------------
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# ----------------------------------------------------------------------------------------
def WX_RF_Restored(cur_line, lineList):
	global saved_contact_lost
	countOKs = 0
	restored = 0
	# If this is only called when an OK record is already seen, then
	# cur_line will index that record; we have 1 countOKs
	for iii in range(cur_line, (cur_line - 12), -1):
		if "Sensor contact lost" in lineList[iii] :
			restored = 0
			break
		elif "WU Response: OK: success" in lineList[iii] :
			countOKs += 1
			if countOKs > 1 :
				restored = 1
				messager( "DEBUG:  Sensor contact appears to have been restored after " + str(elapsed) + " sec  (code 116)")
				break
		else :
			messager( "DEBUG:  Sensor RF status indeterminate.")

	return restored

# ----------------------------------------------------------------------------------------
# Read the ambient temperature from "/web/ambient_tempT.txttmp"
#
# NOTE: This could just return the numeric portion, but then one would need to know
#       the units.  The "interesting metric" could be the difference between
#       ambient temp, and the temp of the processor.
#
# Returns an HTML string generated from ambient_tempT.txt which contains:
#    <#intemp> <#tempunit>
# or     
#    <#intemp> <#tempunitnodeg>
#
# ----------------------------------------------------------------------------------------
def amb_temp():
	global data
	FH = open(ambient_temp_file, "r")
	# data_string = FH.readline()
	# data_string = re.sub('\n', '', data_string)
	data_string = re.sub('\n', '', FH.readline() )
	# lines = re.split('\n', data_string)
	FH.close
	data['amb_temp'] = float( re.sub(r' .*', r'', data_string ) )
	return data_string



# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
	#### if sys.argv[1] = "stop"
	messager("  Starting " + this_script + "  PID=" + str(getpid()))

	write_pid_file()
	### cmx_svc_runtime()	# This reads the PID for the main mono process
	try:
		main()
	except KeyboardInterrupt:
		messager("  Good bye from " + this_script)
#		destroy()

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# NOTE: Examples from /mnt/root/home/pi/Cumulus_MX/MXdiags logs
