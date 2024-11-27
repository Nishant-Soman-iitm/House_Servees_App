from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, Service_Request,service,Booking,Slots,engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os, bcrypt
from app import app
from admin import *
from customer import *
from professional import *

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    slot_time = request.args.get('time')
    slot_date = request.args.get('date')

    if request.method == 'POST':
        # Handle payment logic here
        flash("Payment successful! Slot booked.")
        return redirect(url_for('customer_portal', username=session['user_id']))

    return render_template('checkout.html', slot_time=slot_time, slot_date=slot_date)


@app.route('/avail_services')
def avail_services():
    with Session(engine) as sess:
        services = sess.query(service).all()
    return render_template('avail_services.html', services=services)



@app.route('/logout')
def logout():
    # Clear all session variables for any logged-in user
    session.pop('admin_access', None)
    session.pop('user_id', None)
    session.pop('professional_id', None)
    return redirect(url_for('home'))

@app.route('/update_booking_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('customer_login'))  # Redirect to login if not logged in

    new_status = request.form['status']

    with Session(engine) as sess:
        booking = sess.query(Booking).filter_by(booking_id=booking_id).first()
        if booking:
            booking.status = new_status
            sess.commit()
            flash("Booking status updated successfully.")
        else:
            flash("Booking not found.")

    return redirect(url_for('my_bookings'))