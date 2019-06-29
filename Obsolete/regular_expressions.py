import re
#Jun 14 17:03:03 red-1 TAMPER_STATUS: 2916,93,0
#Jun 14 17:03:08 black-1 TAMPER_STATUS: ees C

{
	"tag": "TAMPER_STATUS",
	"call": null,
	"re_string": [
		":\s+",
		"(",
		"((?P<val_1>\d+)",
		",",
		"(?P<val_2>\d+)",
		",",
		"(?P<val_3>\d+)",
		")",
		"|",
		"(?P<error>ees\sC)",
		")"
	],
	"key_tag": "",
	"data_info": {
		"val_1": "int",
		"val_2": "int",
		"val_3": "int",
		"error": "str",
	}
}

Jun 14 17:05:07 red-1 FIBER_FPGA_TEMP_2.5: #011DIODE rev1 Temp = 46 degrees C

{
	"tag": "FIBER_FPGA_TEMP",
	"call": null,
	"re_string":
		"(?P<FPGA_SIDE>[23]\.5)"
		":\s+",
		"#011DIODE\srev1\sTemp\s=\s(?P<Temp>\d+)\sdegrees\sC",
		"\s*$"
	,
	"key_tag": "",
	"data_info": {
		"FPGA_SIDE": "float",
		"Temp": "int",
	}
}




#Jun 14 17:03:16 black-1 DD_TEST_SDA: 1+0 records in
#Jun 14 17:03:16 black-1 DD_TEST_SDA: 1+0 records out
#Jun 14 17:03:16 black-1 DD_TEST_SDA: 1073741824 bytes (1.1 GB) copied, 2.90054 s, 370 MB/s

{
	"tag": "DD_TEST",
	"call": null,
	"re_string": [
		"_(?P<drive>SD[AB])",
		":\\s+",
		"(((?P<records_in>[\\d]+[+][\\d]+)\\srecords\\sin$)",
		"|",
		"((?P<records_out>[\\d]+[+][\\d]+)\\srecords\\sout$)",
		"|",
		"((?P<bytes_copied>\\b[\\d]+\\b).*\\(.+\\).*(?P<duration>\\b\\d+[.]\\d+)\\s+s,\\s*(?P<rate>\\d+([.]\\d*)?)))"
	],
	"key_tag": "drive",
	"data_info": {
		"drive": "str",
		"records_in": "int",
		"records_out": "int",
		"bytes_copied": "int",
		"duration": "float",
		"rate": "float"
	}
}

