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
# NOTE: Should make sure each "ps" line printed is unique.
#
# ========================================================================================
# 20190609 RAD Started with a bash script but global variables in a loop caused an issue.
#              Copied watchdog.py to get a start.
#
# ========================================================================================

import re
import sys
import subprocess

infile = ""

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
				found += 1

	print "\nfound {} of the expected {} processes".format( found, len(pattern_list) )

	if found != len(pattern_list) :
		print "ERROR: Missing processes..."
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

