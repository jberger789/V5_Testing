import dataset, matplotlib.pyplot as plt
MESSAGE_TAGS = {1: 'STRESS_NG', 2: 'IPMITOOL', 3: 'STREAM_C', 4: 'DD_TEST', 5: 'HDPARM', 6: 'IPERF', 7: 'USB_PASSMARK',8: 'TAMPER_STATUS', 9: 'FIBER_FPGA_TEMP'}
TEST_OPTIONS = {
	'STRESS_NG': ['variable','rate','units'],
	'IPMITOOL': ['sensor','value','units'],
	'STREAM_C': ['function','avg_t',None],
	'DD_TEST': ['drive','rate',None],
	'HDPARM': ['read_type','read_rate',None],
	'IPERF': 'SPECIAL',
	'USB_PASSMARK': ['benchmark_type','avg_rate',None],
	'TAMPER_STATUS': 'SPECIAL',
	'FIBER_FPGA_TEMP': ['fpga_side','temp',None]
}
TEST_UNITS = {
	'STREAM_C': 'MB/s',
	'DD_TEST': 'MB/s',
	'HDPARM': 'MB/sec',
	'USB_PASSMARK': 'Mbit/s',
	'FIBER_FPGA_TEMP': 'Degrees C' 
}
SIDES = ['black','red']
DB = dataset.connect('mysql://guest:password@localhost/test_results')

def test_run_select():
	user_in = ''
	test_list = DB['TESTS'].find()
	rows = []
	ops = []
	for z in test_list:
		rows.append(z)
		ops.append(str(z['id']))
	while user_in != 'exit':
		user_in = input("Which test run would you like to see results for?\n")
		if user_in == 'h' or user_in == 'help':
			print("Enter 'options' for a list of valid responses, or 'exit' to stop the program")
		elif user_in == 'o' or user_in == 'options':
			print("The options are:\n"+"\n".join(list(map(lambda r: "Test {}: {} - {}".format(r['id'],r['start_time'],r['end_time']),rows))))
		elif  user_in in ops:
			test_select(rows[eval(user_in)-1]['start_time'],rows[eval(user_in)-1]['end_time'])



def test_select(start_time,end_time):
	user_in = ''
	while user_in != 'exit':
		user_in = input("Which test would you like to see results for?\n")
		if user_in == 'h' or user_in == 'help':
			print("Enter 'options' for a list of valid responses, or 'exit' to stop the program")
		elif user_in == 'o' or user_in == 'options':
			print("The options are:")
			for k in MESSAGE_TAGS:
				print("{}: {}".format(k,MESSAGE_TAGS[k]))
		elif user_in in MESSAGE_TAGS.values():
			user_in = graph_select(user_in)
		elif eval(user_in) in MESSAGE_TAGS:
			graph_select(MESSAGE_TAGS[eval(user_in)],start_time,end_time)
		else:
			if user_in != 'exit':
				print("That is not a valid response, check your spelling or type 'help' for assistance")



def graph_select(test_key,start_time,end_time):
	user_in = ''
	while user_in != 'go back' and user_in != 'return':
		if TEST_OPTIONS[test_key] != 'SPECIAL':
			user_in = input("Which {} would you like to see results for?\n".format(TEST_OPTIONS[test_key][0]))
			rows = DB[test_key].distinct(TEST_OPTIONS[test_key][0])
			if user_in == 'h' or user_in == 'help':
				print("Enter 'options' for a list of valid responses, or 'go back' to return to test selection")
			elif user_in == 'o' or user_in == 'options':
				print("The options are " + ", ".join(list(map(lambda r: str(r[TEST_OPTIONS[test_key][0]]), rows))))
			elif user_in in list(map(lambda r: str(r[TEST_OPTIONS[test_key][0]]), rows)):
				tmp_units = ''
				if TEST_OPTIONS[test_key][2] != None:
					tmp_units = DB.query("SELECT {} FROM {} WHERE `{}`='{}' LIMIT 1;".format(
						TEST_OPTIONS[test_key][2],test_key,TEST_OPTIONS[test_key][0],user_in)).next()[TEST_OPTIONS[test_key][2]]
				else:
					tmp_units = TEST_UNITS[test_key]
				generate_graph(test_key,user_in,tmp_units,start_time,end_time)
			elif user_in == 'exit':
				return user_in
		elif test_key == 'IPERF':
			user_in = input("Which results would you like to see?\n")
			options = ['bandwidth','loss_percentage','out_of_order_datagrams']
			if user_in == 'h' or user_in == 'help':
				print("Enter 'options' for a list of valid responses, or 'go back' to return to test selection")
			elif user_in == 'o' or user_in == 'options':
				print("The options are " + ", ".join(options))
			elif user_in in options:
				tmp_units = ''
				gen_IPERF_graph(user_in,start_time,end_time)
			elif user_in == 'exit':
				return user_in
		elif test_key == 'TAMPER_STATUS':
			user_in = input("Which results would you like to see?\n")
			options = ['voltage','tamper_events','other']
			if user_in == 'h' or user_in == 'help':
				print("Enter 'options' for a list of valid responses, or 'go back' to return to test selection")
			elif user_in == 'o' or user_in == 'options':
				print("The options are " + ", ".join(options))
			elif user_in in options:
				tmp_units = ''
				gen_TAMPER_graph(user_in,start_time,end_time)
			elif user_in == 'exit':
				return user_in
		else:
			pass


