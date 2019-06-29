import re, os, json

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST', 'HDPARM']

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
		self.units = {}												# Create a dictionary to for units in this Log
		for u in units:												# For each unit in the list given
			self.units[u] = Unit(u)									# -> create a new Unit object
		self.tests = {}												# Set up a dictionary for tests in this log

	def add_test(self,test):
		"""Associate a new test with this log"""
		self.tests[test.tag] = test
		for u in self.units:
			self.units[u].add_test(test)

	def extract_data(self):
		"""Read and interpret data from the log messages file given"""
		# Define the regular expression for capturing the start of relevant log messages:
		re_prefix = re.compile(r"""																		# ===================================================
			(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)		# =   <Gets the date and time of the log message>   =
			\s																							# = ----------------------------------------------- =
			(?P<side>"""+return_or(SIDES)+r""")															# =       <Gets the side of the log message>        =
			-																							# = ----------------------------------------------- =
			(?P<unit>"""+return_or(list(map(lambda u: u.unit_num,  list(self.units.values()))))+r""")	# =    <Gets the unit number of the log message>    =
			\s+																							# = ----------------------------------------------- =
			(?P<tag>"""+return_or(list(map(lambda t: t.tag,  list(self.tests.values()))))+r""")			# = <Determines which test the log message is from> =
			""",re.VERBOSE)																				# ===================================================
		# Open the log file:
		with open(self.message_file_name) as log_file:
			for line in log_file:
				# Check if it appears to be a relevant log message
				match_start = re_prefix.search(line)
				if (match_start != None): # i.e. if the start of the log message does match our regular expression 're_prefix'
					# Figure out which test it is associated with	
					cur_test = self.tests[match_start.group('tag')]									
					# Then interpret the line (starting from the end of the 'start') with the appropriate regular expression
					m2 = cur_test.re.match(line[19+len(match_start.group('side'))+len(cur_test.tag):])
					if (m2 != None): # If that matches too, then:
						# Save the time stamp of the message
						cur_time = Time_Stamp(match_start) 
						self.units[match_start.group('unit')].sides[match_start.group('side')].add_data(cur_test.tag, 
						 cur_test.generate_datagram(m2.group(cur_test.key_tag),cur_time,(list(map(lambda val: m2.group(val), cur_test.data_info)))))

	def view_data(self):
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
								print(return_help())


class Unit(object):
	def __init__(self,unit_num):
		self.unit_num = unit_num
		self.sides = {}
		for s in SIDES:
			self.sides[s] = Side(s)

	def add_test(self,test):
		for s in self.sides:
			self.sides[s].add_test(test)

class Side(object):
	def __init__(self,side_name):
		self.name = side_name
		self.data = {}

	def add_test(self, test):
		self.data[test.tag] = {}

	def add_data(self,testtag,datagram):
		if datagram.id not in self.data[testtag]:
			self.data[testtag][datagram.id] = {}
			self.data[testtag][datagram.id][datagram.time_stamp] = datagram
		for t in self.data[testtag][datagram.id]:
			if str(t) == str(datagram.time_stamp):
				if self.data[testtag][datagram.id][t].add_data(datagram):
					return
		self.data[testtag][datagram.id][datagram.time_stamp] = (datagram)

	def view_data(self,test):
		user_in = ""
		while (user_in != "go back"):
			cur_test_dict = self.data[test.tag]
			user_in = input("Which "+test.key_tag+" would you like to see results for (or type (o)ptions): ")
			if user_in == "options" or user_in == 'o':
				print(return_options(cur_test_dict))
			elif (user_in == 'help' or user_in == 'h'):
				print(return_help())
			elif user_in in cur_test_dict:
				for time_stamp in cur_test_dict[user_in]:
						print(str(time_stamp)+": "+str(cur_test_dict[user_in][time_stamp].data_dict))
						#print(str(time_stamp)+":"+lambda key: return (key+str()

class Test(object):
	def __init__(self,tag=None,call=None,re_string=None,key_tag=None,data_info=None,json_file_name=None):
		if json_file_name:
			with open(json_file_name) as json_file:
				json_dict = (json.load(json_file))
				self.tag = json_dict['tag']
				self.call = json_dict['call']
				self.re = re.compile('\n'.join(json_dict['re_string']),re.VERBOSE)
				self.key_tag = json_dict['key_tag']
				self.data = {key_tag: []}
				self.data_info = json_dict['data_info']
		else:
			self.tag = tag
			self.call = call
			self.re_string = re_string
			self.re = re.compile(re_string,re.VERBOSE)
			self.data = {key_tag: []}
			self.key_tag = key_tag
			self.data_info = data_info

	def add_key(self,key_name):
		if key_name not in self.data:
			self.data[key_name] = []

	def generate_datagram(self,key,time,datum):
		return Test_Datagram(self,key,time,datum)

class Test_Datagram(object):
	def __init__(self,test,key_tag,time,data):
		self.time_stamp = time
		self.id = key_tag
		self.data_dict = {}
		for i in range(0,len(test.data_info)):
			try:
				evaluated = eval(data[i])
				if data[i] == str(evaluated):
					self.data_dict[key] = eval(data[i])
				else:
					self.data_dict[key] = data[i]
			except (SyntaxError, NameError) as e:
				self.data_dict[test.data_info[i]] = (data[i])
			except TypeError:
				if (data[i]) == None:
					self.data_dict[test.data_info[i]] = None

	def add_data(self,datagram):
		def_out = False
		for key in self.data_dict:
			if self.data_dict[key] == None and datagram.data_dict[key] != None:
				try:
					evaluated = eval(datagram.data_dict[key])
					if datagram.data_dict[key] == str(evaluated):
						self.data_dict[key] = eval(datagram.data_dict[key])
					else:
						self.data_dict[key] = (datagram.data_dict[key])
				except (SyntaxError, NameError, TypeError) as e:
					self.data_dict[key] = (datagram.data_dict[key])
				def_out = True
			elif self.data_dict[key] != None and datagram.data_dict[key] != None and self.data_dict[key] != datagram.data_dict[key]:
				return False
		return def_out

class Time_Stamp(object):
	def __init__(self,time_match):
		self.mon = time_match.group('mon')
		self.day = time_match.group('day')
		self.hr  = time_match.group('hr')
		self.min = time_match.group('min')
		self.sec = time_match.group('sec')

	def __str__(self):
		return self.mon + " " + self.day + " at " + ':'.join([self.hr,self.min,self.sec])

def return_or(l):
	return ("|".join(list(map(lambda s: "("+s+")", l))))

def return_or2(l):
	return ("|".join(list(map(lambda s: "("+s+")", l))))

def return_options(options_list):
	return("The options are " + ", ".join(list(options_list)))

def return_help():
	return("Type '(h)elp' to bring up this prompt, '(o)ptions' for a list of viable responses,\n"
		"'go back' to return to the previous prompt, or 'exit' to end the program")

datalog = Log('test_messages',['1'])
for tag in MESSAGE_TAGS:
	datalog.add_test(Test(json_file_name="Tests/"+tag+".json"))

datalog.extract_data()
datalog.view_data()
