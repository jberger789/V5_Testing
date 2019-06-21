#!/bin/bash

# This script will grep red-side results from file in order of test (Stress-ng, DD, IPERF, IPMI Tool)

rm -rf REDCLEAN.txt
rm -rf BLACKCLEAN.txt
touch REDCLEAN.txt
touch BLACKCLEAN.txt


# Arrays representing different tests with different tags to the rsyslog server; can easily be added or taken away
declare -a label
label[0]="STRESS_NG"
label[1]="DD_TEST"
label[2]="HDPARM"
label[3]="STREAM_C"
label[4]="IPERF"
label[5]="USB_PASSMARK"
label[6]="IPMITOOL"
label[7]="TAMPER_STATUS"
label[8]="FIBER_FPGA_TEMP"




# Loop to parse data based on type of test determined by the array
msg_file=$1
for i in ${label[@]}
do
	grep "red-1 $i" "$msg_file" >> REDCLEAN.txt
	grep "black-1 $i" "$msg_file" >> BLACKCLEAN.txt
done

