#!/usr/bin/python3 -u
# @@@ ...
# ----------------------------------------------------------------------------------------
#    NOTE:
#    NOTE:
#    NOTE:        grep 'convert returned data' webcamimager.log
#    NOTE:        ---------------------------------------------
#    NOTE:        ---------------------------------------------
#    NOTE:        ---------------------------------------------
#    NOTE:        ---------------------------------------------
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE: The monitoring / watchdogging should be moved to a separate process.
#    NOTE:     For example ... see other_systemctl
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE: At some point, remove push_to_server() and go with SCP.
#    NOTE:
#    NOTE: This assumes you can
#    NOTE:     ssh -p 21098 dillwjfq@server162.web-hosting.com
#    NOTE:              (without a password)
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:  When the network went out, this caused these script to keep restarting it.
#    NOTE:  Might consider handling it better.
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
#    NOTE:
# ----------------------------------------------------------------------------------------
#
# This script is started by 2 services - for for north- and south-facing cameras:
#	webcam_north.service
#	webcam_south.service
#
# Helpful aliases:
#	alias camstatus='sudo systemctl status webcam_north webcam_south'
#	alias ttttn='tail -fn100 /home/pi/N/webcamimager.log'
#	alias tttts='tail -fn100 /home/pi/S/webcamimager.log'
#	alias watchthecam='sudo nohup /home/pi/webcamwatch.py &'
#	alias wxprocs2='ps -ef | egrep "Cumulus|webcamwatch|DataStopped"'
#
# To see the startup log
#	sudo journalctl -u webcam_south
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
#  ..........................||  (26)
#  2018/11/04 03:38:48 INFO: Process /home/pi/N/North/snapshot-2018-11-04-04-38-41.jpg
#  .......................||  (23)
#  2018/11/04 03:40:49 INFO: Process /home/pi/N/North/snapshot-2018-11-04-04-40-41.jpg
#  ..
# NOTE: Not in Catch-up ....
#  2018/11/04 03:41:01 INFO: Catch-up mode on
#  2018/11/04 03:41:01 DEBUG: file 108 of 137 !!!!!! Skip processing snapshot-2018-11-04-03-40-56.jpg (in Catch-up)
#  .......................2018/11/04 03:43:01 DEBUG: file 110 of 138 !!!!!! Skip processing snapshot-2018-11-04-03-42-56.jpg (in Catch-up)
#  .......................2018/11/04 03:45:01 DEBUG: file 112 of 139 !!!!!! Skip processing snapshot-2018-11-04-03-44-56.jpg (in Catch-up)
#  ..................  (66)
# NOTE: Not down ....
#  2018/11/04 03:46:36 WARNING: Webcam might be down. More than 330 secs since last update
#  2018/11/04 03:46:36 WARNING: power-cycling webcam
#  2018/11/04 03:46:36 ...open relay contacts.
#  2018/11/04 03:46:41 ...close relay contacts.
#  ....2018/11/04 03:47:01 DEBUG: file 114 of 140 !!!!!! Skip processing snapshot-2018-11-04-03-46-56.jpg (in Catch-up)
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
# NOTE: It may be desirable to combine messager() and log_event().  The latter is almost
#       always accompanied by the former, as in the example below.  Generally, when the
#       string passed to messager() starts with "WARNING:" or "ERROR:" it is an event
#       we'd want to log.
#
# NOTE: If we send a message file to a remote node, it could be written to /tmp.
#       I think the OS deletes these periodically, or at least on reboot.
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# NOTE: Might consider leveraging a central message consolodator...
# messager( "WARNING:  CumulusMX reports data_stopped (<#DataStopped> == 1).   (code 101)" )
# log_event("", "CumulusMX reports data_stopped (<#DataStopped> == 1).", 101 )
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#    * NOTE: Should look more carefully of the use of subprocess
# ========================================================================================
#    * NOTE: When I started this up on the North camera on Pi 03 I had to tweak / create
#            / install a few things to get going...
#       sudo apt-get install proftpd      - - - - to allow webcam to upload....
#       sudo apt-get install ffmpeg       - - - - This is a fairly big package....
# XXXXX sudo apt-get install graphicsmagick-imagemagick-compat
#   OPTIONALLY for Astral ...  https://astral.readthedocs.io/en/stable/index.html
#       sudo apt-get install python-pip   - - - - Python package installer (2)
#	pip install astral
#
#
#       mkdir ~/N
#       mkdir ~/N/North
#       mkdir ~/N/North/arc_2018
#       mkdir ~/S
#       mkdir ~/S/South
#       mkdir ~/S/South/arc_2018
#
#       ln -s ~/webcamwatcher/webcamimager.py  ~/N
#       ln -s ~/webcamwatcher/webcamimager.py  ~/S
#       cp -p /home/pi/webcamwatcher/north.cfg ~/N
#       cp -p /home/pi/webcamwatcher/south.cfg ~/S
#		Edit ftp info in .cfg files.
#
#       printf "20180523214508\nsnapshot-2018-05-23-21-45-08.jpg\n" > ~/S/webcamimager__.dat
#       printf "20180523214508\nsnapshot-2018-05-23-21-45-08.jpg\n" > ~/N/webcamimager__.dat
#
# (2) See https://www.makeuseof.com/tag/install-pip-for-python/ - - pip not included in
#	Raspbian lite distros
#
# ----------------------------------------------------------------------------------------
#    * NOTE: Exception handling is weak / inconsistent.  Look at try - except blocks.
#  Refs:
#  https://docs.python.org/2.7/tutorial/errors.html
#  https://docs.python.org/2/library/exceptions.html
#  https://stackoverflow.com/questions/32613375/python-2-7-exception-handling-syntax
#    At the moment push_to_server() may be the best swag at it.  The connection to
#    the GoDaddy-hosted server can be flaky.  Examples:
#
# 2018/07/17 02:35:30 DEBUG: Copy /home/pi/N/North/snapshot-2018-07-17-02-35-37.jpg as N.jpg
# 2018/07/17 02:35:31 FTP Socket Error 113: No route to host
#
# ----------------------------------------------------------------------------------------
#
#   Images as jpg files are uploaded to a folder via ftp from the webcam.  Files
#   are name with date and time (local to the camera) in the form
#   yyyy-mm-dd-HH-MM-SS.  For example:
#
#        snapshot-2018-05-23-16-57-04.jpg
#        snapshot-2018-05-23-16-59-04.jpg
#        snapshot-2018-05-23-17-01-04.jpg
#
#   This script will poll for new files.
#   It can keep track of the last processed file using a stored timestamp from
#      the filename.
#   When a new file is detected, it is uploaded to the server.
#   When a day rollover is detected, the script will:
#      * Use ffmpeg to generate mp4
#      * tar up the days jpg files
#      * Create a web page to access video   <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< To be done
#      * Upload the mp4 file and web page to the server   <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< To be done
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
#   Considered using something to watch for directory changes.  Not sure it's
#   worth the complexity.  I think stat-ing the direcory is inexpensive while
#   polling.  Nevertheless, here are some references:
#
#   https://blog.philippklaus.de/2011/08/watching-directories-for-changes-using-python_-_an-overview
#   https://stackoverflow.com/questions/4708511/how-to-watch-a-directory-for-changes
#        https://github.com/seb-m/pyinotify
#   https://www.michaelcho.me/article/using-pythons-watchdog-to-monitor-changes-to-a-directory
#   http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
#   https://pypi.org/project/watchdog/0.5.4/
#   https://pypi.org/project/python-watcher/
#   https://pypi.org/project/watcher/
#   https://pypi.org/project/fs-watcher/
#   https://github.com/johnwesonga/directory-watcher/blob/master/dirwatcher.py
#   http://www.docmoto.com/support/advanced-topics/creating-a-folder-monitor-using-python/
#
# ========================================================================================
# ========================================================================================
#
#  EXTERNALIZING LOCAL SETTINGS:
#
#  exec()
#  https://docs.python.org/2.0/ref/exec.html
#
#  Best way to retrieve variable values from a text file - Python - Json
#  https://stackoverflow.com/questions/924700/best-way-to-retrieve-variable-values-from-a-text-file-python-json
#
#  https://en.wikipedia.org/wiki/YAML#Comparison_with_JSON
#  https://stackoverflow.com/questions/8525765/load-parameters-from-a-file-in-python
#  https://docs.python.org/2/library/json.html#module-json
#  https://docs.python.org/2/library/configparser.html
#
# ========================================================================================
# ========================================================================================
# ========================================================================================
# 20210223 Getting periodic seg faults from ffmpeg. Added globals:
#			vid_gen_attempt = -1
#			vid_date_string = ""
#          Added dot_interval to the cfg file as an option.  Default is 5 (sec).
# 20210220 Deprecated config variable cam_host.  relay_HOST is used instead which includes
#          the user, i.e. "pi@127.0.0.1"
# 20210202 Changed record_status.py so that if --bgcolor is used with a hex code, the
#          leading '#' should not be included.  I could not find a work-around for that
#          being treated like a comment by the shell.
# 20210114 Added def log_event() to work with statuscollector.py to consolodate a view
#          of what is happening across multiple scripts.
# 20201226 In using Pi Zero-based webcams, and pushing images through ssh and dd, we were
#          seeing a lot of issues around next_image_file() and check_stable_size(). A
#          number of changes were made to make it more tolerant and improve the logging a
#          bit. It to was hard to see what was going on and I don't see that there is
#          a definitive algoritm - e.g. there a bit of trial, error, and twiddling
#          required.
# 20201220 RAD Rewrote check_stable_size(). Either scp_dest has to be configure or
#              ftp_login does,  If ftp_login is "" SCP is used instead of FTP.
#              If mon_log is empty, log monitoring is bypassed. Similarly, if relay_GPIO
#              is a negative value, power-cycling is disabled.
# 20200207 RAD Looks like the video generation process takes on the order of 1 minute.
#              We could drive it from a date change on the snapshot being processed.
#						if last_day_code != day_code :
#              ... in next_image_file().
# 20200118 RAD Updated do_midnight() to handle the ftp config info. Wasn't needed
#              for scp, but that seemed to cause other issues. Also, there were
#              def read_FTP_config()s. Code was using the correct second definition!
# 20200115 RAD Realised the symbolic link in arc_2020 to /rm_older_files.sh was
#              missing when I went to run: alias cleanold='df -h . ; pushd ~/S/South/arc_...
#              Added a line to make the link when the new annual directory is made
#              in midnight_process().
# 20191112 RAD Added other_systemctl to the control file, and use it to restart the
#              other monitored process if required.
# 20190924 RAD Switched push_to_server_via_scp() calls (4) back to push_to_server().
#              It seems this may have been causing our IP hosted server address to
#              be locked / blocked to to bad credentials.  This was affecting multiple
#              users if I understood correctly.  Really curious how credential-less
#              scp can result in bad credentials - but I couldn't justify further
#              tinkering.  Need to update git...
# 20190907 RAD Oddly, scp seems to work most of the time, except after building the mp4
#              file.  It does work twice in midnight_process(), uploading both the
#              thumbnail and the mp4 (the largest file we upload).  It seems to fail
#              after a few additional calls to push_to_server_via_scp(). Added some
#              sleep time for grins, but it seems to have no effect.
# 20190907 RAD Looks like this script, or perhaps CumulusMX caused a locking up of
#              our virtual server IP address.  This error was logged at the time of failure:
#                ERROR: in push_to_server() FTP (connect): 530 Login authentication failed
#              Namecheap support was pretty adamant that it wasn't their issue. Logically
#              I find it difficult to understand how this script could be at fault,
#              since the credentials are read at startup and should never change while
#              running ... unless something very surgical wacked some memory. I did
#              comment out or remove these three from some "global" statements:
#                      ftp_server, ftp_login, ftp_password
#              They should only be allowed to be set by read_FTP_config(). I also
#              log the FTP credentials in push_to_server() if the connect fails and
#              and "authentication" is found in the error message.
# 20190625 RAD Same issue, processes "running" but apparently hung.  So camera_down()
#              may not be very useful here ... at least for this failure mode. A separate
#              watchdog may be required.  As noted below process_new_image() is likely
#              where the hang occurs because immediate afterward the '.' for the next
#              wait cycle is printed - and I'm not seeing it in the log.
#              We are seeing the "INFO: Process ..." message logged.
#              .
#              If I had to guess, I suspect maybe its hanging in push_to_server()
#              so I added a couple debug statements to see what I could learn.
#              NOTE: We store a generic-named image and a thumbnail.
#
# 20190615 RAD The process for the South camera seem to have stopped doing anything but
#              but was apparently still running.  Seems strange.  Seems systemctl didn't
#              detect an issue. Offhand, seems another watchdog might be required.
#              Calls to push_to_test() commented out.  May have hung in process_new_image()
#
#       ----------------------------------------------------------------------------------
#   From the journal  (sudo journalctl -u webcam_south)
#	2019/06/14 07:53:25 WARNING: power-cycling webcam
#	2019/06/14 07:53:25 ssh pi@192.168.1.10 /home/pi/webcamwatcher/power_cycle.py 23
#	2019/06/14 07:53:31 0
#	2019/06/14 07:53:31 2019/06/14 07:53:26 ...open relay contacts on BCM pin 23
#	2019/06/14 07:53:31 ...close relay contacts on BCM pin 23
#	2019/06/15 10:33:01 INFO: Starting /home/pi/S/webcamimager.py   PID=30328
#       ----------------------------------------------------------------------------------
#   From the webcamimager.log
#	..................................................................  (66)
#	2019/06/14 07:53:25 WARNING: Webcam might be down. More than 330 secs since last update
#	2019/06/14 07:53:25 WARNING: power-cycling webcam
#	2019/06/14 07:53:25 ssh pi@192.168.1.10 /home/pi/webcamwatcher/power_cycle.py 23
#	2019/06/14 07:53:31 0
#	2019/06/14 07:53:31 2019/06/14 07:53:26 ...open relay contacts on BCM pin 23
#	2019/06/14 07:53:31 ...close relay contacts on BCM pin 23
#	.......||  (73)
#	2019/06/14 07:54:10 DEBUG: Server image age = 271
#	2019/06/14 07:54:10 INFO: Process /home/pi/S/South/snapshot-2019-06-14-07-54-04.jpg
#	.......................||  (23)
#   ... Log continues for another hour, and it appears images were being uploaded.
#	.......................||  (23)
#	2019/06/14 18:50:19 DEBUG: Server image age = 119
#	2019/06/14 18:50:19 INFO: Process /home/pi/S/South/snapshot-2019-06-14-18-50-13.jpg
#   >>> Gap in the log here; just seemed to stop without any messaging or journal entry...
#   >>>   and no attempt to restart that I could see, but then both processes appeared to
#   >>>   be running.  The South one just wasn't doing anything.
#   >>>		$ procs
#   >>>		Found "pi   842 1  0 Jun01 ? 00:13:59 /usr/bin/python -u ./webcamimager.py /home/pi/N/north.cfg"
#   >>>		Found "pi   843 1  0 Jun01 ? 00:13:52 /usr/bin/python -u ./webcamimager.py /home/pi/S/south.cfg"
#	2019/06/15 10:33:01 INFO: Starting /home/pi/S/webcamimager.py   PID=30328
#	2019/06/15 10:33:01 INFO: reading "/home/pi/S/south.cfg"
#       ----------------------------------------------------------------------------------
#
#
#
# 20190831 RAD Added check_log_age(). This is imcomplete as it only logs (multiple times)
#              that the monitored log of the other instance of this script appears
#              to be stalled. I can not figure out why it stalls, but this routine
#              could eventually restart the other instance.
# 20190601 RAD Deleted everything from GoDaddy; push_to_test() started failing.
# 20190526 RAD Switching over to Namecheap hosting, and using dilly.family as primary.
#              Took out stuff no longer used.
# 20190414 RAD Occasionally see "ValueError: invalid literal for int() with base 10: ''"
#              when urlopen( image_age_URL ) returns a null.  Handle that case explicitly
#              by setting age to 0.
# 20181229 RAD Now using ssh to power-cycle the web camera. This requires that
#              /home/pi/webcamwatcher/power_cycle.py be available. The webcan could
#              be remote, in which case relay_HOST is set to the IP of the system,
#              or if local the loopback address is used; 127.0.0.1.
#
#     Hacked this change back in .... 20181011 https://github.com/radilly/webcamwatcher/commit/02d2380ec09d1a054934fe8021de508c4ef4d62c#diff-d63b4d59d8d25f5618cb001bf3613c1a
# 20181005 RAD Had a blip in Internet connectivity which cause this script to restart
#              by exiting after FTP failed to connect.  This might be a good thing if
#              the FTP issue is something local to the host, but the retry loop was
#              never really getting executed. I changed the routine a lot, but for
#              reference, I copied push_to_server() to push_to_server_OLD() and
#              inadvertently committed it in c284c8f9b79bebc537e23cf2e0567c51a4eafb31.
#
# 20180919 RAD Looking over the log I noticed a brief catchup - for 1 image.  This
#              followed a delay from check_stable_size(). See "log fragment 2" below.
#              I changed the threshold for setting "catching_up = True" from 1 to 2
#              even though I can't quite see why.  I expected this mode would only
#              fire when the script was starting up.
# 20180914 RAD Had a case where the catching_up scheme wasn't working correctly. This
#              script was several images behind and wasn't catching up.  Rewrote
#              next_image_file().
# 20180728 RAD Occurred to me we aren't really doing anything with the 24-hour mp4s.
#              The daylight version is far more interesting.  Changed midnight_process()
#              to skip building the 24-hour image.
# 20180723 RAD Changed wait from 1 to 2 secs in check_stable_size().  Got a failure,
#              "convert convert: Corrupt JPEG data: premature end of data segment."
#              Made the daylight mp4 generation conditional - 24-hour must build first.
# 20180717 RAD Looked like push_to_server() didn't make multiple tries to connect to the
#              hosted webserver.  Failed with "No route to host" and the systemd service
#              stopped.  I wonder if "except socket.error" was too specific, so I now
#              trap all.
# 20180714 RAD Added global dot_counter to count dots added to the log while we're
#              polling for a directory change.  This is where we need to be aware
#              that an image is overdue.
# 20180714 RAD Added read_config() which reads a config file and sets some global
#              variables.  Instead of 4 parameters, we now have just one - the name
#              of the config file. Logging and messaging now uses local time (not
#              UTC). Added camera_down() but it isn't called yet.  Needs to get called
#              when we're logging dots .......
# 20180713 RAD Added some messaging for systemctl.  Changed the name of tar (.tgz) files
#              to start with the YYYYMMDD date like all the other midnight files.
# 20180711 RAD Modified next_image_file() to bypass much of the processing of each snapshot
#              when catching_up == True.  We DO want to handle the midnight rollover.
#              We could, but don't, push images to the webserver every X images...
# 20180710 RAD Cleaned up push_to_test() and moved the routine and the call to it into
#              the live code.  The call to it is commented out.  Also, if you use it,
#              you'll need to set up FTP server, id and password in the def.
# 20180707 RAD Wrote remove_night_images() based on daylight_image_list().  The name
#              change reflects the new function.  Called from midnight_process().
#              Could move a chunk of this around remove_night_images() to a separate
#              subroutine.
# 20180702 RAD Made a stab at uploading mp4 files to the web server.  Could be broken
#              to year folders ... like arc_2018 ... but it may not be an issue...
# 20180702 RAD General cleanup...
# 20180626 RAD Getting to run this as a service.  Changed all active calls from messager()
#              to logger(). Some work on parameter parsing.
# 20180626 RAD Again convert failed to create the thumbnail from an incomplete jpg. It
#              was sleeping for 0.5 secs, but I changed to a full sec, in case the
#              the incoming FTP is "bursty."
# 20180614 RAD Ran into convert trying to create the thumbnail from an incomplete jpg.
#              Added check_stable_size() to handle this rather than a simple stat().
#              Since it is delivered asynchronously, more caution is needed.
# 20180611 RAD As luck would have it, I left a trailing blank on the tar_file name,
#              which caused the isfile() to fail last night.  The retry shut down the
#              midnight process, which is tedious, so maybe I can find a better approach.
# 20180610 RAD Ugly bug with the midnight_process(), or the call to it.  It was getting
#              last_filename passed to it, but this was only set in the first iteration
#              when is is read from a file.
# 20180604 RAD More cleanup.  Seems to be running well in my testing.  Removed a lot
#              of dead code left from watchdog.py.
# 20180603 RAD Cleaned up a bunch of stuff.
# 20180531 RAD Added gloabl catching_up, which detects when the list of files to
#              process exceeds a certain threshold (3 at this point), and reduces
#              the sleep duration during that condition.
# ========================================================================================

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#  https://docs.python.org/2/library/subprocess.html
#  https://pypi.org/project/subprocess32/
#  http://www.pythonforbeginners.com/os/subprocess-for-system-administrators
#  https://pythonspot.com/python-subprocess/
#  http://stackabuse.com/pythons-os-and-subprocess-popen-commands/
#  https://stackoverflow.com/questions/40222793/python-subprocess-check-output-stderr-usage
#
#  Both of these are used, but probabably not very well
#      subprocess.check_call()
#      subprocess.check_output()
#
#  This seemed to do what I usually want.  The shell=True clause is not used, but ...?
#      convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT )
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import subprocess
# check_output
# check_call

