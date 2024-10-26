#!/bin/bash

# this is awkward because Pynq needs root access,
# but in addition it installs its own version of Python
# in a location that only is sourced on login shells,
# so we have to do sudo -i, which means we also lose
# our current directory.

#Assuming this is where pydaq is stored, allows running from anywhere
CURDIR=/home/xilinx/rfsoc-pydaq # `pwd`
sudo xauth add $(xauth -f ~xilinx/.Xauthority list|tail -1)
sudo -i DISPLAY=$DISPLAY python3 $CURDIR/app.py  -c "biquad"
