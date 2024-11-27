from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, Service_Request,service,Booking,Slots,JobReview
from db_init import engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os, bcrypt
from app import app
from backend import *
from professional import *
from admin import *
import re

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    with Session(engine) as sess:
        bookings = sess.query(Booking).filter_by(customer_email=session['user_id']).all()

    return render_template('my_bookings.html', bookings=bookings)
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


@app.route('/customer_profile/<username>', methods=['GET', 'POST'])
def customer_profile(username):
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        city = request.form['city']
        aadhaar = request.form['aadhaar']

        # Validate Aadhaar card format (12 digits)
        if not re.match(r'^\d{12}$', aadhaar):
            flash("Invalid Aadhaar card number. It should be a 12-digit number.")
            return redirect(url_for('customer_profile', username=username))

        with Session(engine) as sess:
            customer = sess.query(Customer_Details).filter_by(Email=username).first()
            if customer:
                customer.name = name
                customer.phone = phone
                customer.city = city
                customer.aadhaar = aadhaar
                sess.commit()
                flash("Profile updated successfully.")
            else:
                flash("Customer not found.")
            return redirect(url_for('customer_profile', username=username))
    
    return render_template('customer_profile.html')


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


@app.route('/submit_review/<int:booking_id>', methods=['GET', 'POST'])
def submit_review(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    if request.method == 'POST':
        review_text = request.form['review_text']
        rating = request.form['rating']

        with Session(engine) as sess:
            new_review = JobReview(booking_id=booking_id, review_text=review_text, rating=rating)
            sess.add(new_review)
            booking = sess.query(Booking).filter_by(booking_id=booking_id).first()
            booking.payment_status = 'Completed'
            sess.commit()
            flash("Review submitted and payment completed.")
            return redirect(url_for('customer_portal', username=session['user_id']))

    return render_template('submit_review.html', booking_id=booking_id)

@app.route('/make_payment/<int:booking_id>', methods=['POST'])
def make_payment(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    with Session(engine) as sess:
        booking = sess.query(Booking).filter_by(booking_id=booking_id).first()
        if booking:
            booking.payment_status = '40% Paid'
            sess.commit()
            flash("40% payment made successfully. The professional can now start the job.")
        else:
            flash("Booking not found.")

    return redirect(url_for('my_bookings'))