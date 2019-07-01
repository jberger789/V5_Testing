import re, os, json, dataset, subprocess
from datetime import date, datetime

SIDES = {'black': "BLK",'red': "RED"}
MESSAGE_TAGS = ['STRESS_NG','IPMITOOL', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP', 'PING_TEST','UPTIME']
#MESSAGE_TAGS = ['STRESS_NG','IPMITOOL', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','TAMPER_STATUS','FIBER_FPGA_TEMP', 'PING_TEST']
#MESSAGE_TAGS = ['stress-ng', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP']
#MESSAGE_TAGS = ['UPTIME']
#MESSAGE_TAGS = ['DD_TEST']
MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
#MAIN_MESSAGE_FILE = "messages_overnight_Jun21"
MAIN_MESSAGE_FILES = ["../Results/messages-20190630","../Results/messages"]
MESSAGE_FILE_NAMES = {'tmp/BLACKCLEAN.txt': "Black Results",'tmp/REDCLEAN.txt': "Red Results"}
#MESSAGE_FILE_NAMES = {'tmp/REDCLEAN.txt': "Red Results"}
DB_ADDRESS = 'mysql://guest:password@localhost/test_results'
DB = dataset.connect(DB_ADDRESS)

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
		test_table = DB.create_table(test.tag)
		test_table.create_column('unit', DB.types.integer)
		test_table.create_column('side', DB.types.string)
		test_table.create_column('time_stamp', DB.types.datetime)
		for key in test.data_info:
			if test.data_info[key] == 'int':
				test_table.create_column(key, DB.types.bigint)
			elif test.data_info[key] == 'float':
				test_table.create_column(key, DB.types.float)
			else:
				test_table.create_column(key, DB.types.string)
		self.tests[test.tag] = test

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
				l_num+=1.0
				# Check if it appears to be a relevant log message
				match_start = re_prefix.search(line)
				if (match_start != None):
					cur_test = self.tests[match_start.group('tag')]
					tmp_insert = parse_line(line,log_file,cur_test,l_num,re_prefix,0)
					if tmp_insert != []:
						table = DB[cur_test.tag]
						#table.insert_many(tmp_insert)
						try:
							try:
								DB.query(insert_ignore_many_query(cur_test,tmp_insert))
							except OperationalError:
								print(tmp_insert)
								input(" ")
						except NameError:
							print(tmp_insert)
							input(" ")
						#except sqlalchemy.exc.IntegrityError:
					l_num += len(tmp_insert)
					if (cur_test.tag == 'DD_TEST'):
						l_num += len(tmp_insert)*2			
			perc = line_count/line_count
			print('\r'+str(perc*100)+'% Complete                        ', end='')
			print(' ')



def parse_line(line,log_file,cur_test,l_num,re_prefix,recur_count):
	# Figure out which test it is associated with
	# Then interpret the line (starting from the end of the 'start') with the appropriate regular expression
	match_start = re_prefix.search(line)
	m2 = cur_test.re.search(line)
	if (m2 != None):
		next_row = {}
		next_row['unit'] = int(match_start.group('unit'))
		next_row['side'] = SIDES[match_start.group('side')]
		next_row['time_stamp'] = make_datetime(match_start)
		if (cur_test.tag == 'USB_PASSMARK'):
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
			elif m2.group('benchmark_type') == 'Read' or m2.group('benchmark_type') == 'Write':
				next_row['benchmark_type'] = m2.group('benchmark_type')
				transfer_rate = 0.0
				max_rate = 0.0
				min_rate = 1000.0
				for i in range(0,16):
					l = log_file.readline()
					#print(l)
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
					if (m_tmp.group('transfer_count')=='1024' and not i == 15):
						print("USB_PASSMARK Error at line [{}]".format(l))
						break
			"""elif (cur_test.tag == 'DD_TEST'):
			for x in range(0,3):
				for k in cur_test.data_info:
					if ((cur_test.data_info[k] == 'int') or (cur_test.data_info[k] == 'float')) and ((m2.group(k)) != None) and (cur_test.data_info[k] != 'str'):
						next_row[k] = eval(m2.group(k))
					elif k not in next_row and m2.group(k)!= None:
						next_row[k] = (m2.group(k))
				l = log_file.readline()
				m2 = cur_test.re.search(l)
			l_num += 2.0"""
		elif (cur_test.num_lines > 1):
			for x in range(0,cur_test.num_lines):
				for k in cur_test.data_info:
					if ((cur_test.data_info[k] == 'int') or (cur_test.data_info[k] == 'float')) and ((m2.group(k)) != None) and (cur_test.data_info[k] != 'str'):
						next_row[k] = eval(m2.group(k))
					elif k not in next_row and m2.group(k)!= None:
						next_row[k] = (m2.group(k))
				l = log_file.readline()
				m2 = cur_test.re.search(l)
			l_num += 2.0
		else:
			for key in cur_test.data_info:
				if ((m2.group(key)) == 'na'):
					next_row[key] = None
				elif ((cur_test.data_info[key] == 'int') or (cur_test.data_info[key] == 'float')) and ((m2.group(key)) != None) and (cur_test.data_info[key] != 'str'):
					next_row[key] = eval(''.join(m2.group(key).split(',')))
				else:
					next_row[key] = (m2.group(key))
		if (recur_count > 200):
			return([(next_row)])
		l = log_file.readline()
		if (cur_test.num_extra_lines > 0):
			tmp_i = cur_test.num_extra_lines
			while tmp_i > 0:
				extra_match = cur_test.extra_re.match(l[19+len(match_start.group('side'))+len(cur_test.tag):])
				if (extra_match != None):
					for datum in cur_test.extra_data:
						next_row[datum] = extra_match.group(datum)
					l = log_file.readline()
					l_num+=1.0
				tmp_i -= 1
		l_num+=1.0
		perc = l_num/line_count
		print('\r'+str(perc*100)+'% Complete                        ', end='')
		recur_count += 1
		return [(next_row)] + parse_line(l,log_file,cur_test,l_num,re_prefix,recur_count)
	else:
		return []


class Test(object):
	def __init__(self,json_file_name=None):
		if json_file_name:
			with open(json_file_name) as json_file:
				json_dict = (json.load(json_file))
				self.tag = json_dict['tag']
				self.call = json_dict['call']
				self.re = re.compile('\n'.join(json_dict['re_string']),re.VERBOSE)
				self.key_tag = json_dict['data_key']
				self.data_info = json_dict['data_info']
				self.num_lines = json_dict['num_lines']
				if (json_dict['extra_lines']):
					self.num_extra_lines = json_dict['num_extra_lines']
					self.extra_re = re.compile('\n'.join(json_dict['extra_re']),re.VERBOSE)
					self.extra_data = json_dict['extra_data']
				else:
					self.num_extra_lines = json_dict['num_extra_lines'] = 0
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

def dictkeys2list(dictionary):
	return ','.join(list(map(lambda key: "`{}`".format(key),dictionary)))

def dictvals2list(key_list,dictionary):
	key_list = list(key_list)
	keys2add = []
	for key in dictionary:
		if key not in key_list:
			keys2add += [key]
	key_list = keys2add + key_list
	return str(tuple(map(lambda key: ("NULL") if (key not in dictionary or not dictionary[key]) else (str(dictionary[key])),key_list)))
	"""output = "("
	for key in dictionary:
		if dictionary[key] == None:
			output+="NULL,"
		else:
			output+=str(dictionary[key])+","
		return (output[0:-1]+")")"""

def insert_ignore_many_query(test, rows):
	return "INSERT IGNORE INTO `{}` (unit,side,time_stamp,{}) VALUES {}".format(test.tag,
		dictkeys2list(test.data_info),
		",".join(list(map(lambda i: dictvals2list(test.data_info,i),rows))))

#DB = dataset.connect('sqlite:///test_results.DB')
#DB = dataset.connect('mysql://jberger:open.local.box@10.1.11.21/test_results')
# print("{} Start: {}".format(MESSAGE_FILE_NAME,datetime.today()))
#
# line_count = get_line_count(MESSAGE_FILE_NAME)

for m in MAIN_MESSAGE_FILES:
	os.system("./TEST.sh {}".format(m))

#datalog = Log('test_messages',['1'])
for msg_file in MESSAGE_FILE_NAMES:
	print("{} Start: {}".format(MESSAGE_FILE_NAMES[msg_file],datetime.today()))
	line_count = get_line_count(msg_file)
	datalog = Log(msg_file,['1'])
	for tag in MESSAGE_TAGS:
		datalog.add_test(Test(json_file_name="../Tests/"+tag+".json"))

	datalog.extract_data()
	print("{} End: {}".format(MESSAGE_FILE_NAMES[msg_file],datetime.today()))


# datalog = Log(MESSAGE_FILE_NAME,['1'])
# for tag in MESSAGE_TAGS:
# 	datalog.add_test(Test(json_file_name="Tests/"+tag+".json"))

# datalog.extract_data()
# print("{} End: {}".format(MESSAGE_FILE_NAME,datetime.today()))
#datalog.view_data()