import flask
from flask import request, jsonify
import psycopg2 # connect (to Postgres database)
import pkg_resources # resource_string (for retrieving sql queries)
import configparser # (to read properties file for database host, etc.)
from anytree import Node, LevelOrderIter

# Reference: https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask#lesson-goals

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.before_first_request
def init():
	print("temp")

	# store the slug hierarchy in memory

	# read the slug hierarchy and store it in a tree in O(N) time
	query = 'SELECT slug, parent_slug FROM regions'

	conn = connect_database()
	cur = conn.cursor()
	cur.execute(query)

	result = cur.fetchall()

	cur.close() # close database connection

	dict_slug_subslugs = dict()
	for slug, parent_slug in result:
		parent = Node(parent_slug)
		child = Node(slug, parent_slug)

	# TODO

	# iterate the final tree and store the list of all sub-slugs for each slug
	

	for slug, subslug in dict_slug_subslugs.items():
		print(x)
		print(y)

	print(jsonify(result))

# E.g., http://127.0.0.1:5000/api/v1/average?origin=CNGGZ&destination=EETLL&date_from=2016-01-01&date_to=2016-01-01
@app.route('/api/v1/average', methods=['GET'])
def average():
	# ensure required arguments are passed
	args = request.args

	origin = args.get('origin')
	destination = args.get('destination')
	date_from = args.get('date_from')
	date_to = args.get('date_to')
	
	if is_null_or_empty(origin, destination, date_from, date_to):
		return jsonify({"error":"Required parameter is missing or empty"})
	else:
		# check if {origin, destination} are in code or slug format
		origin_is_code = True if origin.isupper() else False
		destination_is_code = True if destination.isupper() else False

		if origin_is_code:
			if destination_is_code: # both are in code format
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_CODE_dest_CODE.sql')
				query_params = {'orig_code': origin, 'dest_code': destination, 'date_from': date_from, 'date_to': date_to}
			else: # origin in code format, destination in slug format
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_CODE_dest_CODE.sql')
				query_params = {'orig_code': origin, 'dest_code': destination, 'date_from': date_from, 'date_to': date_to} # TODO
		else:
			if destination_is_code: # origin in slug format, destination in code format
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_CODE_dest_CODE.sql')
				query_params = {'orig_code': origin, 'dest_code': destination, 'date_from': date_from, 'date_to': date_to} # TODO
			else: # both are in slug format
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_CODE_dest_CODE.sql')
				query_params = {'orig_code': origin, 'dest_code': destination, 'date_from': date_from, 'date_to': date_to} # TODO

		# connect to database and execute query
		conn = connect_database()
		cur = conn.cursor()
		cur.execute(query, query_params)

		result = cur.fetchone() # example result: (Decimal('1154.6666666666666667'),)
		average = '{0:f}'.format(result[0]) # retrieve average from query result

		cur.close() # close database connection
		
		return jsonify({"average":average})

def connect_database():
	config = configparser.ConfigParser()
	config.read("api.properties")

	conn = psycopg2.connect(
		host=config.get("database","host")
		, database=config.get("database","database")
		, user=config.get("database","user")
		, password=config.get("database","password")
		, port=config.get("database","port")
	)
	return conn

def is_null_or_empty(*args):
	for x in args:
		if x is None or x is "":
			return True
	return False

app.run()