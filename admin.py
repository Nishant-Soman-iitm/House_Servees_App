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


@app.route('/add_service', methods=['POST'])
def add_service():
    if not session.get('admin_access'):
        return redirect(url_for('admin_page'))  # Redirect to admin page if no access

    name = request.form['name']
    base_price = request.form['base_price']

    with Session(engine) as sess:
        new_service = service(name=name, base_price=base_price)
        sess.add(new_service)
        try:
            sess.commit()
            flash("Service added successfully.")
        except IntegrityError:
            sess.rollback()
            flash("Error occurred while adding the service. Please try again.")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if request.method == 'POST':
        if request.form.get('secret_key') == app.secret_key:
            session['admin_access'] = True  # Grant access to the admin dashboard
            return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
        else:
            return render_template('admin_page.html', error='Invalid Secret Key')
    return render_template('admin_page.html')


@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    if not session.get('admin_access'):
        return redirect(url_for('admin_page'))  # Redirect to admin page if no access

    with Session(engine) as sess:
        service_to_delete = sess.query(service).filter_by(id=service_id).first()
        if service_to_delete:
            professionals = sess.query(Professional_details).filter_by(profession=service_to_delete.name).all()
            for professional in professionals:
                # Notify professionals about the service deletion
                flash(f"Service '{service_to_delete.name}' has been deleted. Please choose another service or remove your account.")
                # You can also send an email notification here if needed

            sess.delete(service_to_delete)
            try:
                sess.commit()
                flash("Service deleted successfully.")
            except IntegrityError:
                sess.rollback()
                flash("Error occurred while deleting the service. Please try again.")
        else:
            flash("Service not found.")
    
    return redirect(url_for('admin_dashboard'))
    
    return redirect(url_for('admin_dashboard'))

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


@app.route('/admin/authenticate_users', methods=['GET', 'POST'])
def authenticate_users():
    if not session.get('admin_access'):
        return redirect(url_for('admin_page'))  # Redirect to admin page if no access

    with Session(engine) as sess:
        customers = sess.query(Customer_Details).all()
        professionals = sess.query(Professional_details).all()

    return render_template('authenticate_users.html', customers=customers, professionals=professionals)

@app.route('/admin/update_user_status/<user_type>/<email>', methods=['POST'])
def update_user_status(user_type, email):
    if not session.get('admin_access'):
        return redirect(url_for('admin_page'))  # Redirect to admin page if no access

    new_status = request.form['status']

    with Session(engine) as sess:
        if user_type == 'customer':
            user = sess.query(Customer_Details).filter_by(Email=email).first()
        elif user_type == 'professional':
            user = sess.query(Professional_details).filter_by(Email=email).first()

        if user:
            user.status = new_status
            sess.commit()
            flash(f"User status updated to {new_status}.")
        else:
            flash("User not found.")

    return redirect(url_for('authenticate_users'))