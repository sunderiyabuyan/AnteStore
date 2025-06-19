import os
from app import create_app, db
from app.models.user import User

def setup_database():
    """Setup database tables and admin user"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"❌ An error occurred while creating database tables: {e}")
            
            # Create admin user if it doesn't exist
            existing_admin = User.query.filter_by(username='Ante').first()
            if not existing_admin:
                print("Creating admin user...")
                admin = User(
                    username='Ante',
                    email='sunderiyabuyan@gmail.com'
                )
                admin.set_password('AnteDB1213$')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created successfully!")
            else:
                print("⚠️ Admin user 'Ante' already exists!")
            print("🔐 Login credentials:")