def generate_graph(test_key,sel_opt,units,start_time,end_time):
	results = []
	x=[]
	y=[]
	for s in SIDES:
		results.append(DB.query("SELECT * FROM {} WHERE side='{}' AND `{}`='{}' AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(test_key,s,TEST_OPTIONS[test_key][0],sel_opt,start_time,end_time)))
		x.append([])
		y.append([])
	

	for ind in range(len(SIDES)):
		for r in results[ind]:
			x[ind].append(r['time_stamp'])
			y[ind].append(r[TEST_OPTIONS[test_key][1]])

	plt.plot(x[0], y[0], color='black',linewidth=2)
	plt.plot(x[1], y[1], color='red',linewidth=1.5)

	plt.ylim(0,(max([max(y[0]),max(y[1])]))*2.5)
	
	plt.xlabel('Time')
	plt.ylabel(units)

	plt.title("{}: {}".format(test_key,sel_opt))

	plt.show()

def gen_IPERF_graph(sel_opt,start_time,end_time):
	results = {}
	x={}
	y={}
	ips = {'black': ['200.50','2.2','3.1'], 'red': ['200.20','2.1','3.2']}
	max_by_op = {'bandwidth': 20, 'loss_percentage': 100, 'out_of_order_datagrams': 1000}
	for s in SIDES:
		results[s] = {}
		x[s] = {}
		y[s] = {}
		for ip in ips[s]:
		#print("SELECT time_stamp,role,address,{} FROM IPERF WHERE side='{}' AND role='{}' AND (address='{}' OR address='{}') AND {} IS NOT NULL;".format(sel_opt,s,role,ip1,ip2,sel_opt))
			results[s][ip]=(DB.query("SELECT time_stamp,role,address,{} FROM IPERF WHERE PID='SUM' AND side='{}' AND (role='CLIENT' OR role='SERVER') AND (address='{}') AND {} IS NOT NULL  AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(sel_opt,s,ip,sel_opt,start_time,end_time)))
			x[s][ip]=[]
			y[s][ip]=[]
	
	for ind in range(0,3):
		for s in SIDES:
			for r in results[s][ips[s][ind]]:
				x[s][ips[s][ind]].append(r['time_stamp'])
				y[s][ips[s][ind]].append(r[sel_opt])
			plt.plot(x[s][ips[s][ind]], y[s][ips[s][ind]], color=s,linewidth=1)
		plt.ylim(0,max_by_op[sel_opt])
		plt.xlabel('Time')
		plt.ylabel(sel_opt)
		plt.title("IPERF {}.x: {}".format(ips[s][ind].split('.')[0],sel_opt))
		plt.show()

def gen_TAMPER_graph(sel_opt,start_time,end_time):
	results = {}
	x={}
	y={}
	max_by_op = {'voltage': 3500, 'tamper_events': 1000, 'other': 10}
	for s in SIDES:
		#print("SELECT time_stamp,role,address,{} FROM IPERF WHERE side='{}' AND role='{}' AND (address='{}' OR address='{}') AND {} IS NOT NULL;".format(sel_opt,s,role,ip1,ip2,sel_opt))
		results[s]=(DB.query("SELECT time_stamp,{} FROM TAMPER_STATUS WHERE side='{}' AND {} IS NOT NULL AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(sel_opt,s,sel_opt,start_time,end_time)))
		x[s]=[]
		y[s]=[]
	
	for s in SIDES:
		for r in results[s]:
			x[s].append(r['time_stamp'])
			y[s].append(r[sel_opt])
		plt.plot(x[s], y[s], color=s,linewidth=1)
	plt.ylim(0,max_by_op[sel_opt])
	plt.xlabel('Time')
	plt.ylabel(sel_opt)
	plt.title("TAMPER_STATUS: {}".format(sel_opt))
	plt.show()





test_run_select()









