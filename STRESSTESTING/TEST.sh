#!/bin/bash

# This script will grep red-side results from file in order of test (Stress-ng, DD, IPERF, IPMI Tool)

# rm -rf RedResults.txt

# Arrays representing different tests with different tags to the rsyslog server; can easily be added or taken away
declare -a label
label[0]="stress-ng"
label[1]="DD_TEST_SDB"
label[2]="HDPARM_SDA"
label[3]="STREAM_C"
label[4]="IPERF_CLIENT"
label[5]="IPERF_SERVER"
label[6]="IPMITOOL"


# Loop to parse data based on type of test determined by the array
for i in ${label[@]}
do
	echo '
	====================================================================================
	' >> RedResults.txt
	echo $i >> RedResults.txt
	cat messages_test_run_5 | grep red-1\ $i | tee -a $i.txt
	#rm -rf $i.txt
done


 
