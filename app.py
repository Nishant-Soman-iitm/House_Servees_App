from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os

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

            if user and user.password == password:  # If user exists and password matches
                # Set the session for the logged-in user
                session['user_id'] = user.Email
                return redirect(url_for('customer_portal', username=user.Email))  # Redirect to customer portal page
            else:
                flash("Invalid username or password. Please try again.")  # Flash error message

        return render_template('customer_login.html')  # Render login page again if login failed

    return render_template('customer_login.html')

@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['pass']
        
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
                new_customer = Customer_Details(Email=username, password=password)
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

@app.route('/customer/portal/<username>')
def customer_portal(username):
    # Logic to handle the customer portal page
    return render_template('customer_portal.html', username=username)


############################################################################################################################################################################

@app.route('/professional/login', methods=['GET', 'POST'])
def professional_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with Session(engine) as sess:
            # Check if the username exists in the database
            professional = sess.query(Professional_details).filter_by(Email=username).first()

            if professional and professional.password == password:  # If user exists and password matches
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
        
        with Session(engine) as sess:
            # Check if username already exists
            existing_user = sess.query(Professional_details).filter_by(Email=username).first()
            if existing_user:
                # If user exists, flash a message and reload registration page
                flash("Username already exists. Please log in.")
                return redirect(url_for('professional_register'))

            # If user does not exist, add new customer to the database
            new_professional = Professional_details(Email=username, password=password, profession=profession)
            sess.add(new_professional)
            
            try:
                sess.commit()
            except IntegrityError as e:
                sess.rollback()  # Rollback on error
                flash("Error: Username already exists.")
                return redirect(url_for('professional_register'))
        
        flash("Registration successful! Please log in.")
        return redirect(url_for('professional_login'))
    
    return render_template('professional_register.html')

@app.route('/professional/portal/<username>')
def professional_portal(username):
    # Retrieve the logged-in professional's email (username) from the session
    professional_email = session.get('professional_id')

    if not professional_email:
        flash("You must be logged in to access the professional portal.")
        return redirect(url_for('professional_login'))

    with Session(engine) as sess:
        # Fetch the professional details from the database
        professional = sess.query(Professional_details).filter_by(Email=professional_email).first()

        if professional:
            # Fetch the professional's profession and pass it to the template
            profession = professional.profession
            return render_template('professional_portal.html', username=professional.Email, profession=profession)
        else:
            flash("Professional not found.")
            return redirect(url_for('professional_login'))

############################################################################################################################################################################

@app.route('/logout')
def logout():
    # Clear all session variables for any logged-in user
    session.pop('admin_access', None)
    session.pop('user_id', None)
    session.pop('professional_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
