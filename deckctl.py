#!/usr/bin/env python

# For Apache:
#  sudo cp -p NEW.py /usr/lib/cgi-bin/


# ==============================================================================
#
# https://www.raspberrypi.org/forums/viewtopic.php?t=94639
#   http://abyz.me.uk/rpi/pigpio/python.html
#
#
# https://hwwong168.wordpress.com/2015/10/04/run-bash-shell-cgi-on-raspberry-pi-apache-2-4/
#
#    library WiringPi
#
#
#
# A different approach, python based:
#  https://www.e-tinkers.com/2018/04/how-to-control-raspberry-pi-gpio-via-http-web-server/
#
#
#
# https://www.raspberrypi.org/forums/viewtopic.php?t=155229
# https://www.raspberrypi.org/forums/viewtopic.php?t=148254
# http://www.civrays.com/myrobot/news/pythoncgi
# https://www.raspberrypi.org/forums/viewtopic.php?t=96200
#
# https://shiroku.net/robotics/run-cgi-program-on-raspberry-pi-as-web-server/
#
#
#
# https://www.raspberrypi.org/forums/viewtopic.php?t=151118
#
# ==============================================================================
# https://www.tutorialspoint.com/python/python_cgi_programming.htm

# https://www.tutorialspoint.com/How-to-pass-Radio-Button-Data-to-Python-CGI-script

# https://stackoverflow.com/questions/41077806/run-python-command-when-a-button-is-clicked



# https://html.com/tags/button/
#    <button type="button" onclick="alert('You pressed the button!')">Click me!</button>


# See https://www.namecheap.com/support/knowledgebase/article.aspx/9587/29/how-to-run-python-scripts
# See http://interactivepython.org/runestone/static/webfundamentals/CGI/forms.html
# ------------------------------------------------------------------------------
# Written for know-the-other.org.  Runs from ~/public_html/cgi-bin
# ------------------------------------------------------------------------------
# ========================================================================================
# 20201213 RAD Hacked up a script for creating links to a video that would expire
#              after a time for the Homewood work.  The hack was named and tested
#              as NEW.py, in .../webcamwatcher/PYTHON/cgi-bin.
# ========================================================================================

import os
# import datetime
import time
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
#  See https://stackoverflow.com/questions/7033953/python-cgi-program-wants-to-know-the-ip-address-of-the-calling-web-page
import cgi
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
import re
import sys
import subprocess
import stat

this_script = sys.argv[0]
if re.match('^\./', this_script) :
	this_script = "{}/{}".format( os.getcwd(), re.sub('^\./', '', this_script) )
logger_file = re.sub('\.py', '.log', this_script)


# Could not get %Z to work. "empty string if the the object is naive" ... which now() is...
strftime_FMT = "%Y/%m/%d %H:%M:%S"


headers = ["Content-type: text/html"]
qs = os.environ['QUERY_STRING']

def sendHeaders():
    for h in headers:
        print h
    print "\n"

def sendForm():
    print '''
    <html><head>
<!-- https://www.w3schools.com/tags/tryit.asp?filename=tryhtml_button_css -->
<style>
.button {
  border: none;
  color: white;
  padding: 15px 32px;
  text-align: center;
  text-decoration: none;
  font-weight: 900;
  display: inline-block;
  font-size: 16px;
  margin: 4px 2px;
  cursor: pointer;
}

.button1 {background-color: green;} /* Green */
.button2 {background-color: #FF1111;} /* Red */
</style>
</head>
    <title>
      Control Deck Lights
    </title></head>
      <body BGCOLOR="#333333" TEXT="#FFFF00" LINK="#FFFF00" VLINK="#FFCC00" ALINK="#FFAAFF"><center>
	<H1>
      Control Deck Lights
	</H1>

        <!-- @@@ -->

	<CENTER>
	<TABLE>
          <TR>
          <TD ROWSPAN=3>
          <IMG SRC="http://192.168.1.172/Deck_Lights_Mini.jpg">
          </TD>

<!--          <TD valign="middle"> -->
          <TD style="vertical-align:top">
<!--            <FONT SIZE=+7><B> &nbsp; &#8593; &nbsp;  -->
            <IMG HEIGHT="60" SRC="http://192.168.1.172/up_arrow_006.jpg">
 <!--       <BR>
            &nbsp; -->
          </TD>
          <TD style="vertical-align:top">
          <!--   https://www.raspberrypi.org/forums/viewtopic.php?t=237543  -->
          <form name="relayform_XXX" method="get" action="NEW.py">
              <button class="button button1" type="submit" name="overhead" value="on"> &nbsp; ON &nbsp; </button>
              <button class="button button2" type="submit" name="overhead" value="off"> &nbsp; OFF &nbsp; </button>
          </form>
          </TD>

          </TR>
          <TR>
          <TD COLSPAN=2>
            &nbsp;
            <BR> &nbsp;
          </TD>
          </TR>
          <TR>
          <TD style="vertical-align:top">
<!--        &nbsp;
            <BR> -->
            <IMG HEIGHT="60" SRC="http://192.168.1.172/down_arrow_006.jpg">
<!--            <FONT SIZE=+7> &nbsp; &#8595; &nbsp; -->
          </TD>
          <TD style="vertical-align:top">

          <!--   https://www.raspberrypi.org/forums/viewtopic.php?t=237543  -->
          <form name="relayform_XXX" method="get" action="NEW.py">
              <button class="button button1" type="submit" name="surface" value="on"> &nbsp; ON &nbsp; </button>
              <button class="button button2" type="submit" name="surface" value="off"> &nbsp; OFF &nbsp; </button>
          </form>
          </TD>
          </TR>

          <TD>
	</TABLE>
	</CENTER>

	<P> &nbsp;
    '''
