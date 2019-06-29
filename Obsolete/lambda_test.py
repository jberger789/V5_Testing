import re, json

SIDES = {1: 'black',2:'red'}
#print (list(map(lambda s: "("+s+")", SIDES)))
#print("|".join(list(map(lambda s: "("+s+")", SIDES))))
def return_or(l):
	return ("|".join(list(map(lambda s: "("+s+")", list(l.values())))))
#print(return_or(SIDES))
#XE = {'1': 'one', '2': 'two'}
#print(str(list(XE.values())))



dd_re = r"""
				(?P<mon>\b\w\w\w\b)\s+(?P<day>\b\d{1,2}\b)\s+(?P<hr>\d\d):(?P<min>\d\d):(?P<sec>\d\d)
				\s
				(?P<side>red)
				-
				(?P<unit>1)
				\s+
				(?P<tag>DD_TEST)
				_(?P<drive>SD[AB]):
				\s+
				(
				(?P<records_in>[\d]+[+][\d]+)
				|
				(?P<records_out>[\d]+[+][\d]+)
				|
				((?P<bytes_copied>\b[\d]+\b).*\(.+\).*(?P<duration>\b\d+[.]\d+)\s+s,\s*(?P<rate>\d+([.]\d*)?))
				)
"""
q = re.compile(dd_re,re.VERBOSE)
p = re.compile(r"""
				(
				(?P<records_in>[\d]+[+][\d]+)
				|
				(?P<records_out>[\d]+[+][\d]+)
				|
				((?P<bytes_copied>\b[\d]+\b).*\(.+\).*(?P<duration>\b\d+[.]\d+)\s+s,\s*(?P<rate>\d+([.]\d*)?))
				)
			""",re.VERBOSE)


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


m = q.search('Jun  5 11:10:34 red-1 DD_TEST_SDA: 1+0 records in')
#print(m.group('drive'))

json_test = r'''
{
	"tag": "IPMITOOL",
	"call": null,
	"re_string": [
		":\\s+",
		"(?P<sensor>\\b[\\w.]+\\b(\\s\\b\\w+\\b)?)",
		"\\s+\\|\\s+",
		"(?P<value>\\b[\\w.]+\\b)",
		"\\s+\\|\\s+",
		"(?P<units>(\\b[\\w]+\\b)(\\s\\b[\\w]+\\b)?)",
		"\\s*\\|\\s+",
		"(?P<status>\\b[\\w]+\\b)",
		"\\s*\\|\\s+",
		"(?P<lo_norec>(\\d+[.]\\d+)|(na))",
		"\\s+\\|\\s+",
		"(?P<lo_crit>(\\d+[.]\\d+)|(na))",
		"\\s+\\|\\s+",
		"(?P<lo_nocrit>(\\d+[.]\\d+)|(na))",
		"\\s+\\|\\s+",
		"(?P<up_nocrit>(\\d+[.]\\d+)|(na))",
		"\\s+\\|\\s+",
		"(?P<up_crit>(\\d+[.]\\d+)|(na))",
		"\\s+\\|\\s+",
		"(?P<up_norec>(\\d+[.]\\d+)|(na))"
	],
	"key_tag": "sensor",
	"data_info": [
		"value",
		"units",
		"status",
		"lo_norec",
		"lo_crit",
		"lo_nocrit",
		"up_nocrit",
		"up_crit",
		"up_norec"
	]
}
'''

class test_json(json.JSONEncoder):
	def default(self, o):
		if (type(o) == Test):
			return{'tag': o.tag, 'call': o.call, 're_string': (list(map(lambda s: s.strip('\t'), o.re_string.split('\n')))), 'key_tag': o.key_tag, 'data_info': o.data_info}
		else:
			return json.JSONEncoder.default(self, o)


#tmp = json.JSONDecoder(strict=False)
with open("IPMITOOL.json") as test_file:
	x = (json.load(test_file))
#x = json.JSONDecoder().decode(json_test)
print('\n'.join(x['re_string']))
#datalog.add_test(Test("DD_TEST",None,dd_re,'drive',['records_in','records_out','bytes_copied','duration','Rate']))

