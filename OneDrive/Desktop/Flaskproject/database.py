# database.py
import mysql.connector
from mysql.connector import Error
import hashlib
import re
from datetime import datetime
import config

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection to XAMPP MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=config.Config.MYSQL_HOST,
                user=config.Config.MYSQL_USER,
                password=config.Config.MYSQL_PASSWORD,
                database=config.Config.MYSQL_DB,
                port=config.Config.MYSQL_PORT,
                use_pure=True,
                auth_plugin='mysql_native_password'
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Connected to XAMPP MySQL database")
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            print("Make sure XAMPP MySQL is running on port 3306")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.lastrowid
        except Error as e:
            print(f"❌ Error executing query: {e}")
            return None
    
    def hash_password(self, password):
        """Hash password using SHA-256 with salt"""
        salt = "loft_city_salt_2024"
        return hashlib.sha256((salt + password).encode()).hexdigest()
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def validate_username(self, username):
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 20:
            return False, "Username must be 3-20 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""
    
    def validate_email(self, email):
        """Validate email format"""
        if not email:
            return False, "Email is required"
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format"
        return True, ""
    
    def validate_password(self, password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        if len(password) > 30:
            return False, "Password must be less than 30 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        return True, ""
    
    def create_user(self, user_data):
        """Create a new user in the database"""
        try:
            # Validate input data
            username = user_data.get('username', '').strip()
            first_name = user_data.get('fname', '').strip()
            last_name = user_data.get('lname', '').strip()
            email = user_data.get('email', '').strip()
            phone = user_data.get('mobile', '').strip() or None
            password = user_data.get('password', '')
            
            # Check if username already exists
            existing_user = self.get_user_by_username(username)
            if existing_user:
                return False, "Username already exists", None
            
            # Check if email already exists
            existing_email = self.get_user_by_email(email)
            if existing_email:
                return False, "Email already registered", None
            
            # Hash password
            hashed_password = self.hash_password(password)
            
            # Insert user
            query = """
                INSERT INTO tbl_user 
                (username, first_name, last_name, email, phone, password_hash) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (username, first_name, last_name, email, phone, hashed_password)
            user_id = self.execute_query(query, params)
            
            if user_id:
                return True, "User created successfully", user_id
            else:
                return False, "Failed to create user", None
                
        except Error as e:
            return False, f"Database error: {str(e)}", None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        query = "SELECT * FROM tbl_user WHERE username = %s"
        result = self.execute_query(query, (username,))
        return result[0] if result else None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        query = "SELECT * FROM tbl_user WHERE email = %s"
        result = self.execute_query(query, (email,))
        return result[0] if result else None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM tbl_user WHERE id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        user = self.get_user_by_username(username)
        if not user:
            return None, "Invalid username or password"
        
        # Check if user is active
        if not user.get('is_active', True):
            return None, "Account is deactivated"
        
        # Verify password
        if self.verify_password(password, user['password_hash']):
            # Update last login
            self.update_last_login(user['id'])
            return user, None
        else:
            return None, "Invalid username or password"
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        query = "UPDATE tbl_user SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
        self.execute_query(query, (user_id,))
    
    def update_user(self, user_id, data):
        """Update user information"""
        try:
            set_clauses = []
            params = []
            
            allowed_fields = ['first_name', 'last_name', 'email', 'phone']
            
            for field in allowed_fields:
                if field in data and data[field]:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field].strip())
            
            if not set_clauses:
                return False, "No fields to update"
            
            params.append(user_id)
            query = f"UPDATE tbl_user SET {', '.join(set_clauses)} WHERE id = %s"
            result = self.execute_query(query, params)
            
            if result is not None:
                return True, "User updated successfully"
            else:
                return False, "Failed to update user"
                
        except Error as e:
            return False, f"Database error: {str(e)}"
    
    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, message = self.validate_password(new_password)
        if not is_valid:
            return False, message
        
        # Hash and update new password
        hashed_password = self.hash_password(new_password)
        query = "UPDATE tbl_user SET password_hash = %s WHERE id = %s"
        result = self.execute_query(query, (hashed_password, user_id))
        
        if result is not None:
            return True, "Password changed successfully"
        else:
            return False, "Failed to change password"