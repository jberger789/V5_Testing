#!/bin/bash

#IPMITOOL.txt
#awk '{print $1, ($2>$3)?0:($2<$3)?1:2}' file3
#i="na"
#2="0x4"
#3="0x1"

awk 'BEGIN { FS="|" } {
	if ($2 < $6 && $6 != $9)
		print $1,$2, "LOW";
else if ($2 > $9 && $6 != $9)
	print $1,$2, "HIGH";
}' IPMITOOL.txt

#awk 'BEGIN { FS="|"; } { print $2; }' IPMITOOL.txt
