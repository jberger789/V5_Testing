import dataset,datetime

SIDES = {"BLACK": 'BLK', "RED": 'RED'}

RESULTS_DB = dataset.connect('mysql://guest:password@localhost/test_results')
TEMPS_DB = dataset.connect('sqlite:///../Results/DAQTEMPS.db')

def insert_ignore_many_query(table, rows):
	"""Generate an appropriate string for inserting potentially duplicate rows into an SQL table.

	**Parameters**:
		``table``
			The name of an SQL table in the current database.  
			Assumes a table with that name exists in the database as defined by **RESULTS_DB**

		``rows``
			a list of rows to insert into ``table``.  
			Assumes every row dictionary contains corresponding values for every data column in the table

	**Returns**: 
		``query_str``
			A string representing an SQL statement that, if executed, performs an *INSERT IGNORE* of every row in ``rows`` into ``table``

	"""
	query_str = "INSERT IGNORE INTO {}(time_stamp,unit,side,ambient,outtake,intake) VALUES {};".format(table,rowvals4SQLmany(rows))
	return query_str

def rowvals4SQLquery(row):
	"""Generates a string representation of the values in ``row``, formatted for an SQL query.

	**Parameters**:	
		``row``
			The dictionary representing the row.
			Assumes the dictionary contains corresponding values for every data column in the table

	**Returns**:
		``row_str``
			A string containing comma separated values from ``row``, enclosed in parentheses

	"""
	row_str = '('+','.join(f'"{row[col]}"' for col in row) + ')'
	return row_str

def rowvals4SQLmany(row_list):
	"""Generates a string representation of the values in many rows, formatted for an SQL query.

	**Parameters**:
		``row_list``
			A list containing the rows (as dictionaries) to be inserted.
			Assumes every row dictionary contains corresponding values for every data column in the table

	**Returns**:
		``out_str``
			A string containing strings generated by :meth:`rowwvals4SQLquery` for each row in ``row_list``, separated by commas

	"""
	out_str = ""
	out_str += ','.join(rowvals4SQLquery(row) for row in row_list)
	return out_str

def temp_shifter():
	"""Takes in temperature data from the database as defined by **TEMPS_DB**, 
	rounds their timestamps to the nearest 10 seconds, and inserts it into the 
	*TEMPERATURES* table in the database as defined by **RESULTS_DB**.

	**Assumes**:
		* Both databases exist as defined
		* The row in *TESTS* with the time interval containing the data to be shifted exists
		* the tables in both databases exist and are formatted as expected
	"""
	test_num = eval(input("Which test do you want to import temperature data for? "))
	test_row = RESULTS_DB['TESTS'].find_one(id=test_num)
	rows = TEMPS_DB.query('SELECT * FROM Temperature WHERE time>="{}" AND time<="{}";'.format(test_row['start_time'],test_row['end_time']))
	next_rows = []
	for r in rows:
		next_rows += convert_row(r)
	RESULTS_DB.query(insert_ignore_many_query('TEMPERATURES',next_rows))

def round_time(tm_str):
	"""Generates a string representation of the values in many rows, formatted for an SQL query.

	**Parameters**:
		``tm_str``
			A string containing a representation of a :mod:`datetime <datetime.datetime>` object in standard format.
			
			Standard format is defined as "YYYY-MM-DD hh:mm:ss(:[msecs])"

	**Returns**:
		``new_tm``
			A :mod:`datetime <datetime.datetime>` object, containing the timestamp from ``tm_str`` rounded to the nearest ten second mark

	"""
	rnd_tm = datetime.datetime.fromisoformat(tm_str)
	td = datetime.timedelta(seconds=round(rnd_tm.second/10+0.001)*10 - rnd_tm.second,microseconds=-rnd_tm.microsecond)
	new_tm = rnd_tm + td
	return new_tm

def convert_row(row):
	"""Takes in a single row of temperature data from **TEMPS_DB** and converts it to two rows of temperature data to be inserted into *TEMPERATURES* in **RESULTS_DB**

	**Parameters**:
		``row``
			A dictionary representing the row retrieved from **TEMPS_DB**.
			Assumes the row was retrieved successfully

	**Returns**:
		``out_rows``
			A list containing the two newly converted rows

	"""
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

if __name__ == '__main__':
	temp_shifter()