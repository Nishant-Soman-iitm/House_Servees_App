from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, Service_Request,service,Booking,Slots,engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os, bcrypt

app = Flask(__name__)
app.secret_key = '0309'  # Set the secret key


############################################################################################################################################################################
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if request.method == 'POST':
        if request.form.get('secret_key') == app.secret_key:
            session['admin_access'] = True  # Grant access to the admin dashboard
            return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
        else:
            return render_template('admin_page.html', error='Invalid Secret Key')
    return render_template('admin_page.html')

'''@app.route('/customer/slots/<professional_email>', methods=['GET'])
def fetch_slots(professional_email):
    with Session(engine) as sess:
        slots = sess.query(slots).filter_by(professional_id=professional_email).all()
    return render_template('slots_modal.html', slots=slots)'''

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_access'):
        return redirect(url_for('admin_page'))  # Redirect to admin page if no access

    with Session(engine) as sess:
        # Fetch all customer and professional details
        all_customers = sess.query(Customer_Details).all()
        all_professionals = sess.query(Professional_details).all()

    # Pass data to the template
    return render_template('admin_dashboard.html', customers=all_customers, professionals=all_professionals)


############################################################################################################################################################################

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['pass']
        
        with Session(engine) as sess:
            # Check if the username exists in the database
            user = sess.query(Customer_Details).filter_by(Email=username).first()

            # Verify that the user exists and the password matches
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
                # Set the session for the logged-in user
                session['user_id'] = user.Email
                return redirect(url_for('customer_portal', username=user.Email))  # Redirect to customer portal
            else:
                flash("Invalid username or password. Please try again.")  # Flash error message

        return render_template('customer_login.html')  # Render login page again if login failed

    return render_template('customer_login.html')

@app.route('/customer/profile/<username>', methods=['GET', 'POST'])
def customer_profile(username):
    if not session.get('user_id'):
        flash("Please log in to access this page.")
        return redirect(url_for('customer_login'))

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        city = request.form['city']
        
        with Session(engine) as sess:
            # Fetch the logged-in customer's profile
            customer = sess.query(Customer_Details).filter_by(Email=username).first()

            if customer:
                # Update the customer details
                customer.name = name
                customer.phone = phone
                customer.city = city

                try:
                    sess.commit()
                    flash("Profile updated successfully!")
                    return redirect(url_for('customer_portal', username=username))
                except Exception as e:
                    sess.rollback()
                    flash("Error updating profile. Please try again.")
            else:
                flash("Customer not found.")

    return render_template('customer_profile.html', username=username)



@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['pass']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            # Start a session to interact with the database
            with Session(engine) as sess:
                # Check if the username already exists
                existing_user = sess.query(Customer_Details).filter_by(Email=username).first()
                
                if existing_user:
                    # If user exists, flash a message and reload registration page
                    flash("Username already exists. Please log in.")
                    return redirect(url_for('customer_register'))

                # If user does not exist, create and add new customer to the database
                new_customer = Customer_Details(Email=username, password=hashed_password)
                sess.add(new_customer)
                
                try:
                    # Commit the transaction to save the new customer
                    sess.commit()
                except IntegrityError:
                    # Rollback in case of error and show message
                    sess.rollback()
                    flash("Error: Database integrity issue. Username might already exist.")
                    return redirect(url_for('customer_register'))
                
            flash("Registration successful! Please log in.")  # Success message
            return redirect(url_for('customer_login'))  # Redirect to login page after success

        except Exception as e:
            # Catch any other errors, log, and show an error message
            flash("An error occurred while registering. Please try again.")
            return redirect(url_for('customer_register'))  # Reload registration page

    return render_template('customer_register.html')

from datetime import datetime, timedelta

@app.route('/customer/portal/<username>', methods=['GET', 'POST'])
def customer_portal(username):
    if not session.get('user_id'):
        flash("Please log in to access your portal.")
        return redirect(url_for('customer_login'))
    
    with Session(engine) as sess:
        customer = sess.query(Customer_Details).filter_by(Email=username).first()
        if not customer:
            flash("Customer not found.")
            return redirect(url_for('customer_login'))

        # Fetch all available professionals
        professionals = sess.query(Professional_details).filter_by(availability=True).all()

        # Date range for next 3 days
        today = datetime.now().date()
        min_date = today
        max_date = today + timedelta(days=3)

    return render_template('customer_portal.html', username=username, professionals=professionals, min_date=min_date, max_date=max_date)



############################################################################################################################################################################

@app.route('/professional/login', methods=['GET', 'POST'])
def professional_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with Session(engine) as sess:
            # Check if the username exists in the database
            professional = sess.query(Professional_details).filter_by(Email=username).first()

            if professional and bcrypt.checkpw(password.encode('utf-8'), professional.password):  # If user exists and password matches
                # Set the session for the logged-in professional
                session['professional_id'] = professional.Email
                return redirect(url_for('professional_portal', username=professional.Email))  # Redirect to professional portal page
            else:
                flash("Invalid username or password. Please try again.")  # Flash error message

        return render_template('professional_login.html')  # Render login page again if login failed

    return render_template('professional_login.html')

