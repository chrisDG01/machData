
import json
import os
import sys
import random
import pyodbc
import subprocess
import datetime



class GlobalVars():
	
		
	def get_table_type(self,tblCols):      # nov 8,2018 cglenn : improve this 
		ttyp = self.table_keys['noK']
		for c in tblCols:
	
			if (c[2] != self.table_keys['noK']) :
				
				if (c[2] == self.table_keys['pkey']): 
					ttyp = self.table_keys['pkey']
					
				if (c[2] == self.table_keys['pdkey']) and (ttyp != self.table_keys['pkey']): 
					ttyp = self.table_keys['pdkey']
				
				if (c[2] == self.table_keys['fkey'])  and (ttyp == self.table_keys['noK']) : ttyp = self.table_keys['fkey']
				if (c[2] == self.table_keys['fdkey']) and (ttyp == self.table_keys['noK']) : ttyp = self.table_keys['fdkey']
				
		return ttyp

		
	def __init__(self,jsonParms):
	
		def create_table_objs(self, jparms):     # nov 8,2018 cglenn : improve this 
			table_list = {}
			tbls       = jparms['g_tableList']
			data_tags  = jparms['g_domainTable']		# Nov 5,2018 : change the name g_domainTable to g_dataTags in the web pages and .js includes
				
			for t in tbls.keys():
				rdesc = {}
				colcnt = 0
				ttyp = self.get_table_type(tbls[t])
				
				for c in tbls[t]:
					rdesc[c[0]] = [c[1], colcnt, c[2]]
					colcnt = colcnt + 1
				
				tblC = DatabaseTable(t,ttyp,data_tags)
				tblC.row_desc = rdesc
				table_list[t] = tblC	
			return table_list
		
		def format_table_relations(self, d):	# nov 8,2018 cglenn : improve this 
			a=[]
			f=[]
			for k,v in d.items():
				a.append(k)
				while (v): a.append(v.pop())
				f.append(a)
				a = []
			return f
		
		self.use_max_DB_ID		    = True  if (jsonParms['g_parameters']['use_max_DB_ID']        == u'True')	else False
		self.global_id_batch_size	= 1 	if (jsonParms['g_parameters']['global_id_batch_size'] == None)	else int(jsonParms['g_parameters']['global_id_batch_size'])
		self.global_id		     	= 1 	if (jsonParms['g_parameters']['global_id'] 			  == None) 	else int(jsonParms['g_parameters']['global_id'])
		self.num_of_batches		    = 1 	if (jsonParms['g_parameters']['num_of_batches']  	  == None)	else int(jsonParms['g_parameters']['num_of_batches'])
		self.curr_batch_number		= 0 	if (jsonParms['g_parameters']['curr_batch_number'] 	  == None)	else int(jsonParms['g_parameters']['curr_batch_number'])
		self.delim_char		     	= '|' 	if (jsonParms['g_parameters']['delim_char']  		  == None)	else jsonParms['g_parameters']['delim_char']
		self.truncate_and_load		= True  if (jsonParms['g_parameters']['truncate_and_load']    == u'True')	else False
		self.write_to_DB 			= True	if (jsonParms['g_parameters']['write_to_DB']    	  == u'True')	else False
		self.table_keys				= jsonParms['g_keyTable']
		self.table_objs				= create_table_objs(self,jsonParms)
		self.table_relations		= format_table_relations(self,jsonParms['g_relationList'])
		self.start_time				= datetime.datetime.now()
		self.curr_time				= datetime.datetime.now()
			
	def update_curr_time(self):
		self.curr_time = datetime.datetime.now()
		
	def get_time_elapsed(self):
		self.update_curr_time()
		return self.curr_time - self.start_time 
		
	def incr_global_id(self):
		self.global_id = self.global_id + 1
		
	def incr_batch_count(self):
		self.curr_batch_number = self.curr_batch_number + 1
				
	def all_to_stdout(self):
		print('==================================================================\n')
		print('start time				: {}\n'.format(self.start_time))
		print('curr time				: {}\n'.format(self.curr_time))
		print('elapsed time				: {}\n'.format(self.get_time_elapsed()))
		print('use_max_DB_ID 			: {}\n'.format(self.use_max_DB_ID ))		     
		print('global_id_batch_size	: {}\n'.format(self.global_id_batch_size )) 	  
		print('global_id				: {}\n'.format(self.global_id ))      	 
		print('num_of_batches			: {}\n'.format(self.num_of_batches )) 		 
		print('curr_batch_number  		: {}\n'.format(self.curr_batch_number ))    
		print('delim_char   			: {}\n'.format(self.delim_char ))         
		print('truncate_and_load 		: {}\n'.format(self.truncate_and_load ))	
		print('write_to_DB 			: {}\n'.format(self.write_to_DB ))	
		print('==================================================================\n')
		
		
