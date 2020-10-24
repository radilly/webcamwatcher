#!/usr/bin/python3 -u
# @@@ ... Restart using...
#
#   kill -9 `cat ./statuscollector.PID`
#
#   nohup /usr/bin/python3 -u ./statuscollector.py /home/pi/status &
#
#   Takes 1 argument - the path to the directory to monitor for new messages.
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#    NOTE:
#    NOTE: Should replace FTP with SCP - after passwordless login is set up.
#    NOTE:
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
#  * NOTE: Need forward links???
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
# ========================================================================================
# ========================================================================================
# 20201021 RAD In the course of starting this up on a "clean" system, I made some
#              assumptions about what would be in place when this script first ran.
#              In part default values were added; ts = 0.0, found_prev_page = "".
# 20190716 RAD Been running a month using scp so it looks good. Can apply this elsewhere
#              but for now will check this in even though you'll see 'T E S T' in a few
#              places.
# 20190610 RAD This seemed to hang indefinately doing an FPT. I had already been
#              thinking about SCP, and webcamimager.py has addition debug logging
#              to try to trap the problem. I do see this error, even though we are quitting ftp
#                       421 Too many connections (8) from this IP
#
#	....2019/06/25 05:53:45 DEBUG: 1561456422.38.txt added to msgqueue #=151   monitor_dir()
#
#	2019/06/25 05:53:45 >>>>>>> <TD>  Webcam image update stalled. </TD>
#
#	2019/06/25 05:53:45 DEBUG: FTP local_file = "/mnt/root/home/pi/status/event_status.html"   remote_path = ""   server = "ftp.dilly.family"
#	2019/06/25 05:53:45 DEBUG: local_file_bare = "event_status.html"
#  >>>  2019/06/25 05:53:45 ERROR: FTP (connect): 421 Too many connections (8) from this IP
#	2019/06/25 05:53:48 WARNING: FTP attempt #1
#  < < < < G A P > > > >
#	2019/07/03 14:38:26 INFO: Starting ./statuscollector.py   PID=30862
#
#
# 20190609 RAD Finished the custover from GoDaddy to Namecheap.  In the process noted
#              that the log info could be more helpful and added to that for DEBUG:
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

# Python 2 to 3
import configparser

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
import datetime
from time import sleep
### import time
import sys
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
from os import listdir, getpid, stat, unlink
from ftplib import FTP
# Python 2 to 3
# from urllib2 import urlopen, URLError, HTTPError
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import re

### import shutil
### import socket   ### For error processing???
### import calendar

# Holds the records used to build the web page.
msgqueue = {}

prev_page = ""
work_dir = ""
main_image = ""
remote_dir = "/home/content/b/o/b/bobdilly/html/WX"
remote_dir = "/var/chroot/home/content/92/3185192/wx"

remote_dir = "/home/dillwjfq/public_html/wx"

remote_dir = ""    # This is for ftp to camdilly@dilly.family

this_script = sys.argv[0]
logger_file = re.sub('\.py', '.log', this_script)

# NOTE  NOTE  NOTE  NOTE  NOTE  ---  This could be sorted in a file to span executions.
#        See webcamwatcher/webcamimager.py  ...  global image_data_file
# NOTE  NOTE  NOTE  NOTE  NOTE  ---  CODED UP A SOLUTION ---  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK  CHECK
# Preliminary tests look OK...
stored_dir_mtime = re.sub('\.py', '__.dat', this_script)
# Real mtime will always be larger
last_image_dir_mtime = 0.0

ftp_login = ""
ftp_password = ""

last_timestamp = 0.0
dot_counter = 0
sleep_for = 10

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"
WEB_URL = "http://dilly.family/wx"
wserver = "dillys.org"
wserver = "ftp.dilly.family"


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
# Mostly leftover stuff.  read_config() uses these...
#
#  NOTE: The relay GPIO port should be externalized.  NOW HARD-WIRED FOR South camera.
#
#  NOTE: For the SunFounder Relay Module, there's sort of a double negative at work.
#     It is active low, so by default you might think GPIO.LOW.
#
#     But ... We are using the NC contacts of the relay so that, with the module
#     unpowered, the webcam gets power.  Power-cycling means energizing the relay
#     briefly by driving the input pin low.
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
relay_GPIO = ""
relay2_GPIO = ""
thumbnail_image = ""
image_age_URL = ""

# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():
	global work_dir
	global last_image_dir_mtime

	if len(sys.argv) >= 2 :
		work_dir = sys.argv[1]
	else :
		log_and_message( "ERROR: working directory is a required first argument." )
		exit()

	if not os.path.isdir( work_dir ) :
		log_and_message( "ERROR: directory \"{}\" not found.".format( work_dir ) )
		exit()

	log_and_message( "INFO: monitoring directory \"{}\"".format( work_dir ) )

	#    NOTE: Should replace FTP with SCP - after passwordless login is set up.
	fetch_FTP_credentials( work_dir + "/.ftp.credentials" )

###	nvers = mono_version()
###	log_and_message("INFO: Mono version: {}" .format( nvers ) )

	python_version = "v " + str(sys.version)
	python_version = re.sub(r'\n', r', ', python_version )
	logger( "INFO: Python version: {}".format( python_version ) )

	build_msgqueue()
	
	# May have to hand-create this file initially...
	last_image_dir_mtime = get_stored_ts()

	prev_page = find_prev_page()

	logger( "INFO: Start monitoring." )

	while True:
		monitor_dir()
		sleep(sleep_for)

	exit()



# ----------------------------------------------------------------------------------------
#  Does the initial filling of the msgqueue array.
#
#
# ----------------------------------------------------------------------------------------
def build_msgqueue( ) :
	global msgqueue
	global prev_page
	global last_timestamp

	logger( "INFO: initial build of Global msgqueue.  build_msgqueue()" )
	# --------------------------------------------------------------------------------
	#  Scan the files in the work directory.
	# --------------------------------------------------------------------------------
	file_list = listdir( work_dir )
	file_list_len = len( file_list )
	file_list.sort()

	logger( "DEBUG: Process all files, skipping any not of the form \"nnnnnnn.nn.txt\"." )
	logger( "DEBUG: Any of the form nnnnnnn.nn.txt are read into array msgqueue.\n" )
	for iii in range( file_list_len ) :
		filename = file_list[ iii ]

		# ------------------------------------------------------------------------
		#  Check the file to make sure its a msg we want to process.
		#  Messages should be named - time.time() + ".txt"
		# ------------------------------------------------------------------------
		if not re.match('[0-9]{8,15}\.[0-9]+.txt$', filename, flags=re.I) :
			logger( "DEBUG: skipping {}".format( filename ) )
			continue

		# ------------------------------------------------------------------------
		# Strip off the ".txt" and use the first part of the filename as a float.
		# ------------------------------------------------------------------------
		ts = float(re.sub(r'\.txt.*', r'', filename))
#		logger( "DEBUG: ts = {}".format( ts ) )

		try :
			found_msg = True
			for_test =  msgqueue[ filename ]
		except KeyError:
			found_msg = False

		if not found_msg :
			FH = open( "{}/{}".format( work_dir, filename ), "r" )
			content = FH.readlines()
			FH.close
			# NOTE: This will include the newlines in the file.
			msgqueue[ filename ] = content
			logger( "DEBUG: {} added to msgqueue #={}  (build_msgqueue)".format( filename, len(msgqueue) ) )

		last_timestamp = ts

	logger( "DEBUG: Global msgqueue loaded with {} members.\n".format( len(msgqueue) ) )





# ----------------------------------------------------------------------------------------
#  Write out an events page (html table)
#
#
# ----------------------------------------------------------------------------------------
def build_events_page( msgQ, page, prev ) :
	timestamp = datetime.datetime.now().strftime(strftime_FMT)

	FH = open( page, "w")

	FH.write( "<HEAD><TITLE>\n" )
	FH.write( "Weather Station Events / Status\n" )
	FH.write( "</TITLE></HEAD><BODY BGCOLOR=\"#555555\" TEXT=\"#FFFFFF\" LINK=\"#FFFF00\" VLINK=\"#FFBB00\" ALINK=\"#FFAAFF\"><H1 ALIGN=center>\n" )
	FH.write( "Weather Station Events / Status\n" )
	FH.write( "</H1>\n" )
	FH.write( "\n" )
	FH.write( "\n" )
	FH.write( "<CENTER>\n" )
	FH.write( "<TABLE BORDER=1>\n" )
	FH.write( "<TR><TH> Timestamp </TH><TH> Description </TH><TH> ID </TH></TR>\n" )
	FH.write( "\n" )

	for dkey in reversed(sorted(msgQ.keys())) :
		FH.write( "<!-- ----------- {} ---------- -->\n".format( dkey ) )
		for jjj in range( len(msgQ[ dkey ] ) ) :
			FH.write( msgQ[ dkey ][jjj] )

	FH.write( "</TABLE>\n" )
	FH.write( "</CENTER>\n" )
	FH.write( "\n<P> &nbsp;\n" )

	# --------------------------------------------------------------------------------
	#  prev, if any, will be the page name for the continuation of the log (backward).
	# --------------------------------------------------------------------------------
	if len( prev ) > 0 :
		FH.write( "<P><A HREF=\"{}\"> Previous records </A>".format( prev ) )


	FH.write( "\n<P ALIGN=CENTER> Updated &nbsp; {}\n".format( timestamp ) )
	FH.write( "\n<P> &nbsp;\n" )
	FH.write( "\n\n" )

	FH.close

	return


