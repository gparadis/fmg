import lazydb

class dbAccess(object):

	def dbConnect(self, connectMethod, connectString):
		return lazydb.Connection(connectMethod, connectString)

	def dbRecordSet(self, sql, *params):	
		db = self.dbConnect()
		return db(sql, *params)

	def dbCommand(self, sql, *params):
		db = self.dbConnect()
		return db.cursor().execute(sql, params)

	def dbInsert(self, sql, *params):
		# Semi-abstract method
		db = self.dbConnect()
		db.cursor().execute(sql, params)
		return db   # so subclasses can access it


