#!/usr/bin/python
# @@@
#
# ----------------------------------------------------------------------------------------
#  This is intended to be run as a cgi-bin script.
#  It collects some information about the state of the system and renders a web page.
#  If copied to apache folder /usr/lib/cgi-bin/pi_health.py it can be accessed as
#      http://192.168.1.172/cgi-bin/pi_health.py  -  for example...
#
# ----------------------------------------------------------------------------------------
#
# ========================================================================================
# 20190820 RAD Added a bgcolor to every tracked row.  Removed a little more commentary.
# 20190820 RAD Cleaned out most of the dead code.
# 20190819 RAD Added hostname(). Tinkered with colors a little. Working, but still has
#              dead code.
# 20190815 RAD Tested as a cgi-bin page.  Added the ability to have yellow and red-shaded
#              rows to indicate the severity of the paramemter.  Still has a lot of junk
#              and dead code but it's working well enough to deploy across my Pis.
# 20190805 RAD Output both a web page file, and the content to stdout which should work
#              for cgi-bin.
# 20190805 RAD Hacked up mem_usage() because I found 2 versions of Raspbian were
#              generating rather different output fo the free command.
# 20190804 RAD Copied watchdog.py. Wanted a separate status tool for Pi in general
#              which could be access via a web server.
# ========================================================================================
#
#  On Installing and Configuring Apache2
#      sudo apt-get update && sudo apt-get upgrade
#      sudo apt-get install apache2
#      ifconfig
#
#   If you have trouble copying and pasting into edited file...
#      sudo ls -al /root
#      sudo cp /home/pi/.vimrc /root
#      sudo vi /etc/apache2/conf-available/serve-cgi-bin.conf
#   Insert line "AddHandler cgi-script .py" above </Directory> as shown...
#             <IfDefine ENABLE_USR_LIB_CGI_BIN>
#                     ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
#                     <Directory "/usr/lib/cgi-bin">
#                             AllowOverride None
#                             Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
#                             Require all granted
#                             AddHandler cgi-script .py          #https://www.raspberrypi.org/forums/viewtopic.php?t=155229
#                     </Directory>
#             </IfDefine>
#
#   This did not work...
#      sudo ln -s /home/pi/webcamwatcher/pi_health.py  /usr/lib/cgi-bin/
#      ls -la /usr/lib/cgi-bin/
#
#   Check error log...
#      less /var/log/apache2/error.log
#
#   May not be necessary...
#      sudo reboot
#
#      sudo a2enmod cgi
#      sudo systemctl -l restart apache2
#
#      sudo ln -s /home/pi/webcamwatcher/pi_health.py  /usr/lib/cgi-bin/
#   Did not work
#      sudo rm /usr/lib/cgi-bin/pi_health.py 
#      sudo cp /home/pi/webcamwatcher/pi_health.py  /usr/lib/cgi-bin/
#   Worked!!
#
#   Check... (without browser)
#      curl localhost/cgi-bin/pi_health.py
#
#
#      systemctl -l status apache2
#      ls -al /var/log/apache2/
#      ls -la /usr/lib/cgi-bin/
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


import sys
import re
import datetime
import subprocess


proc_load_lim = 4.0         # NOTE: This should be removed...


proc_stat_busy = -1		# Sentinal value
proc_stat_idle = -1
proc_stat_hist = []		# Holds last proc_stat_hist_n samples
proc_stat_hist_n = 10		# Control length of history array to keep

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
strftime_FMT = "%Y/%m/%d %H:%M:%S"


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# This is the global data value dictionary.   This is written into by many of
# the routines which follow.
# Most of the keys map to a function name...
#
# https://www.python-course.eu/dictionaries.php
# https://docs.python.org/2/tutorial/datastructures.html#dictionaries
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
data = {}

