
import json
import os
import sys
import random
import pyodbc
import subprocess
import datetime



class GlobalVars():
	def __init__(self,jsonParms):
		
		self.use_max_DB_ID		    = True 	if (jsonParms['g_parameters']['use_max_DB_ID'] 		  == None)	else jsonParms['g_parameters']['use_max_DB_ID']
		self.global_id_batch_size	= 1 	if (jsonParms['g_parameters']['global_id_batch_size'] == None)	else jsonParms['g_parameters']['global_id_batch_size']
		self.global_id		     	= 1 	if (jsonParms['g_parameters']['global_id'] 			  == None) 	else jsonParms['g_parameters']['global_id']
		self.num_of_batches		    = 1 	if (jsonParms['g_parameters']['num_of_batches']  	  == None)	else jsonParms['g_parameters']['num_of_batches']
		self.curr_batch_number		= 0 	if (jsonParms['g_parameters']['curr_batch_number'] 	  == None)	else jsonParms['g_parameters']['curr_batch_number']
		self.delim_char		     	= '|' 	if (jsonParms['g_parameters']['delim_char']  		  == None)	else jsonParms['g_parameters']['delim_char']
		self.truncate_and_load		= True 	if (jsonParms['g_parameters']['truncate_and_load']    == None)	else jsonParms['g_parameters']['truncate_and_load']

		self.keys					= jsonParms['g_keyTable']
		self.table_relations		= []
	
	def all_table_list(self):
		#
		#  tables can be listed multiple times in the relationship list.  This method
		#  will return a unique list of tables
		#
		all_lst = []
		rel_lst = global_vars.table_relations
		processed = {}		# use a dictionary to count unique occurances, ignore duplicate table entries
		
		for r in rel_lst:
			for t in r:
				num_processed  = len(processed.keys())
				processed[t.table_name] = 'processed'
				if num_processed < len(processed.keys()) :
					all_lst.append(t)
		return all_lst
	
	def incr_global_id(self):
		self.global_id = self.global_id + 1
		
	def incr_batch_count(self):
		self.curr_batch_number = self.curr_batch_number + 1
				
	def all_to_stdout(self):
		print('==================================================================\n')
		print('self.use_max_DB_ID 			: {}\n'.format(self.use_max_DB_ID ))		     
		print('self.global_id_batch_size	: {}\n'.format(self.global_id_batch_size )) 	  
		print('self.global_id				: {}\n'.format(self.global_id ))      	 
		print('self.num_of_batches			: {}\n'.format(self.num_of_batches )) 		 
		print('self.curr_batch_number  		: {}\n'.format(self.curr_batch_number ))    
		print('self.delim_char   			: {}\n'.format(self.delim_char ))         
		print('self.truncate_and_load 		: {}\n'.format(self.truncate_and_load ))	 
		#print('self.table_relations		: {}\n'.format(self.table_relations ))	 
		print('==================================================================\n')
		
class DatabaseTable():
	def __init__(self,table_name,table_type,data_tags):
		self.table_name = table_name
		self.table_type = table_type
		self.process_status = ''
		self.data_types = data_tags
		self.row_desc = {}
		self.rows     = []
		self.curr_row = None
		
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
			
			if col_keytyp == global_varskeys['pkey'] : idx_name = global_varskeys['pkey'] + '_' + self.table_name
			if col_keytyp == global_vars.keys['pdkey'] : idx_name = global_vars.keys['pdkey'] + '_' + self.table_name
			if col_keytyp == global_vars.keys['fkey']  : idx_name = global_vars.keys['fkey']  + '_' + self.table_name
			if col_keytyp == global_vars.keys['fdkey'] : idx_name = global_vars.keys['fdkey'] + '_' + self.table_name
			#
			# return first index column found ... 
			#
			if idx_name != '' : 
				return {'name':idx_name, 'col':col_name}
		return {}


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
        return m + '/' + d + '/' + y

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

	for t in global_vars.all_table_list():
		idx = t.get_index_name_and_col()
		if idx['name'].split('_')[0] ==  global_vars.keys['pkey']:
			primary_table_name = idx['name'].split('_')[1]
			primary_table_ID   = idx['col']
			break
				
	sql = 'select max(' + primary_table_ID + ') from ' + primary_table_name 
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	last_ID = runSQL.run_sql(sql)
	runSQL.close_conn()
	return int(last_ID[0][0])

