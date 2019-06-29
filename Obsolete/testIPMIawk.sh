#!/bin/bash


#!/bin/bash


tail -f /var/log/messages |
awk ' BEGIN { FS="|" }  { 
 high_temps["CPU Temp"] = 80;
 low_temps["CPU Temp"] = 5;
 	if (($1 ~ /IPMITOOL/) && ($2 < low_temps["$1"] && $6 != $9))
                {print $1,$2, "LOW";
                printf("kill -SIGUSR1 $(pgrep tester)") | "bash";}
 	else if (($1 ~ /IPMITOOL/) && ($2 > high_temps["$1"] && $6 != $9))
        {print $1,$2, "HIGH";
        print "$high_temps[$1]";
        printf("kill -SIGSTOP $(pgrep tester)") | "bash";}
 }
END { close("bash") }'



 #{ high_temps["CPU Temp"] = "80";
 #low_temps["CPU Temp"] = "5"; 