#!/bin/bash

# This script will grep red-side results from file in order of test (Stress-ng, DD, IPERF, IPMI Tool)

rm -rf RedResults.txt

declare -a label
label[0]="STRESS_NG_RESULTS"
label[1]="DD_RESULTS"
label[2]="STREAM_C"
label[3]="IPERF"
label[4]="IPMI"

LABELSIZE=5

for (( i=0;i<5;i++))
do
	echo '
	====================================================================================
	' >> RedResults.txt
	echo ${label[$i]} >> RedResults.txt
	cat messages.txt | grep ${label[$i]} | tee -a RedResults.txt

done

#for i in ${label[@]}
#	echo $i
#done


 
