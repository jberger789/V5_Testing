import dataset,datetime

SIDES = {"BLACK": 'BLK', "RED": 'RED'}

RESULTS_DB = dataset.connect('mysql://guest:password@localhost/test_results')
TEMPS_DB = dataset.connect('sqlite:///../Results/DAQTEMPS.db')

def insert_ignore_many_query(table, rows):
	"""
	Given:	`table`: the name of an SQL table in the current database
					-> assumes a table with that name exists in
					   the database "RESULTS_DB"
			`rows` : a list of rows to insert into `table`
			   		-> assumes every row has corresponding
			   		   value for every column of the table
	Return: A string representing an SQL statement that, if 
			executed, performs an INSERT IGNORE of every
			row in `rows` into `table`
	"""
	return "INSERT IGNORE INTO {}(time_stamp,unit,side,ambient,outtake,intake) VALUES {};".format(table,rowvals4SQLmany(rows))

def rowvals4SQLquery(row):
	"""
	Desc:	Given a row, returns a string containing 
			the values in the row, separated by commas, 
			enclosed in parentheses
	Given:	`row`:	the dictionary representing the row
					-> assumes the dict contains corresponding
			   		   values for every data column
	Return: A string containing comma separated values
			from `row`, enclosed in parentheses
	"""
	return '('+','.join(f'"{row[col]}"' for col in row) + ')'

def rowvals4SQLmany(row_list):
	out_str = ""
	out_str += ','.join(rowvals4SQLquery(row) for row in row_list)
	return out_str

def temp_shifter():
	test_num = eval(input("Which test do you want to import temperature data for? "))
	test_row = RESULTS_DB['TESTS'].find_one(id=test_num)
	rows = TEMPS_DB.query('SELECT * FROM Temperature WHERE time>="{}" AND time<="{}";'.format(test_row['start_time'],test_row['end_time']))
	next_rows = []
	for r in rows:
		next_rows += convert_row(r)
	RESULTS_DB.query(insert_ignore_many_query('TEMPERATURES',next_rows))

def round_time(tm_str):
	rnd_tm = datetime.datetime.fromisoformat(tm_str)
	td = datetime.timedelta(seconds=round(rnd_tm.second/10+0.001)*10 - rnd_tm.second,microseconds=-rnd_tm.microsecond)
	return rnd_tm + td

def convert_row(row):
	out_rows = []
	time_str = str(round_time(row['time']))
	for s in SIDES:
		next_row = {
		'time_stamp': time_str,
		'unit': 1,
		'side': SIDES[s],
		'ambient': row['AMBIENT'],
		'outtake': row[s+'_OUTTAKE'],
		'intake': row[s+'_INTAKE']
		}
		out_rows += [next_row]
	return out_rows

temp_shifter()