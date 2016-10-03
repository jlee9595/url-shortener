# url-shortener

Basic URL shortening application that tracks basic statistics such as device, times redirected, and time since creation

###Prerequisites
- Python 2
- Pip

###To run locally
1. Clone repository
2. `cd url-shortener`
3. Create virtual environment (optional)
4. `pip install --editable .`
5. `export FLASK_APP=url_shortener`
6. `flask initdb`
7. `flask run`
8. To test: `python setup.py test`

To shorten a url, try something like this:
`curl -d '{"url": "reddit.com/r/jokes"}' -H 'Content-Type: application/json' http://127.0.0.1:5000/`

To get statistics, try something like this:
`curl http://127.0.0.1:5000/`

###Supported operations
####Shorten URL
Path: /

Method: POST

Parameters:
- url - url to be shortened
- desktop_url (optional) - specific url to direct to if device being redirected is a desktop
- mobile_url (optional) - specific url to direct to if device being redirected is a mobile device
- tablet_url (optional) - specific url to direct to if device being redirected is a tablet

Sample output:

`{
  "shortened_url": "http://shorturl.com/a1bC"
}`

####Get Statistics
Path: /

Method: GET

Parameters: None

Sample output:

`[{"shortened_url": "http://shorturl.com/a1bC", 
"time_since_created": "0:26:47", 
"desktop_url": "http://reddit.com/r/jokes", 
"desktop_redirects": 1, 
"mobile_url": "http://reddit.com/r/jokes", 
"mobile_redirects": 0, 
"tablet_url": "http://reddit.com/r/jokes", 
"tablet_redirects": 0}]`
