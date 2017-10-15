#!/usr/bin/python
#
# Stop with ...  sudo kill -9 `cat watchdog.PID`
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
sleep_for = 300
sleep_for = 24
sleep_on_recycle = 600
log_stride = 18

last_secs = 999999          # This is a sentinel value for startup.
last_date = ""
proc_load_lim = 4.0         # See https://www.booleanworld.com/guide-linux-top-command/
mem_usage_lim = 85

### /home/pi/Cumulus_MX/DataStopped.sh
data_stop_file = "/home/pi/Cumulus_MX/web/DataStoppedT.txttmp"
logger_file = sys.argv[0]
logger_file = re.sub('\.py', '.log', logger_file)

strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
saved_exception_tstamp = "9999-99-9999:00:00.999:....."

pcyc_holdoff_time = 0


# https://www.python-course.eu/dictionaries.php
# https://docs.python.org/2/tutorial/datastructures.html#dictionaries
#
data = { 'pid' : getpid() }

data_keys = [ "pid", "server_stalled", "ws_data_stopped", "rf_dropped", "realtime_stalled",
	"proc_load", "camera_down", "effective_used", "mem_pct", "swap_used",
	"swap_pct", "cpu_temp", "cpu_temp_f"]
#
#
#                          pid
#                          >>>                    date-time
#                          server_stalled
#                          ws_data_stopped
#                          rf_dropped
#                          realtime_stalled
#                          proc_load
#                          camera_down
#                          effective_used
#                          mem_pct
#                          swap_used
#                          swap_pct
#                          >>>                    cpu_t
#                          cpu_temp
#                          cpu_temp_f
#
#
#

# exit

# ----------------------------------------------------------------------------------------
#
# Main loop
#
#  To Do:
#		realtime_stalled() return value should be leveraged
# ----------------------------------------------------------------------------------------
def main():
	iii = 0
	### logger("Staring " + sys.argv[0])
	exit
	while True:
		if 0 == iii % log_stride:
			print "date-time, server_stalled, ws_data_stopped, rf_dropped, " + \
				"realtime_stalled, proc_load, camera_down, " + \
				"effective_used, mem_pct, swap_used, swap_pct, " + \
				"cpu_t, cpu_temp, cpu_temp_f "

		print datetime.datetime.utcnow().strftime(strftime_GMT) + \
			",  {},  {},  {},  {},  {:5.2f},  {},".format( server_stalled(), ws_data_stopped(), \
			rf_dropped(), realtime_stalled(), proc_load(), camera_down() ) + \
			 mem_usage()
		############################################################
		### ___print datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S GMT") + \
		### 	mem_usage() + \
		############################################################
		### 	" server_stalled() = " + str( server_stalled() ) + \
		### 	" ws_data_stopped = " + str( ws_data_stopped() ) + \
		### 	" proc_load = " + str( proc_load() ) + \
		### 	mem_usage() + \
		### 	"| rf_dropped() = " + str(rf_dropped())
		############################################################
		###  ___print datetime.datetime.utcnow().strftime("%Y%m%d %H:%M:%S GMT")
		###  ___print "server_stalled() = " + str( server_stalled())
		###  ___print "ws_data_stopped = " + str( ws_data_stopped() )
		############################################################

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		#  https://pythonspot.com/en/ftp-client-in-python/
		#  https://docs.python.org/2/library/ftplib.html
		#  http://api.highcharts.com/highstock/Highcharts.stockChart
		#  https://www.highcharts.com/products/highcharts/
		#  https://www.highcharts.com/products/highcharts/
		#  https://www.highcharts.com/docs/working-with-data/data-module
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if 999 == iii % 3 :
			print "<TABLE>"
			for iii in range(0, len(data)):
				print "<TR><TD> {} </TD><TD> {} </TD></TR>".format( data_keys[iii], data[ data_keys[iii] ] )
			print "</TABLE>"
	#		for key in data :
	#			print key, data[key]


		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		#		swap_pct 0
		#		swap_used 500
		#		cpu_temp 38.089
		#		mem_pct 34
		#		rf_dropped 0
		#		effective_used 323012
		#		pid 16978
		#		cpu_temp_f 100.5602
		#		realtime_stalled -2
		#		proc_load 0.24
		#		server_stalled 0
		#		ws_data_stopped 0
		#		camera_down 0
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .



		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Periodically put a record into the log for reference.
		#___# if 0 == iii % log_stride:
			#___# logger(words[0] + " " + words[2])
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

		iii += 1
		sleep(sleep_for)