# Casing changed from 2 to 3.  Was camel-cased.
import configparser

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
import datetime
from time import sleep
import time
import sys
from os import listdir, getpid, stat, unlink
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#  In this code I use os.path.isfile() in a few places.  Actually os.path.exists() might
#  be a better choice for the way I use it, however may be affected by permissions. I was
#  trying to figure out if there is a better, more specific way to import this, but did
#  not find a definitive answer.
#
#   https://docs.python.org/2/library/os.path.html
#   https://docs.python.org/2/tutorial/modules.html#packages
#   http://thomas-cokelaer.info/tutorials/python/module_os.html
#   http://effbot.org/librarybook/os-path.htm
#   https://stackoverflow.com/questions/2724348/should-i-use-import-os-path-or-import-os
#
# from os.path import isfile
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
import os
from ftplib import FTP
from urllib.request import urlopen
# from urllib.error import URLError, HTTPError
# https://docs.python.org/3/library/urllib.error.html
# https://docs.python.org/3/library/exceptions.html#OSError
from urllib.error import URLError, HTTPError
import shutil
import re

import socket
import calendar
import traceback

mon_log = ""
mon_max_age = 300

relay_GPIO = -1
relay2_GPIO = -1
cam_timeout = 99999
vid_gen_minute = 0

work_dir = ""
main_image = ""
thumbnail_image = ""
remote_dir = ""
image_age_URL = ""

other_systemctl = ""
status_HOST = ""

this_script = sys.argv[0]
script_ts = stat( this_script ).st_mtime
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( os.getcwd(), re.sub('^\./', '', this_script) )

image_data_file = re.sub('\.py', '__.dat', this_script)
logger_file = re.sub('\.py', '.log', this_script)


# Real mtime will always be larger
last_image_dir_mtime = 0.0

USE_SCP = True

ftp_login = ""
ftp_password = ""
ftp_server = ""

current_filename = ""

last_mtime = 0.0

last_filename = ""
last_day_code = -1
catching_up = False
vid_gen_attempt = -1
vid_date_string = ""
dot_counter = 0
small_counter = 0
dot_interval = 5
common_log = ""

# strftime_GMT = "%Y/%m/%d %H:%M:%S GMT"
# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"
time_only_FMT = "%H:%M:%S"
WEB_URL = "http://dilly.family/wx"
# cam_host = "127.0.0.1" # @@@ Deprecated

cfg_parameters = [
	"status_HOST",
	"work_dir",
	"main_image",
	"thumbnail_image",
	"remote_dir",
	"image_age_URL",
	"dot_interval",
	"common_log",
	"relay_GPIO",
	"relay2_GPIO",
	"cam_timeout",
	"vid_gen_minute",
	"relay_HOST",
	"mon_log",
	"mon_max_age",
	"other_systemctl",
	]


next_image_count = 999

# ========================================================================================
# ----------------------------------------------------------------------------------------
#
# Main loop
#
# ----------------------------------------------------------------------------------------
# ========================================================================================
def main():

	if len(sys.argv) >= 2 :
		config_file = sys.argv[1]
	else :
		log_and_message( "ERROR: cfg file is a required first argument." )
		exit()

	log_and_message( "INFO: script_ts = \"{}\"".format(script_ts) )
	if not os.path.isfile( config_file ) :
		log_and_message( "ERROR: cfg file \"{}\" not found.".format( config_file ) )
		exit()

	log_and_message( "INFO: reading \"{}\"".format( config_file ) )

	read_FTP_config( config_file )

	log_and_message( "INFO: USE_SCP = \"{}\"".format(USE_SCP) )
	if not USE_SCP :
		log_and_message( "INFO: ftp_login = \"{}\"".format(ftp_login) )
		log_and_message( "INFO: ftp_server = \"{}\"".format(ftp_server) )
		log_and_message( "INFO: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  ftp_password = \"{}\"".format(ftp_password) )

	read_config( config_file )

	log_and_message( "INFO: scp_dest = \"{}\"".format(scp_dest) )
	log_and_message( "INFO: work_dir = \"{}\"".format(work_dir) )
	log_and_message( "INFO: main_image = \"{}\"".format(main_image) )
	log_and_message( "INFO: thumbnail_image = \"{}\"".format(thumbnail_image) )
	log_and_message( "INFO: remote_dir = \"{}\"".format(remote_dir) )
	log_and_message( "INFO: image_age_URL = \"{}\"".format( image_age_URL ) )
	log_and_message( "INFO: dot_interval= \"{}\"".format( dot_interval ) )
	log_and_message( "INFO: common_log = \"{}\"".format( common_log ) )
# @@@ Deprecated	log_and_message( "INFO: cam_host = \"{}\"".format( cam_host ) )
	log_and_message( "INFO: relay_HOST = \"{}\"".format( relay_HOST ) )
	log_and_message( "INFO: relay_GPIO = \"{}\"".format( relay_GPIO ) )
	log_and_message( "INFO: relay2_GPIO = \"{}\"".format( relay2_GPIO ) )
	log_and_message( "INFO: cam_timeout = \"{}\"".format( cam_timeout ) )
	log_and_message( "INFO: vid_gen_minute = \"{}\"".format( vid_gen_minute ) )
	log_and_message( "INFO: mon_log = \"{}\"".format( mon_log ) )
	log_and_message( "INFO: mon_max_age = \"{}\"".format( mon_max_age ) )
	log_and_message( "INFO: other_systemctl = \"{}\"".format( other_systemctl ) )
	log_and_message( "INFO: status_HOST = \"{}\"".format( status_HOST ) )
	log_and_message( "" )

###	nvers = mono_version()
###	log_and_message("INFO: Mono version: {}" .format( nvers ) )

	python_version = "v " + str(sys.version)
	python_version = re.sub(r'\n', r', ', python_version )
	log_and_message( "INFO: Python version: {}".format( python_version ) )
	log_and_message( "" )

	while True:
		next_image_file()
		check_log_age( )
		sleep(dot_interval)

	exit()







# ----------------------------------------------------------------------------------------
# Handle a new snapshot image:
#  * Make an copy with a generic name
#  * Make a thumbnail version
#  * Upload both to the web server
#
#  Globals referenced: remote_dir, work_dir, thumbnail_image
# ----------------------------------------------------------------------------------------
def process_new_image( source, target) :

	source_file = "{}/{}".format( work_dir, source )
	jpg_size = stat( source_file ).st_size
	jpg_ts = stat( source_file ).st_mtime

	logger( "INFO: Process {} {:8d} B  {:10.1f}".format(source, jpg_size, jpg_ts) )
#	logger( "INFO: Process {} - {:7.1f} KB".format(source_file,jpg_size/1024) )
#DEBUG#	logger( "DEBUG: Called process_new_image(\n\t {},\n\t {} )".format(source_file, target) )
	msg = "INFO: Process {} {:8d} B  {:10.1f}".format(source, jpg_size, jpg_ts)
#	log_event(msg, 999, "")

	try :
		camera_down()     # TESTING
	except :
		logger( "ERROR: In process_new_image() camera_down() failed." )


	shutil.copy2( source_file, target )
	push_to_server( target, remote_dir )

	thumbnail_file = work_dir + '/' + thumbnail_image
#DEBUG#	logger( "DEBUG: Create thumbnail {} and upload to {}".format(thumbnail_file, remote_dir ) )
	convert = ""
	convert_cmd = ['/usr/bin/convert',
			target,
			'-resize', '30%',
			thumbnail_file ]
	try :
		convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
	except:
		logger( "ERROR: Unexpected ERROR in convert: {}".format( sys.exc_info()[0] ) )
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Generally nothing, unless -verbose is used...
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if len(convert) > 0 :
		logger( "WARNING: convert returned data: \"{}\"".format( convert ) )
		logger( "WARNING: Thumbnail image \"{}\" suspect.".format( thumbnail_file ) )
#	else :
#		logger( "DEBUG: convert returned data: \"{}\"".format( convert ) )

	push_to_server( thumbnail_file, remote_dir )

	logger_common( "INFO: Processed {}".format(source_file) )

#DEBUG#	logger( "DEBUG: done" )




# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#  Find the next "unprocessed" image file ... if any
#
#  Note: Would do well to break this up a little.
#
# ----------------------------------------------------------------------------------------
#  NOTE: One thing not addressed, which is a little complicated, is how to handle DST.
#  In the fall the range of 2:00 - 3:00 AM is repeated so that could mess up the
#  image sequence (when building the video).  It could be that images may be
#  over-written.
# ----------------------------------------------------------------------------------------
#  NOTE: On startup, this reprocesses the last file processed.  That was unintended but
#  I decided it was not harmful.  As a result you always see "||  (0)" in the log.
# ----------------------------------------------------------------------------------------
#
#  * If we're in catch-up mode keep at it until we get to the last file....
#	Possibly "process" every 10th file so that the web server sees activity???
#
#  * If we've missed 2 images (4 minutes), power-cycle the camera.
#
#  ??????? If we're not in catch-up mode, start watching the folder for a change.
#
#  * If the timestamp on the work folder has not changed, print a '.' and return.
#
#  * Loop through all the files.
#		We were using the timestamp embedded on the filename, but DST could
#		cause an issue.  Using the filetime should be more general, i.e. stat()
#	* Skip any files older than the last...
#
#  * Loop through all the files.
#
#  * Loop through all the files.
#
# ----------------------------------------------------------------------------------------
def next_image_file() :
	global work_dir, last_mtime, last_filename, last_image_dir_mtime
	global catching_up, current_filename, dot_counter, small_counter
	global last_day_code
	global next_image_count
	global vid_gen_attempt, vid_date_string

	date_rollover = False

#DEBUG#	logger( "DEBUG: in next_image_file()   last_mtime = {}".format( last_mtime ) )
#TEST#	sleep( 0.5 )
	# Should only ever happen at startup...
	if last_mtime == 0.0 :
		last_mtime = float(get_stored_ts())
		last_filename = get_stored_filename()
		last_day_code = int( re.sub(r'snapshot-....-..-(..).*', r'\1', last_filename) )
		# ------------------------------------------------------------------------
		#  The logic as of this writing (06/15/19) causes this last-processed
		#  file to be reprocessed at startup.  Not terrible, but could be
		#  cleaned up at some point...      possible TODO
		# ------------------------------------------------------------------------




	# --------------------------------------------------------------------------------
	#  This product of ( dot_counter * sleep_for ) is a rough estimate of the time
	#  since the last webcam update (and the work folder was modified).  At 2 minute
	#  image updates, this should be around 120 secs, but here allow for a missing
	#  image.  (Most often we count 22 dots per image upload.)
	# --------------------------------------------------------------------------------
	elapsed = ( dot_counter * dot_interval )
	if elapsed > cam_timeout :
		if 0 == ( dot_counter % 22 ) :
			log_string( "  ({})\n".format( dot_counter ) )
			logger( "WARNING: Webcam might be down. More than {} secs since last update".format( elapsed ) )
			log_and_message( "WARNING: power-cycling webcam" )
			power_cycle( )


	# --------------------------------------------------------------------------------
	#  Check the modification time on the image directory.
	#  If it hasn't changed since our last check, just return() now.
	# --------------------------------------------------------------------------------
	image_dir_mtime = stat( work_dir ).st_mtime
