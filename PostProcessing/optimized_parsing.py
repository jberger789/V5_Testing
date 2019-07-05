import re, os, json, dataset, subprocess
from datetime import date, datetime

SIDES = {'black': "BLK",'red': "RED"}
MESSAGE_TAGS = ['STRESS_NG','IPMITOOL', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP', 'PING_TEST','UPTIME']
#MESSAGE_TAGS = ['STRESS_NG','IPMITOOL', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','TAMPER_STATUS','FIBER_FPGA_TEMP', 'PING_TEST']
#MESSAGE_TAGS = ['stress-ng', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP']
#MESSAGE_TAGS = ['UPTIME']
#MESSAGE_TAGS = ['UPTIME']
MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
#MAIN_MESSAGE_FILE = "messages_overnight_Jun21"
MAIN_MESSAGE_FILES = ["../Results/messages_thermal_3"]
MESSAGE_FILE_NAMES = {'tmp/BLACKCLEAN.txt': "Black Results",'tmp/REDCLEAN.txt': "Red Results"}
#MESSAGE_FILE_NAMES = {'tmp/REDCLEAN.txt': "Red Results"}
DB_ADDRESS = 'mysql://guest:password@localhost/test_results'
DB = dataset.connect(DB_ADDRESS)

# class test_json(json.JSONEncoder):
# 	def default(self, o):
# 		if (type(o) == Test):
# 			return{'tag': o.tag, 'call': o.call, 're_string': (list(map(lambda s: s.strip('\t'), o.re_string.split('\n')))), 'key_tag': o.key_tag, 'data_info': o.data_info}
# 		else:
# 			return json.JSONEncoder.default(self, o)

class Log(object):
	def __init__(self,filename,units):
		"""Create a Log object associated with a log messages file"""
		# Save the name of the messages file
		self.message_file_name = filename
		self.log_file = open(self.message_file_name)
		self.units = units
		# Set up a dictionary for tests in this log
		self.tests = {}		
		self.get_line_count()
		self.cur_line_num = 0.0

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

	def get_line_count(self):
		p = subprocess.Popen(['wc', '-l', self.message_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		result, err = p.communicate()
		if p.returncode != 0:
			raise IOError(err)
		self.line_count = float(result.strip().split()[0])
		#print(f"Line Count = {self.line_count}")

	def show_progress(self):
		perc = self.cur_line_num/self.line_count
		print('\r'+str(perc*100)+'% Complete                        ', end='')

	def set_re_prefix(self):
		self.re_prefix = re.compile(r"""																# ===================================================
			(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)		# =   <Gets the date and time of the log message>   =
			\s																							# = ----------------------------------------------- =
			(?P<side>"""+return_or(SIDES)+r""")															# =       <Gets the side of the log message>        =
			-																							# = ----------------------------------------------- =
			(?P<unit>"""+return_or(self.units)+r""")													# =    <Gets the unit number of the log message>    =
			\s+																							# = ----------------------------------------------- =
			(?P<tag>"""+return_or(test.tag for test in self.tests.values())+r""")						# = <Determines which test the log message is from> =
			""",re.VERBOSE)																				# ===================================================	

	def extract_data(self):
		"""Read and interpret data from the log messages file given"""
		# Define the regular expression for capturing the start of relevant log messages:
		self.set_re_prefix()
		for line in self.log_file:																# for each line in the log file:
			self.cur_line_num +=1.0																	# Increment the line count
			match_start = self.re_prefix.search(line) 												# Check if the line has a valid test prefix
			# if it does:
			if (match_start != None):
				cur_test = self.tests[match_start.group('tag')]				# Set the current test according to the tag found
				tmp_insert = self.parse_line(line,cur_test,0)		# Convert the line into row data, recursively
				if tmp_insert != []:
					table = DB[cur_test.tag]
					try:
						try:
							DB.query(insert_ignore_many_query(cur_test,tmp_insert))
						except OperationalError:
							print(tmp_insert)
							input(" ")
					except NameError:
						print(tmp_insert)
						input(" ")
			else:
				pass	
		self.show_progress()
		print(' ')
		self.log_file.close()



	def parse_line(self,line,cur_test,recur_count):
		"""Given a line and a log file, and the test the current line is associated with, 
		will convert the data in the line and in every consecutive line for the same test 
		into a lists of rows to be inserted into the database (recursively)"""
		
		match_start = self.re_prefix.search(line)									# Get the 'preamble' data from the line (i.e. the datetime, side, test tag, etc)
		m2 = cur_test.re.search(line)												# Then get the test data using the appropriate regular expression
		# If test data is recognized:
		if (m2 != None and match_start != None):
			next_row = {}															# Instantiate a dictionary for holding this row's values
			next_row['unit'] = int(match_start.group('unit'))						# Set the unit data as appropriate
			next_row['side'] = SIDES[match_start.group('side')]						# Set the side data as appropriate (in database format)
			next_row['time_stamp'] = make_datetime(match_start)						# Set the time_stamp as appropriate
			# If the current test is USB Passmark, execute a special set of interpretations:
			if (cur_test.tag == 'USB_PASSMARK'):
				if m2.group('benchmark_type2') == 'error counter':
					next_row['benchmark_type'] = m2.group('benchmark_type2')
					error_count = 0;
					self.log_file.readline()
					self.cur_line_num+=1.0
					for i in range(0,10):
						l = self.log_file.readline()
						self.cur_line_num+=1.0
						m_tmp = cur_test.re.match(l[19+len(match_start.group('side'))+len(cur_test.tag):])
						error_count += eval(m_tmp.group('error_count'))
					next_row['error_count'] = error_count
				elif m2.group('benchmark_type') == 'Read' or m2.group('benchmark_type') == 'Write':
					next_row['benchmark_type'] = m2.group('benchmark_type')
					transfer_rate = 0.0
					max_rate = 0.0
					min_rate = 1000.0
					for i in range(0,16):
						l = self.log_file.readline()
						self.cur_line_num +=1.0	
						m_tmp = cur_test.re.match(l[19+len(match_start.group('side'))+len(cur_test.tag):])
						tmp_rate = eval(m_tmp.group('transfer_rate'))
						transfer_rate = transfer_rate+tmp_rate
						if tmp_rate < min_rate:
							min_rate = tmp_rate
							tmp_max = eval(m_tmp.group('max_rate'))
						if tmp_max > max_rate:
							max_rate = tmp_max
						next_row['avg_rate'] = transfer_rate/16.0
						next_row['max_rate'] = max_rate
						next_row['min_rate'] = min_rate
						if (m_tmp.group('transfer_count')=='1024' and i != 15):
							print("USB_PASSMARK Error at line [{}]".format(l))
							return[next_row]
			# Otherwise, check if this test has multiple lines of data
			# If it does:
			elif (cur_test.num_lines > 1):
				for x in range(0,cur_test.num_lines):
					for k in cur_test.data_info:
						if ((cur_test.data_info[k] == 'int') or (cur_test.data_info[k] == 'float')) and (m2.group(k) != None):
							next_row[k] = eval(m2.group(k))
						elif k not in next_row and m2.group(k)!= None:
							next_row[k] = (m2.group(k))
					l = self.log_file.readline()
					self.cur_line_num +=1.0	
					m2 = cur_test.re.search(l)
			# Else, all normal data for a single row is on the current line:
			else:															
				for key in cur_test.data_info:															# For each column key outlined in the test info:
					if m2.group(key) == 'na' or m2.group(key) == None:									# >	If the data for this column has no value (either explicitly or implicitly)
						next_row[key] = None															# 	 >>	Set the column of this row to 'None'
					elif (cur_test.data_info[key] == 'int') or (cur_test.data_info[key] == 'float'): 	# >	If the data for this column is expected to be an int or float
						next_row[key] = eval(''.join(m2.group(key).split(',')))							# 	 >>	Set the column of this row to the evaluated value
					else:																				# Else
						next_row[key] = (m2.group(key))													# >	Set the column of this row to the string value found
			# If the recursion depth is over 200, end the 
			# recursive process (to avoid python's depth limit)
			if (recur_count > 200):
				return([(next_row)])
			# Retrieve the next line of the log_file
			l = self.log_file.readline()
			self.cur_line_num +=1.0	
			# If the current test has possible additonal lines of data
			if (cur_test.num_extra_lines > 0):
				tmp_i = cur_test.num_extra_lines
				while tmp_i > 0:
					extra_match = cur_test.extra_re.search(l[19+len(match_start.group('side'))+len(cur_test.tag):])
					if (extra_match != None):
						for datum in cur_test.extra_data:
							next_row[datum] = extra_match.group(datum)
						l = self.log_file.readline()
						self.cur_line_num+=1.0
					tmp_i -= 1
			self.show_progress()
			recur_count += 1
			return [(next_row)] + self.parse_line(l,cur_test,recur_count)
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

def make_datetime(match_obj):
	"""Given a match object that contains groups with date/time info, return a corresponding python datetime object"""
	return datetime(date.today().year, MONTHS[(match_obj.group('mon'))], int(match_obj.group('day')),
		int(match_obj.group('hr')), int(match_obj.group('min')), int(match_obj.group('sec')))

def return_or(l):
	"""
	**Parameters**:
		``l``
			A list of values ``[v1,...,vn]``

	**Returns**:
		``or_str``
			The string ``"((v1)|...|(vn))"``, which is formatted appropriately for use in an ``or`` statement in a regular expression

	**Example**::

		# Calling 
		return_or(['tea','milk','coffee'])
		# Will return
		"((tea)|(milk)|(coffee))"

	"""
	or_str = '('+'|'.join(f"({v})" for v in l) + ')'
	return or_str


def rowcols4SQLquery(cols,id_cols=[]):
	pre_cols = ','.join(str(col) for col in id_cols)
	if len(pre_cols) > 0:
		pre_cols += ','
	return '(' + pre_cols + ','.join(f"`{col}`" for col in cols) + ')'

def rowvals4SQLquery(row,col_dict,id_cols=[]):
	col_list = id_cols + list(col_dict.keys())
	full_row = {}
	for col in col_list:
		if col not in row or row[col] == None:
			full_row[col]="NULL"
		elif col == "time_stamp" or col == "side" or (col in col_dict and col_dict[col]) == 'str':
			full_row[col] = '"'+str(row[col])+'"'
		else:
			full_row[col] = str(row[col])
	return ','.join(f"{full_row[col]}" for col in col_list)

def rowvals4SQLmany(row_list,col_dict,id_cols=[]):
	out_str = ""
	out_str += ','.join(f"({rowvals4SQLquery(row,col_dict,id_cols)})" for row in row_list)
	return out_str

def insert_ignore_many_query(test, rows):
	pre_cols = ['unit','side','time_stamp']
	return "INSERT IGNORE INTO `{}` {} VALUES {};".format(test.tag,
		rowcols4SQLquery(test.data_info.keys(),pre_cols),
		rowvals4SQLmany(rows,test.data_info,pre_cols))


if __name__ == '__main__':
	for m in MAIN_MESSAGE_FILES:
		os.system(f"./splitbytest.sh {m}")
	os.system("./mergebyside.sh")
	for msg_file in MESSAGE_FILE_NAMES:
		print("{} Start: {}".format(MESSAGE_FILE_NAMES[msg_file],datetime.today()))
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