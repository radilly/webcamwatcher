#!/usr/bin/python
# process_check.py
#
# Check for a set of expected running processes.
#
# Initial input files...
#    cmx_procs.grep
#    rasp_cams.grep
#
# Hacked from watchdog.py
#
# NOTE: Should make sure each "ps" line printed is unique, i.e. unique PID
#       I think the most direct way is to accumulate PID in a dictionary...
#       https://stackoverflow.com/questions/1602934/check-if-a-given-key-already-exists-in-a-dictionary
#       Though this could be a simple list...?
#       https://www.programiz.com/python-programming/methods/list/pop
#
# ========================================================================================
# 20191223 RAD Intend to add an option to generate HTML.  Ultimately this would be
#              driven from a web server, but I've not put one on the Pi running
#              Cumulus MX yet.   I'm a litle concerned about loading and conflicts.
# 20190622 RAD In assessing a missing process, one needs to know which pattern(s) wasn't
#              found.
# 20190609 RAD Started with a bash script but global variables in a loop caused an issue.
#              Copied watchdog.py to get a start.
#
# ========================================================================================

import re
import sys
import subprocess
import argparse

infile = ""
found_PIDS = {}
use_html = False

# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def ps_check():

	found = 0
	return_value = 0

	FH = open(infile, "r")
#	FH = open("rasp_cams.grep", "r")

	# @@@ #######################################################################################################################################################################################################pattern_list = FH.readlines()
	lines = FH.readlines()
	FH.close

	# test_iii = 0
	pattern_list = []
	for line in lines :
		if re.match( "\s*#", line ) :
			continue
		# Python3 ???????????
		# if re.fullmatch( "\s*", line ) :
		if re.match( "^\s*$", line ) :
			continue
		pattern_list.append( line.rstrip() )
		# test_iii += 1
		# print test_iii
		# print pattern_list

	patterns = len(pattern_list)

	ps_output = subprocess.check_output( ["/bin/ps", "-ef"] )

	process = re.split('\n', ps_output)

	if use_html :
		print "<TABLE><TR><TH ALIGN=left>"
		print "<PRE>UID        PID  PPID  C STIME TTY          TIME CMD</PRE>"
		print "</TH></TR>"
	else :
		print "UID        PID  PPID  C STIME TTY          TIME CMD"

	for iii in range(0, len(process)):
		if iii > 555 :
			return

#		print "{}  {}".format( iii, process[iii] )

#		if "init" in process[iii] :
#			print "     init found!"

		for jjj in range(0, len(pattern_list)):
			if re.search( pattern_list[jjj], process[iii]) :

				if use_html :
					print "<TR><TD BGCOLOR=green>"
					print "<PRE>{}</PRE>".format( process[iii] )
					print "</TD></TR>"
				else :
					print "{}".format( process[iii] )


				token = re.split(' *', process[iii] )
				PID = token[1]
				if PID in found_PIDS :
					print "WARNING: duplicate PID {}".format( PID )
				found_PIDS[ PID ] = 1

				xxx = pattern_list.pop( jjj )
				# print "DEBUG: Popped \"{}\"".format( xxx )

				found += 1
				break   # Having changed the pattern_list length...

	if use_html :
		print "<TR><TD>"

	print "\nfound {} of the expected {} processes".format( found, patterns )

	if use_html :
		print "</TD></TR>"

	if found != patterns :
		return_value = 1

		if use_html :
			print "<TR><TD> &nbsp; </TD></TR>"
			print "<TR><TD>"

		print "ERROR: Missing processes..."

		if use_html :
			print "</TD></TR>"


	if len(pattern_list) > 0 :
		for jjj in range(0, len(pattern_list)):

			if use_html :
				print "<TR><TD BGCOLOR=red`>"

			print "{} {}".format( jjj + 1, pattern_list[jjj] )

			if use_html :
				print "</TD></TR>"

	if use_html :
		print "</TABLE>"

	return_value = 0
	exit( return_value )

	return


# ----------------------------------------------------------------------------------------
#
#
# Option to output HTML???
#   https://docs.python.org/2/howto/argparse.html
#   http://zetcode.com/python/argparse/
#
#
#
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	# global use_html

	# --------------------------------------------------------------------------------
	#   https://docs.python.org/2/howto/argparse.html
	# --------------------------------------------------------------------------------
	parser = argparse.ArgumentParser()
	parser.add_argument("infile", help="This will echo the (required) argument given")
	parser.add_argument("--html", help="Output in HTML", action="store_true")
	args = parser.parse_args()