#DEBUG#	logger( "DEBUG: image_dir_mtime {} == last_image_dir_mtime {} ?".format( image_dir_mtime, last_image_dir_mtime ) )
	if image_dir_mtime == last_image_dir_mtime :
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Progress indicator
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if ( dot_counter % 5 ) > 0 :
			log_string( '.' )
		else :
			log_string( ':' )
		dot_counter += 1
		return


#DEBUG#	log_string( "\n DEBUG:\n" )


	last_image_dir_mtime = image_dir_mtime

	date_string = re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename)

	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)

###	print "DEBUG: date_string = " + date_string
###	print "DEBUG: date_stamp = " + date_stamp
###	print "DEBUG: last processed day code = " + last_day_code

	# --------------------------------------------------------------------------------
	#  Find the oldest 'unprocessed' file(s) in the work directory- the directory
	#  which the remote system is writing (image) files into.  The file names came
	#  from the original cameras which incorporated a timestamp.  For example:
	#	snapshot-2020-12-26-14-30-01.jpg
	#	snapshot-yyyy-mm-dd-hh-hh-ss.jpg
	#  So the names will sort into the order in which they were written, and the
	#  order in which we want to process them.
	#
	#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
	#  First pass: look through all files and remove any not starting with "snapshot-".
	#     This should run pretty quickly...
	# --------------------------------------------------------------------------------
	file_list = listdir( work_dir )
	file_list.sort()

	line = 0
	while line < len( file_list ) :
		if "snapshot-" not in file_list[line] :
			file_list.pop(line)
		else :
			line += 1

#DEBUG#			if line == 1 :
#DEBUG#				logger( "DEBUG: ts for {} = {:10.1f}".format( file_list[line-1], stat( work_dir + '/' + file_list[line-1] ).st_mtime ) )




	# --------------------------------------------------------------------------------
	#  Now file_list should contain all the "snapshot" files in this folder, which
	#  could easily be 700 files or more.
	#  .
	#  .
	#  .
	#
	# --------------------------------------------------------------------------------
	file_list_len = len( file_list )
#DEBUG#	logger( "DEBUG: file_list_len = {}".format( file_list_len ) )
	line = 0

	while line < file_list_len :
#DEBUG#		logger( "DEBUG: file {} of {} - - -  {}".format( line+1, file_list_len, file_list[line] ) )

		this_file = file_list[line]
		# file names are 'bare" - no path, which we may need.
		source_file = "{}/{}".format( work_dir, this_file )
		source_mtime = stat( source_file ).st_mtime

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Skip already processed files.
		#   Technically files older than (or as old as) the one last processed.
		# If that's the case, got to the next one.
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#DEBUG#		logger( "DEBUG: current {}  last {} - - -  {}".format( source_mtime, last_mtime, source_mtime <= last_mtime ) )
		if source_mtime <= last_mtime :
#DEBUG#			logger( "DEBUG: file {} of {}, {} should have already been processed.".format( line+1, file_list_len, this_file ) )
			line += 1
			continue

		target_file = "{}/{}".format( work_dir, main_image )
		date_string = re.sub(r'snapshot-(....-..-..).*', r'\1', this_file )


# @@@		log_string( "\n DEBUG:" )
# @@@		logger( "DEBUG: {:8.1f} - {:8.1f} = {:4.1f} for file {}".format( source_mtime, last_mtime, source_mtime-last_mtime, this_file ) )

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Don't process the same file - This should be rare as source_mtime is
		# now re-read after check_stable_size() which can allow the file to
		# "age" a little more than when we read the st_mtime above.
		#
		# 2021/03/27
		# This clause caused a runaway loop and created a 20G+ lg file.
		# The incrementing of line was added.
		# That allowed the script to drop into "INFO: Catch-up mode on".
		#
		#   dot_counter  = 0 delta = 12.049928188323975
		#   dot_counter  = 0 ds = "2021-03-27"
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if last_filename == this_file :
			delta = source_mtime - last_mtime  # DEBUG:
			log_string( "\n" )
			logger( "DEBUG-WARNING: Reprocessing {} last?????   dot_counter  = {} delta = {}".format( last_filename, dot_counter, delta ) )
			logger( "DEBUG-WARNING: Reprocessing {} this?????   dot_counter  = {} ds = \"{}\"".format( this_file, dot_counter, date_string ) )
			line += 1
			continue

			#  ...........................||  (27)  11:15:11
			#  2021/03/27 11:15:11 INFO: Process snapshot-2021-03-27-11-15-01.jpg    32768 B  1616858107.9
			#  [@1][@1a][@5][@6] 11:15:12
			#  NOTE:
			#  NOTE:
			#  NOTE:
			#  NOTE:
			#  NOTE:
			#  NOTE:
			#  NOTE:
			#  NOTE:
			#  2021/03/27 11:15:14 WARNING: convert returned data: "convert convert: Premature end of JPEG file (/mnt/ssd/TEST/Test/T.jpg).
			#  "
			#  2021/03/27 11:15:16 waiting
			#  .......................
			#  2021/03/27 11:16:03 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg last?????   dot_counter  = 23 delta = 12.049928188323975
			#  2021/03/27 11:16:03 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg this?????   dot_counter  = 23 ds = "2021-03-27"


###### NOTE: Could check
###### date +%Z
		if not catching_up and ( (file_list_len - line) > 2 ) :
			catching_up = True
			log_string( "\n" )
			logger( "INFO: Catch-up mode on" )

		if catching_up and (file_list_len - line) < 2 :
			catching_up = False
			log_string( "\n" )
			logger( "INFO: Catch-up mode off" )

		# snapshot-2018-05-23-16-57-04.jpg
		tok = re.split('-', re.sub('\.jpg', '', this_file ) )
		day_code = int(tok[3])
		mm_code = int(tok[5])
		if last_day_code != day_code :
			date_rollover = True
			vid_gen_attempt = 0
			vid_date_string = re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename)
		else :
			date_rollover = False

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# May happen when webcam power-cycles, but NTP hasn't synched yet...
		# -rw-r--r-- 1 pi pi 44070 Jul 11 06:19 N/North/snapshot-1969-12-31-19-02-00.jpg
		# Because of the timezone, this is before the start of the Unix epoch!!!
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if int(tok[1]) < 2000 :
			log_string( "||  ({})  {}\n".format( dot_counter, timestamp() ) )
			next_image_count += 1
			if next_image_count >= 12 :
				logger( "INFO: Monitoring \"{}\"".format(work_dir) )
				next_image_count = 0
			dot_counter = 0
			old_file = this_file
			logger( "WARNING: Probably webcam recently rebooted: old file! {}".format( old_file ) )
			unlink( "{}/{}".format(work_dir, old_file ) )

		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# If not in catching up mode wait for size to "stablize", if not it was
		# written a while ago and no waiting is needed.  Because the file is
		# being written by a remote process, network load can affect timing.
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if not catching_up :
			# this takes 4 seconds.
			jpg_size = check_stable_size( source_file )
		else :
			jpg_size = stat( source_file ).st_size

#DEBUG#		logger( "DEBUG: jpg_size = {}".format( jpg_size ) )

		if jpg_size < 500 :
			log_string( "    ({})\n".format( dot_counter ) )
			logger( "WARNING: Skipping image file {} size = {}".format( source_file, jpg_size ) )
			dot_counter = 0
			small_counter += 1
			# Don't power-cycle unless we've seen a few of these in a row...
			if 0 == ( small_counter % 4 ) :
				power_cycle( )

			unlink( "{}/{}".format(work_dir, this_file ) )
			store_file_data ( source_mtime, this_file )
			last_mtime = source_mtime

			line += 1
			continue
		else :
			small_counter = 0
			# ----------------------------------------------------------------



		# ------------------------------------------------------------------------
		#  Exception cases handled.  Process the file.  (If not catching_up.)
		#
		# ------------------------------------------------------------------------
		if catching_up :
			logger( "DEBUG: file {:5d} of {:5d} !!!!!! Skip processing {} (in Catch-up)".format( line+1, file_list_len, this_file ) )

		else :
			log_string( "||  ({})  {}\n".format( dot_counter, timestamp() ) )
			next_image_count += 1
			if next_image_count >= 12 :
				logger( "INFO: Monitoring \"{}\"".format(work_dir) )
				next_image_count = 0

			process_new_image( this_file, target_file )
			# First '.' right after processing is done...

			if not date_rollover :
				logger( "waiting" )
				log_string( ':' )
				dot_counter = 1



		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# We only know that we have to run the midnight proecess when we get the
		# first image of a new day - i.e. that date number has changed.  The
		# last (previous) image filename contains yesterday's date string.
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if mm_code > vid_gen_minute  and  vid_gen_attempt > -1 :
			logger( "DEBUG: past (mm_code) image-minute {})".format( mm_code ) )
			vid_gen_attempt = -1
			vid_date_string = ""

#DEBUG#		logger( "DEBUG: last_day_code = {}   day_code = {}".format( day_code, last_day_code ) )
		if date_rollover :
			log_string( "\n" )
			logger( "INFO: MIDNIGHT ROLLOVER!\n" )
			midnight_process(re.sub(r'snapshot-(....-..-..).*', r'\1', last_filename))

			vid_date_string = ""

			log_string( ':' )
			dot_counter = 1


		source_mtime = stat( source_file ).st_mtime
		store_file_data ( source_mtime, this_file )
		last_day_code = day_code
		last_mtime = source_mtime
		last_filename = this_file

#DEBUG#		logger( "DEBUG: NEXT!" )

		# ------------------------------------------------------------------------
		#  Increment loop index
		# ------------------------------------------------------------------------
		line += 1

	# ----------------------------------------------------------------------------------------
	# ----------------------------------------------------------------------------------------
	# Here were are past the last file
	# ----------------------------------------------------------------------------------------
	# ----------------------------------------------------------------------------------------





# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
# NOTE: This should restart the "other" instance of this script.
#
# Checks the age of the monitored log.  If its not been updated recently (relative
# to mon_max_age) then we have a problem with the process appending to the log.
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def check_log_age( ) :
	global mon_log, mon_max_age

	if len(mon_log) < 2 :
		return


# @@@ here
	mtime = stat( mon_log ).st_mtime
	now = time.time()
#	print mtime
#	print time.time()
	age = now - mtime
#	print "DEBUG: age = {:10.2f}".format( age )

	if age > mon_max_age and len( other_systemctl ) > 0 :
		log_string( "\n" )
		log_and_message( "ERROR: \"{}\"  has not been updated for {:1.2f} seconds.".format( mon_log, age ) )
		log_and_message( "ERROR: \"{}\"  has not been updated for {:1.2f} seconds.".format( mon_log, age ) )
