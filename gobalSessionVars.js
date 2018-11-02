
var g_machData_json = {};	// holds all json objects ... table diagrams, table relationships, machData.py parameters
var g_tableList     = {}
var g_editControl   = {}
var g_relationList  = {}	
var g_parameters    = {}	
	
var g_domainTable   = {}	// declared only here in machData_designER.html. Others load from session
var g_keyTable      = {}    // declared only here in machData_designER.html. Others load from session
	
	
function getGlobalVars() {

		
	if (sessionStorage.g_machData_json) {
alert('in get GV sess 10 [' + 	sessionStorage.g_machData_json + ']');
			g_machData_json = JSON.parse(sessionStorage.g_machData_json);
										}
										
	if (g_machData_json.g_domainTable)
		{
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
		} // else g_domain
	
	if (g_machData_json.g_keyTable)
		{
			g_keyTable = g_machData_json.g_keyTable
		}
		else
		{
			g_keyTable.PK    = 'PK'
			g_keyTable.FK    = 'FK'
			g_keyTable.PDK   = 'PDK'
			g_keyTable.FDK   = 'FDK'
			g_keyTable.noK   = 'None'
		} // else g_keyTable
	
	if (g_machData_json.g_parameters)
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
		} // else g_parameters
		
		
	if (g_machData_json.g_tableList) 		{g_tableList    = g_machData_json.g_tableList;}
	if (g_machData_json.g_relationList) 	{g_relationList = g_machData_json.g_relationList;}

	
alert('in get GV sess g_domainTable [' + Object.keys(g_domainTable) + ']')


	
} // getGlobalVars	