# ----------------------------------------------------------------------------------------
#  Monitor the directory which event messages are written into.
#
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  NOTE:
#    In the example below, this file timestamp is 0.01 sec newer than the directory
#    mtime - which is hard to explain.
#
# > 12:07:27 DEBUG: ts = 1533340761.65
# > 12:07:27 DEBUG: 1533340761.65.txt added to msgqueue #=106
#   12:07:27 DEBUG: local_file = /mnt/root/home/pi/status/event_status.html   remote_path =    server = dillys.org
#   12:07:27 DEBUG: local_file_bare = event_status.html
# > 12:07:39 DEBUG: image_dir_mtime = 1533340761.64
#
# ----------------------------------------------------------------------------------------
def monitor_dir() :
	global msgqueue
	global prev_page
	global last_image_dir_mtime
	global last_timestamp
	global dot_counter

	found_msg = False
	# --------------------------------------------------------------------------------
	#  Check the modification time on the message directory.
	#  
	# --------------------------------------------------------------------------------
	image_dir_mtime = stat( work_dir ).st_mtime
	logger( "DEBUG: image_dir_mtime = {}".format( image_dir_mtime ) )

	logger( "INFO: Waiting for a directory change.  monitor_dir()" )
	while image_dir_mtime <= last_image_dir_mtime :
		log_string( "." )
#############################################################################		sys.stdout.write( "." )
		dot_counter += 1
		if ( dot_counter % 60 ) == 0 :
			logger( "msgqueue #={}".format( len(msgqueue) ) )
#			log_string( "\n" )
#			sys.stdout.write( "\n" )

		sleep(sleep_for)
		image_dir_mtime = stat( work_dir ).st_mtime


	store_file_data( image_dir_mtime )

	# --------------------------------------------------------------------------------
	#  Scan the files in the work directory.
	#
	#
	#  This should be a separate routine...
	# --------------------------------------------------------------------------------
	file_list = listdir( work_dir )
	file_list_len = len( file_list )
	file_list.sort()
	ts = 0.0

	for iii in range( file_list_len ) :
		filename = file_list[ iii ]

		# ------------------------------------------------------------------------
		#  Check the file to make sure its a msg we want to process.
		#  Messages should be named - time.time() + ".txt"
		# ------------------------------------------------------------------------
		if not re.match('[0-9]{8,15}\.[0-9]+.txt$', filename, flags=re.I) :
#DEBUG#			log_and_message( "DEBUG: skipping {}".format( filename ) )
			continue


		# ------------------------------------------------------------------------
		# Strip off the ".txt" and use the first part of the filename as a float.
		# ------------------------------------------------------------------------
		ts = float(re.sub(r'\.txt.*', r'', filename))
#		log_and_message( "DEBUG: ts = {}".format( ts ) )

		try :
			found_msg = True
			for_test =  msgqueue[ filename ]
###			log_and_message( "DEBUG: Already in msgqueue..." )
		except KeyError:
			found_msg = False
###			log_and_message( "DEBUG: Not found in msgqueue..." )
			# Necessary when above is commented out...
			pass

		#
		######################################################### if float(filename) > last_timestamp :
		if not found_msg :
			FH = open( "{}/{}".format( work_dir, filename ), "r" )
			content = FH.readlines()
			FH.close
			msgqueue[ filename ] = content
			logger( "DEBUG: {} added to msgqueue #={}   monitor_dir()".format( filename, len(msgqueue) ) )

			tmp = msgqueue[ filename ][1]
			tmp.strip( "\n" )
			log_string( "\n" )
			sys.stdout.write( "\n" )
			logger( ">>>>>>> {}".format( tmp ) )