# ----------------------------------------------------------------------------------------
#
#
#
#   https://www.cyberciti.biz/faq/linux-find-out-raspberry-pi-gpu-and-arm-cpu-temperature-command/
#   https://www.raspberrypi.org/forums/viewtopic.php?t=47469
#   https://www.raspberrypi.org/forums/viewtopic.php?t=190489 - Temp and Freq !!
#   https://www.raspberrypi.org/forums/viewtopic.php?t=39953
#   https://raspberrypi.stackexchange.com/questions/56611/is-this-idle-temperature-normal-for-the-rpi-3
#
#
#
#  We could definately round this.   It appears to be quantized .... and maybe close to Farherheit
# ----------------------------------------------------------------------------------------
def read_cpu_temp():
	FH = open("/sys/class/thermal/thermal_zone0/temp", "r")
	CPU_Temp = float( FH.readline() )
	FH.close
	return CPU_Temp / 1000.0


# ----------------------------------------------------------------------------------------
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
	timestamp = datetime.datetime.utcnow().strftime(strftime_GMT)

	print timestamp + " " + message

	if 0 > 1 :
		FH = open(logger_file, "a")
		FH.write(timestamp + message + "\n")
		FH.close

# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.utcnow().strftime(strftime_GMT)
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
	FH = open(data_stop_file, "r")
	data_status = int( FH.readline() )
	FH.close
	if data_status > 0 :
		print "WARNING:  CumulusMX reports data_stopped (<#DataStopped> == 1)."
	data['ws_data_stopped'] = data_status
	return data_status

# ----------------------------------------------------------------------------------------
# Code on the server records checksum of the past 10 values of
#   1 ==> data has stopped
#   0 ==> OK
#
# ----------------------------------------------------------------------------------------
def server_stalled():
	global data
	# --------------------------------------------------------------------------------
	#   2017/10/11 13:01:56 GMT,  0,  0,  0,  24,   0.01,  0,  89248,  9%,  0,  0%,  46.2,  46.160,   115.1,
	#   free|945512|271656|673856|6796|55352|127056|89248|856264|102396|0|102396
	#   Traceback (most recent call last):
	#     File "/mnt/root/home/pi/watchdog.py", line 759, in <module>
	#       main()
	#     File "/mnt/root/home/pi/watchdog.py", line 130, in main
	#       rf_dropped(), realtime_stalled(), proc_load(), camera_down() ) + \
	#     File "/mnt/root/home/pi/watchdog.py", line 306, in server_stalled
	#       response = urllib.urlopen('http://dillys.org/wx/WS_Updates.txt')
	#     File "/usr/lib/python2.7/urllib.py", line 87, in urlopen
	#       return opener.open(url)
	#     File "/usr/lib/python2.7/urllib.py", line 213, in open
	#       return getattr(self, name)(url)
	#     File "/usr/lib/python2.7/urllib.py", line 350, in open_http
	#       h.endheaders(data)
	#     File "/usr/lib/python2.7/httplib.py", line 1035, in endheaders
	#       self._send_output(message_body)
	#     File "/usr/lib/python2.7/httplib.py", line 879, in _send_output
	#       self.send(msg)
	#     File "/usr/lib/python2.7/httplib.py", line 841, in send
	#       self.connect()
	#     File "/usr/lib/python2.7/httplib.py", line 822, in connect
	#       self.timeout, self.source_address)
	#     File "/usr/lib/python2.7/socket.py", line 553, in create_connection
	#       for res in getaddrinfo(host, port, 0, SOCK_STREAM):
	#   IOError: [Errno socket error] [Errno -2] Name or service not known
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
		print "DEBUG: WS_Updates.txt looks short = \"" + content.rstrip() + "\""

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
		print "WARNING:  unique_count =" + str(unique_count) + "; expected 12." + \
			"  realtime.txt data was not updated recently (last 45 mins)."
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
	global last_secs
	global last_date
	#  ---------------------------------------------------------------------
	#  09/10/17 12:02:47 73.0 92 70.6 3.1 4.5 270 ...
	#  09/10/17 12:03:11 73.0 92 70.6 3.1 4.5 270 ...
	#  ---------------------------------------------------------------------
	response = urllib.urlopen('http://dillys.org/wx/realtime.txt')
	content = response.read()
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
		date_str = "0000/00/00"
		timestamp = "00:00:00"
		seconds = last_secs
		diff_secs = -1
	else:
		date_str = words[0]
		timestamp = words[1]
		########## ___print timestamp
		words = re.split(':', timestamp)
		seconds = int(words[2]) + 60 * ( int(words[1]) + ( 60 * int(words[0]) ) )
		diff_secs = seconds - last_secs

	#  ---------------------------------------------------------------------
	#  date-time, server_stalled, ws_data_stopped, rf_dropped, realtime_stalled, proc_load, 
	#  2017/09/17 22:11:35 GMT,  0,  0,  0,  24,  0.0,  101092,  10%,  0,  0%,
	#  free|945512|560028|385484|6768|317364|141572|101092|844420|102396|0|102396
	#  2017/09/17 22:11:59 GMT,  0,  0,  0,  -65471,  0.0,  101244,  10%,  0,  0%,
	#  free|945512|560184|385328|6768|317368|141572|101244|844268|102396|0|102396
	#  WARNING: 65543 elapsed since realtime.txt was updated.
	#  2017/09/17 22:12:24 GMT,  0,  0,  0,  65543,  0.0,  101148,  10%,  0,  0%,
	#  free|945512|560088|385424|6768|317368|141572|101148|844364|102396|0|102396
	#  2017/09/17 22:12:48 GMT,  0,  0,  0,  24,  0.0,  101180,  10%,  0,  0%,
	#  free|945512|560136|385376|6768|317380|141576|101180|844332|102396|0|102396
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
		print "WARNING: " + str(diff_secs) + " elapsed since realtime.txt was updated."
	elif diff_secs < -2000 :
		stat_text = "NOT UPDATED"
		status = -1
		print "DEBUG: Got large negative value from record:\n\t" + content
