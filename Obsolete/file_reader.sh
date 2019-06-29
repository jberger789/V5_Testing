#!/bin/bash
input="test_file.txt"
while true
do
 	if read -r line
	then	
		echo "$line"
	fi
done < "$input"
