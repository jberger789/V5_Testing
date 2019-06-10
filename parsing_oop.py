import re, os

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST_SDA', 'DD_TEST_SDB', 'HDPARM_SDA', 'HDPARM_SDB', 
	'IPERF_SERVER_2.2', 'IPERF_SERVER_3.2', 'IPERF_SERVER_200.20', 'IPERF_CLIENT_2.1', 'IPERF_CLIENT_200.20', 
	'IPERF_SERVER_200.50', 'IPERF_CLIENT_3.1', 'IPERF_CLIENT_200.50']


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
		total_reg_form = r"""
			(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
			\s
			(?P<side>"""+return_or(SIDES)+r""")
			-
			(?P<unit>"""+return_or(list(map(lambda u: u.unit_num,  list(self.units.values()))))+r""")
			\s+
			(?P<tag>"""+return_or(list(map(lambda t: t.tag,  list(self.tests.values()))))+r""")
			("""+return_or(list(map(lambda t: t.data_regex,  list(self.tests.values()))))+r""")
			.*$"""
		print(self.tests)
		print(total_reg_form)
		re_total = re.compile(total_reg_form,re.VERBOSE)
		with open(self.message_file_name) as f:
			for line in f:
				#print(re_total.findall(line))
				m = re_total.match(line)
				#print(m)
				if (m != None):
					cur_test = self.tests[m.group('tag')]
					#print(m.group('drive'))
					cur_test.add_key(m.group(cur_test.key_tag))
					cur_time = Time_Stamp(m.group('mon'),m.group("day"),m.group("hr"),m.group("min"),m.group("sec"))
					self.units[m.group('unit')].sides[m.group('side')].add_data(cur_test.tag, cur_test.generate_datagram(
						m.group(cur_test.key_tag),cur_time,(list(map(lambda val: m.group(val), cur_test.data_info)))))

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
			user_in = input("Which "+test.key_tag+" would you like to see info for (or type options): ")
			if user_in == "options" or user_in == 'o':
				print("The options are " + ", ".join(list(cur_test_dict)))
			elif user_in in cur_test_dict:
				#for datum in self.data_dict[user_in]:
				for dp in cur_test_dict[user_in]:
						print(str(dp.time_stamp)+": "+str(dp.data_dict))
			#print (cur_test_dict)

class Test(object):
	def __init__(self,tag,call,data_regex,key_tag,data_info):
		self.tag = tag
		self.call = call
		self.data_regex = data_regex
		self.data = {}
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


ipmi_re = r"""
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
"""

stress_ng_re = r"""
	:\s+
	.*
	(?P<count>\d+(,\d+)*)
	\s+
	(?P<variable>(\s?\b\w+\b)+)
	\s+
	(?P<Rate>\d+[.]\d+)
	\s+
	(?P<Units>[MBK]?/sec)
	\s*
	([(]\s*(?P<extra>.*)[)])?
"""

#dd_re = r"""_(?P<drive>SD[AB]):\s+((?P<records_in>[\d]+[+][\d]+)|(?P<records_out>[\d]+[+][\d]+)|((?P<bytes_copied>\b[\d]+\b).*\(.+\).*(?P<duration>\b\d+[.]\d+)\s+s,\s*(?P<rate>\d+([.]\d*)?)))"""
"""dd_re = r
	:\s+
	.*
	(?P<drive>\d+(,\d+)*)
	\s+
	(?P<rat>(\s?\b\w+\b)+)
	\s+
	(?P<x>\d+[.]\d+)
	\s+
	(?P<y>[MBK]?/sec)
	\s*
	([(]\s*(?P<z>.*)[)])?
"""


dd_re = r"""
	_(?P<drive>SD[AB])
	:\s+
	((?P<records_in>[\d]+[+][\d]+)
	|
	(?P<records_out>[\d]+[+][\d]+)
	|
	((?P<bytes_copied>\b[\d]+\b).*\(.+\).*(?P<duration>\b\d+[.]\d+)\s+s,\s*(?P<ratE>\d+([.]\d*)?)))
"""


stream_c_re = r"""
				:\s+
				.*
				(?P<function>\b\w+\b)
				:\s+
				(?P<rate>\d+[.]\d+)
				\s+
				(?P<avg_t>\d+[.]\d+)
				\s+
				(?P<min_t>\d+[.]\d+)
				\s+
				(?P<max_t>\d+[.]\d+)
			"""

hdparm_re = r"""
	_(?P<Drive>SD[AB])
	:\s+
	Timing\s(?P<read_type>(cached)|(buffered disk))\sreads:
	\s+
	(?P<size>\d+)\s[M]B
	\s+
	in\s+(?P<timing>\d+[.]\d+)\sseconds\s=
	\s+
	(?P<read_rate>\d+[.]\d+)\s[M]B/sec
"""

#test_list = {}
#test_list.append(ipmi_test)
#print(str(list(test_list.values())))

datalog = Log('test_messages',['1'])
datalog.add_test(Test("IPMITOOL", None, ipmi_re, 'sensor', ['value','units','status','lo_norec','lo_crit','lo_nocrit','up_nocrit','up_crit','up_norec']))
datalog.add_test(Test("stress-ng",None, stress_ng_re,'variable', ['count','variable','Rate','Units','extra']))
datalog.add_test(Test("STREAM_C",None, stream_c_re,'function', ['rate','avg_t','min_t','max_t']))
datalog.add_test(Test("DD_TEST",None, dd_re,'drive',['records_in','records_out','bytes_copied','duration','ratE']))
datalog.add_test(Test("HDPARM",None, hdparm_re,'Drive',['read_type','size','timing','read_rate']))
#print(datalog.tests["DD_TEST"].key_tag)

#datalog.split_by_unit()

#isolate_data(datalog,test_list)
datalog.extract_data()
datalog.view_data()
#for test in test_list:
#	datalog.add_test(test)































