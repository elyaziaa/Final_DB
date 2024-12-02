from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib  # for MD5 hashing suggested in part 3
from datetime import datetime, timedelta

app = Flask(__name__)
conn = pymysql.connect(host='127.0.0.1',
                       user='root',
                       password='root',
                       port=8889,
                       db='airplane',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def hello():
    return render_template('index.html')

# below we use roles because we want to differentiate between when the customer is using the app and when the airline staff uses the app
@app.route('/login')
def login():
    role = request.args.get('role')
    if role == 'customer':  # if the role is equal to customer then we will render the customer_login.html page
        return render_template('customer_login.html')  # rendering this file from the templates page
    elif role == 'staff':  # if the role is equal to staff then we will render the staff_login.html page
        return render_template('staff_login.html')  # rendering this file from the templates page
    else:  # if there is no role, go to the homepage
        return redirect(url_for('hello'))

@app.route('/register')
def register():
    role = request.args.get('role')
    if role == 'customer':  # if the role is equal to customer then we will render the customer_register.html page
        return render_template('customer_register.html')  # rendering this file from the templates page
    elif role == 'staff':  # if the role is equal to staff then we will render the staff_register.html page
        return render_template('staff_register.html')  # rendering this file from the templates page
    else:
        return redirect(url_for('hello'))  # if there is no role, go to the homepage

@app.route('/customer_loginAuth', methods=['POST'])
def customer_loginAuth():
    email = request.form['email']
    password = request.form['password']
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM Customer WHERE Email = %s and Passcode = %s'
    cursor.execute(query, (email, hashed_password))
    data = cursor.fetchone()
    cursor.close()
    
    if data:
        session['email'] = email
        session['role'] = 'customer'
        session['first_name'] = data['First_Name']  # Store first name in the session
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or password'
        return render_template('customer_login.html', error=error)


@app.route('/customer_registerAuth', methods=['POST'])
def customer_registerAuth():
    # Get form data
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    building_num = request.form['building_num']
    street_name = request.form['street_name']
    apartment_num = request.form.get('apartment_num', None)
    city = request.form['city']
    state = request.form['state']
    zip_code = request.form['zip_code']
    date_of_birth = request.form['date_of_birth']

    # Hash the password
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    cursor = conn.cursor()

    # Check if the email already exists
    query = 'SELECT * FROM Customer WHERE Email = %s'
    cursor.execute(query, (email,))
    data = cursor.fetchone()

    if data:
        cursor.close()
        error = "This email is already registered."
        return render_template('customer_register.html', error=error)

    # Insert the new customer into the database
    insert_query = '''
        INSERT INTO Customer (Email, First_Name, Last_Name, Passcode, Building_Num, 
                              Street_Name, Apartment_Num, City, State, Zip_Code, Date_of_Birth)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(insert_query, (
        email, first_name, last_name, hashed_password, building_num, 
        street_name, apartment_num, city, state, zip_code, date_of_birth
    ))
    conn.commit()
    cursor.close()

    # Redirect to the login page after successful registration
    return redirect(url_for('login', role='customer'))


@app.route('/staff_registerAuth', methods=['POST'])
def staff_registerAuth():
    # Get form data
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    date_of_birth = request.form['date_of_birth']

    # Hash the password
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    cursor = conn.cursor()

    # Check if the username already exists
    query = 'SELECT * FROM Airline_Staff WHERE Username = %s'
    cursor.execute(query, (username,))
    data = cursor.fetchone()

    if data:
        cursor.close()
        error = "This username is already registered."
        return render_template('staff_register.html', error=error)

    # Insert the new staff member into the database
    insert_query = '''
        INSERT INTO Airline_Staff (Username, First_Name, Last_Name, Passcode, Date_of_Birth)
        VALUES (%s, %s, %s, %s, %s)
    '''
    cursor.execute(insert_query, (username, first_name, last_name, hashed_password, date_of_birth))
    conn.commit()
    cursor.close()

    # Redirect to the login page after successful registration
    return redirect(url_for('login', role='staff'))



@app.route('/staff_loginAuth', methods=['POST'])
def staff_loginAuth():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM Airline_Staff WHERE Username = %s and Passcode = %s'
    cursor.execute(query, (username, hashed_password))
    data = cursor.fetchone()
    cursor.close()
    
    if data:
        session['username'] = username
        session['role'] = 'staff'
        session['first_name'] = data['First_Name']  # Store first name in the session
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or password'
        return render_template('staff_login.html', error=error)





@app.route('/home')
def home():
    # Redirect to specific home page based on role
    if 'role' in session:
        cursor = conn.cursor()
        if session['role'] == 'customer':  # Check if the user is a customer based on session role
            email = session['email']
            # Query to fetch the first name of the customer
            query = 'SELECT First_Name FROM Customer WHERE Email = %s'
            cursor.execute(query, (email,))
            data = cursor.fetchone()
            cursor.close()
            first_name = data['First_Name'] if data else 'Customer'
            return render_template('customer_home.html', first_name=first_name)
        elif session['role'] == 'staff':  # Check if the user is a staff member based on session role
            username = session['username']
            # Query to fetch the first name of the staff member
            query = 'SELECT First_Name FROM Airline_Staff WHERE Username = %s'
            cursor.execute(query, (username,))
            data = cursor.fetchone()
            cursor.close()
            first_name = data['First_Name'] if data else 'Staff'
            return render_template('staff_home.html', first_name=first_name)
    else:
        return redirect(url_for('hello'))  # If no valid session role, redirect to homepage



@app.route('/search_flights', methods=['POST'])
def search_flights():
    # Retrieve form data
    departure_code = request.form['departure_code']
    arrival_code = request.form['arrival_code']
    trip_type = request.form['trip_type']
    departure_date = request.form['departure_date']
    return_date = request.form.get('return_date') if trip_type == 'round-trip' else None
    target_page = request.form.get('target_page', 'index')  # Default to 'index'

    cursor = conn.cursor()

    # Query for one-way flights
    query = '''
        SELECT * FROM Flight
        WHERE Departure_Code = %s AND Arrival_Code = %s AND Departure_Date = %s
    '''
    params = [departure_code, arrival_code, departure_date]

    # If round-trip, add query for return flight
    if trip_type == 'round-trip' and return_date:
        query += ' UNION ALL SELECT * FROM Flight WHERE Departure_Code = %s AND Arrival_Code = %s AND Departure_Date = %s'
        params.extend([arrival_code, departure_code, return_date])

    cursor.execute(query, params)
    flights = cursor.fetchall()
    cursor.close()

    # Render the appropriate template based on the target_page
    if target_page == 'index':
        return render_template('index.html', flights=flights)
    elif target_page == 'customer_home':
        return render_template('customer_home.html', flights=flights)
    else:
        return "Page not found", 404



@app.route('/flight_status', methods=['POST'])
def flight_status():
    airline_name = request.form['airline_name']
    flight_num = request.form['flight_num']
    date = request.form['date']
    date_type = request.form['date_type']  # 'departure' or 'arrival'

    cursor = conn.cursor()
    query = f'''
        SELECT 
            Flight_Num, 
            Flight_Status, 
            Airline_Name,
            {date_type}_Date AS Date, 
            {date_type}_Time AS Time, 
            Departure_Code, 
            Arrival_Code, 
            %s AS Date_Type
        FROM Flight
        WHERE Airline_Name = %s AND Flight_Num = %s AND {date_type}_Date = %s
    '''
    cursor.execute(query, (date_type, airline_name, flight_num, date))
    flight_status_results = cursor.fetchall()
    cursor.close()

    # Render the template with the flight status results
    return render_template('index.html', flight_status_results=flight_status_results)


@app.route('/rate_flight', methods=['GET', 'POST'])
def rate_flight():
    # Check if user is logged in
    if 'email' not in session:
        return redirect('/login')
    
    # For GET request, fetch available flights to rate
    if request.method == 'GET':
        try:
            # Create database cursor
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Fetch flights the user has taken that are eligible for rating
            cursor.execute("""
                SELECT DISTINCT f.Flight_Num, 
                       f.Departure_Code, 
                       f.Arrival_Code, 
                       f.Departure_Date, 
                       f.Airline_Name,
                       f.Departure_Time
                FROM Flight f
                JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                JOIN (
                    SELECT Ticket_ID, Email FROM Purchase
                    UNION
                    SELECT Ticket_ID, Email FROM Booked
                ) b ON t.Ticket_ID = b.Ticket_ID
                LEFT JOIN Rate_Comment rc ON f.Flight_Num = rc.Flight_Num AND b.Email = rc.Email
                WHERE b.Email = %s 
                  AND f.Departure_Date < CURRENT_DATE
                  AND rc.Flight_Num IS NULL
            """, (session['email'],))
            
            flights_to_rate = cursor.fetchall()
            
            return render_template('rate_flight.html', flights=flights_to_rate)
        
        except pymysql.Error as err:
            print(f"Database error: {err}")
            return "Error fetching flights", 500
        
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    # For POST request, process the rating submission
    elif request.method == 'POST':
        try:
            # Get form data
            flight_num = request.form['flight_num']
            rating = request.form['rating']
            comment = request.form.get('comment', '')  # Optional comment
            
            # Create database cursor
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Validate that the user has actually booked/purchased this flight
            cursor.execute("""
                SELECT 1 
                FROM Flight f
                JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                JOIN (
                    SELECT Ticket_ID, Email FROM Purchase
                    UNION
                    SELECT Ticket_ID, Email FROM Booked
                ) b ON t.Ticket_ID = b.Ticket_ID
                WHERE b.Email = %s 
                  AND f.Flight_Num = %s
                  AND f.Departure_Date < CURRENT_DATE
            """, (session['email'], flight_num))
            
            flight_exists = cursor.fetchone()
            
            # Check if flight rating already exists
            cursor.execute("""
                SELECT 1 
                FROM Rate_Comment 
                WHERE Email = %s AND Flight_Num = %s
            """, (session['email'], flight_num))
            
            already_rated = cursor.fetchone()
            
            # Validate inputs
            if not flight_exists:
                return "Invalid flight or you did not take this flight", 400
            
            if already_rated:
                return "You have already rated this flight", 400
            
            if not (1 <= int(rating) <= 5):
                return "Rating must be between 1 and 5", 400
            
            # Insert rating and comment
            cursor.execute("""
                INSERT INTO Rate_Comment (Email, Flight_Num, Comment, Rating)
                VALUES (%s, %s, %s, %s)
            """, (session['email'], flight_num, comment, rating))
            
            # Commit the transaction
            conn.commit()
            
            # Redirect to confirmation or back to rating page
            return redirect('/customer_home')
        
        except pymysql.Error as err:
            # Rollback in case of error
            conn.rollback()
            print(f"Database error: {err}")
            return "Error submitting rating", 500
        
        except Exception as e:
            # Rollback in case of any other error
            conn.rollback()
            print(f"Unexpected error: {e}")
            return "An unexpected error occurred", 500
        
        finally:
            if 'cursor' in locals():
                cursor.close()



@app.route('/customer_home')
def customer_home():
    # Check if user is logged in
    if 'email' not in session:
        return redirect('/login')
    
    return render_template('customer_home.html', email=session['email'])

@app.route('/cancel_ticket', methods=['POST'])
def cancel_ticket():
    # Initialize variables
    cursor = None

    try:
        # Check if user is logged in
        if 'email' not in session:
            return "Please log in first", 401

        email = session['email']
        ticket_id = request.form['ticket_id']

        # Create database cursor
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Step 1: Validate Ticket Ownership and Flight Timing
        cursor.execute("""
            SELECT t.Flight_Num, t.Seat_Number, f.Departure_Date, f.Departure_Time
            FROM Ticket t
            JOIN Flight f ON t.Flight_Num = f.Flight_Num
            JOIN Booked b ON t.Ticket_ID = b.Ticket_ID
            WHERE t.Ticket_ID = %s AND b.Email = %s
        """, (ticket_id, email))
        ticket_info = cursor.fetchone()

        # Check if ticket exists and belongs to the customer
        if not ticket_info:
            return "Ticket not found or does not belong to you", 400
# Assuming ticket_info['Departure_Time'] is a timedelta
        departure_time = (datetime.min + ticket_info['Departure_Time']).time()
        flight_datetime = datetime.combine(ticket_info['Departure_Date'], departure_time)
        current_datetime = datetime.now()
        
        if flight_datetime - current_datetime <= timedelta(hours=24):
            return "Ticket cannot be canceled less than 24 hours before flight", 400

        # Start database transaction
        conn.begin()

        # Step 2: Remove Booking Record FIRST
        cursor.execute("DELETE FROM Booked WHERE Ticket_ID = %s", (ticket_id,))

        # Step 3: Remove Purchase Record
        cursor.execute("DELETE FROM Purchase WHERE Ticket_ID = %s", (ticket_id,))

        # Step 4: Delete the Ticket
        cursor.execute("DELETE FROM Ticket WHERE Ticket_ID = %s", (ticket_id,))

        # Step 5: Restore Seat Availability
        cursor.execute("""
            UPDATE Seat_Availability 
            SET Is_Available = TRUE 
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (ticket_info['Flight_Num'], ticket_info['Seat_Number']))

        # Confirm all database changes
        conn.commit()

        # Optional: Refund Processing Logic (placeholder)
        # In a real system, you'd implement refund logic here

        return redirect('/customer_home')

    except KeyError as e:
        return f"Missing information: {str(e)}", 400

    except pymysql.Error as err:
        # If database transaction fails, undo changes
        if conn:
            conn.rollback()
        print(f"Database error: {err}")
        return "Error processing ticket cancellation", 500

    except Exception as e:
        # Handle any unexpected errors
        if conn:
            conn.rollback()
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred", 500

    finally:
        # Always close database cursor
        if cursor:
            cursor.close()


@app.route('/view_flights', methods=['GET'])
def view_flights():
    if 'email' not in session:  # Ensure the user is logged in
        return redirect(url_for('login'))

    email = session['email']  # Get the logged-in user's email
    first_name = session.get('first_name', 'Guest')  # Retrieve first name from session
    query_type = request.args.get('type', 'future')  # Get the query type (future/past)

    try:
        with conn.cursor() as cursor:
            if query_type == 'past':
                # Fetch past flights
                query = """
                    SELECT f.Flight_Num, f.Departure_Date, f.Departure_Time, f.Arrival_Date, f.Arrival_Time, 
                           f.Departure_Code, f.Arrival_Code, f.Airline_Name, t.Sold_Price
                    FROM Flight f
                    JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                    JOIN Purchase p ON t.Ticket_ID = p.Ticket_ID
                    WHERE p.Email = %s AND f.Departure_Date < CURDATE()
                    ORDER BY f.Departure_Date DESC
                """
            else:
                # Fetch future flights (default)
                query = """
                    SELECT f.Flight_Num, f.Departure_Date, f.Departure_Time, f.Arrival_Date, f.Arrival_Time, 
                           f.Departure_Code, f.Arrival_Code, f.Airline_Name, t.Sold_Price
                    FROM Flight f
                    JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                    JOIN Purchase p ON t.Ticket_ID = p.Ticket_ID
                    WHERE p.Email = %s AND f.Departure_Date >= CURDATE()
                    ORDER BY f.Departure_Date ASC
                """
            cursor.execute(query, (email,))
            flights = cursor.fetchall()  # Fetch results

        return render_template('customer_home.html', 
                               flights=flights, 
                               query_type=query_type, 
                               first_name=first_name)  # Pass first_name
    except Exception as e:
        print(f"Error fetching flights: {e}")
        return redirect(url_for('customer_home'))






@app.route('/purchase_ticket', methods=['POST'])
def purchase_ticket():
    # Initialize variables to track database connections and ticket
    cursor = None
    ticket_id = None

    try:
        # Step 1: Get Ticket Information from Form
        # Retrieve details submitted by user
        flight_num = request.form['flight_num']
        seat_number = request.form['seat_number']
        card_number = request.form['card_number']


        email = session['email']

        # Create a database cursor to interact with the database
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Step 2: Validate Flight
        # Check if flight exists and is in the future
        cursor.execute("""
            SELECT * FROM Flight 
            WHERE Flight_Num = %s AND Departure_Date >= CURRENT_DATE
        """, (flight_num,))
        flight = cursor.fetchone()

        if not flight:
            return "Sorry, tickets for this flight are not available", 400

        # Step 3: Get Customer Details
        # Retrieve customer information from database
        cursor.execute("""
            SELECT Date_of_Birth, First_Name, Last_Name
            FROM Customer 
            WHERE Email = %s
        """, (email,))
        customer = cursor.fetchone()


        # Step 4: Check Seat Availability
        cursor.execute("""
            SELECT Is_Available FROM Seat_Availability 
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (flight_num, seat_number))
        seat = cursor.fetchone()

        if not seat or not seat['Is_Available']:
            return "Sorry, this seat is not available", 400

        # Step 5: Validate Payment Method
        cursor.execute("""
            SELECT Card_Number FROM Payment_Info pi
            JOIN Booked b ON pi.Card_Number = b.Payment_Card_Number
            WHERE b.Email = %s AND pi.Card_Number = %s
        """, (email, card_number))
        payment_card = cursor.fetchone()

        if not payment_card:
            return "Invalid card details", 400

        # Start a database transaction
        conn.begin()

        # Generate a new Ticket ID
        cursor.execute("SELECT MAX(Ticket_ID) FROM Ticket")
        last_ticket_id = cursor.fetchone()['MAX(Ticket_ID)']
        ticket_id = last_ticket_id + 1 if last_ticket_id else 1

        # Step 6: Create Ticket Record
        cursor.execute("""
            INSERT INTO Ticket 
            (Ticket_ID, Flight_Num, Seat_Number, Date_of_Birth, Email) 
            VALUES (%s, %s, %s, %s, %s)
        """, (ticket_id, flight_num, seat_number, customer['Date_of_Birth'], email))

        # Step 7: Update Seat Availability
        cursor.execute("""
            UPDATE Seat_Availability 
            SET Is_Available = FALSE 
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (flight_num, seat_number))

        # Step 8: Record Purchase Details
        cursor.execute("""
            INSERT INTO Purchase 
            (Email, Ticket_ID, Purchase_Date, Purchase_Time, 
             First_Name, Last_Name, Date_of_Birth)
            VALUES (%s, %s, CURRENT_DATE, CURRENT_TIME, %s, %s, %s)
        """, (email, ticket_id, 
               customer['First_Name'], 
               customer['Last_Name'], 
               customer['Date_of_Birth']))

        # Step 9: Record Booking Information
        cursor.execute("""
            INSERT INTO Booked 
            (Email, Ticket_ID, Payment_Card_Number) 
            VALUES (%s, %s, %s)
        """, (email, ticket_id, card_number))

        # Confirm all database changes
        conn.commit()

        # Redirect to home page after successful purchase
        return redirect('/customer_home')

    except KeyError as e:
        return f"Missing information: {str(e)}", 400

    except pymysql.Error as err:
        # If database transaction fails, undo changes
        if conn:
            conn.rollback()
        print(f"Database error: {err}")
        return "Error processing ticket purchase", 500

    except Exception as e:
        # Handle any unexpected errors
        if conn:
            conn.rollback()
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred", 500

    finally:
        # Always close database cursor
        if cursor:
            cursor.close()

# ----------suha------------------ #

@app.route('/view_staff_flights', methods=['GET', 'POST'])  # (not working yet)
def view_staff_flights():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']  # Get the logged-in staff's username
    cursor = conn.cursor()

    #retrieve the airline the airport staff works at 
    query = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone() # stores the airline the staff works at

    if not staff_airline:
        cursor.close()
        return "Error: Airline Staff does not work at an Airline"
    
    airline_name = staff_airline['Airline_Name']

    # default: show future flights for the next 30 days
    flights = []
    if request.method == 'GET':
        query = """
            SELECT Flight.Flight_Num, Flight.Departure_Date, Flight.Departure_Time, Flight.Arrival_Date, 
            Flight.Arrival_Time, Flight.Departure_Code, Flight.Arrival_Code, Flight.Flight_Status
            FROM Flight
            WHERE WHERE Flight.Departure_Date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """
        cursor.execute(query, (airline_name,))
        flights = cursor.fetchall()

    # filters 
    if request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')


        query =  """
            SELECT Flight.Flight_Num, Flight.Departure_Date, Flight.Departure_Time, Flight.Arrival_Date, 
            Flight.Arrival_Time, Flight.Departure_Code, Flight.Arrival_Code, Flight.Flight_Status
            FROM Flight
            WHERE Flight.Airline_Name = %s
        """

        params = [airline_name]

        if source:
            query += ' AND Flight.Departure_Code IN (SELECT Airport_Code FROM Airport WHERE City LIKE %s OR Airport_Name LIKE %s)'
            params.extend([f"%{source}%", f"%{source}%"])
        if destination:
            query += ' AND Flight.Arrival_Code IN (SELECT Airport_Code FROM Airport WHERE City LIKE %s OR Airport_Name LIKE %s)'
            params.extend([f"%{destination}%", f"%{destination}%"])
        if start_date and end_date:
            query += ' AND Flight.Departure_Date BETWEEN %s AND %s'
            params.extend([start_date, end_date])

        cursor.execute(query, params)
        flights = cursor.fetchall()

    cursor.close()
    return render_template('staff_flights.html', flights=flights, airline_name=airline_name)


@app.route('/view_flight_customers', methods=['POST'])
def view_flight_customers():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))

    flight_num = request.form.get('flight_num')  # Get flight number from the form
    cursor = conn.cursor()

    # Query to fetch customers for the given flight
    query = '''
        SELECT C.First_Name, C.Last_Name, C.Email, T.Ticket_ID
        FROM Ticket T
        JOIN Customer C ON T.Email = C.Email
        WHERE T.Flight_Num = %s
    '''
    cursor.execute(query, (flight_num,))
    customers = cursor.fetchall()
    cursor.close()

    return render_template('view_customers.html', customers=customers, flight_num=flight_num)


@app.route('/change_flight_status', methods=['GET', 'POST']) 
def change_flight_status():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))

    username = session['username'] 
    cursor = conn.cursor()

    # Retrieve the airline the staff works for
    query = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Error: Airline Staff does not work for any airline." # raise an error instead?

    airline_name = staff_airline['Airline_Name']

    if request.method == 'POST':
        # Handle the flight status update
        flight_num = request.form.get('flight_num')
        new_status = request.form.get('status')

        if not flight_num or not new_status: # delete ???
            return "Error: Flight number or status not provided."

        # Update the flight status
        update_query = '''
            UPDATE Flight
            SET Flight_Status = %s
            WHERE Flight_Num = %s AND Airline_Name = %s
        '''
        cursor.execute(update_query, (new_status, flight_num, airline_name))
        conn.commit()

        cursor.close()
        return redirect(url_for('change_flight_status'))  # Redirect to the same page after updating

    # Default: Display flights for the airline to select (only modify future flights)
    query_for_flights = '''
        SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
        FROM Flight
        WHERE Airline_Name = %s AND Departure_Date >= CURDATE()
    '''
    cursor.execute(query_for_flights, (airline_name,))
    flights = cursor.fetchall()
    cursor.close()

    return render_template('change_flight_status.html', flights=flights, airline_name=airline_name)


@app.route('/add_airplane', methods=['GET', 'POST'])
def add_airplane():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    query = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Error: Airline Staff does not work for any airline." # raise an error instead?
    
    airline_name = staff_airline['Airline_Name']

    if request.method == 'POST':
        airplane_id = request.form.get('airplane_id')
        num_seats = request.form.get('num_seats')
        manufacturer = request.form.get('manufacturer')
        model_num = request.form.get('model_num')
        manufacture_date = request.form.get('manufacture_date')

        query_insert = """
            INSERT INTO Airplane (Airline_Name, Airplane_ID, Number_of_Seats, 
            Manufacturing_Company, Model_Num, Manufacturing_Date, Age) 
            VALUES (%s, %s, %s, %s, %s, %s, YEAR(CURDATE()) - YEAR(%s))
        """
        # age = YEAR(CURRENT_DATE) - YEAR(Manufacturing_Date)

        cursor.execute(query_insert, (airline_name, airplane_id, num_seats, manufacturer, 
                                      model_num, manufacture_date, manufacture_date))
        conn.commit()

        # all airplanes owned by the airline
        query_airlines = """
            SELECT Airline_Name, Airplane_ID, Number_of_Seats, 
            Manufacturing_Company, Model_Num, Manufacturing_Date, Age
            FROM Airplane
            WHERE Airplane.Airline_Name = %s
        """

        cursor.execute(query_airlines,(airline_name,))
        airplanes = cursor.fetchall()
        cursor.close()

        return render_template('airplane_confirmation.html', 
                               airplanes=airplanes, airline_name=airline_name)
    
    return render_template('add_airplane.html', airline_name=airline_name)


@app.route('/add_airport', methods=['GET', 'POST'])
def add_airport():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    if request.method == 'POST':
        airport_code = request.form.get('airport_code')
        airport_name = request.form.get('airport_name')
        city = request.form.get('city')
        country = request.form.get('country')
        num_terminals = request.form.get('num_terminals')
        airport_type = request.form.get('airport_type')

        try:
            cursor = conn.cursor()
            query_insert = """
                INSERT INTO Airport (Airport_Code, Airport_Name, City, Country, 
                Number_of_Terminals, Airport_Type) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_insert, (airport_code, airport_name, city, country, num_terminals, airport_type))
            conn.commit()

            # show all airport confirmation ???
            query_airports = """
                SELECT Airport_Code, Airport_Name, City, Country, Number_of_Terminals, Airport_Type
                FROM Airport
                WHERE Airport_Code = %s
            """

            cursor.execute(query_airports, (airport_code,))
            airport = cursor.fetchone()
            cursor.close()

            return render_template('airport_confirmation.html', airport=airport)

        except Exception as e:
            conn.rollback()
            print(f"Error inserting airport: {e}")
            return f"Error: Unable to add airport. {str(e)}"
        
    return render_template('add_airport.html')


@app.route('/view_earned_revenue', methods=['GET'])
def view_earned_revenue():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Error: Airline Staff does not work for any airline." # raise an error instead?
    
    airline_name = staff_airline['Airline_Name']

    query_for_month = """
       SELECT SUM(Ticket.Sold_Price) AS Last_Month_Revenue
        FROM Purchase, Ticket, Flight
        WHERE Flight.Airline_Name = %s
            AND Purchase.Ticket_ID = Ticket.Ticket_ID
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND Purchase.Purchase_Date BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE()
    """
    cursor.execute(query_for_month, (airline_name,))
    revenue_for_month = cursor.fetchone()['Last_Month_Revenue'] or 0
    
    query_for_year = """
        SELECT SUM(Ticket.Sold_Price) AS Last_Year_Revenue
        FROM Purchase, Ticket, Flight
        WHERE Flight.Airline_Name = %s
            AND Purchase.Ticket_ID = Ticket.Ticket_ID
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND Purchase.Purchase_Date BETWEEN CURDATE() - INTERVAL 1 YEAR AND CURDATE()
    """
    cursor.execute(query_for_year, (airline_name,))
    revenue_for_year = cursor.fetchone()['Last_Year_Revenue'] or 0

    cursor.close()

    return render_template(
        'view_earned_revenue.html',
        airline_name=airline_name,
        revenue_last_month=revenue_for_month,
        revenue_last_year=revenue_for_year
    )


@app.route('/view_flight_ratings', methods=['GET'])  # check this after adding rating and comments from customer
def view_flight_ratings():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Error: Airline Staff does not work for any airline." # raise an error instead?
    
    airline_name = staff_airline['Airline_Name']

    query_for_flights = """
        SELECT Flight_Num, Departure_Date, Departure_Code, Arrival_Date, Arrival_Code
        FROM Flight
        WHERE Airline_Name = %s
    """

    cursor.execute(query_for_flights, (airline_name,))
    flights = cursor.fetchall()

    flight_info = []
    for flight in flights:
        flight_num = flight['Flight_Num']

        query_average_rating = """
            SELECT AVG(Rating) AS Average_Rating
            FROM Rate_Comment
            WHERE Flight_Num= %s
        """

        cursor.execute(query_average_rating, (flight_num,))
        rating = cursor.fetchone()['Average_Rating'] or 0

        query_flight_comments = """
            SELECT Comment, Rating, Email
            FROM Rate_Comment
            WHERE Flight_Num= %s
        """
        cursor.execute(query_flight_comments, (flight_num,))
        comments = cursor.fetchall()

        flight_info.append({
            'Flight_Num': flight_num,
            'Departure_Date': flight['Departure_Date'],
            'Arrival_Date': flight['Arrival_Date'],
            'Departure_Code': flight['Departure_Code'],
            'Arrival_Code': flight['Arrival_Code'],
            'Avg_Rating': rating,
            'Comments': comments
        })

    cursor.close()
    return render_template('view_flight_ratings.html', 
                           flights=flight_info, airline_name=airline_name)

@app.route('/view_frequent_customer', methods=['GET', 'POST'])
def view_frequent_customer():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Error: Airline Staff does not work for any airline." # raise an error instead?
    
    airline_name = staff_airline['Airline_Name']

    query_most_freq_cust = """
        SELECT Customer.Email, Customer.First_Name, Customer.Last_Name, 
            COUNT(DISTINCT Flight.Flight_Num) AS Total_Flights
        FROM Ticket, Customer, Flight
        WHERE Flight.Airline_Name = %s
            AND Ticket.Email = Customer.Email
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND Flight.Departure_Date BETWEEN CURDATE() - INTERVAL 1 YEAR AND CURDATE()
        GROUP BY Customer.Email
        ORDER BY Total_Flights DESC
        LIMIT 1
    """
    cursor.execute(query_most_freq_cust, (airline_name,))
    frequent_customer = cursor.fetchone()

    query_customers = """
        SELECT DISTINCT Customer.Email, Customer.First_Name, Customer.Last_Name
        FROM Ticket, Customer, Flight
        WHERE Flight.Airline_Name = %s
            AND Ticket.Email = Customer.Email
            AND Ticket.Flight_Num = Flight.Flight_Num
    """
    cursor.execute(query_customers, (airline_name,))
    customers = cursor.fetchall()

    # customer = request.args.get('email')
    # customer_flights = None

    flight_data = []
    for customer in customers:
        email = customer['Email']

        query_customer_flights = """
            SELECT Flight.Flight_Num, Flight.Departure_Date, Flight.Arrival_Date, 
                Flight.Departure_Code, Flight.Arrival_Code
            FROM Ticket, Flight
            WHERE Ticket.Email = %s AND Flight.Airline_Name = %s
                AND Ticket.Flight_Num = Flight.Flight_Num
                AND Flight.Departure_Date < CURDATE()
        """
        cursor.execute(query_customer_flights, (email, airline_name))
        flights = cursor.fetchall()

        flight_data.append({
            'customer': customer,
            'flights': flights
        })

    cursor.close()    
        
    if not frequent_customer:
        return "No frequent customers found in the last year."

    return render_template(
        'view_frequent_customer.html',
        most_frequent_customer=frequent_customer,
        customer_flights_data=flight_data,
        airline_name=airline_name
    )


# Logout route 
# (modified slightly to lead to the airline staff and customer login pages)
@app.route('/logout')
def logout():
    role = session.get('role')
    session.pop('email', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('first_name', None)

    if role == 'customer':
        return redirect(url_for('login', role='customer'))
    elif role == 'staff':
        return redirect(url_for('login', role='staff'))
    else:
        return redirect(url_for('hello'))

app.secret_key = 'some key that you will never guess'

# Run the app on localhost port 5000
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)