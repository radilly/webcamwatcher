#!/usr/bin/python
#
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# Restart using...
#   kill -9 `cat watchdog.PID` ; nohup /usr/bin/python -u /mnt/root/home/pi/watchdog.py >> /mnt/root/home/pi/watchdog.log 2>&1 &
#
# Stop with ... 
#   kill -9 `cat watchdog.PID`
#
# Start with ...
#   nohup /usr/bin/python -u /mnt/root/home/pi/watchdog.py >> /mnt/root/home/pi/watchdog.log 2>&1 &
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
#
#
#
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
#
#
#
#   NOTE: It would be interesting to see if we could log any "significant"
#         change to a parameter being tracked.  mono_threads comes to mind.
#         It seems to change in "jumps."  Link more than 2X in a few minutes.
#
#
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
# ========================================================================================
#      See MXdiags sample at the end of this file
# ========================================================================================
#              NOTE: Don't necessarily need "Cumulus MX Exception thrown (see above)"
#                    messages.  Added end message 01/08/2018.
# 20180224 RAD Had a case when the readline() in ws_data_stopped() returned ''
#              which could not be converted to an integer. Somewhat kludgy fix.
# 20180108 RAD When I restarted the cumulusmx service the change of PID caused a
#              failure.  cmx_svc_runtime() moved up in the do forever loop to
#              handle this case.
# 20171209 RAD Added cmx_svc_runtime().  Changed the method or writing the CSV-style
#              output lines to leverage the data[] array.
# 20171012 RAD Started writing status.html, which CMX copies up to the web-server.
#              It's pretty simple yet, but now I can at least check the current
#              status remoted via web-browser.
# 20170920 RAD Noticed rf_dropped() was returning "None" in some cases.
#              Cumulus MX is catching an exception tied to Weather Underground.
#              See http://sandaysoft.com/forum/viewtopic.php?f=27&t=16510
#              Added return_value to make sure there is a value returned.
#              Increased the number of records checked too.
#              not to hammer the SD card.
# 20170822 RAD Posted to http://sandaysoft.com/forum/viewtopic.php?f=27&t=16448
#              about this project because I'm not sure I yet have a handle on what
#              to track.  Others may have ideas and be interested...
# 20170712 RAD Want this to run silently (eventually), but log periodically soas
#              not to hammer the SD card.
# ========================================================================================
#
#
#  https://stackoverflow.com/questions/21535467/querying-process-load-in-python
#
#  I noticed 10-12 active processes at one point when Cumulus was sluggish...
#
#
# ========================================================================================
#
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
#
#
# ========================================================================================


from os import listdir
from ftplib import FTP
import shutil
import re

import urllib
import datetime
import RPi.GPIO as GPIO
import time
from time import sleep
import sys
import subprocess
from os import getpid



ftp_credentials_file = "/home/pi/.ftp.credentials"
ftp_login = ""
ftp_password = ""

this_script = sys.argv[0]
image_dir = "/home/pi/images"
last_image_name = ""
image_ts_file = re.sub('\.py', '__.dat', this_script)
last_timestamp = 0





Relay_channel = [17]
# sleep_for = 300
sleep_for = 24
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
data_format = [
	"{:8.4f} days",
	"{}"
	]

thresholds = [
	100,
	0
	]
	# amb_temp   {}


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
#
#
# ----------------------------------------------------------------------------------------
def main():
	global data
	global Prob_Track

	python_version = "v " + str(sys.version)

	next_image_file()
	push_image()


# ----------------------------------------------------------------------------------------
#
#  Subsequent calls find the avergae utilization since the previous call.
#
#
# ----------------------------------------------------------------------------------------
def next_image_file() :

	global last_timestamp

	# Should only ever happen at startup...
	if last_timestamp == 0 :
		last_timestamp = get_stored_ts()

	print "DEBUG: last_timestamp = " + last_timestamp

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

			print "DEBUG: digits = " + digits
			if int(digits) > int(last_timestamp) :
				print "DEBUG: found new image file = " + digits
				break

			print "DEBUG: Compare..."
			print "DEBUG:       -  " + last_timestamp
			print "DEBUG:       -  " + digits
			sleep(1)


	if int(digits) > int(last_timestamp) :
		print "DEBUG: Earliest unprocessed image file is " + file_list[line]
		set_stored_ts ( digits )

	shutil.copy2( image_dir + '/' + file_list[line], image_dir + '/NW.jpg' )

###	convert = subprocess.check_output( ['/usr/bin/convert', 'images/NW.jpg', '-resize', '30%', 'images/NW_thumb.jpg'] )
	convert = subprocess.check_output( ['/usr/bin/convert', 'images/NW.jpg', '-verbose', '-resize', '30%', 'images/NW_thumb.jpg'] )
###	convert = re.sub('.*average: *', '', convert)
###	convert = convert.rstrip()
	messager( "DEBUG: convert data: \"" + convert + "\"" )



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

	set_stored_ts ( digits )

	print "get_stored_ts = " + get_stored_ts()

	return file_list[iii]




# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def set_stored_ts(ts) :
	global image_ts_file
	print "DEBUG: write " + image_ts_file
	FH = open(image_ts_file, "w")
	FH.write( ts )
	FH.close





# ----------------------------------------------------------------------------------------
#
#
#
# ----------------------------------------------------------------------------------------
def get_stored_ts() :
	global image_ts_file
	print "DEBUG: read " + image_ts_file
	FH = open(image_ts_file, "r")
	content = FH.readlines()
	FH.close

	return content[0]



