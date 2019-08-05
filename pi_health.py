#!/usr/bin/python
#
# Restart using...
#                                           kill -9 `cat /mnt/root/home/pi/watchdog.PID` ; nohup /usr/bin/python -u /mnt/root/home/pi/watchdog.py >> /mnt/root/home/pi/watchdog.log 2>&1 &
#
# Stop with ... 
#   kill -9 `cat watchdog.PID`
#
# Start with ...
#   nohup /usr/bin/python -u /mnt/root/home/pi/watchdog.py >> /mnt/root/home/pi/watchdog.log 2>&1 &
#
# ========================================================================================
# 20190722 RAD Hacked up mem_usage() because I found 2 versions of Raspbian were
#              generating rather different output fo the free command.
# 20190722 RAD Copied watchdog.py. Wanted a separate status tool for Pi in general
#              which could be access via a web server.
# ========================================================================================
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

# import urllib
# https://docs.python.org/2/howto/urllib2.html
# https://docs.python.org/2/library/urllib2.html
from urllib2 import urlopen, URLError, HTTPError

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
ws_data_last_count = 0
saved_contact_lost = -1     # Number of epoch secs when RF contact lost

BASE_DIR =              "/mnt/root/home/pi/Cumulus_MX"
data_stop_file =        BASE_DIR + "/web/DataStoppedT.txttmp"
ambient_temp_file =     BASE_DIR + "/web/ambient_tempT.txttmp"
status_page =           BASE_DIR + "/web/status.html"
events_page =           BASE_DIR + "/web/event_status.html"
mxdiags_dir =           BASE_DIR + "/MXdiags"
status_dir =            "/mnt/root/home/pi/status"

status_page =           "/mnt/root/home/pi/pi_health.html"
status_page =           "/mnt/root/home/pi/pi_health.html"
status_page =           "/mnt/root/home/pi/pi_health.html"
status_page =           "/mnt/root/home/pi/pi_health.html"
status_page =           "/home/pi/pi_health.html"

logger_file = sys.argv[0]
logger_file = re.sub('\.py', '.log', logger_file)

WEB_URL = "http://dillys.org/wx"
WEB_URL = "http://dilly.family/wx"

WS_Updates_URL = 	WEB_URL + "/WS_Updates.txt"
realtime_URL = 		WEB_URL + "/realtime.txt"

# NOTE We now have 2 cameras...
image_age_S_URL = 	WEB_URL + "/South/S_age.txt"
image_age_N_URL = 	WEB_URL + "/North/N_age.txt"
image_age_URL = 	WEB_URL + "/North/N_age.txt"
# N_Since_Updated_URL = 'http://dillys.org/wx/N_Since_Updated.txt'
#    Replaced by above

proc_stat_busy = -1		# Sentinal value
proc_stat_idle = -1
proc_stat_hist = []		# Holds last proc_stat_hist_n samples
proc_stat_hist_n = 10		# Control length of history array to keep

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
strftime_FMT = "%Y/%m/%d %H:%M:%S"
saved_exception_tstamp = "9999-99-9999:00:00.999:....."
saved_exception_tstamp = "X"

pcyc_holdoff_time = 0
WU_Cancels = 0

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



# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#	"mono_pid",
#	def cmx_svc_runtime(): SETS
#	def mono_threads(): READS
#
#	"watcher_pid",
#	PID for this process...  SET above
#
#	"last_restarted",
#	def cmx_svc_runtime(): SETS
#
#	"cmx_svc_runtime",
#	def cmx_svc_runtime(): SETS
#
#	"ws_data_stopped",
#	def ws_data_stopped(): SETS
#
#	"rf_dropped",
#	def rf_dropped() : SETS
#
#	"camera_down",
#	def camera_down(): SETS
#
#	"last_realtime",
#	def last_realtime(): SETS
#
#	"server_stalled",
#	def server_stalled(): SETS
#
#	"mono_threads",
#	def mono_threads(): SETS
#
#	"amb_temp",
#	def amb_temp(): SETS
#	COMES FROM THE WX STATION
#
#	"mono_version",
#	def mono_version(): SETS
#
#	"webcamwatch_down"
#	def webcamwatch_down(): SETS
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
data_keys = [
	"system_uptime",
	"proc_pct",
	"proc_load",
	"proc_load_5m",
	"effective_used",
	"mem_pct",
	"swap_used",
	"swap_pct",
	"cpu_temp_c",
	"cpu_temp_f",
	"python_version",
	]
	# amb_temp   {}

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# For HTML Table-style output lines
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# https://pyformat.info/
data_format = [
	"{} ago",
	"{:5.1f}%",
	"{:7.2f}",
	"{:7.2f}",
	"{} bytes",
	"{}&percnt;",
	"{} bytes",
	"{}&percnt;",
	"{:6.1f} &deg;C",
	"{:6.1f} &deg;F",
	"{}",
	]

thresholds = [
	-1,
	10.0,
	4.0,
	4.0,
	-1,
	15,
	1024,
	1,
	55,
	131,
	100,
	-1,
	]
	# amb_temp   {}


