import dataset, matplotlib.pyplot as plt, datetime, json
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button

MESSAGE_TAGS = {1: 'STRESS_NG', 2: 'IPMITOOL', 3: 'STREAM_C', 4: 'DD_TEST', 5: 'HDPARM', 6: 'IPERF', 7: 'USB_PASSMARK',8: 'TAMPER_STATUS', 9: 'FIBER_FPGA_TEMP'}
TEST_OPTIONS = {
	'STRESS_NG': ['variable','rate','units'],
	'IPMITOOL': ['sensor','value','units'],
	'STREAM_C': ['function','rate',None],
	'DD_TEST': ['drive','rate',None],
	'HDPARM': ['read_type','read_rate',None],
	'IPERF': '',
	'USB_PASSMARK': ['benchmark_type','avg_rate',None],
	'TAMPER_STATUS': 'SPECIAL',
	'FIBER_FPGA_TEMP': ['fpga_side','temp',None]
}
TEST_UNITS = {
	'STREAM_C': 'MB/s',
	'DD_TEST': 'MB/s',
	'HDPARM': 'MB/sec',
	'USB_PASSMARK': 'Mbit/s',
	'FIBER_FPGA_TEMP': '°C' 
}
SIDES = {'BLK': 'black','RED': 'red'}
TEMPERATURE_OPS = ['intake','outtake','ambient']
DB = dataset.connect('mysql://guest:password@localhost/test_results')

tests = {}

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
			user_in = graph_select(user_in,start_time,end_time)
		elif eval(user_in) in MESSAGE_TAGS:
			graph_select(MESSAGE_TAGS[eval(user_in)],start_time,end_time)
		else:
			if user_in != 'exit':
				print("That is not a valid response, check your spelling or type 'help' for assistance")



def graph_select(test_key,start_time,end_time):
	user_in = ''
	cur_test = tests[test_key]
	if cur_test.data_key != None:
		rows = DB[test_key].distinct(cur_test.data_key)
		ops = []
		for r in rows:
			ops.append(str(r[cur_test.data_key]))
		op_name = cur_test.data_key
	else:
		ops = cur_test.key_list
		op_name = "values"
	while user_in != 'go back' and user_in != 'return':
		if TEST_OPTIONS[test_key] != 'SPECIAL':
			user_in = input("Which {} would you like to see results for?\n".format(op_name))
			if user_in == 'h' or user_in == 'help':
				print("Enter 'options' for a list of valid responses, or 'go back' to return to test selection")
				print(ops)
			elif user_in == 'o' or user_in == 'options':
				print("The options are \n" + " || ".join(ops))
			elif user_in in ops:
				if cur_test.tag == 'IPERF':
					gen_IPERF_graph(user_in,start_time,end_time)
				else:
					generate_graph(cur_test,user_in,start_time,end_time)
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

