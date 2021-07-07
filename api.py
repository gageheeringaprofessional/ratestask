import flask
from flask import request, jsonify
import psycopg2 # connect (to Postgres database)
import pkg_resources # resource_string (for retrieving sql queries)
import configparser # (to read properties file for database host, etc.)
from collections import defaultdict

# Reference: https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask#lesson-goals

app = flask.Flask(__name__)
app.config["DEBUG"] = True

dict_slug_subslugs = defaultdict(list) # key: slug, value: immediate subslugs

@app.before_first_request
def store_slug_hierarchy():
	""" Store each slug's immediate subslugs in memory.
	"""
	query = 'SELECT slug, parent_slug FROM regions'

	conn = connect_database()
	cursor = conn.cursor()
	cursor.execute(query)
	result = cursor.fetchall()
	cursor.close() # close database connection
	
	for slug, parent_slug in result:
		dict_slug_subslugs[parent_slug].append(slug)

# E.g., http://127.0.0.1:5000/api/v1/average?origin=CNGGZ&destination=EETLL&date_from=2016-01-01&date_to=2016-01-01
@app.route('/api/v1/average', methods=['GET'])
def average():
	""" Return average of transactions given required arguments:
	origin, destination, date_from, date_to
	"""
	args = request.args # ensure required arguments are passed

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

		query_params = {'origin': origin, 'destination': destination, 'date_from': date_from, 'date_to': date_to}

		if origin_is_code:
			if destination_is_code: # both are in code format
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_CODE_dest_CODE.sql')
			else: # origin in code format, destination in slug format
				dest_subslugs = get_subslug_subset(destination)
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_CODE_dest_SLUG.sql')
				query_params['dest_subslugs'] = tuple(dest_subslugs)
		else:
			if destination_is_code: # origin in slug format, destination in code format
				orig_subslugs = get_subslug_subset(origin)
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_SLUG_dest_CODE.sql')
				query_params['orig_subslugs'] = tuple(orig_subslugs)
			else: # both are in slug format
				orig_subslugs = get_subslug_subset(origin)
				dest_subslugs = get_subslug_subset(destination)
				query = pkg_resources.resource_string(__name__, 'queries/get_average_orig_SLUG_dest_SLUG.sql')
				query_params['orig_subslugs'] = tuple(orig_subslugs)
				query_params['dest_subslugs'] = tuple(dest_subslugs)

		conn = connect_database()
		cursor = conn.cursor()
		cursor.execute(query, query_params)

		result = cursor.fetchall()
		
		cursor.close() # close database connection

		ret = []
		for date, decimal in result:
			conversion = {}
			conversion['date'] = str(date.strftime('%Y-%m-%d')) # datetime.date(2016, 1, 1) becomes 2016-01-01
			conversion['average_price'] = str(decimal) # Decimal('1154.6666666666666667') becomes 1154.6666666666666667
			ret.append(conversion)

		return jsonify(ret)

def get_subslug_subset(slug):
	""" Return a given slug along with all of its descendant subslugs.
	"""
	subslugs = {slug}
	for subslug in dict_slug_subslugs[slug]:
		subslugs.add(subslug)
		subslugs.update(get_subslug_subset(subslug))
	return subslugs

def connect_database():
	""" Connect to Postgres database given settings in api.properties.
	"""
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