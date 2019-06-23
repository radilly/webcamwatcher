#!/usr/bin/python
# ps_check
#
# Check for a set of expect running processes.
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
# 20190622 RAD In assessing a missing process, one needs to know which pattern(s) wasn't
#              found.
# 20190609 RAD Started with a bash script but global variables in a loop caused an issue.
#              Copied watchdog.py to get a start.
#
# ========================================================================================

import re
import sys
import subprocess

infile = ""
found_PIDS = {}

# ----------------------------------------------------------------------------------------
#
#
# ----------------------------------------------------------------------------------------
def ps_check():

	found = 0

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
	ps_check()
	exit()


	print "\n\n\n\n\n"

