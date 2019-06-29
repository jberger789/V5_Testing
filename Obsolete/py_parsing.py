import re, os

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST_SDA', 'DD_TEST_SDB', 'HDPARM_SDA', 'HDPARM_SDB', 
	'IPERF_SERVER_2.2', 'IPERF_SERVER_3.2', 'IPERF_SERVER_200.20', 'IPERF_CLIENT_2.1', 'IPERF_CLIENT_200.20', 
	'IPERF_SERVER_200.50', 'IPERF_CLIENT_3.1', 'IPERF_CLIENT_200.50']

IPMI_OUTPUT = ['value','units','status','lo_norec','lo_crit','lo_nocrit','up_nocrit','up_crit','up_norec']
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

def ParseTestData(unit_num, side, tag, data_dict):
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
					for label in IPMI_OUTPUT:
						data_dict[m.group('sensor')+'_'+label]  = (m.group(label))
					"""	
					data_dict[m.group('sensor')+'_value']  = (m.group('value'))
					data_dict[m.group('sensor')+'_units']  = (m.group('units'))
					data_dict[m.group('sensor')+'_status']  = (m.group('status'))
					data_dict[m.group('sensor')+'_lo_norec']  = (m.group('lo_norec'))
					data_dict[m.group('sensor')+'_lo_crit']  = (m.group('lo_crit'))
					data_dict[m.group('sensor')+'_lo_nocrit']  = (m.group('lo_nocrit'))
					data_dict[m.group('sensor')+'_up_nocrit']  = (m.group('up_nocrit'))
					data_dict[m.group('sensor')+'_up_crit']  = (m.group('up_crit'))
					data_dict[m.group('sensor')+'_up_norec']  = (m.group('up_norec'))
					"""

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

		elif ((tag == 'DD_TEST_SDB') or (tag == 'DD_TEST_SDA')):
			re_dd_test = re.compile(r"""
				(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
				:\s+
				(
				(?P<records_in>[\d]+[+][\d]+)
				|
				(?P<records_out>[\d]+[+][\d]+)
				|
				((?P<bytes_copied>\b[\d]+\b).*\(.+\).*(?P<duration>\b\d+[.]\d+)\s+s,\s*(?P<rate>\d+([.]\d*)?))
				)
			""", re.VERBOSE)
			#data_dict = {}
			for line in f:
				m = re_dd_test.search(line)
				dd_groups = ['records_in','records_out','bytes_copied','duration','rate']
				if m:
					for g in dd_groups:
						if (m.group(g)):
							data_dict[tag+'_'+g] = (m.group(g))

			#print(data_dict)
			print(side+'-'+unit_num+" DD Data:")
			user_in = ""
			while user_in != "exit":
				user_in = input("What device?\n")
				if user_in != "exit":
					print("Took "+str(data_dict["DD_TEST_"+user_in+"_duration"])+" s to copy "
						+str(data_dict["DD_TEST_"+user_in+"_bytes_copied"])+" bytes\nat a rate of "
						+str(data_dict["DD_TEST_"+user_in+"_rate"])+" MB/s")

		elif tag == 'stress-ng':
			re_stress_ng = re.compile(r"""
				(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
				:.*\s+
				(?P<count>\d+(,\d+)*)
				\s+
				(?P<variable>(\s?\b\w+\b)+)
				\s+
				(?P<rate>\d+[.]\d+)
				\s+
				(?P<units>[MBK]?/sec)
				\s*
				([(]\s*(?P<extra>.*)[)])?
				\s*$
			""", re.VERBOSE)
			#data_dict = {}
			stress_ng_groups = ['count','variable','rate','units','extra']
			for line in f:
				m = re_stress_ng.search(line)
				if m:
					for g in stress_ng_groups:
						if g != 'variable':
							data_dict[m.group('variable')+'_'+g]  = (m.group(g))
					"""	
					data_dict[m.group('sensor')+'_value']  = (m.group('value'))
					data_dict[m.group('sensor')+'_units']  = (m.group('units'))
					data_dict[m.group('sensor')+'_status']  = (m.group('status'))
					data_dict[m.group('sensor')+'_lo_norec']  = (m.group('lo_norec'))
					data_dict[m.group('sensor')+'_lo_crit']  = (m.group('lo_crit'))
					data_dict[m.group('sensor')+'_lo_nocrit']  = (m.group('lo_nocrit'))
					data_dict[m.group('sensor')+'_up_nocrit']  = (m.group('up_nocrit'))
					data_dict[m.group('sensor')+'_up_crit']  = (m.group('up_crit'))
					data_dict[m.group('sensor')+'_up_norec']  = (m.group('up_norec'))
					"""

			print(side+'-'+unit_num+" stress-ng Data:")
			print(data_dict)
			user_in = ""
			while user_in != "exit":
				user_in = input("What info would you like to see the data for?\n")
				if user_in != "exit":
					print(data_dict[user_in+'_count']+' '+user_in)
					print("at a rate of "+ data_dict[user_in+'_rate']+' '+data_dict[user_in+'_units'])
					if (data_dict[user_in+'_extra'] != None):
						print("("+data_dict[user_in+'_extra']+")")


	return data_dict

ClearPastData()
SplitLogFile()
#ParseTestData("1", "black", "IPMITOOL")
data_dict = {}
#data_dict = ParseTestData("1", "black", "DD_TEST_SDA",data_dict)
#print(data_dict)
#data_dict = ParseTestData("1", "black", "DD_TEST_SDB",data_dict)
data_dict = ParseTestData("1", "black", "stress-ng", data_dict)





