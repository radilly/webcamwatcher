#!/usr/bin/python3
# NOTE: @@@
#
#  This is intended to provide an interface to the statuscollector.service.
#  This was originally coded in watchdog.py, but the objective of that service is to
#  allow different processes, possibly running on other systems to add messages to
#  a central event log.
#
# ========================================================================================
import argparse
import re
import datetime
import time
import sys
import os

BASE_DIR =              "/home/pi"
BASE_DIR =              "/mnt/ssd"
status_dir =            BASE_DIR + "/status"

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
strftime_FMT = "%Y/%m/%d %H:%M:%S"

this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( os.getcwd(), re.sub('^\./', '', this_script) )

logger_file = re.sub('\.py', '.log', this_script)


# ----------------------------------------------------------------------------------------
# Appends an event table line (HTML) to the event list.
# Has to be maintained manually.
#
# NOTE: One possibility is to set colors for certain code ranges.
# ----------------------------------------------------------------------------------------
def log_event(ID, description, code, fill):

	logger( "DEBUG: in log_event({}, {}, {} ,{})".format( ID, description, code, fill ) )

	bgcolor = "TD"
	# Supply timestamp if no ID was given
	if len(ID) < 1 :
		ID = datetime.datetime.now().strftime(strftime_FMT)

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

	if len(fill) == 6  and re.match('^[0-9A-F]{6}$', fill, flags=re.I) :
		fill = "\"{}\"".format( fill )


	if len( fill ) > 0 :
		logger( "DEBUG: fill = \"{}\"".format( fill ) )
		bgcolor = "TD BGCOLOR={}".format( fill )


	format_str = "<TR><TD> {} </TD>\n<TD> {} </TD>\n<{}> {} </TD></TR>\n"

	status_file = "{}/{}.txt".format( status_dir, time.time() )
	FH = open(status_file, "w+")
	FH.write( format_str.format( ID, description, bgcolor, code) )
	FH.close



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
#
#   https://docs.python.org/3.7/library/argparse.html
#   http://zetcode.com/python/argparse/
#
# ----------------------------------------------------------------------------------------
logger( "DEBUG: sys.argv {}".format( sys.argv ) )

helptext = ""
helptext = helptext + "Registers a status event by writing a record into a file."
helptext = helptext + "  Typically used as a simple IPC to add records to an event log."
parser = argparse.ArgumentParser(description=helptext)

helptext = "Description of the event to be logged."
parser.add_argument("description", help=helptext)

helptext = "Code number, hopefully unique so it points to a specific code location."
parser.add_argument("code", type=int, help=helptext)

parser.add_argument("--id", default="", help="THIS COULD BE OPTIONAL.  If blanks, something like '2020/12/23 20:44:43 (local)'")
parser.add_argument("--bgcolor", default="", help="Specify background color for the code cell." +
	"  If hex, do NOT include the leading '#' character.")
# parser.add_argument("--html", help="Output in HTML", action="store_true")
args = parser.parse_args()

description = args.description
code = args.code

ID = args.id

bgcolor = args.bgcolor
if bgcolor == "none" :
	bgcolor = ""

logger( "DEBUG: log_event( {}, {}, {} ,{} )".format( ID, description, code, bgcolor ) )
log_event(ID, description, code, bgcolor)

exit()



#if "args.id" in globals() :
#	ID = ""
#else :
#	ID = args.id

#if len(args.id) > 0 :
#	ID = ""
#else :
#	ID = args.id

#if args.id :
#	ID = ""
#else :
#	ID = args.id


print( "description = \"{}\"".format( description ) )
print( "code = \"{}\"".format( code ) )
print( "ID = \"{}\"".format( ID ) )

exit()

log_event(ID, description, code)

exit()


print( "\n\n\n\n\n" )


