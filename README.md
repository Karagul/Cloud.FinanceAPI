# Cloud.FinanceAPI
 

API Documentation
-----------------

REST = Representational State Transfer 


Authorisation: Requires authentication for resource access

- GET **/**
	
	Returns Historical Pricing 
	Requires authentication for resource access.
    The body must contain a JSON object that defines `username` and `password` fields.<br>
    On success a status code 200 is returned. The body of the response contains a JSON object with the newly added user.
    On failure status code 400 (bad request) is returned.
    Required parameters:
    - *num*: # of stocks requested from FXCM API
    - *from*: timestamp from which to get data
    - *to*: timestamp to which to get data

    Example of a `curl` request using *username/password* authentication:

    $ curl -u nasra:qmul -i -X GET http://localhost:8080/?num=10from=1494086400&to=1503835200

- POST **/subscribe**

	Post subscribe to Data Streaming 
	Requires authentication for resource access
	Data will be inputed in pairs e.g. EURO/POUND    
    On success a status code 200 is returned. The body of the response contains a JSON object with the requested user.
    On failure status code 400 (bad request) is returned.
    Required parameters:
    - *pairs*: currency pair to exchange from and to

    Example of a `curl` request using *username/password* authentication:

    $ curl -u nasra:qmul -i -H "Content-Type: application/json" -X POST -d '{"pairs":"EUR/USD"}' http://localhost:8080/subscribe

- GET **/users**

	Get users by name 
	Require authentication for resource access based on username and password
    Return an authentication token.
    Executes CQL query on cassandra through established session, allows to get all the users with matching name. 
    Append to the created list, each user's name and age.
    If no name matches then return json object with 'error' and 'username not found' with status code 404 (Not found)
    On success a JSON object is returned with 'success' and code 200 (Success)
    Required parameters:
    - *name*: name of the user account

    Example of a `curl` request using *username/password* authentication:

    $ curl -u nasra:qmul -i -X GET http://localhost:8080/users?name=XYZ

- DELETE **/users/<str:name>**

	Delete users BY name
    Iterates all obtained result names, will delete all user records with matching name.
    This request must be authenticated using a auth.login_required Basic Authentication header.
    On success a JSON object is returned with 'success' and 'User data deleted' however if no users found, returns error response to user as json object 'error' and 'Username not found' with code 404 (not found).
    Required parameters:
    - *name*: name of user account

    Example of a `curl` request using *username/password* authentication:

    $ curl -u nasra:qmul -i -X DELETE http://localhost:8080/users/XYZ

- PUT **/users/<str:name>**

	PUT (UPDATING) user's passwords, this method will iterate all recieved records and updates user passwords with matching names. 
	This request must be authenticated using a auth.login_required Basic Authentication header. 
	Required parameters:
	- *password*: new password for user account

    Example of a `curl` request using *username/password* authentication:

    $ curl -u nasra:qmul -i -X PUT -H "Content-Type: application/json" -d '{"password":"queenmary"}' http://localhost:8080/users/nasra

- POST **/users/<str:name>**

	This method allows user to create a new user record with given parameters. 
	- *name*: name of new user account 
	- *password*: password for new user account
	- *age*: age of the user
	A success response is returned to user as a json object with 'success' and 'New user created'. A hash function is any function that can be used to map data of arbitrary size onto data of a fixed size. The values returned by a hash function are called hash values. In this section a hash function has been utilised to assign a unique ID to user's passwords so that they are safe over the network and in the database, this is done to increase the security of the application. 

    Example of a `curl` request using *username/password* authentication:

    $ curl -i -X POST -H "Content-Type: application/json" -d '{"password":"qmul","age":20}' http://localhost:8080/users/nasra

- Verify Authorisation token 

	Here the token of a user is used as a 'SECRET_KEY', the token's signature will be checked whether it is a valid token and whether it has expired. If the token is an invalid token it will be return None. If the token is valid, the first user data with matching name is collected from database. Once the token expires it cannot be used anymore and the client needs to request a new one. 

	In this implementation it is possible to use an unexpired token as authentication to request a new token when the expiration data is close to end. This allows the client to change from one token to the next and never need to send username and password after the initial token is obtained.