'''	
def set_next_id():
    global global_id
    global_id = global_id + 1
'''

def table_ddl(ddl_type,tbl):
	table_name = tbl.table_name
	ddl = tbl.get_table_ddl()
	
	if ddl_type == 'CREATE':
		retstr = 'create table ' + table_name + ' ('
		
		for col in ddl:
			cn  = col[0]
			cdt = col[1]
			retstr = retstr + cn + ' ' + cdt + ','
		return retstr[:-1] + ')'
		
	if ddl_type == 'DROP':
		retstr = 'truncate table ' + table_name + ';\n'
		retstr = retstr + 'drop table ' + table_name + ';\n'
	else:
		retstr = None
	return retstr


def check_tables():
	tstat  = []
	retlst = []
	all_tables = global_vars.all_table_list()
	
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()

	for t in all_tables:
		
		if not(runSQL.check_if_object_exists(t)) : tstat.append(t)
	
	runSQL.close_conn()	
	if tstat == []: 
		retlst = ['ALL_EXIST']
			
	if len(tstat) == len(all_tables): 
		retlst = ['NONE_EXIST']
		
	if (retlst == []) and (len(tstat) != len(all_tables)): 
		retlst = tstat
		
	return retlst	
	


def check_indexes():
	tstat = []
	all_tables = global_vars.all_table_list()
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
    
	for t in all_tables:
		if not(runSQL.check_if_index_exists(t)) : tstat.append(t)
	
	runSQL.close_conn()	

	if tstat == []: 
		retlst = ['ALL_EXIST']
		
	if len(tstat) == len(all_tables):
		retlst = ['NONE_EXIST']
		
	if (tstat != [] and len(tstat) != len(all_tables)): 
		retlst = all_tables
		
	return retlst	
		
	
	
def create_all_tables():
	do_all = ''
	for t in global_vars.all_table_list():
		do_all = do_all + table_ddl('CREATE',t) + ';\n'
		
	#print_and_split(do_all)			
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	

def create_all_indexes():
	do_all = ''
	for t in global_vars.all_table_list():
		idx = t.get_index_name_and_col()
		do_all = do_all + 'CREATE INDEX ' + idx['name'] + ' on (' + idx['col'] + ');\n'
		
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
		
	
def drop_all_indexes():
	index_status = check_indexes()
	
	if index_status[0] == 'NONE_EXIST' : 
		return True

	do_all = ''
	for t in global_vars.all_table_list():
		do_all = do_all + 'DROP INDEX ' + t.get_index_name_and_col()['name'] + ';\n'
			
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	
	
def truncate_and_drop_tables():
	do_all = ''
	
	for t in global_vars.all_table_list():
		do_all = do_all + table_ddl('DROP',t) + '\n'
		
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	

def bcp_all_data():
	delim_char = global_vars.delim_char
	do_all = ''
	for t in global_vars.all_table_list():
		do_bcp = 'bcp ' + t.table_name + ' in ' + t.table_name + '.csv -Smssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com -Umssql_01_admin -PTh3Bomb! -dtestEntity -c -t"'+delim_char+'"'
		os.system(do_bcp)
		if t.table_type == global_vars.keys['pdkey'] : 
			t.process_status = 'loaded_to_database'
	
def define_domain_table(tbl):
# this is replaced with  a JSON object that defines the domain tables
#
# column description list : [data_type, col_order, col_key_type] ; col_key_type : (PK, FK, DK, None) 
# DK = domain key from domain ( loopup or code ) tables
#
	if tbl.table_name == 'd_person_type' :
		tbl.row_desc['pTypeID']			 = ['int',0, global_vars.dkey]
		tbl.row_desc['person_type_name'] = ['vstr80',1, None]
	
	if tbl.table_name == 'd_email':
		tbl.row_desc['eTypeID']		   	 = ['int',0, global_vars.dkey]
		tbl.row_desc['email_type'] 		 = ['vstr20',1, None]
	
	if tbl.table_name == 'd_phone':
		tbl.row_desc['phTypeID']	   	 = ['int',0, global_vars.dkey]
		tbl.row_desc['phone_type'] 		 = ['vstr20',1, None]

	if tbl.table_name == 'd_biz_action':
		tbl.row_desc['baTypeID']	   	 = ['int',0, global_vars.dkey]
		tbl.row_desc['biz_action'] 		 = ['vstr80',1, None]

	if tbl.table_name == 'd_address':
		tbl.row_desc['addrTypeID']	 	 = ['int',0, global_vars.dkey]
		tbl.row_desc['address_type'] 	 = ['vstr20',1, None]

	if tbl.table_name == 'd_perm_action':
		tbl.row_desc['permTypeID']		 = ['int',0, global_vars.dkey]
		tbl.row_desc['perm_action'] 	 = ['vstr20',1, None]

	
	
