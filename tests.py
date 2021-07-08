import requests

url = 'http://127.0.0.1:5000/api/v1/average'
params = '?origin={}&destination={}&date_from={}&date_to={}'

# TODO: Check all below by hand

################################################################################
#
# (origin, destination) = (code, code)
#
################################################################################

def test_CNGGZ_to_EETLL():
	request = url + params.format('CNGGZ', 'EETLL', '2016-01-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	average = int(body[0]['average_price']) # average price between origin and destination on 2016-01-01
	assert average == 1154

	average = int(body[14]['average_price']) # average price between origin and destination on 2016-01-15
	assert average == 1155

	average = int(body[23]['average_price']) # average price between origin and destination on 2016-01-24
	assert average == 1154

	average = int(body[30]['average_price']) # average price between origin and destination on 2016-01-31
	assert average == 1154

def test_CNGGZ_to_EETLL_invalid_date_range():
	request = url + params.format('CNGGZ', 'EETLL', '2016-02-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	assert len(body) == 0 # no transactions expected

def test_CNGGZ_to_EETLL_invalid_date_format():
	request = url + params.format('CNGGZ', 'EETLL', '2016-001', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	assert body['error'] == 'Improper date format provided, use YYYY-MM-DD'

def test_CNGGZ_to_EETLL_param_missing():
	request = url + '?origin={}&destination={}'.format('CNGGZ', 'EETLL')
	response = requests.get(request)
	body = response.json()

	assert body['error'] == 'Required parameter is missing or empty'

################################################################################
#
# (origin, destination) = (code, slug)
#
################################################################################

def test_CNCWN_to_baltic():
	request = url + params.format('CNCWN', 'baltic', '2016-01-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	average = int(body[0]['average_price'])  # average price between origin and destination on 2016-01-01
	assert average == 1195

	average = int(body[14]['average_price']) # average price between origin and destination on 2016-01-15
	assert average == 1214

	average = int(body[23]['average_price']) # average price between origin and destination on 2016-01-24
	assert average == 1160

	average = int(body[30]['average_price']) # average price between origin and destination on 2016-01-31
	assert average == 1093

def test_CNQIN_to_scandinavia():
	request = url + params.format('CNQIN', 'scandinavia', '2016-01-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	average = int(body[2]['average_price']) # average price between origin and destination on 2016-01-03
	assert average == 1723


################################################################################
#
# (origin, destination) = (slug, code)
#
################################################################################

def test_china_east_main_to_CNGGZ():
	request = url + params.format('china_east_main', 'CNGGZ', '2016-01-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	assert len(body) == 0 # no transactions expected

def test_china_east_main_to_CNGGZ_param_missing():
	request = url + '?origin={}&destination={}&date_from={}'.format('china_east_main', 'CNGGZ', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	assert body['error'] == 'Required parameter is missing or empty'

################################################################################
#
# (origin, destination) = (slug, slug)
#
################################################################################

def test_china_main_to_baltic():
	request = url + params.format('china_main', 'baltic', '2016-01-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	average = int(body[0]['average_price'])  # average price between origin and destination on 2016-01-01
	assert average == 1380

	average = int(body[30]['average_price']) # average price between origin and destination on 2016-01-31
	assert average == 1164

def test_uk_sub_to_uk_sub():
	request = url + params.format('uk_sub', 'uk_sub', '2016-01-01', '2016-01-31')
	response = requests.get(request)
	body = response.json()

	assert len(body) == 0 # no transactions expected

