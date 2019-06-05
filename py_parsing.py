import re, os

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST_SDA', 'DD_TEST_SDB', 'HDPARM_SDA', 'HDPARM_SDB', 
	'IPERF_SERVER_2.2', 'IPERF_SERVER_3.2', 'IPERF_SERVER_200.20', 'IPERF_CLIENT_2.1', 'IPERF_CLIENT_200.20', 'IPERF_SERVER_200.50', 'IPERF_CLIENT_3.1', 'IPERF_CLIENT_200.50']

messages_file = open('test_messages', 'r')

unit_num = 1
while os.path.exists("Unit_"+str(unit_num)):
	os.system("rm -r Unit_"+str(unit_num))
	unit_num += 1

re_sideN = re.compile('(?P<side>('+SIDES[0]+')|('+SIDES[1]+'))-(?P<unit_num>\d+)')

"""re_by_tag = []
for tag in MESSAGE_TAGS:
	re_by_tag.append(re.compile(tag))"""


for line in messages_file:
	m = re_sideN.search(line)
	if m:
		if not os.path.exists('Unit_'+m.group('unit_num')):
			os.mkdir('Unit_'+m.group('unit_num'))
		dirName = 'Unit_'+m.group('unit_num')+'/'+m.group('side')
		if not os.path.exists(dirName):
			os.mkdir(dirName)
		for tag in MESSAGE_TAGS: #range(0,len(MESSAGE_TAGS)):
			#if re_by_tag[i].search(line):
			tag_ind = line.find(tag)
			if not tag_ind == -1:
				with open(dirName+"/"+tag+".txt",'a') as f:
					#f.write(line)
					f.write(line[0:tag_ind-3-len(m.group('unit_num'))-len(m.group('side'))]+line[tag_ind+len(tag):])