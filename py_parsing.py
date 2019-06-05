import re, os

SIDES = ['black','red']
MESSAGE_TAGS = ['IPMITOOL','stress-ng', 'STREAM_C', 'DD_TEST_SDA', 'DD_TEST_SDB', 'HDPARM_SDA', 'HDPARM_SDB']

messages_file = open('test_messages', 'r')

re_sideN = re.compile('(?P<side>('+SIDES[0]+')|('+SIDES[1]+'))-(?P<num>\d+)')

re_by_tag = []
for tag in MESSAGE_TAGS:
	re_by_tag.append(re.compile(tag))

for line in messages_file:
	m = re_sideN.search(line)
	if m:
		dirName = m.group('side')+'_'+m.group('num');
		if not os.path.exists(dirName):
			os.mkdir(dirName)
		for i in range(0,len(MESSAGE_TAGS)):
			if re_by_tag[i].search(line):
				with open(dirName+"/messages"+MESSAGE_TAGS[i]+".txt",'a') as f:
					f.write(line)