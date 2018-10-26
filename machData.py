
import json
import os
import random
import pyodbc
import subprocess
import datetime

global_use_max_DB_ID     = True  # if this is true then the global_id value is set to the max primary table ID in the DB
global_id_batch_size 	 = 100
global_id            	 = 0
global_num_of_batches	 = 10
delim_char           	 = '|'
truncate_and_load 		 = False

people     = ['people_ID,full_name,date_of_birth',
			  'int,varchar(128),datetime',
			  'PK,people,people_ID']
address    = ['addr_type_ID,addr,people_ID',
			  'int,varchar(128),int',
			  'FK,address,people_ID']
email      = ['email_type_ID,email,people_ID',
			  'int,varchar(80),int',
			  'FK,email,people_ID']
phone      = ['phone_type_ID,phone,people_ID',
			  'int,varchar(80),int',
			  'FK,phone,people_ID']
personType = ['people_ID,person_type_ID,start_date,expire_date',
			  'int,int,datetime,datetime',
			  'FK,personType,people_ID']
			  
first_data_row = 3	



class MockData:

    def __init__(self):

        self.entity_type  = {'personType': {'patient': 0, 'anethesiologist': 1, 'surgeon': 2,
                                            'or_nurse': 3, 'nurse_01': 4},
                             'email': {'primary':0, 'work':1},
                             'phone': {'primary':0, 'work':1},
                             'businessArea': {'scheduling':0, 'patientRecords_All': 1, 'patientRecords_Op': 2 },
                             'address' : {'primary':0, 'work':1},
                             'permissionActions' : {'full':0,'read': 1, 'update': 2, 'create':3, 'delete':4 }
                             }


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

    def get_entity_group_list(self):
        return list(self.entity_type)


    def get_entity_type_list(self):
        gid = 0
        rl = []

        for g in self.get_entity_group_list():
            for t in list(self.entity_type[g]):
                rl.append([gid, t])
            gid = gid + 1

        return rl


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
	
	def check_if_object_exists(self, db_obj):
		if not(self.mssql_conn) : self.open_conn()
		cur = self.mssql_conn.cursor()
		cur.execute('select 1 from sys.objects where name = \'' + db_obj + '\'')
		return cur.fetchall()
			
	def check_if_index_exists(self, db_obj):
		if not(self.mssql_conn) : self.open_conn()
		cur = self.mssql_conn.cursor()
		cur.execute('select 1 from sys.indexes where name = \'' + db_obj + '\'')
		return cur.fetchall()
		
'''
   start functions 
'''		
def get_last_id():
	primary_table_name = 'people'
	primary_table_ID   = 'people_ID'
	sql = 'select max(' + primary_table_ID + ') from ' + primary_table_name 
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	last_ID = runSQL.run_sql(sql)
	runSQL.close_conn()
	
	return int(last_ID[0][0])
		
def set_next_id():
    global global_id
    global_id = global_id + 1

def table_ddl(ddl_type,lst):
	table_name = lst[2].split(',')[1]
	
	if ddl_type == 'CREATE':
		retstr = 'create table ' + table_name + ' ('
		colNames = lst[0].split(',')
		colDTs   = lst[1].split(',')
		for i in range(len(colNames)):
			cn  = colNames[i]
			cdt = colDTs[i]
			retstr = retstr + cn + ' ' + cdt + ','
		
		return retstr[:len(retstr)-1] + ')'
		
	if ddl_type == 'DROP':
		retstr = 'truncate table ' + table_name + '\n'
		retstr = retstr + 'drop table ' + table_name + '\n'
	else:
		retstr = None

	return retstr

def index_ddl(ddl_type,lst):
	s     = lst[2].split(',')
	idx_type = s[0]
	table_name = s[1]
	idx_col    = s[2]
	
	if ddl_type == 'CREATE' : 
		retstr = 'create index ' + idx_type + '_' + table_name + ' on ' + table_name + ' (' + idx_col + ')'
		return retstr
		
	if ddl_type == 'DROP'   : 
		retstr = 'drop index ' + table_name + '.' + idx_type + '_' + table_name
	else : 
		retstr = None
	
	return retstr

	