class DatabaseTable():
	def __init__(self,table_name,table_type,data_tags):
		self.table_name = table_name
		self.table_type = table_type
		self.process_status = []
		self.data_types = data_tags
		self.row_desc = {}
		self.rows     = []
		self.row_in_process = False
		
	def is_row_in_progress(self):
		if ( len(self.rows) > 0 ) : 
			r = self.rows.pop()
			for c in r: 
				if c == '_$noColValue' :
					self.rows.append(r)
					return True
			self.rows.append(r)
		return False
		
	def clear_all_rows(self):
		self.rows = []
		
	def get_datatype_ddl(self,col_name):
		return self.data_types[self.row_desc[col_name][0]]
		
	def get_table_ddl(self):
		ddl = [None] * len(self.row_desc)
		
		for col_name in self.row_desc.keys():
			col_dtype    = self.get_datatype_ddl(col_name)
			col_ord      = self.row_desc[col_name][1]
			if ddl[col_ord] == None : ddl[col_ord] = [col_name,col_dtype]
		
			
		return ddl	
	
	def get_table_desc(self):
		ddl = [None] * len(self.row_desc)
		
		for col_name in self.row_desc.keys():
			col_dtype    = self.row_desc[col_name][0]
			col_ord      = self.row_desc[col_name][1]
			col_keytyp	 = self.row_desc[col_name][2]
			if ddl[col_ord] == None : ddl[col_ord] = [col_name,col_dtype,col_keytyp]
		return ddl	
	
	def get_index_name_and_col(self):
		idx_name = ''
		for col_name in self.row_desc.keys():
			col_keytyp = self.row_desc[col_name][2]
			
			if col_keytyp == global_vars.table_keys['pkey']  : idx_name = global_vars.table_keys['pkey']  + '_' + self.table_name
			if col_keytyp == global_vars.table_keys['pdkey'] : idx_name = global_vars.table_keys['pdkey'] + '_' + self.table_name
			if col_keytyp == global_vars.table_keys['fkey']  : idx_name = global_vars.table_keys['fkey']  + '_' + self.table_name
			if col_keytyp == global_vars.table_keys['fdkey'] : idx_name = global_vars.table_keys['fdkey'] + '_' + self.table_name
			#
			# return first index column found ... 
			#
			if idx_name != '' : 
				return {'name':idx_name, 'col':col_name}
		return {}

	def get_column_names_by_keytype(self, keyType):
		cn = []		
		for col_name in self.row_desc.keys():
			#print('row desc [{}] search key [{}]'.format(self.row_desc[col_name][2], keyType))
			if self.row_desc[col_name][2] == keyType :
				cn.append(col_name)
		return cn
		
		
		
		
		
		
