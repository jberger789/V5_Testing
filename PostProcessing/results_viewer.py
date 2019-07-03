import dataset, matplotlib.pyplot as plt, datetime, json
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button

MESSAGE_TAGS = {1: 'STRESS_NG', 2: 'IPMITOOL', 3: 'STREAM_C', 4: 'DD_TEST', 5: 'HDPARM', 6: 'IPERF', 7: 'USB_PASSMARK',8: 'TAMPER_STATUS', 9: 'FIBER_FPGA_TEMP', 10: 'PING_TEST', 11: 'UPTIME'}
TEST_OPTIONS = {
	'STRESS_NG': ['variable','rate','units'],
	'IPMITOOL': ['sensor','value','units'],
	'STREAM_C': ['function','rate',None],
	'DD_TEST': ['drive','rate',None],
	'HDPARM': ['read_type','read_rate',None],
	'IPERF': '',
	'USB_PASSMARK': ['benchmark_type','avg_rate',None],
	'TAMPER_STATUS': '',
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
			print(return_help)
			#print("Enter 'options' for a list of valid responses, or 'exit' to stop the program")
		elif user_in == 'o' or user_in == 'options':
			print(return_options((f"Test {r['id']}: {r['start_time']} - {r['end_time']}" for r in rows),'\n'))
			#print("The options are:\n"+"\n".join(list(map(lambda r: "Test {}: {} - {}".format(r['id'],r['start_time'],r['end_time']),rows))))
		elif  user_in in ops:
			test_select(rows[eval(user_in)-1]['start_time'],rows[eval(user_in)-1]['end_time'])



def test_select(start_time,end_time):
	user_in = ''
	while user_in != 'exit':
		user_in = input("Which test would you like to see results for?\n")
		if user_in == 'h' or user_in == 'help':
			print(return_help)
			#print("Enter 'options' for a list of valid responses, or 'exit' to stop the program")
		elif user_in == 'o' or user_in == 'options':
			print(return_options((f"{k}: {MESSAGE_TAGS[k]}" for k in MESSAGE_TAGS),'\n'))
			#print("The options are:")
			#for k in MESSAGE_TAGS:
			#	print("{}: {}".format(k,MESSAGE_TAGS[k]))
		elif user_in == 's' or user_in == 'save':
			autogenerate_graphs(start_time,end_time)
		elif user_in == 't':
			gen_temp_graph(start_time,end_time)
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
		user_in = input("Which {} would you like to see results for?\n".format(op_name))
		if user_in == 'h' or user_in == 'help':
			print(return_help)
			#print("Enter 'options' for a list of valid responses, or 'go back' to return to test selection")
		elif user_in == 'o' or user_in == 'options':
			print(return_options(ops,' || '))
		elif user_in in ops:
			if cur_test.tag == 'IPERF':
				gen_IPERF_graph(user_in,start_time,end_time)
			else:
				generate_graph(cur_test,user_in,start_time,end_time)
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

def generate_graph(cur_test,sel_opt,start_time,end_time,max_y=None, where_addendum = "", sub_title = "", save_to_file=False):
	units = determine_units(cur_test,sel_opt)
	x,y=get_data(cur_test,sel_opt,start_time,end_time,where_addendum)
	x_tmp, y_tmp = map_time2temp(x,y)
	#print(x)
	if cur_test.tag == 'TAMPER_STATUS':
		max_y = 3500
	if max_y == None:
		if len(y['RED']) > 0:
			max_y = max(y['RED'])*2.5 + 5
		else:
			max_y = 10
	

	upper_info = {'xlabel': 'Time', 'ylabel': sel_opt + " (" + units + ")", 'ylim': max_y, 'fmt': '-'}
	lower_info = {'xlabel': 'Temperature', 'ylabel': sel_opt + " " + units, 'ylim': max_y, 'fmt': '.', 'xunits': "°C"}
	fig_info = {'tag': cur_test.tag + sub_title,'test_opt': sel_opt}
	one_and_three_fig(x,y,upper_info,x_tmp,y_tmp,lower_info,fig_info)
	if save_to_file:
		plt.savefig("../Graphs/{} ({}).png".format(fig_info['tag'],fig_info['test_opt']))
	else:
		plt.show()
		

def gen_IPERF_graph(sel_opt,start_time,end_time,stf=False):
	cur_test = tests['IPERF']
	#x,y={},{}
	ips = {'BLK': {'Ethernet':'200.50','Fiber (Black)':'2.2','Fiber (Red)':'3.1'}, 'RED': {'Ethernet':'200.20','Fiber (Black)':'2.1','Fiber (Red)':'3.2'}}
	interfaces = ['Ethernet', 'Fiber (Black)', 'Fiber (Red)']
	max_by_op = {'bandwidth': 20, 'loss_percentage': 100, 'out_of_order_datagrams': 1000}

	for i in interfaces:
		where_addendum = " AND PID='SUM' AND role='SERVER' AND (address='{}' OR address='{}')".format(ips['RED'][i],ips['BLK'][i])
		generate_graph(cur_test,sel_opt,start_time,end_time,max_by_op[sel_opt],where_addendum, ": "+ i,save_to_file=stf)
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

# def gen_TAMPER_graph(sel_opt,start_time,end_time):
# 	results = {}
# 	x={}
# 	y={}
# 	max_by_op = {'voltage': 3500, 'tamper_events': 1000, 'other': 10}
# 	for s in SIDES:
# 		#print("SELECT time_stamp,role,address,{} FROM IPERF WHERE side='{}' AND role='{}' AND (address='{}' OR address='{}') AND {} IS NOT NULL;".format(sel_opt,s,role,ip1,ip2,sel_opt))
# 		results[s]=(DB.query("SELECT time_stamp,{} FROM TAMPER_STATUS WHERE side='{}' AND {} IS NOT NULL AND (time_stamp >= '{}' AND time_stamp <= '{}');".format(sel_opt,s,sel_opt,start_time,end_time)))
# 		x[s]=[]
# 		y[s]=[]
	
# 	for s in SIDES:
# 		for r in results[s]:
# 			x[s].append(r['time_stamp'])
# 			y[s].append(r[sel_opt])
# 		plt.plot(x[s], y[s], color=SIDES[s],linewidth=1)
# 	plt.ylim(0,max_by_op[sel_opt])
# 	plt.xlabel('Time')
# 	plt.ylabel(sel_opt)
# 	plt.title("TAMPER_STATUS: {}".format(sel_opt))
# 	plt.show()


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

def gen_temp_graph(start_time,end_time):
	temperatures = ['ambient','intake','outtake']
	x,y = {},{}

	for loc in temperatures:
		x[loc],y[loc] = {},{}
		for s in SIDES:
			x[loc][s] = []
			y[loc][s] = []

	results=(DB.query("SELECT * FROM TEMPERATURES WHERE (time_stamp >= '{}' AND time_stamp <= '{}');".format(start_time,end_time)))
	for r in results:
		s = r['side']
		for loc in temperatures:
			x[loc][s].append(r['time_stamp'])			
			y[loc][s].append(r[loc])

	info = {'xlabel': "time",'ylabel': "Temperature", 'yunits': '°C','ylim': 100,'fmt': '-'}
	fig_info = {'tag': "Temperature", 'test_opt': ""}

	#three_vert_fig(x,y,info,fig_info)
	tricolor_fig(x,y,info,fig_info)
	plt.show()

def one_and_three_fig(upperx,uppery,upper_info,lowerx,lowery,lower_info,fig_info):
	fig = plt.figure(figsize=(15,9))
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
			if (len(lowerx[key][s]) > 0 and len(lowerx[key][s]) > 0):
				#print(lowery[key][s])
				#print(lowerx[key][s])
				my_plotter(axb[lower_ind],lowerx[key][s],lowery[key][s],lower_info['fmt'],{'color':SIDES[s]})
		axb[lower_ind].set_xlabel('{}: ({}) {}'.format(lower_info['xlabel'],key,lower_info['xunits']))
		axb[lower_ind].set_ylim(0,lower_info['ylim'])
		lower_ind+=1
	fig.suptitle("{}: {}".format(fig_info['tag'],fig_info['test_opt']))

def three_vert_fig(x,y,info, fig_info):
	fig = plt.figure(figsize=(15,9))
	plt.subplots_adjust(hspace=0.3)
	gs = GridSpec(3, 1, figure=fig)
	ay = []
	for i in range(0,3):
		ay.append(fig.add_subplot(gs[i, 0]))
	lower_ind = 2
	ay[lower_ind].set_xlabel(info['xlabel'])
	for key in y:
		for s in SIDES:
			my_plotter(ay[lower_ind],x[key][s],y[key][s],info['fmt'],{'color':SIDES[s]})
		ay[lower_ind].set_ylabel('{}: ({}) {}'.format(info['ylabel'],key,info['yunits']))
		ay[lower_ind].set_ylim(0,info['ylim'])
		lower_ind-=1
	fig.suptitle("{}: {}".format(fig_info['tag'],fig_info['test_opt']))


def tricolor_fig(x,y,info, fig_info):
	fig = plt.figure(figsize=(15,9))
	plt.subplots_adjust(hspace=0.3)
	gs = GridSpec(1, 1, figure=fig)
	ay = (fig.add_subplot(gs[0, 0]))
	color_dict={"BLK": ['black','green','blue'], "RED": ['red','yellow','orange']}
	ind = 0
	ay.set_xlabel(info['xlabel'])
	for key in y:
		for s in SIDES:
			my_plotter(ay,x[key][s],y[key][s],info['fmt'],{'color':color_dict[s][ind]})
		ind+=1
	ay.set_ylabel('{}: ({}) {}'.format(info['ylabel'],key,info['yunits']))
	ay.set_ylim(0,info['ylim'])
	fig.suptitle("{}: {}".format(fig_info['tag'],fig_info['test_opt']))

def my_plotter(ax,xdata,ydata,fmt, param_dict):
	out = ax.plot(xdata, ydata, fmt, **param_dict)
	return out


def return_options(options_list,sep_char):
	return("The options are \n" + sep_char.join(list(options_list)))

def return_help():
	return("Type '(h)elp' to bring up this prompt, '(o)ptions' for a list of viable responses,\n"
		"'go back' to return to the previous prompt, or 'exit' to end the program")

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


def autogenerate_graphs(start_time,end_time):
	print("Start: {}".format(datetime.datetime.today()))
	test_data_graphs = {
	"STRESS_NG": ['Instructions','CPU Cycles'],
	"IPMITOOL": ['CPU Temp', 'FAN1', 'FAN2', 'FANA', '5VCC', '5VSB', '3.3VCC', '3.3VSB', '12V'],
	"STREAM_C": ['Add','Copy'],
	"IPERF": ['bandwidth','loss_percentage','out_of_order_datagrams'],
	"USB_PASSMARK": ['error counter', 'Read', 'Write'],
	"TAMPER_STATUS": ['voltage'],
	"PING_TEST": ['packet_loss','total_time','average'],
	"UPTIME": ['load_avg']
	}
	for test in test_data_graphs:
		for option in test_data_graphs[test]:
			if test == 'IPERF':
				gen_IPERF_graph(option,start_time,end_time,stf=True)
			else:
				generate_graph(tests[test],option,start_time,end_time,save_to_file=True)

	print("End: {}".format(datetime.datetime.today()))

for n in MESSAGE_TAGS:
	tests[MESSAGE_TAGS[n]] = Test("../Tests/"+MESSAGE_TAGS[n]+".json")

test_run_select()










