from flask import Flask, request, abort, jsonify, redirect, Response, g
from datetime import datetime
from collections import OrderedDict
import sqlite3
import json
import os

app = Flask(__name__)

app.config.update(dict(
	DATABASE = os.path.join(app.root_path, 'database.db')
))

mapping = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

"""DATABASE SETUP"""

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print 'Initialized the database.'

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(app.config['DATABASE'])
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


"""APPLICATION"""

@app.route("/")
def list_statistics():
	db = get_db()
	rows = db.execute("SELECT * FROM urls")
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
	return Response(json.dumps(output), mimetype='application/json')


@app.route("/", methods=["POST"])
def shorten_url():
    if not request.is_json or not "url" in request.get_json():
    	abort(403)

    parsed = request.get_json()

    url = parsed["url"]
    if url[0:4] != "http":
    	url = "http://" + url

    desktop_url = parsed["desktop_url"] if "desktop_url" in parsed else url
    mobile_url = parsed["mobile_url"] if "mobile_url" in parsed else url
    tablet_url = parsed["tablet_url"] if "tablet_url" in parsed else url

    db = get_db()
    db.execute('''
    	INSERT INTO urls 
    	VALUES (?,0,?,0,?,0,null,?)''', 
    	(desktop_url, mobile_url, tablet_url, datetime.now().replace(microsecond=0)))
    row_id = db.execute("SELECT Count(*) FROM urls").fetchone()[0]
    shortened = to_shortened(row_id)
    db.execute("UPDATE urls SET shortened=? WHERE rowid=?", (shortened, row_id))
    db.commit()

    return jsonify(shortened_url=request.url_root+shortened), 201

@app.route("/<shortened>")
def direct_to_original(shortened):
	db = get_db()
	num_rows = db.execute("SELECT Count(*) FROM urls").fetchone()[0]
	row_id = to_row_id(shortened)
	if row_id > num_rows or row_id == 0:
		abort(404)

	platform = request.user_agent.platform
	if platform == "android" or platform == "iphone":
		device = "mobile"
	elif platform == "ipad":
		device = "tablet"
	else:
		device = "desktop"

	db.execute('''
		UPDATE urls 
		SET ''' + device + "_redirects = " + device + '''_redirects+1 
		WHERE rowid=?''', (row_id,))
	url = db.execute("SELECT " + device + "_url FROM urls WHERE rowid=?", (row_id,)).fetchone()[0]

	db.commit()
	return redirect(url)


"""HELPER FUNCTIONS"""

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
    app.run(threaded=True)