@app.route('/professional/register', methods=['GET', 'POST'])
def professional_register():
    if request.method == 'POST':
        username = request.form['username']
        profession = request.form['profession']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        with Session(engine) as sess:
            # Check if username already exists
            print(f"Checking if username {username} exists")  # Debugging line
            existing_user = sess.query(Professional_details).filter_by(Email=username).first()
            
            if existing_user:
                print(f"User found with username: {existing_user.Email}")  # Debugging line
                flash("Username already exists. Please log in.")
                return redirect(url_for('professional_register'))

            print("Creating new professional account.")  # Debugging line
            # If user does not exist, add new professional to the database
            new_professional = Professional_details(Email=username, password=hashed_password, profession=profession)
            sess.add(new_professional)
            
            try:
                sess.commit()
            except IntegrityError as e:
                sess.rollback()  # Rollback on error
                print(f"Error: {e}")  # Debugging line
                flash("Error: Username already exists.")
                return redirect(url_for('professional_register'))
        
        flash("Registration successful! Please log in.")
        return redirect(url_for('professional_login'))
    
    return render_template('professional_register.html')


@app.route('/professional/portal/<username>', methods=['GET', 'POST'])
def professional_portal(username):
    # Retrieve the logged-in professional's email (username) from the session
    professional_email = session.get('professional_id')

    if not professional_email:
        flash("You must be logged in to access the professional portal.")
        return redirect(url_for('professional_login'))

    with Session(engine) as sess:
        # Fetch the professional details from the database
        professional = sess.query(Professional_details).filter_by(Email=professional_email).first()

        if not professional:
            flash("Professional not found.")
            return redirect(url_for('professional_login'))

        # Fetch the professional's profession
        profession = professional.profession
        
        # Fetch service requests that are "Pending" for the professional
        service_requests = sess.query(Service_Request).filter_by(
            professional_email=professional_email, status="Pending"
        ).all()

    # Render the professional portal template with service requests
    return render_template('professional_portal.html', 
                           username=professional.Email, 
                           profession=profession, 
                           service_requests=service_requests)

        




############################################################################################################################################################################

@app.route('/book_slot', methods=['POST'])
def book_slot():
    professional_email = request.form['professional_email']
    slot_date = request.form['date']
    slot_time = request.form['slot_time']

    with Session(engine) as sess:
        # Save the booking in the database
        new_request = Service_Request(
            professional_email=professional_email,
            customer_email=session.get('user_id'),
            slot_date=slot_date,
            slot_time=slot_time,
            status="Pending"
        )
        sess.add(new_request)
        sess.commit()

    flash("Slot booked successfully! Wait for confirmation.")
    return redirect(url_for('customer_portal', username=session.get('user_id')))



@app.route('/professional/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    with Session(engine) as sess:
        request = sess.query(Service_Request).get(request_id)
        if request:
            request.status = "Accepted"
            
            # Derive professional and customer emails from Service_Request
            professional_email = request.professional_email
            customer_email = request.customer_email
            slot_date = request.slot_date
            slot_time = request.slot_time

            # Create a new Booking object using the derived values
            new_booking = Booking(
                professional_email=professional_email,
                customer_email=customer_email,
                slot_date=slot_date,
                slot_time=slot_time,
                status="Confirmed"
            )
            sess.add(new_booking)

            # Update the status of the slot to mark it as booked
            slot = sess.query(Slots).filter_by(
                professional_email=professional_email, 
                slot_date=slot_date, 
                slot_time=slot_time
            ).first()
            if slot:
                slot.is_booked = True  # Mark the slot as booked
            sess.commit()
            flash("Request accepted and slot confirmed!")
            return redirect(url_for('professional_portal', username=professional_email))



@app.route('/professional/reject_request/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    with Session(engine) as sess:
        request = sess.query(Service_Request).get(request_id)
        if request:
            request.status = "Rejected"
            sess.commit()
            flash("Request rejected.")
            return redirect(url_for('professional_portal', username=request.professional_email))




############################################################################################################################################################################
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    slot_time = request.args.get('time')
    slot_date = request.args.get('date')

    if request.method == 'POST':
        # Handle payment logic here
        flash("Payment successful! Slot booked.")
        return redirect(url_for('customer_portal', username=session['user_id']))

    return render_template('checkout.html', slot_time=slot_time, slot_date=slot_date)

@app.route('/logout')
def logout():
    # Clear all session variables for any logged-in user
    session.pop('admin_access', None)
    session.pop('user_id', None)
    session.pop('professional_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
