#!/bin/bash

#This populates the ARP table on the Red side with the Black side's RX port IP/MAC pair

RED_RX_IP="192.168.3.2"
RED_TX_IP="192.168.2.1"

BLACK_RX_IP="192.168.2.2"
BLACK_TX_IP="192.168.3.1"

BLACK_RX_MAC="10:4d:77:02:00:08"
BLACK_TX_MAC="10:4d:77:02:00:09"

RED_RX_MAC="10:4d:77:02:00:0a"
RED_TX_MAC="10:4d:77:02:00:0b"

RSYSLOG_IP="192.168.100.70"
RSYSLOG_MAC="d4:be:d9:63:91:e7"

TX_INTERFACE="enp23s0f1"
RX_INTERFACE="enp23s0f0"

#ARP TABLES
arp -s $BLACK_RX_IP $BLACK_RX_MAC
arp -s $BLACK_TX_IP $BLACK_TX_MAC

#RSYSLOG ARP
arp -s $RSYSLOG_IP $RSYSLOG_MAC

#SELINUX AND FIREWALLS
setenforce 0
service firewalld stop

#RP FILTERING OFF
echo "0" > /proc/sys/net/ipv4/conf/all/rp_filter
echo "0" > /proc/sys/net/ipv4/conf/default/rp_filter
echo "0" > /proc/sys/net/ipv4/conf/enp23s0f0/rp_filter
echo "0" > /proc/sys/net/ipv4/conf/enp23s0f1/rp_filter
echo "0" > /proc/sys/net/ipv4/conf/lo/rp_filter

#INTERFACE BUFFERS
ethtool -G enp23s0f0 tx 4096
ethtool -G enp23s0f0 rx 4096
ethtool -G enp23s0f1 tx 4096
ethtool -G enp23s0f1 rx 4096

#RETURN PATH ROUTES
ip route add $BLACK_RX_IP via $RED_TX_IP dev $TX_INTERFACE
