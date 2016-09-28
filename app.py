from flask import Flask, request, abort, jsonify, redirect, Response
from datetime import datetime
from collections import OrderedDict
import sqlite3
import json

app = Flask(__name__)

mapping = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS urls (
	desktop_url text, 
	desktop_redirects int, 
	mobile_url text, 
	mobile_redirects int, 
	tablet_url text, 
	tablet_redirects int, 
	shortened text, 
	created text)''')
conn.commit()
conn.close()

@app.route("/")
def list_statistics():
	conn = sqlite3.connect('database.db')
	c = conn.cursor()
	rows = c.execute("SELECT * FROM urls")
	output = []
	for row in rows:
		output.append(OrderedDict([
			("shortened_url", request.url_root + row[6]), 
			("time_since_created", get_time_elapsed(row[7])), 
			("desktop_url", row[0]), 
			("desktop_redirects", row[1]), 
			("mobile_url", row[2]), 
			("mobile_redirects", row[3]), 
			("tablet_url", row[4]), 
			("tablet_redirects", row[5])]))

	conn.close()
	return Response(json.dumps(output), mimetype='application/json')


@app.route("/", methods=["POST"])
def shorten_url():
    parsed = request.get_json()
    if not "url" in parsed:
    	abort(403)

    url = parsed["url"]
    if url[0:4] != "http":
    	url = "http://" + url
    desktop_url = parsed["desktop_url"] if "desktop_url" in parsed else url
    mobile_url = parsed["mobile_url"] if "mobile_url" in parsed else url
    tablet_url = parsed["tablet_url"] if "tablet_url" in parsed else url

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
    	INSERT INTO urls 
    	VALUES (?,0,?,0,?,0,null,?)''', 
    	(desktop_url, mobile_url, tablet_url, datetime.now().replace(microsecond=0)))

    row_id = c.lastrowid
    shortened = to_shortened(row_id)
    c.execute("UPDATE urls SET shortened=? WHERE rowid=?", (shortened, row_id))
    conn.commit()
    conn.close()

    return jsonify(shortened_url=request.url_root+shortened), 201

@app.route("/<shortened>")
def direct_to_original(shortened):
	conn = sqlite3.connect('database.db')
	c = conn.cursor()
	c.execute("SELECT Count(*) FROM urls")
	num_rows = c.fetchone()[0]

	row_id = to_row_id(shortened)
	if row_id > num_rows or row_id == 0:
		conn.close()
		abort(404)

	platform = request.user_agent.platform
	if platform == "android" or platform == "iphone":
		c.execute('''
			UPDATE urls 
			SET mobile_redirects = mobile_redirects+1 
			WHERE rowid=?''', (row_id,))
		c.execute("SELECT mobile_url FROM urls WHERE rowid=?", (row_id,))
	elif platform == "ipad":
		c.execute('''
			UPDATE urls 
			SET tablet_redirects = tablet_redirects+1 
			WHERE rowid=?''', (row_id,))
		c.execute("SELECT tablet_url FROM urls WHERE rowid=?", (row_id,))
	else:
		c.execute('''
			UPDATE urls 
			SET desktop_redirects = desktop_redirects+1 
			WHERE rowid=?''', (row_id,))
		c.execute("SELECT desktop_url FROM urls WHERE rowid=?", (row_id,))

	url=c.fetchone()[0]
	conn.commit()
	conn.close()

	return redirect(url)

def to_row_id(shortened):
	unmapped = []
	for char in shortened:
		unmapped.append(mapping.index(char))
	return to_base_10(62, unmapped)

def to_shortened(row_id):
	shortened = ""
	for digit in to_base(62, row_id):
		shortened += mapping[digit]
	return shortened

#convert from base 10 to a specified base
def to_base(base, num):
	converted = []
	current = num
	while current > 0:
		converted.append(current%base)
		current = current/base
	converted.reverse()
	return converted

def to_base_10(base, num):
	num.reverse()
	converted = 0
	i=0
	for digit in num:
		converted += digit * base**i
		i+=1
	return converted

def get_time_elapsed(time):
	now = datetime.now().replace(microsecond=0)
	return str(now - datetime.strptime(time, "%Y-%m-%d %H:%M:%S") )

if __name__ == "__main__":
    app.run()