import dataset, matplotlib.pyplot as plt, datetime, json
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button

MESSAGE_TAGS = {1: 'STRESS_NG', 2: 'IPMITOOL', 3: 'STREAM_C', 4: 'DD_TEST', 5: 'HDPARM', 6: 'IPERF', 7: 'USB_PASSMARK',8: 'TAMPER_STATUS', 9: 'FIBER_FPGA_TEMP', 10: 'PING_TEST', 11: 'UPTIME'}
"""dict: Dictionary containing shorthand numerical ids and the corresponding test names for each."""
TEST_DATA_GRAPHS = {
	"STRESS_NG": ['Instructions','CPU Cycles'],
	"IPMITOOL": ['CPU Temp', 'FAN1', 'FAN2', 'FANA', '5VCC', '5VSB', '3.3VCC', '3.3VSB', '12V'],
	"STREAM_C": ['Add','Copy'],
	"IPERF": ['bandwidth','loss_percentage','out_of_order_datagrams','lost_datagrams'],
	"USB_PASSMARK": ['error counter', 'Read', 'Write'],
	"TAMPER_STATUS": ['voltage'],
	"PING_TEST": ['packet_loss','total_time','average'],
	"UPTIME": ['load_avg'],
	"FIBER_FPGA_TEMP": ['2.5', '3.5'],
	"DD_TEST": ['SDA'],
	"HDPARM": ["cached", "buffered disk"]	
}
"""dict: Dictionary containing the names of tests to be auto-graphed, and the corresponding list of options to be graphed for each test."""
SIDES = {'BLK': 'black','RED': 'red'}
"""dict: Dictionary containing key-names for the sides in the database, as well as their corresponding full names/colors."""
TEMPERATURE_OPS = ['intake','outtake','ambient']
"""list of str: List of valid temperature keys (aka options)."""
DB = dataset.connect('mysql://guest:password@localhost/test_results')
""":class:`Database <dataset.database>`: Database containing results from all tests."""

tests = {}

def test_run_select():
	"""Allows the user to select test run that they wish to generate graphs for.
	
	If the user enters 'o' or 'options', returns the list of test runs stored 
	in the *TESTS* table of :const:`DB`, along with their start and end times.
	"""
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
	"""Allows the user the select the test for which they wish to view data.

	If the user enters 'o' or 'options', returns the list of available tests, 
	along with a numerical shorthand they can be entered as.

	Has additional options.  One is to run :func:`autogenerate_graphs` by 
	entering 's' or 'save', allowing the user to automatically generate 
	a preset selection of graphs for their selected test run. The other
	allows the user to generate a graph of temperature vs. time, by
	entering 't'

	Parameters
	----------
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the current test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the current test run ended.
	"""
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
	"""Allows the user the select the test option for which they wish to generate a graph.

	If the user enters 'o' or 'options', returns the list of valid options for the current test.

	Parameters
	----------
	test_key : :class:`Test <results_viewer.Test>`
		The :class:`Test <results_viewer.Test>` which the user has currently selected.
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the current test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the current test run ended.
	"""
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
	"""Retrieve test data from the database.

	Get the data associated with the selected test run, from current test's database,
	limited to only the data specified by the selected option.

	Parameters
	----------
	cur_test : :class:`Test <results_viewer.Test>`
		The :class:`Test <results_viewer.Test>` for which we wish to obtain data.
	sel_opt : str
		The user selected option denoting the subset of data we care about.
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run ended.
	where_addendum : str, optional
		An optional string which is used to specify additional constraints for the query to the database.
		Empty by default, and only used by some tests.

	Returns
	-------
	x : dict
		A dictionary containing a list of the desired x-axis data associated with each side
	y : dict
		A dictionary containing a list of the desired y-axis data associated with each side
	"""
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
	else:
		for s in SIDES:
			results=(DB.query("SELECT * FROM {} WHERE side='{}' AND `{}` IS NOT NULL AND (time_stamp >= '{}' AND time_stamp <= '{}')".format(cur_test.tag,s,sel_opt,start_time,end_time)+ where_addendum + ";"))
			x[s],y[s]=[],[]
			for r in results:
				x[s].append(r['time_stamp'])
				y[s].append(r[sel_opt])
	return x,y

def determine_units(cur_test,sel_opt):
	"""Returns to appropriate units for the selected test and option.

	Parameters
	----------
	cur_test : :class:`Test <results_viewer.Test>`
		The :class:`Test <results_viewer.Test>` for which we wish to obtain data.
	sel_opt : str
		The user selected option denoting the subset of 
		test data that we care about.

	Returns
	-------
	units : str
		The units of the data in the selected subset.
	"""
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