#DEBUG#			log_and_message( msgqueue[ filename ] )
#DEBUG#			for jjj in range( len(msgqueue[ filename ] ) ) :
#DEBUG#				sys.stdout.write( "{}:  {}".format( jjj, msgqueue[ filename ][jjj] ) )
#	exit()

	# NOTE: When we write the web page we change image_dir_mtime for the next pass.
	last_image_dir_mtime = image_dir_mtime
	last_timestamp = ts

	events_page = "{}/event_status.html".format( work_dir )

	if len(msgqueue) >= 200 :
		prune_msgqueue( )

	build_events_page( msgqueue, events_page, prev_page )

	# push_to_server( events_page, remote_dir, wserver )
	push_to_server_via_scp( events_page, remote_dir, wserver )

	dot_counter = 0

	logger( "DEBUG: mtime = {} for {}".format( stat( events_page ).st_mtime, events_page ) )

	return


# ----------------------------------------------------------------------------------------
#  This deals with the log getting too long.  >= 200 records.
#  We will chop in in half
#
#  - Find record 101.  We want to split at this record.
#  - Write from record 101 on to a file named "{}_event_status.html".format( ts ).
#     ts is the integer part of filename ts that will be first in this file.
#
# ----------------------------------------------------------------------------------------
def prune_msgqueue( ) :
	global msgqueue
	global prev_page

	prevqueue = {}
	moving = False

	logger( "DEBUG: in prune_msgqueue( )" )

	iii = 0
	for dkey in reversed(sorted(msgqueue.keys())) :
		iii += 1
		if iii == 101 :
			moving = True
			ts = re.sub(r'\.[0-9]+\.txt.*', r'', dkey)
			new_prev_page = "{}/{}_event_status.html".format( work_dir, ts )
			new_pp_short = "{}_event_status.html".format( ts )

		if moving :
			prevqueue[ dkey ] = msgqueue.pop( dkey )
			logger( "DEBUG: prevqueue #={}".format( len(prevqueue) ) )
			unlink( "{}/{}".format( work_dir, dkey ) )

	logger( "DEBUG: Create {} (previous page)".format( new_pp_short ) )
	build_events_page( prevqueue, new_prev_page, prev_page )

	# push_to_server( new_prev_page, remote_dir, wserver )
	push_to_server_via_scp( new_prev_page, remote_dir, wserver )

	prev_page = new_pp_short

	return







# ----------------------------------------------------------------------------------------
#  Call when this script is started, and prev_page is not yet set.
#  This is needed to chain pages backwards in history.
#
# NOTE - We could save this in a file.  This isn't too expensive to run.  The risk is if
#        for some reason work_dir gets cleaned out.  I suppose this is implicitly
#        stored in the last page we wrote...
# ----------------------------------------------------------------------------------------
def find_prev_page() :
	global prev_page

	# --------------------------------------------------------------------------------
	#  Scan the files in the work directory.
	# --------------------------------------------------------------------------------
	file_list = listdir( work_dir )
	file_list_len = len( file_list )
	file_list.sort()
	found_prev_page = ""

	for iii in range( file_list_len ) :
		filename = file_list[ iii ]
		if re.match('[0-9]{8,15}_event_status.html', filename, flags=re.I) :
			found_prev_page = filename
			logger( "DEBUG: found_prev_page = \"{}\"".format( found_prev_page ) )


	prev_page = found_prev_page
	logger( "DEBUG: Global prev_page now set to {} in find_prev_page()".format( prev_page ) )





# ----------------------------------------------------------------------------------------
#  T E S T
#  T E S T
#  T E S T
#  T E S T
#  T E S T
#
#  References:
#   https://stackoverflow.com/questions/68335/how-to-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
#   https://stackoverflow.com/questions/250283/how-to-scp-in-python
#
#   https://stackoverflow.com/questions/68335/how-to-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
#   https://stackoverflow.com/questions/68335/how-to-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
#
# @@@
# ----------------------------------------------------------------------------------------
def push_to_server_via_scp(local_file, remote_path, server) :
	remote_path = "public_html/wx"
#      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#	destination = "user@remotehost:remotepath"
	destination = "dillwjfq@server162.web-hosting.com:" + remote_path
	destination = "dillwjfq@premium29.web-hosting.com:" + remote_path

	try :
		output = subprocess.check_output(["scp", "-q", "-P", "21098", local_file, destination])
		lines = re.split('\n', output)
	except :
		lines = {}
		messager( "ERROR: scp: {}".format( sys.exc_info()[0] ) )

	if len(lines) > 1 :
		for jjj in range( len(lines) ) :
			print( "DEBUG: #{} \"{}\"".format( jjj, lines[jjj] ) )
	
	return


