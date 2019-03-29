# using flask container framework
# from flask import Flask, Response
from flask import Flask, jsonify
# for handling http requests
import requests
# for communication with external trading api
from socketIO_client import SocketIO
# for communication with cassandra cluster
from cassandra.cluster import Cluster
# for password hashing and passowrd hash verification
from passlib.apps import custom_app_context as pwd_context
# for token based authentication
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
# for password based authentication
from flask_httpauth import HTTPBasicAuth
# for use in resource access authentication
auth = HTTPBasicAuth()
# set to communicate with cassandra cluster named 'cassandra'
cluster = Cluster(['cassandra'])
# establish connection to cassandra cluster
session = cluster.connect()
# for handling routes via flask
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
#load configuration from file
app.config.from_pyfile('config.py')


# the url of the external trading api
TRADING_API_URL = app.config['TRADING_API_URL']
# the port number of the external trading api
WEBSOCKET_PORT = app.config['WEBSOCKET_PORT']
# client access token for the external trading api
ACCESS_TOKEN = app.config['ACCESS_TOKEN']

# function to execute when establish socket connection to external trading api
def on_connect():
	print('Websocket Connected: ' + socketIO._engineIO_session.id)

# function to execute when terminate socket connection to external trading api
def on_close():
	print('Websocket Closed.')

# the socket library function for external trading api communication
socketIO = SocketIO(TRADING_API_URL, WEBSOCKET_PORT, params = {'access_token': ACCESS_TOKEN})
# set function to call on connection establish
socketIO.on('connect', on_connect)
# set function to call on connection terminate
socketIO.on('disconnect', on_close)

# the access token to be used when requesting resources from the external trading api
bearer_access_token = "Bearer " + socketIO._engineIO_session.id + ACCESS_TOKEN

# GET Historical Pricing
# curl -u nasra:qmul -i -X GET http://localhost:8080/?num=10from=1494086400&to=1503835200
@app.route('/',methods=['GET'])
# require authentication for resource access
@auth.login_required
def index():
	# store request arguments as variable
	num = request.args['num']
	v_from = request.args['from']
	to = request.args['to']
	# resource path for the external trading api
	method = '/candles/1/H1'
	# send GET http request to external trading api with access token and required parameters
	hist_response = requests.get(TRADING_API_URL + method,
					headers = {
						'User-Agent': 'request',
						'Authorization': bearer_access_token,
						'Accept': 'application/json',
						'Content-Type': 'application/x-www-form-urlencoded'
					},
					params = {
						# 'num': 10,
						'num': num,
						# 'from': 1494086400,
						'from': v_from,
						# 'to': 1503835200
						'to': to
					})
	# if request successful
	if hist_response.status_code == 200:
		# return success response as json to user
		return jsonify({'success':hist_response.json()}), 200
		# return str(hist_response.json())
	else:
		# return error reponse as json to user
		# return jsonify({'error':hist_response}), ???
		return jsonify({'error':'FAILED'})

# POST Subscribe to Data Streaming
# curl -u nasra:qmul -i -H "Content-Type: application/json" -X POST -d '{"pairs":"EUR/USD"}' http://localhost:8080/subscribe
@app.route('/subscribe',methods=['POST'])
# require authentication for resource access
@auth.login_required
def subscribe():
	# store request argument as variable
	pairs = request.json.get('pairs')
	# resource path for the external trading api
	method = '/subscribe'

	# streaming
	# def generate():
	# 	sub_response = requests.post(TRADING_API_URL + method,
	# 					headers = {
	# 						'User-Agent': 'request',
	# 						'Authorization': bearer_access_token,
	# 						'Accept': 'applcation/json',
	# 						'Content-Type': 'application/x-www-form-urlencoded'
	# 					},
	# 					data = {
	# 						'pairs': 'EUR/USD'
	# 					})
	# 	yield str(sub_response.json())
	# return Response(generate(), content_type='application/json')

	# send POST http request to external trading api with access token and required parameters
	sub_response = requests.post(TRADING_API_URL + method,
					headers = {
						'User-Agent': 'request',
						'Authorization': bearer_access_token,
						'Accept': 'applcation/json',
						'Content-Type': 'application/x-www-form-urlencoded'
					},
					data = {
						'pairs': pairs
					})
	# if request successful
	if sub_response.status_code == 200:
		# return success response as json to user
		return jsonify({'success':sub_response.json()}), 200
		# return str(sub_response.json())
	else:
		# return error reponse as json to user
		# return jsonify({'error':sub_response}), ???
		return jsonify({'error':sub_response})