def generate_graph(cur_test,sel_opt,start_time,end_time,max_y=None, where_addendum = "", sub_title = "", save_to_file=False,graph_type='plot',):
	"""Performs the steps necessary to generate a graph for the selected subset of data.
	
	Parameters
	----------
	cur_test : :class:`Test <results_viewer.Test>`
		The :class:`Test <results_viewer.Test>` for which we wish to obtain data.
	sel_opt : str
		The user selected option denoting the subset of 
		test data that we care about.
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run ended.
	max_y : int, optional
		The value to use for the max y value on the graphs.
	where_addendum : str, optional
		An optional string which is used to specify additional constraints for the query to the database.
		Empty by default, and only used by some tests.
	sub_title : str, optional
		The subtitle to append to the figure title. By default an empty string.
	save_to_file : bool
		A boolean telling the function if the figures should be saved to a file
		instead of displayed on screen. ``False`` by default.
	graph_type : str
		The type of graph to generate.  Set to 'plot' by default.
		Valid options are 'plot' to generate a normal plot, or 
		'hist' to generate a histogram.
	"""
	units = determine_units(cur_test,sel_opt)
	x,y=get_data(cur_test,sel_opt,start_time,end_time,where_addendum)
	x_tmp, y_tmp = map_time2temp(x,y)
	#print(x)
	if cur_test.tag == 'TAMPER_STATUS':
		max_y = 3500
	# if max_y == None:
	# 	if len(y['RED']) > 0:
	# 		max_y = max(y['RED'])*2.5 + 5
	# 	else:
	# 		max_y = 10
	ymin,ymax = 1000000000000000,0
	for s in SIDES:
		tmp_min,tmp_max = get_ylims(y[s])
		if tmp_min != None and tmp_max != None:
			if tmp_min < ymin:
				ymin = tmp_min
			if tmp_max > ymax:
				ymax = tmp_max


	upper_info = {'xlabel': 'Time', 'ylabel': sel_opt + " (" + units + ")", 'ymin': ymin,'ymax': ymax, 'fmt': '-'}
	lower_info = {'xlabel': 'Temperature', 'ylabel': sel_opt + " " + units, 'ymin': ymin,'ymax': ymax, 'fmt': '.', 'xunits': "°C"}
	fig_info = {'tag': cur_test.tag + sub_title,'test_opt': sel_opt}

	if graph_type=='plot':
		one_and_three_fig(x,y,upper_info,x_tmp,y_tmp,lower_info,fig_info)
	elif graph_type=='hist':
		double_hist_fig(y,{'xlabel': sel_opt + " (" + units + ")"},fig_info)
	if save_to_file:
		plt.savefig("../Graphs/{} ({}).png".format(fig_info['tag'],fig_info['test_opt']))
	else:
		plt.show()
		
def get_ylims(y_data):
	if len(y_data) > 0:
		ymin,ymax = y_data[0],y_data[0]
		for pt in y_data:
			if pt < ymin:
				ymin = pt
			if pt > ymax:
				ymax = pt
		return ymin,ymax
	else:
		return None,None

def gen_IPERF_graph(sel_opt,start_time,end_time,stf=False):
	"""Variant function for generating a graph of IPERF values, calls :func:`generate_graph` with additional parameters specific to IPERF

	Parameters
	----------
	sel_opt : str
		The user selected option denoting the subset of 
		test data that we care about.
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run ended.
	stf : bool
		A boolean telling the function if the figures should be saved to a file
		instead of displayed on screen. ``False`` by default.
	"""
	cur_test = tests['IPERF']
	#x,y={},{}
	ips = {'BLK': {'Ethernet':'200.50','Fiber (Black)':'2.2','Fiber (Red)':'3.1'}, 'RED': {'Ethernet':'200.20','Fiber (Black)':'2.1','Fiber (Red)':'3.2'}}
	interfaces = ['Ethernet', 'Fiber (Black)', 'Fiber (Red)']
	max_by_op = {'bandwidth': 20, 'loss_percentage': 100, 'out_of_order_datagrams': 1000, 'lost_datagrams': 100000}

	for i in interfaces:
		where_addendum = " AND PID='SUM' AND role='SERVER' AND (address='{}' OR address='{}')".format(ips['RED'][i],ips['BLK'][i])
		generate_graph(cur_test,sel_opt,start_time,end_time,max_by_op[sel_opt],where_addendum, " "+ i,save_to_file=stf)

