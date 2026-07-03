# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import timedelta
import config
from database import Database

app = Flask(__name__)
app.secret_key = config.Config.SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=24)

# Initialize database
db = Database()

@app.route('/')
def index():
    # Check if user is logged in
    if 'user_id' in session:
        if db.connect():
            user = db.get_user_by_id(session['user_id'])
            db.disconnect()
            if user:
                return render_template('index.html', user=user, logged_in=True)
    return render_template('index.html', logged_in=False)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        flash('Thank you for contacting us! We will respond within 24 hours.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to index
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')
        
        # Connect to database
        if not db.connect():
            flash('Database connection error. Please make sure XAMPP MySQL is running.', 'danger')
            return render_template('login.html')
        
        try:
            # Authenticate user
            user, error = db.authenticate_user(username, password)
            
            if user:
                # Set session
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session['user_email'] = user['email']
                session['user_first_name'] = user['first_name']
                session.permanent = True
                
                flash(f'Welcome back, {user["first_name"]}!', 'success')
                
                # Redirect to index page
                return redirect(url_for('index'))
            else:
                flash(error or 'Invalid username or password. Please try again.', 'danger')
                
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
        finally:
            db.disconnect()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If user is already logged in, redirect to index
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        first_name = request.form.get('fname', '').strip()
        last_name = request.form.get('lname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('mobile', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Connect to database
        if not db.connect():
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('signup.html', 
                                 username=username, fname=first_name, 
                                 lname=last_name, email=email, mobile=phone)
        
        try:
            # Validate username
            is_valid, message = db.validate_username(username)
            if not is_valid:
                flash(message, 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
            
            # Validate first name
            if not first_name or len(first_name) < 2:
                flash('First name must be at least 2 characters', 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
            
            # Validate last name
            if not last_name or len(last_name) < 2:
                flash('Last name must be at least 2 characters', 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
            
            # Validate email
            is_valid, message = db.validate_email(email)
            if not is_valid:
                flash(message, 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
            
            # Validate password
            is_valid, message = db.validate_password(password)
            if not is_valid:
                flash(message, 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
            
            # Check if passwords match
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
            
            # Create user
            user_data = {
                'username': username,
                'fname': first_name,
                'lname': last_name,
                'email': email,
                'mobile': phone,
                'password': password
            }
            
            success, message, user_id = db.create_user(user_data)
            
            if success:
                flash('Registration successful! Please login to continue.', 'success')
                db.disconnect()
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
                db.disconnect()
                return render_template('signup.html', 
                                     username=username, fname=first_name, 
                                     lname=last_name, email=email, mobile=phone)
                
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            db.disconnect()
            return render_template('signup.html', 
                                 username=username, fname=first_name, 
                                 lname=last_name, email=email, mobile=phone)
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    # Get user data
    if not db.connect():
        flash('Database connection error. Please try again.', 'danger')
        return redirect(url_for('index'))
    
    try:
        user = db.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            flash('User not found. Please login again.', 'danger')
            return redirect(url_for('login'))
        return render_template('profile.html', user=user)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))
    finally:
        db.disconnect()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('fname'),
            'last_name': request.form.get('lname'),
            'email': request.form.get('email'),
            'phone': request.form.get('mobile')
        }
        
        if not db.connect():
            flash('Database connection error.', 'danger')
            return redirect(url_for('profile'))
        
        try:
            success, message = db.update_user(session['user_id'], data)
            if success:
                # Update session name
                user = db.get_user_by_id(session['user_id'])
                if user:
                    session['user_name'] = f"{user['first_name']} {user['last_name']}"
                    session['user_first_name'] = user['first_name']
                flash(message, 'success')
            else:
                flash(message, 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
        finally:
            db.disconnect()
        
        return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
def change_password():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('profile'))
        
        if not db.connect():
            flash('Database connection error.', 'danger')
            return redirect(url_for('profile'))
        
        try:
            success, message = db.change_password(session['user_id'], old_password, new_password)
            flash(message, 'success' if success else 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
        finally:
            db.disconnect()
        
        return redirect(url_for('profile'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=config.Config.DEBUG, host='0.0.0.0', port=5000)