# ----------------------------------------------------------------------------------------
#
#
#@@@
#  https://pythonspot.com/en/ftp-client-in-python/
#  https://docs.python.org/2/library/ftplib.html
# ----------------------------------------------------------------------------------------
def push_image() :
	global image_ts_file

	print "DEBUG: read " + image_ts_file
	FH = open(ftp_credentials_file, "r")
	data = FH.readlines()
	FH.close

	ftp_login = data[0].strip("\n")
	ftp_password = data[1].strip("\n")

	print "DEBUG: ftp_login = " + ftp_login + "    ftp_password = " + ftp_password

	ftp = FTP('dillys.org')
	ftp.login( ftp_login, ftp_password )
	print ftp.pwd()

	### ftp.retrlines('LIST')

	data = []

###	ftp.cwd('/NorthFacing/')
###	ftp.dir(data.append)



	filename = 'images/NW_thumb.jpg'
	ftp.storbinary('STOR NW_thumb.jpg', open(filename, 'rb'))


 
	ftp.quit()
 
###	for line in data:
###		print "-", line


#  images/NW_thumb.jpg bobdilly@dillys.org:/home/content/b/o/b/bobdilly/html/WX










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
		rf_dropped()
		last_realtime()
		proc_load()
		proc_pct()
		camera_down()
		cmx_svc_runtime()
		mono_threads()
		mem_usage()
		webcamwatch_down()

		CSV_rec = datetime.datetime.utcnow().strftime(strftime_FMT) + ","
		Prob_Flag = " ,"

		for jjj in range(0, len(CSV_keys)):
			format_str = " " + CSV_format[jjj] + ","
			CSV_rec = CSV_rec + format_str.format( data[CSV_keys[jjj]] )
			if Prob_Track[jjj] > 0 :
				if data[CSV_keys[jjj]] > 0 :
					Prob_Flag = " <<<<<,"

		print CSV_rec + Prob_Flag

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# NOTE: Would be great to output data and use highcharts
		#
		#  https://pythonspot.com/en/ftp-client-in-python/
		#  https://docs.python.org/2/library/ftplib.html
		#  http://api.highcharts.com/highstock/Highcharts.stockChart
		#  https://www.highcharts.com/products/highcharts/
		#  https://www.highcharts.com/products/highcharts/
		#  https://www.highcharts.com/docs/working-with-data/data-module
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if 0 == iii % summary_stride :
			summarize()

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		#		swap_pct 0
		#		swap_used 500
		#		cpu_temp 38.089
		#		mem_pct 34
		#		rf_dropped 0
		#		effective_used 323012
		#		watcher_pid 16978
		#		cpu_temp_f 100.5602
		#		last_realtime -2
		#		proc_load 0.24
		#		server_stalled 0
		#		ws_data_stopped 0
		#		camera_down 0
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

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
# Appends an event table line (HTML) to the event list.
# Has to be maintained manually.
#
# ----------------------------------------------------------------------------------------
def log_event(ID, description, code):
	bgcolor = "TD"
	# Supply timestamp if no ID was given
	if len(ID) < 1 :
		ID = datetime.datetime.now().strftime(strftime_FMT + " (local)")

	# http://htmlcolorcodes.com/
	if code == 101 :
		bgcolor = "TD BGCOLOR=blue"
	if code == 103 :
		bgcolor = "TD BGCOLOR=#BA37C7"    # Violet-Pink
	if code == 104 :
		bgcolor = "TD BGCOLOR=#6137C7"    # Blue-Purple
	if code == 105 :
		bgcolor = "TD BGCOLOR=#0E7135"    # Dark Green
	if code == 111 :
		bgcolor = "TD BGCOLOR=#1F838A"    # Dark Turquoise
	if code == 112 :
		bgcolor = "TD BGCOLOR=#0E7135"    # Dark Green
	if code == 115 :
		bgcolor = "TD BGCOLOR=red"
	if code == 116 :
		bgcolor = "TD BGCOLOR=green"
	if code == 118 :
		bgcolor = "TD BGCOLOR=#CC04BD"    # Dark Hot Pink-purple

	format_str = "<TR><TD> {} </TD>\n<TD> {} </TD>\n<{}> {} </TD></TR>\n"

	FH = open(events_page , "a")
	FH.write( format_str.format( ID, description, bgcolor, code) )

	FH.close