class MockData:

	def __init__(self):

		self.name_list    = [['Adam', 'Abel','Amelia','Ava','Alfie,'],
							['Bob','Bander'],
							['Chris', 'Candice','Charlie'],
							['Debra', 'Darwin'],
							['Emily'],
							['Freddie'],
							['George','Grace'],
							['Harry'],
							['Isabella','Isla'],
							['Jacob','Jack'],
							['Lily'],
							['Mia'],
							['Noah'],
							['Oscar','Olivia','Oliver'],
							['Sophia']]

		self.street_list = [['Allster Ave', 'Abigail Court'],
							['Bin Ave','Binder Road'],
							['Cedar'],
							['Eighth','Elm'],
							['Fifth' ],
							['Hill'],
							['Lake'], 
							['Maple','Main'],  
							['Ninth'],  
							['Oak'],  
							['Pine','Park'],  
							['Sixth','Seventh'],  
							['View'],  
							['Washington']]

		self.city_list   = [['Arch City', 'Abel Town'],
							['Big Bend','Brandy Town','Berkeley'],
							['Foster City'],
							['Oakland'],
							['Richmond'],
							['San Francisco']]

	def random_int(self, s,e):
		return random.randint(s,e)

	def random_amt(self, s,e):
		return round(random.randint(s,e)*1.0/1.1,2)
		
	def random_string(self, l):
		return str('S' * l)
				
	def random_date(self, sy,ey):
		y = str(self.random_int(sy,ey))
		
		m = self.random_int(1,12)
		if m < 10 :
			m = '0' + str(m)
		else:
			m = str(m)
		
		d = self.random_int(1, 28)
		if d < 10 :
			d = '0' + str(d)
		else:
			d = str(d)
		return  y + '-' + m + '-' + d 

	def random_phone(self):
		a = str(self.random_int(310,760))
		
		b = str(self.random_int(200,900))
		c = str(self.random_int(1000, 9000))
		return '(' + a + ')' + b + '-' + c

	def random_from_list(self,lst):
		n = len(lst) - 1
		return lst[self.random_int(0, n)]
	
	def get_random_string(self,lst):
		l = self.random_from_list(lst)
		return self.random_from_list(l)
	
	def random_full_name(self):
		f = self.get_random_string(self.name_list)
		l = self.get_random_string(self.name_list)
		return f + ' ' + l
	
	def random_addr(self):
		n = self.random_int(1000, 2300)
		s = self.get_random_string(self.street_list)
		c = self.get_random_string(self.city_list)
		z = self.random_int(90000, 97000)
		return str(n) + ' ' + s + ', ' + c + ' ' + str(z)
						
		
		
		
class RunDDL_MSSQL:
	def __init__(self, driver, server, database, user, password):
		self.mssql_driver 	= 'DRIVER='   + driver
		self.mssql_server   = 'SERVER='   + server
		self.mssql_database = 'DATABASE=' + database
		self.mssql_user     = 'UID='      + user
		self.mssql_password = 'PWD='      + password
		self.mssql_conn     = None
		
	def open_conn(self):
		s = self.mssql_driver + ';' + self.mssql_server + ';' +  self.mssql_database + ';' +  self.mssql_user + ';' +  self.mssql_password
		#print(s)
		self.mssql_conn = pyodbc.connect(s)
	
	def close_conn(self):
		self.mssql_conn.close()
	
	def run_sql(self, sql):
		cur = self.mssql_conn.cursor()
		cur.execute(sql)
		result = cur.fetchall()
		cur.commit()
		cur.close			  
		return result
    
	def run_ddl(self, ddl):
		#print('in run_ddl [{}]'.format(ddl))
		if (len(ddl)>0):
			cur = self.mssql_conn.cursor()
			cur.execute(ddl)
			cur.commit()
			cur.close			  
	
	def check_if_object_exists(self, t):
		if not(self.mssql_conn) : self.open_conn()
		cur = self.mssql_conn.cursor()
		cur.execute('select 1 from sys.objects where name = \'' + t.table_name + '\'')
		return cur.fetchall()
			
	def check_if_index_exists(self, t):
		if t.get_index_name_and_col().keys() :
			idx_name = t.get_index_name_and_col()['name']
			
			if not(self.mssql_conn) : self.open_conn()
			cur = self.mssql_conn.cursor()
			cur.execute('select 1 from sys.indexes where name = \'' + idx_name + '\'')
			ret = cur.fetchall()
		else:
			ret = False
		return ret
		
'''
   start functions =======================================================================================================
'''		
def get_last_id():
#
# write a check parent table for last primary id .... this suggests that we only create one PK relation at a time
# ... so how to handle models with multiple PK's ??  Run this multiple times?
#
	primary_table_name	= ''
	primary_table_ID	= ''

	for t in global_vars.table_objs.values():
		idx = t.get_index_name_and_col()
		if idx['name'].split('_')[0] ==  global_vars.table_keys['pkey']:
			primary_table_name = idx['name'].split('_')[1]
			primary_table_ID   = idx['col']
			break
				
	sql = 'select max(' + primary_table_ID + ') from ' + primary_table_name 
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	last_ID = runSQL.run_sql(sql)
	runSQL.close_conn()
	return int(last_ID[0][0])

	