def gen_IPERF_graph_alt(sel_opt,start_time,end_time,stf=False):
	cur_test = tests['IPERF']
	#x,y={},{}
	ips = {'BLK': {'Ethernet':'200.50','Fiber (Black)':'2.2','Fiber (Red)':'3.1'}, 'RED': {'Ethernet':'200.20','Fiber (Black)':'2.1','Fiber (Red)':'3.2'}}
	interfaces = ['Ethernet', 'Fiber (Black)', 'Fiber (Red)']
	max_by_op = {'bandwidth': 20, 'loss_percentage': 100, 'out_of_order_datagrams': 10000, 'lost_datagrams': 1000000}

	for i in interfaces:
		where_addendum = " AND PID='SUM' AND role='SERVER' AND (address='{}' OR address='{}') AND interval_start>5 AND interval_end>10".format(ips['RED'][i],ips['BLK'][i])
		generate_graph(cur_test,sel_opt,start_time,end_time,max_by_op[sel_opt],where_addendum, " "+ i,save_to_file=stf,graph_type='hist')


def map_time2temp(times,data):
	"""Maps a list of time stamps and a list data to a list of temperatures and a list of data at the corresponding times.

	Parameters
	----------
	times : list of :class:`datetime <datetime.datetime>`
		The list of time stamps to find corresponding temperature values for.
	data : list
		List of values, where the index of each value corresponds to an index in ``times``.
		Included to ensure that the number of data points in the x and y axes are not misaligned.
	
	Returns
	-------
	temps_list : list of float
		List of the temperature values corresponding to the time stamps in ``times``.
	temp_data : list
		List of values, where the index of each value corresponds to an index in ``temps_list``.
	"""
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
	"""Generate a graph of the temperature data vs. time.

	Parameters
	----------
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run ended.
	"""
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
	"""Generate a figure with one large upper graph of data vs time, and three smaller lower graphs of data vs temperature.

	Parameters
	----------
	upperx : dict
		Dictionary containing lists of x-axis data that correspond to each side in :const:`SIDES`.
	uppery : dict
		Dictionary containing lists of y-axis data that correspond to each side in :const:`SIDES`.
	upper_info : dict
		Dictionary contain information used when generating the upper graph, such as the 
		graph format, the y limit, and various labels and titles.
	lowerx : dict
		Dictionary containing dictionaries that correspond to each side in :const:`SIDES`,
		which in turn contain lists of x-axis data that correspond to each of three keys.
	lowery : dict
		Dictionary containing dictionaries that correspond to each side in :const:`SIDES`,
		which in turn contain lists of y-axis data that correspond to each of three keys.
	lower_info : dict
		Dictionary contain information used when generating the lower graph, such as the 
		graph format, the y limit, and various labels and titles.
	fig_info : dict
		Dictionary containing more general info that applies the the figure as a whole.
	"""
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
	axt.set_ylim(upper_info['ymin'],upper_info['ymax'])
	lower_ind = 0
	axb[lower_ind].set_ylabel(lower_info['ylabel'])
	for key in lowerx:
		for s in SIDES:
			if (len(lowerx[key][s]) > 0 and len(lowerx[key][s]) > 0):
				#print(lowery[key][s])
				#print(lowerx[key][s])
				my_plotter(axb[lower_ind],lowerx[key][s],lowery[key][s],lower_info['fmt'],{'color':SIDES[s]})
		axb[lower_ind].set_xlabel('{}: ({}) {}'.format(lower_info['xlabel'],key,lower_info['xunits']))
		axb[lower_ind].set_ylim(lower_info['ymin'],lower_info['ymax'])
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
	"""Generate a figure with one large graph, with data graphed in three different colors.

	That is, three colors per side, for a total of six colors.  Each color corresponds to one 
	side and key.

	Parameters
	----------
	x : dict
		Dictionary containing dictionaries that correspond to each side in :const:`SIDES`,
		which in turn contain lists of x-axis data that correspond to each of three keys.
	y : dict
		Dictionary containing dictionaries that correspond to each side in :const:`SIDES`,
		which in turn contain lists of y-axis data that correspond to each of three keys.
	info : dict
		Dictionary contain information used when generating the graph, such as the 
		graph format, the y limit, and various labels and titles.
	fig_info : dict
		Dictionary containing more general info that applies the the figure as a whole.
	"""
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
	ay.set_ylabel('{}: {}'.format(info['ylabel'],info['yunits']))
	ay.set_ylim(0,info['ylim'])
	fig.suptitle("{}".format(fig_info['tag']))

def double_hist_fig(data,fig_info):
	fig = plt.figure(figsize=(15,9))
	plt.subplots_adjust(hspace=0.3)
	gs = GridSpec(2, 1, figure=fig)
	ax = {}
	ind = 0
	for s in SIDES:
		ax[s]=(fig.add_subplot(gs[ind, 0]))
		ind+=1

	for s in SIDES:
		plot_hist(ax[s],data[s],{'bins': fig_info['bin_info'], 'color':SIDES[s]})
		ax[s].set_xlabel(fig_info['xlabel'])

	fig.suptitle("Histogram of {}: {}".format(fig_info['tag'],fig_info['test_opt']))