# ----------------------------------------------------------------------------------------
# This generates a Raspberry Pi Status page, which Cumulus MX ftp's to the server.
# It is mostly an HTML table.
#
# ----------------------------------------------------------------------------------------
def summarize():
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)
	cmx_svc_runtime()

	FH = open(status_page , "w")

	FH.write( "<HEAD><TITLE>\n" )
	FH.write( "Raspberry Pi / Cumulus MX Health\n" )
	FH.write( "</TITLE></HEAD><BODY BGCOLOR=\"#555555\" TEXT=\"#FFFFFF\" LINK=\"#FFFF00\" VLINK=\"#FFBB00\" ALINK=\"#FFAAFF\"><H1 ALIGN=center>\n" )
	FH.write( "Raspberry Pi / Cumulus MX Health\n" )
	FH.write( "</H1>\n\n" )
	# FH.write( "<P> &nbsp;\n\n" )
	
	FH.write( "<CENTER>\n")
	FH.write( "<TABLE CELLPADDING=7><TR><TD VALIGN=\"TOP\">\n\n")

	FH.write( "<CENTER>\n")
	FH.write( "<TABLE BORDER=1>\n" )
	FH.write( "<TR><TH> Parameter </TH><TH> Current Value </TH><TH> Threshold </TH</TR>\n" )
	# NOTE: We may not choose to print everything in data[]
	for iii in range(0, len(data_keys)):
		bgcolor = ""
		if thresholds[iii] > -1 :
			# print "   data {}  threshold {}".format( data[data_keys[iii]], thresholds[iii] )
			if data[data_keys[iii]] > thresholds[iii] :
				bgcolor = " BGCOLOR=\"red\""
		
		# format_str = "<TR><TD> {} </TD><TD ALIGN=right> " + data_format[iii]  + " </TD></TR>\n"
		# FH.write( format_str.format( data_keys[iii], data[ data_keys[iii] ] ) )
		# thresholds
		format_str = "<TR><TD{}> {} </TD><TD ALIGN=right{}> " + data_format[iii]  + " </TD><TD ALIGN=right{}> {} </TD></TR>\n"
		FH.write( format_str.format( bgcolor, data_keys[iii], bgcolor, data[data_keys[iii]], bgcolor, thresholds[iii] ) )

	FH.write( "<TR><TD COLSPAN=3 ALIGN=center><FONT SIZE=-1>\n" )
	FH.write( datetime.datetime.utcnow().strftime(strftime_FMT) + " GMT" )
	FH.write( "<BR> " + datetime.datetime.now().strftime(strftime_FMT) + " Local" )
	FH.write( "</FONT></TD></TR>\n" )

	FH.write( "</TABLE>\n" )

	# This is how often the page updates locally, but only to the web server every 5 minutes.
	# FH.write( "<P ALIGN=center><FONT SIZE=-3> Updated every {} secs </FONT>".format( sleep_for * summary_stride ) )

	FH.write( "<P> &nbsp;\n" )
	FH.write( "<A HREF=\"Dilly_WX_Indoor.jpg\"><IMG SRC=\"Dilly_WX_Indoor_050.jpg\"></A>\n")
	FH.write( "<BR><FONT SIZE=-3>CLICK TO ENLARGE</FONT>\n")
	FH.write( "</CENTER>\n\n")
	FH.write( "</TD></TR></TABLE>\n")
	FH.write( "</CENTER>\n\n")

	FH.write( "<P> &nbsp;\n" )
	FH.write( "<center><table style=\"width:100%;border-collapse: collapse; border-spacing: 0;\" >\n" )
  	FH.write( "  <tr>\n" )

	FH.write( "    <td align=\"center\" class=\"td_navigation_bar\">:<a href=\"index.htm\">now</a>::<a href=\"gauges.htm\">gauges</a>:" + \
		":<a href=\"today.htm\">today</a>::<a href=\"yesterday.htm\">yesterday</a>::<a href=\"thismonth.htm\">this&nbsp;month</a>:" + \
		":<a href=\"thisyear.htm\">this&nbsp;year</a>:\n" )
	FH.write( "    <br>:<a href=\"record.htm\">records</a>::<a href=\"monthlyrecord.htm\">monthly&nbsp;records</a>:" + \
		":<a href=\"trends.htm\">trends</a>::<a TARGET=\"_blank\" HREF=\"http://sandaysoft.com/forum/\">forum</a>:" + \
		":<a href=\"http://dillys.org/WX/NW_View.html\">webcam</a>:\n" )
	FH.write( "    <br>:<a TARGET=\"_blank\" HREF=\"https://app.weathercloud.net/d0208473809#current\">Weathercloud</a>:" + \
		":<a TARGET=\"_blank\" HREF=\"https://www.pwsweather.com/obs/RADILLY.html\">PWS&nbsp;Weather</a>:" + \
		":<a TARGET=\"_blank\" HREF=\"https://wx.aerisweather.com/local/us/pa/mcmurray\">AerisWeather</a>:" + \
		":<a TARGET=\"_blank\" HREF=\"https://radar.weather.gov/Conus/full_loop.php\">NWS&nbsp;Composite&nbsp;US&nbsp;Radar</a>:\n" + \
		":<a TARGET=\"_blank\" HREF=\"https://www.windy.com/40.279/-80.089?39.317,-80.089,7,m:eMiadVG\">Windy</a>:\n" )
	FH.write( "    <br>:<a href=\"status.html\">Pi status</a>:" + \
		":<a href=\"events.html\">Event&nbsp;Log</a>:\n" + \
		":<a TARGET=\"_blank\" HREF=\"https://www.wunderground.com/personal-weather-station/dashboard?ID=KPAMCMUR4\">KPAMCMUR4</a>:</td>\n" )

  	FH.write( "  </tr>\n" )
	FH.write( " </table></center>\n" )

	FH.write( "<P> &nbsp;\n" )
	FH.write( "<P ALIGN=CENTER> Last updated: " + timestamp + " UTC\n" )

	FH.close


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
# Copied from the SunFounder example to configure the GPIO ports.
#
# ----------------------------------------------------------------------------------------
def GPIO_setup():
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
# This power-cycles the web cam by triggering the rely for a period.
#
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
# Clean up the GPIO configure on exit
#
# ----------------------------------------------------------------------------------------
def destroy():
	##DEBUG## ___print "\nShutting down..."
	logger("Shutting down...\n")
	GPIO.output(17, GPIO.HIGH)
	GPIO.cleanup()

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
			log_event("", "CumulusMX reports data_stopped (<#DataStopped> == 1).", 101 )
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
				log_event("", "DEBUG:  Sensor contact <B>appears</B> to have been restored. Out for " + str(elapsed) + " sec", 116 )
				break
		else :
			messager( "DEBUG:  Sensor RF status indeterminate.")

	return restored


