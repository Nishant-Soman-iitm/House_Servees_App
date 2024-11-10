from flask import Flask, render_template, request, redirect, url_for, session, flash,get_flashed_messages
from db_init import Customer_Details, Professional_details, engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = '0309'  # Set the secret key

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if request.method == 'POST':
        if request.form.get('secret_key') == app.secret_key:
            session['admin_access'] = True  # Set session variable
            return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
        else:
            return render_template('admin_page.html', error='Invalid Secret Key')
    return render_template('admin_page.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_access'):
        return redirect(url_for('admin_page'))  # Redirect to admin page if no access
    return render_template('admin_dashboard.html')

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with Session(engine) as sess:
            # Check if the username exists in the database
            user = sess.query(Customer_Details).filter_by(Email=username).first()

            if user and user.password == password:  # If user exists and password matches
                # Set the session for the logged-in user
                session['user_id'] = user.Email
                print(1)
                return redirect(url_for('customer_portal'))  # Redirect to customer portal page
            else:
                flash("Invalid username or password. Please try again.")  # Flash error message
                print(2)
        print(3)
        return render_template('customer_login.html')  # Render login page again if login failed
    print(4)

    return render_template('customer_login.html')

@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print("Username:", username)
        print("Password:", password)
        
        # Start a session to interact with the database
        try:
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
                sess.commit()  # Commit the transaction to save changes
                flash("Registration successful! Please log in.")
                
            return redirect(url_for('customer_login'))  # Redirect to login after successful registration

        except IntegrityError:
            # Catch specific database errors
            flash("Database integrity error. Username might already exist.")
            return redirect(url_for('customer_register'))

        except Exception as e:
            # Catch any other errors, log, and flash message
            print(f"Error occurred: {e}")
            flash("An error occurred while registering. Please try again.")
            return redirect(url_for('customer_register'))

    return render_template('customer_register.html')

@app.route('/professional/login', methods=['GET', 'POST'])
def professional_login():
    if request.method == 'POST':
        # Handle professional login logic here
        pass
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

@app.route('/logout')
def logout():
    session.pop('admin_access', None)  # Corrected to use Flask's session
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
