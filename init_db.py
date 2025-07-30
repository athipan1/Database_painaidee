#!/usr/bin/env python3
"""
Database initialization script.
Creates the database tables if they don't exist.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize the database with required tables."""
    try:
        from app import create_app
        from app.models import db
        
        # Create app
        app = create_app()
        
        print("🔧 Initializing database...")
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test database connection
            result = db.session.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Database connection verified")
            else:
                print("❌ Database connection test failed")
                return False
            
            print("🎉 Database initialization completed!")
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)