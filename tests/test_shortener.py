from url_shortener import url_shortener
import os
import pytest
import tempfile
import json

'''Tests the 3 endpoints of this API'''

@pytest.fixture
def client(request):
	db_fd, url_shortener.app.config['DATABASE'] = tempfile.mkstemp()
	url_shortener.app.config['TESTING'] = True
	client = url_shortener.app.test_client()
	with url_shortener.app.app_context():
		url_shortener.init_db()

	def teardown():
		os.close(db_fd)
		os.unlink(url_shortener.app.config['DATABASE'])
	request.addfinalizer(teardown)

	return client

def test_shorten_url(client):
	rv = client.post('/', 
		data=json.dumps({"url":"https://www.crunchbase.com/"}), 
		content_type='application/json')
	assert '"shortened_url": "http://localhost/b"' in rv.data

def test_redirect(client):
	client.post('/', 
		data=json.dumps({"url":"https://www.crunchbase.com/"}), 
		content_type='application/json')
	rv = client.get('/b')
	assert "https://www.crunchbase.com/" in rv.data

def test_get_statistics(client):
	client.post('/', 
		data=json.dumps({"url":"https://www.crunchbase.com/"}), 
		content_type='application/json')
	rv = client.get('/')
	assert '"desktop_redirects": 0' in rv.data
	client.get('/b')
	rv = client.get('/')
	assert '"desktop_redirects": 1' in rv.data