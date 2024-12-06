from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib  # for MD5 hashing suggested in part 3
from datetime import datetime, timedelta

app = Flask(__name__)
conn = pymysql.connect(host='127.0.0.1',
                       user='root',
                       password='root',
                       port=8889,
                       db='airplane_updated',
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
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    date_of_birth = request.form['date_of_birth']
    email = request.form['email']
    phone = request.form['phone']
    airline = request.form['airline']

    hashed_password = hashlib.md5(password.encode()).hexdigest()

    cursor = conn.cursor()

    # check if username is already taken
    query = 'SELECT * FROM Airline_Staff WHERE Username = %s'
    cursor.execute(query, (username,))
    data = cursor.fetchone()

    if data:
        cursor.close()
        error = "This username is taken."
        return render_template('staff_register.html', error=error)
    
    # check to see if airline exists
    query_airline = 'SELECT * FROM Airline WHERE Airline_Name = %s'
    cursor.execute(query_airline, (airline,))
    airline_data = cursor.fetchone()

    if not airline_data:
        cursor.close()
        error = f"Airline does not exist."
        return render_template('staff_register.html', error=error)

    try:
        insert_query = """
            INSERT INTO Airline_Staff (Username, First_Name, Last_Name, Passcode, Date_of_Birth)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (username, first_name, last_name, hashed_password, date_of_birth))
        
        query_email = """
            INSERT INTO Airline_Staff_Email (Username, Email)
            VALUES (%s, %s)
        """
        cursor.execute(query_email, (username, email))
        
        query_phone = """
            INSERT INTO Airline_Staff_Phone (Username, Phone)
            VALUES (%s, %s)
        """    
        cursor.execute(query_phone, (username, phone))
        
        # update which airline the user/staff works at
        query_works_for = """
            INSERT INTO Works_For (Username, Airline_Name)
            VALUES (%s, %s)
        """
        cursor.execute(query_works_for, (username, airline))

        conn.commit()

    except Exception as e:
        conn.rollback()
        cursor.close()
        return f"Error during registration: {str(e)}"
    
    cursor.close()
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
            query_airline = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
            cursor.execute(query_airline, (username,))
            staff_airline = cursor.fetchone()
            airline_name = staff_airline['Airline_Name']
            first_name = data['First_Name'] if data else 'Staff'
            cursor.close()
            return render_template('staff_home.html', first_name=first_name, airline_name=airline_name)
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

@app.route('/view_staff_flights', methods=['GET', 'POST'])
def view_staff_flights():
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
        return "Airline for Airline Staff Not Found."
    
    airline_name = staff_airline['Airline_Name']
    flights = []
    customers = []

    # the default is to show the future flights for the next 30 days
    if request.method == 'GET':
        query_flights = """
                    SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
                    FROM Flight
                    WHERE Airline_Name = %s 
                    AND (
                        (Departure_Date BETWEEN CURDATE() AND CURDATE() + INTERVAL 30 DAY) OR
                        (Departure_Date = CURDATE() AND Departure_Time > CURTIME())
                    )
                """
        cursor.execute(query_flights, (airline_name,))
        flights = cursor.fetchall()

    # filters that a staff can input through the forms
    elif request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        query_flights = """
            SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
            FROM Flight
            WHERE Airline_Name = %s
        """
        params = [airline_name]

        if start_date and end_date:
            query_flights += " AND Departure_Date BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        if start_date and not end_date:
            return "specify end date"
        
        if not start_date and end_date:
            return "specify start date"   

        if source:
            query_flights += " AND Departure_Code = %s"
            params.append(source)

        if destination:
            query_flights += " AND Arrival_Code = %s"
            params.append(destination)

        cursor.execute(query_flights, params)
        flights = cursor.fetchall()

    # customers and the flights they have taken 
    flight_numbers = [flight['Flight_Num'] for flight in flights]
    if flight_numbers:
        query_customers = """
            SELECT DISTINCT Customer.Email, Customer.First_Name, Customer.Last_Name,
                Flight.Flight_Num, Flight.Departure_Date
            FROM Ticket
            JOIN Customer ON Ticket.Email = Customer.Email
            JOIN Flight ON Ticket.Flight_Num = Flight.Flight_Num
            WHERE Flight.Airline_Name = %s AND Flight.Flight_Num IN ({})
            ORDER BY Flight.Flight_Num
        """.format(", ".join(["%s"] * len(flight_numbers)))

        params = [airline_name] + flight_numbers
        cursor.execute(query_customers, params)
        customers = cursor.fetchall()

    cursor.close()
    return render_template('view_staff_flights.html', flights=flights, customers=customers)


# use case 3
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
        return "Airline for Airline Staff Not Found"

    airline_name = staff_airline['Airline_Name']

    if request.method == 'POST':
        # Handle the flight status update
        flight_num = request.form.get('flight_num')
        new_status = request.form.get('status')

        if not flight_num or not new_status:
            return "Flight number or status not provided"
       
        try:
            # Update the flight status
            update_query = '''
                UPDATE Flight
                SET Flight_Status = %s
                WHERE Flight_Num = %s AND Airline_Name = %s
            '''
            cursor.execute(update_query, (new_status, flight_num, airline_name))
            conn.commit()
        
        except Exception as e:    
            conn.rollback()
            cursor.close()
            return f"Unable to update flight status. {str(e)}"
        
        cursor.close()
        return redirect(url_for('change_flight_status'))

    # only modify status of future flights
    query_for_flights = """
        SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
        FROM Flight
        WHERE Airline_Name = %s AND Departure_Date >= CURDATE()
    """

    # query_for_flights = """
    #     SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
    #     FROM Flight
    #     WHERE Airline_Name = %s
    # """

    cursor.execute(query_for_flights, (airline_name,))
    flights = cursor.fetchall()
    cursor.close()

    return render_template('change_flight_status.html', flights=flights, airline_name=airline_name)


# use case 4
# multiple airplanes with same id cannot exist within an airline
@app.route('/add_airplane', methods=['GET', 'POST'])
def add_airplane():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        query = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
        cursor.execute(query, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            airplane_id = request.form.get('airplane_id')
            num_seats = request.form.get('num_seats')
            manufacturer = request.form.get('manufacturer')
            model_num = request.form.get('model_num')
            manufacture_date = request.form.get('manufacture_date')

            if not (airplane_id and num_seats and manufacturer and model_num and manufacture_date):
                return "Fill out all fields."

            try:
                conn.begin()
                query_date = "SELECT CURDATE()"
                cursor.execute(query_date)
                current_date = cursor.fetchone()['CURDATE()']

                if manufacture_date > str(current_date):
                    return f"The manufacturing date cannot exceed the current date."

                # Check for duplicate airplane within the airline
                query_duplicate = """
                    SELECT * 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name = %s
                """
                cursor.execute(query_duplicate, (airplane_id, airline_name))
                existing_airplane = cursor.fetchone()

                if existing_airplane:
                    return f"Airplane with ID {airplane_id} already exists."

                # Insert the airplane
                query_insert_airplane = """
                    INSERT INTO Airplane (Airline_Name, Airplane_ID, Number_of_Seats, 
                                          Manufacturing_Company, Model_Num, Manufacturing_Date, Age) 
                    VALUES (%s, %s, %s, %s, %s, %s, YEAR(CURDATE()) - YEAR(%s))
                """
                cursor.execute(query_insert_airplane, (airline_name, airplane_id, num_seats, manufacturer, 
                                              model_num, manufacture_date, manufacture_date))
                
                # update owns table
                query_insert_owns = """
                    INSERT INTO Owns (Airline_Name, Airplane_ID) 
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert_owns, (airline_name, airplane_id))
                
                conn.commit()

                # get all the airplanes for confirmation page
                query_airplanes = """
                    SELECT Airline_Name, Airplane_ID, Number_of_Seats, 
                           Manufacturing_Company, Model_Num, Manufacturing_Date, Age
                    FROM Airplane
                    WHERE Airline_Name = %s
                """
                cursor.execute(query_airplanes, (airline_name,))
                airplanes = cursor.fetchall()

                return render_template('airplane_confirmation.html', 
                                       airplanes=airplanes, airline_name=airline_name)
            
            except Exception as e:
                conn.rollback()
                return f"Unable to add new airplane. {str(e)}"
        
        return render_template('add_airplane.html', airline_name=airline_name)

    except Exception as e:
        return f"Error: {str(e)}"
    
    finally:
        cursor.close()

# use case 5
# make sure airport is not associated with airline already
@app.route('/add_airport', methods=['GET', 'POST'])
def add_airport():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        # get the airline the staff works for
        query_airline = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
        cursor.execute(query_airline, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            airport_code = request.form.get('airport_code')
            airport_name = request.form.get('airport_name')
            city = request.form.get('city')
            country = request.form.get('country')
            num_terminals = request.form.get('num_terminals')
            airport_type = request.form.get('airport_type')

            if not (airport_code and airport_name and city and country and num_terminals and airport_type):
                return "Fill out all fields."

            try:
                # check if the airport already exists
                query_duplicate_airport = """
                    SELECT * 
                    FROM Airport 
                    WHERE Airport_Code = %s
                """
                cursor.execute(query_duplicate_airport, (airport_code,))
                existing_airport = cursor.fetchone()

                # if the airport does not exist, insert new airport into db
                if not existing_airport:
                    query_insert_airport = """
                        INSERT INTO Airport (Airport_Code, Airport_Name, City, Country, 
                                             Number_of_Terminals, Airport_Type) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query_insert_airport, (airport_code, airport_name, city, country, num_terminals, airport_type))
                    conn.commit()

                # check if the airport is operated by this airline
                query_duplicate_operates = """
                    SELECT * 
                    FROM Operates 
                    WHERE Airline_Name = %s AND Airport_Code = %s
                """
                cursor.execute(query_duplicate_operates, (airline_name, airport_code))
                existing_association = cursor.fetchone()

                if existing_association:
                    return f"The airport {airport_code} is already associated with the airline {airline_name}."

                # associate the airport with the airline through operates
                query_insert_operates = """
                    INSERT INTO Operates (Airline_Name, Airport_Code) 
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert_operates, (airline_name, airport_code))
                conn.commit()

                # confirmation info for staff
                query_airports = """
                    SELECT Airport_Code, Airport_Name, City, Country, Number_of_Terminals, Airport_Type
                    FROM Airport
                    WHERE Airport_Code = %s
                """
                cursor.execute(query_airports, (airport_code,))
                airport = cursor.fetchone()

                return render_template(
                    'airport_confirmation.html', 
                    airport=airport, 
                    airline_name=airline_name
                )

            except Exception as e:
                conn.rollback()
                return f"Unable to add airport. {str(e)}"
            
        return render_template('add_airport.html', airline_name=airline_name)

    except Exception as e:
        return f"Error: {str(e)}"

    finally:
        cursor.close()


#use case 9
# ensure customer email matches ??? ---- modified the month and year query 
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
        return "Airline for Airline Staff Not Found."
    
    airline_name = staff_airline['Airline_Name']

    query_for_month = """
        SELECT SUM(Ticket.Sold_Price) AS Last_Month_Revenue
        FROM Purchase
        JOIN Ticket ON Purchase.Ticket_ID = Ticket.Ticket_ID
        JOIN Flight ON Ticket.Flight_Num = Flight.Flight_Num
        WHERE Flight.Airline_Name = %s
        AND Purchase.Purchase_Date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND CURDATE();
    """
    cursor.execute(query_for_month, (airline_name,))
    revenue_for_month = cursor.fetchone()['Last_Month_Revenue'] or 0


    # query_for_month = """
    #    SELECT SUM(Ticket.Sold_Price) AS Last_Month_Revenue
    #     FROM Purchase, Ticket, Flight, Customer
    #     WHERE Flight.Airline_Name = %s
    #         AND Purchase.Ticket_ID = Ticket.Ticket_ID
    #         AND Ticket.Flight_Num = Flight.Flight_Num
    #         AND Purchase.Email = Customer.Email
    #         AND (
    #             Purchase.Purchase_Date BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE()
    #             OR (Purchase.Purchase_Date = CURDATE() AND Purchase.Purchase_Time <= CURTIME())
    #         )
    # """
    # cursor.execute(query_for_month, (airline_name,))
    # revenue_for_month = cursor.fetchone()['Last_Month_Revenue'] or 0
    
    # query_for_year = """
    #     SELECT SUM(Ticket.Sold_Price) AS Last_Year_Revenue
    #     FROM Purchase, Ticket, Flight, Customer
    #     WHERE Flight.Airline_Name = %s
    #         AND Purchase.Ticket_ID = Ticket.Ticket_ID
    #         AND Ticket.Flight_Num = Flight.Flight_Num
    #         AND Purchase.Email = Customer.Email
    #         AND (
    #             Purchase.Purchase_Date BETWEEN CURDATE() - INTERVAL 1 YEAR AND CURDATE()
    #             OR (Purchase.Purchase_Date = CURDATE() AND Purchase.Purchase_Time <= CURTIME())
    #         )
    # """
    # cursor.execute(query_for_year, (airline_name,))
    # revenue_for_year = cursor.fetchone()['Last_Year_Revenue'] or 0

    query_for_year = """
        SELECT SUM(Ticket.Sold_Price) AS Last_Year_Revenue
        FROM Purchase
        JOIN Ticket ON Purchase.Ticket_ID = Ticket.Ticket_ID
        JOIN Flight ON Ticket.Flight_Num = Flight.Flight_Num
        WHERE Flight.Airline_Name = %s
        AND Purchase.Purchase_Date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE();
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

# use case 6
@app.route('/view_flight_ratings', methods=['GET'])
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
        return "Airline for Airline Staff Not Found."
    
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
        departure_date = flight['Departure_Date']

        query_average_rating = """
            SELECT AVG(Rating) AS Average_Rating
            FROM Rate_Comment, Flight
            WHERE Rate_Comment.Flight_Num = Flight.Flight_Num
                AND Rate_Comment.Flight_Num= %s 
                AND Flight.Departure_Date = %s
                AND Flight.Airline_Name = %s
        """
        cursor.execute(query_average_rating, (flight_num, departure_date, airline_name))
        rating = cursor.fetchone()['Average_Rating'] or 0
        # group by departure date
        query_flight_comments = """
            SELECT Rate_Comment.Comment, Rate_Comment.Rating, Rate_Comment.Email
            FROM Rate_Comment, Flight
            WHERE Rate_Comment.Flight_Num = Flight.Flight_Num
                AND Rate_Comment.Flight_Num= %s 
                AND Flight.Departure_Date = %s
                AND Flight.Airline_Name = %s
        """
        cursor.execute(query_flight_comments, (flight_num, departure_date, airline_name))
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

# use case 8
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
        return "Airline for Airline Staff Not Found."
    
    airline_name = staff_airline['Airline_Name']

    # query_most_freq_cust = """
    #     SELECT Customer.Email, Customer.First_Name, Customer.Last_Name, 
    #         COUNT(DISTINCT CONCAT(Flight.Flight_Num, Flight.Departure_Date)) AS Total_Flights
    #     FROM Ticket, Customer, Flight
    #     WHERE Flight.Airline_Name = %s
    #         AND Ticket.Email = Customer.Email
    #         AND Ticket.Flight_Num = Flight.Flight_Num
    #         AND (
    #             (Flight.Departure_Date BETWEEN CURDATE() - INTERVAL 1 YEAR AND CURDATE())
    #             OR (Flight.Departure_Date = CURDATE() AND Flight.Departure_Time < CURTIME())
    #         )    
    #     GROUP BY Customer.Email
    #     ORDER BY Total_Flights DESC
    #     LIMIT 1
    # """


    query_most_freq_cust = """
        SELECT Customer.Email, Customer.First_Name, Customer.Last_Name, 
            COUNT(DISTINCT Flight.Flight_Num) AS Total_Flights
        FROM Ticket, Customer, Flight
        WHERE Flight.Airline_Name = %s
            AND Ticket.Email = Customer.Email
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND (
                (Flight.Departure_Date BETWEEN CURDATE() - INTERVAL 1 YEAR AND CURDATE())
                OR (Flight.Departure_Date = CURDATE() AND Flight.Departure_Time < CURTIME())
            )    
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

    flight_data = []
    for customer in customers:
        email = customer['Email']

        query_customer_flights = """
            SELECT Flight.Flight_Num, Flight.Departure_Date, Flight.Arrival_Date, 
                Flight.Departure_Code, Flight.Arrival_Code
            FROM Ticket, Flight
            WHERE Ticket.Email = %s 
                AND Flight.Airline_Name = %s
                AND Ticket.Flight_Num = Flight.Flight_Num
                AND (
                    Flight.Departure_Date < CURDATE() OR 
                    (Flight.Departure_Date = CURDATE() AND Flight.Departure_Time < CURTIME())
                )
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

# use case 2
# make sure airplane is not already in a flight at the same time !!!
# make sure the departure and arrival dates are not before curdate (ensure creation of flights for future) ???
# make sure airplane and airports exists
# make sure airplane is not under maintenance 
# make sure airline operates at departure and arrival airports
# if any of these fails, undo changes
@app.route('/create_flight', methods=['GET', 'POST'])
def create_flight():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        # get the airline name the staff works at
        query_airline = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
        cursor.execute(query_airline, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            flight_num = request.form.get('flight_num')
            departure_date = request.form.get('departure_date')
            departure_time = request.form.get('departure_time')
            arrival_date = request.form.get('arrival_date')
            arrival_time = request.form.get('arrival_time')
            base_ticket_price = request.form.get('base_ticket_price')
            flight_status = request.form.get('flight_status')
            airplane_id = request.form.get('airplane_id')
            departure_code = request.form.get('departure_code')
            arrival_code = request.form.get('arrival_code')

            if not all([flight_num, departure_date, departure_time, arrival_date, arrival_time, 
                        base_ticket_price, flight_status, airplane_id, departure_code, arrival_code]):
                return "Fill out all fields."

            try:
                conn.begin()
                # check for airplane existence within the airline
                query_airplane = """
                    SELECT * 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name = %s
                """
                cursor.execute(query_airplane, (airplane_id, airline_name))
                airplane = cursor.fetchone()

                if not airplane:
                    return f"Airplane not found."
                                
                # check for availability due to maintenance
                query_maintenance = """
                    SELECT * 
                    FROM Maintenance_Procedure
                    WHERE Airplane_ID = %s 
                      AND Airline_Name = %s 
                      AND (
                        (%s BETWEEN Start_Date AND End_Date)
                        OR (%s BETWEEN Start_Date AND End_Date)
                        OR (Start_Date = %s AND Start_Time < %s)
                        OR (End_Date = %s AND End_Time > %s)
                      )
                """
                cursor.execute(query_maintenance, (
                airplane_id, airline_name, 
                departure_date, arrival_date, 
                departure_date, departure_time, 
                arrival_date, arrival_time
                ))
                maintenance = cursor.fetchone()

                if maintenance:
                    return f"The airplane is under maintenance during the given flight time."

                # check airports to see if if they exist
                query_airport = "SELECT * FROM Airport WHERE Airport_Code = %s"
                cursor.execute(query_airport, (departure_code,))
                departure_airport = cursor.fetchone()

                cursor.execute(query_airport, (arrival_code,))
                arrival_airport = cursor.fetchone()

                if not departure_airport:
                    return f"Departure airport does not exist."
                if not arrival_airport:
                    return f"Arrival airport does not exist."

                # ensure that the airline operates at the given airports
                query_operates = """
                    SELECT * 
                    FROM Operates 
                    WHERE Airline_Name = %s AND Airport_Code = %s
                """
                cursor.execute(query_operates, (airline_name, departure_code))
                operates_departure = cursor.fetchone()

                cursor.execute(query_operates, (airline_name, arrival_code))
                operates_arrival = cursor.fetchone()

                if not operates_departure:
                    return f"Airline does not operate at departure airport."
                if not operates_arrival:
                    return f"Airline does not operate at arrival airport."

                # Insert the flight into the Flight table using the form data
                query_insert_flight = """
                    INSERT INTO Flight (Flight_Num, Departure_Date, Departure_Time, Arrival_Date, 
                                    Arrival_Time, Base_Ticket_Price, Flight_Status, Airline_Name, 
                                    Departure_Code, Arrival_Code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_insert_flight, (flight_num, departure_date, departure_time, arrival_date, 
                                                     arrival_time, base_ticket_price, flight_status, airline_name, 
                                                     departure_code, arrival_code))

                # seat availability based on airplane seats
                query_seats = "SELECT Number_of_Seats FROM Airplane WHERE Airplane_ID = %s"
                cursor.execute(query_seats, (airplane_id,))
                num_seats = cursor.fetchone()['Number_of_Seats']

                for seat in range(1, num_seats + 1):
                    seat_number = f"{seat:03}"
                    query_insert_seat = """
                        INSERT INTO Seat_Availability (Flight_Num, Seat_Number, Is_Available)
                        VALUES (%s, %s, TRUE)
                    """
                    cursor.execute(query_insert_seat, (flight_num, seat_number))

                conn.commit()

                # get all future flights and its info for the next 30 days
                query_future_flights = """
                    SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
                    FROM Flight
                    WHERE Airline_Name = %s 
                    AND (
                        (Departure_Date BETWEEN CURDATE() AND CURDATE() + INTERVAL 30 DAY) OR
                        (Departure_Date = CURDATE() AND Departure_Time > CURTIME())
                    )
                """
                cursor.execute(query_future_flights, (airline_name,))
                flights = cursor.fetchall()

                return render_template('future_flights.html', flights=flights, airline_name=airline_name)

            except Exception as e:
                conn.rollback()
                return f"Unable to create flight. {str(e)}"

        # future flights to show to staff (the default view)
        query_future_flights = """
            SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
            FROM Flight
            WHERE Airline_Name = %s AND Departure_Date BETWEEN CURDATE() AND CURDATE() + INTERVAL 30 DAY
        """
        cursor.execute(query_future_flights, (airline_name,))
        flights = cursor.fetchall()

        return render_template('create_flight.html', flights=flights, airline_name=airline_name)

    except Exception as e:
        return f"Error: {str(e)}"

    finally:
        cursor.close()

@app.route('/schedule_maintenance', methods=['GET', 'POST'])
def schedule_maintenance():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        # Retrieve the airline the staff works for
        query_airline = "SELECT Airline_Name FROM Works_For WHERE Username = %s"
        cursor.execute(query_airline, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            # get data from form inputs
            airplane_id = request.form.get('airplane_id')
            start_date = request.form.get('start_date')
            start_time = request.form.get('start_time')
            end_date = request.form.get('end_date')
            end_time = request.form.get('end_time')

            if not ([airplane_id and start_date and start_time and end_date and end_time]):
                return "Fill out all fields."

            try:
                # make sure the airplane exists and belongs to the correct airline
                query_airplane = """
                    SELECT * 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name = %s
                """
                cursor.execute(query_airplane, (airplane_id, airline_name))
                airplane = cursor.fetchone()

                if not airplane:
                    return f"Given airplane was not found."

                # looking for existing maintenenace procedure at the same time
                query_maintenance = """
                    SELECT * 
                    FROM Maintenance_Procedure
                    WHERE Airplane_ID = %s 
                      AND Airline_Name = %s 
                      AND (
                        (%s BETWEEN Start_Date AND End_Date) 
                        OR (%s BETWEEN Start_Date AND End_Date)
                      )
                """
                cursor.execute(query_maintenance, (
                    airplane_id, airline_name, 
                    start_date, end_date
                ))
                existing = cursor.fetchone()

                if existing:
                    return f"Airplane is already scheduled for maintenance during the given dates."

                # insert into maintenance procedure
                query_insert_maintenance = """
                    INSERT INTO Maintenance_Procedure (
                        Airline_Name, Airplane_ID, Start_Date, Start_Time, End_Date, End_Time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_insert_maintenance, (
                    airline_name, airplane_id, 
                    start_date, start_time, 
                    end_date, end_time
                ))
                conn.commit()

            except Exception as e:
                conn.rollback()
                return f"Unable to schedule maintenance: {str(e)}"

        return render_template('schedule_maintenance.html', airline_name=airline_name)

    except Exception as e:
        return f"Error: {str(e)}"

    finally:
        cursor.close()

# adding additional emails and phones fro airline staff
@app.route('/add_staff_contact', methods=['GET', 'POST'])
def add_staff_contact():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')

        try:
            if email:
                query_email = """
                        INSERT INTO Airline_Staff_Email (Username, Email)
                        VALUES (%s, %s)
                    """
                cursor.execute(query_email, (username, email))
            
            if phone: 
                query_phone = """
                        INSERT INTO Airline_Staff_Phone (Username, Phone)
                        VALUES (%s, %s)
                    """    
                cursor.execute(query_phone, (username, phone))

            conn.commit()

        except Exception as e:
            conn.rollback()
            return "error occuered"

        finally:
            cursor.close()

    return render_template('add_staff_contact.html')    


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