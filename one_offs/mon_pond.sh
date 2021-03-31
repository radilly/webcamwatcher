#!/bin/bash

# 20210331 Embedded ping in a loop as it was failing once in a while
# If you pipe through grep directly, it appears the RC is from grep.

ITER=8
RC=-1
while [[ ${ITER} -gt 0  &&  ${RC} -ne 0 ]] ; do
#	echo "ITER = ${ITER}  and  RC = ${RC}"
	ITER=$( expr ${ITER} - 1 )
	PING_OUT=`ping -c 1 192.168.1.166` ; RC=$?
	if [[ ${RC} -ne 0 ]] ; then
		/home/pi/webcamwatcher/gpio_driver.py 16 hi > /dev/null
		date +'%T %F Status: Problem <<<<<<<<<'
	else
		/home/pi/webcamwatcher/gpio_driver.py 16 lo > /dev/null
		date +'%T %F Status: OK'
		sleep 3
		break
	fi
done

echo

exit




PING_OUT=`ping -c 1 192.168.1.166` ; RC=$?
echo "$PING_OUT" | egrep '(bytes of data.|packets transmitted)'
# echo "RC = ${RC}"
if [[ ${RC} -ne 0 ]] ; then
	/home/pi/webcamwatcher/gpio_driver.py 16 hi > /dev/null
	date +'%T %F Status: Problem <<<<<<<<<'
else
	/home/pi/webcamwatcher/gpio_driver.py 16 lo > /dev/null
	date +'%T %F Status: OK'
fi

echo

exit

