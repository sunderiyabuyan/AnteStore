import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ante1213$')
    
    # Handle different PostgreSQL drivers
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Replace postgres:// with postgresql:// if needed
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        # Add SSL mode for production
        if 'postgresql://' in DATABASE_URL and 'sslmode' not in DATABASE_URL:
            DATABASE_URL += '?sslmode=require'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    ITEMS_PER_PAGE = 50
    LOW_STOCK_THRESHOLD = 10
    
    # Production settings
    DEBUG = os.environ.get('FLASK_ENV') != 'production'