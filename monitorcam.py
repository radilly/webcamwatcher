#!/usr/bin/python3 -u
# @@@ @@@@@@ ... 
# 
# This script is started by 2 services - for for north- and south-facing cameras: 
#	webcam_north.service
#	webcam_south.service
#
# ----------------------------------------------------------------------------------------
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
# ========================================================================================
# 20201105 This was a hack of webcamimager.py.
#
# ========================================================================================
import subprocess
import configparser

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
from urllib.request import urlopen
# from urllib.error import URLError, HTTPError
import re

mon_log = ""
mon_max_age = 300

relay_GPIO = -1
relay2_GPIO = -1

work_dir = ""
main_image = ""
thumbnail_image = ""
remote_dir = ""
image_age_URL = ""

other_systemctl = ""

this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( os.getcwd(), re.sub('^\./', '', this_script) )

image_data_file = re.sub('\.py', '__.dat', this_script)
logger_file = re.sub('\.py', '.log', this_script)

ftp_login = ""
ftp_password = ""
ftp_server = ""

current_filename = ""

sleep_for = 8

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"
cam_host = "127.0.0.1"

cfg_parameters = [
	"work_dir",
	"main_image",
	"thumbnail_image",
	"remote_dir",
	"image_age_URL",
	"cam_host",
	"relay_GPIO",
	"relay2_GPIO",
	"relay_HOST",
	"mon_log",
	"mon_max_age",
	"other_systemctl",
	]



# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():

	if len(sys.argv) >= 2 :
		config_file = sys.argv[1]
	else :
		log_and_message( "ERROR: cfg file is a required first argument." )
		exit()

	if not os.path.isfile( config_file ) :
		log_and_message( "ERROR: cfg file \"{}\" not found.".format( config_file ) )
		exit()

	log_and_message( "INFO: reading \"{}\"".format( config_file ) )

#>>>	read_FTP_config( config_file )

#>>>	log_and_message( "INFO: ftp_server = \"{}\"".format(ftp_server) )
#>>>	log_and_message( "INFO: ftp_login = \"{}\"".format(ftp_login) )
#>>>	log_and_message( "INFO: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  ftp_password = \"{}\"".format(ftp_password) )

	read_config( config_file )

	log_and_message( "INFO: work_dir = \"{}\"".format(work_dir) )
	log_and_message( "INFO: main_image = \"{}\"".format(main_image) )
	log_and_message( "INFO: thumbnail_image = \"{}\"".format(thumbnail_image) )
	log_and_message( "INFO: remote_dir = \"{}\"".format(remote_dir) )
	log_and_message( "INFO: image_age_URL = \"{}\"".format( image_age_URL ) )
	log_and_message( "INFO: cam_host = \"{}\"".format( cam_host ) )
	log_and_message( "INFO: relay_HOST = \"{}\"".format( relay_HOST ) )
	log_and_message( "INFO: relay_GPIO = \"{}\"".format( relay_GPIO ) )
	log_and_message( "INFO: relay2_GPIO = \"{}\"".format( relay2_GPIO ) )
	log_and_message( "INFO: mon_log = \"{}\"".format( mon_log ) )
	log_and_message( "INFO: mon_max_age = \"{}\"".format( mon_max_age ) )
	log_and_message( "INFO: other_systemctl = \"{}\"".format( other_systemctl ) )
	log_and_message( "." )

	python_version = "v " + str(sys.version)
	python_version = re.sub(r'\n', r', ', python_version )
	log_and_message( "INFO: Python version: {}".format( python_version ) )

	old = -999
	log_and_message( "DEBUG: Monitoring: {}".format( image_age_URL ) )
	while True:
#>>>		next_image_file()
#>>>		check_log_age( )

		age = camera_down()
		if old > -1 and old != age :
			log_and_message( "DEBUG: image age changed" )
		log_and_message( "DEBUG: image age = {}".format( age ) )
		old = age
		sleep(sleep_for)

	exit()



# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
# NOTE: This should restart the "other" instance of this script.
#
# Checks the age of the monitored log.  If its not been updated recently (relative
# to mon_max_age) then we have a problem with the process appending to the log.
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def check_log_age( ) :
	global mon_log, mon_max_age


# @@@ here
	mtime = stat( mon_log ).st_mtime
	now = time.time()
#	print mtime
#	print time.time()
	age = now - mtime
