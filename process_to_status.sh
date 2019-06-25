#!/bin/bash

# Use in the Pi staging folder to delete older files.
#
# KEEP controls how many we keep, typically a mulitple of 3


STAT_FILE="/mnt/root/home/pi/Cumulus_MX/web/status.html"
STAT_FILE="/mnt/root/home/pi/Cumulus_MX/web/procs.html"

echo "<HEAD><TITLE>" > ${STAT_FILE}
echo "Raspberry Pi Expected Processes" >> ${STAT_FILE}
echo "</TITLE></HEAD><BODY BGCOLOR="#555555" TEXT="#FFFFFF" LINK="#FFFF00" VLINK="#FFBB00" ALINK="#FFAAFF"><H1 ALIGN=center>" >> ${STAT_FILE}
echo "Raspberry Pi Expected Processes" >> ${STAT_FILE}
echo "</H1>" >> ${STAT_FILE}
echo "" >> ${STAT_FILE}
echo "<CENTER>" >> ${STAT_FILE}
echo "<TABLE>" >> ${STAT_FILE}
echo "<TR><TD>" >> ${STAT_FILE}

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<BR> Local on `hostname` <BR>" >> ${STAT_FILE}
echo "</TD></TR>" >> ${STAT_FILE}
echo "<TR><TD>" >> ${STAT_FILE}
echo "<PRE>" >> ${STAT_FILE}

~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "</PRE>" >> ${STAT_FILE}
echo "</TD></TR>" >> ${STAT_FILE}
echo "<TR><TD>" >> ${STAT_FILE}
echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<BR> ssh pi@raspb_01_cams <BR>" >> ${STAT_FILE}
echo "</TD></TR>" >> ${STAT_FILE}
echo "<TR><TD>" >> ${STAT_FILE}
echo "<PRE>" >> ${STAT_FILE}

ssh pi@raspb_01_cams ~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "</PRE>" >> ${STAT_FILE}
echo "</TD></TR>" >> ${STAT_FILE}
echo "</TABLE>" >> ${STAT_FILE}

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<P><FONT SIZE=-1> `date +'%x %X %Z'` </FONT>" >> ${STAT_FILE}
# sleep 35

exit
exit
exit
exit

# =============================================================================
# =============================================================================
#!/bin/bash

# Use in the Pi staging folder to delete older files.
#
# KEEP controls how many we keep, typically a mulitple of 3


STAT_FILE="/mnt/root/home/pi/Cumulus_MX/web/status.html"
STAT_FILE="/mnt/root/home/pi/Cumulus_MX/web/procs.html"

echo "<HEAD><TITLE>" > ${STAT_FILE}
echo "Raspberry Pi Expected Processes" >> ${STAT_FILE}
echo "</TITLE></HEAD><BODY BGCOLOR="#555555" TEXT="#FFFFFF" LINK="#FFFF00" VLINK="#FFBB00" ALINK="#FFAAFF"><H1 ALIGN=center>" >> ${STAT_FILE}
echo "Raspberry Pi Expected Processes" >> ${STAT_FILE}
echo "</H1>" >> ${STAT_FILE}
echo "" >> ${STAT_FILE}
echo "<CENTER>" >> ${STAT_FILE}

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<BR> Local on `hostname` <BR>" >> ${STAT_FILE}
echo "<PRE>" >> ${STAT_FILE}

~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "</PRE>" >> ${STAT_FILE}
echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<BR> ssh pi@raspb_01_cams <BR>" >> ${STAT_FILE}
echo "<PRE>" >> ${STAT_FILE}

ssh pi@raspb_01_cams ~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "</PRE>" >> ${STAT_FILE}

# sleep 35

exit
exit
exit
exit

# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================

#!/bin/bash

# Use in the Pi staging folder to delete older files.
#
# KEEP controls how many we keep, typically a mulitple of 3


STAT_FILE="/mnt/root/home/pi/Cumulus_MX/web/status.html"

echo "<P> &nbsp;"
# The range of AGE should be from 0 - 75 if everything is working.
# Let's hold up doing this until the status file has been updated
# fairly recently...
AGE=0
while [[ ${AGE} -lt 5 || ${AGE} -gt 135 ]]  ; do
	echo "<BR> DEBUG: NOW = `date +%s`"
	echo "<BR> DEBUG: Timestamp for ${STAT_FILE} = `date +%s -r ${STAT_FILE}`"
	ls -l --full-time ${STAT_FILE}
	AGE=$(expr `date +%s` - `date +%s -r ${STAT_FILE}`)
	echo "<BR> AGE = ${AGE}"
	sleep 1 