def make_mock_data_files():
	global delim_char
	global global_id
	global global_id_batch_size
	
	global people 		
	global address 		
	global email 		
	global phone 		
	global personType 	
		
	tlst  = ['people', 'address', 'email', 'phone', 'personType']
		
	people = people[:first_data_row]
	address= address[:first_data_row]
	email= email[:first_data_row]
	phone= phone[:first_data_row]
	personType= personType[:first_data_row]
	
	max_loop = global_id + global_id_batch_size
	
	print('.... creating data files. starting ID : {}'.format(global_id))
	
	while global_id < max_loop:
		str_gid = str(global_id)
		
		row = str_gid + delim_char + md.random_full_name() + delim_char + md.random_date(1945,1985)
		people.append(row)
				
		row = str(md.entity_type['address']['primary'])  + delim_char + md.random_addr() + delim_char + str_gid
		address.append(row)
		row = str(md.entity_type['address']['work']) + delim_char + md.random_addr() + delim_char +  str_gid
		address.append(row)
		
		row = str(md.entity_type['email']['primary']) + delim_char + 'primary' + str_gid + '@email.com' + delim_char +  str_gid
		email.append(row)
		row = str(md.entity_type['email']['work']) + delim_char + 'work' + str_gid + '@email.com' + delim_char + str_gid
		email.append(row)
		
		row = str(md.entity_type['phone']['primary']) + delim_char + md.random_phone() + delim_char + str_gid
		phone.append(row)
		row = str(md.entity_type['phone']['work']) + delim_char + md.random_phone() + delim_char + str_gid
		phone.append(row)
		
		row = str_gid + delim_char + str( md.random_from_list(list(md.entity_type['personType'].values())) ) + delim_char + \
			md.random_date(2010,2015) + delim_char +  md.random_date(2016,2020)
		personType.append(row)
		
		set_next_id()

	with open("people.csv", "w") as write_file:
		#write_file.write(people[0]+'\n') 	    
		for l in people[first_data_row:]: write_file.write(l+'\n')

	with open("address.csv", "w") as write_file:
		#write_file.write(address[0]+'\n') 	
		for l in address[first_data_row:]: write_file.write(l+'\n')

	with open("email.csv", "w") as write_file:
		#write_file.write(email[0]+'\n')
		for l in email[first_data_row:]: write_file.write(l + '\n')

	with open("phone.csv", "w") as write_file:
		#write_file.write(phone[0]+'\n')
		for l in phone[first_data_row:]: write_file.write(l + '\n')

	with open("personType.csv", "w") as write_file:
		#write_file.write(personType[0]+'\n')
		for l in personType[first_data_row:]: write_file.write(l + '\n')

	with open('entity_group.csv', 'w') as write_file:
		#l = 'entity_group_ID, entity_group'
		#write_file.write(l + '\n')

		i = 0
		for s in md.get_entity_group_list():
			l = str(i) + delim_char + s
			write_file.write(l + '\n')
			i = i + 1

	with open('entity_type.csv', 'w') as write_file:
		#l = 'entity_group_ID, entity_type_ID, entity_type'
		#write_file.write(l + '\n')

		i    = 0
		cgid = 0
		for l in md.get_entity_type_list():
			gid = l[0]
			if gid != cgid :
				i = 0
				cgid = gid

			s   = str(l[0]) + delim_char + str(i) + delim_char + l[1]
			write_file.write(s + '\n')
			i = i + 1
	
	
	print('.... creating data files. last ID : {}'.format(global_id))
	
	
	
def check_tables():
	tlst  = ['people', 'address', 'email', 'phone', 'personType']
	tstat = []
	
	if len(tlst) == 0 : return None
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	
	runSQL.open_conn()

	for t in tlst:
		if not(runSQL.check_if_object_exists(t)) : tstat.append(t)
	
	runSQL.close_conn()	

	if tstat == []            : retlst = ['ALL_EXIST']
	if len(tstat) == len(tlst): retlst = ['NONE_EXIST']
	if (tstat != [] and len(tstat) != len(tlst)): retlst = tstat
		
	return retlst	
	


def check_indexes():
	tlst  = ['PK_people', 'FK_address', 'FK_email', 'FK_phone', 'FK_personType']
	tstat = []
	
	if len(tlst) == 0 : return None
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()

	for t in tlst:
		if not(runSQL.check_if_index_exists(t)) : tstat.append(t)
	
	runSQL.close_conn()	

	if tstat == []            : retlst = ['ALL_EXIST']
	if len(tstat) == len(tlst): retlst = ['NONE_EXIST']
	if (tstat != [] and len(tstat) != len(tlst)): retlst = tstat
		
	return retlst	
		
	
	
