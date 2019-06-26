#!/bin/bash

#network config
/root/ARP_BLACK.sh
logger network config complete


#mount USB
mount /dev/sdb1 /mnt
logger USB mount complete


SIDE=$
logger test start

#start iperf servers
#iperf -s -u -B 192.168.2.2 -i 5 | logger -t IPERF_SERVER_2.2 & 
#logger 192.168.2.2 iperf server up on fiber
#iperf -s -u -B 192.168.200.50 -i 5 | logger -t IPERF_SERVER_200.50 &
#logger 192.168.200.50 iperf server up on eno2


#IPMItool temperature reading
ipmitool sensor | logger -t IPMITOOL

#stress-ng cpu test
stress-ng -c 6 --metrics-brief --perf -t 10 --syslog

#stream_c.exe ram test
/root/STREAM/stream_c.exe | logger -t STREAM_C

#dd test - sda write
dd if=/dev/zero of=/tmp/test.dat bs=1G count=1 oflag=direct 2>&1 | logger -t DD_TEST_SDA 

#dd test - sdb write
dd if=/dev/zero of=/mnt/test.dat bs=250M count=1 oflag=direct 2>&1 | logger -t DD_TEST_SDB

#hdparm test - sda read
hdparm -Tt /dev/sda | logger -t HDPARM_SDA

#hdparm test - sdb read
hdparm -Tt /dev/sdb | logger -t HDPARM_SDB

#iperf - fiber
ssh root@192.168.200.20 'iperf -s -u -B 192.168.3.2 -i 5 > logger -t IPERF_SERVER_3.2 &' &
#ssh root@192.168.200.20 iperf -B 192.168.2.1 -c 192.168.2.2 -u -b 10g -t 20 -i 5 -P 1 | logger -t
iperf -B 192.168.3.1 -c 192.168.3.2 -u -b 10g -t 20 -i 5 -P 1 | logger -t IPERF_CLIENT_3.1

#iperf - eno2 ethernet B to R
ssh root@192.168.200.20 'iperf -s -u -B 192.168.200.20 -i 5 > logger -t IPERF_SERVER_200.20 &'
iperf -B 192.168.200.50 -c 192.168.200.20 -u -b 10g -t 20 -i 5 -P 1 | logger -t IPERF_CLIENT_200.50

#IPMItool temperature reading
ipmitool sensor | logger -t IPMITOOL

logger test complete