def populate_domain_table(tbl):
# this is replaced with  a JSON object that declares the data in the domain tables

	delim_char = global_vars.delim_char
	
	if tbl.table_name == 'd_person_type' :
		tbl.rows.append('0' + delim_char + 'patient')
		tbl.rows.append('1' + delim_char + 'anethesiologist')
		tbl.rows.append('2' + delim_char + 'surgeon')
		tbl.rows.append('3' + delim_char + 'or_nurse')
	
	if tbl.table_name == 'd_email':
		tbl.rows.append('0' + delim_char + 'primary')
		tbl.rows.append('1' + delim_char + 'work')
	
	if tbl.table_name == 'd_phone':
		tbl.rows.append('0' + delim_char + 'primary')
		tbl.rows.append('1' + delim_char + 'work')

	if tbl.table_name == 'd_biz_action':
		tbl.rows.append('0' + delim_char + 'scheduling')
		tbl.rows.append('1' + delim_char + 'patientRecords_All')
		tbl.rows.append('2' + delim_char + 'patientRecords_Op')

	if tbl.table_name == 'd_address':
		tbl.rows.append('0' + delim_char + 'primary')
		tbl.rows.append('1' + delim_char + 'work')

	if tbl.table_name == 'd_perm_action':
		tbl.rows.append('0' + delim_char + 'full')
		tbl.rows.append('1' + delim_char + 'read')
		tbl.rows.append('2' + delim_char + 'update')
		tbl.rows.append('3' + delim_char + 'create')
		tbl.rows.append('4' + delim_char + 'delete')		

def	define_table(tbl):
# this is replaced with the table / column names and definition defined in a JSON object
	
	if tbl.table_name == 'people':
		tbl.row_desc['peopleID']	 	= ['int',      0, global_vars.keys['pkey']]
		tbl.row_desc['full_name']	 	= ['full_name',1, None]
		tbl.row_desc['date_of_birth']	= ['dob',      2, None]
		
	if tbl.table_name == 'address':
		tbl.row_desc['addrTypeID']	 	= ['int',      0, global_vars.keys['pdkey']]
		tbl.row_desc['peopleID']	 	= ['int',      1, global_vars.keys['fkey']]
		tbl.row_desc['address']	 	    = ['address',  2, None]
		
	if tbl.table_name == 'email':
		tbl.row_desc['eTypeID']	 	    = ['int',      0, global_vars.keys['pdkey']]
		tbl.row_desc['peopleID']	 	= ['int',      1, global_vars.keys['fkey']]
		tbl.row_desc['email']	 	    = ['email',  2, None]
		
	if tbl.table_name == 'phone':
		tbl.row_desc['phTypeID']	 	= ['int',      0, global_vars.keys['pdkey']]
		tbl.row_desc['peopleID']	 	= ['int',      1, global_vars.keys['fkey']]
		tbl.row_desc['phone_num']	 	= ['phone',  2, None]
		
	if tbl.table_name == 'people_by_type':
		tbl.row_desc['pTypeID']	 	    = ['int',      0, global_vars.keys['pdkey']]
		tbl.row_desc['peopleID']	 	= ['int',      1, global_vars.keys['fkey']]	
		
			
def clear_all_table_rows():
	for t in global_vars.all_table_list():
		if t.table_type != global_vars.keys['pdkey'] : t.clear_all_rows()
		
def write_tables_to_file():
	for t in global_vars.all_table_list():
		if t.process_status == '' :  
			with open(t.table_name+'.csv', "w") as write_file:
				for l in t.rows: write_file.write(str(l)+'\n')

