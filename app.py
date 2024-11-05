from flask import Flask, render_template, request, redirect, url_for, session

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
    return render_template('admin_dashboard.html')  # Create this template for the dashboard

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        # Handle customer login logic here
        pass
    return render_template('customer_login.html')

@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        # Handle customer registration logic here
        pass
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
        # Handle professional registration logic here
        pass
    return render_template('professional_register.html')

@app.route('/logout')
def logout():
    session.pop('admin_access', None)  # Remove session variable
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
