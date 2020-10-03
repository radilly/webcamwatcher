
alias apt_update='sudo apt-get update && sudo apt-get upgrade && sudo apt-get dist-upgrade'

alias camstatus='sudo systemctl status webcam_north webcam_south'
alias cleanold='df -h . ; cd ~/S/South/arc_`date +%Y` ; ./rm_older_files.sh ; cd ~/N/North/arc_`date +%Y` ; ./rm_older_files.sh ; df -h .'
alias cleanold='df -h . ; pushd ~/S/South/arc_`date +%Y` ; ./rm_older_files.sh ; popd ; pushd ~/N/North/arc_`date +%Y` ; ./rm_older_files.sh ; popd ; df -h .'

alias ck_4_old='check_for_old_snapshots.sh'
alias ck_journal='sudo journalctl -u webcam_south'
# Also   ffmpeg -i ~/S/South/arc_2020/20200114_daylight.mp4 -vcodec copy -f rawvideo -y /dev/null 2>&1 ; echo $?
alias ck_vid_validity='/home/pi/bin/check_latest_vids.sh'

#  https://ma.ttias.be/clear-systemd-journal/
#  https://www.loggly.com/ultimate-guide/managing-journal-size/
alias clean_journal='sudo journalctl --vacuum-time=10d'

alias piprocs='ps -ef | egrep "^pi"'
alias procs='~/bin/process_check.py ~/expected_procs.grep'

### alias startcumulus='/usr/bin/nohup sudo /usr/bin/mono $PWD/CumulusMX.exe &'
alias startcumulus='sudo /usr/bin/nohup /usr/bin/mono $PWD/CumulusMX.exe &'
alias wxprocs='ps -ef | grep -f ~/background.grep'
alias wxprocs2='ps -ef | egrep "Cumulus|webcamwatch|DataStopped"'
alias wxstatus='sudo systemctl status cumulusmx wxwatchdog'
alias watchthecam='sudo nohup /home/pi/webcamwatch.py &'
alias tail_diags='tail --lines=150 -f `ls -tr /mnt/root/home/pi/Cumulus_MX/MXdiags/* | tail -1`'
alias tail_namecheap='tail --lines=150 -f ~/namecheap_ftp.log'

alias trackerprocs='ps -fp `cat /mnt/root/home/pi/watchdog.PID` -p `cat /mnt/root/home/pi/top_tracker.PID`'
alias os_release='cat /etc/os-release'
alias os_release_02='lsb_release -a'
# alias launcht='/mnt/root/home/pi/launch_trackers.sh'
alias tttts='tail -fn100 /home/pi/S/webcamimager.log'
alias ttttn='tail -fn100 /home/pi/N/webcamimager.log'

alias top_mon='cd /mnt/root/home/pi/ ; tail -fn500 top_mono.log'



# alias launchn='cd /home/pi/N ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/N/North N.jpg N_thumb.jpg North >> webcamimager.log 2>&1 & ; tail -fn100 /home/pi/N/webcamimager.log'
# alias launchs='cd /home/pi/S ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/S/South S.jpg S_thumb.jpg South >> webcamimager.log 2>&1 & ; tail -fn100 /home/pi/S/webcamimager.log'
# alias launchS='cd /home/pi ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/South S.jpg S_thumb.jpg South >> webcamimager.log 2>&1 & ; tail -fn100 /home/pi/webcamimager.log'
# alias launchn='cd /home/pi/N ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/N/North N.jpg N_thumb.jpg North >> webcamimager.log 2>&1 &'
# alias launchs='cd /home/pi/S ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/S/South S.jpg S_thumb.jpg South >> webcamimager.log 2>&1 &'
# alias launchn='cd /home/pi/N ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/N/North N.jpg N_thumb.jpg North &'
# alias launchs='cd /home/pi/S ; kill -9 `cat webcamimager.PID` ; nohup /usr/bin/python -u ./webcamimager.py /home/pi/S/South S.jpg S_thumb.jpg South &'



alias top_mon='cd /mnt/root/home/pi/ ; tail -fn500 top_mono.log'

alias mk_mpeg_example='cat /home/pi/N/North/snapshot-2018-06-24*.jpg | ffmpeg -f image2pipe -r 8 -vcodec mjpeg -i - -vcodec libx264 /home/pi/N/North/arc_2018/20180624.mp4'

alias ck_uploads='ls --full-time -adltr /home/pi/[NS]/[NS]*/* | grep -v `date +snapshot-%Y-%m-%d`'
alias ck_snaps='ls --full-time -adltr /home/pi/[NS]/[NS]*/* | tail'

alias powercyclecam='~/power_cycle.py 23'


