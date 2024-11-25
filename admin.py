from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, Service_Request,service,Booking,Slots,engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os, bcrypt
from app import app
from backend import *
from customer import *
from professional import *

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
        all_services=sess.query(service).all()

    # Pass data to the template
    return render_template('admin_dashboard.html', customers=all_customers, professionals=all_professionals, services=all_services)