def plot_hist(ax,data,param_dict):
	out = ax.hist(data,**param_dict)
	return out

def my_plotter(ax,xdata,ydata,fmt, param_dict):
	"""Plot ``xdata`` and ``ydata``.

	Parameters
	----------
	ax : :class:`axis <matplotlib.axis>`
		The :class:`axis <matplotlib.axis>` on which to plot the data.
	xdata : list
		The list of data for the x-axis.
	ydata : list
		The list of data for the y-axis.
	fmt : str
		The format string for the plot.
	param_dict : dict
		Additional parameters.
	"""
	out = ax.plot(xdata, ydata, fmt, **param_dict)
	return out


def return_options(options_list,sep_char):
	"""Return the options listed in ``options_list``.

	Parameters
	----------
	options_list : list of str
		The list of the options to return.
	sep_char : str
		The character to use when separating the options.

	Returns
	-------
	str
		A string listing the available options, with each option separated 
		by the character defined by ``sep_char``.
"""
	return("The options are \n" + sep_char.join(list(options_list)))

def return_help():
	"""Return the standard help message.

	Returns
	-------
	str
		The standard help message, listing valid user inputs.
	"""
	return("Type '(h)elp' to bring up this prompt, '(o)ptions' for a list of viable responses,\n"
		"'go back' to return to the previous prompt, or 'exit' to end the program")

class Test(object):
	"""An object which represents all of the information regarding a single test.

	Parameters
	----------
	json_file_name : str
		The filename of the json file from which test information should be loaded.

	Attributes
	----------
	tag : str
		The tag associated with the test (also used as the name of the test, 
		and the name of the table containing the test data).
	data_key : str
		The name of the column which contains the names of the different
		subsets of data the user can choose from when generating a graph.  
		Use is mutually exclusive with :attr:`key_list`.
	data_info : dict
		A dictionary with keys corresponding to the names of the data columns
		in the test's table, and values corresponding to the type of each column.
	data_tag : str
		The name of the column in which the desired data is stored, not used
		by all tests.
	key_list : list of str
		A list of the names of different subsets of data the user can choose 
		from when generating a graph. Use is mutually exclusive with :attr:`data_key`.
	units_key : str
		The name of the column which contains the units of the data stored in 
		the current row of the table. Not present for all tests.
	units_dict : dict
		A dictionary matching the options from :attr:`key_list` with the 
		appropriate units. Present when :attr:`units_key` is not.
	"""
	def __init__(self,json_file_name):
		with open(json_file_name) as json_file:
			json_dict = (json.load(json_file))
			self.tag = json_dict['tag']
			self.data_key = json_dict['data_key']
			self.data_info = json_dict['data_info']
			self.data_tag = json_dict['data_tag']
			self.key_list = json_dict['key_list']
			self.units_key = json_dict['units_key']
			self.units_dict = json_dict['units_dict']


def autogenerate_graphs(start_time,end_time):
	"""Generate a set of predetermined graphs and save them as pngs.

	The graphs are determined by the constant :const:`TEST_DATA_GRAPHS`

	Parameters
	----------
	start_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run began.
	end_time : :class:`datetime <datetime.datetime>`
		The time at which the currently selected test run ended.
	"""
	print("Start: {}".format(datetime.datetime.today()))
	for test in TEST_DATA_GRAPHS:
		for option in TEST_DATA_GRAPHS[test]:
			if test == 'IPERF':
				gen_IPERF_graph(option,start_time,end_time,stf=True)
			else:
				generate_graph(tests[test],option,start_time,end_time,save_to_file=True)

	print("End: {}".format(datetime.datetime.today()))

for n in MESSAGE_TAGS:
	tests[MESSAGE_TAGS[n]] = Test("../Tests/"+MESSAGE_TAGS[n]+".json")

def TPM_random_hist():
	random_ints = {}
	for s in SIDES:
		random_ints[s] = []
		with open('../Results/'+SIDES[s]+'_random') as random_file:
			for line in random_file:
				random_ints[s] += (int(hex_int, 16) for hex_int in line.split(' '))
	fig_info = {'bin_info': 256, 'xlabel': 'Random Number', 'tag': "TPM", 'test_opt': "RndNumGen"}
	double_hist_fig(random_ints,fig_info)
	plt.show()


if __name__ == '__main__':
	#TPM_random_hist()
	test_run_select()










