import re, os, json, dataset, subprocess
from datetime import date, datetime

SIDES = {'black': "BLK",'red': "RED"}
"""dict: Dictionary containing names of the sides, as well as their corresponding strings for table entry"""
MESSAGE_TAGS = ['STRESS_NG','IPMITOOL', 'STREAM_C', 'DD_TEST', 'HDPARM', 'IPERF','USB_PASSMARK','TAMPER_STATUS','FIBER_FPGA_TEMP', 'PING_TEST','UPTIME']
"""list of str: List containing tags of the tests used during the current test run.  Set manually."""
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
PREFIX_COLS = ['time_stamp','unit','side']
"""list of str: List containing names of the prefix columns"""

class Log(object):
	"""An object associated with a log messages file.

	Contains details about what units and tests are 
	expected to have results in the log.

	Parameters
	----------
	filename : str
		The name of the log file.
	units : list of str
		The list containing the units with results in the log.

	Attributes
	----------
	message_file_name : str
		The name of the log messages file.
	log_file : file
		The log file itself.
	units : list of str
		The list of units associated with this log.
	tests : dict
		A dictionary containing the name (tags) of tests
		associated with this log as keys, with the values 
		as the corresponding :class:`Test` objects.
	line_count : float
		The number of lines in the log file.
	cur_line_num : float
		The current line number.
	re_prefix : :py:class:`re.Match`
		The regular expression associated with the prefixes
		of the messages in this log.
	"""
	def __init__(self,filename,units):
		self.message_file_name = filename
		self.log_file = open(self.message_file_name)
		self.units = units
		# Set up a dictionary for tests in this log
		self.tests = {}	
		# Find the total number of lines in the file,
		# and set the initial line number to 0
		self.line_count = self.get_line_count()
		self.cur_line_num = 0.0

	def add_test(self,test):
		"""Associate a new test with this log.
		
		Attempts to set up a new table in the database for 
		storing data from this test. After it has done so, or 
		if such a table already exists, this method adds the 
		new test to the test dictionary :attr:`tests`, where the 
		key is the string equivalent to this test's tag (:attr:`Test.tag`).

		Parameters
		----------
		test : :class:`Test <optimized_parsing.Test>`
			The :class:`Test <optimized_parsing.Test>` to be added to this log.

		Note
		----
		May raise errors when attempting to create a 
		new table, as there is no available way to 
		specify the length of an SQL string type.
		"""
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
		"""Return the number of lines in the log file.
		
		Returns
		-------
		float
			The number of lines in the file with the name attr:`message_file_name`.

		Raises
		------
		IOError
			The file with the name attr:`message_file_name` could not be opened.
		"""
		p = subprocess.Popen(['wc', '-l', self.message_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		result, err = p.communicate()
		if p.returncode != 0:
			raise IOError(err)
		return float(result.strip().split()[0])

	def show_progress(self):
		"""Print the current progress in parsing the log file."""
		perc = self.cur_line_num/self.line_count
		print('\r'+str(perc*100)+'% Complete                        ', end='')

	def set_re_prefix(self):
		"""Set up the regular expression for the `prefix`.
		
		The `prefix` is the part of the log message that contains 
		the time stamp, the unit and side, and the test tag.  
		The regular expression for matching the `prefix` is as 
		such dependent on which units were tested and which  
		tests were performed during the test run that the log  
		file contains results from. The `prefix` makes it possible 
		to determine if a log message came from a test or not, 
		thus quickly ruling out some irrelevant log messages,
		and making it possible to determine which test the log
		messsage may have come from.
		"""
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
		"""Extracts test results from the log file.

		For each line in the log file, checks if it has a relevant `prefix`.
		If it does, then it calls :meth:`parse_line` on the line to attempt to 
		convert data from the line into a row to be inserted into the database.
		
		When it recieves the list of rows to be inserted, it then attempts to insert
		them into the corresponding test table in the database, using a query string 
		generated by :func:`insert_ignore_many_query()`, in order to ensure 
		that duplicate entries are not inserted.
		"""
		self.set_re_prefix()
		for line in self.log_file:
			self.cur_line_num +=1.0																	# Increment the line count
			prefix = self.re_prefix.search(line) 												# Check if the line has a valid test prefix
			# if it does:
			if (prefix != None):
				cur_test = self.tests[prefix.group('tag')]				# Set the current test according to the tag found
				tmp_insert = self.parse_line(line,cur_test)				# Convert the line into row data, recursively
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
		self.show_progress()
		print(' ')
		self.log_file.close()



	def parse_line(self,line,cur_test,recur_count=0):
		"""Converts data from a log message into a row to insert into an SQL table.

		Given a log message line and the test the line is associated with, attempts 
		to interpret the data in the line into a row dictionary.

		The exact interpretation process is dependant on the individual test, but in 
		general it attemps to match the line to a regular expression corresponding 
		to the current test's output format, and then uses the groups found by the 
		regular expression, along with the variables specified in the test's 
		:attr:`data_info <optimized_parsing.Test.data_info>` attribute to populate a row dictionary with the data.

		For tests that do (or may) have multiple lines of data for a single test result
		(and thus a single row of data), will also check and attempt to parse the 
		following lines as specified by the attributes of ``cur_test``.

		After successfully filling a dictionary for a full row of data for the
		current test, will call itself recursively on the next line in the log file, 
		under the assumption that the next line also belongs to the same test.  This 
		continues until it either reaches the end of the lines associated with the 
		current test, or it exceeds python's recursion limit. This allows it to return 
		a list of rows to be inserted into a single table with one query, which is 
		much faster than inserting each row individually.

		Parameters
		----------
		line : str
			A string containing a single line from the log file, which presumable contains
			a log message generated by the test denoted in ``cur_test``.
		cur_test : :class:`Test <optimized_parsing.Test>`
			The :class:`Test <optimized_parsing.Test>` that is expected to 
			correspond to the test results contained in line.
		recur_count: int
			Stores current recursion depth, to avoid raising an error if the limit is reached. 
			Set to ``0`` by default if no value is specified.
		
		Returns
		-------
		list
			A list of `row` dictionaries.  Every row in the list is associated with the same test.
		"""
		
		match_start = self.re_prefix.search(line)									# Get the 'prefix' data from the line
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
	"""An object which represents all of the information regarding a single test.

	Parameters
	----------
	json_file_name : str
		The filename of the json file from which test information should be loaded.

	Attributes
	----------
	tag : str
		The tag associated with the test (also used as the name of the test, 
		and the name of the table containing the test data).
	re : :class:`re.Pattern`
		The regular expression used for parsing log messages from the test.
	key_tag : str
		The name of the variable by which test data is separated.  Not used 
		in all tests.  An example is sensor for IPMI_TOOL, since every sensor
		has the same data fields, and thus are stored in separate rows.
	data_info : dict
		A dictionary with keys corresponding to the names of the data columns
		in the test's table, and values corresponding to the type of each column.
	num_lines : int
		The number of lines of log messages that contain data for a single test result.
	num_extra_lines : int
		The number of additional lines of log messages that *may* contain data for 
		a single test result, often in a separate format.

		Set to **0** if not present in the test's information file.
	extra_re : :class:`re.Pattern`
		The regular expression used for recognizing the data in extra lines. Only used by some tests.
	extra_data : list of str
		The list containing the names of the data present in extra lines. Only used by some_tests.
	"""
	def __init__(self,json_file_name=None):
		with open(json_file_name) as json_file:
			json_dict = (json.load(json_file))
			self.tag = json_dict['tag']
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
	"""Given a match object that contains groups with date/time info, return a corresponding python datetime object.
	
	Parameters
	----------
	match_obj : :class:`re.Match`
		A match object which contains time stamp information, and corresponding groups.

	Returns
	-------
	:class:`datetime <datetime.datetime>`
		A datetime object containing the time stamp information in ``match_obj``.
	"""
	return datetime(date.today().year, MONTHS[(match_obj.group('mon'))], int(match_obj.group('day')),
		int(match_obj.group('hr')), int(match_obj.group('min')), int(match_obj.group('sec')))

def return_or(val_list):
	"""Return the contents of *val_list* in as a regex `or` statement.

	Parameters
	----------
	val_list : list
		A list of values ``[v1,...,vn]``

	Returns
	-------
	str
		The string ``"((v1)|...|(vn))"``, which is formatted appropriately 
		for use in an `or` statement in a regular expression

	Example
	-------
	>>> print(return_or(['tea','milk','coffee']))
	"((tea)|(milk)|(coffee))"

	"""
	return '('+'|'.join(f"({val})" for val in val_list) + ')'


def rowcols4SQLquery(cols,pre_cols=PREFIX_COLS):
	"""Generates a string representation column names for a table.
	
	The output is formatted for use in an SQL query 
	(where the values of ``cols`` are the column names of the table).

	Parameters
	----------	
	cols : list
		A list of strings representing the names of the columns
		unique to a specific test table.

	pre_cols: list
		A list containing the names of columns which are not contained 
		in the row dictionary.

		This parameter is set to :const:`PREFIX_COLS` by default, since the 
		columns for `time_stamp`, `unit`, and `side` are those which 
		would not usually be contained in the row dicitionary, as  
		they are not unique to a specific test table, and thus their 
		values are extracted separately from those corresponding 
		to the columns in ``cols``.

	Returns
	-------
	str
		A string containing comma separated values from ``pre_cols`` and ``cols``, 
		enclosed in parentheses. Suitable for use when naming the columns in 
		an SQL *INSERT* query.

	"""
	pre_str = ','.join(str(col) for col in pre_cols)
	if len(pre_str) > 0:
		pre_str += ','
	return '(' + pre_str + ','.join(f"`{col}`" for col in cols) + ')'

def rowvals4SQLquery(row,col_info,pre_cols=PREFIX_COLS):
	"""Generates a string representation of the values in a row.

	Given a row dictionary, and a dictionary containing column info
	for the correspoding test, returns a string representation of
	the corresponding values in rows for every column of the table.
	
	Parameters
	----------
	row : dictionary
		A dictionary containing the data for a single row of an SQL
		table. The keys are the names of columns, with the values as 
		the corresponding values.
	col_info : dicitionary
		A dictionary containing the columns unique to a specific test as keys, 
		with the corresponding values as the data types of the columns.
	pre_cols: list
		A list containing the names of columns which are not contained 
		in ``col_info``.

		This parameter is set to :const:`PREFIX_COLS` by default, since the 
		columns for `time_stamp`, `unit`, and `side` are those which 
		are not unique to any single test, and thus are not contained
		within ``col_info``.

	Returns
	-------
	str
		A string representing all the column data in ``row`` (with all data 
		formatted as appropriate, and empty columns rendered as "NULL"), 
		with data separated by commas and enclosed in parentheses. 
		Suitable for use in an SQL *INSERT* query.
	"""
	col_list = pre_cols + list(col_info.keys())
	full_row = {}
	# With each column name as a key, set its corresponding 
	# value in full_row to an appropriate string respresentation,
	# or NULL if the row does not contain any data for the column.
	for col in col_list:
		if col not in row or row[col] == None:
			full_row[col]="NULL"
		elif col == "time_stamp" or col == "side" or (col in col_dict and col_dict[col]) == 'str':
			full_row[col] = '"'+str(row[col])+'"'
		else:
			full_row[col] = str(row[col])
	return '('+','.join(f"{full_row[col]}" for col in col_list) + ')'

def rowvals4SQLmany(row_list,col_info):
	"""Generates a string representation of the values in many rows.

	Given a list of row dicitonaries, and dictionary containing column info
	for the corresponding test, returns a string representation of the row data.

	Parameters
	----------
	row_list : list
		A list containing the rows (as dictionaries) to be inserted.
		
		Assumes every row dictionary contains corresponding values for 
		every data column in the table.

	col_info : dictionary
		A dictionary containing the columns unique to a specific test as keys, 
		with the corresponding values as the data types of the columns.

	Returns
	-------
	str
		A string representing the data in all of the rows in ``row_list``,
		with each row's data string separated by commas. Suitable for 
		use in an SQL *INSERT* query for many rows of data.
	"""
	return ','.join(rowvals4SQLquery((row,col_dict,id_cols) for row in row_list))

def insert_ignore_many_query(test, rows):
	"""Returns a string for an SQL *INSERT IGNORE* query for multiple rows of data.

	Given a :class:`Test` object and a list of rows, generate an SQL query string
	for inserting all of the rows in ``rows`` into the table corresponding 
	to ``test``.

	Parameters
	----------
	test : :class:`Test <optimized_parsing.Test>`
		The :class:`Test <optimized_parsing.Test>` that corresponds to the data contained in ``rows``.
	rows : list
		A list of row dictionaries to be inserted into the table 
		corresponding to ``test``.

	Returns
	-------
	str
		A string that, when executed as an SQL query, will
		perform an *INSERT IGNORE* of the rows in ``rows`` 
		into the table corresponding to ``test``

	Note
	----
	Because this code was created for internal use (and ideally automated use), 
	it makes no attempt at data sanitization, meaning it could, in theory, allow
	a malicious actor with arbitrary access to this code to perform an SQL injection 
	attack. However, if they only have access to the log file, it is unlikely that
	they would be able to embed arbitrary SQL queries that would still be recognized by
	the regular expressions that parse the line (assuming they cannot create arbitrary tests)
	"""
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