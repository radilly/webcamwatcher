#!/usr/bin/python
#
# This is called as needed - perhaps remotely - to create an "event record"
# which is read by statuscollector.py. That script, in turn, generates a log
# as html for any processes which should create a record in the status_dir.
#
#
# ========================================================================================
# 20181116 RAD WU_Cancels added to count when CMX cancels the WU update. When
#              this is found in the log, it is now treated as a special case.
# ========================================================================================
# ========================================================================================

# Basics
import sys
import re
import time
import datetime

# Utility
import subprocess
from os import getpid


# BASE_DIR =              "/mnt/root/home/pi/Cumulus_MX"
# data_stop_file =        BASE_DIR + "/web/DataStoppedT.txttmp"
status_dir =            "/mnt/root/home/pi/status"

logger_file = sys.argv[0]
logger_file = re.sub('\.py', '.log', logger_file)

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
strftime_FMT = "%Y/%m/%d %H:%M:%S"





# main
#---------
log_header_stride = 15
summary_stride = 3

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
	"mono_pid",
	"watcher_pid",
	"last_restarted",
	"cmx_svc_runtime",
	"server_stalled",
	"ws_data_stopped",
	"rf_dropped",
	"camera_down",
	"last_realtime",
	"proc_pct",
	"proc_load",
	"proc_load_5m",
	"mono_threads",
	"effective_used",
	"mem_pct",
	"swap_used",
	"swap_pct",
	"cpu_temp_c",
	"cpu_temp_f",
	"amb_temp",
	"python_version",
	"mono_version",
	"webcamwatch_down"
	]
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
	"{} sec",
	"{:5.1f}%",
	"{:7.2f}",
	"{:7.2f}",
	"{}",
	"{} bytes",
	"{}&percnt;",
	"{} bytes",
	"{}&percnt;",
	"{:6.1f} &deg;C",
	"{:6.1f} &deg;F",
	"{:6.1f} &deg;F",
	"{}",
	"{}",
	"{}"
	]

thresholds = [
	-1,
	-1,
	-1,
	-1,
	0,
	0,
	0,
	0,
	120,
	10.0,
	4.0,
	4.0,
	20,
	-1,
	15,
	1024,
	1,
	55,
	131,
	100,
	-1,
	-1,
	0
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

		CSV_rec = datetime.datetime.now().strftime(strftime_FMT) + ","
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


	status_file = "{}/{}.txt".format( status_dir, time.time() )
	FH = open(status_file, "w+")
	FH.write( format_str.format( ID, description, bgcolor, code) )
	FH.close



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
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
###	GPIO_setup()
	#### if sys.argv[1] = "stop"
	this_script = sys.argv[0]


	ID = sys.argv[1]
	description = sys.argv[2]
	code = sys.argv[3]
	log_event(ID, description, code)

	exit()
	exit()
	exit()
	exit()
	exit()
	exit()
	exit()
	exit()


	print "\n\n\n\n\n"

	messager("INFO: Starting " + this_script + "  PID=" + str(getpid()))

	write_pid_file()
	cmx_svc_runtime()	# This reads the PID for the main mono process

	messager("INFO: Mono version: {}" .format( mono_version() ) )

	messager("DEBUG: Logging to {}" .format( logger_file ) )

	try:
		main()
	except KeyboardInterrupt :
		messager("  Good bye from " + this_script)
#		destroy()

# ----------------------------------------------------------------------------------------
