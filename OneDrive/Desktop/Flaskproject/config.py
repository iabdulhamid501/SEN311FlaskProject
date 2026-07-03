# config.py
class Config:
    # MySQL Configuration for XAMPP
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Leave empty for XAMPP default
    MYSQL_DB = 'loft_city_db'
    MYSQL_PORT = 3306
    
    # Secret key for sessions
    SECRET_KEY = 'your-secret-key-here-change-in-production'
    
    # Application settings
    DEBUG = True
    TESTING = False