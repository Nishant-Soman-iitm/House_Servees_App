from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_init import Customer_Details, Professional_details, Service_Request,service,Booking,Slots,engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import os, bcrypt

app = Flask(__name__)
app.secret_key = '0309'  # Set the secret key


from backend import *
from admin import *
from customer import *
from professional import *


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
