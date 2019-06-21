import re, os, json, dataset, subprocess
from datetime import date, datetime

SIDES = ['black','red']
MESSAGE_TAGS = ['STRESS_NG','IPMITOOL', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP']
#MESSAGE_TAGS = ['stress-ng', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP']
#MESSAGE_TAGS = ['USB_PASSMARK']
MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
MAIN_MESSAGE_FILE = "messages_overnight_Jun21"
MESSAGE_FILE_NAMES = ['BLACKCLEAN.txt','REDCLEAN.txt']

class test_json(json.JSONEncoder):
	def default(self, o):
		if (type(o) == Test):
			return{'tag': o.tag, 'call': o.call, 're_string': (list(map(lambda s: s.strip('\t'), o.re_string.split('\n')))), 'key_tag': o.key_tag, 'data_info': o.data_info}
		else:
			return json.JSONEncoder.default(self, o)

class Log(object):
	def __init__(self,filename,units):
		"""Create a Log object associated with a log messages file"""
		self.message_file_name = filename 							# Save the name of the messages file
		self.units = units
		self.tests = {}												# Set up a dictionary for tests in this log

	def add_test(self,test):
		"""Associate a new test with this log"""
		test_table = db.create_table(test.tag)
		test_table.create_column('unit', db.types.text)
		test_table.create_column('side', db.types.text)
		test_table.create_column('time_stamp', db.types.datetime)
		"""for i in range(0,len(test.data_info)):
			if test.data_types[i] == 'int':
				test_table.create_column(test.data_info[i], db.types.integer)
			elif test.data_types[i] == 'float':
				test_table.create_column(test.data_info[i], db.types.float)
			else:
				test_table.create_column(test.data_info[i], db.types.text)
		"""
		for key in test.data_info:
			if test.data_info[key] == 'int':
				test_table.create_column(key, db.types.bigint)
			elif test.data_info[key] == 'float':
				test_table.create_column(key, db.types.float)
			else:
				test_table.create_column(key, db.types.text)
		self.tests[test.tag] = test
		#for u in self.units:
		#	self.units[u].add_test(test)

	def extract_data(self):
		"""Read and interpret data from the log messages file given"""
		# Define the regular expression for capturing the start of relevant log messages:
		re_prefix = re.compile(r"""																		# ===================================================
			(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)		# =   <Gets the date and time of the log message>   =
			\s																							# = ----------------------------------------------- =
			(?P<side>"""+return_or(SIDES)+r""")															# =       <Gets the side of the log message>        =
			-																							# = ----------------------------------------------- =
			(?P<unit>"""+return_or(self.units)+r""")													# =    <Gets the unit number of the log message>    =
			\s+																							# = ----------------------------------------------- =
			(?P<tag>"""+return_or(list(map(lambda t: t.tag,  list(self.tests.values()))))+r""")			# = <Determines which test the log message is from> =
			""",re.VERBOSE)																				# ===================================================
		# Open the log file:
		with open(self.message_file_name) as log_file:
			l_num = 0.0
			for line in log_file:
				# Check if it appears to be a relevant log message
				match_start = re_prefix.search(line)
				if (match_start != None): 	# i.e. if the start of the log message does match our regular expression 're_prefix'

					# Figure out which test it is associated with
					cur_test = self.tests[match_start.group('tag')]
					# Then interpret the line (starting from the end of the 'start') with the appropriate regular expression
					m2 = cur_test.re.match(line[19+len(match_start.group('side'))+len(cur_test.tag):])
					if (m2 != None): # If that matches too, then:
						table = db[match_start.group('tag')]
						next_row = {}

						next_row['unit'] = match_start.group('unit')
						next_row['side'] = match_start.group('side')
						next_row['time_stamp'] = make_datetime(match_start)

						if (match_start.group('tag') == 'USB_PASSMARK'):
							if m2.group('benchmark_type2') == 'error counter':
								next_row['benchmark_type'] = m2.group('benchmark_type2')
								error_count = 0;
								log_file.readline()
								l_num += 1.0
								for i in range(0,10):
									l = log_file.readline()
									m_tmp = cur_test.re.match(l[19+len(match_start.group('side'))+len(cur_test.tag):])
									error_count += eval(m_tmp.group('error_count'))
									l_num += 1.0
								next_row['error_count'] = error_count
								table.insert(next_row)
							elif m2.group('benchmark_type') == 'Read' or m2.group('benchmark_type') == 'Write':
								next_row['benchmark_type'] = m2.group('benchmark_type')
								transfer_rate = 0.0
								max_rate = 0.0
								min_rate = 1000.0
								for i in range(0,16):
									l = log_file.readline()
									m_tmp = cur_test.re.match(l[19+len(match_start.group('side'))+len(cur_test.tag):])
									tmp_rate = eval(m_tmp.group('transfer_rate'))
									transfer_rate = transfer_rate+tmp_rate
									if tmp_rate < min_rate:
										min_rate = tmp_rate
									tmp_max = eval(m_tmp.group('max_rate'))
									if tmp_max > max_rate:
										max_rate = tmp_max
									l_num += 1.0
								next_row['avg_rate'] = transfer_rate/16.0
								next_row['max_rate'] = max_rate
								next_row['min_rate'] = min_rate
								table.insert(next_row)
						else:
							for key in cur_test.data_info:
								#print(key)
								#print((m2.group(2)))
								if ((m2.group(key)) == 'na'):
									next_row[key] = None
								elif ((cur_test.data_info[key] == 'int') or (cur_test.data_info[key] == 'float')) and ((m2.group(key)) != None) and (cur_test.data_info[key] != 'str'):
									next_row[key] = eval(''.join(m2.group(key).split(',')))
										
								else:
									next_row[key] = (m2.group(key))

							query_str = "SELECT * FROM {} WHERE id=(SELECT MAX(id) FROM {}) AND time_stamp='{}.000000';".format(match_start.group('tag'),match_start.group('tag'),next_row['time_stamp'])
							row = db.query(query_str)
							#print(query_str)
							try:
								r = row.next()
							except StopIteration:
								row = None
							while row != None:
								newer_row = return_full_row(r,next_row)
								if newer_row != next_row:
									table.upsert(newer_row,['id'])
									break
								try:
									r = row.next()
								except StopIteration:
									row = None
							else:
								table.insert(next_row)

				l_num +=1.0
				perc = l_num/line_count
				print('\r'+str(perc*100)+'% Complete                        ', end='')
			print(' ')


"""	def view_data(self):
		user_in = ""
		while (user_in != 'exit'):
			user_in = input("Which unit would you like to see data for?\n")
			unit_num = user_in
			if unit_num in self.units:
				cur_unit = self.units[unit_num]
				while (user_in != 'go back' and user_in != 'exit'):
					user_in = input("Which side?\n")
					if user_in in cur_unit.sides:
						cur_side = cur_unit.sides[user_in]
						while (user_in != 'go back' and user_in != 'exit'):
							user_in = input("Which test would you like to see data for?\n")
							if user_in in cur_side.data:
								cur_side.view_data(self.tests[user_in])
							elif (user_in == 'options' or user_in == 'o'):
								print(return_options(self.tests))
							elif (user_in == 'help' or user_in == 'h'):
								print(return_help())"""

class Test(object):
	def __init__(self,json_file_name=None):
		if json_file_name:
			with open(json_file_name) as json_file:
				json_dict = (json.load(json_file))
				self.tag = json_dict['tag']
				self.call = json_dict['call']
				self.re = re.compile('\n'.join(json_dict['re_string']),re.VERBOSE)
				self.key_tag = json_dict['key_tag']
				self.data_info = json_dict['data_info']
				#self.data_types = json_dict['data_types']

def make_datetime(match_obj):
	"""Given a match object that contains groups with date/time info, return a corresponding python datetime object"""
	return datetime(date.today().year, MONTHS[(match_obj.group('mon'))], int(match_obj.group('day')),
		int(match_obj.group('hr')), int(match_obj.group('min')), int(match_obj.group('sec')))

def return_or(l):
	return ("|".join(list(map(lambda s: "("+s+")", l))))

def return_options(options_list):
	return("The options are " + ", ".join(list(options_list)))

def return_help():
	return("Type '(h)elp' to bring up this prompt, '(o)ptions' for a list of viable responses,\n"
		"'go back' to return to the previous prompt, or 'exit' to end the program")


def return_full_row(row_match, new_row):
	update = True
	temp_row = {}
	for key in row_match:
		#print(key)
		if key != 'id' and key != 'time_stamp':
			if row_match[key] == new_row[key] or (row_match[key] != None and new_row[key] == None):
				temp_row[key] = row_match[key]
				#print(1)
			elif row_match[key] == None and new_row[key] != None:
				temp_row[key] = new_row[key]
				#print(2)
			else:
				#print(3)
				#print(row_match[key])
				#print(new_row[key])
				return new_row
	temp_row['id'] = row_match['id']
	return temp_row

def get_line_count(file):
	p = subprocess.Popen(['wc', '-l', file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	result, err = p.communicate()
	if p.returncode != 0:
		raise IOError(err)
	return (float(result.strip().split()[0]))

#db = dataset.connect('sqlite:///test_results.db')
#db = dataset.connect('mysql://jberger:open.local.box@10.1.11.21/test_results')
# print("{} Start: {}".format(MESSAGE_FILE_NAME,datetime.today()))
db = dataset.connect('mysql://guest:password@localhost/test_results')

# line_count = get_line_count(MESSAGE_FILE_NAME)

os.system("./TEST.sh {}".format(MAIN_MESSAGE_FILE))

datalog = Log('test_messages',['1'])
for msg_file in MESSAGE_FILE_NAMES:
	print("{} Start: {}".format(msg_file,datetime.today()))
	line_count = get_line_count(msg_file)
	datalog = Log(msg_file,['1'])
	for tag in MESSAGE_TAGS:
		datalog.add_test(Test(json_file_name="Tests/"+tag+".json"))

	datalog.extract_data()
	print("{} End: {}".format(msg_file,datetime.today()))


# datalog = Log(MESSAGE_FILE_NAME,['1'])
# for tag in MESSAGE_TAGS:
# 	datalog.add_test(Test(json_file_name="Tests/"+tag+".json"))

# datalog.extract_data()
# print("{} End: {}".format(MESSAGE_FILE_NAME,datetime.today()))
#datalog.view_data()
