#!/usr/bin/python
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
#
# ========================================================================================
# 20171209 RAD Added cmx_svc_runtime().  Changed the method or writing the CSV-style
#              output lines to leverage the data[] array.
#              NOTE: 
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

import urllib
import re
import datetime
import RPi.GPIO as GPIO
import time
from time import sleep
import sys
import subprocess
from os import getpid
from os import listdir

Relay_channel = [17]
# sleep_for = 300
sleep_for = 24
sleep_on_recycle = 600
log_stride = 20
summary_stride = 3

last_secs = 999999          # This is a sentinel value for startup.
last_date = ""
proc_load_lim = 4.0         # See https://www.booleanworld.com/guide-linux-top-command/
mem_usage_lim = 85
ws_data_last_secs = 0       # Number of epoch secs at outage start
saved_contact_lost = 0      # Number of epoch secs when RF contact lost

### /home/pi/Cumulus_MX/DataStopped.sh
# data_stop_file = "/home/pi/Cumulus_MX/web/DataStoppedT.txttmp"
BASE_DIR =              "/mnt/root/home/pi/Cumulus_MX"
###############################################################################   data_stop_file =        "mnt/root/home/pi/Cumulus_MX/web/DataStoppedT.txttmp"
###############################################################################   ambient_temp_file =     "mnt/root/home/pi/Cumulus_MX/web/ambient_tempT.txttmp"
###############################################################################   status_page =           "mnt/root/home/pi/Cumulus_MX/web/status.html"
###############################################################################   mxdiags_dir =           "mnt/root/home/pi/Cumulus_MX/MXdiags"

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

pcyc_holdoff_time = 0


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# This is the global data value dictionary
# Most of the keys map to a function name...
#
#
# https://www.python-course.eu/dictionaries.php
# https://docs.python.org/2/tutorial/datastructures.html#dictionaries
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
data = []
data = { 'watcher_pid' : getpid() }
data_keys = [
	"watcher_pid",
	"mono_pid",
	"last_restarted",
	"cmx_svc_runtime",
	"server_stalled",
	"ws_data_stopped",
	"rf_dropped",
	"realtime_stalled",
	"proc_pct",
	"proc_load",
	"proc_load_5m",
	"camera_down",
	"mono_threads",
	"effective_used",
	"mem_pct",
	"swap_used",
	"swap_pct",
	"cpu_temp_c",
	"cpu_temp_f",
	"python_version" ]
	# amb_temp   {}

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# For HTML Table-style output lines
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# https://pyformat.info/
data_format = [
	"{}",
	"{}",
	"{} ago",
	"{:8.4f} days",
	"{}",
	"{}",
	"{}",
	"{}",
	"{:5.1f}%",
	"{:7.2f}",
	"{:7.2f}",
	"{}",
	"{}",
	"{}",
	"{}&percnt;",
	"{}",
	"{}&percnt;",
	"{:6.1f}",
	"{:6.1f}",
	"{}" ]

	#  Went to just the numbers for temps...  was
	#     "{:6.1f} &deg;C",
	#     "{:6.1f} &deg;F" ]

thresholds = [
	-1,
	-1,
	-1,
	-1,
	1,
	1,
	1,
	120,
	10.0,
	4.0,
	4.0,
	1,
	20,
	-1,
	15,
	1024,
	1,
	55,
	125,
	-1 ]
	# amb_temp   {}


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# For CSV-style output line
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#    "date-time",
CSV_keys = [
	"server_stalled",
	"ws_data_stopped",
	"rf_dropped",
	"realtime_stalled",
	"proc_load",
	"camera_down",
	"mono_threads",
	"effective_used",
	"mem_pct",
	"swap_used",
	"swap_pct",
	"cpu_temp_c",
	"cpu_temp_f",
	"amb_temp",
	"proc_pct",
	"cmx_svc_runtime", ]

# https://pyformat.info/
CSV_format = [
	"{}",
	"{}",
	"{}",
	"{:3d}",
	"{:7.2f}",
	"{}",
	"{:5d}",
	"{:6d}",
	"{:2d}%",
	"{:6d}",
	"{:2d}%",
	"{:4.1f}c",
	"{:5.1f}f",
	"{:5.1f}f",
	"{:5.1f}%",
	"{:16.10f}" ]


# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
#
#
#  To Do:
#		realtime_stalled() return value should be leveraged <<<  OBSOLETE???????????????
# ----------------------------------------------------------------------------------------
def main():
	global data

	python_version = "v " + str(sys.version)
	python_version = re.sub(' *\n *', '<BR>', python_version )
	python_version = re.sub(' *\(', '<BR>(', python_version )

	messager("Python version: " + str(sys.version))
	data['python_version'] = python_version

	iii = 0
	while True:
		if 0 == iii % log_stride:
			amb_temp()        # This won't / shouldn't change rapidly so sample periodically

			hdr = "date-time,"
			for jjj in range(0, len(CSV_keys)):
				hdr = hdr + " {},".format( CSV_keys[jjj] )

			print hdr

		# Capture the data by calling functions.  Ignore return values.
		server_stalled()
		ws_data_stopped()
		rf_dropped()
		realtime_stalled()
		proc_load()
		proc_pct()
		camera_down()
		mono_threads()
		cmx_svc_runtime()
		mem_usage()

		CSV_rec = datetime.datetime.utcnow().strftime(strftime_FMT) + ","

		for jjj in range(0, len(CSV_keys)):
			format_str = " " + CSV_format[jjj] + ","
			CSV_rec = CSV_rec + format_str.format( data[CSV_keys[jjj]] )

		print CSV_rec

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
		#		realtime_stalled -2
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
	#
	# --------------------------------------------------------------------------------
	fileHandle = open ( "/proc/" + str(PID) + "/stat","r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	lineList[0] = re.sub('\n', '', lineList[0])        # Remove any newline which might be left
	tok = re.split(' *', lineList[0])

	data['mono_threads'] = int(tok[19])
	return int(tok[19])

# ----------------------------------------------------------------------------------------
# OLD Count the mono threads running
# 
#  NOTE: 15 is s good number, but this seems to grow after a few weeks...
# ----------------------------------------------------------------------------------------
def OLD_mono_threads():
	global data
	load = subprocess.check_output(["/usr/bin/top", "-H", "-w", "125", "-n", "1", "-b", "-o", "+RES"])
	lines = re.split('\n', load)
	jjj = 0
	for iii in range(0, len(lines)):
		if re.search('mono$', lines[iii]) :
			jjj += 1
	data['mono_threads'] = jjj
	return jjj







# ----------------------------------------------------------------------------------------
# Appends an event table line (HTML) to the event list.
# Has to be maintained manually.
#
# ----------------------------------------------------------------------------------------
def log_event(ID, description, code):
	# Supply timestamp if no ID was given
	if len(ID) < 1 :
		ID = datetime.datetime.now().strftime(strftime_FMT + " (local)")

	FH = open(events_page , "a")

	format_str = "<TR><TD> {} </TD><TD> {} </TD><TD> {} </TD></TR>\n"
	FH.write( format_str.format( ID, description, code ) )

	FH.close

# ----------------------------------------------------------------------------------------
# This generates a Raspberry Pi Status page, which Cumulus MX ftp's to the server.
# It is mostly an HTML table.
#
# ----------------------------------------------------------------------------------------
def summarize():
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)
	last_restarted()

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

	# format_str = "<TR><TD> Ambient Temp </TD><TD ALIGN=right> {} </TD></TR>\n"
	# thresholds
	format_str = "<TR><TD> Ambient Temp &deg;F </TD><TD ALIGN=right> {} </TD><TD ALIGN=right> -1 </TD></TR>\n"
	## >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FH.write( format_str.format( amb_temp() ) )
	FH.write( format_str.format( data['amb_temp'] ) )


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
		":<a href=\"trends.htm\">trends</a>::<a href=\"http://sandaysoft.com/forum/\">forum</a>:" + \
		":<a href=\"http://dillys.org/WX/NW_View.html\">webcam</a>:\n" )
	FH.write( "    <br>:<a href=\"status.html\">Pi status</a>:" + \
		":<a href=\"https://www.wunderground.com/personal-weather-station/dashboard?ID=KPAMCMUR4\">KPAMCMUR4</a>:</td>\n" )

  	FH.write( "  </tr>\n" )
	FH.write( " </table></center>\n" )

	FH.write( "<P> &nbsp;\n" )
	FH.write( "<P ALIGN=CENTER> Updated: " + timestamp + "\n" )

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
	FH = open(data_stop_file, "r")
	data_status = int( FH.readline() )
	FH.close
	if data_status > 0 :
		if ws_data_last_secs < 1 :
			ws_data_last_secs = int( datetime.datetime.utcnow().strftime("%s") )
			# Long message the first time we see this...
			messager( "WARNING:  CumulusMX reports data_stopped (<#DataStopped> == 1)." )
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
def realtime_stalled():
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
		print "Unexpected ERROR:", sys.exc_info()[0]
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
		messager( "DEBUG: content = \"" + content + "\"" )

	words = re.split(' +', content)

	#  ---------------------------------------------------------------------
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
	#  date-time, server_stalled, ws_data_stopped, rf_dropped, realtime_stalled, proc_load, 
	#  2017/09/17 22:11:59 GMT,  0,  0,  0,  -65471,  0.0,  101244,  10%,  0,  0%,
	#  free|945512|560184|385328|6768|317368|141572|101244|844268|102396|0|102396
	#  WARNING: 65543 elapsed since realtime.txt was updated.
	#  2017/09/17 22:12:24 GMT,  0,  0,  0,  65543,  0.0,  101148,  10%,  0,  0%,
	#  free|945512|560088|385424|6768|317368|141572|101148|844364|102396|0|102396
	#  
    	#  Because above, when we get an incomplete file, lacking a timestamp
    	#  we set the time to "00:00:00" and we get a weird number for
	#  realtime_stalled.  The nominal value we expect is 24, or perhaps
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
	data['realtime_stalled'] = diff_secs
	return diff_secs       # For now we track this number. Later should return status.




