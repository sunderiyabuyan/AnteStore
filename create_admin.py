import os
import sys
from app import create_app, db
from app.models.user import User

def create_admin_user():
    """Create admin user for production"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if admin already exists
            existing_admin = User.query.filter_by(username='Ante').first()
            if existing_admin:
                print("✅ Ante user already exists!")
                return
            
            # Create admin user
            admin = User(
                username='Ante',
                email='sunderiyabuyan@gmail.com'
            )
            admin.set_password('AnteDB1213$')
            admin.save()
            
            print("✅ Admin user created successfully!")
            print("🔐 Login credentials:")
            print("   Username: Ante")
            print("   Password: AnteDB1213!")
            print("⚠️  Change password after first login!")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")

if __name__ == '__main__':
    create_admin_user()