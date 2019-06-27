
var g_machData_json = {};	// holds all json objects ... table diagrams, table relationships, machData.py parameters
var g_tableList     = {}
var g_editControl   = {}
var g_relationList  = {}	
var g_parameters    = {}	
var g_domainTable   = {}	
var g_keyTable      = {}    
var g_domainData	= {}
var g_numOfdomainTable = 0 	


function distributeGlobalVars() {	
								
	if  (('g_machData_json' in sessionStorage) == true )
		{ 
			g_machData_json = JSON.parse(sessionStorage.g_machData_json);	
		}							
								
	if  (('g_domainTable' in g_machData_json) == true )  
		{
			if ( Object.keys(g_machData_json.g_domainTable).length ==  g_numOfdomainTable)  {
				g_domainTable = g_machData_json.g_domainTable
			}	
			else
			{
				g_domainTable.int 		= 'integer'
				g_domainTable.vstr20 	= 'varchar(20)'
				g_domainTable.vstr80 	= 'varchar(80)'
				g_domainTable.vstr128 	= 'varchar(128)'
				g_domainTable.dtetm 	= 'datetime'
				g_domainTable.phone 	= 'varchar(20)'
				g_domainTable.email 	= 'varchar(40)'
				g_domainTable.address 	= 'varchar(128)'
				g_domainTable.full_name = 'varchar(128)'
				g_domainTable.dob 		= 'datetime'
				g_domainTable.amt500	= 'numeric(10,2)'
				g_domainTable.amt1000	= 'numeric(10,2)'				
			} // else g_domain
		}
		
	if (('g_keyTable' in g_machData_json) == true )  
		{
			g_keyTable = g_machData_json.g_keyTable
		}
		else
		{
			g_keyTable.pkey  = 'PK'
			g_keyTable.fkey  = 'FK'
			g_keyTable.pdkey = 'PDK'
			g_keyTable.fdkey = 'FDK'
			g_keyTable.noK   = 'None'
		} // else g_keyTable
	
	if (('g_parameters' in g_machData_json) == true )  
		{
			g_parameters = g_machData_json.g_parameters
		}
		else
		{
			g_parameters.use_max_DB_ID		     = false  // if this is true then the global_id value is set to the max primary table ID in the DB
			g_parameters.global_id_batch_size	 = 10
			g_parameters.global_id            	 = 1
			g_parameters.num_of_batches	 		 = 1
			g_parameters.curr_batch_number       = 0
			g_parameters.delim_char           	 = '|'
			g_parameters.truncate_and_load 		 = true
			g_parameters.write_to_DB 		 	 = false
			
			
		} // else g_parameters
	
	
	if (('g_tableList'    in g_machData_json) == true ) {g_tableList    = g_machData_json.g_tableList;}
	if (('g_relationList' in g_machData_json) == true ) {g_relationList = g_machData_json.g_relationList;}
	if (('g_domainData'   in g_machData_json) == true ) {g_domainData   = g_machData_json.g_domainData;}


} // distributeGlobalVars	



function putGlobalVars() {
	var g_machData_json = {};	// holds all json objects ... table diagrams, table relationships, machData.py parameters
		
	if (Object.keys(g_domainTable).length 	> 0) {g_machData_json.g_domainTable  = g_domainTable;}
	if (Object.keys(g_keyTable).length  	> 0) {g_machData_json.g_keyTable 	 = g_keyTable;}
	if (Object.keys(g_tableList).length 	> 0) {g_machData_json.g_tableList 	 = g_tableList;}
	if (Object.keys(g_relationList).length 	> 0) {g_machData_json.g_relationList = g_relationList;}
	if (Object.keys(g_parameters).length 	> 0) {g_machData_json.g_parameters 	 = g_parameters;}
	if (Object.keys(g_domainData).length 	> 0) {g_machData_json.g_domainData 	 = g_domainData;}
	
	sessionStorage.g_machData_json =  JSON.stringify(g_machData_json); 

} // putGlobalVars	
