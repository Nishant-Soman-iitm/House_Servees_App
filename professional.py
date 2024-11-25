from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, Service_Request,service,Booking,Slots,engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os, bcrypt
from app import app
from backend import *
from admin import *
from customer import *


@app.route('/reg_prof')
def reg_prof():
    return render_template('professional_register.html')

@app.route('/register_professional', methods=['GET', 'POST'])
def register_professional():
    if request.method == 'POST':
        username = request.form['username']
        profession = request.form['profession']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        with Session(engine) as sess:
            existing_user = sess.query(Professional_details).filter_by(Email=username).first()
            if existing_user:
                flash("Username already exists. Please log in.")
                return redirect(url_for('professional_login'))

            # Check if the profession exists in the services table
            service_exists = sess.query(service).filter_by(name=profession).first()
            if not service_exists:
                flash("Service does not exist.")
                return redirect(url_for('register_professional'))

            new_professional = Professional_details(Email=username, password=hashed_password, profession=profession)
            sess.add(new_professional)
            try:
                sess.commit()
                flash("Registration successful! Please log in.")
                return redirect(url_for('professional_login'))
            except IntegrityError:
                sess.rollback()
                flash("Error occurred during registration. Please try again.")
    
    # Fetch services for radio buttons
    with Session(engine) as sess:
        services = sess.query(service).all()

    return render_template('professional_register.html', services=services)

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