# ----------------------------------------------------------------------------------------
# For CSV-style output line
# ----------------------------------------------------------------------------------------
#       "date-time",
CSV_keys = [
	"server_stalled",
	"ws_data_stopped",
	"rf_dropped",
	"last_realtime",
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
	"cmx_svc_runtime",
	"webcamwatch_down"
	]

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
	"{:9.4f}",
	"{}",
	]

# This is used to determine which fields should trip the problem flag.
Prob_Track = [
	1,
	1,
	1,
	0,
	0,
	1,
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	0,
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
#  To Do:
#		last_realtime() return value should be leveraged <<<  OBSOLETE???????????????
# ----------------------------------------------------------------------------------------
def main():
	global data
	global Prob_Track

	python_version = "v " + str(sys.version)
	python_version = re.sub(' *\n *', '<BR>', python_version )
	python_version = re.sub(' *\(', '<BR>(', python_version )

	messager("INFO: Python version: " + str(sys.version))
	data['python_version'] = python_version

	iii = 0
	while True:
		# No longer used:
		#  if 0 == iii % log_header_stride:
			#   amb_temp()        # This won't / shouldn't change rapidly so sample periodically

			#   hdr = "date-time,"
			#   for jjj in range(0, len(CSV_keys)):
			#	hdr = hdr + " {},".format( CSV_keys[jjj] )

			#   print hdr

		# Capture the data by calling functions.  Ignore return values.
		#
		# No longer used:
		#   server_stalled()
		#   ws_data_stopped()
		#   rf_dropped()
		#   last_realtime()
		proc_load()
		proc_pct()
		#   camera_down()
		#   cmx_svc_runtime()
		#   mono_threads()
		mem_usage()
		#   webcamwatch_down()

		CSV_rec = datetime.datetime.now().strftime(strftime_FMT) + ","
		Prob_Flag = " ,"

		# No longer used:
		#   for jjj in range(0, len(CSV_keys)):
		#	format_str = " " + CSV_format[jjj] + ","
		#	CSV_rec = CSV_rec + format_str.format( data[CSV_keys[jjj]] )
		#	if Prob_Track[jjj] > 0 :
		#		if data[CSV_keys[jjj]] > 0 :
		#			Prob_Flag = " <<<<<,"

		#   print CSV_rec + Prob_Flag

		#   if 0 == iii % summary_stride :
		#	summarize()
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

		exit
		exit
		exit
		exit
		exit
		exit
		exit
		exit

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
	if "DOWN" in PID :
		return -1

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

#	FH = open(events_page , "a")
#	FH.write( format_str.format( ID, description, bgcolor, code) )
#	FH.close

	status_file = "{}/{}.txt".format( status_dir, time.time() )
	FH = open(status_file, "w+")
	FH.write( format_str.format( ID, description, bgcolor, code) )
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
# Near the bottom of this file there is a log fragment showing the messaging leading
# up to a restart of CMX.  The USB coms goes down periodically, and this seems to be
# the only way to fix it. Not sure the timing of that is right yet, and there are 3
# (now 4) different messages when we lose the USB.  That's messy buit largely working.
# It definately *evolved*, and could probably stand a re-write.
# 20180908
# ----------------------------------------------------------------------------------------
def ws_data_stopped():
	global data
	global ws_data_last_secs
	global ws_data_last_count
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
		ws_data_last_count += 1
		if ws_data_last_secs < 1 :
			ws_data_last_secs = int( datetime.datetime.utcnow().strftime("%s") )
			# Long message the first time we see this...
			messager( "WARNING:  CumulusMX reports data_stopped (<#DataStopped> == 1).   (code 101)" )
			log_event("", "CumulusMX reports data_stopped (<#DataStopped> == 1).", 101 )
		else:
			elapsed = int( datetime.datetime.utcnow().strftime("%s") ) -  ws_data_last_secs 
			if elapsed > 400 :
				messager( "WARNING:   systemctl restart cumulusmx.   (code 999)" )
				log_event("", "systemctl restart cumulusmx.", 999 )
				restart_cmd = ['/usr/bin/sudo',
					'systemctl',
					'restart',
					'cumulusmx']

				try :
					restart = subprocess.check_output( restart_cmd, stderr=subprocess.STDOUT )
				except:
					logger( "ERROR: Unexpected ERROR in restart: {}".format( sys.exc_info()[0] ) )

				# . . . . . . . . . . . . . . . . . . . . . . . . . . . .
				# Generally nothing, unless -verbose is used...
				# . . . . . . . . . . . . . . . . . . . . . . . . . . . .
				if len(restart) > 0 :
					logger( "DEBUG: restart returned data: \"" + restart + "\"" )
###########################################################################################################################################################################################################################################################################################################				exit()
				sleep( 10 )
				print "\n\n\n\n\n"
				messager( "INFO: systemctl restarted cumulusmx.   (code 998)" )
				log_event("", "systemctl restarted cumulusmx.", 998 )


			# Short message while this status continues
			elif 0 == ws_data_last_count % 3 :
				messager( "WARNING:  CumulusMX reports data_stopped ... " + str(elapsed) + " sec" )
	else:
		ws_data_last_secs = 0
		ws_data_last_count = 0
	data['ws_data_stopped'] = data_status
	return data_status

# ----------------------------------------------------------------------------------------
# Code on the server records checksum of the past 12 values of realtime.txt (after
# stripping off the timestamp). WS_Updates.txt is a count of the unique checksums
# in this mini log, across the past 12 updates to realtime.txt (12 minutes).
#
# Returns:
#   1 ==> data has stopped
#   0 ==> OK
# ----------------------------------------------------------------------------------------
def server_stalled():
	global data
	content = "1" # 20190529 - I guess if urlopen() fails, content may not be set...
	# --------------------------------------------------------------------------------
	#   2017/10/11 13:01:56 GMT,  0,  0,  0,  24,   0.01,  0,  89248,  9%,  0,  0%,  46.2,  46.160,   115.1,
	#   free|945512|271656|673856|6796|55352|127056|89248|856264|102396|0|102396
	# --------------------------------------------------------------------------------
	try:
		response = urlopen( WS_Updates_URL )
		content = response.read()
#@@@#
	except ( URLError, Exception ) as err :
	### >>>> except URLError as err :
	# At one point got "httplib.BadStatusLine: ''" (unhandled) - See below
		messager( "ERROR: in server_stalled: {}".format( sys.exc_info()[0] ) )
		if hasattr(err, 'reason'):
			messager( 'ERROR: We failed to reach a server.' )
			messager( 'ERROR: Reason: ()'.format( err.reason ) )
			# Avoid downstream issue working with this variable.
			content = "1"
		elif hasattr(err, 'code'):
			messager( 'ERROR: The server couldn\'t fulfill the request.' )
			messager( 'ERROR: code: ()'.format( err.code ) )
			# Avoid downstream issue working with this variable.
			content = "1"
####	else:
    # everything is fine
#	except :
#		print "Unexpected ERROR in server_stalled:", sys.exc_info()[0]
#		content = "1"      # Assume a bad answer...
	# .................................................................
	# Strip off the trailing newline which is helpful when catting on the other
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
	except :
		# .........................................................
		# Big value - obvious if debugging...
		# .........................................................
		unique_count = 99
	##_DEBUG_## ___print "wx/WS_Updates.txt = " + str( unique_count )
	if unique_count < 3 :
		data['server_stalled'] = 1
		messager( "WARNING:  unique_count =" + str(unique_count) + "; expected 12." + \
			"  realtime.txt data was not updated recently (last 45 mins)." )
		return 1
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
def last_realtime():
	global data
	global last_secs
	global last_date
	# --------------------------------------------------------------------------------
	#  09/10/17 12:02:47 73.0 92 70.6 3.1 4.5 270 ...
	#  09/10/17 12:03:11 73.0 92 70.6 3.1 4.5 270 ...
	#  Search for "20181015" to see an odd error I've gotten several times...
	#         BadStatusLine 
	# --------------------------------------------------------------------------------
	try :
		response = urlopen( realtime_URL )
		content = response.read()
	except ( URLError, Exception ) as err :
		messager( "ERROR: in last_realtime: {}".format( sys.exc_info()[0] ) )
		# ------------------------------------------------------------------------
		#  See https://docs.python.org/2/tutorial/errors.html (~ middle)
		# ------------------------------------------------------------------------
		messager( "ERROR: type: {}".format( type(err) ) )
		messager( "ERROR: args: {}".format( err.args ) )
		if hasattr(err, 'reason'):
			messager( 'ERROR: We failed to reach a server.' )
			messager( 'ERROR: Reason: ()'.format( err.reason ) )
		elif hasattr(err, 'code'):
			messager( 'ERROR: The server couldn\'t fulfill the request.' )
			messager( 'ERROR: code: ()'.format( err.code ) )
		# ------------------------------------------------------------------------
		#  https://docs.python.org/2/tutorial/errors.html
		#  https://docs.python.org/2/library/sys.html
		#  https://docs.python.org/3/library/traceback.html
		#  https://docs.python.org/2/library/traceback.html
		#
		#  https://stackoverflow.com/questions/8238360/how-to-save-traceback-sys-exc-info-values-in-a-variable
		# ------------------------------------------------------------------------
		content = "00/00/00 00:00:00 45.5 80 39.7 0.0 0.7 360 0.00 0.05 30.14 N 0 mph ..."
		messager( "DEBUG: content = \"" + content + "\" in last_realtime()" )

	words = re.split(' +', content)

	# --------------------------------------------------------------------------------
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
	# --------------------------------------------------------------------------------
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

	# --------------------------------------------------------------------------------
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
	# --------------------------------------------------------------------------------
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
	uptime = re.sub('.*up *', '', load)
	uptime = re.sub(',.*', '', uptime)

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
	data['system_uptime'] = uptime
	return cur_proc_load


	if cur_proc_load > proc_load_lim :
		messager( "WARNING: 1 minute load average = " + str(cur_proc_load) + \
			";  proc_load_lim = " + str(proc_load_lim) )
		return 1
	else:
		return 0



# ----------------------------------------------------------------------------------------
# 
# NOTE: This is sort of a hack.  WU has been behaving badly so I'm not tracking it...
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
				messager( "DEBUG:  Sensor RF contact appears to have been restored after " + str(elapsed) + " sec  (code 116)")
				log_event("", "DEBUG:  Sensor RF contact <B>appears</B> to have been restored. Out for " + str(elapsed) + " sec", 116 )
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
	global WU_Cancels
	check_lines = 12
	return_value = 0
	logger_code =111
	file_list = listdir( mxdiags_dir )

	file_list.sort()

	#  At time I collect files here, so look at the whole list if need be...
	count = len( file_list )
	for iii in range(-1, -1 * count, -1):
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

		if "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.Exception" in lineList[iii] :
#WU#		if "Exception" in lineList[iii] :
			exception_tstamp = re.sub(r'([-0-9]+ [\.:0-9]+).*', r'\1', lineList[iii] )
			# If this is an Exception we've not seen before
			if saved_exception_tstamp != exception_tstamp :
				# --------------------------------------------------------
				# This is the signature of the most common exception we seem to see.
				# --------------------------------------------------------
				# That said, these all seem to come from WU, Weather Underground processing
				#   WU update:    at System.Net.WebConnection.HandleError
				#
				# Did a little investigation to check that...
				#     pi@raspberrypi_02:/mnt/root/home/pi/Cumulus_MX/MXdiags $ ls 2*txt
				#     20180204-140446.txt  20180503-213654.txt  20180523-155342.txt  20180604-131915.txt
				#     20180204-150113.txt  20180510-081824.txt  20180524-075048.txt  20180607-082958.txt
				#     pi@raspberrypi_02:/mnt/root/home/pi/Cumulus_MX/MXdiags $ grep Exception 2*txt|wc
				#        1867   20537  302454
				#     pi@raspberrypi_02:/mnt/root/home/pi/Cumulus_MX/MXdiags $ grep Exception 2*txt|grep -v 'WU update:'|wc
				#           0       0       0
				#     pi@raspberrypi_02:/mnt/root/home/pi/Cumulus_MX/MXdiags $
				# --------------------------------------------------------

				if "WU update:    at System.Net.WebConnection.HandleError(WebExceptionStatus" in lineList[iii] :
#WU# This whole if block is never executed if saved_exception_tstamp never changes
#WU#					logger_code =110
#WU#					saved_exception_tstamp = exception_tstamp 
#@@@#					pass
					pass
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
				messager( "WARNING:  Sensor RF contact lost; ignoring outdoor data.  " + \
					"Press \"V\" button on WS console   (code 115)" )
				log_event("", "Sensor RF contact lost; ignoring outdoor data.", 115 )
			else:
				elapsed = int( datetime.datetime.utcnow().strftime("%s") ) -  saved_contact_lost 
				# Shorter message while this status continues
				messager( "WARNING:  Sensor RF contact lost; ... " + str(elapsed) + " sec" )

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
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		# 20181116 RAD WU_Cancels added
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		#
		# NOTE:  This caused a 24 hour outage with Weather Underground
		# NOTE:  This caused a 24 hour outage with Weather Underground
		# NOTE:  This caused a 24 hour outage with Weather Underground
		# NOTE:  This caused a 24 hour outage with Weather Underground
		# NOTE:  This caused a 24 hour outage with Weather Underground
		# NOTE:  This caused a 24 hour outage with Weather Underground
		#
		# 2018/11/15 13:32:56, 0, 0, 0,  24,    0.00, 0,    16, 138936, 14%,   2356,  2%, 38.1c, 100.6f,  63.7f,   0.4%,   17.6674, 0, ,
		# 2018/11/15 13:33:21, 0, 0, 0,  24,    0.00, 0,    16, 138860, 14%,   2356,  2%, 37.6c,  99.6f,  63.7f,   0.4%,   17.6677, 0, ,
		# 77265	2018-11-15 13:30:03.554 WeatherCloud Response: OK: 200
		# 77266	2018-11-15 13:31:00.994 WU Response: OK: success
		# 77267	
		# 77268	2018-11-15 13:33:40.825 WU update: The Task was canceled
		# 2018/11/15 13:33:45 WARNING:   "The Task was canceled"  from  /mnt/root/home/pi/Cumulus_MX/MXdiags/20181028-223154.txt
		# 
		#   * * * * *  almost 700 of this in MXdiags  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
		#
		# 79363	2018-11-16 12:30:02.904 WeatherCloud Response: OK: 200
		# 79364	2018-11-16 12:31:40.696 WU update: The Task was canceled
		# 79365	2018-11-16 12:33:40.659 WU update: The Task was canceled
		# 2018/11/16 12:33:45 WARNING:   "The Task was canceled"  from  /mnt/root/home/pi/Cumulus_MX/MXdiags/20181028-223154.txt
		#
		# 2018/11/16 12:33:46, 0, 0, 0,  23,    0.00, 0,    17, 129992, 13%,   2852,  2%, 37.6c,  99.6f,  63.7f,   0.9%,   18.6263, 0, ,
		# 2018/11/16 12:34:10, 0, 0, 0,   0,    0.30, 0,    12, 146404, 15%,   2780,  2%, 38.6c, 101.5f,  63.7f,  15.5%,    0.0002, 0, ,
		# 2018/11/16 12:34:35, 0, 0, 0,  45,    0.22, 0,    13, 147356, 15%,   2780,  2%, 38.6c, 101.5f,  63.7f,   1.3%,    0.0005, 0, ,
		#
		# ------------------------------------------------------------------------
		#   The WU handling is a mess.  Some of it is WU and some of it is
		#   CMX.  The above, almost 24 hour outage was fixed by restarting
		#   the systemctl cumulusmx process.  It's still spewing a lot of the
		#   exception errors, but some data is getting through.
		#
		#   To handle this case we could keep an array of timestamps of
		#   times we saw a "WU update: The Task was canceled" - a special
		#   case of the else test below.  If we keep pruning that array to
		#   some fixed period, say an hour, and if the array size grows to
		#   something near 60 members (1 for each minute), we could
		#   restart CMX.  This doesn't happen often, but I believe we've
		#   seen it several times.
		#
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		# ------------------------------------------------------------------------
		elif "WU update: The Task was canceled" in lineList[iii] :
			WU_Cancels += 1
			messager( "WARNING:   The WEATHER UNDERGROUND Task was canceled Instance # {}".format( WU_Cancels ) )

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
			WU_Cancels = 0
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
					log_event("", "Sensor RF contact RESTORED; receiving telemetry again. " + str(elapsed) + " sec", 116 )
					messager( "INFO:  Sensor RF contact RESTORED; ... lost for " + str(elapsed) + " sec   (code 116)" )
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
#  Check webcam status by fetching a control file from the hosted web-server.
#  The file just contains a number - the number of seconds between the time of
#  last writing the generically-named full-size image file, e.g. N.jpg by FTP,
#  an the current time.  Since cron_10_min.sh runs every 5 minutes
#
#   Can verify with: curl http://dillys.org/wx/North/N_age.txt
#
#    Copied from "webcamwatch.py" and modified for here...
#
#  NOTE: Should make the camera a parameter.  2 things affected:
#           * The URL to check
#           * The index to store in data[]
#
#  NOTE: Question:  Is pcyc_holdoff_time really required?  It adds complexity...
#
# ----------------------------------------------------------------------------------------
def camera_down():
	global data
	global pcyc_holdoff_time
	age = ""
	is_down = 1

	try:
		response = urlopen( image_age_URL )
		age = response.read()
		age = age.rstrip()
	except ( URLError, Exception ) as err :
	### >>>> except URLError as err :
		messager( "ERROR: in camera_down: {}".format( sys.exc_info()[0] ) )
		if hasattr(err, 'reason'):
			messager( 'ERROR: We failed to reach a server.' )
			messager( 'ERROR: Reason: ()'.format( err.reason ) )
		elif hasattr(err, 'code'):
			messager( 'ERROR: The server couldn\'t fulfill the request.' )
			messager( 'ERROR: code: ()'.format( err.code ) )
		age = "0"
		logger("WARNING: Read URL failed.  Assumed image age: {}".format( age ) )


	# --------------------------------------------------------------------------------
	# Keep as string up until this point, because of...
	#      TypeError: object of type 'int' has no len()
	# --------------------------------------------------------------------------------
	if len( age ) < 1 :
		age = "0"
		logger("WARNING: Read null.  Assumed image age: {}".format( age ) )

	# --------------------------------------------------------------------------------
	#
	# --------------------------------------------------------------------------------
	if int(age) > 600 :
		logger("WARNING: Old image age: {}".format( age ) )
		## power_cycle()

		# ------------------------------------------------------------------------
		#  NOTE: This pcyc_holdoff_time business may not be needed.
		#  Seems to me we only want to avoid power-cycling the webcam repeatedly
		#  We are not doing that from here at the moment...
		# ------------------------------------------------------------------------
		if pcyc_holdoff_time > 0 :
			if int(time.strftime("%s")) > pcyc_holdoff_time :
				# holdoff has expired
				logger("WARNING: Waiting on webcam image update at web server.")
				###### if data['camera_down'] == 0 :
				######	log_event("", " waiting on webcam image update.", 104 )
		else:
			pcyc_holdoff_time = int(time.strftime("%s")) + 600
			logger("DEBUG: power cycle needed.")
			log_event("", " Webcam image update stalled.", 103 )

	else:
		is_down = 0
		if data['camera_down'] == 1 :
			log_event("", " Webcam image updating!.", 105 )
		pcyc_holdoff_time = 0


	data['camera_down'] = is_down
	return is_down


# ----------------------------------------------------------------------------------------
# Return run-time of cumulusmx service as fractional days - Excel-style date.
#
# 2017-12-22 def last_restarted() was rolled into this routine.
# ----------------------------------------------------------------------------------------
def cmx_svc_runtime():
	global data
	lines = [ "   Active: active (running) since DOWN; DOWN", " Main PID: DOWN (mono)" ]

	try :
		output = subprocess.check_output(["/bin/systemctl", "status", "cumulusmx"])
		lines = re.split('\n', output)
	except :
		messager( "ERROR: From systemctl status: {}".format( sys.exc_info()[0] ) )
####		lines[0] = "   Active: active (running) since DOWN; DOWN"
####		lines[1] = " Main PID: DOWN (mono)"

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#   Active: active (running) since Sat 2018-06-23 10:10:30 EDT; 4s ago
	# Main PID: 3364 (mono)
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#   Active: activating (auto-restart) (Result: signal) since Tue 2018-12-25 09:04:04 EST; 4s ago
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
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
			duration = re.sub('min', ' min', duration)


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#  Handle case where we DO NOT have a properly formatted date...
	#   Active: active (running) since Sat 2018-06-23 10:10:30 EDT; 4s ago
	#   Active: activating (auto-restart) (Result: signal) since Tue 2018-12-25 09:04:04 EST; 4s ago
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	try :
		timestamp = datetime.datetime.now().strptime(start_time, "%Y-%m-%d %H:%M:%S %Z")
		start_secs = int(timestamp.strftime("%s"))
	except :
		# Set the start time to now so runtime is (near) zero or negative
		start_secs = int(datetime.datetime.now().strftime("%s")) - 2


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
	lines = [ "   Active: active (running) since DOWN; DOWN", "", "" ]

	try :
		output = subprocess.check_output(["/bin/systemctl", "status", "wxwatchdog"])
		lines = re.split('\n', output)
	except :
####		messager( "ERROR: From systemctl status: {}".format( sys.exc_info()[0] ) )
		lines[2] = ""


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
# Write message to the log file with a leading timestamp.
#
# NOTE: This just calls messager() at the moment.  (Not exactly sure why I did this...
#       testing maybe?) (There are about 4X as many calls to messager() at the moment.)
#
# NOTE: Most of the calls to messager() should be converted to logger() at some point.
#	especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	# This is not being launched automatically and output is redirected to the log.
	messager(message)
#############################################################################
####	timestamp = datetime.datetime.now().strftime(strftime_FMT)
####
####	FH = open(logger_file, "a")
####	FH.write( "{} {}\n".format( timestamp, message) )
####	FH.close
#############################################################################

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)

