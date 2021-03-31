#!/bin/bash


EXPECTED=$( expr `date +%_H` '*' 30 + `date +%_M` / 2 )
EXPECTEDx2=$( expr ${EXPECTED} '*' 2 )
EXPECTEDx2=$( expr `date +%_H` '*' 60 + `date +%_M` )

echo
date +"At %H:%M expect approximately ${EXPECTED} snapshots for today (or @ 1 minute interval, ${EXPECTEDx2})"
echo

for DIR in S/South N/North TEST/Test ; do
#	echo "home/pi/S/South" "/home/pi/N/North"
#	LETTER=`echo ${DIR} | sed 's/^\(.\).*/\1/'`
	DIR="/mnt/ssd/${DIR}"
	echo ${DIR}

	ls ${DIR} | sed -n 's/snapshot-//p' | cut -c1-10 | uniq | while read DATE ; do
#		printf "For ${DATE} in ${CAMERA}:  "
		printf "For date ${DATE} : "
		printf "%s snapshots\n\n" `ls ${DIR}/snapshot-${DATE}* | wc -l`
	done

done

exit
exit
exit
exit

#!/bin/bash


EXPECTED=$( expr `date +%_H` '*' 30 + `date +%_M` / 2 )

echo
date +"At %H:%M expect approximately ${EXPECTED} snapshots for today"
echo

for DIR in South North ; do
#	echo "home/pi/S/South" "/home/pi/N/North"
	LETTER=`echo ${DIR} | sed 's/^\(.\).*/\1/'`
	DIR="/mnt/ssd/${LETTER}/${DIR}"
	echo ${DIR}

	ls ${DIR} | sed -n 's/snapshot-//p' | cut -c1-10 | uniq | while read DATE ; do
#		printf "For ${DATE} in ${CAMERA}:  "
		printf "For date ${DATE} : "
		printf "%s snapshots\n\n" `ls ${DIR}/snapshot-${DATE}* | wc -l`
	done

done

exit
exit
exit
exit


EXPECTED=$( expr `date +%_H` '*' 30 + `date +%_M` / 2 )

echo
date +"At %H:%M expect approximately ${EXPECTED} snapshots for today"
echo

for DIR in South North ; do
#	echo "home/pi/S/South" "/home/pi/N/North"
	LETTER=`echo ${DIR} | sed 's/^\(.\).*/\1/'`
	DIR="/home/pi/${LETTER}/${DIR}"
	echo ${DIR}

	ls ${DIR} | sed -n 's/snapshot-//p' | cut -c1-10 | uniq | while read DATE ; do
#		printf "For ${DATE} in ${CAMERA}:  "
		printf "For date ${DATE} : "
		printf "%s snapshots\n\n" `ls ${DIR}/snapshot-${DATE}* | wc -l`
	done

done
exit


if [ $# -ne 1 ] ; then
	echo "ERROR: One paramter expected.  'north' or 'south'"
	exit
fi

CAMERA=`echo "${1}" | tr '[:upper:]' '[:lower:]'`

echo ${CAMERA} | egrep -qi '^(south|north)$' ; RC=${?}

if [ ${RC} -ne 0 ] ; then
	echo "ERROR: Paramter should be 'north' or 'south'"
	exit
fi

if [ ${CAMERA} == 'south' ] ; then
	DIRECTORY="/home/pi/S/South"
else
	DIRECTORY="/home/pi/N/North"
fi



ls ${DIRECTORY} | sed -n 's/snapshot-//p' | cut -c1-10 | uniq | while read DATE ; do printf "For ${DATE} in ${CAMERA}:  " ; ls ${DIRECTORY}/snapshot-${DATE}* | wc -l ; done

exit


if [ $# -ne 1 ] ; then
	echo "ERROR: One paramter expected.  'north' or 'south'"
	exit
fi

CAMERA=`echo "${1}" | tr '[:upper:]' '[:lower:]'`

echo ${CAMERA} | egrep -qi '^(south|north)$' ; RC=${?}

if [ ${RC} -ne 0 ] ; then
	echo "ERROR: Paramter should be 'north' or 'south'"
	exit
fi

if [ ${CAMERA} == 'south' ] ; then
	DIRECTORY="/home/pi/S/South"
else
	DIRECTORY="/home/pi/N/North"
fi



ls ${DIRECTORY} | sed -n 's/snapshot-//p' | cut -c1-10 | uniq | while read DATE ; do printf "For ${DATE} in ${CAMERA}:  " ; ls ${DIRECTORY}/snapshot-${DATE}* | wc -l ; done

