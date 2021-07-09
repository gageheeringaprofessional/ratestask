import flask
from flask import request, jsonify

import psycopg2 # connect (to Postgres database)

from pkg_resources import resource_string # (for retrieving sql queries)
import configparser # (to read properties file)

from collections import defaultdict
from datetime import datetime # (for validating user input)


app = flask.Flask(__name__)
app.config['DEBUG'] = True

PROPERTIES_FILE = 'api.properties'

cache_direct_subslugs = defaultdict(list) # KEY: slug, VALUE: direct subslugs
# E.g., baltic:['finland_main', 'baltic_main', 'poland_main']

cache_port_codes = defaultdict(list) # KEY: slug, VALUE: direct port codes
# E.g., stockholm_area:['SENRK', 'SESOE', 'SEGVX', 'SEOXE', 'SESTO']


@app.before_first_request
def update_cache_direct_subslugs():
    """ Store each slug's direct subslugs in memory.
    This is used to avoid redundant querying.

    The full API implementation would update the cache upon encountering
    a new slug.
    """
    query = 'SELECT slug, parent_slug FROM regions'

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close() # Close database connection
    
    for slug, parent_slug in result:
        cache_direct_subslugs[parent_slug].append(slug)

@app.before_first_request
def update_cache_port_codes():
    """ Store each slug's direct ports in memory.
    This is used to avoid redundant querying.

    The full API implementation would update the cache upon encountering
    a new port code.
    """
    query = 'SELECT parent_slug, code FROM ports'

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close() # Close database connection
    
    for parent_slug, code in result:
        cache_port_codes[parent_slug].append(code)

@app.route('/api/v1/average', methods=['GET'])
def average():
    """ Return the average daily price of transactions between an origin and
    destination within a date range.
    
    If the average is comprised of fewer than 3 days, return null for that day.
    """
    args = request.args # ensure required arguments are passed

    origin = args.get('origin')
    destination = args.get('destination')
    date_from = args.get('date_from')
    date_to = args.get('date_to')
    
    if is_null_or_empty(origin, destination, date_from, date_to):
        return jsonify( {'error': 'Required parameter is missing or empty'} ), 400

    elif not is_valid_date(date_from) or not is_valid_date(date_to):
        return jsonify( {'error': 'Improper date format provided, use YYYY-MM-DD'} ), 400

    elif not is_valid_code_or_slug(origin) or not is_valid_code_or_slug(destination):
        return jsonify( {'error': 'Non-existent code or slug provided'} ) # still valid input

    else:
        query_and_params = average_query(origin, destination, date_from, date_to)

        conn = connect_database()
        cursor = conn.cursor()
        cursor.execute(query_and_params['query'], query_and_params['params'])
        result = cursor.fetchall()
        cursor.close() # Close database connection

        ret = [
            {
                'date': str(date.strftime('%Y-%m-%d'))
                # datetime.date(2016, 1, 1) becomes 2016-01-01
                , 'average_price': None if decimal is None else str(decimal).partition('.')[0]
                # Decimal('1154.6666666666666667') becomes 1154
            }
            for date, decimal in result
        ]

        return jsonify(ret)

def average_query(origin, destination, date_from, date_to):
    """ Return the appropriate average query given whether
    {origin, destination} are in code or slug format.
    """

    # Read query path from api.settings
    config = configparser.ConfigParser()
    config.read(PROPERTIES_FILE)

    # Place = or IN symbol in query depending on origin and destination formats
    raw_query = resource_string(__name__, config.get('queries', 'get_average'))

    query_string = raw_query.decode('utf-8') # Convert bytes to string
    query_string = query_string.replace('{orig_in_or_equals}', '=' if is_code(origin) else 'IN')
    query_string = query_string.replace('{dest_in_or_equals}', '=' if is_code(destination) else 'IN')

    query = str.encode(query_string) # Convert back to bytes
    params = {'origin': origin, 'destination': destination, 'date_from': date_from, 'date_to': date_to}

    if is_code(origin) and is_slug(destination):
        params['destination'] = get_ports_of_slug_and_descendants(destination)

    elif is_slug(origin) and is_code(destination):
        params['origin'] = get_ports_of_slug_and_descendants(origin)

    elif is_slug(origin) and is_slug(destination):
        params['origin'] = get_ports_of_slug_and_descendants(origin)
        params['destination'] = get_ports_of_slug_and_descendants(destination)

    return {'query': query, 'params': params}

def get_ports_of_slug_and_descendants(slug):
    """ Return all ports associated with a given slug or any of its
    descendant subslugs.
    """    
    slug_and_descendants = get_slug_and_descendants(slug)
    ports = []
    for region in slug_and_descendants:
        ports.extend(cache_port_codes[region])

    return tuple(ports)

def get_slug_and_descendants(slug):
    """ Return a given slug along with all of its descendant subslugs.
    """
    group = {slug}
    for subslug in cache_direct_subslugs[slug]:
        group.add(subslug)
        group.update(get_slug_and_descendants(subslug))

    return group

def connect_database():
    config = configparser.ConfigParser()
    config.read(PROPERTIES_FILE)

    conn = psycopg2.connect(
        host=config.get('database', 'host')
        , database=config.get('database', 'database')
        , user=config.get('database', 'user')
        , password=config.get('database', 'password')
        , port=config.get('database', 'port')
    )
    return conn

def is_valid_code_or_slug(location):
    """ Check that the code or slug exists in the database.
    """
    config = configparser.ConfigParser()
    config.read(PROPERTIES_FILE)

    if is_code(location):
        query = resource_string(__name__, config.get('queries', 'verify_code'))
    else:
        query = resource_string(__name__, config.get('queries', 'verify_slug'))

    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute(query, {'location': location})
    result = cursor.fetchone()
    cursor.close() # Close database connection

    return result[0] # True or False

def is_code(location):
    return len(location) == 5 and location.isupper()

def is_slug(location):
    return not is_code(location)

def is_valid_date(date_text):
    """ Source: https://stackoverflow.com/a/37045601/16401644
    """
    try:
        if date_text != datetime.strptime(date_text, '%Y-%m-%d').strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False

def is_null_or_empty(*args):
    for x in args:
        if x is None or x == '':
            return True
    return False

if __name__ == "__main__":
    app.run()