def clear_all_row_in_progress() :
	for tbl in global_vars.table_objs.values():
		tbl.row_in_process = False
	

def table_ddl(ddl_type,tbl):
	table_name = tbl.table_name
	#print('in table_ddl name [{}]\n'.format(table_name))
	ddl = tbl.get_table_ddl()
	#print('in table_ddl ddl [{}]\n'.format(ddl))
	
	if ddl_type == 'CREATE':
		retstr = 'create table [' + table_name + '] ('
		
		for col in ddl:
			cn  = col[0]
			cdt = col[1]
			retstr = retstr + '[' + cn + ']' + ' ' + cdt + ','
		return retstr[:-1] + ')'
		
	if ddl_type == 'DROP':
		retstr = 'truncate table ' + table_name + ';\n'
		retstr = retstr + 'drop table ' + table_name + ';\n'
	else:
		retstr = None
	return retstr


	
def set_all_table_status():
	
	all_tables = global_vars.table_objs.values()
		
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()

	for t in all_tables:
		if (runSQL.check_if_object_exists(t)) : t.process_status.append('in_db')
	
	runSQL.close_conn()	
			
	


def check_indexes():
	all_tables = global_vars.table_objs.values()
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
    
	for t in all_tables:
		if ('in_db' in t.process_status) :
			if (runSQL.check_if_index_exists(t)) : t.process_status.append('has_index')
	
	runSQL.close_conn()	

		
	
	
def create_all_tables(ttyp = None):
	do_all = ''
	for t in global_vars.table_objs.values():
		
		if (ttyp == 'DOMAIN') and (t.table_type == global_vars.table_keys['pdkey']) :
			do_all = do_all + table_ddl('CREATE',t) + ';\n'
			
		if (ttyp != 'DOMAIN') and (t.table_type != global_vars.table_keys['pdkey']):
			do_all = do_all + table_ddl('CREATE',t) + ';\n'
				
	#print_and_split(do_all)			
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	#print ('create table [{}]'.format(do_all))
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	

def create_all_indexes():
	do_all = ''
	for t in global_vars.table_objs.values():
		idx = t.get_index_name_and_col()
		do_all = do_all + 'CREATE INDEX ' + idx['name'] + ' on ' + t.table_name + ' (' + idx['col'] + ');\n'
		
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
		
	
def drop_all_indexes():
	check_indexes()	


	do_all = ''
	for t in global_vars.table_objs.values():
		if ('has_index' in t.process_status) :
			do_all = do_all + 'DROP INDEX ' + t.get_index_name_and_col()['name'] + ';\n'
			
			
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	
	
def truncate_and_drop_tables(ttyp = None):
	do_all = ''
	
	for t in global_vars.table_objs.values():
		if ('in_db' in t.process_status) :
			 # if we are dropping DOMAIN tables do only domain tables else drop all others except domain tables
			if (ttyp == 'DOMAIN') and (t.table_type == global_vars.table_keys['pdkey']) :
				do_all = do_all + table_ddl('DROP',t) + '\n'
			
			if (ttyp != 'DOMAIN') and (t.table_type != global_vars.table_keys['pdkey']):
				do_all = do_all + table_ddl('DROP',t) + '\n'
						
	if (len(do_all) > 0):
		#print ('in trunc/load do_all [{}]'.format(do_all))
		runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
		runSQL.open_conn()
		runSQL.run_ddl(do_all)
		runSQL.close_conn()	
	
def	write_domain_data():
	truncate_and_drop_tables('DOMAIN')
	create_all_tables('DOMAIN')
	write_tables_to_file('DOMAIN')
	bcp_all_data('DOMAIN')
		
def bcp_a_table(tbl):
	print ('bcp :: table name [{}]'.format(tbl.table_name))
	delim_char = global_vars.delim_char
	do_all = ''
	do_bcp = 'bcp ' + tbl.table_name + ' in ' + tbl.table_name + '.csv -Smssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com -Umssql_01_admin -PTh3Bomb! -dtestEntity -c -t"'+delim_char+'"'
	#print (do_bcp)
	os.system(do_bcp)

