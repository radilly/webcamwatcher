#!/bin/bash

# --------------------------------------------------------------------------------
# NOTE: Example crontab...
# m h  dom mon dow   command
#
# 0,15,30,45 * * * * /home/pi/webcamwatcher/one_offs/mon_pond.sh >> /home/pi/mon_pond.log
# --------------------------------------------------------------------------------
# 20210331 Embedded ping in a loop as it was failing once in a while.
# If you pipe through grep directly, it appears the RC is from grep.
# --------------------------------------------------------------------------------

host="192.168.1.166"

ITER=8
RC=-1
while [[ ${ITER} -gt 0  &&  ${RC} -ne 0 ]] ; do
	PING_OUT=`ping -c 1 ${host}` ; RC=$?
	echo "ITER = ${ITER}  and  RC = ${RC}"
#################################	ITER=$( expr ${ITER} - 1 )
	(( ITER-- ))
	if [[ ${RC} -ne 0 ]] ; then
		/home/pi/webcamwatcher/gpio_driver.py 16 hi > /dev/null
		echo "$PING_OUT" | egrep 'packets transmitted'
		date +'%T %F Status: Problem <<<<<<<<<'
	else
		/home/pi/webcamwatcher/gpio_driver.py 16 lo > /dev/null
		echo "$PING_OUT" | egrep '(bytes of data.|packets transmitted)'
		date +'%T %F Status: OK'
		sleep 3
		break
	fi
done

echo

exit