# ----------------------------------------------------------------------------------------
#  This pushes the specified file to the (hosted) web server via FTP.
#
#  FTP User: camdilly
#  FTP default PWD: /home/content/b/o/b/bobdilly/html/WX
#
#  https://pythonspot.com/en/ftp-client-in-python/
#  https://docs.python.org/2/library/ftplib.html
# ----------------------------------------------------------------------------------------
def push_to_server(local_file, remote_path, server) :
	global ftp_login
	global ftp_password

	logger( "DEBUG: FTP local_file = \"{}\"   remote_path = \"{}\"   server = \"{}\"".format( local_file, remote_path, server ) )

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)
	else :
		local_file_bare = local_file

	logger( "DEBUG: local_file_bare = \"{}\"".format( local_file_bare ) )

	# --------------------------------------------------------------------------------
	#  Ran into a case where the first FTP command failed...
	#    So we loop through a set of attempts.  Notice all the "continue" statements.
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
	# See https://stackoverflow.com/questions/567622/is-there-a-pythonic-way-to-try-something-up-to-a-maximum-number-of-times
	# --------------------------------------------------------------------------------
	for iii in range(12) :
		if iii > 0 :
		# Not on first iteration.  The increase the sleep time with each iteration.
			sleep( iii * 3 )
			logger( "WARNING: in push_to_server() FTP attempt #{}".format( iii ) )

		try :
			# ----------------------------------------------------------------
			# Ref: https://docs.python.org/2/library/ftplib.html
			# NOTE: The login/user, and password could be given here...
			#     FTP([host[, user[, passwd[, acct[, timeout]]]]])
			# ----------------------------------------------------------------
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
#DEBUG#			logger( "DEBUG: ftp = FTP( {}, {}, {} )".format( server, ftp_login, ftp_password ) )
			ftp = FTP( server, ftp_login, ftp_password )
		except Exception as problem :
			logger( "ERROR: in push_to_server() FTP (connect): {}".format( problem ) )
			continue

#DEBUG#		log_and_message( "DEBUG: remote_path = {}".format( remote_path ) )

		if len( remote_path ) > 1 :
			try :
#DEBUG#				logger( "DEBUG: FTP remote cd to {}".format( remote_path ) )
				ftp.cwd( remote_path )
			except Exception as problem :
				logger( "ERROR: in push_to_server() ftp.cwd {}".format( problem ) )
				continue

		try :
#DEBUG#			logger( "DEBUG: FTP STOR {} to  {}".format( local_file_bare, local_file) )
			ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
		except Exception as problem :
			logger( "ERROR: in push_to_server() ftp.storbinary {}".format( problem ) )
			continue

		try :
			ftp.quit()
		except Exception as problem :
			logger( "ERROR: in push_to_server() ftp.quit {}".format( problem ) )
			ftp.close()


		break

	return


# ----------------------------------------------------------------------------------------
#  Read the ftp_credentials_file and store the credentials for later usage.
#
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
	print( "{} {}".format( timestamp, message) )

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def log_and_message(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print( "{} {}".format( timestamp, message) )

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



# ========================================================================================
# ----------------------------------------------------------------------------------------
#  These routines store and fetch information we need to persist between invocations
#  of this script.  This needs to track what's already been "processed."
#
#  The variable last_timestamp is initialized to 0, but otherwise hold the tstamp for
#  the file last processed.
#
# ----------------------------------------------------------------------------------------
def store_file_data(tstamp) :
#DEBUG#	messager( "DEBUG: write " + stored_dir_mtime )
	FH = open( stored_dir_mtime, "a" )
	FH.write( str(tstamp) + "\n" )
	FH.close

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_ts() :
#DEBUG#	messager( "DEBUG: read " + stored_dir_mtime )
	try:
		FH = open( stored_dir_mtime, "r" )
		content = FH.readlines()
		FH.close

		tstamp = str(content[0].strip("\n"))
	except:
		logger( "WARNING: Creating new  \"{}\" file.".format( stored_dir_mtime ) )
		tstamp = 0
		store_file_data(tstamp)


	logger( "DEBUG: Stored tstamp = \"{}\" from get_stored_ts()".format( tstamp ) )

	return float(tstamp)




# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	log_string( "\n\n\n\n" )
	sys.stdout.write( "\n\n\n\n" )

	log_and_message("INFO: Starting {}   PID={}".format( this_script, getpid() ) )

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