#		log_and_message( "ERROR: \"{}\"  has not been updated for {:1.2f} seconds.".format( mon_log, age ) )


		restart_cmd = [ "/usr/bin/sudo",
				"/bin/systemctl",
				"restart",
				other_systemctl,
				]

		try:
			reply = subprocess.check_output( restart_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
			logger( "DEBUG: Result from {}: Returned = {:7.1f} bytes.".format( restart_cmd, len(reply) ) )
		except Exception as problem :
			log_and_message( "ERROR: Unexpected ERROR in {}: {}".format( restart_cmd, sys.exc_info()[0] ) )
			log_and_message( "ERROR: systemctl restart: {}".format( problem ) )

	return






# ----------------------------------------------------------------------------------------
# Read the config file, and set global variables based on it.
#
# NOTE: While the flexibility to override any global may have some benefits, it's not
#	clear this shouldn't be limited to specific variables.  We do some verification
#	of the values, and in fact some of these are required or we fail to run.
#
#	See cfg_parameters array for checking.
# ----------------------------------------------------------------------------------------
def read_config( config_file ) :
	global work_dir, main_image, thumbnail_image, remote_dir
# @@@ Deprecated	global cam_host
	global relay_HOST, cam_timeout, vid_gen_minute
	global relay_GPIO, relay2_GPIO, webcam_ON, webcam_OFF
	global mon_log, mon_max_age
	global other_systemctl
	global dot_interval

# 	# https://docs.python.org/2/library/configparser.html
	config = configparser.RawConfigParser()
	# This was necessary to avoid folding variable names to all lowercase.
	# https://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
	config.optionxform = str
	config.read( config_file )
	#print config.getboolean('Settings','bla') # Manual Way to acess them

	# https://stackoverflow.com/questions/924700/best-way-to-retrieve-variable-values-from-a-text-file-python-json
	parameter=dict(config.items("webcamimager"))
	for p in parameter:
		parameter[p]=parameter[p].split("#",1)[0].strip() # To get rid of inline comments
###		messager( "DEBUG: p = {}".format( p ) )
###		messager( "DEBUG: parameter[p] = {}".format( parameter[p] ) )

	globals().update(parameter)  #Make them availible globally





	if not os.path.exists( work_dir ) :
		log_and_message( "ERROR: work_dir, \"{}\" not found.".format( work_dir ) )
		exit()

	if not re.match('.+\.jpg$', main_image, flags=re.I) :
		log_and_message( "ERROR: main_image, \"{}\" not ending in .jpg.".format( main_image ) )
		exit()

	if not re.match('.+\.jpg$', thumbnail_image, flags=re.I) :
		log_and_message( "ERROR: thumbnail_image, \"{}\" not ending in .jpg.".format( main_image ) )
		exit()

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Check the FTP credentials we read.
	#
	#  See push_to_server() which tries this in a loop... To handle GoDaddy outages.
	#
	#  NOTE:  See also similar code in def check_FTP_config()
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if not USE_SCP :
		ftp_OK = False

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#    2019/12/20 09:38:15 ERROR: Unexpected ERROR in FTP connect: <class 'socket.error'>
	#    2019/12/20 09:38:15 ERROR: FTP (connect): [Errno 110] Connection timed out
	#    2019/12/20 09:38:15 ERROR: Quitting due to FTP error(s) above.  Exiting in 30 seconds ...
	#    2019/12/20 09:38:45   Good bye from /home/pi/N/webcamimager.py
	# --------------------------------------------------------------------------------
		for iii in range(8) :
		# Not on first iteration.  Then increase the sleep time with each iteration.
		#  With a 4 sec multiplier this comes to 112 seconds max...     (28 * 4)
			if iii > 0 :
				logger( "DEBUG: in read_config() checking credentials sleep( {} )".format( iii * 15 ) )
				sleep( iii * 15 )

			try :
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
				ftp = FTP( ftp_server, ftp_login, ftp_password )
				ftp_OK = True
				break
			except Exception as problem :
				log_and_message( "ERROR: Unexpected ERROR in FTP connect: {}".format( sys.exc_info()[0] ) )
				log_and_message( "ERROR: in read_config() FTP (connect): {}".format( problem ) )
				log_and_message( "DEBUG: FTP credentials: s=\"{}\" l=\"{}\" p=\"{}\"".format( ftp_server, ftp_login, ftp_password ) )
#@@@			if "authentication" in problem :
#@@@				logger( "DEBUG: FTP credentials: s=\"{}\" l=\"{}\" p=\"{}\"".format( ftp_server, ftp_login, ftp_password ) )

		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------

#@@@	try :
#@@@		ftp = FTP( ftp_server, ftp_login, ftp_password )
#@@@		ftp_OK = True
#@@@	except Exception as problem :
#@@@		log_and_message( "ERROR: Unexpected ERROR in FTP connect: {}".format( sys.exc_info()[0] ) )
#@@@		log_and_message( "ERROR: FTP (connect): {}".format( problem ) )

		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------
		# ----------------------------------------------------------------------------------------

		if ftp_OK :
			try :
				ftp.cwd( remote_dir )
			except :
				ftp_OK = False
				log_and_message( "ERROR: Unexpected ERROR in FTP cwd: {}".format( sys.exc_info()[0] ) )
				log_and_message( "ERROR: remote_dir = \"{}\" is likely bad.".format(remote_dir) )

			try :
				ftp.quit()
			except :
				ftp_OK = False
				log_and_message( "ERROR: Unexpected ERROR in FTP quit: {}".format( sys.exc_info()[0] ) )
				log_and_message( "ERROR: remote_dir = \"{}\" is likely bad.".format(remote_dir) )


		if not ftp_OK :
			log_and_message( "ERROR: Quitting due to FTP error(s) above.  Exiting in 30 seconds ..." )
			sleep( 240 )
			log_and_message("  Good bye from " + this_script )
			log_string( "\n" )
			exit()

		try:

#DEBUG#		logger("DEBUG: reading: \"{}\"".format( image_age_URL ) )
			response = urlopen( image_age_URL )
#DEBUG#		logger("DEBUG: image age read from web: \"{}\"".format( age ) )
		except:
			log_and_message( "ERROR: Unexpected ERROR in urlopen: {}".format( sys.exc_info()[0] ) )
			log_and_message( "ERROR: image_age_URL = \"{}\" is likely bad.".format(image_age_URL) )


	if USE_SCP  and  len(scp_dest) < 3 :
		log_and_message( "ERROR: scp_dest = \"{}\"".format(scp_dest) )
		log_and_message( "ERROR: ftp_login = \"{}\"".format(ftp_login) )
		log_and_message( "ERROR: One of these needs to be specified in the config file." )
		exit()


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# We could handle these more generally.  If a value contains digits, convert to
	# int().  If digits and a '.', use float().
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	relay_GPIO = int( relay_GPIO )

	relay2_GPIO = int( relay2_GPIO )

	cam_timeout = int( cam_timeout )

	vid_gen_minute = int( vid_gen_minute )

	if len(mon_log) > 0  and  not os.path.exists(mon_log) :
		log_and_message( "ERROR: mon_log \"{}\" not found.".format( mon_log ) )
		if len(mon_log) > 1 :
			exit()

	dot_interval = int( dot_interval )

	mon_max_age = int( mon_max_age )

	cam_timeout = int( cam_timeout )

	ssh_cmd = [ "ssh", status_HOST, "pwd" ]

	try :
		output = subprocess.check_output(ssh_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
	except subprocess.CalledProcessError as e :
		output = ""
		logger( "ERROR: ssh: \"{}\" (from read_config), CalledProcessError)".format( sys.exc_info()[0] ) )
		logger( "DEBUG: ssh cmd = {}".format( e.cmd ) )
		logger( "DEBUG: ssh returncode = {}".format( e.returncode ) )
		logger( "DEBUG: ssh error output:\n{}".format( e.output ) )
		logger( "DEBUG: ssh command::\n{}".format( ssh_cmd ) )
		# https://stackoverflow.com/questions/7575284/check-output-from-calledprocesserror
	except :
		output = ""
		logger( "ERROR: ssh: {} (from read_config(), general case)".format( sys.exc_info()[0] ) )

	ssh_cmd = [ "ssh", status_HOST, "pwd" ]
	try :
		output = subprocess.check_output(ssh_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
	except :
		logger( "ERROR: status_HOST not accessible: {}".format( status_HOST ) )
		logger( "ERROR: ssh: {} (from read_config(), general case)".format( sys.exc_info()[0] ) )






# ----------------------------------------------------------------------------------------
# Cycle the power on the relay / GPIO.
# The off time can be specified.  Here in secs.
# Setting relay_GPIO to less than zero disables this function.
#
# From a quick test, the (South) RSX-3211 webam seems to take around 32 secs to reboot.
# ----------------------------------------------------------------------------------------
def power_cycle( ):

	if relay_GPIO < 0 :
		return

	cmd = "ssh {} /home/pi/webcamwatcher/power_cycle.py {}".format( relay_HOST, relay_GPIO )

	log_and_message( cmd )

	process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output,stderr = process.communicate()
	status = process.poll()
	log_and_message( status )
	log_and_message( output )

	# --------------------------------------------------------------------------------
	#  NOTE: I ran into this.  Perhaps I changed the code but never restarted it
	#   sudo journalctl -u webcam_south.service
	#   Mar 08 11:03:12 raspb_01_Cams python[525]: ssh: connect to host 23 port 22: Invalid argument
	#   Mar 08 11:05:02 raspb_01_Cams python[525]: 2019/03/08 11:05:02 WARNING: power-cycling webcam
	#   Mar 08 11:05:02 raspb_01_Cams python[525]: 255
	#   Mar 08 11:05:02 raspb_01_Cams python[525]: ssh: connect to host 23 port 22: Invalid argument
	#   Mar 08 11:06:52 raspb_01_Cams python[525]: 2019/03/08 11:06:52 WARNING: power-cycling webcam
	#   Mar 08 11:06:52 raspb_01_Cams python[525]: 255
	# --------------------------------------------------------------------------------

	return



# ----------------------------------------------------------------------------------------
#  This runs a script on the "status host", the Cumulus Pi at this point, which creates
#  a status record, which the statuscollector.py process appends to a status event log.
#
#  NOTE: If you want to pass a hex code for "background" do NOT include the leading '#'.
#  NOTE: If you want to pass a hex code for "background" do NOT include the leading '#'.
#  NOTE: If you want to pass a hex code for "background" do NOT include the leading '#'.
#
#
# ----------------------------------------------------------------------------------------
def log_event(description, code, background) :
	global status_HOST

#	logger( "DEBUG: background = \"{}\"".format( background ) )
	if len(background) > 0 :
		ssh_cmd = [
			"ssh",
			status_HOST,
			"bin/record_status.py",
			"--bgcolor",
			background,
			"\"{}\"".format(description),
			str(code),
			]
	else :
		ssh_cmd = [
			"ssh",
			status_HOST,
			"bin/record_status.py",
			"\"{}\"".format(description),
			str(code),
			]

	logger( "DEBUG: log_event ssh command: \"{}\"".format( ssh_cmd ) )

# @@@
	try :
		output = subprocess.check_output(ssh_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
	except subprocess.CalledProcessError as e :
		output = ""
		logger( "ERROR: ssh: \"{}\" (from log_event), CalledProcessError)".format( sys.exc_info()[0] ) )
		logger( "DEBUG: ssh cmd = {}".format( e.cmd ) )
		logger( "DEBUG: ssh returncode = {}".format( e.returncode ) )
		logger( "DEBUG: ssh error output:\n{}".format( e.output ) )
		logger( "DEBUG: ssh command::\n{}".format( ssh_cmd ) )
		# https://stackoverflow.com/questions/7575284/check-output-from-calledprocesserror
	except Exception as e :
		output = ""
		logger( "ERROR: ssh: {} (from log_event(), general case sys.exc_info)".format( sys.exc_info()[0] ) )
		logger( "ERROR: ssh: {} (from log_event(), general case sys.exc_info)".format( sys.exc_info() ) )
		logger( "ERROR: ssh: {} (from log_event(), general case e)".format( e ) )
		logger( "DEBUG: ssh command::\n{}".format( ssh_cmd ) )



#####	lines = re.split('\n', output)
	# if len(lines[0]) > 0 or len(lines) > 1 :
#####	if scp_failed and len(lines) > 1 :
#####		logger( "DEBUG: ssh stdout output:\n".format( output ) )
#####		for jjj in range( len(lines) ) :
#####			logger( "DEBUG: #{} \"{}\"".format( jjj, lines[jjj] ) )

	return



# ----------------------------------------------------------------------------------------
#  Handle a set of midnight tasks.
#  * Check for the arc_<YYYY> directory, and make if if needed.
#     * Also link /home/pi/webcamwatcher/rm_older_files.sh
#  * Tar up the day's snapshot images.
#  * Create thumbnail image for web pages.
#  * Delete many of the 'dark hours' images.
#  * Create the "daylight" mp4 video, and push to the web server.
#  * If all went well, remove the day's snapshot images.
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def midnight_process(date_string) :
	global work_dir
	ffmpeg_failed = True
	tar_failed = True

#DEBUG#	logger( "DEBUG: Called midnight_process( {} )".format(date_string ) )
	logger( "DEBUG: Called midnight_process( {} )".format(date_string ) )

	# Example: 20180523 - - - (looks like a number, but a string here.)
	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = work_dir + '/arc_' + yyyy
	tar_file = arc_dir + "/" + date_stamp + "_arc.tgz"

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Create tar file after some checking.
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if not os.path.exists( arc_dir ) :
		logger( "INFO: Created {}.  HAPPY NEW YEAR.".format( arc_dir) )
		os.mkdir( arc_dir, 0o755 )
		os.symlink( "/home/pi/webcamwatcher/rm_older_files.sh", arc_dir + "/rm_older_files.sh" )

	if os.path.isfile( tar_file ) :
		logger( "ERROR: {} already exists.  Quitting Midnight process.".format( tar_file ) )
		return

	tar_size = tar_dailies(date_string)

	if tar_size < 0 :
		logger( "ERROR: tar_dailies() failed.  Quitting Midnight process." )
		return
	else :
		tar_failed = False


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Create thumbnail image for web pages
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	tnf = daily_thumbnail( date_string, work_dir )
	if len(tnf) > 0 :
		push_to_server( tnf, remote_dir )

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# To make the daylight image, delete most of the dark overnight images.
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if remove_night_images( date_string, work_dir ) < 1 :
		logger( "WARNING: Could not find images for date \"{}\"".format( date_string ) )

	mp4_file_daylight = "{}/{}_daylight.mp4".format( arc_dir, date_stamp )
	### logger( "DEBUG: Building {}".format( mp4_file_daylight ) )
	ffmpeg_failed = generate_video( date_string, mp4_file_daylight )

	if not ffmpeg_failed :
		push_to_server( mp4_file_daylight, remote_dir )
	else :
		log_and_message( "ERROR: in midnight_process() ffmpeg failed." )


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# Cleanup the individual snapshot images for the day if things went well above...
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if tar_size <= 5000000 :
		logger( "WARNING: Tar is too small to justify deleting jpg files for {}.".format( date_string ) )

	elif not ffmpeg_failed and not tar_failed :
		logger( "INFO: Tar is large enough to delete jpg files for {}.".format( date_string ) )

		try:
			subprocess.check_output("rm " + work_dir + "/snapshot-" + date_string + r"*.jpg", shell=True)
		except :
			logger( "ERROR: Unexpected ERROR in rm: {}".format( sys.exc_info()[0] ) )
	else :
		logger( "WARNING: ffmpeg or tar failed; skip deleting jpg files for {}.".format( date_string ) )

# @@@
	if not ffmpeg_failed and not tar_failed :
		log_event("INFO: Video generated, images archived for {}".format( mp4_file_daylight ), 205, "0E7135")
	else :
		log_event("ERROR: Video not generated, or images not archived for {}".format( mp4_file_daylight ), 215, "red")


#DEBUG#	logger( "DEBUG: sleep( 15 )" )
#DEBUG#	sleep( 15 )
	logger( "DEBUG: sleep( 15 )\n" )
	sleep( 15 )


# ----------------------------------------------------------------------------------------
#  This handles the generation of an mp4 file
#
#  Storing 1 image every 2 minutes yields ( 60 / 2 ) * 24 = 720 frames
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def generate_video(date_string, mp4_out) :
	global work_dir

	logger( "DEBUG: generate_video( \"{}\", \"{}\" ) called".format( date_string, mp4_out ) )

	RC = -1
	ffmpeg_failed = True

	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
	yyyy = re.sub(r'(....).*', r'\1', date_string)

	# https://stackoverflow.com/questions/82831/how-to-check-whether-a-file-exists?rq=1
	if os.path.isfile( mp4_out ) :
		logger( "WARNING: {} already exists and will be deleted.".format ( mp4_out ) )
		unlink( mp4_out )

	cat_cmd = r"cat {}/snapshot-{}*.jpg".format( work_dir, date_string )
	logger( "DEBUG: cat_cmd = \"{}\"".format( cat_cmd ) )

	# NOTE: Trailing blank
	# ffmpeg_opts = "-f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 "
	# Per https://superuser.com/questions/326629/how-can-i-make-ffmpeg-be-quieter-less-verbose
	#    "-nostats -loglevel 0"   seems to cut the stderr output to almost nothing.
	#    "-nostats"    seems to eliminate the changing status which really blows up logs.
	# NOTE: Trailing blank
	ffmpeg_opts = "-f image2pipe -nostats -r 8 -vcodec mjpeg -i - -vcodec libx264 "
	logger( "DEBUG: ffmpeg_opts = \"{}\"".format( ffmpeg_opts ) )

	ffmpeg_cmd = cat_cmd + r" | ffmpeg " + ffmpeg_opts + mp4_out
	logger( "DEBUG: ffmpeg_cmd = \"{}\"".format( ffmpeg_cmd ) )

	logger( "DEBUG: calling = wait_ffmpeg()" )
	wait_ffmpeg()

	log_and_message( "DEBUG: Creating mp4 using cmd:\n\n{}".format( ffmpeg_cmd ) )
	ffmpeg = ""

	# --------------------------------------------------------------------------------
	# Ran into this once on 01/20/2021
	#
	#    Stream mapping:
	#      Stream #0:0 -> #0:0 (mjpeg (native) -> h264 (libx264))
	#    frame=   47 fps=0.0 q=0.0 size=       0kB time=00:00:00.00 bitrate=N/A speed=   0x
	#    frame=   69 fps= 60 q=24.0 size=      13kB time=00:00:02.00 bitrate=  52.8kbits/s speed=1.73x
	#    #frame=   94 fps= 57 q=24.0 size=      24kB time=00:00:05.12 bitrate=  39.1kbits/s speed=3.09x
	#    frame=  719 fps= 11 q=24.0 size=   22492kB time=00:01:23.25 bitrate=2213.3kbits/s speed=1.32x
	#    *** stack smashing detected ***: ffmpeg terminated
	#    Aborted
	#    2021/01/21 00:03:06 ERROR: Unexpected ERROR in ffmpeg:
	#    .
	#    Get an occaisional seg fault from ffmpeg - but we don't see it... logged in nohup at the moment
	#    See https://stackoverflow.com/questions/22250893/capture-segmentation-fault-message-for-a-crashed-subprocess-no-out-and-err-af
	#        Popen(shell_command, shell=True, stdout=PIPE, stderr=PIPE)
	#    .
	#    .
	# --------------------------------------------------------------------------------
	start = time.time()
	try :
		ffmpeg = subprocess.check_output(ffmpeg_cmd , shell=True).decode('utf-8')
		### ffmpeg_failed = False
	except subprocess.CalledProcessError as e :
		logger( "ERROR: ffmpeg: \"{}\" (from generate_video), CalledProcessError)".format( sys.exc_info()[0] ) )
		logger( "DEBUG: ffmpeg cmd = {}".format( e.cmd ) )
		logger( "DEBUG: ffmpeg returncode = {}".format( e.returncode ) )
		RC = e.returncode
		if e.returncode == 139 :
			logger( "DEBUG: Likely ffmpeg Segmentation fault" )
		logger( "DEBUG: ffmpeg output:\n{}".format( e.output ) )
		logger( "DEBUG: ffmpeg command::\n{}".format( ffmpeg_cmd ) )
		# https://docs.python.org/3/library/subprocess.html
		# https://stackoverflow.com/questions/7575284/check-output-from-calledprocesserror
	except Exception as problem :
		log_and_message( "ERROR: Unexpected ERROR in ffmpeg: \"{}\"".format( problem ) )
		ffmpeg_failed = True
		iii = 0
		for p in problem:
			iii += 1
			log_and_message( "DEBUG: {} ::: \"{}\"".format( iii, p ) )
###	except CalledProcessError, EHandle:
###	except :
###		log_and_message( "ERROR: Unexpected ERROR in ffmpeg: {}".format( sys.exc_info()[0] ) )
###		ffmpeg_failed = True
	else :
		ffmpeg_failed = False
	# finally :
		# See  https://docs.python.org/3/tutorial/errors.html

	elapsed = time.time() - start
	log_and_message( "DEBUG: ffmpeg runtime = {}".format( elapsed ) )
	# -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-
	# -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-
	# NOTE: ffmpeg -v info -nostats -i /mnt/ssd/TEST/Test/arc_2021/20210223_daylight.mp4 -f null -
	# Could be used to verify mp4 is good
	# See https://superuser.com/questions/100288/how-can-i-check-the-integrity-of-a-video-file-avi-mpeg-mp4
	#
	# or ffprobe 20210222_daylight.mp4 ; echo $?
	#     $ ffprobe 20210311_daylight.mp4 ; echo $?
	#     ffprobe version 3.2.15-0+deb9u2 Copyright (c) 2007-2020 the FFmpeg developers
	#         Metadata:
	#           handler_name    : VideoHandler
	#     0  <--  Returns 0 on success
	#     $ ffprobe .20210311_daylight.mp4 ; echo $?
	#     ffprobe version 3.2.15-0+deb9u2 Copyright (c) 2007-2020 the FFmpeg developers
	#       libpostproc    54.  1.100 / 54.  1.100
	#     [mov,mp4,m4a,3gp,3g2,mj2 @ 0x1fe7e00] moov atom not found
	#     .20210311_daylight.mp4: Invalid data found when processing input
	#     1  <--  Returns 1 on failure
	#
	# NOTE: https://stackoverflow.com/questions/59627740/how-to-validate-mp4-file-or-audio-files-in-general-with-python
	# -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-
	# -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-

	if len(ffmpeg) > 0 :
		log_and_message( "DEBUG: ffmpeg returned data: \"{}\"".format( ffmpeg ) )
	else :
		log_and_message( "DEBUG: ffmpeg returned nothing. ffmpeg_failed = {}, RC = {}".format( ffmpeg_failed, RC ) )

	if ffmpeg_failed :
		log_and_message( "WARNING: ffmpeg failed." )
	else :
		log_and_message( "DEBUG: ffmpeg success." )

	return ffmpeg_failed



# ----------------------------------------------------------------------------------------
#  This handles the tar of a daily set of image snapshots
#
#  Example argument:   2018-05-23
# ----------------------------------------------------------------------------------------
def tar_dailies(date_string) :
	global work_dir
	# global only technically needed if we write to variable
	tar_size = -1
	tar_failed = True

	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#  Tinkered with a few ideas for tar.
	#  Could not get --directory to work as I expected from the man page.
	#  I am also a little concerned about using a wildcard with the tar command.
	#  Seems like it might be safer to build a table of files, and the -T option
	#   (as I have been doing on the hosted server).  daily_image_list() builds it.
	#
	#   tar -c -zf South/arc_2018/arc-2018-06-01.tgz -T South/arc_2018/index-2018-06-01.txt
	#   tar tzvf South/arc_2018/arc-2018-06-01.tgz | less
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)
	arc_dir = work_dir + '/arc_' + yyyy
	image_index = arc_dir + '/index-' + date_string + ".txt"
	tar_file = arc_dir + "/" + date_stamp + "_arc.tgz"


	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#  NOTE: This is a bit draconian ... Need to think through a kinder, gentler approach
	#	In practice, I've been moving the existing one to /tmp.
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	if os.path.isfile( tar_file ) :
		logger( "ERROR: {} already exists.  Quitting tar process.".format( tar_file ) )
		return tar_size

	#
	#  The --directory flag would be elegant, if I could get it to work...
	#
	current_directory = os.getcwd()
	os.chdir( work_dir )
	

	#  Creats a list like South/arc_2018/index-2018-06-01.txt for use with -T
	nnn = daily_image_list(date_string, '.' )
	if ( nnn < 50 ) :
		logger( "WARNING: Index list looks short with {} items.".format( nnn ) )
	else :
		tar_cmd = "tar -c -T " + image_index + " -zf " + tar_file

		logger( "DEBUG: Creating tar file with: " + tar_cmd )
		try:
			subprocess.check_call(tar_cmd, shell=True)
			tar_failed = False
			unlink( image_index )
		except :
			logger( "ERROR: Unexpected ERROR in {}: {}".format( tar_cmd, sys.exc_info()[0] ) )

	try:
		tar_size = stat( tar_file ).st_size
	except :
		logger( "ERROR: Unexpected ERROR in stat: {}".format( sys.exc_info()[0] ) )
		tar_size = -1

	logger( "DEBUG: tar file size = {}".format( tar_size ) )



	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	#  If the system crashes before this is complete, you might see this
	#     gzip: stdin: unexpected end of file
	#     tar: Unexpected EOF in archive
	#     tar: Error is not recoverable: exiting now
	# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
	tar_cmd = [ "tar",
			"-tzf",
			tar_file ]
	try:
##		reply = subprocess.check_call(tar_cmd, shell=True)
		reply = subprocess.check_output( tar_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
##		print reply
##		logger( "DEBUG: tar -tzf members = {}".format( len(reply) ) )
		logger( "DEBUG: tar -tzf {} checked.  Returned = {} bytes.".format( tar_file, len(reply) ) )
	except :
		logger( "ERROR: Unexpected ERROR in {}: {}".format( tar_cmd, sys.exc_info()[0] ) )
		tar_size = -1

	os.chdir( current_directory )

	return tar_size




# ----------------------------------------------------------------------------------------
# Wait for a file to be completely written.
#
# We can notice a new file, or a directory m-time changing before a file is completely
# written.  This routine this attempts to insure that writing has been finished by
# checking that it's size has stopped growing.  There are 2 parameters involving in
# getting to *size stability*, set at the start of this routine:
#  * same_count_min - The minimum number of times (counts) seeing the same file size.
#  * sleep_for - The sleep time between reading the size in each iteration.
#
# We're just waiting for the file size to setle down, so we check it periodically
# looking to get the same size so many times in a row. We're trying to balance finding
# this condition fairly quickly after the (remote) writing completes (incurring a small
# delay) and making this a busy resource-consuming loop.
#
# This routine should rarely generate messages. If it does, these 2 parameters can
# be adjusted.  Largely trial and error, and is affected by network loading.
#
# The minimum time to return with a stable file size in seconds is
#       ( same_count_min - 1 ) * sleep_for
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#   20180614 16:37:09 DEBUG: convert returned data: "convert: Premature end of JPEG file
#	`South/S.jpg' @ warning/jpeg.c/JPEGWarningHandler/352.
# ----------------------------------------------------------------------------------------
def check_stable_size( filename ) :
	same_count_min = 5
	pause_for = 0.8

#DEBUG#	log_string( "DEBUG: \n" )

	# Need to get same_count_min sizes the same in a row to decide that we're stable
	same_count = 0
	last_size = -1
	newline = False
	for attempt in range(30) :
		file_size = stat( filename ).st_size
###		logger( "DEBUG: {} file_size = {} last_size = {}.".format(filename, file_size, last_size) )

		if file_size == last_size :
			same_count += 1
			if same_count > same_count_min :
				if not newline :
					log_string( "\n" )
					newline = True
				logger( "WARNING: {} == {} bytes,  same_count = {},  attempt # = {}".format( \
					file_size, last_size, same_count, attempt ) )
#DEBUG#			else :
#DEBUG#				logger( "DEBUG: {} == {}   same_count = {}  attempt = {}".format(file_size, last_size, same_count, attempt ) )
			if same_count >= same_count_min :
				break
		else :
			same_count = 0

		last_size = file_size
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# We should see this message fairly infrequently. `Seeing this frequently
		# in the log file may suggest that same_count_min needs to be nudged up.
		# At the moment ingaes are dropped here every 2 minutes so a few extra
		# seconds to process are of no significance.
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		if attempt >= same_count_min + 1 :
			if not newline :
				log_string( "\n" )
				newline = True
			logger( "WARNING: check_stable_size wait #{:2d}.  {} bytes  same_count ={:2d}.".format( \
				attempt+1, file_size, same_count) )

		sleep( pause_for )

	return last_size



# ----------------------------------------------------------------------------------------
#  Find image from the morning and make a thumbnail of it to represent the daily video.
#  Looks for the first image with hour > 7, i.e. around the 8 o'clock hour.
#
#  date_string example = "2018-07-04" - i.e. the date part of a snapshot file.
# ----------------------------------------------------------------------------------------
def daily_thumbnail( date_string, working_dir ) :
	morning_image = ""
	thumbnail_file = ""

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	file_list = listdir( working_dir )
	file_list_len = len( file_list )
	file_list.sort()

	look_for = "snapshot-" + date_string
###	logger( "DEBUG: look_for = {}.".format( look_for ) )

	found = 0

	for iii in range(0, file_list_len ) :
###		logger( "DEBUG: file[{}] = {}.".format( iii, file_list[iii] ) )
		if look_for in file_list[iii] :
			#   snapshot-2018-07-04-13-16-34.jpg
			#                       ^^
			hh = re.sub(r'.*snapshot-....-..-..-(..).*', r'\1', file_list[iii] )
###			logger( "DEBUG: hh = {}.".format( hh ) )

			if int(hh) > 7 :
###				logger( "DEBUG: For thumbnail file[{}] = {}.".format( iii, file_list[iii] ) )
				morning_image = working_dir + '/' + file_list[iii]
				break

	if len(morning_image) > 0 :

		# Example: 20180523 - - - (looks like a number, but a string here.)
		date_stamp = re.sub(r'(\d*)-(\d*)-(\d*)', r'\1\2\3', date_string)

		thumbnail_file = arc_dir + '/' + date_stamp + "-thumb.jpg"

		convert = ""
		logger( "DEBUG: Create thumbnail {}".format( date_stamp + "-thumb.jpg" ) )
		convert_cmd = ['/usr/bin/convert',
				morning_image,
				'-resize', '20%',
				thumbnail_file ]
		logger( "DEBUG: convert cmd = \"{}\"".format( convert_cmd ) )

		try :
			convert = subprocess.check_output( convert_cmd, stderr=subprocess.STDOUT ).decode('utf-8')
		except:
			logger( "ERROR: Unexpected ERROR in convert: {}".format( sys.exc_info()[0] ) )

	return thumbnail_file




# ----------------------------------------------------------------------------------------
#  Remove (most of) the dark night-time snapshots which are generally "uninteresting."
#  We do this before creating the mp4 video.
#
# ----------------------------------------------------------------------------------------
# NOTE: What I'd like to do, ideally, is vary the length of the video based on the date.
#	In the Summer we have around 15 hours of daylight here, in Winter about 9.
#	First light is maybe 30 minutes before.  I might try to approximate this.
#	Python Astral, https://astral.readthedocs.io/en/latest/ can calulate accurately
#	but I really just want to lop off the "boring" black frames at either end of the
#	day.
#
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#	https://pypi.org/project/astral/
#	https://astral.readthedocs.io/en/stable/index.html
#	https://www.programcreek.com/python/example/104603/astral.Astral
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
# Also see:
#	https://www.timeanddate.com/astronomy/astronomical-twilight.html
#	http://aa.usno.navy.mil/data/docs/RS_OneYear.php
#	http://aa.usno.navy.mil/cgi-bin/aa_rstablew.pl?ID=AA&year=2018&task=0&state=PA&place=Canonsburg
#	https://michelanders.blogspot.com/2010/12/calulating-sunrise-and-sunset-in-python.html
#	https://stackoverflow.com/questions/19615350/calculate-sunrise-and-sunset-times-for-a-given-gps-coordinate-within-postgresql
#
#
#	Daylight saving time 2018 in Pennsylvania began at 2:00 AM on
#	Sunday, March 11
#	and ends at 2:00 AM on
#	Sunday, November 4
#	All times are in Eastern Time.
#
#  date_string example = "2018-07-04" - i.e. the date part of a snapshot file.
#  working_dir example = "/home/pi/N/North"
# ----------------------------------------------------------------------------------------
# NOTE: Cheap sunrise-sunset solution...
# I loaded data from http://aa.usno.navy.mil/data/docs/RS_OneYear.php into a spreadsheet.
#  Doesn't handle DST
#
# cal -hy 2018 | sed 's/ /~/a'
#
# date -d 20181104 +'%u %Z'
# date -d 20181105 +'%u %Z'
# ----------------------------------------------------------------------------------------
def remove_night_images( date_string, working_dir ) :

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	file_list = listdir( working_dir )
	file_list.sort()
	file_list_len = len( file_list )

	look_for = "snapshot-" + date_string
	logger( "DEBUG: look_for = {}.".format( look_for ) )

	kept = 0
	deleted = 0

	for iii in range(0, file_list_len ) :
		if look_for in file_list[iii] :
			# file snapshot-2018-07-05-21-04-50.jpg is 12542 bytes.
			hhmm = int( re.sub( r'.*snapshot-2...-..-..-(..)-(..).*', r'\1\2', file_list[iii] ) )
			if hhmm < 500 :
				unlink( working_dir + "/" + file_list[iii] )
				deleted += 1
			elif hhmm > 2200 :
				unlink( working_dir + "/" + file_list[iii] )
				deleted += 1
			else :
				kept += 1

	found = kept + deleted
	logger( "DEBUG: remove_night_images kept {} and deleted {} of {}".format( kept, deleted, found ) )
	return found



# ----------------------------------------------------------------------------------------
#  Build a list of the days files (used as input to tar).
#
# ----------------------------------------------------------------------------------------
def daily_image_list( date_string, working_dir ) :

	yyyy = re.sub(r'(....).*', r'\1', date_string)
	arc_dir = working_dir + '/arc_' + yyyy

	look_for = "snapshot-" + date_string

	file_list = listdir( working_dir )
	file_list_len = len( file_list )

	image_index = arc_dir + '/index-' + date_string + ".txt"
	FH = open(image_index, "w")

	found = 0
	line = 0
	while line < file_list_len :
		if look_for in file_list[line] :
			FH.write( working_dir + "/" + file_list[line] + "\n" )
			found += 1
		line += 1

	logger( "DEBUG: {} items found for index file.".format( found ) )

	FH.close

	return found



# ========================================================================================
# ----------------------------------------------------------------------------------------
#  These routines store and fetch information we need to persist between invocations
#  of this script.  This needs to track what's already been "processed."
#
#  The variable last_mtime is initialized to 0.0, but otherwise hold the ts for
#  the file last processed.
#
# ----------------------------------------------------------------------------------------
def store_file_data(ts, filename) :
	global image_data_file
#DEBUG#	messager( "DEBUG: write " + image_data_file )
	FH = open(image_data_file, "w")
	FH.write( str(ts) + "\n" )
	FH.write( filename + "\n" )
	FH.close

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_ts() :
	global image_data_file
#DEBUG#	messager( "DEBUG: read " + image_data_file )
	try:
		FH = open(image_data_file, "r")
		content = FH.readlines()
		FH.close

		ts = str(content[0].strip("\n"))
	except:
		ts = 0.0
		filename = "snapshot-2000-01-01-01-01-01.jpg"
		store_file_data(ts, filename)

	logger( "DEBUG: Stored ts = {:8.1f}".format( float(ts) ) )

	return ts

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------
def get_stored_filename() :
	global image_data_file
#DEBUG#	messager( "DEBUG: read " + image_data_file )

	try:
		FH = open(image_data_file, "r")
		content = FH.readlines()
		FH.close

		filename = str(content[1].strip("\n"))
	except:
		ts = 0.0
		filename = "snapshot-2000-01-01-01-01-01.jpg"
		store_file_data(ts, filename)

	logger( "DEBUG: Stored filename = {}".format( filename ) )

	return filename





# ----------------------------------------------------------------------------------------
#
#  This selects the file transfer protocol we'll use.
#
# ----------------------------------------------------------------------------------------
def push_to_server(local_file, remote_path) :

	if USE_SCP :
		push_to_server_via_scp(local_file, remote_path)
	else :
		push_to_server_via_ftp(local_file, remote_path)




# ----------------------------------------------------------------------------------------
#  This pushes the specified file to the (hosted) web server via SCP.
#
#  References:
#   https://stackoverflow.com/questions/68335/how-to-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
#   https://stackoverflow.com/questions/250283/how-to-scp-in-python
#
#   https://stackoverflow.com/questions/68335/how-to-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
#   https://stackoverflow.com/questions/68335/how-to-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
# ----------------------------------------------------------------------------------------
def push_to_server_via_scp(local_file, remote_path) :

#	scp_dest = "user@remotehost:remotepath"
	destination = scp_dest + remote_path
	scp_failed = False

#	logger( "DEBUG: subprocess.check_output([\"scp\", \"-q\", \"-P\", \"21098\", {}, {}])".format( local_file, destination ) )

	# Create empty array in case the try block fails. This by the way creates a 0-th member.
	# Before I got the logic right with an "or" below, I saw...
	#   DEBUG: #0 ""
	try :
		output = subprocess.check_output(["scp", "-q", "-P", "21098", local_file, destination], stderr=subprocess.STDOUT ).decode('utf-8')
	except subprocess.CalledProcessError as e :
		scp_failed = True
		# lines = []
		# lines[0] = ""
	# if len(lines[0]) > 0 or len(lines) > 1 :
		output = ""
		logger( "ERROR: scp: \"{}\" (from push_to_server_via_scp(), CalledProcessError)".format( sys.exc_info()[0] ) )
		logger( "DEBUG: scp cmd = {}".format( e.cmd ) )
		logger( "DEBUG: scp returncode = {}".format( e.returncode ) )
		logger( "DEBUG: scp error output:\n{}".format( e.output ) )
		# https://stackoverflow.com/questions/7575284/check-output-from-calledprocesserror
	except :
		scp_failed = True
		# lines = []
		# lines[0] = ""
		output = ""
		logger( "ERROR: scp: {} (from push_to_server_via_scp(), general case)".format( sys.exc_info()[0] ) )


	lines = re.split('\n', output)
	# if len(lines[0]) > 0 or len(lines) > 1 :
	if scp_failed and len(lines) > 1 :
		logger( "DEBUG: scp stdout output:\n".format( output ) )
		for jjj in range( len(lines) ) :
			logger( "DEBUG: #{} \"{}\"".format( jjj, lines[jjj] ) )
	
	return



# ----------------------------------------------------------------------------------------
#  This pushes the specified file to the (hosted) web server via FTP.
#
#
#  FTP User: camdilly
#  FTP PWD: /home/content/b/o/b/bobdilly/html/WX
#
#  https://pythonspot.com/en/ftp-client-in-python/
#  https://docs.python.org/2/library/ftplib.html
#    NOTE:
#    NOTE:
#    NOTE: The third argument, server, is no longer needed...
#    NOTE:
#    NOTE:
# ----------------------------------------------------------------------------------------
def push_to_server_via_ftp(local_file, remote_path) :
	ftp_OK = False

#DEBUG#	logger( "DEBUG: push_to_server_via_ftp( {}, {}, {} )".format( local_file, remote_path, server ) )
#DEBUG#	logger( "DEBUG: push_to_server_via_ftp( {}, {}, {} )".format( local_file, remote_path, ftp_server ) )

	if re.search('/', local_file) :
		local_file_bare = re.sub(r'.*/', r'', local_file)

	# --------------------------------------------------------------------------------
	#  The ftp sequence involves 4 commands.  If any fail, those that follow may
	#  not make any sense to attempt, with the possible exception of quit (which
	#  could itself fail.
	#    ftp = FTP( server, ftp_login, ftp_password )
	#    ftp.cwd( remote_path )
	#    ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
	#    ftp.quit()
	#  Ran into a case where the first FTP command failed...
	#
	# https://stackoverflow.com/questions/567622/is-there-a-pythonic-way-to-try-something-up-to-a-maximum-number-of-times
	# --------------------------------------------------------------------------------
	for iii in range(8) :
		# Not on first iteration.  Then increase the sleep time with each iteration.
		#  With a 4 sec multiplier this comes to 112 seconds max...     (28 * 4)
		if iii > 0 :
			logger( "DEBUG: in push_to_server_via_ftp() sleep( {} )".format( iii * 4 ) )
			sleep( iii * 4 )

		try :
			# ----------------------------------------------------------------
			#
			# Ref: https://docs.python.org/2/library/ftplib.html
			# NOTE: The login/user, and password could be given here...
			#	FTP([host[, user[, passwd[, acct[, timeout]]]]])
			#
			# ----------------------------------------------------------------
			#  Odds are if this works, the remainng commands probably will
			# ----------------------------------------------------------------
#DEBUG#			messager( "DEBUG: FTP connect to {}".format( server ) )
			ftp = FTP( ftp_server, ftp_login, ftp_password )
			ftp_OK = True
			break
		except Exception as problem :
			logger( "ERROR: in push_to_server_via_ftp() FTP (connect): {}".format( problem ) )

			logger( "DEBUG: FTP credentials: s=\"{}\" l=\"{}\" p=\"{}\"".format( ftp_server, ftp_login, ftp_password ) )
#			if "authentication" in problem :
#				logger( "DEBUG: FTP credentials: s=\"{}\" l=\"{}\" p=\"{}\"".format( ftp_server, ftp_login, ftp_password ) )

		# ----------------------------------------------------------------------------------------
		#
		# ----------------------------------------------------------------------------------------


	if ftp_OK :
		try :
#DEBUG#			logger( "DEBUG: FTP remote cd to {}".format( remote_path ) )
			ftp.cwd( remote_path )
		except Exception as problem :
			logger( "ERROR: in push_to_server_via_ftp() ftp.cwd {}".format( problem ) )
			ftp_OK = False
	# --------------------------------------------------------------------------------
	#  Not absolutely sure I want to do this, but sometimes the process is just hosed...
	# --------------------------------------------------------------------------------
	else:
		exit()


	# --------------------------------------------------------------------------------
	# NOTE: It looks like this might be a temporary condition and a retry might
	#       might be in order...
	#       I would expect this is the previous use of the socket was busy.
	#       I suppose it could be 2 instances of this trying to ftp files concurrently.
	#
	#  https://stackoverflow.com/questions/6176445/problem-socket-error-address-already-in-use-in-python-selenium
	#  https://stackoverflow.com/questions/41423642/python-socket-server-address-already-in-use
	#
	# --------------------------------------------------------------------------------
	#  2019/09/10 17:36:36 ERROR: in push_to_server() ftp.storbinary 425 Unable to identify the local data socket: Address already in use
	#  2019/09/10 19:28:36 ERROR: in push_to_server() ftp.storbinary 425 Unable to identify the local data socket: Address already in use
	#  2019/09/11 12:26:47 ERROR: in push_to_server() ftp.storbinary 425 Unable to identify the local data socket: Address already in use
	#  2019/09/11 13:12:50 ERROR: in push_to_server() ftp.storbinary 425 Unable to identify the local data socket: Address already in use
	# --------------------------------------------------------------------------------

	if ftp_OK :
		for iii in range(8) :
			if iii > 0 :
				logger( "DEBUG: in push_to_server_via_ftp() sleep( {} )".format( iii * 4 ) )
				sleep( iii * 4 )

			try :
				if iii > 0 :
					logger( "DEBUG: FTP STOR {} ===> {}  attempt #{}".format( local_file, local_file_bare, iii+1) )
				else :
					dummy_for_else_clause = 1
#DEBUG#					logger( "DEBUG: FTP STOR {} ---> {}".format( local_file, local_file_bare ) )

				ftp.storbinary('STOR ' +  local_file_bare, open(local_file, 'rb'))
				ftp_OK = True
				break

			except Exception as problem :
				logger( "ERROR: in push_to_server_via_ftp() ftp.storbinary \"{}\"".format( problem ) )
				# --------------------------------------------------------
				# --------------------------------------------------------
				#                       if not catching_up and ( (file_list_len - line) > 2 ) :
				#
				# Should wait and retry when problem =
				#
				# 425 Unable to identify the local data socket: Address already in use
				#						997 in sample
				#
				# Wrap in a loop as with the above line:
				#    ftp = FTP( ftp_server, ftp_login, ftp_password )
				#
				#
				# Other repiles to consider are:
 				# [Errno 101] Network is unreachable		3 in sample
 				# [Errno 110] Connection timed out		76 in sample
				#						out of 102841 calls
				# --------------------------------------------------------
				# --------------------------------------------------------
				ftp_OK = False


	try :
		ftp.quit()
	except Exception as problem :
		logger( "ERROR: in push_to_server_via_ftp() ftp.quit {}".format( problem ) )
		ftp.close()


	return


# ----------------------------------------------------------------------------------------
#  Read the [ftp] section of the config file passed as the first argument to this script.
#
#
# ----------------------------------------------------------------------------------------
def read_FTP_config( config_file ) :
	global ftp_login
	global ftp_password
	global ftp_server

#	NOTE: Copied from def read_config( config_file )
#	------------------------------------------------

# 	# https://docs.python.org/2/library/configparser.html
	config = configparser.RawConfigParser()
	# This was necessary to avoid folding variable names to all lowercase.
	# https://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
	config.optionxform = str
	config.read( config_file )
	#print config.getboolean('Settings','bla') # Manual Way to acess them

	# https://stackoverflow.com/questions/924700/best-way-to-retrieve-variable-values-from-a-text-file-python-json
	parameter=dict(config.items("ftp"))
	for p in parameter:
		parameter[p]=parameter[p].split("#",1)[0].strip() # To get rid of inline comments

###		messager( "DEBUG: p = {}".format( p ) )
###		messager( "DEBUG: parameter[p] = {}".format( parameter[p] ) )

	globals().update(parameter)  #Make them availible globally

	if len(ftp_login) < 1 :
		USE_SCP = True
		log_and_message( "INFO: ftp_login = \"{}\" - - Setting USE_SCP = {}".format(ftp_login, USE_SCP) )
	else :
		check_FTP_config()


# ----------------------------------------------------------------------------------------
#    NOTE: Relies on globals.
#
# ----------------------------------------------------------------------------------------
def check_FTP_config() :
	ftp_OK = False

	try :
		ftp = FTP( ftp_server, ftp_login, ftp_password )
		ftp_OK = True
	except Exception as problem :
		log_and_message( "ERROR: Unexpected ERROR in FTP connect: {}".format( sys.exc_info()[0] ) )
		log_and_message( "ERROR: FTP (connect): {}".format( problem ) )

	if ftp_OK :
		try :
			ftp.quit()
		except :
			ftp_OK = False
			log_and_message( "ERROR: Unexpected ERROR in FTP quit: {}".format( sys.exc_info()[0] ) )
	return ftp_OK


# ----------------------------------------------------------------------------------------
# Return a timestamp - time only
# ----------------------------------------------------------------------------------------
def timestamp() :
	time = datetime.datetime.now().strftime(time_only_FMT)
#	logger( "DEBUG: {}".format( time ) )
	return time


# ----------------------------------------------------------------------------------------
# Write message to the log file with a leading timestamp.
#
# NOTE: Most of the call to messager() should be converted to logger() at some point.
#	especially if we want to turn this into a service.
# ----------------------------------------------------------------------------------------
def logger(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)

	FH = open(logger_file, "a")
	FH.write( "{} {}\n".format( timestamp, message) )
	FH.close

# ----------------------------------------------------------------------------------------
# Write message to common log file with a leading timestamp.
#
#   Same as logger() except that this is used for key events (image processed) shared
#   among multiple instances of this so that, if one want's to reboot for example, one
#   can look at the system as a whole...
# ----------------------------------------------------------------------------------------
def logger_common(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)

	if len( common_log ) > 1 :
		FH = open(common_log, "a")
		FH.write( "{} {}\n".format( timestamp, message) )
		FH.close

# ----------------------------------------------------------------------------------------
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print("{} {}".format( timestamp, message))

# ----------------------------------------------------------------------------------------
# Print and log the message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def log_and_message(message):
	messager(message)
	logger(message)

# ----------------------------------------------------------------------------------------
# This prints just a symbol or two - for a progress indicator.
#
#		sys.stdout.write('.')
#		sys.stdout.flush()
# ----------------------------------------------------------------------------------------
def log_string(text):
	FH = open(logger_file, "a")
	FH.write( text )
	FH.close

# ----------------------------------------------------------------------------------------
# Write the PID of this Python script to a .PID file by the name name.
# This gets run at script start-up.
# ----------------------------------------------------------------------------------------
def write_pid_file():
	PID = str(getpid()) + "\n"
	pid_file = sys.argv[0]
	pid_file = re.sub('\.py', '.PID', pid_file)

	FH = open(pid_file, "w")
	FH.write(PID)
	FH.close


# ----------------------------------------------------------------------------------------
#  Fetch the version of mono
#
# ----------------------------------------------------------------------------------------
def mono_version():
###	global data

	try :
		response = subprocess.check_output(["/usr/bin/mono", "-V"]).decode('utf-8')
		line = re.split('\n', response)
		tok = re.split(' *', line[0])
		version = tok[4]
	except:
		logger( "WARNING: From mono version check: {}".format( sys.exc_info()[0] ) )
		version = "Not found"

###	data['mono_version'] = version
	return version



# ----------------------------------------------------------------------------------------
#  Wait for ffmpeg (to complete).
#
#  Running two instances of ffmpeg on a Pi concurrently seems to be a problem.
# ----------------------------------------------------------------------------------------
def wait_ffmpeg() :
	delay_secs = 10
	delay_secs = 5
	# Total wait approximately delay_secs * range() below.

	for iii in range(35) :
#		messager( "DEBUG: iteration {}".format( iii ) )
		try:
			response = subprocess.check_output(["/bin/ps", "-ef"]).decode('utf-8')
			line = re.split('\n', response)
		except :
			logger( "ERROR: Unexpected ERROR in ps -ef: {}".format( sys.exc_info()[0] ) )
			line = []


		for jjj in range( len(line) ) :
			if "ffmpeg" in line[jjj] :
				logger( "DEBUG: #{} total delay {} sec: '{}'".format( iii, iii * delay_secs, line[jjj] ) )
				sleep( delay_secs )
				break

#		messager( "DEBUG: jjj+1 = {}  len(line) = {}".format( jjj + 1, len(line) ) )
		if jjj + 1 >= len(line) :
			return



# ----------------------------------------------------------------------------------------
#  Check webcam status by fetching a control file from the hosted web-server.
#  The file just contains a number - the number of seconds between the time of
#  last writing the generically-named full-size image file, e.g. N.jpg by FTP,
#  an the current time.  Since cron_10_min.sh runs every 5 minutes
#
#   Can verify with: curl http://dillys.org/wx/North/N_age.txt
#
#  20180705 - Since moving most of the web cam image processing to the Pi, cron_10_min.sh
#  was seriously chopped down.  I also deleted a lof of the control files, including the
#  one this routine was looking at.  Oopps.  Looking at this routine, I decided it was
#  too complicated.
#
#  20180415 - Camera didn't stop, but was uploading some garbage periodically.
#  This file gets an epoch timestamp written to it when we've seen a number of 0-length
#  or rather short images uploaded from the webcam within a certain period.
#		response = urllib.urlopen('http://dillys.org/wx/N_cam_reboot_request.txt')
#
# ----------------------------------------------------------------------------------------
def camera_down():
#	global check_counter

	log_string( "[@1]" )  # On entry - NOTE: Added because of apparent hang, maybe in urlopen()
			      # NOTE: See banner 2021/03/25 at the end for an example
			      # NOTE: See banner 2021/03/25 at the end for an example

	age = "0"
	content = "-1\n-1"

	# --------------------------------------------------------------------------------
	#
	# --------------------------------------------------------------------------------
	try :
#>>>		response = urlopen( realtime_URL )
		response = urlopen( image_age_URL )
		log_string( "[@1a]" )  # After urlopen() call - NOTE: Added because of apparent hang, maybe in urlopen()

		# NOTE: The decode() methed seemed required for Python 3.  See
		#       https://stackoverflow.com/questions/31019854/typeerror-cant-use-a-string-pattern-on-a-bytes-like-object-in-re-findall
		#       https://stackoverflow.com/questions/37722051/re-search-typeerror-cannot-use-a-string-pattern-on-a-bytes-like-object
		# NOTE: This was moved to an else clause after the exceptions.
		# content = response.read().decode('utf-8')

	except ( URLError, Exception ) as err :
		log_string( "[@2]" )  # First except block, URLError - NOTE: Added because of apparent hang, maybe in urlopen()
		log_and_message( "ERROR: in camera_down: {}".format( sys.exc_info()[0] ) )
		# ------------------------------------------------------------------------
		#  See https://docs.python.org/2/tutorial/errors.html (~ middle)
		# ------------------------------------------------------------------------
		log_and_message( "ERROR: type: {}".format( type(err) ) )
		log_and_message( "ERROR: args: {}".format( err.args ) )
		if hasattr(err, 'reason'):
			log_and_message( 'ERROR: We failed to reach a server.' )
			log_and_message( 'ERROR: Reason: {}'.format( err.reason ) )

		elif hasattr(err, 'code'):
			log_and_message( 'ERROR: The server couldn\'t fulfill the request.' )
			log_and_message( 'ERROR: code: {}'.format( err.code ) )

		else:
			# ----------------------------------------------------------------
			# https://docs.python.org/3.5/library/sys.html   exc_info()
			# https://docs.python.org/3.5/library/traceback.html?highlight=format_exception
			# https://www.programcreek.com/python/example/246/traceback.format_exception
			# ----------------------------------------------------------------
			err_type, err_value, err_tb = err
			log_and_message( "ERROR: in camera_down: type: {}".format( err_type ) )
			log_and_message( "ERROR: in camera_down: value: {}".format( err_value ) )
			log_and_message( "ERROR: in camera_down: {}".format( traceback.format_exception( err_type, err_value, err_tb ) ) )

		# ------------------------------------------------------------------------
		#  https://docs.python.org/2/tutorial/errors.html
		#  https://docs.python.org/2/library/sys.html
		#  https://docs.python.org/3/library/traceback.html
		#  https://docs.python.org/2/library/traceback.html
		#
		#  https://stackoverflow.com/questions/8238360/how-to-save-traceback-sys-exc-info-values-in-a-variable
		# ------------------------------------------------------------------------
		log_and_message( "DEBUG: content = \"" + content + "\" in camera_down()" )


#
	except :
		log_string( "[@4]" )  # Default except block - NOTE: Added because of apparent hang, maybe in urlopen()
		log_and_message( "ERROR: in camera_down: NOT URLError" )
		log_and_message( "DEBUG: Calling traceback.print_tb(tb, limit=None, file=None)" )
		traceback.print_tb(file=sys.stdout)

	else :
		content = response.read().decode('utf-8')
######	logger( "DEBUG: content = \"" + content + "\" in camera_down()" )

	log_string( "[@5]" )  # End of urlopen() try block - NOTE: Added because of apparent hang, maybe in urlopen()

	#---# logger( "DEBUG: len(content) = {}".format( len(content) ) )
	lines = re.split( '\n', content )
	#---# logger( "DEBUG: len(lines) = {}".format( len(lines) ) )

	age = int( lines[0] )
	seconds = int( lines[1] )

	# --------------------------------------------------------------------------------
	# ================================================================================
	# ================================================================================
	# ================================================================================
	#   For testing...
	# ================================================================================
	# ================================================================================
	# ================================================================================
	# logger( "DEBUG: Server image age = {}".format(age) )
	log_string( "[@6] {}\n".format( timestamp() ) )  # On camera_down() return - NOTE: Added because of apparent hang, maybe in urlopen()
	return

	# ================================================================================
	#
	# ================================================================================
	if age > cam_timeout :
		logger("WARNING: image age: {}".format( age ) )
		power_cycle( )
#		log_restart( "webcam power-cycled, interval: {}".format( age ) )
		# Give the cam time to reset, and the webserver crontab to fire.
		# The camera comes up pretty quickly, but it seems to resynch to
		# the 5-minute interval, and the server crontab only fires every
		# 5 minutes (unsyncronized as a practical matter).  So 10 min max.
		sleep(2)
#		sleep(sleep_on_recycle)
		return 1
	else:
		return 0



# ----------------------------------------------------------------------------------------
# The function main contains a "do forever..." (and is called in a try block here)
#
# This handles the startup and shutdown of the script.
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
######################################################################################################	global work_dir, main_image, thumbnail_image, remote_dir
	#### This might be useful...
	#### if sys.argv[1] = "stop"
	log_string( "\n\n\n\n" )
	print( "\n\n\n\n" )
	log_and_message("INFO: Starting {}   PID={}".format( this_script, getpid() ) )

###		For testing @@@
###	global ftp_login
###	global ftp_password
###	tnf = daily_thumbnail( "2018-07-04", "/home/pi/N/North" )
###	if len(tnf) > 0 :
###		fetch_FTP_credentials( ".ftp.credentials" )
###		NOTE:  Use read_FTP_config( config_file )
###		push_to_server( tnf, "North", wserver )
###	exit()
###	wait_ffmpeg()
###	exit()

###  For re-processing failed overnight video creation, etc.
###	do_midnight()
###	exit()


	write_pid_file()

	try:
		main()

	# --------------------------------------------------------------------------------
	# Probably should handle external signals.  I manually use kill -9 (SIGKILL)
	#   https://www.cyberciti.biz/faq/unix-kill-command-examples/
	# Not sure what systemctl uses...
	# --------------------------------------------------------------------------------
	except KeyboardInterrupt:
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		# Progress indicator Ending
		# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
		log_string( "\n" )
		logger("  Good bye from " + this_script)

	exit()


# ----------------------------------------------------------------------------------------
#  This started as a test.  Turned out with some embellishment, to be helpful in
#  going back in history to create a _daylight version of the video.  For the moment
#  this remains here are the end of the file just in case.
#
#  Before running...
#     - Create a .save directory under arc_20xx
#     - Move (mv) the 3 files for the date in question
#     - Run the hacked webcamimager.py
#     - Copy or move (mv) the .save/*.tgz back to arc_20xx
#         --> This tar will have *ALL* the day's frames
#     - Remove the files in .save/ - if you wish
#
#  You may want to hack up logger()...
#  def logger(message):
#	messager(message)      <<<<<<<<--------------------  INSERT
#	return                 <<<<<<<<--------------------  INSERT
#	timestamp = datetime.datetime.now().strftime(strftime_FMT)
#
# Modify
# def midnight_process(date_string) :
#	return                 <<<<<<<<--------------------  INSERT
#	logger( "DEBUG: sleep( 15 )" )
#	sleep( 15 )
#
#  Arguments:
#  Arguments:
#   1 - "N" or "S"
#   2 - date string, e.g. 2018-05-23
# ----------------------------------------------------------------------------------------
def do_midnight() :
	global work_dir, remote_dir
	if len(sys.argv) < 3 :
		print("Too few arguments")
		print("Example:")
		print("S 2020-01-13")
		### print "S 2020-01-13 ~/S/south.cfg"
		exit()

	print("{} arguments".format(len(sys.argv)-1))

	### config_file = sys.argv[3]
	date_string = sys.argv[2]

	NS = sys.argv[1]
	if "N" in NS :
		mp4_file = "/mnt/ssd/N/North/arc_2018/{}_daylight.mp4".format( re.sub(r'-', r'', date_string) )
		remote_dir = "North"
		work_dir = "/mnt/ssd/N/North"
		config_file = "/mnt/ssd/N/north.cfg"
	elif "S" in NS :
		mp4_file = "/mnt/ssd/S/South/arc_2018/{}_daylight.mp4".format( re.sub(r'-', r'', date_string) )
		remote_dir = "South"
		work_dir = "/mnt/ssd/S/South"
		config_file = "/mnt/ssd/S/south.cfg"
	elif "T" in NS :
		mp4_file = "/mnt/ssd/TEST/Test/arc_2018/{}_daylight.mp4".format( re.sub(r'-', r'', date_string) )
		remote_dir = "Test"
		work_dir = "/mnt/ssd/TEST/Test"
		config_file = "/mnt/ssd/TEST/test.cfg"
	else :
		print("Arg #1 is bad.  Use N or S or T")
		exit()

	read_FTP_config( config_file )

	midnight_process( date_string )

	return

# ========================================================================================
#    * NOTE: Some Python pages I refer to
#  Regular Expressions
#  https://docs.python.org/2/library/re.html
# ========================================================================================

########################################################################################
########################################################################################
########################################################################################
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# 06/03/2018 Midnight
#
#  ........................................
#  2018/06/04 04:03:44 DEBUG: Copy image file South/snapshot-2018-06-04-00-03-46.jpg as S.jpg and upload to South
#  2018/06/04 04:03:45 DEBUG: Create and upload thumbnail South/S_thumb.jpg to server directory South
#  INFO: MIDNIGHT ROLLOVER!
#  INFO: MIDNIGHT ROLLOVER!
#  INFO: MIDNIGHT ROLLOVER!
#  INFO: MIDNIGHT ROLLOVER!
#  2018/06/04 04:03:46 DEBUG: Creating tar file with: tar -c -T South/arc_2018/index-2018-06-03.txt -zf South/arc_2018/arc-2018-06-03.tgz
#  2018/06/04 04:03:50 DEBUG: tar file size = 15671428
#  2018/06/04 04:03:50 DEBUG: Creating mp4 fileSouth/20180603.mp4
#  2018/06/04 04:03:50 DEBUG: cat_cmd = "cat South/snapshot-2018-06-03*.jpg"
#  2018/06/04 04:03:50 DEBUG: ffmpeg_opts = "-f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 "
#  2018/06/04 04:03:50 DEBUG: ffmpeg_cmd = "cat South/snapshot-2018-06-03*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 South/20180603.mp4"
#  2018/06/04 04:03:50 DEBUG: Creating mp4 using cmd: cat South/snapshot-2018-06-03*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 South/20180603.mp4
#  ffmpeg version 3.2.10-1~deb9u1+rpt1 Copyright (c) 2000-2018 the FFmpeg developers
#    built with gcc 6.3.0 (Raspbian 6.3.0-18+rpi1) 20170516
#    configuration: --prefix=/usr --extra-version='1~deb9u1+rpt1' --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libebur128 --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libmp3lame --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-omx-rpi --enable-mmal --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libopencv --enable-libx264 --enable-shared
#    libavutil      55. 34.101 / 55. 34.101
#    libavcodec     57. 64.101 / 57. 64.101
#    libavformat    57. 56.101 / 57. 56.101
#    libavdevice    57.  1.100 / 57.  1.100
#    libavfilter     6. 65.100 /  6. 65.100
#    libavresample   3.  1.  0 /  3.  1.  0
#    libswscale      4.  2.100 /  4.  2.100
#    libswresample   2.  3.100 /  2.  3.100
#    libpostproc    54.  1.100 / 54.  1.100
#  Input #0, image2pipe, from 'pipe:':
#    Duration: N/A, bitrate: N/A
#    Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 640x480, 8 fps, 8 tbr, 8 tbn, 8 tbc
#  No pixel format specified, yuvj420p for H.264 encoding chosen.
#  Use -pix_fmt yuv420p for compatibility with outdated media players.
#  [libx264 @ 0x1962db0] using cpu capabilities: ARMv6 NEON
#  [libx264 @ 0x1962db0] profile High, level 2.2
#  [libx264 @ 0x1962db0] 264 - core 148 r2748 97eaef2 - H.264/MPEG-4 AVC codec - Copyleft 2003-2016 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=6 lookahead_threads=1 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=8 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00
#  Output #0, mp4, to 'South/20180603.mp4':
#    Metadata:
#      encoder         : Lavf57.56.101
#      Stream #0:0: Video: h264 (libx264) ([33][0][0][0] / 0x0021), yuvj420p(pc), 640x480, q=-1--1, 8 fps, 16384 tbn, 8 tbc
#      Metadata:
#        encoder         : Lavc57.64.101 libx264
#      Side data:
#        cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: -1
#  Stream mapping:
#    Stream #0:0 -> #0:0 (mjpeg (native) -> h264 (libx264))
#  frame=  288 fps=9.0 q=-1.0 Lsize=    7586kB time=00:00:35.62 bitrate=1744.4kbits/s speed=1.11x
#  video:7582kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.055490%
#  [libx264 @ 0x1962db0] frame I:4     Avg QP:20.24  size: 56232
#  [libx264 @ 0x1962db0] frame P:86    Avg QP:20.98  size: 35120
#  [libx264 @ 0x1962db0] frame B:198   Avg QP:22.33  size: 22817
#  [libx264 @ 0x1962db0] consecutive B-frames:  6.2%  4.9%  4.2% 84.7%
#  [libx264 @ 0x1962db0] mb I  I16..4:  5.8% 82.0% 12.2%
#  [libx264 @ 0x1962db0] mb P  I16..4:  3.7% 51.2%  4.8%  P16..4: 15.8% 14.1%  8.4%  0.0%  0.0%    skip: 2.1%
#  [libx264 @ 0x1962db0] mb B  I16..4:  2.5% 21.6%  2.0%  B16..8: 24.1% 16.2%  6.2%  direct:21.8%  skip: 5.6%  L0:40.5% L1:33.0% BI:26.5%
#  [libx264 @ 0x1962db0] 8x8 transform intra:84.3% inter:70.2%
#  [libx264 @ 0x1962db0] coded y,uvDC,uvAC intra: 63.6% 83.5% 59.5% inter: 67.5% 78.7% 23.2%
#  [libx264 @ 0x1962db0] i16 v,h,dc,p: 44% 29% 25%  2%
#  [libx264 @ 0x1962db0] i8 v,h,dc,ddl,ddr,vr,hd,vl,hu: 22% 19% 41%  2%  3%  2%  4%  3%  4%
#  [libx264 @ 0x1962db0] i4 v,h,dc,ddl,ddr,vr,hd,vl,hu: 14% 18% 12%  7% 11%  8% 12%  7% 11%
#  [libx264 @ 0x1962db0] i8c dc,h,v,p: 54% 22% 19%  5%
#  [libx264 @ 0x1962db0] Weighted P-Frames: Y:40.7% UV:39.5%
#  [libx264 @ 0x1962db0] ref P L0: 38.3% 15.8% 19.5% 19.1%  7.3%
#  [libx264 @ 0x1962db0] ref B L0: 68.4% 24.0%  7.7%
#  [libx264 @ 0x1962db0] ref B L1: 87.4% 12.6%
#  [libx264 @ 0x1962db0] kb/s:1725.10
#  2018/06/04 04:04:22 INFO: Tar is large enough to delete jpg files.
#  2018/06/04 04:04:29 DEBUG: file # 6 of 6 (last)
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# log fragment 2
# I only really expected Catch-up mode to occur when the script starts up.  I can't see
# why it would occur here, other than check_stable_size() induced delay which is fairly
# rare when we're in steady state.  I bumped the threshold for setting "catching_up = True"
# from 1 to 2 ... without fully understanding why.
#
# 2018/09/18 16:50:32 INFO: process /home/pi/N/North/snapshot-2018-09-18-16-50-47.jpg
# .......................||  (23)
# 2018/09/18 16:52:32 INFO: process /home/pi/N/North/snapshot-2018-09-18-16-52-47.jpg
# .......................2018/09/18 16:54:31 DEBUG: check_stable_size wait #2.  69819 bytes.
# ||  (23)
# 2018/09/18 16:54:33 INFO: process /home/pi/N/North/snapshot-2018-09-18-16-54-47.jpg
# .......................2018/09/18 16:56:31 INFO: Catch-up mode on
# 2018/09/18 16:56:33 DEBUG: file 1031 of 1032 !!!!!! Skip processing snapshot-2018-09-18-16-54-47.jpg (in Catch-up)
# 2018/09/18 16:56:33 INFO: Catch-up mode off
# ||  (23)
# 2018/09/18 16:56:35 INFO: process /home/pi/N/North/snapshot-2018-09-18-16-56-47.jpg
# .......................||  (23)
#
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#
#  $ ./do_midnight.py S 2018-09-30
#  2018/10/01 09:28:04 INFO: Starting /home/pi/do_midnight.py   PID=3739
#  3 arguments
#  2018/10/01 09:28:14 DEBUG: Creating mp4 using cmd: cat /home/pi/S/South/snapshot-2018-09-30*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 /home/pi/S/South/arc_2018/20180930_daylight.mp4
#  ffmpeg version 3.2.10-1~deb9u1+rpt2 Copyright (c) 2000-2018 the FFmpeg developers
#    built with gcc 6.3.0 (Raspbian 6.3.0-18+rpi1+deb9u1) 20170516
#    configuration: --prefix=/usr --extra-version='1~deb9u1+rpt2' --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libebur128 --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libmp3lame --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-omx-rpi --enable-mmal --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libiec61883 --arch=armhf --enable-chromaprint --enable-frei0r --enable-libopencv --enable-libx264 --enable-shared
#    libavutil      55. 34.101 / 55. 34.101
#    libavcodec     57. 64.101 / 57. 64.101
#    libavformat    57. 56.101 / 57. 56.101
#    libavdevice    57.  1.100 / 57.  1.100
#    libavfilter     6. 65.100 /  6. 65.100
#    libavresample   3.  1.  0 /  3.  1.  0
#    libswscale      4.  2.100 /  4.  2.100
#  libswresample   2.  3.100 /  2.  3.100
#    libpostproc    54.  1.100 / 54.  1.100
#  Input #0, image2pipe, from 'pipe:':
#    Duration: N/A, bitrate: N/A
#      Stream #0:0: Video: mjpeg, yuvj420p(pc, bt470bg/unknown/unknown), 640x480, 8 fps, 8 tbr, 8 tbn, 8 tbc
#  No pixel format specified, yuvj420p for H.264 encoding chosen.
#  Use -pix_fmt yuv420p for compatibility with outdated media players.
#  [libx264 @ 0x558db0] using cpu capabilities: ARMv6 NEON
#  [libx264 @ 0x558db0] profile High, level 2.2
#  [libx264 @ 0x558db0] 264 - core 148 r2748 97eaef2 - H.264/MPEG-4 AVC codec - Copyleft 2003-2016 - http://www.videolan.org/x264.html - options: cabac=1 ref=3 deblock=1:0:0 analyse=0x3:0x113 me=hex subme=7 psy=1 psy_rd=1.00:0.00 mixed_ref=1 me_range=16 chroma_me=1 trellis=1 8x8dct=1 cqm=0 deadzone=21,11 fast_pskip=1 chroma_qp_offset=-2 threads=6 lookahead_threads=1 sliced_threads=0 nr=0 decimate=1 interlaced=0 bluray_compat=0 constrained_intra=0 bframes=3 b_pyramid=2 b_adapt=1 b_bias=0 direct=1 weightb=1 open_gop=0 weightp=2 keyint=250 keyint_min=8 scenecut=40 intra_refresh=0 rc_lookahead=40 rc=crf mbtree=1 crf=23.0 qcomp=0.60 qpmin=0 qpmax=69 qpstep=4 ip_ratio=1.40 aq=1:1.00
#  Output #0, mp4, to '/home/pi/S/South/arc_2018/20180930_daylight.mp4':
#    Metadata:
#      encoder         : Lavf57.56.101
#      Stream #0:0: Video: h264 (libx264) ([33][0][0][0] / 0x0021), yuvj420p(pc), 640x480, q=-1--1, 8 fps, 16384 tbn, 8 tbc
#      Metadata:
#        encoder         : Lavc57.64.101 libx264
#      Side data:
#        cpb: bitrate max/min/avg: 0/0/0 buffer size: 0 vbv_delay: -1
#  Stream mapping:
#    Stream #0:0 -> #0:0 (mjpeg (native) -> h264 (libx264))
#  frame=  154 fps= 14 q=24.0 size=    1827kB time=00:00:12.62 bitrate=1185.8kbits/s speed=1.12x
#      ** CRASH **
#
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

# 03/01/2021 This process just seemed to freeze.

#   $ procs
#   UID        PID  PPID  C STIME TTY          TIME CMD
#   pi        1757     1  0 Feb24 ?        00:07:10 /usr/bin/python3 -u /mnt/ssd/S/webcamimager.py /mnt/ssd/S/south.cfg
#   pi        1811     1  0 Feb24 ?        00:10:06 /usr/bin/python3 -u /mnt/ssd/N/webcamimager.py /mnt/ssd/N/north.cfg
#   pi        1928     1  0 Feb24 ?        00:19:18 /usr/bin/python3 -u /mnt/ssd/TEST/webcamimager.py /mnt/ssd/TEST/test.cfg
#   found 3 of the expected 3 processes

#   $ logs
#   DEBUG: checking 3 log files...
#   DEBUG: age =    57.12  max =   500.00  /home/pi/webcamwatcher/pinger.log
#   DEBUG: age =     1.66  max =    20.00  /mnt/ssd/S/webcamimager.log
#   DEBUG: age = 51232.01  max =    20.00  /mnt/ssd/N/webcamimager.log
#   ERROR: log file /mnt/ssd/N/webcamimager.log is age = 51232.01 seconds old (beyond    20.00 )


# "webcamimager.log"
#   2021/02/28 18:33:26 ERROR: args: (OSError(0, 'Error'),)
#   2021/02/28 18:33:26 ERROR: We failed to reach a server.
#   2021/02/28 18:33:26 ERROR: Reason: [Errno 0] Error
#   2021/02/28 18:33:26 DEBUG: content = "-1
#   -1" in camera_down()
#   2021/02/28 18:33:32 waiting
#   .||  (1)  18:33:39
#   2021/02/28 18:33:39 INFO: Process snapshot-2021-02-28-18-33-01.jpg    13857 B  1614555182.3
#   2021/02/28 18:34:09 waiting
#   .||  (1)  18:34:17
#   2021/02/28 18:34:17 INFO: Process snapshot-2021-02-28-18-34-01.jpg    15121 B  1614555243.0
#   2021/02/28 18:34:31 waiting
#   .......||  (7)  18:35:09
#   2021/02/28 18:35:09 INFO: Process snapshot-2021-02-28-18-35-01.jpg    13185 B  1614555302.7
#   2021/02/28 18:35:37 waiting
#   .....||  (5)  18:36:05
#   2021/02/28 18:36:05 INFO: Monitoring "/mnt/ssd/N/North"
#   2021/02/28 18:36:05 INFO: Process snapshot-2021-02-28-18-36-01.jpg    12453 B  1614555362.5
#   2021/02/28 18:36:39 waiting
#   .....||  (5)  18:37:07
#   2021/02/28 18:37:07 INFO: Process snapshot-2021-02-28-18-37-01.jpg    11854 B  1614555422.2
# NOTE: given "sleep_for = 5", the time for each 'dot', it is taking a long time to process...
#
#       S T U C K
#       S T U C K
#       S T U C K
#
#

# "sudo journalctl -u webcam_north"
#   Feb 28 00:03:57 raspb_01_Cams python3[1811]: 2021/02/28 00:03:57 DEBUG: ffmpeg returned nothing.
#   Feb 28 00:03:57 raspb_01_Cams python3[1811]: 2021/02/28 00:03:57 DEBUG: ffmpeg success.
#   Feb 28 18:33:26 raspb_01_Cams python3[1811]: 2021/02/28 18:33:26 ERROR: in camera_down: <class 'urllib.error.URLError'>
#   Feb 28 18:33:26 raspb_01_Cams python3[1811]: 2021/02/28 18:33:26 ERROR: type: <class 'urllib.error.URLError'>
#   Feb 28 18:33:26 raspb_01_Cams python3[1811]: 2021/02/28 18:33:26 ERROR: args: (OSError(0, 'Error'),)
#   Feb 28 18:33:26 raspb_01_Cams python3[1811]: 2021/02/28 18:33:26 ERROR: We failed to reach a server.
#   Feb 28 18:33:26 raspb_01_Cams python3[1811]: 2021/02/28 18:33:26 ERROR: Reason: [Errno 0] Error
#
# Restarted  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
#   Mar 01 08:51:39 raspb_01_Cams systemd[1]: Stopping Webcam Image Processing North...
#   Mar 01 08:51:39 raspb_01_Cams systemd[1]: Stopped Webcam Image Processing North.
#   Mar 01 08:51:39 raspb_01_Cams systemd[1]: Started Webcam Image Processing North.

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

 #####    ###    #####     #          #   ###    #####        #  #####  #######
#     #  #   #  #     #   ##         #   #   #  #     #      #  #     # #
      # # #   #       #  # #        #   # #   #       #     #         # #
 #####  #  #  #  #####     #       #    #  #  #  #####     #     #####   #####
#       #   # # #          #      #     #   # #       #   #     #             #
#        #   #  #          #     #       #   #  #     #  #      #       #     #
#######   ###   #######  #####  #         ###    #####  #       #######  #####

#   .........................||  (25)  12:18:05
#   2021/03/25 12:18:05 INFO: Monitoring "/mnt/ssd/N/North"
#   2021/03/25 12:18:05 INFO: Process snapshot-2021-03-25-12-18-01.jpg   138227 B  1616689082.5
#   [@1][@5][@6]
#   2021/03/25 12:18:10 waiting
#   ..........................||  (26)  12:19:05
#   2021/03/25 12:19:05 INFO: Process snapshot-2021-03-25-12-19-01.jpg   139409 B  1616689142.2
#   [@1][@5][@6]
#   2021/03/25 12:19:18 waiting
#   .......................||  (23)  12:20:06
#   2021/03/25 12:20:06 INFO: Process snapshot-2021-03-25-12-20-01.jpg   139297 B  1616689202.9
#   [@1][@5][@6]
#   2021/03/25 12:20:19 waiting
#   ......................||  (22)  12:21:06
#   2021/03/25 12:21:06 INFO: Process snapshot-2021-03-25-12-21-01.jpg   139361 B  1616689262.5
#   [@1]2021/03/25 12:23:18 ERROR: in camera_down: <class 'urllib.error.URLError'>
#   2021/03/25 12:23:18 ERROR: type: <class 'urllib.error.URLError'>
#   2021/03/25 12:23:18 ERROR: args: (TimeoutError(110, 'Connection timed out'),)
#   2021/03/25 12:23:18 ERROR: We failed to reach a server.
#   2021/03/25 12:23:18 ERROR: Reason: [Errno 110] Connection timed out
#   2021/03/25 12:23:18 DEBUG: content = "-1
#   -1" in camera_down()
#   2021/03/25 12:23:18 DEBUG: content = "-1
#   -1" in camera_down()
#   [@5][@6]
#   2021/03/25 12:23:24 waiting
#   .||  (1)  12:23:29
#   2021/03/25 12:23:29 INFO: Process snapshot-2021-03-25-12-22-01.jpg   139059 B  1616689322.2
#   [@1][@5][@6]
#
#   . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#      NOTE: the gap in time...
#   . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
#   2021/03/25 12:40:11 waiting
#   ..........................||  (26)  12:41:06
#   2021/03/25 12:41:06 INFO: Process snapshot-2021-03-25-12-41-01.jpg   135112 B  1616690462.3
#   [@1][@5][@6]
#   2021/03/25 12:41:11 waiting
#   ..........................||  (26)  12:42:06
#   2021/03/25 12:42:06 INFO: Monitoring "/mnt/ssd/N/North"
#   2021/03/25 12:42:06 INFO: Process snapshot-2021-03-25-12-42-02.jpg   134155 B  1616690523.0
#   [@1]2021/03/25 12:44:49 ERROR: in camera_down: <class 'urllib.error.URLError'>
#   2021/03/25 12:44:49 ERROR: type: <class 'urllib.error.URLError'>
#   2021/03/25 12:44:49 ERROR: args: (TimeoutError(110, 'Connection timed out'),)
#   2021/03/25 12:44:49 ERROR: We failed to reach a server.
#   2021/03/25 12:44:49 ERROR: Reason: [Errno 110] Connection timed out
#   2021/03/25 12:44:49 DEBUG: content = "-1
#   -1" in camera_down()
#   2021/03/25 12:44:49 DEBUG: content = "-1
#   -1" in camera_down()
#   [@5][@6]
#   2021/03/25 12:45:09 waiting
#   .
#   2021/03/25 12:45:11 INFO: Catch-up mode on
#   2021/03/25 12:45:11 DEBUG: file   764 of   766 !!!!!! Skip processing snapshot-2021-03-25-12-43-01.jpg (in Catch-up)
#   2021/03/25 12:45:11 DEBUG: file   765 of   766 !!!!!! Skip processing snapshot-2021-03-25-12-44-01.jpg (in Catch-up)
#
#   2021/03/25 12:45:11 INFO: Catch-up mode off
#   ||  (1)  12:45:14
#   2021/03/25 12:45:14 INFO: Process snapshot-2021-03-25-12-45-02.jpg   133274 B  1616690703.0
#   [@1][@5][@6]
#   2021/03/25 12:45:20 waiting
#
#   . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#      NOTE: the gap in time...
#   . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
#   ..........................||  (26)  13:35:06
#   2021/03/25 13:35:06 INFO: Process snapshot-2021-03-25-13-35-01.jpg   138561 B  1616693702.6
#   [@1][@5][@6]
#   2021/03/25 13:35:22 waiting
#   ....................||  (20)  13:36:05
#   2021/03/25 13:36:05 INFO: Process snapshot-2021-03-25-13-36-01.jpg   139513 B  1616693762.3
#   [@1]
#        NOTE: Hung after the first beacon was logged.
#
#
# NOTE: From . . . sudo journalctl -u webcam_north
#
#   Mar 25 10:17:46 raspb_01_Cams python3[28939]: 2021/03/25 10:17:46 INFO: mon_max_age = "600"
#   Mar 25 10:17:46 raspb_01_Cams python3[28939]: 2021/03/25 10:17:46 INFO: other_systemctl = "webcam_south"
#   Mar 25 10:17:46 raspb_01_Cams python3[28939]: 2021/03/25 10:17:46 INFO: status_HOST = "pi@192.168.1.10"
#   Mar 25 10:17:46 raspb_01_Cams python3[28939]: 2021/03/25 10:17:46
#   Mar 25 10:17:46 raspb_01_Cams python3[28939]: 2021/03/25 10:17:46 INFO: Python version: v 3.5.3 (default, Nov 18 2020, 21:09:16) ,
#   Mar 25 10:17:46 raspb_01_Cams python3[28939]: 2021/03/25 10:17:46
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: 2021/03/25 12:23:18 ERROR: in camera_down: <class 'urllib.error.URLError'>
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: 2021/03/25 12:23:18 ERROR: type: <class 'urllib.error.URLError'>
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: 2021/03/25 12:23:18 ERROR: args: (TimeoutError(110, 'Connection timed out'),)
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: 2021/03/25 12:23:18 ERROR: We failed to reach a server.
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: 2021/03/25 12:23:18 ERROR: Reason: [Errno 110] Connection timed out
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: 2021/03/25 12:23:18 DEBUG: content = "-1
#   Mar 25 12:23:18 raspb_01_Cams python3[28939]: -1" in camera_down()
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: 2021/03/25 12:44:49 ERROR: in camera_down: <class 'urllib.error.URLError'>
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: 2021/03/25 12:44:49 ERROR: type: <class 'urllib.error.URLError'>
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: 2021/03/25 12:44:49 ERROR: args: (TimeoutError(110, 'Connection timed out'),)
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: 2021/03/25 12:44:49 ERROR: We failed to reach a server.
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: 2021/03/25 12:44:49 ERROR: Reason: [Errno 110] Connection timed out
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: 2021/03/25 12:44:49 DEBUG: content = "-1
#   Mar 25 12:44:49 raspb_01_Cams python3[28939]: -1" in camera_down()


# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

 #####    ###    #####     #          #   ###    #####        #  #####  #######
#     #  #   #  #     #   ##         #   #   #  #     #      #  #     # #    #
      # # #   #       #  # #        #   # #   #       #     #         #     #
 #####  #  #  #  #####     #       #    #  #  #  #####     #     #####     #
#       #   # # #          #      #     #   # #       #   #     #         #
#        #   #  #          #     #       #   #  #     #  #      #         #
#######   ###   #######  #####  #         ###    #####  #       #######   #

# Runaway loop...
#
#   2021/03/28 09:08:27 INFO: status_HOST = "pi@192.168.1.10"
#   2021/03/28 09:08:27 
#   2021/03/28 09:08:27 INFO: Python version: v 3.5.3 (default, Nov 18 2020, 21:09:16) , [GCC 6.3.0 20170516]
#   2021/03/28 09:08:27 
#   2021/03/28 09:08:27 DEBUG: Stored ts = 1616858107.9
#   2021/03/28 09:08:27 DEBUG: Stored filename = snapshot-2021-03-27-11-15-01.jpg
#
#   2021/03/28 09:08:27 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg last?????   dot_counter  = 0 delta = 12.049928188323975
#   2021/03/28 09:08:27 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg this?????   dot_counter  = 0 ds = "2021-03-27"
#
#   2021/03/28 09:08:27 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg last?????   dot_counter  = 0 delta = 12.049928188323975
#   2021/03/28 09:08:27 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg this?????   dot_counter  = 0 ds = "2021-03-27"
#
#   2021/03/28 09:08:27 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg last?????   dot_counter  = 0 delta = 12.049928188323975
#   2021/03/28 09:08:27 DEBUG-WARNING: Reprocessing snapshot-2021-03-27-11-15-01.jpg this?????   dot_counter  = 0 ds = "2021-03-27"
#


# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------