#		for item in content :
#			print "    " + item
		if last_date != date_str :
			print "DEBUG: Likely the day rolled over as save date does not match..."
			if seconds < 300 :
				print "DEBUG:    ... and seconds = ${seconds}"
	else:
		stat_text = "ok"
		status = 0


	#########################  ___print "  {}    {}    {}   {}".format(timestamp,seconds,diff_secs,status)
	last_secs = seconds
	last_date = date_str
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
	load = subprocess.check_output('/usr/bin/uptime')
	load = re.sub('.*average: *', '', load)
	# load = re.sub(',', '', load)
	# words = re.split(' ', load)
	# cur_proc_load = float(words[0])
	cur_proc_load = float(re.sub(', .*', '', load))
	# ___print cur_proc_load
	# ___print cur_proc_load
	# ___print cur_proc_load
	# ___print cur_proc_load
	if cur_proc_load > proc_load_lim :
		print "WARNING: \t" + \
			"proc_load_lim = " + str(proc_load_lim) + \
			"\t\t 1 minute load average = " + str(cur_proc_load)
	data['proc_load'] = cur_proc_load
	return cur_proc_load


	if cur_proc_load > proc_load_lim :
		print "WARNING: 1 minute load average = " + str(cur_proc_load) + \
			";  proc_load_lim = " + str(proc_load_lim)
		return 1
	else:
		return 0



# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
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
		print "WARNING:  Expecting 11 tokens from \"free\", but got " + str(mem_pct) 

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
		print "WARNING:  " + str(mem_pct) + "% mem in use"

	free = re.sub(' ', '|', free)                     # Replace each blank with a |

	cpu_temp = read_cpu_temp()
	data['cpu_temp'] = cpu_temp
	cpu_temp_f = ( cpu_temp * 1.8 ) + 32
	data['cpu_temp_f'] = cpu_temp_f

	return "  {},  {}%,  {},  {}%,  {:4.1f},  {:6.3f},   {:5.1f},".format(effective_used, mem_pct, swap_used, swap_pct, \
		cpu_temp, cpu_temp, cpu_temp_f ) + \
		"\nfree|" + free
