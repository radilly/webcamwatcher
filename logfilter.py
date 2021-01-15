#!/usr/bin/python3

# NOTE: https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html

#    cat `ls -tr /mnt/ssd/Cumulus_MX/MXdiags/* | tail -1` | ./logfilter.py | less -R

import sys
import re

for line in sys.stdin :

	line = line.rstrip()

	# line = re.sub('(?P<string>TEST/Test)', "\u001b[{}m\g<string>\u001b[0m".format( 41 ), line)
	line = re.sub("({})".format( "Error" ), "\u001b[{}m\g<1>\u001b[0m".format( 41             ), line)
	line = re.sub("({})".format( "N/North"   ), "\u001b[{}m\g<1>\u001b[0m".format( "44m\u001b[30" ), line)
	line = re.sub("({})".format( "WU Response:"   ), "\u001b[{}m\g<1>\u001b[0m".format( "32;1"         ), line)

	print( line )

exit()


#   Black:				\u001b[ 30    m
#   Red:				\u001b[ 31    m
#   Green:				\u001b[ 32    m
#   Yellow:				\u001b[ 33    m
#   Blue:				\u001b[ 34    m
#   Magenta:				\u001b[ 35    m
#   Cyan:				\u001b[ 36    m
#   White:				\u001b[ 37    m
#   Reset:				\u001b[ 0     m

#   Bright Black:			\u001b[ 30;1  m
#   Bright Red:				\u001b[ 31;1  m
#   Bright Green:			\u001b[ 32;1  m
#   Bright Yellow:			\u001b[ 33;1  m
#   Bright Blue:			\u001b[ 34;1  m
#   Bright Magenta:			\u001b[ 35;1  m
#   Bright Cyan:			\u001b[ 36;1  m
#   Bright White:			\u001b[ 37;1  m
#   Reset:				\u001b[ 0     m

#   Background Black:			\u001b[ 40    m
#   Background Red:			\u001b[ 41    m
#   Background Green:			\u001b[ 42    m
#   Background Yellow:			\u001b[ 43    m
#   Background Blue:			\u001b[ 44    m
#   Background Magenta:			\u001b[ 45    m
#   Background Cyan:			\u001b[ 46    m
#   Background White:			\u001b[ 47    m

#   Background Bright Black:		\u001b[ 40;1  m
#   Background Bright Red:		\u001b[ 41;1  m
#   Background Bright Green:		\u001b[ 42;1  m
#   Background Bright Yellow:		\u001b[ 43;1  m
#   Background Bright Blue:		\u001b[ 44;1  m
#   Background Bright Magenta:		\u001b[ 45;1  m
#   Background Bright Cyan:		\u001b[ 46;1  m
#   Background Bright White:		\u001b[ 47;1  m

#   Bold: 				\u001b[ 1     m
#   Underline: 				\u001b[ 4     m
#   Reversed: 				\u001b[ 7     m

def xxx() :
	line = line.rstrip()

	line = re.sub('TEST/Test', "\u001b[{}mTEST/Test\u001b[0m".format( 41 ), line)
	line = re.sub('N/North', "\u001b[{}mN/North\u001b[0m".format( "44m\u001b[30" ), line)
	line = re.sub('S/South', "\u001b[{}mS/South\u001b[0m".format( "32;1" ), line)

	line = re.sub('TEST/Test','\u001b[41mTEST/Test\u001b[0m',line)
	line = re.sub('N/North','\u001b[44m\u001b[30mN/North\u001b[0m',line)
	line = re.sub('S/South','\u001b[32;1mS/South\u001b[0m',line)

	print( line )