def get_data(cur_test,sel_opt,start_time,end_time, where_addendum = ""):
	x,y={},{}
	if (cur_test.data_key != None):
		for s in SIDES:
			results=(DB.query("SELECT * FROM {} WHERE side='{}' AND `{}`='{}' AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(cur_test.tag,s,cur_test.data_key,sel_opt,start_time,end_time)))
			x[s],y[s]=[],[]
			for r in results:
				x[s].append(r['time_stamp'])
				if (cur_test.tag == 'USB_PASSMARK' and sel_opt == 'error counter'):
					y[s].append(r['error_count'])
				else:
					y[s].append(r[cur_test.data_tag])
				#print(x[s])
				#print(y[s])
	else:
		for s in SIDES:
			results=(DB.query("SELECT * FROM {} WHERE side='{}' AND `{}` IS NOT NULL AND (time_stamp >= '{}' AND time_stamp <= '{}')".format(cur_test.tag,s,sel_opt,start_time,end_time)+ where_addendum + ";"))
			x[s],y[s]=[],[]
			for r in results:
				x[s].append(r['time_stamp'])
				y[s].append(r[sel_opt])
	return x,y

def determine_units(cur_test,sel_opt):
	units = ""
	if cur_test.units_key != None and cur_test.units_key in cur_test.data_info:
		if cur_test.data_key != None:
			units = DB.query("SELECT {} FROM {} WHERE `{}`='{}' LIMIT 1;".format(cur_test.units_key,cur_test.tag,cur_test.data_key,sel_opt)).next()[cur_test.units_key]
		else:
			units = DB.query("SELECT {} FROM {} WHERE `{}` IS NOT NULL LIMIT 1;".format(cur_test.units_key,cur_test.tag,sel_opt)).next()[cur_test.units_key]
	elif cur_test.units_dict != None:
		units = cur_test.units_dict[sel_opt]
	else:
		units = cur_test.units_key

	return units

def generate_graph(cur_test,sel_opt,start_time,end_time,max_y=None, where_addendum = "", sub_title = ""):
	units = determine_units(cur_test,sel_opt)
	x,y=get_data(cur_test,sel_opt,start_time,end_time,where_addendum)
	x_tmp, y_tmp = map_time2temp(x,y)
	if max_y == None:
		max_y = max(y['RED'])*2.5 + 5
	"""for s in SIDES:
		results=(DB.query("SELECT * FROM {} WHERE side='{}' AND `{}`='{}' AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(test_key,s,TEST_OPTIONS[test_key][0],sel_opt,start_time,end_time)))
		x[s]=[]
		y[s]=[]
		for r in results:
			x[s].append(r['time_stamp'])
			y[s].append(r[TEST_OPTIONS[test_key][1]])"""

	

	upper_info = {'xlabel': 'Time', 'ylabel': sel_opt + " (" + units + ")", 'ylim': max_y, 'fmt': '-'}
	lower_info = {'xlabel': 'Temperature', 'ylabel': sel_opt + " " + units, 'ylim': max_y, 'fmt': '.', 'xunits': "°C"}
	one_and_three_fig(x,y,upper_info,x_tmp,y_tmp,lower_info,{'tag': cur_test.tag + sub_title,'test_opt': sel_opt})
	plt.show()


"""def generate_graph(test_key,sel_opt,units,start_time,end_time):
	results = {}
	x={}
	y={}
	for s in SIDES:
		results[s]=(DB.query("SELECT * FROM {} WHERE side='{}' AND `{}`='{}' AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(test_key,s,TEST_OPTIONS[test_key][0],sel_opt,start_time,end_time)))
		x[s]=[]
		y[s]=[]
				

	for s in SIDES:
		for r in results[s]:
			x[s].append(r['time_stamp'])
			y[s].append(r[TEST_OPTIONS[test_key][1]])
		#print(len(x[s]))
		#print(len(y[s]))
	user_in = input("VS Time (t) or Temperature (tmp)?\n")
	if (user_in == "Temperature" or user_in == "tmp"):
		x = gen_temp_graph(x,y)
		line_style = '.'
		plot_ind = 0
		fig, axs = plt.subplots(1, 3, sharey=True)
		fig.subplots_adjust(wspace=0)
		axs[0].set_ylabel(units)
		for key in x:
			for s in SIDES:
				axs[plot_ind].plot(x[key][s], y[s], line_style, color=SIDES[s])
			axs[plot_ind].set_xlabel('Temperature ({}) °C'.format(key))
			axs[plot_ind].set_ylim(0,(max(y[s])*2.5))
			plot_ind+=1
		fig.suptitle("{}: {}".format(test_key,sel_opt))
		
	else:
		line_style = '-'
		plt.xlabel('Time')
		for s in SIDES:
			if (len(x[s]) > 0 and len(y[s]) > 0):
				plt.plot(x[s], y[s], line_style, color=SIDES[s])		
			plt.ylabel(units)
	plt.show()"""

def gen_IPERF_graph(sel_opt,start_time,end_time):
	cur_test = tests['IPERF']
	#x,y={},{}
	ips = {'BLK': {'Ethernet':'200.50','Fiber (Black)':'2.2','Fiber (Red)':'3.1'}, 'RED': {'Ethernet':'200.20','Fiber (Black)':'2.1','Fiber (Red)':'3.2'}}
	interfaces = ['Ethernet', 'Fiber (Black)', 'Fiber (Red)']
	max_by_op = {'bandwidth': 20, 'loss_percentage': 100, 'out_of_order_datagrams': 1000}

	for i in interfaces:
		where_addendum = " AND PID='SUM' AND role='SERVER' AND (address='{}' OR address='{}')".format(ips['RED'][i],ips['BLK'][i])
		generate_graph(cur_test,sel_opt,start_time,end_time,max_by_op[sel_opt],where_addendum, ": "+ i)
		#query_str = "SELECT time_stamp,role,address,transfer_units,{} FROM IPERF WHERE PID='SUM' AND role='SERVER' AND (address='{}' OR address='{}') AND {} IS NOT NULL  AND (time_stamp >= '{}' AND time_stamp <= '{}')".format(sel_opt,s,ips['RED'][i],ips['BLK'][i],sel_opt,start_time,end_time))

	"""for i in interfaces:
		x[i],y[i] = {},{}
		for s in SIDES:
			x[i][s] = []
			y[i][s] = []
			#print("SELECT time_stamp,role,address,{} FROM IPERF WHERE PID='SUM' AND side='{}' AND role='SERVER' AND (address='{}') AND {} IS NOT NULL  AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(sel_opt,,ips[s][ind],sel_opt,start_time,end_time))
			results=(DB.query("SELECT time_stamp,role,address,transfer_units,{} FROM IPERF WHERE PID='SUM' AND side='{}' AND role='SERVER' AND (address='{}') AND {} IS NOT NULL  AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(sel_opt,s,ips[s][i],sel_opt,start_time,end_time)))
			for r in results:
				if (sel_opt == 'out_of_order_datagrams' or r['transfer_units'] != 'NULL'):
					x[i][s].append(r['time_stamp'])
					y[i][s].append(r[sel_opt])

	x_tmp, y_tmp = {}, {}
	for i in interfaces:
		x_tmp[i], y_tmp[i] = map_time2temp(x[i],y[i])


	upper_info = {'xlabel': 'Time', 'ylabel': sel_opt, 'ylim': max_by_op[sel_opt], 'fmt': '-'}
	lower_info = {'xlabel': 'Temperature', 'ylabel': sel_opt, 'ylim': max_by_op[sel_opt], 'fmt': '.', 'xunits': "°C"}

	for i in interfaces:
		one_and_three_fig(x[i],y[i],upper_info,x_tmp[i],y_tmp[i],lower_info,{'tag': 'IPERF '+i,'test_opt': sel_opt})
		plt.show()"""

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
		plt.plot(x[s], y[s], color=SIDES[s],linewidth=1)
	plt.ylim(0,max_by_op[sel_opt])
	plt.xlabel('Time')
	plt.ylabel(sel_opt)
	plt.title("TAMPER_STATUS: {}".format(sel_opt))
	plt.show()


def map_time2temp(times,data):
	temps_list,temp_data={},{}
	for i in TEMPERATURE_OPS:
		temps_list[i],temp_data[i] = {},{}
	for s in SIDES:
		for k in temps_list:
			temps_list[k][s] = []
			temp_data[k][s]  = data[s]
		for ts in times[s]:
			temp_tm = ts + datetime.timedelta(seconds=round(ts.second/10+0.001)*10 - ts.second)
			temp_row = DB['TEMPERATURES'].find_one(side=s,time_stamp=temp_tm)
			while not temp_row:
				temp_tm+=datetime.timedelta(seconds=10)
				temp_row = DB['TEMPERATURES'].find_one(side=s,time_stamp=temp_tm)
			for key in temps_list:
				temps_list[key][s].append(temp_row[key])

	return temps_list, temp_data


def one_and_three_fig(upperx,uppery,upper_info,lowerx,lowery,lower_info,fig_info):
	fig = plt.figure()
	plt.subplots_adjust(hspace=0.3)
	gs = GridSpec(2, 3, figure=fig)
	axt = fig.add_subplot(gs[0, :])
	axb = []
	for i in range(0,3):
		axb.append(fig.add_subplot(gs[1, i]))
	for s in SIDES:
		if (len(upperx[s]) > 0 and len(uppery[s]) > 0):
			my_plotter(axt,upperx[s],uppery[s],upper_info['fmt'],{'color':SIDES[s]})
	axt.set_ylabel(upper_info['ylabel'])
	axt.set_xlabel(upper_info['xlabel'])
	axt.set_ylim(0,(upper_info['ylim']))
	lower_ind = 0
	axb[lower_ind].set_ylabel(lower_info['ylabel'])
	for key in lowerx:
		for s in SIDES:
			my_plotter(axb[lower_ind],lowerx[key][s],lowery[key][s],lower_info['fmt'],{'color':SIDES[s]})
		axb[lower_ind].set_xlabel('{}: ({}) {}'.format(lower_info['xlabel'],key,lower_info['xunits']))
		axb[lower_ind].set_ylim(0,lower_info['ylim'])
		lower_ind+=1
	fig.suptitle("{}: {}".format(fig_info['tag'],fig_info['test_opt']))


def my_plotter(ax,xdata,ydata,fmt, param_dict):
	out = ax.plot(xdata, ydata, fmt, **param_dict)
	return out

class Test(object):
	def __init__(self,json_file_name):
		with open(json_file_name) as json_file:
			json_dict = (json.load(json_file))
			self.tag = json_dict['tag']
			self.call = json_dict['call']
			self.data_key = json_dict['data_key']
			self.data_tag = json_dict['data_tag']
			self.key_list = json_dict['key_list']
			self.units_key = json_dict['units_key']
			self.units_dict = json_dict['units_dict']
			self.data_info = json_dict['data_info']




for n in MESSAGE_TAGS:
	tests[MESSAGE_TAGS[n]] = Test("../Tests/"+MESSAGE_TAGS[n]+".json")

test_run_select()









