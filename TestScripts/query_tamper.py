#!/bin/python

import serial
import os

s=serial.Serial(port='/dev/ttyUSB0',baudrate=9600,timeout=1)
s.write('GET STATUS\r\n')
s.readline()
status=s.readline()
os.system("echo %s" % status)

#s.write('RESET COUNTER\r\n')

