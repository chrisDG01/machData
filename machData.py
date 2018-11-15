
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
		print('self.write_to_DB 			: {}\n'.format(self.write_to_DB ))	
		
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
		self.row_in_process = False
		
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

	

def clear_all_process_status() :
	for tbl in global_vars.table_objs.values():
		tbl.row_in_process = False
	

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
	all_tables = global_vars.table_objs.values()
	
	
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
	all_tables = global_vars.table_objs.values()
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
	for t in global_vars.table_objs.values():
		do_all = do_all + table_ddl('CREATE',t) + ';\n'
		
	#print_and_split(do_all)			
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	

def create_all_indexes():
	do_all = ''
	for t in global_vars.table_objs.values():
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
	for t in global_vars.table_objs.values():
		do_all = do_all + 'DROP INDEX ' + t.get_index_name_and_col()['name'] + ';\n'
			
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	
	
def truncate_and_drop_tables():
	do_all = ''
	
	for t in global_vars.table_objs.values():
		do_all = do_all + table_ddl('DROP',t) + '\n'
		
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	

def bcp_all_data():
	delim_char = global_vars.delim_char
	do_all = ''
	for t in global_vars.table_objs.values():
		do_bcp = 'bcp ' + t.table_name + ' in ' + t.table_name + '.csv -Smssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com -Umssql_01_admin -PTh3Bomb! -dtestEntity -c -t"'+delim_char+'"'
		os.system(do_bcp)
		if t.table_type == global_vars.table_keys['pdkey'] : 
			t.process_status = 'loaded_to_database'
	
def load_domain_table(tbl):
# this is replaced with  a JSON object that defines the domain tables
#
# column description list : [data_type, col_order, col_key_type] ; col_key_type : (PK, FK, DK, None) 
# DK = domain key from domain ( loopup or code ) tables
#
	if tbl.table_name == 'd_person_type' :
		tbl.row_desc['pTypeID']			 = ['int',0, global_vars.dkey]
		tbl.row_desc['person_type_name'] = ['vstr80',1, None]
	
	
	
def populate_domain_table(tbl):
# this is replaced with  a JSON object that declares the data in the domain tables

	delim_char = global_vars.delim_char
	
	if tbl.table_name == 'd_person_type' :
		tbl.rows.append('0' + delim_char + 'patient')
		tbl.rows.append('1' + delim_char + 'anethesiologist')
		tbl.rows.append('2' + delim_char + 'surgeon')
		tbl.rows.append('3' + delim_char + 'or_nurse')
	
			
def clear_all_table_rows():
	for t in global_vars.table_objs.values():
		if t.table_type != global_vars.table_keys['pdkey'] : t.clear_all_rows()
		
def write_tables_to_file():
	delim_char = global_vars.delim_char
	
	for t in global_vars.table_objs.values():
		if t.process_status == '' :  
			with open(t.table_name+'.csv', "w") as write_file:
				for l in t.rows: 
					s = ''.join(c+delim_char for c in l)[:-1]
					write_file.write(s+'\n')

def populate_and_create_relationships():
	# this will be replaced by a JSON object that describes the tables and maps the relationships
	# in building the relation list. Assume the global id is static through the entire list read .. 
	# by enitre list I am refering to the list that contains the relation lists. 
	# The relatino list is a multi dimesional arry ( list ) of lists. The larger list is what we process usinfg a single 
	# global id. the global id is incremented with each iteration of the list
	
	clear_all_table_rows()
	max_loop = global_vars.global_id + global_vars.global_id_batch_size
	while global_vars.global_id < max_loop:
		
		clear_all_process_status()
		for relation_list in global_vars.table_relations:
			 
			ptbl = global_vars.table_objs[relation_list[0]]

			populate_table(ptbl,None)
				
			for tn in relation_list[1:]:
				populate_table(ptbl,global_vars.table_objs[tn])	
		
		global_vars.incr_global_id()
			
	print ('\nnumber of rows per batch {} \n\n'.format(global_vars.global_id_batch_size))
		
		
def populate_table(ptbl,tbl):
	
    
	pkey  = global_vars.table_keys['pkey']
	pdkey = global_vars.table_keys['pdkey']
	fkey  = global_vars.table_keys['fkey']
	fdkey = global_vars.table_keys['fdkey']
	
	
	if ptbl.table_type == global_vars.table_keys['pdkey'] and tbl == None : 
		return
		
	dkey = ''
	if ptbl.table_type == global_vars.table_keys['pdkey'] and tbl != None : 
		dkey = str(md.random_from_list(ptbl.rows)[0])							# we assume the primary key is the first column in the row
	
	if ptbl.table_type == global_vars.table_keys['pkey'] :
		pkColNames = ptbl.get_column_names_by_keytype(ptbl.table_type)

	if ptbl.table_type == global_vars.table_keys['pdkey'] :
		pdkColNames = ptbl.get_column_names_by_keytype(ptbl.table_type)
		
	if ptbl.table_type != global_vars.table_keys['pdkey'] and tbl == None : 
		tbl = ptbl

	# nov 12, 2018 cglenn
	# if parent and child are being processed and the parent is pkey or pdkey then  : if (colnames are equal) and ptbl is pkey and tbl is fkey 
	# then link them ( tbl.fkey gets the str_gid
	
	delim_char = global_vars.delim_char
	str_gid = str(global_vars.global_id)
	
	row = []
	if tbl.row_in_process == True:
		row = tbl.rows.pop()
	
	for col in 	tbl.get_table_desc():
		
		if ((col[2] == fdkey) and (col[0] in pdkColNames)):
			row.append(dkey)  # put in correct index of row....
			
		if 	tbl.row_in_process == False:
			if col[2] in [ pkey,fkey ]:
				row.append(str_gid)
			
			#if col[2] == pdkey : row = row + dkey + delim_char
			
			if col[2] == u'None' :
				#print ('.... 10 row :: {} '.format(row))
				if col[1] == 'full_name' : row.append(md.random_full_name())
				if col[1] == 'dob'       : row.append(md.random_date(1945,1985)) 	 
				if col[1] == 'dtetm'     : row.append(md.random_date(1900,2020)) 	 
				if col[1] == 'address'   : row.append(md.random_addr())			 	 
				if col[1] == 'email'     : row.append(str_gid + '@email.com') 	 	
				if col[1] == 'phone'     : row.append(md.random_phone())         	 
				if col[1] == 'int'       : row.append(str(md.random_int(1000,10000)))
				if col[1] == 'vstr20'    : row.append(str('S' * 20))		 	        
				if col[1] == 'vstr80'    : row.append(str('S' * 80))		 	        
				if col[1] == 'vstr128'   : row.append(str('S' * 128))		 	    
				
	tbl.rows.append(row)			
	tbl.row_in_process = True
	
def get_parms_missing(jsonParms):
		r=[]
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
	
	
	#print('keys {} '.format(global_vars.table_keys));
		

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
	
	
	if global_vars.use_max_DB_ID : 
		global_vars.global_id = get_last_id() + 1
	
	global_vars.all_to_stdout()	
	
	if (global_vars.write_to_DB):
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
				
		if (global_vars.write_to_DB) : 
			bcp_all_data()
			
		global_vars.incr_batch_count()
		global_vars.all_to_stdout()
		
	print('\n\nrun completed....')
	
		
	