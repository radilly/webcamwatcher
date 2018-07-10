#!/bin/bash

# Use in the Pi staging folder to delete older files.
#
# KEEP controls how many we keep, typically a mulitple of 4

KEEP=16
#  One set of midnight files:
#       -rw-r--r-- 1 pi pi 37381560 Jul  9 00:02 arc-2018-07-08.tgz
#       -rw-r--r-- 1 pi pi 12864722 Jul  9 00:03 20180708.mp4
#       -rw-r--r-- 1 pi pi     4280 Jul  9 00:03 20180708-thumb.jpg
#       -rw-r--r-- 1 pi pi 12147344 Jul  9 00:05 20180708_daylight.mp4
DELETE=`ls *.tgz *.mp4 *.jpg | head -n -${KEEP} | wc -l`
USED_BEFORE=`df . | grep -v 'Filesystem' | awk '{print $3}'`

echo
echo "${DELETE} file(s) to delete"
echo

if [[ ${DELETE} -gt 0 ]] ; then
	echo "DELETING:"
	ls -tr *.tgz *.mp4 *.jpg | head -n -${KEEP} | while read FILE ; do
		ls -al ${FILE}
		rm ${FILE}
	done
	echo
fi

USED_AFTER=`df . | grep -v 'Filesystem' | awk '{print $3}'`
echo "1K Blcoks recovered = `expr ${USED_BEFORE} '-' ${USED_AFTER}`"

exit

