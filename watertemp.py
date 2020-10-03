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
#
# NOTE: The more general solution might be to read the full log which has readings
#       from two probes - usually.  For water temp we want ID 28-02099177c8a6.
#       Could be for some reason we're not reading it and we should handle...
#
#    ==> record_temp.log <==
#    01/02/20,20:55,28-02099177c8a6,1937,1.94,35.49,28-021791772e4a,9062,9.06,48.31,
#    01/02/20,21:00,28-02099177c8a6,1812,1.81,35.26,28-021791772e4a,9000,9.00,48.20,
#    01/02/20,21:05,28-02099177c8a6,1875,1.88,35.38,28-021791772e4a,8812,8.81,47.86,
#    01/02/20,21:10,28-02099177c8a6,2000,2.00,35.60,28-021791772e4a,8750,8.75,47.75,
#    01/02/20,21:15,28-02099177c8a6,2062,2.06,35.71,28-021791772e4a,8937,8.94,48.09,
#
#    ==> record_temp.waterlog <==
#    01/02/20,20:55,35.49
#    01/02/20,21:00,35.26
#    01/02/20,21:05,35.38
#    01/02/20,21:10,35.60
#    01/02/20,21:15,35.71
#
# ========================================================================================
# ========================================================================================
# ========================================================================================
# 20201003 RAD Added a bar chart column with scaling to exaggerate the changes.
# 20200102 RAD Was fiddling with the box inside where the temp was in the green
#              zone.  There was a typo in setting bgcolor in the default case.
#              Added quite of number of DEBUG prints to figure it out...
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

maxT = -999.0
minT = +999.0
rangeT = -1.0
scaleT = -1.0


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
	global minT, scaleT


	# --------------------------------------------------------------------------------
	# check_lines controls length of the first table, and the second
	# --------------------------------------------------------------------------------
	check_lines = 5

	fileHandle = open ( watertemplog,"r" )
	lineList = fileHandle.readlines()
	fileHandle.close()

	# --------------------------------------------------------------------------------
	#  Find the min and max readings.  Compute a scale facor for the bar chart.
	# --------------------------------------------------------------------------------
	maxT = -999.0
	for iii in range(-1, -140, -1 ):
		tok = re.split(',', lineList[iii])
		temp = float( tok[2] )
		maxT = max( maxT, temp )
		minT = min( minT, temp )
	rangeT = maxT - minT
	scaleT = 500 / rangeT

        print "Content-type: text/html\n\n\n\n"
        print "<META HTTP-EQUIV=\"refresh\" CONTENT=\"300\">"
	print "<HEAD>\n"
#	print "table, th, td {"
#	print "  border: 1px solid black;"
#	print "}\n"
#	print "th, td {"
#  	print "padding: 15px;"
#	print "}\n"
	print "<TITLE> Pond Water Temp </TITLE>"
	# See https://www.quora.com/How-can-I-get-the-logo-on-title-bar
	print "<link rel = \"icon\" type = \"image/png\" href = \"/WX_Blue_Green_32x32.png\">"
	print "</HEAD>"
	print "<H1 Align=left> Pond Water Temp </H1>"
	print "<BR> Min Temp = {:5.2f}&deg;".format( minT )
	print "<BR> Max Temp = {:5.2f}&deg;".format( maxT )
	print "<H2 Align=left> 5-Minute Reads </H2>"
	print "<TABLE BORDER=1 CELLPADDING=3>"

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

	for iii in range(-1-check_lines, ((check_lines+1) * -12 * check_lines), -12 ):
		lineList[iii] = re.sub('\n', ' ', lineList[iii])        # Remove any newline which might be left
		table_line( lineList[iii] )
		### print lineList[iii] 
		### messager( "DEBUG:  lineList[" + str(iii) + "] = \"" + lineList[iii] + "\"" )

	print "</TABLE>"


	return


# ----------------------------------------------------------------------------------------
# Called for each line in the tables generated.
#
#
#
# ----------------------------------------------------------------------------------------
# @@@
def table_line( text_in ) :
#	global minT, scaleT

	tok = re.split(',', text_in )
	temp = float( tok[2] )

	# --------------------------------------------------------------------------------
	# NOTE: code %23 maps to '#' sign
	# --------------------------------------------------------------------------------
	barWidth = int( 1 + (temp - minT) * scaleT )
	if temp < 40.0 :
###		print "<!-- DEBUG: temp < 40.0 -->"
		bgcolor = " BGCOLOR=\"#FF5555\""
		img = "<TD WIDTH=525 BGCOLOR=#000000><IMG SRC=\"/1_pixel_%23FF5555.jpg\" HEIGHT=8 WIDTH={}>".format( barWidth )
###		print "<!-- DEBUG: bgcolor = \"{}\" -->".format( bgcolor )
	elif temp < 50.0 :
###		print "<!-- DEBUG: temp < 50.0 -->"
		bgcolor = " BGCOLOR=\"yellow\""
		img = "<TD WIDTH=525 BGCOLOR=#000000><IMG SRC=\"/1_pixel_Yellow.jpg\" HEIGHT=8 WIDTH={}>".format( barWidth )
###		print "<!-- DEBUG: bgcolor = \"{}\" -->".format( bgcolor )
	else :
###		print "<!-- DEBUG: else clause -->"
		bgcolor = " BGCOLOR=\"#00F900\""
		img = "<TD WIDTH=525 BGCOLOR=#000000><IMG SRC=\"/1_pixel_%2300F900.jpg\" HEIGHT=8 WIDTH={}>".format( barWidth )
###		print "<!-- DEBUG: bgcolor = \"{}\" -->".format( bgcolor )

###	print "<!-- DEBUG: bgcolor = {} -->".format( bgcolor )

	print "<TR{}><TD> &nbsp; {} &nbsp; {} &nbsp; </TD><TH> &nbsp; {}&deg; &nbsp; </TH>{}</TD><TR>".format( bgcolor, tok[0], tok[1], tok[2], img )


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
