#!/usr/bin/python
# @@@
#
#    NOTE:  Read probe "28-02099177c8a6"
#    NOTE:  Read probe "28-02099177c8a6"
#    NOTE:  Read probe "28-02099177c8a6"
#    NOTE:  Read probe "28-02099177c8a6"
#
#
# ----------------------------------------------------------------------------------------
#  This is intended to be run as a cgi-bin script.
#  It collects some information about the state of the system and renders a web page.
#  If copied to apache folder /usr/lib/cgi-bin/pi_health.py it can be accessed as
#      http://192.168.1.172/cgi-bin/pi_health.py  -  for example...
#
#  Check... (without browser)
#      curl localhost/cgi-bin/pi_health.py
#
# ----------------------------------------------------------------------------------------
# Depends on crontab entry:
#
#   */5 * * * * /home/pi/record_temp.sh
# ----------------------------------------------------------------------------------------
#
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# 20191104 RAD Been working on something to present tracked pond water temp.
#              Started with watchdog.py ... much of which is still here.
#
# ========================================================================================

import re
import datetime
import sys

# @@@
watertemplog="/home/pi/record_temp.waterlog"


logger_file = sys.argv[0]
logger_file = re.sub('\.py', '.log', logger_file)


# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
strftime_FMT = "%Y/%m/%d %H:%M:%S"


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

# @@@

        print "Content-type: text/html\n\n\n\n"
	print "<HEAD>\n"
#	print "table, th, td {"
#	print "  border: 1px solid black;"
#	print "}\n"
#	print "th, td {"
#  	print "padding: 15px;"
#	print "}\n"
	print "<TITLE> Pond Water Temp </TITLE>"
	# See https://www.quora.com/How-can-I-get-the-logo-on-title-bar
	print "<link rel = \"icon\" type = \"image/png\" href = \"WX_Blue_Green_32x32.png\">"
	print "</HEAD>"
	print "<H1 Align=left> Pond Water Temp </H1>"
	print "<H2 Align=left> 5-Minute Reads </H2>"
	print "<TABLE BORDER=1 CELLPADDING=3>"

	# --------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------
	check_lines = 5

	fileHandle = open ( watertemplog,"r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	for iii in range(-1, (-1 * (check_lines+1)), -1):
		lineList[iii] = re.sub('\n', ' ', lineList[iii])        # Remove any newline which might be left
		table_line( lineList[iii] )
		### print lineList[iii] 
		### messager( "DEBUG:  lineList[" + str(iii) + "] = \"" + lineList[iii] + "\"" )

	print "</TABLE>"

	print "<P><HR>"

	print "<H3 Align=left> Key for Fish Feeding by Temperature </H3>"
	print "<TABLE BORDER=1 CELLPADDING=3>"
	print "<TR BGCOLOR=\"#FF5555\"><TD> &nbsp; Do not feed fish. &nbsp; </TH><TR>"
	print "<TR BGCOLOR=\"yellow\"><TD> &nbsp; Feed every few days with cold water food. &nbsp; </TH><TR>"
	print "<TR BGCOLOR=\"#00F900\"><TD> &nbsp; Feed fish normally. &nbsp; </TH><TR>"
	print "</TABLE>"


	print "<P><HR>"

	print "<H2 Align=left> Hourly Reads </H2>"
	print "<TABLE BORDER=1 CELLPADDING=3>"

	for iii in range(-1-check_lines, (-1 * (check_lines+1)*11*check_lines), -12 ):
		lineList[iii] = re.sub('\n', ' ', lineList[iii])        # Remove any newline which might be left
		table_line( lineList[iii] )
		### print lineList[iii] 
		### messager( "DEBUG:  lineList[" + str(iii) + "] = \"" + lineList[iii] + "\"" )

	print "</TABLE>"


	return
	# --------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------








# ----------------------------------------------------------------------------------------
#
#
#
#
# ----------------------------------------------------------------------------------------
# @@@
def table_line( text_in ) :

###	text = re.sub( ",", " &nbsp; ", text_in, count=1 )
###	text = re.sub( ",", " </TD><TD> ", text, count=1 )
###	print "<TR><TD> " + text + "</TD><TR>"

###	print "<!-- DEBUG: text_in = \"{}\" -->".format( text_in )
	tok = re.split(',', text_in )
	temp = float( tok[2] )
###	print "<!-- DEBUG: temp = {} -->".format( temp )

	if temp < 40.0 :
		bgcolor = " BGCOLOR=\"#FF5555\""
	elif temp < 50.0 :
		bgcolor = " BGCOLOR=\"yellow\""
	else :
		bcgolor = " BGCOLOR=\"#00F900\""

###	print "<!-- DEBUG: bgcolor = {} -->".format( bgcolor )

	print "<TR{}><TD> &nbsp; {} &nbsp; {} &nbsp; </TD><TH> &nbsp; {}&deg; &nbsp; </TH><TR>".format( bgcolor, tok[0], tok[1], tok[2] )


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
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	try:
		main()
	except KeyboardInterrupt :
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