#	print "DEBUG: age = {:10.2f}".format( age )

	if age > mon_max_age and len( other_systemctl ) > 0 :
		log_string( "\n" )
		log_and_message( "ERROR: \"{}\"  has not been updated for {:1.2f} seconds.".format( mon_log, age ) )

		restart_cmd = [ "/usr/bin/sudo",
				"/bin/systemctl",
				"restart",
				other_systemctl,
				]

		try:
			reply = subprocess.check_output( restart_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
			logger( "DEBUG: Result from {}: Returned = {} bytes.".format( restart_cmd, len(reply) ) )
		except Exception as problem :
			log_and_message( "ERROR: Unexpected ERROR in {}: {}".format( restart_cmd, sys.exc_info()[0] ) )
			log_and_message( "ERROR: systemctl restart: {}".format( problem ) )

	return




# ----------------------------------------------------------------------------------------
#  Check webcam status by fetching a control file from the hosted web-server.
#  The file just contains a number - the number of seconds between the time of
#  last writing the generically-named full-size image file, e.g. N.jpg by FTP,
#  an the current time.  Since cron_10_min.sh runs every 5 minutes
#
#   Can verify with: curl http://dillys.org/wx/North/N_age.txt
#
#  20180705 - Since moving most of the web cam image processing to the Pi, cron_10_min.sh
#  was seriously chopped down.  I also deleted a lof of the control files, including the
#  one this routine was looking at.  Oopps.  Looking at this routine, I decided it was
#  too complicated.
#
#  20180415 - Camera didn't stop, but was uploading some garbage periodically.
#  This file gets an epoch timestamp written to it when we've seen a number of 0-length
#  or rather short images uploaded from the webcam within a certain period.
#		response = urllib.urlopen('http://dillys.org/wx/N_cam_reboot_request.txt')
#
# ----------------------------------------------------------------------------------------
def camera_down():
#	global check_counter

	age = "0"

	# --------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------
	try :
		response = urlopen( image_age_URL )

		# NOTE: The decode() method seemed required for Python 3.  See
		#       https://stackoverflow.com/questions/31019854/typeerror-cant-use-a-string-pattern-on-a-bytes-like-object-in-re-findall
		#       https://stackoverflow.com/questions/37722051/re-search-typeerror-cannot-use-a-string-pattern-on-a-bytes-like-object
		content = response.read().decode('utf-8')

	except ( URLError, Exception ) as err :
		log_and_message( "ERROR: in camera_down: {}".format( sys.exc_info()[0] ) )
		# ------------------------------------------------------------------------
		#  See https://docs.python.org/2/tutorial/errors.html (~ middle)
		# ------------------------------------------------------------------------
		log_and_message( "ERROR: type: {}".format( type(err) ) )
		log_and_message( "ERROR: args: {}".format( err.args ) )
		if hasattr(err, 'reason'):
			log_and_message( 'ERROR: We failed to reach a server.' )
			log_and_message( 'ERROR: Reason: {}'.format( err.reason ) )

		elif hasattr(err, 'code'):
			log_and_message( 'ERROR: The server couldn\'t fulfill the request.' )
			log_and_message( 'ERROR: code: {}'.format( err.code ) )

		else:
			log_and_message( 'ERROR: Reason: {}'.format( err.reason ) )
			log_and_message( 'ERROR: code: {}'.format( err.code ) )

		# ------------------------------------------------------------------------
		#  https://docs.python.org/2/tutorial/errors.html
		#  https://docs.python.org/2/library/sys.html
		#  https://docs.python.org/3/library/traceback.html
		#  https://docs.python.org/2/library/traceback.html
		#
		#  https://stackoverflow.com/questions/8238360/how-to-save-traceback-sys-exc-info-values-in-a-variable
		# ------------------------------------------------------------------------
		content = "-1\n-1"
		logger( "DEBUG: content = \"" + content + "\" in camera_down()" )

	logger( "DEBUG: content = \"" + content + "\" in camera_down()" )

	#---# logger( "DEBUG: len(content) = {}".format( len(content) ) )
	lines = re.split( '\n', content )
	#---# logger( "DEBUG: len(lines) = {}".format( len(lines) ) )

	age = int( lines[0] )
	age_secs = int( lines[1] )

	now_secs = int( time.time() )
	# --------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------

	ssh_cmd = ["ssh", "pi@127.0.0.1", "/bin/date", "+%s", "-r", "/home/pi/N/webcamimager.log"]

#	logger( "DEBUG: subprocess.check_output([\"scp\", \"-q\", \"-P\", \"21098\", {}, {}])".format( local_file, destination ) )

	# Create empty array in case the try block fails. This by the way creates a 0-th member.
	# Before I got the logic right with an "or" below, I saw...
	#   DEBUG: #0 ""
	try :
		output = subprocess.check_output( ssh_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
	except subprocess.CalledProcessError as e :
		ssh_failed = True
		# lines = []
		# lines[0] = ""
	# if len(lines[0]) > 0 or len(lines) > 1 :
		output = ""
		logger( "ERROR: ssh: \"{}\" (from camera_down(), CalledProcessError)".format( sys.exc_info()[0] ) )
		logger( "DEBUG: ssh cmd = {}".format( e.cmd ) )
		logger( "DEBUG: ssh returncode = {}".format( e.returncode ) )
		logger( "DEBUG: ssh error output:\n{}".format( e.output ) )
		# https://stackoverflow.com/questions/7575284/check-output-from-calledprocesserror
	except :
		ssh_failed = True
		# lines = []
		# lines[0] = ""
		output = ""
		logger( "ERROR: ssh: {} (from camera_down(), general case)".format( sys.exc_info()[0] ) )


	log_mtime = int( output )
	log_and_message( "DEBUG: log_mtime = {} - - - {}".format( log_mtime, now_secs - log_mtime ) )

	lines = re.split('\n', output)




	calculated = now_secs - age_secs

	logger( "DEBUG: Server image age = {}".format(age) )
	# return "{} / {}  calc: {}".format( age, age_secs, calculated )
	return age_secs



	# ================================================================================
	#
	# ================================================================================
	log_and_message( "INFO: mon_max_age = \"{}\"".format( mon_max_age ) )
	if age > 420 :
		logger("WARNING: image age: {}".format( age ) )
		power_cycle( 5 )
#		log_restart( "webcam power-cycled, interval: {}".format( age ) )
		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.
		sleep(2)
#		sleep(sleep_on_recycle)
		return 1
	else:
		return 0








# ----------------------------------------------------------------------------------------
# Read the config file, and set global variables based on it.
#
# NOTE: While the flexibility to override any global may have some benefits, it's not
#	clear this shouldn't be limited to specific variables.  We do some verification
#	of the values, and in fact some of these are required or we fail to run.
#
#	See cfg_parameters array for checking.
# ----------------------------------------------------------------------------------------
def read_config( config_file ) :
	global work_dir, main_image, thumbnail_image, remote_dir
	global cam_host, relay_HOST
	global relay_GPIO, relay2_GPIO, webcam_ON, webcam_OFF
	global mon_log, mon_max_age
	global other_systemctl

# 	# https://docs.python.org/2/library/configparser.html
	config = configparser.RawConfigParser()
	# This was necessary to avoid folding variable names to all lowercase.
	# https://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
	config.optionxform = str
	config.read( config_file )
	#print config.getboolean('Settings','bla') # Manual Way to acess them

	# https://stackoverflow.com/questions/924700/best-way-to-retrieve-variable-values-from-a-text-file-python-json
	parameter=dict(config.items("webcamimager"))
	for p in parameter:
		parameter[p]=parameter[p].split("#",1)[0].strip() # To get rid of inline comments
###		messager( "DEBUG: p = {}".format( p ) )
###		messager( "DEBUG: parameter[p] = {}".format( parameter[p] ) )

	globals().update(parameter)  #Make them availible globally

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
	relay_GPIO = int( relay_GPIO )

	relay2_GPIO = int( relay2_GPIO )

#>>>	if not os.path.exists( mon_log ) :
#>>>		log_and_message( "ERROR: mon_log \"{}\" not found.".format( mon_log ) )
#>>>		exit()

	mon_max_age = int( mon_max_age )




# ----------------------------------------------------------------------------------------
# Cycle the power on the relay / GPIO.
# The off time can be specified.  Here in secs.
#
# From a quick test, the (South) RSX-3211 webam seems to take around 32 secs to reboot.
# ----------------------------------------------------------------------------------------
def power_cycle( interval ):

	cmd = "ssh {} /home/pi/webcamwatcher/power_cycle.py {}".format( relay_HOST, relay_GPIO )

	log_and_message( cmd )

	process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output,stderr = process.communicate()
	status = process.poll()
	log_and_message( status )
	log_and_message( output )

	return





# ========================================================================================
# ----------------------------------------------------------------------------------------
#  These routines store and fetch information we need to persist between invocations
#  of this script.  This needs to track what's already been "processed."
#
#  The variable last_mtime is initialized to 0.0, but otherwise hold the ts for
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
	try:
		FH = open(image_data_file, "r")
		content = FH.readlines()
		FH.close

		ts = str(content[0].strip("\n"))
	except:
		ts = 0.0
		filename = "snapshot-2000-01-01-01-01-01.jpg"
		store_file_data(ts, filename)

	logger( "DEBUG: Stored ts = {}".format( ts ) )

	return ts

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_filename() :
	global image_data_file
#DEBUG#	messager( "DEBUG: read " + image_data_file )

	try:
		FH = open(image_data_file, "r")
		content = FH.readlines()
		FH.close

		filename = str(content[1].strip("\n"))
	except:
		ts = 0.0
		filename = "snapshot-2000-01-01-01-01-01.jpg"
		store_file_data(ts, filename)

	logger( "DEBUG: Stored filename = {}".format( filename ) )

	return filename











# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
#  This selects the file transfer protocol we'll use.
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def push_to_server(local_file, remote_path) :

	push_to_server_via_scp(local_file, remote_path)
	return

	push_to_server_via_ftp(local_file, remote_path)




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
def push_to_server_via_scp(local_file, remote_path) :

#	destination = "user@remotehost:remotepath"
	destination = "dillwjfq@premium29.web-hosting.com:public_html/wx/" + remote_path
	scp_failed = False

#	logger( "DEBUG: subprocess.check_output([\"scp\", \"-q\", \"-P\", \"21098\", {}, {}])".format( local_file, destination ) )

	# Create empty array in case the try block fails. This by the way creates a 0-th member.
	# Before I got the logic right with an "or" below, I saw...
	#   DEBUG: #0 ""
	try :
		output = subprocess.check_output(["scp", "-q", "-P", "21098", local_file, destination], stderr=subprocess.STDOUT ).decode('utf-8')
	except subprocess.CalledProcessError as e :
		scp_failed = True
		# lines = []
		# lines[0] = ""
	# if len(lines[0]) > 0 or len(lines) > 1 :
		output = ""
		logger( "ERROR: scp: \"{}\" (from push_to_server_via_scp(), CalledProcessError)".format( sys.exc_info()[0] ) )
		logger( "DEBUG: scp cmd = {}".format( e.cmd ) )
		logger( "DEBUG: scp returncode = {}".format( e.returncode ) )
		logger( "DEBUG: scp error output:\n{}".format( e.output ) )
		# https://stackoverflow.com/questions/7575284/check-output-from-calledprocesserror
	except :
		scp_failed = True
		# lines = []
		# lines[0] = ""
		output = ""
		logger( "ERROR: scp: {} (from push_to_server_via_scp(), general case)".format( sys.exc_info()[0] ) )


	lines = re.split('\n', output)
	# if len(lines[0]) > 0 or len(lines) > 1 :
	if scp_failed and len(lines) > 1 :
		logger( "DEBUG: scp stdout output:\n".format( e.output ) )
		for jjj in range( len(lines) ) :
			logger( "DEBUG: #{} \"{}\"".format( jjj, lines[jjj] ) )
	
	return



# ----------------------------------------------------------------------------------------
#  This pushes the specified file to the (hosted) web server via FTP.
#
#
#  FTP User: camdilly
#  FTP PWD: /home/content/b/o/b/bobdilly/html/WX
#
#  https://pythonspot.com/en/ftp-client-in-python/
#  https://docs.python.org/2/library/ftplib.html
#    NOTE: 
#    NOTE: 
#    NOTE: The third argument, server, is no longer needed...
#    NOTE: 
#    NOTE: 
# ----------------------------------------------------------------------------------------
def push_to_server_via_ftp(local_file, remote_path) :
	ftp_OK = False

#DEBUG#	logger( "DEBUG: push_to_server_via_ftp( {}, {}, {} )".format( local_file, remote_path, server ) )
#DEBUG#	logger( "DEBUG: push_to_server_via_ftp( {}, {}, {} )".format( local_file, remote_path, ftp_server ) )

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)

	# --------------------------------------------------------------------------------
	#  The ftp sequence involves 4 commands.  If any fail, those that follow may
	#  not make any sense to attempt, with the possible exception of quit (which
	#  could itself fail.
	#    ftp = FTP( server, ftp_login, ftp_password )
	#    ftp.cwd( remote_path )
	#    ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
	#    ftp.quit()
	#  Ran into a case where the first FTP command failed...
	#
	# https://stackoverflow.com/questions/567622/is-there-a-pythonic-way-to-try-something-up-to-a-maximum-number-of-times
	# --------------------------------------------------------------------------------
	for iii in range(8) :
		# Not on first iteration.  Then increase the sleep time with each iteration.
		#  With a 4 sec multiplier this comes to 112 seconds max...     (28 * 4)
		if iii > 0 :
			logger( "DEBUG: in push_to_server_via_ftp() sleep( {} )".format( iii * 4 ) )
			sleep( iii * 4 )

		try :
			# ----------------------------------------------------------------
			#
			# Ref: https://docs.python.org/2/library/ftplib.html
			# NOTE: The login/user, and password could be given here...
			#	FTP([host[, user[, passwd[, acct[, timeout]]]]])
			#
			# ----------------------------------------------------------------
			#  Odds are if this works, the remainng commands probably will
			# ----------------------------------------------------------------
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
			ftp = FTP( ftp_server, ftp_login, ftp_password )
			ftp_OK = True
			break
		except Exception as problem :
			logger( "ERROR: in push_to_server_via_ftp() FTP (connect): {}".format( problem ) )

			logger( "DEBUG: FTP credentials: s=\"{}\" l=\"{}\" p=\"{}\"".format( ftp_server, ftp_login, ftp_password ) )
#@@@			if "authentication" in problem :
#@@@				logger( "DEBUG: FTP credentials: s=\"{}\" l=\"{}\" p=\"{}\"".format( ftp_server, ftp_login, ftp_password ) )

	# --------------------------------------------------------------------------------

	if ftp_OK :
		try :
#DEBUG#			logger( "DEBUG: FTP remote cd to {}".format( remote_path ) )
			ftp.cwd( remote_path )
		except Exception as problem :
			logger( "ERROR: in push_to_server_via_ftp() ftp.cwd {}".format( problem ) )
			ftp_OK = False
	# --------------------------------------------------------------------------------
	#  Not absolutely sure I want to do this, but sometimes the process is just hosed...
	# --------------------------------------------------------------------------------
	else:
		exit()


	# --------------------------------------------------------------------------------
	# NOTE: It looks like this might be a temporary condition and a retry might
	#       might be in order...
	#       I would expect this is the previous use of the socket was busy.
	#       I suppose it could be 2 instances of this trying to ftp files concurrently.
	#
	#  https://stackoverflow.com/questions/6176445/problem-socket-error-address-already-in-use-in-python-selenium
	#  https://stackoverflow.com/questions/41423642/python-socket-server-address-already-in-use
	#
	# --------------------------------------------------------------------------------

	if ftp_OK :
		for iii in range(8) :
			if iii > 0 :
				logger( "DEBUG: in push_to_server_via_ftp() sleep( {} )".format( iii * 4 ) )
				sleep( iii * 4 )

			try :
				if iii > 0 :
					logger( "DEBUG: FTP STOR {} ===> {}  attempt #{}".format( local_file, local_file_bare, iii+1) )
				else :
					dummy_for_else_clause = 1
#DEBUG#					logger( "DEBUG: FTP STOR {} ---> {}".format( local_file, local_file_bare ) )

				ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
				ftp_OK = True
				break

			except Exception as problem :
				logger( "ERROR: in push_to_server_via_ftp() ftp.storbinary \"{}\"".format( problem ) )
				# --------------------------------------------------------
				# --------------------------------------------------------
				#                       if not catching_up and ( (file_list_len - line) > 2 ) :
				# @@@
				# Should wait and retry when problem =
				#
				# 425 Unable to identify the local data socket: Address already in use
				#						997 in sample
				#
				# Wrap in a loop as with the above line:
				#    ftp = FTP( ftp_server, ftp_login, ftp_password )
				#
				#
				# Other repiles to consider are:
 				# [Errno 101] Network is unreachable		3 in sample
 				# [Errno 110] Connection timed out		76 in sample
				#						out of 102841 calls
				# --------------------------------------------------------
				# --------------------------------------------------------
				ftp_OK = False


	try :
		ftp.quit()
	except Exception as problem :
		logger( "ERROR: in push_to_server_via_ftp() ftp.quit {}".format( problem ) )
		ftp.close()


	return


# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# NOTE: Most of the call to messager() should be converted to logger() at some point.
#	especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)

	FH = open(logger_file, "a")
	FH.write( "{} {}\n".format( timestamp, message) )
	FH.close

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print("{} {}".format( timestamp, message))

# ----------------------------------------------------------------------------------------
# Print and log the message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def log_and_message(message):
	messager(message)
	logger(message)

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
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
	#### This might be useful...
	#### if sys.argv[1] = "stop"
	log_string( "\n\n\n\n" )
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
# ----------------------------------------------------------------------------------------
