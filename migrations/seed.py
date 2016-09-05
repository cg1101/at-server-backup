import sqlalchemy

from alembic import context

from db.schema import t_database_settings


def add_seed_data(table_name: str, data: dict):
	"""
	Adds a seed data record to the database if the 
	database has already been seeded. The data is
	a dictionary of insert field/value pairs.
	
	Examples:
	add_seed_data("tenses", {'name': 'Past'})
	add_seed_data("tenses", {'name': 'Present'})
	add_seed_data("tenses", {'name': 'Future'})
	"""
	if is_database_seeded():

		if not len(data.keys()):
			raise ValueError("Must provide data to insert")

		# build column and value lists
		columns = []
		values = []

		for field in data.keys():
			columns.append(field)
			values.append(":{0}".format(field))

		columns = ",".join(columns)
		values = ",".join(values)

		# build query and insert data
		sql = "insert into %(table_name)s (%(columns)s) values (%(values)s)" %dict(table_name=table_name, columns=columns, values=values)
		migrate_context = context.get_context()
		migrate_context.connection.execute(sqlalchemy.text(sql), **data)


def delete_seed_data(table_name: str, constraint: str, **data):
	"""
	Deletes seed data from the database if the database
	has already been seeded. The constraint should select
	the single record to be deleted. Any variables that
	need to be included in the constraint are to be passed
	in the data. For information on string formatting, check
	sqlalchemy.text.
	
	Examples:
	delete_seed_data("tenses", "name = :name", name="Past")
	delete_seed_data("tenses", "name = :name", name="Present")
	delete_seed_data("tenses", "name = :name", name="Future")
	"""
	if is_database_seeded():
		sql = "delete from %(table_name)s where %(constraint)s" %dict(table_name=table_name, constraint=constraint)
		migrate_context = context.get_context()
		migrate_context.connection.execute(sqlalchemy.text(sql), **data)


def is_database_seeded():
	"""
	Checks if the database has been seeded according
	to the settings table.
	"""
	migrate_context = context.get_context()
	
	# check if settings table exists
	if not migrate_context.dialect.has_table(migrate_context.connection, t_database_settings.name):
		return False
	
	result = migrate_context.connection.execute(t_database_settings.select())

	# check if record exists
	if not result.rowcount:
		return False

	if result.rowcount > 1:
		raise RuntimeError("Multiple database settings rows")
	
	# return seed status value
	settings = result.fetchone()
	return settings["seeded"]