# ----------------------------------------------------------------------------------------
# Check the Cumulus MX Diags log for anything strange going on.
#
# If "WU Response: OK: success" is the last line we should be OK.
# Cumulus will throw an exception once in a while, one of which looks like an
# unexpected/unhandled response from Weather Underground, plus others.
# The most challenging one is when the base station loses (RF) contact
# with the remote sensor unit (as in example below). There's a "down"
# on the base console that will sometimes re-acquire the RF connection.
#   I've not yet figured out out to make the Pi press the button -
#   perform the equivalent reset....
#
# The logs are dated, but the filenames should sort numerically....
# "MXdiags/20170912-202909.txt"
#
# ----------------------------------------------------------------------------------------
# Looking for this in the Diags log....
#   2017-09-15 20:26:45.616 Sensor contact lost; ignoring outdoor data
#   2017-09-15 20:26:55.616 Sensor contact lost; ignoring outdoor data
#   2017-09-15 20:27:00.666 WU Response: OK: success
#   
# ----------------------------------------------------------------------------------------
def rf_dropped() :
	global saved_exception_tstamp
	global saved_contact_lost
	global data
	check_lines = 12
	return_value = 0
	logger_code =111
	file_list = listdir( mxdiags_dir )

	file_list.sort()

	#for iii in range(0, len(file_list)):
	#	___print str(iii) + "  " + file_list[iii]

	for iii in range(-1, -5, -1):
		### messager( "DEBUG:  Checking in diags file, " + file_list[iii])
		if re.search('^20', file_list[iii]) :
			log_file = file_list[iii]
			break



	### messager( "DEBUG:  log_file = " + log_file )
	# ___print log_file

	# --------------------------------------------------------------------------------
	# Work backwards from the end of the most recent file looking for
	# one of the lines above.
	# --------------------------------------------------------------------------------

	fileHandle = open ( mxdiags_dir + "/" + log_file,"r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	for iii in range(-1, (-1 * check_lines), -1):
		lineList[iii] = re.sub('\n', ' ', lineList[iii])        # Remove any newline which might be left
		### messager( "DEBUG:  lineList[" + str(iii) + "] = \"" + lineList[iii] + "\"" )
		# ___print str(iii) + " \t" + lineList[iii]
		# ------------------------------------------------------------------------
		# We may print the same exception multiple times.  It could be identified
		# by the timestamp...
		# 
		#     2017-09-22 22:24:00.485
		#     -----------------------
		# ------------------------------------------------------------------------
		# 2017/09/23 02:23:38 GMT,  0,  0,  0,  24,   0.15,  0,  150444,  15%,  0,  0%,  48.3,  48.312,
		# free|945512|764200|181312|6828|445312|168444|150444|795068|102396|0|102396
		# WARNING:  Cumulus MX Exception thrown
		# 
		# 1       2017-09-22 22:24:00.485 WU update:    at System.Net.WebConnection.HandleError(WebExceptionStatus st, System.Exception e, System.String where)
		# 2017/09/23 02:24:02 GMT,  0,  0,  0,  24,   0.10,  0,  150672,  15%,  0,  0%,  49.4,  49.388,
		# free|945512|764432|181080|6828|445316|168444|150672|794840|102396|0|102396
		# WARNING:  Cumulus MX Exception thrown
		# 
		# 1       2017-09-22 22:24:00.485 WU update:    at System.Net.WebConnection.HandleError(WebExceptionStatus st, System.Exception e, System.String where)
		# 2017/09/23 02:24:27 GMT,  0,  0,  0,  24,   0.06,  0,  150808,  15%,  0,  0%,  49.4,  49.388,
		# free|945512|764580|180932|6828|445328|168444|150808|794704|102396|0|102396
		# ------------------------------------------------------------------------
		#      WARNING:  exception_tstamp = 2017-10-0210:57:00.626:.....


		#   2017/11/09 18:28:07 GMT WARNING:  Cumulus MX Exception thrown:    exception_tstamp =
		#   2017-11-0913:28:00.388:.....
		#   2017-11-09 13:28:00.388 WU update:    at System.Net.WebConnection.HandleError(WebExceptionStatus st, System.Exception e, System.String where)

		if "Exception" in lineList[iii] :
			exception_tstamp = re.sub(r'([-0-9]+ [\.:0-9]+).*', r'\1', lineList[iii] )
			if saved_exception_tstamp != exception_tstamp :
				# This is the signature of the most common exception we seem to see.
				if "at System.Net.WebConnection.HandleError(WebExceptionStatus" in lineList[iii] :
					logger_code =110
					saved_exception_tstamp = exception_tstamp 
				else :
					logger_code =111

				print ""
				messager( "WARNING:  Cumulus MX Exception thrown:    exception_tstamp = " + \
					exception_tstamp + "  (" + str(logger_code) + ")" )

				# --------------------------------------------------------
				# --------------------------------------------------------
				#  NOTE: This should be moved to a function.
				# --------------------------------------------------------
				# --------------------------------------------------------
				log_fragment = "<BR><FONT SIZE=-1><PRE>\n"
				for jjj in range(iii-3, 0, 1) :
					# Number the lines in the file we read
					print str(len(lineList)+jjj+1) + "\t" + lineList[jjj].rstrip()
					log_fragment = log_fragment + \
						"{:06d}  {}\n".format( (len(lineList)+jjj+1), lineList[jjj].rstrip())

				log_fragment = log_fragment + "</PRE></FONT>\n"
				messager( "WARNING:    from  " + mxdiags_dir + "/" + log_file )
				print ""

				log_event(exception_tstamp, "Cumulus MX Exception thrown:" + log_fragment, logger_code )
###			else:
###				messager( "WARNING:  Cumulus MX Exception thrown (see above) @ " + \
###				check_lines = 12
###					exception_tstamp )
			break

		# ------------------------------------------------------------------------
		#   2017-09-15 20:26:45.616 Sensor contact lost; ignoring outdoor data
		#   2017-09-15 20:26:55.616 Sensor contact lost; ignoring outdoor data
		#   2017-09-15 20:27:00.666 WU Response: OK: success
		#   
		#   2017-09-15 20:28:00.677 WU Response: OK: success
		#   
		# See example block below. It is possible to see the good message in 
		# the middle of a period of disconnect because CumulusMX continues to
		# report to Weather Underground. (Only the indoor data is valid.)
		# ------------------------------------------------------------------------
		########### if "Sensor contact lost; ignoring outdoor data" in lineList[iii] :
		### 2017-11-05 07:36:59.373 Sensor contact lost; ignoring outdoor data
		elif "Sensor contact lost" in lineList[iii] :
			### messager( "DEBUG:  Sensor contact lost; " + lineList[iii])
			if saved_contact_lost < 1 :
				# 20180226 - Just testing at this point....
				WX_RF_Restored(iii, lineList)
				saved_contact_lost = int( datetime.datetime.utcnow().strftime("%s") )
				# Long message the first time we see this...
				messager( "WARNING:  Sensor contact lost; ignoring outdoor data.  " + \
					"Press \"V\" button on WS console   (code 115)" )
				log_event("", "Sensor contact lost; ignoring outdoor data.", 115 )
			else:
				elapsed = int( datetime.datetime.utcnow().strftime("%s") ) -  saved_contact_lost 
				# Shorter message while this status continues
				messager( "WARNING:  Sensor contact lost; ... " + str(elapsed) + " sec" )

			return_value = 1
			break



		# ------------------------------------------------------------------------
		# 01/22/18 - This type of message caused a problem for Weather Underground
		#            which required a restart/reboot to clear.
		#
		# NOTE: Find unexpected messages really needs some analysis and thought.
		#
		# This is a grep of the diags logs for "WU" when CMX got stuck...
		#   2018-01-22 05:54:01.173 WU Response: OK: success
		#   2018-01-22 05:55:01.213 WU Response: OK: success
		#   2018-01-22 05:57:40.987 WU update: The Task was canceled
		#   2018-01-22 05:59:40.996 WU update: The Task was canceled
		#   2018-01-22 06:01:41.021 WU update: The Task was canceled
		#   2018-01-22 06:03:41.006 WU update: The Task was canceled
		#
		# I also looked for unique WeatherCloud messages
		#   WeatherCloud Response: InternalServerError: <h1>CException</h1>
		#   WeatherCloud Response: OK: 200
		#   WeatherCloud Response: OK: 429
		#   WeatherCloud update: The Task was canceled
		#
		# ------------------------------------------------------------------------
		elif "The Task was canceled" in lineList[iii] :
			# ----------------------------------------------------------------
			# ----------------------------------------------------------------
			#  NOTE: This should be moved to a function.
			# ----------------------------------------------------------------
			# ----------------------------------------------------------------
			log_fragment = "<BR><FONT SIZE=-1><PRE>\n"
			for jjj in range(iii-3, 0, 1) :
				# Number the lines in the file we read
				# Here we do NOT use the messager() function.
				print str(len(lineList)+jjj+1) + "\t" + lineList[jjj].rstrip()
				log_fragment = log_fragment + \
					"{:06d}  {}\n".format( (len(lineList)+jjj+1), lineList[jjj].rstrip())

			log_fragment = log_fragment + "</PRE></FONT>\n"
			messager( "WARNING:   \"The Task was canceled\"  from  " + mxdiags_dir + "/" + log_file )
			print ""

			log_event("", "Cumulus MX: \"The Task was canceled\"" + log_fragment, 118 )

			break  #####  <<<<<<  NOTE: Not sure this is right.  Check when it fires...
			# ----------------------------------------------------------------
			# NOTE: I think the breaks need to be looked at carefully...
			# Example of resulting log output ... looks reasonable I think.
			#
			#   705	
			#   706	2018-01-22 13:21:00.429 WU Response: OK: success
			#   707	
			#   708	2018-01-22 13:21:40.234 WeatherCloud update: The Task was canceled
			#   2018/01/22 18:21:43 WARNING:   "The Task was canceled"  from  /mnt/root/home/pi/Cumulus_MX/MXdiags/20180122-095424.txt
			#
			# ----------------------------------------------------------------




		# ------------------------------------------------------------------------
		# This message, "Data input appears to have stopped" occurs when
		# the USB link is lost.  It doesn seem like CumulusMX ever recovers,
		# but hase to be restarted.
		#
		#
		# ------------------------------------------------------------------------
		elif "Data input appears to have stopped" in lineList[iii] :
			# ----------------------------------------------------------------
			log_event("", "Data input appears to have stopped, USB likely disconnected.", 120 )
			messager( "INFO: \"Data input appears to have stopped\", USB likely disconnected.   (code 120)" )
			return_value = 1
			break







		# ------------------------------------------------------------------------
		# See the block below for a "Sensor contact lost" example.
		# It is possible to get some "good" messages in the midst of a string
		# of these "bad" messages.
		# 11/05/17 - Added an if to skip the break until at least a few lines
		#            have been checked.
		# 01/08/18 - Changed that check from -3 to -2
		# ------------------------------------------------------------------------
		elif "WU Response: OK: success" in lineList[iii] :
		# 	___print "Data OK"
			if iii < 0 :    #################################################  HACKED -----   ALWAYS TRUE
				# --------------------------------------------------------
				# This is not quite right. CMX sends stuck data to WU.
				# See the block below with starts:
				#    Pulling these Latest reading records out, I notice a ...
				# See the block below with starts:
				# --------------------------------------------------------
				if saved_contact_lost > 2 :
					elapsed = int( datetime.datetime.utcnow().strftime("%s") ) -  saved_contact_lost 
					log_event("", "Sensor contact RESTORED; receiving telemetry again. " + str(elapsed) + " sec", 116 )
					messager( "INFO:  Sensor contact RESTORED; ... lost for " + str(elapsed) + " sec   (code 116)" )
				saved_contact_lost = -1
				if len( saved_exception_tstamp ) > 3 :
					messager( "INFO: \"WU Response: OK: success\"; clearing pending exception flag.   (code 112)" )
					log_event("","\"WU Response: OK: success\"; clearing pending exception flag.", 112 )
				saved_exception_tstamp = "X"    # Set this flag back to the sentinal value
				break

		else :
			if iii < (-1 * check_lines) + 1 :
				messager( "WARNING:  Unknown status from  " + mxdiags_dir + "/" + log_file + "   (code 199)" )
				for jjj in range(iii-3, 0, 1) :
					# Number the lines in the file we read
					print str(len(lineList)+jjj+1) + "\t" + lineList[jjj].rstrip()
				log_event("", "Unknown status from  " + mxdiags_dir + "/" + log_file, 199 )


	# --------------------------------------------------------------------------------
	#   Not sure what to do with "None", or where exactly this comes from.
	#   Added return_value to make sure there is a value returned.
	#   Increased the number of records checked too.
	#   
	#  2017/09/20 12:50:21 GMT,  0,  0,  None,  24,  0.16,  0,  122740,  12%,  0,  0%,
	#  free|945512|664316|281196|6764|392848|148728|122740|822772|102396|0|102396
	#  2017/09/20 12:50:46 GMT,  0,  0,  None,  24,  0.1,  0,  122608,  12%,  0,  0%,
	#  free|945512|664200|281312|6764|392860|148732|122608|822904|102396|0|102396
	#  2017/09/20 12:51:11 GMT,  0,  0,  0,  24,  0.07,  0,  122696,  12%,  0,  0%,
	# --------------------------------------------------------------------------------
	data['rf_dropped'] = return_value
	return return_value


	# --------------------------------------------------------------------------------
	# Pulling these Latest reading records out, I notice a pattern when the RF seems
	# to be down of "FF FF FF" as shown, but it isn't quite right because we didn't
	# have around 20 minutes of changing data from looking at the graphs.
	# 
	#  2018-02-26 05:25:00.424 Latest reading: 75A0: 18 35 B1 00 FF FF FF 6A 26 FF FF FF 80 45 0E C0
	#  2018-02-26 05:30:00.439 Latest reading: 75A0: 1D 35 B2 00 FF FF FF 6C 26 FF FF FF 80 45 0E C0
	#  2018-02-26 05:35:00.453 Latest reading: 75B0: 04 35 B2 00 47 28 00 6C 26 00 00 00 00 45 0E 80
	#  2018-02-26 05:40:00.469 Latest reading: 75B0: 09 35 B2 00 47 28 00 6B 26 00 00 00 00 45 0E 80
	#  2018-02-26 05:45:00.483 Latest reading: 75B0: 0E 35 B3 00 47 28 00 6B 26 00 00 00 00 45 0E 80
	#  2018-02-26 05:50:00.498 Latest reading: 75B0: 11 36 B5 00 47 28 00 6F 26 00 00 00 00 45 0E 80
	#  2018-02-26 05:55:00.513 Latest reading: 75B0: 18 36 B6 00 FF FF FF 6D 26 FF FF FF 80 45 0E C0
	#  2018-02-26 06:00:00.539 Latest reading: 75B0: 1D 36 B7 00 FF FF FF 6D 26 FF FF FF 80 45 0E C0
	#                                                            ^^^^^^^^
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	# Looking at the charts, there appears to be a single jump in values between
	# 5:32 and 5:33.   In the data log the shift shows up this way, with a string
	# before and after 5:33 of the same values.
	#
	#  26/02/18,05:30,40.6,72,32.3,3.1,5.4,360,0.00,0.00,30.42,43.15,64.0,53,5.4,38.9,40.6,0.0,0,0.000,0.000,35.4,0,0.0,360,0.00,0.00
	#  26/02/18,05:35,39.2,71,30.6,0.0,0.0,0,0.00,0.00,30.42,43.15,64.0,53,0.0,39.2,39.2,0.0,0,0.000,0.000,35.4,0,0.0,360,0.00,0.00
	#
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	# Looking at the details of the Diags log around this time, the "Sensor contact lost"
	# one might think the data is updating for something like 18 minutes, but that's not
	# what the temperature chart shows, which is just a single jag in the plot at 5:33.
	# CMX is still sending data, even though it is stuck.
	#
	#  2018-02-26 05:31:49.202 Sensor contact lost; ignoring outdoor data
	#  2018-02-26 05:31:59.150 Sensor contact lost; ignoring outdoor data
	#  2018-02-26 05:32:00.666 WU Response: OK: success
	#
	#  2018-02-26 05:32:09.150 Sensor contact lost; ignoring outdoor data
	#  2018-02-26 05:33:00.681 WU Response: OK: success
	#
	#  2018-02-26 05:34:00.667 WU Response: OK: success
	#
	#  2018-02-26 05:35:00.448 Writing log entry for 2/26/2018 5:35:00 AM
	#  2018-02-26 05:35:00.449 Written log entry for 2/26/2018 5:35:00 AM
	#  2018-02-26 05:35:00.453 Writing today.ini, LastUpdateTime = 2/26/2018 5:35:00 AM raindaystart = 43.14566924733 rain counter = 43.14566924733
	#  2018-02-26 05:35:00.453 Latest reading: 75B0: 04 35 B2 00 47 28 00 6C 26 00 00 00 00 45 0E 80
	#  2018-02-26 05:35:00.682 WU Response: OK: success
	#
	#      ..... Gap here .....
	#
	#  2018-02-26 05:48:00.694 WU Response: OK: success
	#
	#  2018-02-26 05:49:00.674 WU Response: OK: success
	#
	#  2018-02-26 05:50:00.492 Writing log entry for 2/26/2018 5:50:00 AM
	#  2018-02-26 05:50:00.494 Written log entry for 2/26/2018 5:50:00 AM
	#  2018-02-26 05:50:00.497 Writing today.ini, LastUpdateTime = 2/26/2018 5:50:00 AM raindaystart = 43.14566924733 rain counter = 43.14566924733
	#  2018-02-26 05:50:00.498 Latest reading: 75B0: 11 36 B5 00 47 28 00 6F 26 00 00 00 00 45 0E 80
	#  2018-02-26 05:50:00.707 WU Response: OK: success
	#
	#  2018-02-26 05:50:01.010 WeatherCloud Response: OK: 200
	#  2018-02-26 05:50:49.156 Sensor contact lost; ignoring outdoor data
	#  2018-02-26 05:50:59.578 Sensor contact lost; ignoring outdoor data
	#  2018-02-26 05:51:00.979 WU Response: OK: success
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	# 
	# Maybe we can't conclude the RF has restarted unless we see a minimum
	# of two "WU Response: OK: success" records in a row.  Or, if we do see
	# such a record, the one before cannot be "Sensor contact lost." But there
	# is an exception to that as well, when proceeded by a "Latest reading"
	# record, we still might have dropped RF.  Its also possible a
	# "WeatherCloud Response" record could be in there depending on the
	# response time from the server.
	# 
	# --------------------------------------------------------------------------------
	# Appears that CumulusMX retries to read the sensor approximately every 10 seconds
	#     2017-11-05 07:33:49.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:33:59.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:34:00.946 WU Response: OK: success
	#     
	#     2017-11-05 07:34:09.372 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:34:19.472 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:34:29.472 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:34:39.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:34:49.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:34:59.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:35:00.348 Writing log entry for 11/5/2017 7:35:00 AM
	#     2017-11-05 07:35:00.350 Written log entry for 11/5/2017 7:35:00 AM
	#     2017-11-05 07:35:00.353 Writing today.ini, LastUpdateTime = 11/5/2017 7:35:00 AM raindaystart = 32.811...
	#     2017-11-05 07:35:00.353 Latest reading: 21F0: 09 3D CA 00 FF FF FF 33 26 FF FF FF 84 EF 0A C0
	#     2017-11-05 07:35:00.946 WU Response: OK: success
	#     
	#     2017-11-05 07:35:09.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:35:19.373 Sensor contact lost; ignoring outdoor data
	#     2017-11-05 07:35:29.373 Sensor contact lost; ignoring outdoor data
	# --------------------------------------------------------------------------------




# ----------------------------------------------------------------------------------------
#  Check web cam status.
#
#  After power-cycling the web cam, it could take up to 5 minutes for the next
#  image update.  But more importantly, the dillys.org webserver cron job only
#  runs every 5 minutes... but empirically, up to 10 minutes - accounting for
#  each 5 minutes....?
#
# NOTE: I have similar code running as a service as of this writing, which
#       drives a relay which interrupts the power to the web cam -
#       a power-cycle.  Eventually, that functionality will go here...
#
# ----------------------------------------------------------------------------------------
def camera_down():
	global data
	global pcyc_holdoff_time

	#___# # <<<<<<<<<<<<<<<<<<<< COMMENTED OUT THE RELAY STUFF

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
		print "Unexpected ERROR in camera_down:", sys.exc_info()[0]
		content = "0 0 00:00:00_UTC "
		messager( "DEBUG: content = \"" + content + "\" in camera_down()" )

	words = re.split(' +', content)
	##DEBUG## ___print words[0], words[2]

	# --------------------------------------------------------------------------------
	#										##
	#										##
	#     Traceback (most recent call last):					##
	#       File "/mnt/root/home/pi/watchdog.py", line 672, in <module>		##
	#         write_pid_file()							##
	#       File "/mnt/root/home/pi/watchdog.py", line 125, in main			##
	#         rf_dropped(), last_realtime(), proc_load(), camera_down() ) + \	##
	#       File "/mnt/root/home/pi/watchdog.py", line 643, in camera_down		##
	#     										##
	#     ValueError: invalid literal for int() with base 10: ''			##
	#										##
	#										##
	# --------------------------------------------------------------------------------

	##### interval = int(result.group(1))
	try:
		interval = int(words[0])
	except:
		interval = -99999
		messager( "DEBUG: camera_down(): interval looked invalid, \"" + words[0] + "\"" )


	if interval > 3000:
		#___# power_cycle()

		# ------------------------------------------------------------------------
		#
		#   2017/10/04 13:05:12 GMT 3166 13:05:02_UTC power cycled
		#   2017/10/04 13:05:12 GMT,  0,  0,  0,  24,   0.00,  1,  93332,  9%,  0,  0%,  43.5,  43.470,   110.2,
		#   free|945512|296608|648904|6768|77532|125744|93332|852180|102396|0|102396
		#
		#   2017/10/04 13:15:25 GMT 3465 13:10:01_UTC power cycled
		#   2017/10/04 13:15:25 GMT,  0,  0,  0,  24,   0.17,  1,  92956,  9%,  0,  0%,  42.9,  42.932,   109.3,
		#   free|945512|296760|648752|6768|78044|125760|92956|852556|102396|0|102396
		# ------------------------------------------------------------------------

		if pcyc_holdoff_time > 0 :
			if int(time.strftime("%s")) > pcyc_holdoff_time :
				# holdoff has expired
				logger(words[0] + " " + words[2] + " waiting on webcam image update.")
				###### if data['camera_down'] == 0 :
				######	log_event("", " waiting on webcam image update.", 104 )
		else:
			pcyc_holdoff_time = int(time.strftime("%s")) + 600
			logger(words[0] + " " + words[2] + " power cycled")
			log_event("", " Webcam image update stalled.", 103 )

		# ------------------------------------------------------------------------
		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.
		# ------------------------------------------------------------------------

		#___# sleep(sleep_on_recycle)
		data['camera_down'] = 1
		return 1
	else:
		if data['camera_down'] == 1 :
			log_event("", " Webcam image updating!.", 105 )
		pcyc_holdoff_time = 0
		data['camera_down'] = 0
		return 0


# ----------------------------------------------------------------------------------------
# Return run-time of cumulusmx service as fractional days - Excel-style date.
#
# 2017-12-22 def last_restarted() was rolled into this routine.
# ----------------------------------------------------------------------------------------
#      $ systemctl status cumulusmx | grep since
#        Active: active (running) since Thu 2017-10-19 17:34:34 EDT; 2 weeks 3 days ago
# ----------------------------------------------------------------------------------------
def cmx_svc_runtime():
	global data
	output = subprocess.check_output(["/bin/systemctl", "status", "cumulusmx"])
	lines = re.split('\n', output)



	for iii in range(0, len(lines)):
		if re.search('Main PID:', lines[iii]) :
			mono_pid = re.sub('.*Main PID:.', '', lines[iii])
			mono_pid = re.sub(' \(.*', '', mono_pid)
			break

		if re.search('since', lines[iii]) :

			start_time = re.sub('.* since ... ', '', lines[iii])
			start_time = re.sub(';.*', '', start_time)
			duration = re.sub('.*; ', '', lines[iii])
			duration = re.sub(' ago', '', duration)




	timestamp = datetime.datetime.now().strptime(start_time, "%Y-%m-%d %H:%M:%S %Z")
	start_secs = int(timestamp.strftime("%s"))
	now_secs = int(datetime.datetime.now().strftime("%s"))
	secs_running = now_secs - start_secs
	in_days = float(secs_running) / float( 60*60*24 )

	data['cmx_svc_runtime'] = in_days
	data['mono_pid'] = mono_pid
	data['last_restarted'] = duration
	return in_days




# ----------------------------------------------------------------------------------------
# Return status of wxwatchdog service 
#
# ----------------------------------------------------------------------------------------
#   $ systemctl status wxwatchdog 
#     Active: active (running) since Thu 2017-10-19 17:34:34 EDT; 2 weeks 3 days ago
#     Active: inactive (dead) (Result: exit-code) since Tue 2018-01-16 12:54:10 EST; 8h ago
# ----------------------------------------------------------------------------------------
def webcamwatch_down():
	global data
	ret_val = 1
	output = subprocess.check_output(["/bin/systemctl", "status", "wxwatchdog"])
	lines = re.split('\n', output)

	for iii in range(0, len(lines)):
		if re.search('Active:', lines[iii]) :
			### print lines[iii]
			status = re.sub('.*Active:', '', lines[iii])
			### print status
			status = re.sub(' *since.*', '', status)
			### print status
			if re.search(' active .running.', status) :
				ret_val = 0

	data['webcamwatch_down'] = ret_val
	return ret_val



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
###	GPIO_setup()
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
#   2.7.9 (default, Sep 17 2016, 20:26:04)
#   [GCC 4.9.2]
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# NOTE: Examples from /mnt/root/home/pi/Cumulus_MX/MXdiags logs
# ----------------------------------------------------------------------------------------
# NOTE: Bad (out-of-range) data detected.  Probably result of RF issues.
#   2018-03-03 19:36:00.941 WU Response: OK: success
#
#   2018-03-03 19:36:12.777 Ignoring bad data: pressure = 6381.9
#   2018-03-03 19:36:12.778                    offset = 0
#   2018-03-03 19:36:12.778 Sensor contact lost; ignoring outdoor data
#   2018-03-03 19:37:01.194 WU Response: OK: success
#
# ----------------------------------------------------------------------------------------
# NOTE: Very short period of "Sensor contact lost; ignoring outdoor data"
#   2018-03-03 15:16:03.595 WU Response: OK: success
#
#   2018-03-03 15:16:12.714 Sensor contact lost; ignoring outdoor data
#   2018-03-03 15:17:01.291 WU Response: OK: success
#
#   2018-03-03 15:18:01.087 WU Response: OK: success
# ----------------------------------------------------------------------------------------
# NOTE: At startup, communicating with various sites...
#   2018-02-04 15:01:17.360 Creating WU URL #1
#   2018-02-04 15:01:17.360 http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=KPAMCMUR4&PASSWORD=**********&dateutc=2018-02-04+20%3A00%3A16&winddir=180&windspeedmph=1.6&windgustmph=3.8&windspdmph_avg2m=0.7&winddir_avg2m=195&humidity=82&tempf=37.0&rainin=0.00&dailyrainin=0.06&baromin=29.988&dewptf=32.1&indoortempf=68.5&indoorhumidity=36&softwaretype=Cumulus%20v3.0.0&action=updateraw
#   2018-02-04 15:01:17.363 Creating PWS URL #1
#   2018-02-04 15:01:17.363 http://www.pwsweather.com/pwsupdate/pwsupdate.php?ID=RADILLY&PASSWORD=**********&dateutc=2018-02-04+20%3A00%3A16&winddir=195&windspeedmph=0.7&windgustmph=3.8&humidity=82&tempf=37.0&rainin=0.00&dailyrainin=0.06&baromin=29.988&dewptf=32.1&softwaretype=Cumulus%20v3.0.0&action=updateraw
#   2018-02-04 15:01:17.364 End processing history data
#   2018-02-04 15:01:17.373 Start Timers
#   2018-02-04 15:01:17.373 Starting 1-minute timer
#   2018-02-04 15:01:17.376 Attempting realtime FTP connect
#   2018-02-04 15:01:18.436 Starting Realtime timer, interval = 24 seconds
#   2018-02-04 15:01:18.441 Uploading WU archive #1
#   2018-02-04 15:01:18.626 Uploading PWS archive #1
#   2018-02-04 15:01:18.988 PWS Response: OK: 
#   <html>
#   <head>
#      <title>PWS Weather Station Update</title>
#   </head>
#   <body>
#   Data Logged and posted in METAR mirror.
#
#   </body>
#   </html>
#   2018-02-04 15:01:18.989 End of PWS archive upload
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