def create_all_tables():
	tlst  = [people, address, email, phone, personType]
	do_all = ''

	if len(tlst) == 0 : return None

	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	  
	for t in tlst:
		#print('in create all tables {} {} len{}'.format(t,tlst, len(tlst)))
		do_all = do_all + table_ddl('CREATE', t) + ';\n'
	
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	

def create_all_indexes():
	tlst  = [people, address, email, phone, personType] #, entity_group, entity_type]
	do_all = ''
	
	if len(tlst) == 0 : return None
	
	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
	  
	for t in tlst:
		do_all = do_all + index_ddl('CREATE', t) + ';\n'
	
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
		
	

def drop_all_indexes():
	tlst  = [people, address, email, phone, personType]
	do_all = ''
	
	index_status = check_indexes()
	
	if index_status[0] != 'ALL_EXIST' : 
		print_and_split('not all indexes found .. {}'.format(index_status))
		
	if len(tlst) == 0 : return None

	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
		
	for t in tlst:
		do_all = do_all + index_ddl('DROP', t) + '; '
	#print_and_split(do_all)
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	
	
	
def truncate_and_drop_tables():
	tlst  = [people, address, email, phone, personType]
	do_all = ''
	
	if len(tlst) == 0 : return None

	runSQL = RunDDL_MSSQL('{SQL Server}','mssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com','testEntity','mssql_01_admin','Th3Bomb!')
	runSQL.open_conn()
		
	for t in tlst:
		do_all = do_all + table_ddl('DROP', t) + ';\n'
		
	runSQL.run_ddl(do_all)
	runSQL.close_conn()	
	return True	


def bcp_all_data():
	global delim_char
	tlst  = ['people', 'address', 'email', 'phone', 'personType']
	
	if len(tlst) == 0 : return None
		
	for t in tlst:

		do_bcp = 'bcp ' + t + ' in ' + t + '.csv -Smssql-01.cq79i0ypklbj.us-east-2.rds.amazonaws.com -Umssql_01_admin -PTh3Bomb! -dtestEntity -c -t"'+delim_char+'"'

		print(do_bcp)
		os.system(do_bcp)
		
	return True		
	
	
def print_and_split(msg):
	print(msg)
	exit(0)
	
if __name__ == '__main__':
	
	if global_use_max_DB_ID : 
		global_id = get_last_id() + 1
		
	sdt = datetime.datetime.now()
	
	print('start time                	: {}'.format(str(sdt)))
	print('current working directory 	: {}'.format(os.getcwd()))
	print('using max global ID from DB	: {}'.format(global_use_max_DB_ID))
	print('global ID starting at     	: {}'.format(global_id))
	print('batch size                	: {}'.format(global_id_batch_size))
	print('number of batches         	: {}'.format(global_num_of_batches))
	print('truncate and load mode    	: {}'.format(truncate_and_load))
	
	md = MockData()

	
	
	table_status = check_tables()
	
	if (table_status[0] != 'NONE_EXIST') and (table_status[0] != 'ALL_EXIST') :
		print('these tables are missing ....{}'.format(table_status))
		exit(1)
	
	if (table_status[0] == 'ALL_EXIST' and truncate_and_load): 
		truncate_and_drop_tables()
		create_all_tables()
	
	if (table_status[0] == 'ALL_EXIST' and not(truncate_and_load)): 
		drop_all_indexes()
		
	if (table_status[0] == 'NONE_EXIST'):
		create_all_tables()
		
	nb = 0
	while nb < global_num_of_batches:
		print('....batch size                   : {}'.format(global_id_batch_size))
		print('....number of batches to process : {}'.format(global_num_of_batches))
		print('....processing batch number      : {}'.format(nb+1))
		print('....starting ID for this batch   : {}'.format(global_id))
			
		make_mock_data_files()
		bcp_all_data()
		nb = nb + 1
		
	#print_and_split('about to create all indexes')
	
	create_all_indexes()
	
	edt = datetime.datetime.now()
	print('start time                : {}'.format(str(sdt)))
	print('finish time               : {}'.format(str(edt)))
	
	print('thats all folks!!')
	