#    print "<P><FONT SIZE=-2> logger_file = " 
#    print logger_file 
    print "</FONT>"
    print '''
      </body>
    </html>
    '''


def sendForm_001():
    print '''
    <html><head>
<!-- https://www.w3schools.com/tags/tryit.asp?filename=tryhtml_button_css -->
<style>
.button {
  border: none;
  color: white;
  padding: 15px 32px;
  text-align: center;
  text-decoration: none;
  font-weight: 900;
  display: inline-block;
  font-size: 16px;
  margin: 4px 2px;
  cursor: pointer;
}

.button1 {background-color: green;} /* Green */
.button2 {background-color: #FF1111;} /* Red */
</style>
</head>
    <title>
      Control Deck Lights
    </title></head>
      <body BGCOLOR="#333333" TEXT="#FF0000" LINK="#FFFF00" VLINK="#FFCC00" ALINK="#FFAAFF"><center>
	<H1>
      Control Deck Lights
	</H1>

        <!-- @@@ -->

	<HR>
          <!--   https://www.raspberrypi.org/forums/viewtopic.php?t=237543  -->
          <form name="relayform_XXX" method="get" action="NEW.py">
              <button class="button button1" type="submit" name="overhead" value="on"> -Overhead-ON- </button>
              <button class="button button2" type="submit" name="overhead" value="off"> -Overhead-OFF- </button>
              <P> &nbsp;
              <P> &nbsp;
              <button class="button button1" type="submit" name="surface" value="on"> -Surface-ON- </button>
              <button class="button button2" type="submit" name="surface" value="off"> -Surface-OFF- </button>
          </form>

	<P> &nbsp;
    '''
#    print "<P> logger_file = " 
#    print logger_file 
    print '''
      </body>
    </html>
    '''

# ------------------------------------------------------------------------------
# NOTE: Handle case where link already exists...
# ------------------------------------------------------------------------------
def sendPage(name, cmd):
    expires = int(time.time()) + 3600
    expires_human = time.ctime( expires )


#    cmd = "sudo " + cmd
#--    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#--    output,stderr = process.communicate()
#--    status = process.poll()
#	process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#	output,stderr = process.communicate()
#	status = process.poll()
#	print status
#	print output


    print '''
    <html>
      <meta http-equiv="refresh" content="1;URL='NEW.py'">
      <head><title>
      qs = os.environ['QUERY_STRING']
    </title></head>
      <body BGCOLOR="#333333" TEXT="#FFFF00" LINK="#FFFF00" VLINK="#FFCC00" ALINK="#FFAAFF"><center>
        <h2>qs = os.environ['QUERY_STRING']</h2>
	<P> QUERY_STRING: {0}
	<P> &nbsp;
	<P> Shell Command: {1}
	<P> &nbsp;
      </body>
    </html>
    '''.format( name, cmd )

#--    source="/home/knowkeye/public_html/PROTECT/WPRC19001_Homewood_Campaign_FINAL.mp4"
#--    dest="/home/knowkeye/public_html/TEMPORARY/{0}.mp4".format( name )
#--    try :
#--        os.symlink(source, dest)
#--    except :
#--        print "<P> &nbsp; <P><FONT COLOR=red> WARNING: os.symlink( {0}, {1})</FONT>".format( source, dest )

#--    FH = open(links_list, "a")
#--    FH.write( "{0} {1}    {2}\n".format( expires, dest, expires_human ) )
#--    FH.close

#--    FH = open(links_log, "a")
#--    FH.write( "<P> Link: {1} <BR> Expires: {2}\n".format( expires, dest, expires_human ) )
    # FH.write( "<TR><TD> Link: {1} </TD><TD> Expires: {2} </TD><TR>\n".format( expires, dest, expires_human ) )

