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
		self.message_file_name = filename
		self.units = {}
		for u in units:
			self.units[u] = Unit(u)
		self.tests = {}

	def add_test(self,test):
		self.tests[test.tag] = test
		for u in self.units:
			self.units[u].add_test(test)

	def extract_data(self):
		re_prefix = re.compile(r"""
			(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
			\s
			(?P<side>"""+return_or(SIDES)+r""")
			-
			(?P<unit>"""+return_or(list(map(lambda u: u.unit_num,  list(self.units.values()))))+r""")
			\s+
			(?P<tag>"""+return_or(list(map(lambda t: t.tag,  list(self.tests.values()))))+r""")
			.*$
			""",re.VERBOSE)
		with open(self.message_file_name) as f:
			for line in f:
				m = re_prefix.search(line)
				#print(m)
				if (m != None):
					cur_test = self.tests[m.group('tag')]
					#m2 = cur_test.re.search(line)
					m2 = cur_test.re.match(line[19+len(m.group('side'))+len(cur_test.tag):])
					if (m2 != None):
						#cur_test.add_key(m2.group(cur_test.key_tag))
						cur_time = Time_Stamp(m.group('mon'),m.group("day"),m.group("hr"),m.group("min"),m.group("sec"))
						self.units[m.group('unit')].sides[m.group('side')].add_data(cur_test.tag, cur_test.generate_datagram(
							m2.group(cur_test.key_tag),cur_time,(list(map(lambda val: m2.group(val), cur_test.data_info)))))

	def view_data(self):
		user_in = ""
		while (user_in != 'exit'):
			user_in = input("Which unit would you like to see data for?\n")
			unit_num = user_in
			if unit_num in self.units:
				cur_unit = self.units[unit_num]
				while (user_in != 'go back'):
					user_in = input("Which side?\n")
					if user_in in cur_unit.sides:
						cur_side = cur_unit.sides[user_in]
						while (user_in != 'go back'):
							user_in = input("Which test would you like to see data for?\n")
							if user_in in cur_side.data:
								cur_side.view_data(self.tests[user_in])

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
			self.data[testtag][datagram.id] = []
		self.data[testtag][datagram.id].append(datagram)

	def view_data(self,test):
		user_in = ""
		while (user_in != "go back"):
			cur_test_dict = self.data[test.tag]
			user_in = input("Which "+test.key_tag+" would you like to see results for (or type (o)ptions): ")
			if user_in == "options" or user_in == 'o':
				print("The options are " + ", ".join(list(cur_test_dict)))
			elif user_in in cur_test_dict:
				for dp in cur_test_dict[user_in]:
						print(str(dp.time_stamp)+": "+str(dp.data_dict))

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
	def __init__(self,test,key,time,data):
		self.time_stamp = time
		self.id = key
		self.data_dict = {}
		for i in range(0,len(test.data_info)):
			self.data_dict[test.data_info[i]] = data[i]

class Time_Stamp(object):
	def __init__(self,mon,day,hr,minu,sec):
		self.mon = mon
		self.day = day
		self.hr = hr
		self.min = minu
		self.sec = sec

	def __str__(self):
		return self.mon + " " + self.day + " at " + ':'.join([self.hr,self.min,self.sec])

def return_or(l):
	return ("|".join(list(map(lambda s: "("+s+")", l))))

def return_or2(l):
	return ("|".join(list(map(lambda s: "("+s+")", l))))


datalog = Log('test_messages',['1'])
for tag in MESSAGE_TAGS:
	datalog.add_test(Test(json_file_name=tag+".json"))

datalog.extract_data()
datalog.view_data()
