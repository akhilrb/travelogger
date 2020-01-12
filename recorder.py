#!/usr/bin/python3
import os
import subprocess
import time
import sys
import shelve
import argparse
import datetime
import psutil

parser = argparse.ArgumentParser(description='Record a timelapse')
parser.add_argument('--image-prefix', '-ip', dest='imagePrefix',type=str, action='store', default='timelapse', help='name prefix')
parser.add_argument('--image-extension', '-ie', dest='imageExtension',type=str, action='store', default='jpeg', help='extension')
parser.add_argument('--folder-prefix', '-fp', dest='folderPrefix',type=str, action='store', default='timelapse', help='folder prefix')
parser.add_argument('--frame-size', '-fs', dest='frameSize',type=str, action='store', default='1280x720', help='resolution')
parser.add_argument('--input-time', '-it', dest='inputTime',type=str, action='store', default='1800', help='recording input time')
parser.add_argument('--output-time', '-ot', dest='outputTime',type=str, action='store', default='60', help='recording output time')
# output fps manual configuration
parser.add_argument('--total-frames', '-tf', dest='totalFrames',type=str, action='store', default='-1', help='total frames')
parser.add_argument('--out-frame-rate', '-ofps', dest='ofps',type=str, action='store', default='24', help='output fps')
# cheap hack for headless installations
parser.add_argument('--force-usb', '-fu', dest='fu', action='store_true', help='force input from USB video device')
settings = parser.parse_args()

CONFIG_FILE_EXTENSION = ".cgp"
FRAME_SIZE = settings.frameSize
IMAGE_PREFIX = settings.imagePrefix
FOLDER_PREFIX = settings.folderPrefix
OUTPUT_TIME = settings.outputTime
INPUT_TIME = settings.inputTime
IMAGE_EXTENSION = "." + settings.imageExtension
OFPS = settings.ofps

# take precedence of explicitly mentioned total frames over ofps
if(settings.totalFrames != '-1'):
    TOTAL_FRAMES = settings.totalFrames
    OFPS = str(float(TOTAL_FRAMES)/float(OUTPUT_TIME))
else:
    TOTAL_FRAMES = str(int(float(OUTPUT_TIME)*float(OFPS)))

IFPS = str(float(TOTAL_FRAMES)/float(INPUT_TIME))
DELAY = str(float(1)/float(IFPS))
ZERO_DIGITS = len(TOTAL_FRAMES)

captureCommand = ""
BLUE =  '\033[0;38;2;32;128;192m'
RED =   '\033[0;38;2;255;32;32m'
GREEN = '\033[0;38;2;0;192;0m'
YELLOW ='\033[0;38;2;192;192;0m'
NC =    '\033[0m'

def cmdLine(cmd):
    process = subprocess.Popen(args = cmd, stdout = subprocess.PIPE, universal_newlines = True, shell = True)
    return process.communicate()[0]

def cmdLineWaitUntilExecution(cmd):
    process = subprocess.call(args = cmd, stdout = subprocess.PIPE, universal_newlines = True, shell = True)
    #return process.communicate()[0]

def secsToHours(secs):
    mm, ss = divmod(secs, 60)
    hh, mm = divmod(mm, 60)
    return "%d hr %02d min %02.2f sec" % (hh, mm, ss)

def printSpecifications():
    # print recording details
    '''
    for which in range(1,len(str(settings).split(', '))):
        print(str(settings).split(', ')[which])
    '''
    print("===")
    print("In:\t%.3f FPS\tOut:\t%.3f FPS" %(float(IFPS),float(OFPS)))
    print("Total recording time = " + secsToHours(float(TOTAL_FRAMES)/float(IFPS)))
    print("Total timelapse time = " + secsToHours(float(TOTAL_FRAMES)/float(OFPS)))
    print("Factor (In : Out)    = %.2f" % (float(OFPS)/float(IFPS)))
    # every image is almost 100 KB, although this depends on the size of the frame
    print("Estimated disk usage = %s MB (%d frames)" % (str(float(TOTAL_FRAMES)*100/1024),int(TOTAL_FRAMES)))
    print("Avaliable disk space = " + str((psutil.disk_usage("/")[2])/1024/1024) + " MB")
    print("===")