# GET users BY name
# curl -u nasra:qmul -i -X GET http://localhost:8080/users?name=XYZ
@app.route('/users',methods=['GET'])
# require authentication for resource access
@auth.login_required
# def users_get(name):
def get_users():
	# store request argument as variable
	name = request.args['name']
	# execute cql query on cassandra through established session
	# get all users with matching name
	rows = session.execute("Select * From users Where name = '{}'".format(name))
	# declare empty list
	users = {}
	# iterate all obtained results
	for user in rows:
		# append to the created list, each user's name and age
		# users.append('{}, {}'.format(name, user.age))
		users.append('{}, {}'.format(name, user['age']))
	# if list empty, that is received no results from cassandra database
	if len(users) == 0:
		# return error response to user as json
		return jsonify({'error':'Username not found'}), 404
	# return success response to user as json
	return jsonify({'success':users})

# DELETE users BY name
# curl -u nasra:qmul -i -X DELETE http://localhost:8080/users/XYZ
# curl -u ujdjmbujy7tgjgjsgdc8:x -i -X DELETE http://localhost:8080/users/XYZ
@app.route('/users/<str:name>',methods=['DELETE'])
# require authentication for resource access
@auth.login_required
def delete_users(name):
	# execute cql query on cassandra through established session
	# get all users with matching name
	rows = session.execute("Select * From users Where name = '{}'".format(name))
	# iterate all obtained results
	for user in rows:
		# delete all user records with matching name
		session.execute("Delete From users Where name = '{}'".format(name))
		# return success response to user
		return jsonify({'success':'User data deleted'})
	# if no users found, return error response to user
	return jsonify({'error':'Username not found'}), 404

# PUT (UPDATING) users
# curl -u nasra:qmul -i -X PUT -H "Content-Type: application/json" -d '{"password":"queenmary"}' http://localhost:8080/users/nasra
@app.route('/users/<str:name>',methods=['PUT'])
# require authentication for resource
@auth.login_required
def update_users(name):
	# store request argument as variable
	password = request.json.get('password')
	# get all users from database with matching name
	rows = session.execute("Select * From users Where name = '{}'".format(name))
	# iterate all recieved records
	for user in rows:
		# update user passwords with matching name
		session.execute("Update users Set password = '{}' Where name = '{}'".format(hash_password(password), name))
		# return success response to user
		return jsonify({'success':'User password updated'})
	# return error response to user
	return jsonify({'error':'Username not found'}), 404

# POST user
# curl -i -X POST -H "Content-Type: application/json" -d '{"password":"qmul","age":20}' http://localhost:8080/users/nasra
@app.route('/users/<str:name>',methods=['POST'])
def create_users(name):
	# store request arguments as variable
	password = request.json.get('password')
	age = request.json.get('age')
	# create new user record with given parameters
	session.execute("Insert Into users (name, password, age) Values ('{}', '{}', '{}')".format(name, hash_password(password), age))
	# return success response to user
	return jsonify({'success':'New user created'})
+
# returns hash for given user password
def hash_password(password):
	# return encrypted password
	return pwd_context.encrypt(password)

# verify given password by comparing against a given hash
def verify_password_hash(password, password_hash):
	# return true if hashes match, else false
	return pwd_context.verify(password, password_hash)

# generate a new token for given user name
def generate_auth_token(name, expiration = 600):
	#
	s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
	#
	return s.dumps({ 'name': name })

# verify given token
# static because ???
#
@staticmethod
def verify_auth_token(token):
	#
	s = Serializer(app.config['SECRET_KEY'])
	try:
		#
		data = s.loads(token)
	except SignatureExpired:
		# valid token, but expired
		return None
	except BadSignature:
		# invalid token
		return None
	# get first user data with matching name
	user = session.execute("Select * From users Where name = '{}' Limit 1".format(data['name']))
	# return retrieved data to calling method
	return user

# authentication with token, or name and password
@auth.verify_password
def verify_password(username_or_token, password):
    # try authenticating with token
    user = verify_auth_token(username_or_token)
    # if token failed to authenticate
    if not user:
    	# try authenticating with name and password
    	# get first user data with matching name
    	user = session.execute("Select * From users Where name = '{}' Limit 1".format(username_or_token))
    	# if no user found or password hash did not match
    	if not user or not verify_password_hash(password, user['password_hash']):
        	# failed to authenticate with both token, and name/password
        	return False
	# set global access variable to retrieved user data
    g.user = user
    # user verified
    return True

#
if __name__ == '__main__':
	#
	app.run(host='0.0.0.0',port=8080)