#
#	return "  {},  {}%,  {},  {}%,".format(effective_used, mem_pct, swap_used, swap_pct) + \
#		"\nfree|" + free
#
#	return " mem_used={} ({}%) swap_used={} ({}%)".format(effective_used, mem_pct, swap_used, swap_pct) + \
#		"\nfree|" + free
#
#	return " mem_used={} ({}%) swap_used={} ({}%)".format(effective_used, mem_pct, swap_used, swap_pct) + \
#		"  {}/{}/{}/{}/{}".format(bu_ca_used, bu_ca_free, shared, buffers, cached)


# ----------------------------------------------------------------------------------------
#
# "MXdiags/20170912-202909.txt"
#
# To Do: Should externalize or "calculate" the path to the diag logs.
#
# ----------------------------------------------------------------------------------------
def rf_dropped() :
	global saved_exception_tstamp
	return_value = 0
	file_list = listdir("/mnt/root/home/pi/Cumulus_MX/MXdiags/")
	file_list.sort()

	#for iii in range(0, len(file_list)):
	#	___print str(iii) + "  " + file_list[iii]

	log_file = file_list[len(file_list)-1]           # Last file in the list
	# ___print log_file

	# --------------------------------------------------------------------------------
	#   2017-09-15 20:26:45.616 Sensor contact lost; ignoring outdoor data
	#   2017-09-15 20:26:55.616 Sensor contact lost; ignoring outdoor data
	#   2017-09-15 20:27:00.666 WU Response: OK: success
	#   
	#   2017-09-15 20:28:00.677 WU Response: OK: success
	#   
	# --------------------------------------------------------------------------------
	# Work backwards from the end of the most recent file looking for
	# one of the lines above.
	# --------------------------------------------------------------------------------
	fileHandle = open ( "/mnt/root/home/pi/Cumulus_MX/MXdiags/" + log_file,"r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	for iii in range(-1, -12, -1):
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

		if "Exception" in lineList[iii] :
			exception_tstamp = re.sub('[^-\.:0-9]*', '', lineList[iii] )
			if saved_exception_tstamp == exception_tstamp :
				print "WARNING:  Cumulus MX Exception thrown (see above)"
			else:
				print "WARNING:  exception_tstamp = " + exception_tstamp 
				print "WARNING:  Cumulus MX Exception thrown\n"
				for jjj in range(iii-1, -1, 1) :
					print str(jjj-iii+1) + "\t" + lineList[jjj]
			saved_exception_tstamp = exception_tstamp 
		if "Sensor contact lost; ignoring outdoor data" in lineList[iii] :
			print "WARNING:  Sensor contact lost; ignoring outdoor data.  " + \
				"Press \"V\" button on WS console"
			return_value = 1
			break
		if "WU Response: OK: success" in lineList[iii] :
		# 	___print "Data OK"
			break
	# --------------------------------------------------------------------------------
	#   Not sure what to do with "None", or where exactly this comes from.
	#   Added return_value to make sure there is a value returned.
	#   Increased the number of records cecked too.
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



# ----------------------------------------------------------------------------------------
#  Check web cam status.
#
#  After power-cycling the web cam, it could take up to 5 minutes for the next
#  image update.  But more importantly, the dillys.org webserver cron job only
#  runs every 5 minutes... but empirically, up to 10 minutes - accounting for
#  each 5 minutes....?
#
#
#
# ----------------------------------------------------------------------------------------
def camera_down():
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
		print "DEBUG: content = \"" + content + "\""

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
	interval = int(words[0])
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


		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.

		#___# sleep(sleep_on_recycle)
		data['camera_down'] = 1
		return 1
	else:
		pcyc_holdoff_time = 0
		data['camera_down'] = 0
		return 0


# ----------------------------------------------------------------------------------------
# 
# 
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
###	setup()
	#### if sys.argv[1] = "stop"
	this_script = sys.argv[0]
	messager("  Starting " + this_script + "  PID=" + str(getpid()))
	# logger( "Starting " + this_script + "  PID=" + str(getpid()))
	write_pid_file()
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
# ----------------------------------------------------------------------------------------
