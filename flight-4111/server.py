
# python server.py --debug

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
	python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import logging
from flask import jsonify
from flask import url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
logging.basicConfig(level=logging.DEBUG) 
logger = logging.getLogger(__name__)  


passengerID=0
bookingID=7

currentPassengerID=0

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.148.223.31/proj1part2
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.148.223.31/proj1part2"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "sa4564"
DATABASE_PASSWRD = "521455"
DATABASE_HOST = "34.148.223.31"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)
conn = engine.connect()


#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
# with engine.connect() as conn:
# 	create_table_command = """
# 	CREATE TABLE IF NOT EXISTS test (
# 		id serial,
# 		name text
# 	)
# 	"""
# 	res = conn.execute(text(create_table_command))
# 	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
# 	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	# conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass
#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

@app.route('/login', methods=['POST']) #adding a new route for handling login submissions
def login():
    
    global passengerID, currentPassengerID
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']

    try: 
        with engine.connect() as conn: #check if a passenger already exists
            result = conn.execute(text(""" 
            SELECT passenger_id FROM passenger 
             WHERE email = :email
            """), {"email": email})
                
            passenger = result.fetchone()

            if passenger: # set currentPassengerID if passenger exists
                currentPassengerID = passenger[0]
            else:
                passenger +=1  #insert new record if doesn't exist
                currentPassengerID = passengerID
                conn.execute(text("""
                INSERT INTO passenger (passenger_id, first_name, last_name, email)
                VALUES (:passenger_id, :first_name, :last_name, :email)
                """), {
                "passenger_id": passengerID,
                 "first_name": first_name,
                "last_name": last_name,
                "email": email
                })
                conn.commit()
            return redirect('/homepage')
    except Exception as e:
            print(f"Error during login: {e}")
            return redirect('/?error=login_failed')
                  
@app.route('/')
def login_page():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like

    #
    # example of a database query
    #
    return render_template("index.html")
	
#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT airport.city, airport.name, airport.airport_code FROM airport, route where departure=airport.airport_code"))
        dep_airports = sorted([(row[0], row[1], row[2]) for row in result])
        
        result = conn.execute(text("SELECT DISTINCT airport.city, airport.name, airport.airport_code FROM airport, route where arrival=airport.airport_code"))
        arr_airports = sorted([(row[0], row[1], row[2]) for row in result])
        

    return render_template("homepage.html", deps=dep_airports, arr=arr_airports)

@app.route('/search-flights', methods=['POST'])
def search_flights():
    data = request.get_json()
    from_code = data['from']
    to_code = data['to']
    date = data['date'] 

    
    with engine.connect() as conn:
        query = text("""
            SELECT f.flight_id, f.airline, f.departure_time, f.arrival_time, f.tailnum, r.distance
            FROM flight f
            JOIN route r ON f.route_id = r.route_id
            WHERE r.departure = :from_code
            AND r.arrival = :to_code
            AND CAST(f.departure_time AS DATE) = :date
        """)
        
        result = conn.execute(query, {
            "from_code": from_code,
            "to_code": to_code,
            "date": date
        })
		
        flights = [{
            "flight_id": row[0],
            "airline": row[1],
            "departure_time": str(row[2]),
            "arrival_time": str(row[3]),
            "tailnum": str(row[4]),
            "distance": str(row[5]),
            "dep_airport": from_code,
            "arr_airport": to_code,
        } for row in result]

    return jsonify({"flights": flights})
    
@app.route('/add-booking', methods=['POST'])
def add_booking():
    global bookingID, currentPassengerID
    data = request.get_json()
    flight_id = data['flight_id']

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO booking (BOOKING_ID, FLIGHT_ID, PASSENGER_ID)
            VALUES (:booking_id, :flight_id, :passenger_id)
        """), {
            "booking_id": bookingID,
            "flight_id": flight_id,
            "passenger_id": currentPassengerID
        })
        
    bookingID+=1

    return jsonify({"message": "Booking added!"})

    
@app.route('/logout')
def logout():
	return redirect('/')

@app.route('/delete-booking', methods=['POST'])
def delete_booking():
    booking_id = request.form['booking_id']
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM booking WHERE booking_id = :booking_id"), 
                     {"booking_id": booking_id})
    
    return redirect(url_for('my_bookings'))


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	# g.conn.commit()
	return redirect('/')


@app.route('/my-bookings', methods=['GET', 'POST'])
def my_bookings():
    global currentPassengerID

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT first_name, last_name, email 
            FROM passenger 
            WHERE passenger_id = :currentPassengerID
        """), {
            "currentPassengerID": currentPassengerID
        })

        passengerDetails = [{
            "first_name": row[0],
            "last_name": row[1],
            "email": str(row[2])
        } for row in result]
        
       
        result = conn.execute(text("""
        SELECT 
            b.flight_id, 
            b.booking_id, 
            f.departure_time, 
            f.arrival_time, 
            f.airline, 
            f.tailnum, 
            r.distance, 
            r.departure AS dep_airport_code, 
            dep_airport.name AS dep_airport_name,
            dep_airport.city AS dep_airport_city,
            r.arrival AS arr_airport_code, 
            arr_airport.name AS arr_airport_name,
            arr_airport.city AS arr_airport_city
        FROM passenger p
        JOIN booking b ON p.passenger_id = b.passenger_id
        JOIN flight f ON b.flight_id = f.flight_id
        JOIN route r ON f.route_id = r.route_id
        JOIN airport dep_airport ON r.departure = dep_airport.airport_code
        JOIN airport arr_airport ON r.arrival = arr_airport.airport_code
        WHERE p.passenger_id = :currentPassengerID;

        """), {
            "currentPassengerID": currentPassengerID
        }) 
        
        bookings = [{
        "flight_id": str(row[0]),
        "booking_id": str(row[1]),
        "departure_time": str(row[2]),
        "arrival_time": str(row[3]),
        "airline": str(row[4]),
        "tailnum": str(row[5]),
        "distance": str(row[6]),
        "dep_airport_code": str(row[7]),
        "dep_airport_name": str(row[8]),
        "dep_airport_city": str(row[9]),
        "arr_airport_code": str(row[10]),
        "arr_airport_name": str(row[11]),
        "arr_airport_city": str(row[12])
        } for row in result]

    return render_template("my-bookings.html", passenger=passengerDetails, bookings=bookings)

if __name__ == "__main__":
	import click
	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
