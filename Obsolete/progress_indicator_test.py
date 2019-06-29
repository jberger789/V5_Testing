import subprocess, time

FILENAME = "messages_multiday_test_cp"

p = subprocess.Popen(['wc', '-l', FILENAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
result, err = p.communicate()
if p.returncode != 0:
	raise IOError(err)
line_count = (float(result.strip().split()[0]))

print(line_count)
with open(FILENAME) as f:
	l_num = 0.0
	for line in f:
		l_num +=1.0
		perc = l_num/line_count
		print('\r'+str(perc*100)+'% Complete                        ', end='')
		time.sleep(0.001)
print(' ')

|=======             |	


