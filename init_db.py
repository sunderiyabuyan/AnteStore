#!/usr/bin/env python3
"""
Simple database initialization script for Railway
"""

print("🚀 Starting database initialization...")

try:
    # Import Flask app and database
    from app import create_app, db
    print("✅ Flask app imported")
    
    # Import all models to register them
    from app.models.user import User
    from app.models.products import Product  
    from app.models.sales import Sale, SalesItem
    print("✅ Models imported")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        print("🔧 Creating database tables...")
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if admin user exists
        existing_admin = User.query.filter_by(username='Ante').first()
        
        if existing_admin:
            print("✅ Admin user 'Ante' already exists!")
        else:
            print("🔧 Creating admin user...")
            
            # Create admin user
            admin = User(
                username='Ante',
                email='sunderiyabuyan@gmail.com'
            )
            admin.set_password('AnteDB1213$')
            
            # Save to database
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
        
        print("=" * 50)
        print("🎉 DATABASE SETUP COMPLETE!")
        print("🔐 Login credentials:")
        print("   Username: Ante")
        print("   Password: AnteDB1213$")
        print("   Email: sunderiyabuyan@gmail.com")
        print("=" * 50)
        print("🌐 Your app is now ready to use!")
        
except Exception as e:
    print(f"❌ Error during database setup: {e}")
    import traceback
    traceback.print_exc()
    exit(1)