#--    try : 
#--        ipaddress = cgi.escape(os.environ["REMOTE_ADDR"])
#--    except :
#--        ipaddress = "0.0.0.0"
#--    FH.write( "<BR> <I>From IP: {0}</I>\n".format( ipaddress ) )
#--    FH.close




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
# Print message with a leading timestamp.
#
# ----------------------------------------------------------------------------------------
def messager(message):
	timestamp = datetime.datetime.now().strftime(strftime_FMT)
	print "{} {}".format( timestamp, message)

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
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
#       M A I N
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

if not qs:
    sendHeaders()
    sendForm()
else:

#   2049  /home/pi/gpio_driver.py 18 lo		OFF
#   2059  /home/pi/gpio_driver.py 18 hi		ON
#
#      The relay on pin 22 is active LOW...
#   2057  /home/pi/gpio_driver.py 22 hi		OFF
#   2058  /home/pi/gpio_driver.py 22 lo		ON
#      relay_GPIO = 22
#   2060  /home/pi/light_timer.py on
#   2061  /home/pi/light_timer.py off

#   overhead=on		 -Overhead-ON- 
#   overhead=off	 -Overhead-OFF- 
#   surface=on		 -Surface-ON- 
#   surface=off		 -Surface-OFF- 

    if 'overhead' in qs:
        cmd = "/home/pi/gpio_driver.py 18"
        if 'on' in qs:
            cmd = cmd + " hi"
        else:
            cmd = cmd + " lo"
    elif 'surface' in qs:
        cmd = "/home/pi/gpio_driver.py 22"
        if 'on' in qs:
            cmd = cmd + " lo"
        else:
            cmd = cmd + " hi"
##--        cmd = "/home/pi/light_timer.py"
##--        if 'on' in qs:
##--            cmd = cmd + " on"
##--        else:
##--            cmd = cmd + " off"
    else:
        cmd = "could not decipher..."

    cmd_file ="/home/pi/.commands_in/{}.command.txt".format( time.time() )

    FH = open( cmd_file, "w" )
    FH.write( cmd )
    FH.close

    #   https://www.tutorialspoint.com/python/os_chmod.htm
    os.chmod( cmd_file, stat.S_IRWXU | stat.S_IRWXG )
    os.chmod( cmd_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH )


    #   stat.S_IREAD : Read by owner.
    #   stat.S_IWRITE : Write by owner.
    #   stat.S_IRUSR : Read by owner.
    #   stat.S_IWUSR : Write by owner.
    #   stat.S_IRGRP : Read by group.
    #   stat.S_IWGRP : Write by group.
    #   stat.S_IROTH : Read by others.
    #   stat.S_IWOTH : Write by others.
    #   stat.S_IXGRP : Execute by group.
    #   stat.S_IXUSR : Execute by owner.
    #   stat.S_IEXEC : Execute by owner.
    #   stat.S_IRWXU : Read, write, and execute by owner.
    #   stat.S_IRWXG : Read, write, and execute by group.
    #   stat.S_IRWXO : Read, write, and execute by others.
    #########################################################################------  os.chmod( cmd_file, stat.S_IRWXU | stat.S_IRWXG )
    #########################################################################------  os.chmod( cmd_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP )
    #########################################################################------  os.chmod( cmd_file, stat.S_IRWXU | stat.S_IRWXG )

    # NOTE: No permission for this... ???
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )
    # os.chown( cmd_file, 1000, 1000 )



#--    if 'phonenumber' in qs:
#--        name = qs.split('=')[1]
#--    else:
#--        name = 'No Name Provided'
    sendHeaders()
    sendPage(qs, cmd)

exit()







#	process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#	output,stderr = process.communicate()
#	status = process.poll()
#	print status
#	print output

# 1859  /home/pi/gpio_driver.py 18 lo
# 1860  ~/light_timer.py off




#        <TABLE>
#          <TR>
#          <TD ROWSPAN=3>
#          <IMG SRC="http://192.168.1.172/Deck_Lights_Mini.jpg">
#          </TD>
#          <TD>
#            <FONT SIZE=+5> &nbsp; &#8593; &nbsp;
#            <BR>
#            &nbsp; &#8595; &nbsp;
#          </TD>
#          <TD>
#
#          <!--   https://www.raspberrypi.org/forums/viewtopic.php?t=237543  -->
#          <form name="relayform_XXX" method="get" action="NEW.py">
#              <button class="button button1" type="submit" name="overhead" value="on"> &nbsp; ON &nbsp; </button>
#              <button class="button button2" type="submit" name="overhead" value="off"> &nbsp; OFF &nbsp; </button>
#              <br>
#              <button class="button button1" type="submit" name="surface" value="on"> &nbsp; ON &nbsp; </button>
#              <button class="button button2" type="submit" name="surface" value="off"> &nbsp; OFF &nbsp; </button>
#          </form>
#          </TD>
#          </TR>
#
#          <TD>
#	</TABLE>

