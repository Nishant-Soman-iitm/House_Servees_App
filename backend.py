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

@app.route('/add_service', methods=['POST'])
def add_service():
    name = request.form['name']

    with Session(engine) as sess:
        new_service = service(name=name)
        sess.add(new_service)
        try:
            sess.commit()
            flash("Service added successfully!")
        except IntegrityError:
            sess.rollback()
            flash("Error: Could not add service. Please try again.")
    return redirect(url_for('admin_dashboard'))


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