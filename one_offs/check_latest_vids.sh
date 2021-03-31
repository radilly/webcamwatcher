#! /bin/bash

# ls -tr ~/[NS]/*/arc*/*mp4 | tail -n2 | while read FILE ; do
ls -tr /mnt/ssd/[NST]*/*/arc*/*mp4 | tail -n3 | while read FILE ; do

	echo "Checking ${FILE}"
	TEMP="/tmp/`date +%s`.`basename ${FILE}`.txt"
	touch "${TEMP}"

	ffprobe -select_streams v -show_streams "${FILE}" &>> "${TEMP}" ; RC=$?
	# ffprobe -select_streams v -show_streams "${FILE}" 2>&1 "${TEMP}" ; RC=$?
	egrep '(nb_frames|ffprobe|atom|Invalid)' "${TEMP}"
	ls  -al "${TEMP}"
	rm "${TEMP}"
	#  https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
	if [[ $RC -ne 0 ]] ; then
		printf $'\033[31m'
		echo "RC=${RC}"
		echo "ERROR: Likely problem with ${FILE}"
		printf $'\033[0m'
	else


		printf $'\033[32m'
		echo "RC=${RC}"
		printf $'\033[0m'
	fi
	echo

done



exit

ls -tr ~/[NS]/*/arc*/*mp4 | tail -n2 | xargs -ti ffprobe -select_streams v -show_streams {} 2>&1 | egrep '(nb_frames|ffprobe)'
echo "RC=$?"


