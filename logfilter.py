#!/usr/bin/python3

# NOTE: https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html

import sys
import re

for line in sys.stdin :

	line = line.rstrip()

	# line = re.sub('(?P<string>TEST/Test)', "\u001b[{}m\g<string>\u001b[0m".format( 41 ), line)
	line = re.sub("({})".format( "TEST/Test" ), "\u001b[{}m\g<1>\u001b[0m".format( 41             ), line)
	line = re.sub("({})".format( "N/North"   ), "\u001b[{}m\g<1>\u001b[0m".format( "44m\u001b[30" ), line)
	line = re.sub("({})".format( "S/South"   ), "\u001b[{}m\g<1>\u001b[0m".format( "32;1"         ), line)

	print( line )

exit()

def xxx() :
	line = line.rstrip()

	line = re.sub('TEST/Test', "\u001b[{}mTEST/Test\u001b[0m".format( 41 ), line)
	line = re.sub('N/North', "\u001b[{}mN/North\u001b[0m".format( "44m\u001b[30" ), line)
	line = re.sub('S/South', "\u001b[{}mS/South\u001b[0m".format( "32;1" ), line)

	line = re.sub('TEST/Test','\u001b[41mTEST/Test\u001b[0m',line)
	line = re.sub('N/North','\u001b[44m\u001b[30mN/North\u001b[0m',line)
	line = re.sub('S/South','\u001b[32;1mS/South\u001b[0m',line)

	print( line )