#	print args.infile
#	if args.html:
#		print "html turned on"

	use_html = args.html

	infile = args.infile
	### infile = sys.argv[1]
	ps_check()
	exit()


	print "\n\n\n\n\n"





# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def argparse_examples():


	# --------------------------------------------------------------------------------
	#   https://docs.python.org/2/howto/argparse.html
	# --------------------------------------------------------------------------------
	parser = argparse.ArgumentParser()
	parser.add_argument("echo", help="This will echo the (required) argument given")
	parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
	args = parser.parse_args()
	print args.echo
	if args.verbose:
		print "verbose turned on"

	exit()


	# --------------------------------------------------------------------------------
	#   https://docs.python.org/2/howto/argparse.html
	# --------------------------------------------------------------------------------
	parser = argparse.ArgumentParser()
	parser.add_argument("echo", help="This will echo the (required) argument given")
	parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
	args = parser.parse_args()
	print args.echo
	if args.verbose:
		print "verbose turned on"

	exit()

	# --------------------------------------------------------------------------------
	#   https://docs.python.org/2/howto/argparse.html
	# --------------------------------------------------------------------------------
	parser = argparse.ArgumentParser()
	parser.add_argument("echo", help="This will echo the (required) argument given")
	parser.add_argument("--verbosity", help="increase output verbosity to the level specified")
	args = parser.parse_args()
	print args.echo
	if args.verbosity:
		print "verbosity turned on"

	exit()

	# --------------------------------------------------------------------------------
	#   https://docs.python.org/2/howto/argparse.html
	# --------------------------------------------------------------------------------
	parser = argparse.ArgumentParser()
	parser.add_argument("echo", help="This will echo the (required) argument given")
	args = parser.parse_args()
	print args.echo

	exit()


# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def ps_check______():

	found = 0
	return_value = 0

	FH = open(infile, "r")
#	FH = open("rasp_cams.grep", "r")
	pattern_list = FH.readlines()
	FH.close


	for iii in range(0, len(pattern_list)):
		pattern_list[iii] = pattern_list[iii].rstrip()
#		print pattern_list[iii]

	patterns = len(pattern_list)

	ps_output = subprocess.check_output( ["/bin/ps", "-ef"] )

	process = re.split('\n', ps_output)

	if use_html :
		print "<TABLE><TR><TH>"

	print "UID        PID  PPID  C STIME TTY          TIME CMD"

	if use_html :
		print "</TH></TR>"

	for iii in range(0, len(process)):
		if iii > 555 :
			return

#		print "{}  {}".format( iii, process[iii] )

#		if "init" in process[iii] :
#			print "     init found!"

		for jjj in range(0, len(pattern_list)):
			if re.search( pattern_list[jjj], process[iii]) :

				if use_html :
					print "<TR><TD BGCOLOR=green>"

				print "{}".format( process[iii] )

				if use_html :
					print "</TD></TR>"

				token = re.split(' *', process[iii] )
				PID = token[1]
				if PID in found_PIDS :
					print "WARNING: duplicate PID {}".format( PID )
				found_PIDS[ PID ] = 1

				xxx = pattern_list.pop( jjj )
				# print "DEBUG: Popped \"{}\"".format( xxx )

				found += 1
				break   # Having changed the pattern_list length...

	if use_html :
		print "<TR><TD>"

	print "\nfound {} of the expected {} processes".format( found, patterns )


	if use_html :
		print "</TD></TR>"

	if found != patterns :
		return_value = 1

		if use_html :
			print "<TR><TD> &nbsp; </TD></TR>"
			print "<TR><TD>"

		print "ERROR: Missing processes..."

		if use_html :
			print "</TD></TR>"


	if len(pattern_list) > 0 :
		for jjj in range(0, len(pattern_list)):

			if use_html :
				print "<TR><TD BGCOLOR=red`>"


			print "{} {}".format( jjj + 1, pattern_list[jjj] )

			if use_html :
				print "</TD></TR>"

	if use_html :
		print "</TABLE>"

	return_value = 0
	exit( return_value )

	return


# ----------------------------------------------------------------------------------------