# ----------------------------------------------------------------------------------------
# Print and log the message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def log_and_message(message):
	messager(message)
	logger(message)


# ----------------------------------------------------------------------------------------
# Write the PID of this Python script to a .PID file by the name name.
# This gets run at script start-up.
# ----------------------------------------------------------------------------------------
def write_pid_file():
	PID = str(getpid()) + "\n"
	pid_file = sys.argv[0]
	pid_file = re.sub('\.py', '.PID', pid_file)

	messager( "DEBUG: Writing {}".format( pid_file ) )

	FH = open(pid_file, "w")
	FH.write(PID)
	FH.close



# ----------------------------------------------------------------------------------------
# This generates a Raspberry Pi Status page, which Cumulus MX ftp's to the server.
# It is mostly an HTML table.
#
# ----------------------------------------------------------------------------------------
def summarize():
	timestamp = datetime.datetime.utcnow().strftime(strftime_FMT)

	# No longer used:
	#   cmx_svc_runtime()

	FH = open(status_page , "w")

	FH.write( "<HEAD><TITLE>\n" )
	FH.write( "Raspberry Pi Health\n" )
	FH.write( "</TITLE></HEAD><BODY BGCOLOR=\"#555555\" TEXT=\"#FFFFFF\" LINK=\"#FFFF00\" VLINK=\"#FFBB00\" ALINK=\"#FFAAFF\"><H1 ALIGN=center>\n" )
	FH.write( "Raspberry Pi Health\n" )
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
#@@@
#		print " - - - - - - "
#		print iii
#		print data_format[iii]
#		print bgcolor
#		print data_keys[iii]
#		print data[data_keys[iii]]
#		print thresholds[iii]
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
	FH.write( " <!-- FOOTER -->\n" )
  	FH.write( "  <tr>\n" )

	FH.write( "    <td align=\"center\" class=\"td_navigation_bar\">:<a href=\"index.htm\">now</a>::<a href=\"gauges.htm\">gauges</a>:" + \
		":<a href=\"today.htm\">today</a>::<a href=\"yesterday.htm\">yesterday</a>::<a href=\"thismonth.htm\">this&nbsp;month</a>:" + \
		":<a href=\"thisyear.htm\">this&nbsp;year</a>:\n" )
	FH.write( "    <br>:<a href=\"record.htm\">records</a>::<a href=\"monthlyrecord.htm\">monthly&nbsp;records</a>:" + \
		":<a href=\"trends.htm\">trends</a>::<a TARGET=\"_blank\" HREF=\"http://sandaysoft.com/forum/\">forum</a>:" + \
		":<a href=\"" + WEB_URL + "\">webcam</a>:\n" )
	FH.write( "    <br>:<a TARGET=\"_blank\" HREF=\"https://app.weathercloud.net/d0208473809#current\">Weathercloud</a>:" + \
		":<a TARGET=\"_blank\" HREF=\"https://www.pwsweather.com/obs/RADILLY.html\">PWS&nbsp;Weather</a>:" + \
		":<a TARGET=\"_blank\" HREF=\"https://wx.aerisweather.com/local/us/pa/mcmurray\">AerisWeather</a>:" + \
		":<a TARGET=\"_blank\" HREF=\"https://radar.weather.gov/Conus/full_loop.php\">NWS&nbsp;Composite&nbsp;US&nbsp;Radar</a>:\n" + \
		":<a TARGET=\"_blank\" HREF=\"https://www.windy.com/40.279/-80.089?39.317,-80.089,7,m:eMiadVG\">Windy</a>:\n" )
	FH.write( "    <br>:<a href=\"status.html\">Pi status</a>:" + \
		":<a href=\"event_status.html\">Event&nbsp;Log</a>:\n" + \
		":<a href=\"procs.html\">Check&nbsp;Procs</a>:\n" + \
		":<a TARGET=\"_blank\" HREF=\"https://www.wunderground.com/personal-weather-station/dashboard?ID=KPAMCMUR4\">KPAMCMUR4</a>:</td>\n" )

  	FH.write( "  </tr>\n\n" )
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
# From raspberrypi_03 . . . . . .
#                 total        used        free      shared  buff/cache   available
#   Mem:         949444       42700       97504       48112      809240      793092
#   Swap:        102396           0      102396
# 20190805 - On this system the '-/+ buffers/cache:' lines was missing, and maybe
#            rolled into the line above in some way.
#
#   0   945512 mem_total	# - Referenced
#   1   311232 mem_used		# -
#   2   634280 mem_free		# -
#   3     6768 shared		# -
#   4    83880 buffers		# -
#   5   128100 cached		# -
#   6    99252 bu_ca_used	# -
#   7   846260 bu_ca_free	# - Referenced
#   8   102396 swap_total	# - Referenced
#   9        0 swap_used	# - Referenced
#  10   102396 swap_free	# -
#
#		swap_pct = 100 * swap_used / swap_total
#		effective_used = mem_total - bu_ca_free
#		mem_pct = 100 * effective_used / mem_total
#		data['swap_used'] = swap_used
#		data['swap_pct'] = swap_pct
#		data['effective_used'] = effective_used 
#		data['mem_pct'] = mem_pct
#
#   0   MemTotal:         949444 kB   <---
#   .   MemFree:           94228 kB
#   .   MemAvailable:     791532 kB   <---
#   4   Buffers:           63852 kB
#   5   Cached:           686676 kB
#   .   SwapCached:            0 kB
#   .   Active:           360448 kB
#   .   Inactive:         408048 kB
#   .   Active(anon):      13604 kB
#   .   Inactive(anon):    52472 kB
#   .   Active(file):     346844 kB
#   .   Inactive(file):   355576 kB
#   .   Unevictable:           0 kB
#   .   Mlocked:               0 kB
#   8   SwapTotal:        102396 kB   <---
#  10   SwapFree:         102396 kB   <---
#
#		data['swap_used'] = SwapTotal - SwapFree
#		data['swap_pct'] = 100 * (SwapTotal - SwapFree) / SwapTotal
#		data['effective_used'] = MemTotal - MemAvailable
#		data['mem_pct'] = 100 * (MemTotal - MemAvailable) / MemTotal
#
# See:
#   http://www.linuxatemyram.com/http://www.linuxatemyram.com/
#   http://www.linuxnix.com/find-ram-size-in-linuxunix/
#
# ----------------------------------------------------------------------------------------
#   Distributor ID: Raspbian
#   Description:    Raspbian GNU/Linux 9.9 (stretch)
#   Release:        9.9
#   Codename:       stretch
#
#   DEBUG: --->
#                 total        used        free      shared  buff/cache   available
#   Mem:         949444       44524       94176       48112      810744      791276
#   Swap:        102396           0      102396
#
#   DEBUG:    0
#   DEBUG:    1 total
#   DEBUG:    2 used
#   DEBUG:    3 free
#   DEBUG:    4 shared
#   DEBUG:    5 buff/cache
#   DEBUG:    6 available
#   Mem:
#   DEBUG:    7 949444
#   DEBUG:    8 44524
#   DEBUG:    9 94176
#   DEBUG:   10 48112
#   DEBUG:   11 810744
#   DEBUG:   12 791276
#   Swap:
#   DEBUG:   13 102396
#   DEBUG:   14 0
#   DEBUG:   15 102396
# ----------------------------------------------------------------------------------------
#   Distributor ID: Raspbian
#   Description:    Raspbian GNU/Linux 8.0 (jessie)
#   Release:        8.0
#   Codename:       jessie
#
#   DEBUG: --->
#                total       used       free     shared    buffers     cached
#   Mem:        945512     905728      39784      48996     303816     135856
#   -/+ buffers/cache:     466056     479456
#   Swap:       102396      35860      66536
#
#   DEBUG:    0
#   DEBUG:    1 total
#   DEBUG:    2 used
#   DEBUG:    3 free
#   DEBUG:    4 shared
#   DEBUG:    5 buffers
#   DEBUG:    6 cached
#   Mem:
#   DEBUG:    7 945512
#   DEBUG:    8 906364
#   DEBUG:    9 39148
#   DEBUG:   10 48996
#   DEBUG:   11 304104
#   DEBUG:   12 135864
#   -/+
#   DEBUG:   13 buffers/cache:
#   DEBUG:   14 466396
#   DEBUG:   15 479116
#   Swap:
#   DEBUG:   16 102396
#   DEBUG:   17 35860
#   DEBUG:   18 66536
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#    https://blog.sleeplessbeastie.eu/2018/01/31/how-to-parse-free-output-to-display-available-memory/
#    https://www.thegeekdiary.com/understanding-proc-meminfo-file-analyzing-memory-utilization-in-linux/
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#   cat /proc/meminfo
#   MemTotal:         949444 kB
#   MemFree:           97448 kB
#   MemAvailable:     794576 kB
#   Buffers:           63852 kB
#   Cached:           686600 kB
#   SwapCached:            0 kB
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def mem_usage():
	global data

	free = subprocess.check_output(["/usr/bin/lsb_release", "-a"])
	print "DEBUG: --->\n{}".format( free )

	free = subprocess.check_output(["/usr/bin/free", "-V"])
	print "DEBUG: --->\n{}".format( free )

	free = subprocess.check_output(["/usr/bin/free"])

	print "DEBUG: --->\n{}".format( free )

	words = re.split(' +', free)
	for iii in range(0, len(words)):
		print "DEBUG: {:4d} {}".format( iii, words[iii])

	meminfoarray = dict()
	meminfo = subprocess.check_output(["/bin/cat", "/proc/meminfo"])
	print "DEBUG: --->\n{}".format( meminfo )
	line = re.split("\n", meminfo )
	for iii in range(0, len(line)):
