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

infile = ""
found_PIDS = {}

# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def log_check():

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
#
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

	infile = sys.argv[1]
	log_check()
	exit()


	print "\n\n\n\n\n"

