'''Main dbaccess module for accessing VFP tables via ODBC.'''

import odbc
from dbaccess import dbAccess

class dbVFP(dbAccess):
	def __init__(self, dbpath):
		self.dbpath = dbpath
	def dbConnect(self):
		connectString = ('driver={Microsoft FoxPro VFP Driver (*.dbf)};'
				'SourceType=DBF;SourceDB='+self.dbpath)
		return dbAccess.dbConnect(self, odbc.odbc, connectString)

	def dbInsert(self, sql, *params):
		# execute the passed command, and return the last_insert_id():
		db = dbAccess.dbInsert(self, sql, *params)		
		
		# No real great way to get the last insert id
		# from vfp as it isn't a real db server. Return
		# -1 instead.
		return -1		

		# This is how it is done in MySQL:
		#idcursor = db("select last_insert_id() as iid")
		#return idcursor[0].iid


if __name__ == "__main__":
	# Test runs only if we are running as a script:
	print "Hello, let us look at the breakfast menu shall we?"
	dbvfp1 = dbVFP("c:/temp/pytest/")
	sqlresult = dbvfp1.dbRecordSet("select * from test")
	for record in sqlresult:
		print record
		#print "%s %n %s %.4f" % (record.id_fam_courb, record.age_ligne_courb, record.id_type_courb, record.val)
	print "Do any of these sound appetizing?"