# ----------------------------------------------------------------------------------------
# uptime  gives  a one line display of the following information.  The current time,
# how long the system has been running, how many users are currently logged on,  and
# the system load averages for the past 1, 5, and 15 minutes.
#   [' 08:39:19 up 3 days, 8 min,  2 users,  load average: 0.00, 0.00, 0.00\n']
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
#
# Examine the output from the free command - particularly focusing on swap usage.
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
	file_list = listdir( mxdiags_dir )

	file_list.sort()

	#for iii in range(0, len(file_list)):
	#	___print str(iii) + "  " + file_list[iii]

	log_file = file_list[len(file_list)-1]           # Last file in the list
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
			if saved_exception_tstamp == exception_tstamp :
				messager( "WARNING:  Cumulus MX Exception thrown (see above) @ " + \
					exception_tstamp )
				###############################################################               log_event(exception_tstamp, "Cumulus MX Exception thrown (see above)"
			else:
				print ""
				###   messager( "DEBUG:  exception_tstamp = " + exception_tstamp  )
				messager( "WARNING:  Cumulus MX Exception thrown:    exception_tstamp = " + \
					exception_tstamp )

				log_fragment = "<BR><FONT SIZE=-1><PRE>\n"
				for jjj in range(iii-3, 0, 1) :
					# Number the lines in the file we read
					print str(len(lineList)+jjj+1) + "\t" + lineList[jjj].rstrip()
					log_fragment = log_fragment + \
						"{:06d}  {}\n".format( (len(lineList)+jjj+1), lineList[jjj].rstrip())

				log_fragment = log_fragment + "</PRE></FONT>\n"
				messager( "WARNING:    from  " + mxdiags_dir + "/" + log_file )
				print ""
				log_event(exception_tstamp, "Cumulus MX Exception thrown:" + log_fragment, 110 )
			saved_exception_tstamp = exception_tstamp 
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
			if saved_contact_lost < 1 :
				saved_contact_lost = int( datetime.datetime.utcnow().strftime("%s") )
				# Long message the first time we see this...
				messager( "WARNING:  Sensor contact lost; ignoring outdoor data.  " + \
					"Press \"V\" button on WS console" )
				log_event("", "Sensor contact lost; ignoring outdoor data.", 115)
			else:
				elapsed = int( datetime.datetime.utcnow().strftime("%s") ) -  saved_contact_lost 
				# Shorter message while this status continues
				messager( "WARNING:  Sensor contact lost; ... " + str(elapsed) + " sec" )

			return_value = 1
			break

		# ------------------------------------------------------------------------
		# See the block below for a "Sensor contact lost" example.
		# It is possible to get some "good" messages in the midst of a string
		# of these "bad" messages.
		# 11/05/17 - Added an if to skip the break until at least a few lines
		#            have been checked.
		# ------------------------------------------------------------------------
		elif "WU Response: OK: success" in lineList[iii] :
		# 	___print "Data OK"
			if iii < -3 :
				saved_contact_lost = 0
				break

		else :
			if iii < (-1 * check_lines) + 1 :
				messager( "WARNING:  Unknown status from  " + mxdiags_dir + "/" + log_file )
				for jjj in range(iii-3, 0, 1) :
					# Number the lines in the file we read
					print str(len(lineList)+jjj+1) + "\t" + lineList[jjj].rstrip()
				log_event("", "Unknown status from  " + mxdiags_dir + "/" + log_file, 199 )


	# --------------------------------------------------------------------------------
	#   Not sure what to do with "None", or where exactly this comes from.
	#   Added return_value to make sure there is a value returned.
	#   Increased the number of records checked too.
	#   
	#  date-time, server_stalled, ws_data_stopped, rf_dropped, realtime_stalled, proc_load, camera_down, effective_used, mem_pct, swap_used, swap_pct
	#  2017/09/20 12:49:57 GMT,  0,  0,  0,  24,  0.01,  0,  107120,  11%,  0,  0%,
	#  free|945512|648688|296824|6764|392836|148732|107120|838392|102396|0|102396
	#  2017/09/20 12:50:21 GMT,  0,  0,  None,  24,  0.16,  0,  122740,  12%,  0,  0%,
	#  free|945512|664316|281196|6764|392848|148728|122740|822772|102396|0|102396
	#  2017/09/20 12:50:46 GMT,  0,  0,  None,  24,  0.1,  0,  122608,  12%,  0,  0%,
	#  free|945512|664200|281312|6764|392860|148732|122608|822904|102396|0|102396
	#  2017/09/20 12:51:11 GMT,  0,  0,  0,  24,  0.07,  0,  122696,  12%,  0,  0%,
	#  free|945512|664296|281216|6764|392868|148732|122696|822816|102396|0|102396
	# --------------------------------------------------------------------------------
	data['rf_dropped'] = return_value
	return return_value


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
	#     2017-11-05 07:35:00.353 Writing today.ini, LastUpdateTime = 11/5/2017 7:35:00 AM raindaystart = 32.81102358858 rain counter = 33.05905508439
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
		content = "0 0 00:00:00_UTC "
		messager( "DEBUG: content = \"" + content + "\"" )

	words = re.split(' +', content)
	##DEBUG## ___print words[0], words[2]

	# --------------------------------------------------------------------------------
	#										##
	#										##
	#     Traceback (most recent call last):					##
	#       File "/mnt/root/home/pi/watchdog.py", line 672, in <module>		##
	#         write_pid_file()							##
	#       File "/mnt/root/home/pi/watchdog.py", line 125, in main			##
	#         rf_dropped(), realtime_stalled(), proc_load(), camera_down() ) + \	##
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
		else:
			pcyc_holdoff_time = int(time.strftime("%s")) + 600
			logger(words[0] + " " + words[2] + " power cycled")

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
		pcyc_holdoff_time = 0
		data['camera_down'] = 0
		return 0



