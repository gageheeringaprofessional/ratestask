import flask
from flask import request, jsonify
import psycopg2 # connect (to Postgres database)
import pkg_resources # resource_string (for retrieving sql queries)
import configparser # (to read properties file for database)
from collections import defaultdict
from datetime import datetime # (for validating user input)

# Reference: https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask#lesson-goals

app = flask.Flask(__name__)
app.config["DEBUG"] = True

map_slug_subslugs = defaultdict(list) # KEY: slug, VALUE: direct subslugs
# E.g., baltic:['finland_main', 'baltic_main', 'poland_main']

map_slug_codes = defaultdict(list) # KEY: slug, VALUE: codes belonging directly to the slug
# E.g., stockholm_area:['SENRK', 'SESOE', 'SEGVX', 'SEOXE', 'SESTO']

@app.before_first_request
def store_slug_hierarchy():
	""" Store each slug's direct subslugs in memory.

	This assumes no new slugs (e.g., united_states) will be added to the
	database outside of the API.

	The full API implementation would update the 'map_slug_subslugs'
	dict when a new slug was encountered.
	"""
	query = 'SELECT slug, parent_slug FROM regions'

	conn = connect_database()
	cursor = conn.cursor()
	cursor.execute(query)
	result = cursor.fetchall()
	cursor.close() # close database connection
	
	for slug, parent_slug in result:
		map_slug_subslugs[parent_slug].append(slug)

@app.before_first_request
def store_slug_ports():
	""" Store each slug's direct ports.

	This assumes no new codes (e.g., GAGEH) will be added to the
	database outside of the API.

	The full API implementation would update the 'map_slug_codes'
	dict when a new port was encountered.
	"""
	query = 'SELECT parent_slug, code FROM ports'

	conn = connect_database()
	cursor = conn.cursor()
	cursor.execute(query)
	result = cursor.fetchall()
	cursor.close() # close database connection
	
	for parent_slug, code in result:
		map_slug_codes[parent_slug].append(code)

@app.route('/api/v1/average', methods=['GET'])
def average():
	""" Return the average daily price of transactions between
	an origin and a destination within a date range.
	If the average is comprised of fewer than 3 days, return null
	for that day.

	Example call:
	http://127.0.0.1:5000/api/v1/average?origin=CNGGZ&destination=EETLL&date_from=2016-01-01&date_to=2016-01-01
	"""
	args = request.args # ensure required arguments are passed

	origin = args.get('origin')
	destination = args.get('destination')
	date_from = args.get('date_from')
	date_to = args.get('date_to')
	
	if is_null_or_empty(origin, destination, date_from, date_to):
		return jsonify({"error":"Required parameter is missing or empty"})
	elif not validate_date(date_from) and validate_date(date_to):
		return jsonify({"error":"Improper date format provided, use YYYY-MM-DD"})
	elif not validate_code_or_slug(origin) and validate_code_or_slug(destination):
		return jsonify({"error":"Non-existent code or slug provided"})
	else:
		query = average_query(origin, destination, date_from, date_to)

		conn = connect_database()
		cursor = conn.cursor()
		cursor.execute(query['query'], query['params'])
		result = cursor.fetchall()
		cursor.close() # close database connection

		ret = []
		for date, decimal in result:
			conversion = {} 
			# datetime.date(2016, 1, 1) becomes 2016-01-01
			conversion['date'] = str(date.strftime('%Y-%m-%d'))
			# Decimal('1154.6666666666666667') becomes 1154
			conversion['average_price'] = None if decimal is None else str(decimal).partition('.')[0]
			ret.append(conversion)

		return jsonify(ret)

def average_query(origin, destination, date_from, date_to):
	""" Return the appropriate average query given whether
	{origin, destination} are in code or slug format.
	"""

	# Read query path from api.settings
	config = configparser.ConfigParser()
	config.read("api.properties")

	orig_format = 'code' if is_code(origin) else 'slug'
	dest_format = 'code' if is_code(destination) else 'slug'

	params = {'origin': origin, 'destination': destination, 'date_from': date_from, 'date_to': date_to}

	if (orig_format, dest_format) == ('code', 'code'):
		query = pkg_resources.resource_string(__name__, config.get("queries","avg_code_code"))

	elif (orig_format, dest_format) == ('code', 'slug'):
		query = pkg_resources.resource_string(__name__, config.get("queries","avg_code_slug"))
		params['destination'] = get_slug_group_ports(destination)

	elif (orig_format, dest_format) == ('slug', 'code'):
		query = pkg_resources.resource_string(__name__, config.get("queries","avg_slug_code"))
		params['origin'] = get_slug_group_ports(origin)

	else:
		query = pkg_resources.resource_string(__name__, config.get("queries","avg_slug_slug"))
		params['origin'] = get_slug_group_ports(origin)
		params['destination'] = get_slug_group_ports(destination)

	return {'query': query, 'params': params}

def get_slug_group_ports(slug):
	""" Return all ports associated with a given slug
	or any of its descendant subslugs.
	"""	
	relevant_slugs = get_slug_group(slug)
	ports = []
	for region in relevant_slugs:
		ports.extend(map_slug_codes[region])

	return tuple(ports)

def get_slug_group(slug):
	""" Return a given slug along with all of its descendant subslugs.
	"""
	group = {slug}
	for subslug in map_slug_subslugs[slug]:
		group.add(subslug)
		group.update(get_slug_group(subslug))

	return group

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

def validate_code_or_slug(target):
	""" Check that the code or slug exists in the database.
	"""
	config = configparser.ConfigParser()
	config.read("api.properties")

	if is_code(target):
		query = pkg_resources.resource_string(__name__, config.get("queries","verify_code"))
	else:
		query = pkg_resources.resource_string(__name__, config.get("queries","verify_slug"))

	conn = connect_database()
	cursor = conn.cursor()
	cursor.execute(query, {'target': target})
	result = cursor.fetchone()
	cursor.close() # close database connection

	return result[0]

def is_code(target):
	""" Return true if the result matches the port code format.
	"""
	return len(target) == 5 and target.isupper()

def validate_date(date_text):
	""" Source: https://stackoverflow.com/a/37045601/16401644
	"""
	try:
		if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
			raise ValueError
		return True
	except ValueError:
		return False

def is_null_or_empty(*args):
	for x in args:
		if x is None or x == "":
			return True
	return False

app.run()