done

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<PRE>" >> ${STAT_FILE}
echo "<BR> Local on `hostname` <BR>" >> ${STAT_FILE}

~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<BR> ssh pi@raspb_01_cams <BR>" >> ${STAT_FILE}

ssh pi@raspb_01_cams ~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "</PRE>" >> ${STAT_FILE}

# sleep 35

exit
exit
exit
exit

# =============================================================================
# =============================================================================
# =============================================================================
# =============================================================================

#!/bin/bash

# Use in the Pi staging folder to delete older files.
#
# KEEP controls how many we keep, typically a mulitple of 3


STAT_FILE="/mnt/root/home/pi/Cumulus_MX/web/status.html"

echo "<P> &nbsp;"
# The range of AGE should be from 0 - 75 if everything is working.
# Let's hold up doing this until the status file has been updated
# fairly recently...
AGE=0
while [[ ${AGE} -lt 10000 || ${AGE} -gt -1 ]]  ; do
	echo "<BR> DEBUG: NOW = `date +%s`"
	echo "<BR> DEBUG: Timestamp for ${STAT_FILE} = `date +%s -r ${STAT_FILE}`"
	ls -l --full-time ${STAT_FILE}
	AGE=$(expr `date +%s` - `date +%s -r ${STAT_FILE}`)
	echo "<BR> AGE = ${AGE}"
	sleep 1 
done
exit

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<PRE>" >> ${STAT_FILE}
echo "<BR> Local on `hostname` <BR>" >> ${STAT_FILE}
~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}

echo "<P> &nbsp;" >> ${STAT_FILE}
echo "<BR> ssh pi@raspb_01_cams <BR>" >> ${STAT_FILE}
ssh pi@raspb_01_cams ~/bin/process_check.py ~/expected_procs.grep  >> ${STAT_FILE}
echo "</PRE>" >> ${STAT_FILE}

sleep 35

exit
exit
exit
exit

KEEP=12
#  One set of midnight files:
#       -rw-r--r-- 1 pi pi 37381560 Jul  9 00:02 arc-2018-07-08.tgz
#       -rw-r--r-- 1 pi pi 12864722 Jul  9 00:03 20180708.mp4
#       -rw-r--r-- 1 pi pi     4280 Jul  9 00:03 20180708-thumb.jpg
# >>>>  -rw-r--r-- 1 pi pi 12147344 Jul  9 00:05 20180708_daylight.mp4 <<<< Not making now
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
echo "1K Blocks recovered = `expr ${USED_BEFORE} '-' ${USED_AFTER}`"

exit

 1982  head yyyy
 1983  head yyy
 1984  history | grep messager
 1985  less yyy
 1986  rm yyy
 1987  git status
 1988  procs
 1989  ttttt
 1990  cd webcamwatcher/
 1991  git pull
 1992  git status
 1993  cd .ssh/
 1994  ls
 1995  vi authorized_keys 
 1996  grep 'Bobs-Laptop-rsa-key-20180511' ~/.ssh/authorized_keys 
 1997  procs
 1998  ~/bin/process_check.py ~/expected_procs.grep 
 1999  ssh pi@raspb_cams01 ~/bin/process_check.py ~/expected_procs.grep 
 2000  ssh pi@raspb_01_cams ~/bin/process_check.py ~/expected_procs.grep 
 2001  ttttt
 2002  find . -name status.html -ls
 2003  ls $PWD/Cumulus_MX/web/status.html
 2004  date +%s /mnt/root/home/pi/Cumulus_MX/web/status.html
 2005  date +%s -f /mnt/root/home/pi/Cumulus_MX/web/status.html
 2006  mand date
 2007  man date
 2008  date +%s -r /mnt/root/home/pi/Cumulus_MX/web/status.html
 2009  expr `date +%s -r /mnt/root/home/pi/Cumulus_MX/web/status.html` - `date +%s`
 2010* while true ; do expr `date +%s -r /mnt/root/home/pi/Cumulus_MX/web/status.html` - `date +%s` ; sleep 1 ; done"
 2011  cd webcamwatcher/
 2012  ls -al
 2013  cp -p rm_older_files.sh process_to_status.sh
 2014  history | tail -33 >> process_to_status.sh 