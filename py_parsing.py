import re, os

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST_SDA', 'DD_TEST_SDB', 'HDPARM_SDA', 'HDPARM_SDB', 
	'IPERF_SERVER_2.2', 'IPERF_SERVER_3.2', 'IPERF_SERVER_200.20', 'IPERF_CLIENT_2.1', 'IPERF_CLIENT_200.20', 
	'IPERF_SERVER_200.50', 'IPERF_CLIENT_3.1', 'IPERF_CLIENT_200.50']

#Open the log file to read from
messages_file = open('test_messages', 'r')

#Clear out data from last test run
unit_count = 1
while os.path.exists("Unit_"+str(unit_count)):
	os.system("rm -r Unit_"+str(unit_count))
	unit_count += 1

#Regular expression for parsing out which lines belong to which unit and side
re_sideN = re.compile('(?P<side>('+SIDES[0]+')|('+SIDES[1]+'))-(?P<unit_num>\d+)')

#Separate log messages into individual files for each test, organized by unit and side
for line in messages_file:
	m = re_sideN.search(line)																	# Determine if a given log message
	if m:																						# came from a test unit
		#Deal with directories
		unit_dir_name = 'Unit_'+m.group('unit_num')												# Determine the directory name for this unit
		side_dir_name = unit_dir_name + '/' m.group('side')										# Determine the directory name for this side		
		if not os.path.exists(unit_dir_name):													# Check whether the directory for the unit exists
			os.mkdir(unit_dir_name)																# If not, create it
		if not os.path.exists(side_dir_name):													# Check whether the directory for the side exists
			os.mkdir(side_dir_name)																# If not, create it
		#Separate data by test
		for tag in MESSAGE_TAGS:																# For each data tag, check
			tag_ind = line.find(tag)															# if the current log message
			if not tag_ind == -1:																# is for that test
				with open(dirName+"/"+tag+".txt",'a') as f:										# If it is, open its file
					f.write(line[0:tag_ind-3-len(m.group('unit_num'))-len(m.group('side'))]		# and write the message to it
						+line[tag_ind+len(tag):])												# sans unit number/test tag


#Close the log file
close(messages_file)