data_keys = [
	"hostname",
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

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# For HTML Table-style output lines
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# https://pyformat.info/
data_format = [
	"{}",
	"{}",
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


# https://snakify.org/en/lessons/two_dimensional_lists_arrays/
# I considered how to externalize this, but haven't come up with anything clever
# when running under apache
threshold_matrix = [
	[     -1,    -1  ],    # "hostname",
	[     -1,    -1  ],    # "system_uptime",
	[    8.0,  16.0  ],    # "proc_pct",
	[    1.0,   2.0  ],    # "proc_load",
	[    4.0,   4.0  ],    # "proc_load_5m",
	[     -1,    -1  ],    # "effective_used",
	[     15,    25  ],    # "mem_pct",
	[   1024,  4096  ],    # "swap_used",
	[      1,     5  ],    # "swap_pct",
	[     50,    55  ],    # "cpu_temp_c",
	[    122,   131  ],    # "cpu_temp_f",
	[     -1,    -1  ],    # "python_version",
	]





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

	pct_util = float(busy * 100) / float(idle + busy)
#	if proc_stat_busy < 0 :
#		### print "Since last boot:  {} * 100 / {}".format( busy, idle+busy )
#		### print "{:6.3f}%".format( float(busy * 100) / float(idle + busy) )
#		### print "========"
#		pct_util = float(busy * 100) / float(idle + busy)
#
#	else :
#		delta_busy = busy - proc_stat_busy 
#		delta_idle = idle - proc_stat_idle
#		timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
#		pct_util = float(delta_busy * 100) / float(delta_idle + delta_busy)
#		### print "{} {:6.3f}%".format( timestamp, pct_util )
#		# ------------------------------------------------------------------------
#		# Unused for now.  Here in case we want to look at a rolling average...
#		# ------------------------------------------------------------------------
#		if len(proc_stat_hist) > (proc_stat_hist_n -1) :
#			proc_stat_hist = proc_stat_hist[1:]
#		proc_stat_hist.append( pct_util )

	proc_stat_busy = busy
	proc_stat_idle = idle
	data['proc_pct'] = pct_util
	return pct_util







# ----------------------------------------------------------------------------------------
# hostname - get the bane of the system
#
#
# ----------------------------------------------------------------------------------------
def hostname():
	global data
	name = subprocess.check_output('/bin/hostname')
	data['hostname'] = name.rstrip()





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
	data['system_uptime'] = uptime.rstrip()
	return cur_proc_load


	if cur_proc_load > proc_load_lim :
		messager( "WARNING: 1 minute load average = " + str(cur_proc_load) + \
			";  proc_load_lim = " + str(proc_load_lim) )
		return 1
	else:
		return 0







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
# This generates a Raspberry Pi Status page, which Cumulus MX ftp's to the server.
# It is mostly an HTML table.
#
# ----------------------------------------------------------------------------------------
def status_table():

        print ( "Content-type: text/html\n\n\n\n" )
	print ( "<HEAD><TITLE>\n" )
	print ( "Raspberry Pi Health\n" )
	print ( "</TITLE></HEAD><BODY BGCOLOR=\"#BBBBBB\" TEXT=\"#010101\" LINK=\"#FFFF00\" VLINK=\"#FFBB00\" ALINK=\"#FFAAFF\"><H1 ALIGN=center>\n" )
	print ( "Raspberry Pi Health\n" )
	print ( "</H1>\n" )
	# print ( "<P> &nbsp;\n\n" )

	print ( "<CENTER>\n")
	print ( "<TABLE BORDER=1 `CELLPADDING=4>\n")
#	print ( "<TABLE BORDER=1 `CELLPADDING=2><TR><TD VALIGN=\"TOP\">\n")

#	print ( "<CENTER>\n")
#	print ( "<TABLE BORDER=1>\n" )
	print ( "<TR><TH> Parameter </TH><TH> Current Value </TH><TH> Thresholds </TH</TR>\n" )
	print ( "<TR><TH> &nbsp; </TH><TH> &nbsp; </TH><TH> yellow, red </TH</TR>\n" )
	# NOTE: We may not choose to print everything in data[]
	for iii in range(0, len(data_keys)):
		bgcolor = ""
		thresholds = " {}, &nbsp; &nbsp;  {}".format( threshold_matrix[iii][0], threshold_matrix[iii][1] )
		if threshold_matrix[iii][1] > -1 :
			if data[data_keys[iii]] >= threshold_matrix[iii][1] :
				bgcolor = " BGCOLOR=\"red\""
				bgcolor = " BGCOLOR=\"#DD000\""
			elif data[data_keys[iii]] >= threshold_matrix[iii][0] :
				bgcolor = " BGCOLOR=\"#BBBB00\""
				bgcolor = " BGCOLOR=\"yellow\" FGCOLOR=\"black\""
			else :
				bgcolor = " BGCOLOR=\"green\""
				bgcolor = " BGCOLOR=\"#11BB11\""
		else: 
			thresholds = "&nbsp;"
			thresholds = "<FONT SIZE=-2> reference </FONT>"

#		format_str = "<TR><TD{}> {} </TD><TD ALIGN=right{}> " + data_format[iii]  + " </TD><TD ALIGN=right{}> {} </TD></TR>\n"
#		format_str = "<TR><TD{}> {} </TD><TD ALIGN=right{}> <B><FONT COLOR=\"black\"> " + data_format[iii]  + " </TD><TD ALIGN=right{}> {}, {} </TD></TR>\n"

#		format_str = "<TR><TD{}> {} </TD><TD ALIGN=right{}> " + data_format[iii]  + " </TD><TD ALIGN=right{}> {}, {} </TD></TR>\n"
		format_str = "<TR><TD{}> {} </TD><TD ALIGN=right{}> " + data_format[iii]  + " </TD><TD ALIGN=center{}> {} </TD></TR>\n"
#
#		print " - - - - - - "
#		print iii
#		print data_format[iii]
#		print bgcolor
#		print data_keys[iii]
#		print data[data_keys[iii]]

#		print ( format_str.format( bgcolor, data_keys[iii], bgcolor, data[data_keys[iii]], bgcolor, threshold_matrix[iii][0], threshold_matrix[iii][1] ) )
		print ( format_str.format( bgcolor, data_keys[iii], bgcolor, data[data_keys[iii]], bgcolor, thresholds ) )

	print ( "<TR><TD COLSPAN=3 ALIGN=center><FONT SIZE=-1>\n" )
	print ( datetime.datetime.utcnow().strftime(strftime_FMT) + " GMT" )
	print ( "<BR> " + datetime.datetime.now().strftime(strftime_FMT) + " Local" )
	print ( "</FONT></TD></TR>\n" )

	print ( "</TABLE>\n" )



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



# @@@

# ----------------------------------------------------------------------------------------
# NOTE: Data is stored into the data[] array, so this could be converted to returning
#       a binary return code.
#
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
def mem_usage():
	global data

#	free = subprocess.check_output(["/usr/bin/lsb_release", "-a"])
#	print "DEBUG: --->\n{}".format( free )

#	free = subprocess.check_output(["/usr/bin/free", "-V"])
#	print "DEBUG: --->\n{}".format( free )

	free = subprocess.check_output(["/usr/bin/free"])

#	print "DEBUG: --->\n{}".format( free )

#	words = re.split(' +', free)
#	for iii in range(0, len(words)):
#		print "DEBUG: {:4d} {}".format( iii, words[iii])

	meminfoarray = dict()
	meminfo = subprocess.check_output(["/bin/cat", "/proc/meminfo"])
#	print "DEBUG: --->\n{}".format( meminfo )
	line = re.split("\n", meminfo )
	for iii in range(0, len(line)):
#		print line[iii]
		tok = re.split("[: ]*", line[iii])
#		for jjj in range(0, len(tok)):
#			print "{:5d} {}".format(jjj, tok[jjj])
#		print "len = {}".format( len(tok) )
		if len(tok) == 3 :
			meminfoarray[ tok[0] ] = tok[1]
#	print meminfoarray


	data['swap_used'] = int( meminfoarray["SwapTotal"] ) - int( meminfoarray["SwapFree"] )
	data['swap_pct'] = 100 * (int( meminfoarray["SwapTotal"] ) - int( meminfoarray["SwapFree"] )) / int( meminfoarray["SwapTotal"] )
	data['effective_used'] = int( meminfoarray["MemTotal"] ) - int( meminfoarray["MemAvailable"] )
	data['mem_pct'] = 100 * (int( meminfoarray["MemTotal"] ) - int( meminfoarray["MemAvailable"] )) / int( meminfoarray["MemTotal"] )



	cpu_temp = read_cpu_temp()
	data['cpu_temp_c'] = cpu_temp
	cpu_temp_f = ( cpu_temp * 1.8 ) + 32
	data['cpu_temp_f'] = cpu_temp_f







# ----------------------------------------------------------------------------------------
#
#
#
# ----------------------------------------------------------------------------------------
def make_page() :
	global data

	python_version = "v " + str(sys.version)
	python_version = re.sub(' *\n *', '<BR>', python_version )
	python_version = re.sub(' *\(', '<BR>(', python_version )

	#   messager("INFO: Python version: " + str(sys.version))
	data['python_version'] = python_version

	hostname()
	proc_load()
	proc_pct()
	mem_usage()

	status_table()


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
