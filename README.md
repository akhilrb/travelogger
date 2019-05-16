# travelogger

TraveLogger is a Raspberry Pi (Zero) based configurable timelapse recorder written in Python.
It is compatible with RPi camera modules as well as USB cameras.  
Just set the input-time, the output-time, and the output frame-rate, and **travelogger** will do everything else on its own.

---

## Dependencies and Packages

### Debian

For RPi camera modules, the frames are captured using `raspistill`, and that for USB cameras using `streamer`.  
Install them using `sudo apt-get install raspistill streamer`

Next, a few more packages need to be installed for stitching the frames together. [This article](https://www.raspberrypi.org/forums/viewtopic.php?t=72435) by *phamthanhnam* on Raspberry Pi Forums advised that the OpenMAX plugin in gstreamer supports the Raspberry Pi GPU and can stitch the images much faster with far less CPU utilisation.

```
sudo sh -c 'echo deb http://vontaene.de/raspbian-updates/ . main >> /etc/apt/sources.list'

sudo apt-get update

sudo apt-get install libgstreamer1.0-0 liborc-0.4-0 gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 gstreamer1.0-alsa gstreamer1.0-omx gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-pulseaudio gstreamer1.0-tools gstreamer1.0-x libgstreamer-plugins-bad1.0-0 libgstreamer-plugins-base1.0-0
```

### Python

The script uses  
`argparse` for conventional argument parsing, and  
`psutil` for getting available disk space

Install these using  
`pip3 install -u argparse psutil`

---

## Usage

For a quick test, run:  
```
python3 recorder.py
```

A new folder with the script's runtime-stamp will be created and all frames and the stitched video will be stored in it.  

### Configurables

|Argument|Short|Default Value|Description|
|:---:|:---:|:---:|:---:|
|--image-prefix|-ip|timelapse|prefix for image name|
|--image-extension|-ie|jpeg|image extension|
|--folder-prefix|-fp|timelapse|prefix for folder name|
|--frame-size|-fs|1280x720|resolution of captured frame|
|--input-time|-it|1800|recording input time|
|--output-time|-ot|60|recording output time|
|--total-frames|-tf|1440|total frames|
|--out-frame-rate|-ofps|24|output fps|
|--force-usb|-fu|-|force input from a video device|

---

## Examples

```
python3 recorder.py -fp ../timelapse -ip sunset -fs 640x480 -it 3600 -ot 30
```

sets and displays the following configuration:

```
In:	0.200 FPS	Out:	24.000 FPS
Total recording time = 1 hr 00 min 0.00 sec
Total timelapse time = 0 hr 00 min 30.00 sec
Factor (In : Out)    = 120.00
Estimated disk usage = 70.3125 MB (720 frames)
Avaliable disk space = 6745.21875 MB

```

and stores all files with the prefix `sunset` in a folder named `timelapse` outside the parent directory.

---

### Forcing total frames

```
python3 recorder.py -fp timelapse -ip sunset -fs 640x480 -tf 500 -ofps 30
```

sets and displays the following configuration:

```
In:	0.278 FPS	Out:	8.333 FPS
Total recording time = 0 hr 30 min 0.00 sec
Total timelapse time = 0 hr 00 min 60.00 sec
Factor (In : Out)    = 30.00
Estimated disk usage = 48.828125 MB (500 frames)
Avaliable disk space = 6743.77734375 MB

```

Notice that the set output frame-rate value was over-ridden with the set number of frames.  

---

### Errors

`* failed to open vchiq instance`  
is a known error prompt which is encountered while trying to use the GPU for stitching the images.  
It is probable that the user running travelogger is not in the **video** group.

Add the user to the **video** group using:  
`sudo usermod -aG video $(whoami)`

It is probably better from a perspective of security to make a separate user with video permissions and run travelogger through that user.
