#!/bin/bash

# Roll the webcamimager.log

OLD_FILE=`date +webcamimager.%Y%m%d.log`


if [[ -f webcamimager.log ]] ; then
	echo "INFO: Waiting for last line of log to be an INFO or DEBUG message..."
else
	echo "ERROR: File webcamimager.log not found!"
	exit
fi

# exit

# Wait for last line to be an info message
# set -xv
# while [[ `tail -n 1 webcamimager.log | grep -c INFO:` -lt 1 ]] ; do
while [[ `tail -n 1 webcamimager.log | egrep -c ' (DEBUG|INFO): '` -lt 1 ]] ; do
	sleep 1
	printf "."
	true
done

echo "rolling log..."
mv webcamimager.log ${OLD_FILE}
tail -n 250 ${OLD_FILE} >> webcamimager.log
gzip ${OLD_FILE}


exit


 1456  while [[ `tail -n 1 webcamimager.log | grep -c INFO` -lt 1 ]] ; do true ; done ; tail -n 3 webcamimager.log
 1457  echo mv webcamimager.log `date +webcamimager.%Y%m%d.log` ; echo touch webcamimager.log
 1458  while [[ `tail -n 1 webcamimager.log | grep -c INFO` -lt 1 ]] ; do true ; done ; tail -n 3 webcamimager.log ; mv webcamimager.log `date +webcamimager.%Y%m%d.log` ; tail -n 250 `date +webcamimager.%Y%m%d.log` >> webcamimager.log
 1459  ls -altr
 1460  ttttn
 1461  head webcamimager.log 
 1462  cd ../S/
 1463  while [[ `tail -n 1 webcamimager.log | grep -c INFO` -lt 1 ]] ; do true ; done ; tail -n 3 webcamimager.log ; mv webcamimager.log `date +webcamimager.%Y%m%d.log` ; tail -n 250 `date +webcamimager.%Y%m%d.log` >> webcamimager.log
 1464  head webcamimager.log 
 1465  history | tail > roll_webcamimager_log.sh
