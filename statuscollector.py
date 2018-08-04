#!/usr/bin/python -u
# @@@ ... Restart using...
#
#   kill -9 `cat ./statuscollector.PID`
#
#   nohup /usr/bin/python -u ./statuscollector.py /mnt/root/home/pi/status &
#
#   Takes 1 argument - the path to the directory to monitor for new messages.
#
# ----------------------------------------------------------------------------------------
#  * NOTE: Lots of unused code to clean up...
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
# ----------------------------------------------------------------------------------------
#
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
from urllib2 import urlopen, URLError, HTTPError
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
remote_dir = ""

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

last_timestamp = 0
dot_counter = 0
sleep_for = 10

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"
wserver = "dillys.org"


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

	log_and_message( "DEBUG: monitoring directory \"{}\"".format( work_dir ) )

	fetch_FTP_credentials( work_dir + "/.ftp.credentials" )

###	nvers = mono_version()
###	log_and_message("INFO: Mono version: {}" .format( nvers ) )

	python_version = "v " + str(sys.version)
	python_version = re.sub(r'\n', r', ', python_version )
	log_and_message( "INFO: Python version: {}".format( python_version ) )

	# May have to hand-create this file initially...
	last_image_dir_mtime = get_stored_ts()

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

	for dkey in reversed(sorted(msgqueue.keys())) :
		FH.write( "<!-- ----------- {} ---------- -->\n".format( dkey ) )
		for jjj in range( len(msgqueue[ dkey ] ) ) :
			FH.write( msgqueue[ dkey ][jjj] )

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


	store_file_data( image_dir_mtime )

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
		#  Messages should be named - time.time() + ".txt"
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

	# NOTE: When we write the web page we change image_dir_mtime for the next pass.
	last_image_dir_mtime = image_dir_mtime
	last_timestamp = filename

	events_page = "{}/event_status.html".format( work_dir )

	if len(msgqueue) >= 200 :
		prune_msgqueue( )

	if len( prev_page ) < 5 :
		prev_page = found_prev_page

	build_events_page( msgqueue, events_page, prev_page )

	push_to_server( events_page, remote_dir, wserver )

	dot_counter = 0

	log_and_message( "DEBUG: mtime = {} for {}".format( stat( events_page ).st_mtime, events_page ) )

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

	log_and_message( "DEBUG: in prune_msgqueue( )" )

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

	log_and_message( "DEBUG: local_file = {}   remote_path = {}   server = {}".format( local_file, remote_path, server ) )

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)
	else :
		local_file_bare = local_file

	log_and_message( "DEBUG: local_file_bare = {}".format( local_file_bare ) )

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
	for iii in range(8) :
		if iii > 1 :
		# Not on first iteration.  The increase the sleep time with each iteration.
			sleep( iii * 3 )

		try :
			# ----------------------------------------------------------------
			# Ref: https://docs.python.org/2/library/ftplib.html
			# NOTE: The login/user, and password could be given here...
			#     FTP([host[, user[, passwd[, acct[, timeout]]]]])
			# ----------------------------------------------------------------
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
			ftp = FTP( server, ftp_login, ftp_password )
		except Exception as problem :
			logger( "ERROR: FTP (connect): {}".format( problem ) )
			continue

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
		# Yes, that's a return that's not at the funtion end.
		# 08/04/2018 - I think replacing it with a break may be cleaner...
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
###		return
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
	FH = open( stored_dir_mtime, "w" )
	FH.write( str(tstamp) + "\n" )
	FH.close
# @@@

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_ts() :
#DEBUG#	messager( "DEBUG: read " + stored_dir_mtime )
	FH = open( stored_dir_mtime, "r" )
	content = FH.readlines()
	FH.close

	tstamp = str(content[0].strip("\n"))
	log_and_message( "DEBUG: Stored tstamp = \"{}\" from get_stored_ts()".format( tstamp ) )

	return tstamp




# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
#
#      NOTE:    Here for reference ... for the moment...
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------



# ----------------------------------------------------------------------------------------
#  This handles the tar of a daily set of image snapshots
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def tar_dailies(date_string) :
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
# Read the config file, and set global variables based on it.
#
# NOTE: While the flexibility to override any global may have some benefits, it's not
#       clear this shouldn't be limited to specific variables.  We do some verification
#       of the values, and in fact some of these are required or we fail to run.
# ----------------------------------------------------------------------------------------
def read_config( config_file ) :
	global work_dir, main_image, thumbnail_image, remote_dir
	global ftp_login, ftp_password
	global relay_GPIO, relay2_GPIO

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