# ----------------------------------------------------------------------------------------
# For reporting, get the "time" of last start from systemctl.  It's really a pretty
# human-readable string.  A timestamp is also available.
# ----------------------------------------------------------------------------------------
# NOTE: This and cmx_svc_runtime() could be combined.
# ----------------------------------------------------------------------------------------
#
#      $ systemctl status cumulusmx | grep since
#        Active: active (running) since Thu 2017-10-19 17:34:34 EDT; 2 weeks 3 days ago
#
# ----------------------------------------------------------------------------------------
def last_restarted():
	global data
	######## load = subprocess.check_output(["/usr/bin/top", "-H", "-w", "125", "-n", "1", "-b", "-o", "+RES"])
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
			#  TO STRIP TIMEZONE #####  start_time = re.sub('...;.*', '', start_time)
			##########################################                                  break

	# messager( "DEBUG: CumulusXM service started at " + start_time )
	# messager( "DEBUG: CumulusXM service was started " + duration )
	timestamp = datetime.datetime.now().strptime(start_time, "%Y-%m-%d %H:%M:%S %Z")
	# print timestamp.strftime(strftime_FMT)

	data['mono_pid'] = mono_pid
	data['last_restarted'] = duration
	return duration

# ----------------------------------------------------------------------------------------
# Return run-time of cumulusmx service as fractional days - Excel-style date.
#
# ----------------------------------------------------------------------------------------
# NOTE: This and last_restarted() could be combined.
# ----------------------------------------------------------------------------------------
#      $ systemctl status cumulusmx | grep since
#        Active: active (running) since Thu 2017-10-19 17:34:34 EDT; 2 weeks 3 days ago
# ----------------------------------------------------------------------------------------
def cmx_svc_runtime():
	global data
	strftime_pattern = "%Y-%m-%d %H:%M:%S %Z"
	output = subprocess.check_output(["/bin/systemctl", "status", "cumulusmx"])
	lines = re.split('\n', output)

	for iii in range(0, len(lines)):
		if re.search('since', lines[iii]) :

			start_time = re.sub('.* since ... ', '', lines[iii])
			start_time = re.sub(';.*', '', start_time)
			#  TO STRIP TIMEZONE #####  start_time = re.sub('...;.*', '', start_time)
			break

	timestamp = datetime.datetime.now().strptime(start_time, strftime_pattern)
	start_secs = int(timestamp.strftime("%s"))
	now_secs = int(datetime.datetime.now().strftime("%s"))
	duration = now_secs - start_secs
	in_days = float(duration) / float( 60*60*24 )

	data['cmx_svc_runtime'] = in_days
	return in_days





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
	this_script = sys.argv[0]
	messager("  Starting " + this_script + "  PID=" + str(getpid()))

	write_pid_file()
	last_restarted()	# This reads the PID for the main mono process
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
