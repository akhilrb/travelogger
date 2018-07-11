import os
import subprocess
import time
import sys
import shelve
import argparse
import datetime

parser = argparse.ArgumentParser(description='Record a timelapse')
parser.add_argument('--frame-size', '-fs', dest='frameSize',type=str, action='store', default='1280x720', help='resolution')
parser.add_argument('--image-prefix', '-ip', dest='imagePrefix',type=str, action='store', default='timelapse', help='name prefix')
parser.add_argument('--image-extension', '-ie', dest='imageExtension',type=str, action='store', default='jpeg', help='extension')
# output fps manual configuration
parser.add_argument('--total-frames', '-tf', dest='totalFrames',type=str, action='store', default='1440', help='total frames')
parser.add_argument('--in-frame-rate', '-ifps', dest='ifps',type=str, action='store', default='0.8', help='input fps')
parser.add_argument('--out-frame-rate', '-ofps', dest='ofps',type=str, action='store', default='24', help='output fps')
settings = parser.parse_args()

FRAME_SIZE = settings.frameSize
IMAGE_PREFIX = settings.imagePrefix
FOLDER_PREFIX = settings.folderPrefix
IMAGE_EXTENSION = "." + settings.imageExtension
TOTAL_FRAMES = settings.totalFrames
IFPS = settings.ifps
OFPS = settings.ofps
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

def prepareFolderVariables():
    global IMAGE_PREFIX, FOLDER_PREFIX
    tt = datetime.datetime.today().timetuple()
    folderName = str(tt.tm_year) + str(tt.tm_mon) + str(tt.tm_mday) + str(tt.tm_hour) + str(tt.tm_min) + str(tt.tm_sec)
    FOLDER_PREFIX += folderName
    cmdLineWaitUntilExecution("mkdir " + FOLDER_PREFIX)

def setupCamera():
    global captureCommand
    
    zeros = ""
    for x in range(ZERO_DIGITS):
        zeros+="0"

    params = cmdLine("vcgencmd get_camera")
    if(str(params).find("supported=1 detected=1") != -1):
        # Camera Module
        print(GREEN+"Camera module detected"+NC)
        # hardcode for now, will update soon
        OUTPUT_TIME = 3600000
        DELAY = 2500
        captureCommand = "raspistill -o " + FOLDER_PREFIX + "/" +IMAGE_PREFIX + "%0"+ZERO_DIGITS+"d" + IMAGE_EXTENSION + " -tl " + DELAY + " -t " + OUTPUT_TIME
    elif(str(params).find("supported=1 detected=0") != -1):
        # USB Camera
        print(GREEN+"USB camera detected"+NC)
        captureCommand = "streamer -t " + TOTAL_FRAMES + " -r " + IFPS + " -s " + FRAME_SIZE + " -o " + FOLDER_PREFIX + "/" + IMAGE_PREFIX + zeros + IMAGE_EXTENSION
    else:
        print(RED+"No grabber device detected!"+NC)
        sys.exit()

prepareFolderVariables()
setupCamera()

try:
    cmdLineWaitUntilExecution(captureCommand)
except KeyboardInterrupt as e:
    print("Recording interrupted")
try:
    startTime = time.perf_counter()
    print(YELLOW+"Stitching images, please wait..."+NC)
    cmd1 = "gst-launch-1.0 multifilesrc location=" + FOLDER_PREFIX + "/" + IMAGE_PREFIX + "%0" + str(ZERO_DIGITS) + "d.jpeg "
    cmd2 = "index=1 caps="+"image/jpeg,framerate="+OFPS+"/1"+" ! jpegdec ! omxh264enc ! avimux ! filesink location="+FOLDER_PREFIX+"/"+IMAGE_PREFIX+".avi"
    cmdLineWaitUntilExecution(cmd1+cmd2)
    endTime = time.perf_counter()
    print(GREEN+"Finished "+NC+"(" + str(endTime - startTime) + " seconds)")
except KeyboardInterrupt as e:
    print("Saving interrupted")
