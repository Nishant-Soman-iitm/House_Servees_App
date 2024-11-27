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
        username = request.form['username']
        password = request.form['password']

        with Session(engine) as sess:
            # Check if the username exists in the database
            customer = sess.query(Customer_Details).filter_by(Email=username).first()

            if customer and bcrypt.checkpw(password.encode('utf-8'), customer.password):  # If user exists and password matches
                if customer.status == 'Blocked':
                    flash("Your account is blocked. Please contact support.")
                    return render_template('customer_login.html')
                elif customer.status == 'Pending':
                    flash("Your account is pending approval. Please wait for admin approval.")
                    return render_template('customer_login.html')

                # Check if the profile is complete
                if not customer.name or not customer.phone or not customer.city or not customer.aadhaar:
                    session['user_id'] = customer.Email
                    flash("Please complete your profile before accessing the portal.")
                    return redirect(url_for('customer_profile', username=customer.Email))

                # Set the session for the logged-in customer
                session['user_id'] = customer.Email
                return redirect(url_for('customer_portal', username=customer.Email))  # Redirect to customer portal page
            else:
                flash("Invalid username or password. Please try again.")  # Flash error message

        return render_template('customer_login.html')  # Render login page again if login failed

    return render_template('customer_login.html')


@app.route('/customer_profile/<username>', methods=['GET', 'POST'])
def customer_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    with Session(engine) as sess:
        customer = sess.query(Customer_Details).filter_by(Email=username).first()

        if request.method == 'POST':
            customer.name = request.form['name']
            customer.phone = request.form['phone']
            customer.city = request.form['city']
            customer.aadhaar = request.form['aadhaar']
            sess.commit()
            flash("Profile updated successfully.")
            return redirect(url_for('customer_portal', username=username))

    return render_template('customer_profile.html', customer=customer)


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

@app.route('/customer_portal/<username>', methods=['GET', 'POST'])
def customer_portal(username):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    city = request.args.get('city', '')
    profession = request.args.get('profession', '')

    with Session(engine) as sess:
        query = sess.query(Professional_details)
        if city:
            query = query.filter_by(city=city)
        if profession:
            query = query.filter_by(profession=profession)
        professionals = query.all()

        # Calculate average rating for each professional
        for professional in professionals:
            reviews = sess.query(JobReview).join(Booking).filter(Booking.professional_email == professional.Email).all()
            if reviews:
                professional.average_rating = sum(review.rating for review in reviews) / len(reviews)
            else:
                professional.average_rating = 'No reviews yet'

        professionals = sorted(professionals, key=lambda p: p.average_rating, reverse=True)

    return render_template('customer_portal.html', username=username, professionals=professionals, city=city, profession=profession)


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


@app.route('/customer_profile_view/<username>', methods=['GET'])
def customer_profile_view(username):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    with Session(engine) as sess:
        customer = sess.query(Customer_Details).filter_by(Email=username).first()

    return render_template('customer_profile_view.html', customer=customer)

@app.route('/update_customer_profile/<username>', methods=['POST'])
def update_customer_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    with Session(engine) as sess:
        customer = sess.query(Customer_Details).filter_by(Email=username).first()
        customer.city = request.form['city']
        sess.commit()
        flash("City updated successfully.")
        return redirect(url_for('customer_profile_view', username=username))

@app.route('/reset_customer_password/<username>', methods=['POST'])
def reset_customer_password(username):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    new_password = request.form['new_password']
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    with Session(engine) as sess:
        customer = sess.query(Customer_Details).filter_by(Email=username).first()
        customer.password = hashed_password
        sess.commit()
        flash("Password reset successfully.")
        return redirect(url_for('customer_profile_view', username=username))