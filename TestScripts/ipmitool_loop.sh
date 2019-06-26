#!/bin/bash
i=0
while true;
do
#IPMItool temperature reading
ipmitool sensor 2>&1 | logger -t IPMITOOL
wait $!

/root/diodev1_03/diode querytemp 192.168.2.2 192.168.2.5 2>&1 | logger -t FIBER_FPGA_TEMP_2.5
wait $!

/root/diodev1_03/diode querytemp 192.168.3.1 192.168.3.5 2>&1 | logger -t FIBER_FPGA_TEMP_3.5
wait $!
if (($i%10 == 0))
then
	/root/query_tamper.py 2>&1 | logger -t TAMPER_STATUS
	wait $!
fi

((i++))
sleep 10
done
