#!/bin/python

# grepping iperf results
cat messages.txt | grep -E "black-1 root: \["'[ ]*'.*\]'.*'[ ]'[[:alum]]+ | tee iperf.txt