#		print line[iii]
		tok = re.split("[: ]*", line[iii])
#		for jjj in range(0, len(tok)):
#			print "{:5d} {}".format(jjj, tok[jjj])
#		print "len = {}".format( len(tok) )
		if len(tok) == 3 :
			meminfoarray[ tok[0] ] = tok[1]
	print meminfoarray

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
	mem_used = int(words[1])	# Not referenced
	mem_free = int(words[2])	# Not referenced

	shared = words[3]		# Not referenced
	buffers = words[4]		# Not referenced
	cached = words[5]		# Not referenced

	bu_ca_used = int(words[6])	# Not referenced
	bu_ca_free = int(words[7])

	swap_total = int(words[8])
	swap_used = int(words[9])
	data['swap_used'] = swap_used
	swap_free = int(words[10])	# Not referenced

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
#  Fetch the version of mono
#
# ----------------------------------------------------------------------------------------
def mono_version():
	global data

	try :
		response = subprocess.check_output(["/usr/bin/mono", "-V"])
		line = re.split('\n', response)
		tok = re.split(' *', line[0])
		version = tok[4]
	except :
		messager( "ERROR: From mono version check: {}".format( sys.exc_info()[0] ) )
		version = "Not found"

	data['mono_version'] = version
	return version






# ----------------------------------------------------------------------------------------
#
#
#
#
#
#
#
#
# ----------------------------------------------------------------------------------------
def make_page() :
	global data
	#### if sys.argv[1] = "stop"
	this_script = sys.argv[0]

	#   print "\n\n\n\n\n"

	#   messager("INFO: Starting " + this_script + "  PID=" + str(getpid()))

	#   write_pid_file()
	#   cmx_svc_runtime()	# This reads the PID for the main mono process

	#   messager("INFO: Mono version: {}" .format( mono_version() ) )

	#   messager("DEBUG: Logging to {}" .format( logger_file ) )

	python_version = "v " + str(sys.version)
	python_version = re.sub(' *\n *', '<BR>', python_version )
	python_version = re.sub(' *\(', '<BR>(', python_version )

	#   messager("INFO: Python version: " + str(sys.version))
	data['python_version'] = python_version

	proc_load()
	proc_pct()
	mem_usage()

	summarize()

	exit()
	exit()
	exit()
	exit()
	exit()
	exit()

# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
	make_page()

# ----------------------------------------------------------------------------------------
#   2.7.9 (default, Sep 17 2016, 20:26:04)
#   [GCC 4.9.2]
# ----------------------------------------------------------------------------------------