def prepareFolderVariables():
    # prepare folder variables to be used for the entire run
    global IMAGE_PREFIX, FOLDER_PREFIX
    FOLDER_PREFIX += datetime.datetime.today().strftime("%Y.%m.%d--%H.%M.%S")
    cmdLineWaitUntilExecution("mkdir " + FOLDER_PREFIX)

def setupCamera():
    # detect camera and prepare capture command accordingly
    global captureCommand
    zeros = ""
    for x in range(ZERO_DIGITS):
        zeros+="0"

    params = cmdLine("vcgencmd get_camera")
    if(str(params).find("supported=1 detected=1") != -1):
        # Camera Module
        print(GREEN+"Camera module detected"+NC)
        OUTPUT_TIME = 3600000
        DELAY = 2500
        captureCommand = "raspistill -o " + FOLDER_PREFIX + "/" +IMAGE_PREFIX + "%0"+ZERO_DIGITS+"d" + IMAGE_EXTENSION + " -tl " + DELAY + " -t " + OUTPUT_TIME
    elif(str(params).find("supported=1 detected=0") != -1):
        # USB Camera
        print(GREEN+"USB camera deteced"+NC)
        captureCommand = "streamer -t " + TOTAL_FRAMES + " -r " + IFPS + " -s " + FRAME_SIZE + " -o " + FOLDER_PREFIX + "/" + IMAGE_PREFIX + zeros + IMAGE_EXTENSION
    # Either the cameras are not connected, or there is no x-session available.
    # This might be a headless install
    else:
        print(RED+"No grabber device detected!"+NC)
        # Try to look for video devices in the /dev directory
        if(settings.fu):
            forcedDevice = cmdLine("ls /dev | grep video")
            if(forcedDevice == ""):
                print(RED+"Failed to recognize any input video devices!"+NC)
                sys.exit()
            print(YELLOW+"Forcing input from /dev/"+NC+forcedDevice)
            captureCommand = "streamer -t " + TOTAL_FRAMES + " -r " + IFPS + " -s " + FRAME_SIZE + " -o " + FOLDER_PREFIX + "/" + IMAGE_PREFIX + zeros + IMAGE_EXTENSION
        else:
            print(RED+"Exiting"+NC)
            sys.exit()

#configPrompt()

prepareFolderVariables()
printSpecifications()
setupCamera()

try:
    print(BLUE+"Now recording"+NC)
    startTime = time.perf_counter()
    cmdLineWaitUntilExecution(captureCommand)
    endTime = time.perf_counter()
    print(GREEN+"Finished recording"+NC+"(%s)" % secsToHours(endTime - startTime))
except KeyboardInterrupt as e:
    print(YELLOW+"Recording interrupted"+NC)
try:
    startTime = time.perf_counter()
    print(BLUE+"Stitching images, please wait..."+NC)
    cmd1 = "gst-launch-1.0 multifilesrc location=" + FOLDER_PREFIX + "/" + IMAGE_PREFIX + "%0" + str(ZERO_DIGITS) + "d.jpeg "
    cmd2 = "index=1 caps="+"image/jpeg,framerate="+OFPS+"/1"+" ! jpegdec ! omxh264enc ! avimux ! filesink location="+FOLDER_PREFIX+"/mov_"+FOLDER_PREFIX+".avi"
    cmdLineWaitUntilExecution(cmd1+cmd2)
    endTime = time.perf_counter()
    print(GREEN+"Finished "+NC+"(%s)" % secsToHours(endTime - startTime))
except KeyboardInterrupt as e:
    print(YELLOW+"Stitching interrupted. Couldn't save video."+NC)