def populate_and_create_relationships():
	# this will be replaced by a JSON object that describes the tables and maps the relationships
	# in building the relation list. Assume the global id is static through the entire list read .. 
	# by enitre list I am refering to the list that contains the relation lists. 
	# The relatino list is a multi dimesional arry ( list ) of lists. The larger list is what we process usinfg a single 
	# global id. the global id is incremented with each iteration of the list
	
	clear_all_table_rows()
	max_loop = global_vars.global_id + global_vars.global_id_batch_size
	while global_vars.global_id < max_loop:
			
		for relation_list in global_vars.table_relations:
				
			ptbl = relation_list[0]
						
			populate_table(ptbl,None)
				
			for tbl in relation_list[1:]:
				populate_table(ptbl,tbl)	
		
		global_vars.incr_global_id()
		#print ('....completed batch number {}'.format(global_vars.global_id - first_batch_id))
			
	print ('\nnumber of rows per batch {} \n\n'.format(global_vars.global_id_batch_size))
		
		
def populate_table(ptbl,tbl):
	if tbl == None : 
		tname = ''
	else:
		tname = tbl.table_name
    
	pkey  = global_vars.keys['pkey']
	pdkey = global_vars.keys['pdkey']
	fkey  = global_vars.keys['fkey']
	
	if ptbl.table_type == global_vars.keys['pdkey'] and tbl == None : return
	dkey = ''
	
	if ptbl.table_type == global_vars.keys['pdkey'] and tbl != None : 
		dkey = str(md.random_from_list(ptbl.rows)[0])
		
	if ptbl.table_type != global_vars.keys['pdkey'] and tbl == None : tbl = ptbl
	delim_char = global_vars.delim_char
	row = ''
	str_gid = str(global_vars.global_id)
	
	for col in 	tbl.get_table_desc():
		#print ('col :: {} '.format(col))
		if col[2] == pkey or col[2] == fkey : row = row + str_gid + delim_char
		if col[2] == pdkey : row = row + dkey + delim_char
		if col[2] == None :
			if col[1] == 'full_name' : row = row + md.random_full_name() 	 + delim_char  
			if col[1] == 'dob'       : row = row + md.random_date(1945,1985) + delim_char  
			if col[1] == 'dtetm'     : row = row + md.random_date(1900,2020) + delim_char  
			if col[1] == 'address'   : row = row + md.random_addr()			 + delim_char  
			if col[1] == 'email'     : row = row + str_gid + '@email.com' 	 + delim_char
			if col[1] == 'phone'     : row = row + md.random_phone()         + delim_char  
			#if col[1] == 'int'       : row = row + md.random_int(1000,10000) + delim_char  
			
	tbl.rows.append(row[:-1])			

def get_table_type(tblCols):
	ttyp = global_vars.keys['noK']
	for c in tblCols:
		#print('10 c {}\n'.format(c))   
		if (c[2] != global_vars.keys['noK']) :
			#print('20 c[2] {}\n'.format(c[2]))   
			if (c[2] == global_vars.keys['pkey']): 
				ttyp = global_vars.keys['pkey']
			#print('30 ttyp {}\n'.format(ttyp))		
			if (c[2] == global_vars.keys['pdkey']) and (ttyp != global_vars.keys['pkey']): 
				ttyp = global_vars.keys['pdkey']
			#print('40 ttyp {}\n'.format(ttyp))
			if (c[2] == global_vars.keys['fkey'])  and (ttyp == global_vars.keys['noK']) : ttyp = global_vars.keys['fkey']
			if (c[2] == global_vars.keys['fdkey']) and (ttyp == global_vars.keys['noK']) : ttyp = global_vars.keys['fdkey']
			#print('50 ttyp {}\n'.format(ttyp))
	return ttyp
	
def load_and_validate_parameters(jsonParms):
	table_list = []
	
	tbls        = jsonParms['g_tableList']
	data_tags   = jsonParms['g_domainTable']		# Nov 5,2018 : change the name g_domainTable to g_dataTags in the web pages and .js includes
		
	for t in tbls.keys():
		rdesc = {}
		colcnt = 0
		ttyp = get_table_type(tbls[t])
		
		for c in tbls[t]:
			rdesc[c[0]] = [c[1], colcnt, c[2]]
			colcnt = colcnt + 1
		
		tblC = DatabaseTable(t,ttyp,data_tags)
		tblC.row_desc = rdesc
		table_list.append(tblC)	
		
	return table_list
	
	
