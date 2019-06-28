import dataset,datetime

SIDES = {"BLACK": 'BLK', "RED": 'RED'}

RESULTS_DB = dataset.connect('mysql://guest:password@localhost/test_results')
TEMPS_DB = dataset.connect('sqlite:///../Results/DAQTEMPS.db')

def insert_ignore_many_query(table, rows):
	return "INSERT IGNORE INTO {}({}) VALUES {};".format(table,','.join([key for key in rows[0]]),','.join(['('+','.join(['"'+str(r[keys])+'"' for keys in r])+')' for r in rows]))



def temp_shifter():
	test_num = eval(input("Which test do you want to import temperature data for? "))
	test_row = RESULTS_DB['TESTS'].find_one(id=test_num)
	#print('SELECT * FROM Temperature WHERE time>="{}" AND time<="{}"'.format(test_row['start_time'],test_row['end_time']))
	rows = TEMPS_DB.query('SELECT * FROM Temperature WHERE time>="{}" AND time<="{}";'.format(test_row['start_time'],test_row['end_time']))
	next_rows = []
	for r in rows:
		rnd_tm = datetime.datetime.fromisoformat(r['time'])
		td = datetime.timedelta(seconds=round(rnd_tm.second/10+0.001)*10 - rnd_tm.second,microseconds=-rnd_tm.microsecond)
		for s in SIDES:
			next_row = {}
			next_row['time_stamp'] = str(rnd_tm + td)
			next_row['unit'] = 1
			next_row['side'] = SIDES[s]
			next_row['ambient'] = r['AMBIENT']
			next_row['outtake'] = r[s+'_OUTTAKE']
			next_row['intake'] = r[s+'_INTAKE']

			next_rows.append(next_row)

	RESULTS_DB.query(insert_ignore_many_query('TEMPERATURES',next_rows))



temp_shifter()

#' '.join(map('('+','.join(map(r[keys] for keys in r)+')') for r in rows))' '.join(map('('+','.join([str(r[keys]) for keys in r])+')') for r in rows))