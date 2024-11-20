#!/bin/bash

# Editing this constantly is quite annoying. Just run this and then python the file you want to run
CURDIR=/home/xilinx/rfsoc-pydaq
sudo xauth add $(xauth -f ~xilinx/.Xauthority list|tail -1)
sudo -i DISPLAY=$DISPLAY