def print_and_split(msg):
	print(msg)
	exit(0)
	
	
if __name__ == '__main__':
	
	with open(sys.argv[1]) as f:
		for l in f:
			jsonParms = json.loads(l)
	
	
	
	
	global_vars = GlobalVars(jsonParms)

	tl = load_and_validate_parameters(jsonParms)
	
	#print_and_split('\ntype tl {}'.format(type(tl)))
	#print('\na table name {}'.format(tl[0].table_name))
	#print('\nall table type userA {}'.format(tl[0].table_type))
		

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
	'''
	tname = 'people'
	ttype = global_vars.keys['pkey']
	table_list = {}
	table_list[tname] = DatabaseTable(tname,ttype)
	define_table(table_list[tname])
	print ('row desc {}'.format(table_list[tname].row_desc))
	tname = 'address'
	ttype = global_vars.keys['fkey']
	table_list[tname] = DatabaseTable(tname,ttype)
	define_table(table_list[tname])
	print ('row desc {}'.format(table_list[tname].row_desc))
	print (global_vars.all_table_list())
	print_and_split('cya')
	
	d_person_type = DatabaseTable('d_person_type', 'domain')
	d_email       = DatabaseTable('d_email', 'domain')
	d_phone       = DatabaseTable('d_phone', 'domain')
	d_biz_action  = DatabaseTable('d_biz_action', 'domain')
	d_address     = DatabaseTable('d_address', 'domain')
	d_perm_action = DatabaseTable('d_perm_action', 'domain')
	
	#define domain tables - later this data will be obtained from JSON input
	define_domain_table(d_person_type)
	define_domain_table(d_email)
	define_domain_table(d_phone)
	define_domain_table(d_biz_action)
	define_domain_table(d_address)
	define_domain_table(d_perm_action)
	
	#populate domain tables - later this data will be obtained from JSON input

	populate_domain_table(d_person_type)
	populate_domain_table(d_email)
	populate_domain_table(d_phone)
	populate_domain_table(d_biz_action)
	populate_domain_table(d_address)
	populate_domain_table(d_perm_action)
	
	# later this data will be obtained from JSON input
	
	people     		   = DatabaseTable('people','parent')
	address    		   = DatabaseTable('address','child')
	email      		   = DatabaseTable('email','child')
	phone      		   = DatabaseTable('phone','child')
	people_by_type     = DatabaseTable('people_by_type','child')
	'''


	# later this assignment to global_vars will be from the JSON object that defines the table/column names and thier and relationships
	# the first table in the list is the primary table in the relationship, the other tables are child relations
	
	global_vars.table_relations.append([tl[0],tl[1]])
	
	'''
	global_vars.table_relations.append([people])	
	global_vars.table_relations.append([d_address,address])
	global_vars.table_relations.append([d_email,email])
	global_vars.table_relations.append([d_phone,phone])
	global_vars.table_relations.append([d_person_type,people_by_type])
	
	# later this data will be obtained from JSON input
	
	define_table(people)
	define_table(address)
	define_table(email)
	define_table(phone)
	define_table(people_by_type)
	'''
	# this will be run after the JSON is parsed and tables defined and in the case of domain tables populated with data
	# essentially this is where the code will start ( again, after the JSON parse )
	#
	
	if global_vars.use_max_DB_ID : 
		global_vars.global_id = get_last_id() + 1
	
	global_vars.all_to_stdout()	
	
	table_status = check_tables()
	#print_and_split(table_status)
	
	if (table_status[0] != 'NONE_EXIST') and (table_status[0] != 'ALL_EXIST') :
		print('these tables are missing ....{}'.format(table_status))
		exit(1)
	
	if (table_status[0] == 'ALL_EXIST' and global_vars.truncate_and_load): 
		truncate_and_drop_tables()
		create_all_tables()
	
	if (table_status[0] == 'ALL_EXIST' and not(global_vars.truncate_and_load)): 
		drop_all_indexes()
		
	if (table_status[0] == 'NONE_EXIST'):
		create_all_tables()
	
	while global_vars.curr_batch_number < global_vars.num_of_batches:
		populate_and_create_relationships()
		write_tables_to_file()
		bcp_all_data()
		global_vars.incr_batch_count()
		global_vars.all_to_stdout()
		
	print_and_split('\n\ncya 100')
	
		
	