def bcp_all_data(ttyp = None):
	for t in global_vars.table_objs.values():
		if ('in_db' in t.process_status) :
			if (ttyp == 'DOMAIN') and (t.table_type == global_vars.table_keys['pdkey']) :
				bcp_a_table(t)
			
			if (ttyp != 'DOMAIN') and (t.table_type != global_vars.table_keys['pdkey']):
				bcp_a_table(t)
	
	
def load_domain_tables(jsparms):
	dtbls = []
	for t in jsparms['g_tableList'].keys():
		if 'PDK' in ''.join(str(e) for e in jsparms['g_tableList'][t]): 
			dtbls.append(t)
	#print_and_split(dtbls)	
	for t in dtbls:
		for r in jsparms['g_domainData'][t]:
			cr = []
			for c in r:
				cr.append(str(c))
				
			global_vars.table_objs[t].rows.append(cr)		
			
		#print("in load domain tables ...t [{}] rows [{}]".format(t,	global_vars.table_objs[t].rows))
			
def clear_all_table_rows():
	for t in global_vars.table_objs.values():
		if t.table_type != global_vars.table_keys['pdkey'] : t.clear_all_rows()
		
def write_a_file(tbl):
	delim_char = global_vars.delim_char
	#print('write a file. tbl [{}]  typ [{}]  process stat [{}]'.format(tbl.table_name, tbl.table_type, tbl.process_status))
	
	with open(tbl.table_name+'.csv', "w") as write_file:
		for l in tbl.rows: 
			s = ''.join(str(c) + delim_char for c in l)[:-1]
			#if (tbl.table_type == 'PDK') : print("in write a file ...t.name [{}] line [{}]".format(tbl.table_name,s))
			write_file.write(s+'\n')	
		
		
def write_tables_to_file(ttyp = None):
	for t in global_vars.table_objs.values():
	# if we are processing DOMAIN tables do only domain tables else process all others except domain tables
		if (ttyp == 'DOMAIN') and (t.table_type == global_vars.table_keys['pdkey']) :
			write_a_file(t)
			
		if (ttyp != 'DOMAIN') and (t.table_type != global_vars.table_keys['pdkey']):
			write_a_file(t)
						
					
def create_a_batch_of_all_tables():
	
	clear_all_table_rows()
	
	pkey  = global_vars.table_keys['pkey']
	pdkey = global_vars.table_keys['pdkey']
	fkey  = global_vars.table_keys['fkey']
	fdkey = global_vars.table_keys['fdkey']
	
	max_loop = global_vars.global_id + global_vars.global_id_batch_size
		
	while global_vars.global_id < max_loop:
		primaryColNames = {}
		
		#
		# find and assign primary key values for all domain and parent tables keep in primaryColNames
		#
		for tbl in global_vars.table_objs.values():
			if tbl.table_type == pkey :
				primaryColNames[str(tbl.get_column_names_by_keytype(pkey)[0])] = str(global_vars.global_id)

			if tbl.table_type == pdkey:
				primaryColNames[str(tbl.get_column_names_by_keytype(pdkey)[0])] = str(md.random_from_list(tbl.rows)[0])		
				
		#print_and_split(	primaryColNames.items() )	
		#
		# now create data for each row in all tables except domain tables
		#
		for tbl in global_vars.table_objs.values():
			if tbl.table_type != pdkey :
				cidx = 0
				row = ['_$noColValue'] * len(tbl.row_desc)
				
				for col in 	tbl.get_table_desc():		
					if col[2] in [pkey, fkey, fdkey]:
						row[cidx] = primaryColNames[col[0]]
						
					if col[2] == u'None' :
						#print ('....10 table [{}] row :: {} '.format(tbl.table_name,row))
						if col[1] == 'full_name' : row[cidx]=md.random_full_name()
						if col[1] == 'dob'       : row[cidx]=md.random_date(1958,1985) 	 
						if col[1] == 'dtetm'     : row[cidx]=md.random_date(2000,2018) 	 
						if col[1] == 'address'   : row[cidx]=md.random_addr()			 	 
						if col[1] == 'email'     : row[cidx]='email.' + str(global_vars.global_id) + '@email.com' 	 	
						if col[1] == 'phone'     : row[cidx]=md.random_phone()         	 
						if col[1] == 'int'       : row[cidx]=str(md.random_int(1000,10000))
						if col[1] == 'amt'       : row[cidx]=str(md.random_amt(10,1000))
						if col[1] == 'vstr20'    : row[cidx]=str('S2' * 10)		 	        
						if col[1] == 'vstr80'    : row[cidx]=str('S8' * 40)		 	        
						if col[1] == 'vstr128'   : row[cidx]=str('S128' * 32)		 	    
					cidx = cidx + 1	
				tbl.rows.append(row)
				
		global_vars.incr_global_id()
		#print(	global_vars.global_id )
	print ('\nnumber of rows per batch {} \n\n'.format(global_vars.global_id_batch_size))
		
		

	
