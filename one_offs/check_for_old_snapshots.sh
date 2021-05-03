#!/bin/bash

# On web cam image collector Pi, check for old snapshot jpg files.


EXPECTED=$( expr `date +%_H` '*' 30 + `date +%_M` / 2 )
EXPECTEDx2=$( expr ${EXPECTED} '*' 2 )
EXPECTEDx2=$( expr `date +%_H` '*' 60 + `date +%_M` )

echo
date +"At %H:%M expect approximately ${EXPECTED} snapshots for today (or @ 1 minute interval, ${EXPECTEDx2})"
echo

TODAY=$( date +%Y-%m-%d )

for DIR in S/South N/North TEST/Test ; do
#	echo "home/pi/S/South" "/home/pi/N/North"
#	LETTER=`echo ${DIR} | sed 's/^\(.\).*/\1/'`
	DIR="/mnt/ssd/${DIR}"
	echo ${DIR}

	ls ${DIR} | sed -n 's/snapshot-//p' | cut -c1-10 | uniq | while read DATE ; do
#		printf "For ${DATE} in ${CAMERA}:  "
		printf "For date ${DATE} : "
		printf "%s snapshots\n" `ls ${DIR}/snapshot-${DATE}* | wc -l`
		if [[ "$TODAY" -ne "${DATE}" ]] ; then
			echo "OLD!!  ls ${DIR}/snapshot-${DATE}\*.jpg"
		fi
		echo
	done

done

exit

