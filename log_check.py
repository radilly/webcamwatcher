#!/usr/bin/python
# log_check
#
# Check for aging of a set of files
#
# Initial input file...
#    ~/tracked_logs.txt
#
# Hacked from process_check.py
#
# NOTE: In my testing the 3 logs I monitored were updated with rather varied
#       frequency.  A second argument could be the acceptable age limit.
#
#
# ========================================================================================
# 20190722 RAD The age of certain logs may be a better indicator of a stuck process.
#              Started with a copy of process_check.py
#
# ========================================================================================

import re
import sys
import subprocess
from os import stat
import time
import argparse

infile = ""
found_PIDS = {}
use_html = False

# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def log_check():

	found = 0

	FH = open(infile, "r")
#	FH = open("rasp_cams.grep", "r")
	lines = FH.readlines()
	FH.close


	# test_iii = 0
	log_file_list = []
	for line in lines :
		if re.match( "\s*#", line ) :
			continue
		# Python3 ???????????
		# if re.fullmatch( "\s*", line ) :
		if re.match( "^\s*$", line ) :
			continue
		log_file_list.append( line.rstrip() )
		# test_iii += 1
		# print test_iii
		# print log_file_list


#########################	for iii in range(0, len(log_file_list)):
#########################		log_file_list[iii] = log_file_list[iii].rstrip()
#		print log_file_list[iii]
#
#		NOTE: Doesn't work because range is called just once above...
#		if re.search('^#', log_file_list[iii]) :
#			log_file_list.pop( iii )

	log_files = len(log_file_list)

	if use_html :
#		print "<TABLE><TR><TH ALIGN=left>"
		print "<TABLE><TR><TD>"
		print "DEBUG: checking {} log files...".format( log_files )
		print "</TD></TR>"
#		print "</TH></TR>"
	else :
		print "DEBUG: checking {} log files...".format( log_files )

	now = time.time()

	for iii in range(0, len(log_file_list)):
		if re.search('^#', log_file_list[iii]) :
			continue

		age_limit = 99999
		token = re.split('\s*', log_file_list[iii] )
		if len(token) > 1 :
			age_limit = token[1]
			log_file_list[iii] = token[0]
#		print "DEBUG: pattern {} \"{}\"".format( iii, log_file_list[iii] )
		log_mtime = stat( log_file_list[iii] ).st_mtime
		age = now - log_mtime
#		print "DEBUG: mtime = {}".format( log_mtime )

		if use_html :
			print "<TR><TD BGCOLOR=green>"
			print "<PRE>DEBUG: age = {:8.2f}  max = {:8.2f}  {}</PRE>".format( age, float(age_limit), log_file_list[iii] )
			print "</TD></TR>"
		else :
			print "DEBUG: age = {:8.2f}  max = {:8.2f}  {}".format( age, float(age_limit), log_file_list[iii] )


		if age > float(age_limit) :

			if use_html :
				print "<TR><TD BGCOLOR=red>"
				print "<PRE>ERROR: log file {} is age = {:8.2f} seconds old (beyond {:8.2f} )</PRE>".format( log_file_list[iii], age, float(age_limit) )
				print "</TD></TR>"
			else :
				print "ERROR: log file {} is age = {:8.2f} seconds old (beyond {:8.2f} )".format( log_file_list[iii], age, float(age_limit) )

	if use_html :
		print "</TABLE>"

	exit()
	exit()
	exit()
	exit()
	exit()

#	image_dir_mtime = stat( work_dir ).st_mtime



# ----------------------------------------------------------------------------------------
# def log_check():

	found = 0

	FH = open(infile, "r")
#	FH = open("rasp_cams.grep", "r")
	pattern_list = FH.readlines()
	FH.close


	for iii in range(0, len(pattern_list)):
		pattern_list[iii] = pattern_list[iii].rstrip()
#		print pattern_list[iii]
#
#		NOTE: Doesn't work because range is called just once above...
#		if re.search('^#', pattern_list[iii]) :
#			pattern_list.pop( iii )

	patterns = len(pattern_list)

	now = time.time()

	for iii in range(0, len(pattern_list)):
		if re.search('^#', pattern_list[iii]) :
			continue

		age_limit = 99999
		token = re.split('\s*', pattern_list[iii] )
		if len(token) > 1 :
			age_limit = token[1]
			pattern_list[iii] = token[0]
#		print "DEBUG: pattern {} \"{}\"".format( iii, pattern_list[iii] )
		log_mtime = stat( pattern_list[iii] ).st_mtime
#		print "DEBUG: mtime = {}".format( log_mtime )
		print "DEBUG: age = {:8.2f}  max = {:8.2f}  {}".format( now - log_mtime, float(age_limit), pattern_list[iii] )

	exit()
	exit()
	exit()
	exit()
	exit()

#	image_dir_mtime = stat( work_dir ).st_mtime




	ps_output = subprocess.check_output( ["/bin/ps", "-ef"] )

	process = re.split('\n', ps_output)

	print "UID        PID  PPID  C STIME TTY          TIME CMD"
	for iii in range(0, len(process)):
		if iii > 555 :
			return

#		print "{}  {}".format( iii, process[iii] )

#		if "init" in process[iii] :
#			print "     init found!"

		for jjj in range(0, len(pattern_list)):
			if re.search( pattern_list[jjj], process[iii]) :
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

	print "\nfound {} of the expected {} processes".format( found, patterns )

	if found != patterns :
		print "ERROR: Missing processes..."

	if len(pattern_list) > 0 :
		for jjj in range(0, len(pattern_list)):
			print "{} {}".format( jjj + 1, pattern_list[jjj] )


		exit( 1 )

	exit( 0 )

	return



# ----------------------------------------------------------------------------------------
#
# Option to output HTML???
#   https://docs.python.org/2/howto/argparse.html
#   http://zetcode.com/python/argparse/
#
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
	parser.add_argument("infile", help="Contains a list of log file to check, and optionally a time threshhold")
	parser.add_argument("--html", help="Output in HTML", action="store_true")
	args = parser.parse_args()
#	print args.infile
#	if args.html:
#		print "html turned on"
	if not args.html:
		print "\n\n\n\n\n"

	use_html = args.html

	infile = args.infile
	### infile = sys.argv[1]
	log_check()
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
