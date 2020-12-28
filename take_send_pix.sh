#!/usr/bin/bash

# This script uses the raspistill program - standard on all Raspberry OS versions -
# to take a still image and write it to a directory on a remote machine. Other
# than logging, this should minimze the I/O to the local SD card.
#
# The essential technique here to generate the raspistill outout to sdtout, and
# then pipe it over ssh to a dd command on the remote system to write the file.
#
#   raspistill -o -   |   ssh ss of=<file path and name>
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Modify these to match your installation.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REMOTE_ADDR="pi@192.168.1.167"
REMOTE_PATH="/mnt/ssd/N/North"


LOG=/home/pi/take_send_pix.txt
FILE=`/usr/bin/date +'snapshot-%Y-%m-%d-%H-%M-%S.jpg'`


date +'%T %Y%m%d' >> ${LOG} 2>&1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# NOTE: Paths differ between the Raspberry OS 2020-12-02 and 2018-06-27 (on the remote)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
/usr/bin/raspistill --quality 25 --thumb none \
	--annotate 12 --annotateex '16,0xff,0x808000' \
        --timeout 250 --width 640 --height 480 --nopreview -o - | \
        /bin/ssh ${REMOTE_ADDR} /bin/dd of=${REMOTE_PATH}/${FILE} >> ${LOG} 2>&1

/usr/bin/ssh ${REMOTE_ADDR} /bin/ls -l ${REMOTE_PATH}/${FILE} >> ${LOG} 2>&1


# /usr/bin/raspistill --quality 25 --thumb none --annotate 12 --annotateex '16,0xff,0x808000' --timeout 250 --width 640 --height 480 --nopreview -o ${FILE} >> ${LOG} 2>&1

# /usr/bin/scp ${FILE} ${REMOTE_ADDR}:${REMOTE_PATH} >> ${LOG} 2>&1

echo `date +%T` "done" >> ${LOG} 2>&1
# echo `date +%T` `/usr/bin/ls -l ${FILE}` >> ${LOG} 2>&1


exit

