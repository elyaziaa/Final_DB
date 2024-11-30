from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib  # for MD5 hashing suggested in part 3

app = Flask(__name__)
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='nov28',
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

        # Check if user is logged in
        if 'email' not in session:
            return "Please log in first", 401

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
            return "Sorry, this flight is not available", 400

        # Step 3: Get Customer Details
        # Retrieve customer information from database
        cursor.execute("""
            SELECT Date_of_Birth, First_Name, Last_Name
            FROM Customer 
            WHERE Email = %s
        """, (email,))
        customer = cursor.fetchone()

        if not customer:
            return "Customer profile not found", 400

        # Step 4: Check Seat Availability
        cursor.execute("""
            SELECT Is_Available FROM Seat_Availability 
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (flight_num, seat_number))
        seat = cursor.fetchone()

        if not seat or not seat['Is_Available']:
            return "Sorry, this seat is already taken", 400

        # Step 5: Validate Payment Method
        cursor.execute("""
            SELECT Card_Number FROM Payment_Info pi
            JOIN Booked b ON pi.Card_Number = b.Payment_Card_Number
            WHERE b.Email = %s AND pi.Card_Number = %s
        """, (email, card_number))
        payment_card = cursor.fetchone()

        if not payment_card:
            return "Invalid payment method", 400

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



# Logout route
@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/')

app.secret_key = 'some key that you will never guess'

# Run the app on localhost port 5000
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