def get_parms_missing(jsonParms):
		r=[]
		d = json.dumps(jsonParms)
		#print('[{}]'.format(d))
		try: 
			b = jsonParms['g_parameters']
		except :
			r.append('g_parameters')
			
			
		try: 
			b = jsonParms['g_keyTable']
		except :
			r.append('g_keyTable')
			
			
		try: 
			b = jsonParms['g_tableList']
		except :
			r.append('g_tableList')
			
			
		try: 
			b = jsonParms['g_domainTable']
		except:
			r.append('g_domainTable')
			
		try: 
			b = jsonParms['g_domainData']
		except:
			r.append(g_domainData)	
			
		
		try: 
			b = jsonParms['g_relationList']
		except :
			r.append('g_relationList')

		return r	

	
def print_and_split(msg):
	print(msg)
	exit(0)
	
	
if __name__ == '__main__':
	
	with open(sys.argv[1]) as f:
		for l in f:
			jsonParms = json.loads(l)
	
	err = get_parms_missing(jsonParms)
	if ( err ) :
		print_and_split('\nError on processing json file -- quitting.\n...Missing these parameters ... [{}]'.format(err))
	
	global_vars = GlobalVars(jsonParms)
	
	load_domain_tables(jsonParms)
	
	md = MockData()
	
	# d_ are domain tables ( aka lookup, drop down ) -- they define the codes of the model
	# e_ are entity tables -- they describe the items of the model ( ex users, sale_items, item_description )
	# t_ are transaction tables -- they are the tables that hold the events of the entity tables ( ex sales, scheduling, inventory )
	#
	# later we will accpet a JSON object that defines the tables, columns and relationships. From this we will create the
	# table definitions and domain table data. Then create the table_relations dictionary and run the populate functions 
	#
	
	# 	1) open json machData.json
	#	2) get table list
	#	3) add to table_list{} 
	#	4) create DatabaseTable object for the table --> ttype : map parent to PK 
	#   5) get relation list from machData.json
	
	# loadAndValidate parameters

	# later this assignment to global_vars will be from the JSON object that defines the table/column names and thier and relationships
	# the first table in the list is the primary table in the relationship, the other tables are child relations
	
	
	#global_vars.table_relations.append([tl[1],tl[0]])
	
	global_vars.all_to_stdout()	
	
	if (global_vars.write_to_DB):

		if global_vars.use_max_DB_ID : 
			global_vars.global_id = get_last_id() + 1
		
		set_all_table_status()
				
		if (global_vars.truncate_and_load): 
			truncate_and_drop_tables()
			create_all_tables()
		
		if not(global_vars.truncate_and_load): 
			drop_all_indexes()
	
		write_domain_data()
	else:
		write_tables_to_file('DOMAIN')
	
	while global_vars.curr_batch_number < global_vars.num_of_batches:
	
		create_a_batch_of_all_tables()
	
		write_tables_to_file()
				
		if (global_vars.write_to_DB) : 
			bcp_all_data()
			
		global_vars.incr_batch_count()
		global_vars.all_to_stdout()
		
		
	if (global_vars.write_to_DB and global_vars.truncate_and_load):
		print("creating indexes....")
		create_all_indexes()	
		global_vars.all_to_stdout()	
	
	print('\n\nrun completed....')
	
		
	