# Jun 14 17:04:46 red-1 USB_PASSMARK: /proc/bus/usb/devices not found - trying /sys
# Jun 14 17:04:46 red-1 USB_PASSMARK: Found USB3 plug : firmware: 2.5 PMU34PLIYK speed: 480 at 1:4
# Jun 14 17:04:46 red-1 USB_PASSMARK: Connecting [Serial: PMU34PLIYK]
# Jun 14 17:04:46 red-1 USB_PASSMARK: Connecting [Serial: PMU34PLIYK]
# Jun 14 17:04:46 red-1 USB_PASSMARK: Testing plug PMU34PLIYK starts in 5 seconds
# Jun 14 17:04:46 red-1 USB_PASSMARK: Loopback testing plug PMU34PLIYK
# Jun 14 17:04:46 red-1 USB_PASSMARK: libusb_control_transfer failed -7
# Jun 14 17:04:46 red-1 USB_PASSMARK: Set USB3 error counter config
# Jun 14 17:04:46 red-1 USB_PASSMARK: libusb_control_transfer failed -7
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 100 - Bytes sent: 6553600 - Bytes received 6553600
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 200 - Bytes sent: 13107200 - Bytes received 13107200
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 300 - Bytes sent: 19660800 - Bytes received 19660800
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 400 - Bytes sent: 26214400 - Bytes received 26214400
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 500 - Bytes sent: 32768000 - Bytes received 32768000
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 600 - Bytes sent: 39321600 - Bytes received 39321600
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 700 - Bytes sent: 45875200 - Bytes received 45875200
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 800 - Bytes sent: 52428800 - Bytes received 52428800
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 900 - Bytes sent: 58982400 - Bytes received 58982400
# Jun 14 17:04:46 red-1 USB_PASSMARK: Error Count: 0 - Packets sent: 1000 - Bytes sent: 65536000 - Bytes received 65536000
# Jun 14 17:04:46 red-1 USB_PASSMARK: libusb_control_transfer failed -7
# Jun 14 17:04:46 red-1 USB_PASSMARK: Benchmarking plug PMU34PLIYK
# Jun 14 17:04:46 red-1 USB_PASSMARK: Connecting [Serial: PMU34PLIYK]
# Jun 14 17:04:46 red-1 USB_PASSMARK: Connecting [Serial: PMU34PLIYK]
# Jun 14 17:04:46 red-1 USB_PASSMARK: Turn LCD display off
# Jun 14 17:04:46 red-1 USB_PASSMARK: Read benchmark
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 64/1024 - Transfer rate: 358.80 Mbit/s (Max rate: 358.80 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 128/1024 - Transfer rate: 358.84 Mbit/s (Max rate: 358.84 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 192/1024 - Transfer rate: 359.54 Mbit/s (Max rate: 359.54 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 256/1024 - Transfer rate: 360.11 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 320/1024 - Transfer rate: 359.79 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 384/1024 - Transfer rate: 359.09 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 448/1024 - Transfer rate: 359.78 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 512/1024 - Transfer rate: 358.73 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 576/1024 - Transfer rate: 359.35 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 640/1024 - Transfer rate: 359.25 Mbit/s (Max rate: 360.11 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 704/1024 - Transfer rate: 360.31 Mbit/s (Max rate: 360.31 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 768/1024 - Transfer rate: 359.13 Mbit/s (Max rate: 360.31 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 832/1024 - Transfer rate: 361.17 Mbit/s (Max rate: 361.17 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 896/1024 - Transfer rate: 359.62 Mbit/s (Max rate: 361.17 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 960/1024 - Transfer rate: 359.61 Mbit/s (Max rate: 361.17 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 1024/1024 - Transfer rate: 359.70 Mbit/s (Max rate: 361.17 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Turn LCD display off
# Jun 14 17:04:46 red-1 USB_PASSMARK: Write benchmark
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 64/1024 - Transfer rate: 325.26 Mbit/s (Max rate: 325.26 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 128/1024 - Transfer rate: 325.37 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 192/1024 - Transfer rate: 324.02 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 256/1024 - Transfer rate: 325.24 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 320/1024 - Transfer rate: 324.60 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 384/1024 - Transfer rate: 324.02 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 448/1024 - Transfer rate: 324.43 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 512/1024 - Transfer rate: 324.65 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 576/1024 - Transfer rate: 325.10 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 640/1024 - Transfer rate: 324.45 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 704/1024 - Transfer rate: 323.47 Mbit/s (Max rate: 325.37 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 768/1024 - Transfer rate: 332.95 Mbit/s (Max rate: 332.95 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 832/1024 - Transfer rate: 339.96 Mbit/s (Max rate: 339.96 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 896/1024 - Transfer rate: 331.21 Mbit/s (Max rate: 339.96 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 960/1024 - Transfer rate: 332.27 Mbit/s (Max rate: 339.96 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Transfer count 1024/1024 - Transfer rate: 334.10 Mbit/s (Max rate: 339.96 Mbit/s)
# Jun 14 17:04:46 red-1 USB_PASSMARK: Turn LCD display on
# Jun 14 17:04:46 red-1 USB_PASSMARK_RC: 0 0



{
	"tag": "USB_PASSMARK",
	"call": null,
	"re_string": [
		":\\s+",
		"(",
		"(",
		"(?P<benchmark_type>((Read)|(Write)))\\sbenchmark\\s*$",
		")",
		"|",
		"(",
		"Set\\sUSB3\\s(?P<benchmark_type>error\\scounter)\\sconfig\\s*$",
		")",
		"|",
		"(",
		"Transfer\\scount\\s(?P<transfer_count>\\d+)/1024",
		"\\s-\\s",
		"Transfer\\srate:\\s(?P<transfer_rate>\\d+\\.\\d+)\\sMbits/s\\s",
		"\\(Max\\srate:\\s(?P<max_rate>\\d+\\.\\d+)\\sMbit/s\\)\\s*$",
		")",
		"|",
		"(",
		"Error\\scount:\\s(?P<error_count>\\d+)",
		"\\s-\\s",
		"Packets\\ssent:\\s(?P<packets_sent>\\d+)",
		"\\s-\\s",
		"Bytes\\ssent:\\s(?P<bytes_sent>\\d+)",
		"\\s-\\s",
		"Bytes\\sreceived\\s(?P<bytes_received>\\d+)",
		")",
		")",
	],
	"key_tag": "benchmark_type",
	"data_info": {
		"benchmark_type": "str",
		"transfer_count": "int",
		"transfer_rate": "float",
		"max_rate": "float",
		"packets_sent": "int",
		"bytes_sent": "int",
		"bytes_received": "int"
	}
}
