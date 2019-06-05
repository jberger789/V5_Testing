import re, os

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST_SDA', 'DD_TEST_SDB', 'HDPARM_SDA', 'HDPARM_SDB', 
	'IPERF_SERVER_2.2', 'IPERF_SERVER_3.2', 'IPERF_SERVER_200.20', 'IPERF_CLIENT_2.1', 'IPERF_CLIENT_200.20', 
	'IPERF_SERVER_200.50', 'IPERF_CLIENT_3.1', 'IPERF_CLIENT_200.50']

#########################################################

def ClearPastData():
	"""Clears out data from last test run"""

	unit_count = 1
	while os.path.exists("Unit_"+str(unit_count)):
		os.system("rm -r Unit_"+str(unit_count))
		unit_count += 1

#########################################################

def SplitLogFile():
	"""Splits up the messages from the log file by unit, side, and test"""

	#Open the log file to read from
	messages_file = open('test_messages', 'r')

	#Regular expression for determining which lines belong to which unit and side
	re_sideN = re.compile('(?P<side>('+SIDES[0]+')|('+SIDES[1]+'))-(?P<unit_num>\d+)')

	#Separate log messages into individual files for each test, organized by unit and side
	for line in messages_file:
		m = re_sideN.search(line)																	# Determine if a given log message
		if m:																						# came from a test unit
			#Deal with directories
			unit_dir_name = 'Unit_'+m.group('unit_num')												# Determine the directory name for this unit
			side_dir_name = unit_dir_name+'/'+m.group('side')										# Determine the directory name for this side		
			if not os.path.exists(unit_dir_name):													# Check whether the directory for the unit exists
				os.mkdir(unit_dir_name)																# If not, create it
			if not os.path.exists(side_dir_name):													# Check whether the directory for the side exists
				os.mkdir(side_dir_name)																# If not, create it
			#Separate data by test
			for tag in MESSAGE_TAGS:																# For each data tag, check
				tag_ind = line.find(tag)															# if the current log message
				if not tag_ind == -1:																# is for that test
					with open(side_dir_name+"/"+tag+".txt",'a') as f:								# If it is, open its file
						f.write(line[0:tag_ind-3-len(m.group('unit_num'))-len(m.group('side'))]		# and write the message to it
							+line[tag_ind+len(tag):])												# sans unit number/test tag

	#Close the log file
	messages_file.close()

#########################################################

def ParseTestData(unit_num, side, tag):
	raw_data = 'Unit_'+unit_num+'/'+side+'/'+tag+'.txt'
	with open(raw_data) as f:
		if tag == 'STREAM_C':
			re_stream_c = re.compile(r"""
				(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
				: 
				(?P<function>\b\w+\b)
				:\s+
				(?P<rate>\d+[.]\d+)
				\s+
				(?P<avg_t>\d+[.]\d+)
				\s+
				(?P<min_t>\d+[.]\d+)
				\s+
				(?P<max_t>\d+[.]\d+)
			""", re.VERBOSE)
			data_dict = {}
			for line in f:
				m = re_stream_c.search(line)
				if m:
					data_dict[m.group('function')+'_rate']  = float(m.group('rate'))
					data_dict[m.group('function')+'_avg_t'] = float(m.group('avg_t'))
					data_dict[m.group('function')+'_min_t'] = float(m.group('min_t'))
					data_dict[m.group('function')+'_max_t'] = float(m.group('max_t'))

			print(side+'-'+unit_num+" STREAM_C Data:")
			user_in = ""
			while user_in != "exit":
				user_in = input("What function would you data for to see?\n")
				if user_in != "exit":
					print("Best Rate : " + str(data_dict[user_in+"_rate"])+" MB/s")
					print("Avg Time  : " + str(data_dict[user_in+"_avg_t"])+" s")
					print("Min Time  : " + str(data_dict[user_in+"_min_t"])+" s")
					print("Max Time  : " + str(data_dict[user_in+"_max_t"])+" s")
		elif tag == 'IPMITOOL':
			re_ipmi = re.compile(r"""
				(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
				:\s+
				(?P<sensor>\b[\w.]+\b(\s\b\w+\b)?)
				\s+\|\s+
				(?P<value>\b[\w.]+\b)
				\s+\|\s+
				(?P<units>(\b[\w.]+\b[\s]+){0,2})
				\s*\|\s+
				(?P<status>\b[\w]+\b)
				\s*\|\s+
				(?P<lo_norec>(\d+[.]\d+)|(na))
				\s+\|\s+
				(?P<lo_crit>(\d+[.]\d+)|(na))
				\s+\|\s+
				(?P<lo_nocrit>(\d+[.]\d+)|(na))
				\s+\|\s+
				(?P<up_nocrit>(\d+[.]\d+)|(na))
				\s+\|\s+
				(?P<up_crit>(\d+[.]\d+)|(na))
				\s+\|\s+
				(?P<up_norec>(\d+[.]\d+)|(na))
				\s*$
			""", re.VERBOSE)
			data_dict = {}
			sensor_list = []
			for line in f:
				m = re_ipmi.search(line)
				if m:
					sensor_list.append(m.group('sensor'))
					data_dict[m.group('sensor')+'_value']  = (m.group('value'))
					data_dict[m.group('sensor')+'_units']  = (m.group('units'))
					data_dict[m.group('sensor')+'_status']  = (m.group('status'))
					data_dict[m.group('sensor')+'_lo_norec']  = (m.group('lo_norec'))
					data_dict[m.group('sensor')+'_lo_crit']  = (m.group('lo_crit'))
					data_dict[m.group('sensor')+'_lo_nocrit']  = (m.group('lo_nocrit'))
					data_dict[m.group('sensor')+'_up_norec']  = (m.group('up_norec'))
					data_dict[m.group('sensor')+'_up_crit']  = (m.group('up_crit'))
					data_dict[m.group('sensor')+'_up_nocrit']  = (m.group('up_nocrit'))

			print(side+'-'+unit_num+" IPMI Data:")
			#print(data_dict)
			user_in = ""
			while user_in != "exit":
				user_in = input("What sensor would you like to see the data for?\n")
				if user_in != "exit":
					print("Current Value : " + str(data_dict[user_in+"_value"])+" "+str(data_dict[user_in+"_units"]))
					print("Status        : " + str(data_dict[user_in+"_status"]))
					print("Low NoRec     : " + str(data_dict[user_in+"_lo_norec"])+" "+str(data_dict[user_in+"_units"]))
					print("Low Crit      : " + str(data_dict[user_in+"_lo_crit"])+" "+str(data_dict[user_in+"_units"]))
					print("Low NoCrit    : " + str(data_dict[user_in+"_lo_nocrit"])+" "+str(data_dict[user_in+"_units"]))
					print("High NoCrit   : " + str(data_dict[user_in+"_up_nocrit"])+" "+str(data_dict[user_in+"_units"]))
					print("High Crit     : " + str(data_dict[user_in+"_up_crit"])+" "+str(data_dict[user_in+"_units"]))
					print("High NoRec    : " + str(data_dict[user_in+"_up_norec"])+" "+str(data_dict[user_in+"_units"]))


ClearPastData()
SplitLogFile()
ParseTestData("1", "Black", "IPMITOOL")






