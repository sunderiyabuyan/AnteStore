"""
Force Database Table Creation Script
This will create all tables and verify they exist
"""
from app import create_app, db
from app.models.user import User
from app.models.products import Product
from app.models.sales import Sale, SalesItem

def force_create_tables():
    """Force create all database tables"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Starting database table creation...")
        
        try:
            # Test database connection first
            print("📡 Testing database connection...")
            result = db.engine.execute('SELECT 1 as test')
            test_result = result.fetchone()[0]
            if test_result == 1:
                print("✅ Database connection successful!")
            
            # Show current database URL (masked)
            db_url = str(db.engine.url)
            if 'postgresql' in db_url:
                print(f"🗄️ Connected to PostgreSQL database")
            else:
                print(f"🗄️ Connected to: {db_url}")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        try:
            # Import all models to ensure they're registered
            print("📋 Importing all models...")
            from app.models.user import User
            from app.models.products import Product 
            from app.models.sales import Sale, SalesItem
            
            # Check what tables exist before creation
            print("🔍 Checking existing tables...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"   Existing tables: {existing_tables}")
            
            # Force create all tables
            print("🔨 Creating all database tables...")
            db.create_all()
            
            # Verify tables were created
            print("✅ Verifying table creation...")
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"   Created tables: {tables}")
            
            # Check specific tables we need
            required_tables = ['users', 'products', 'sales', 'sales_items']
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    print(f"   ✅ {table} table exists")
                else:
                    print(f"   ❌ {table} table missing")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"⚠️ Missing tables: {missing_tables}")
                return False
            else:
                print("🎉 All required tables created successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            return False

def create_admin_user():
    """Create admin user after tables are created"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if admin already exists
            existing_admin = User.query.filter_by(username='Ante').first()
            if existing_admin:
                print("⚠️ Admin user 'Ante' already exists!")
                print(f"   Email: {existing_admin.email}")
                print(f"   Created: {existing_admin.created_at}")
                return True
            
            # Create admin user
            print("👤 Creating admin user...")
            admin = User(
                username='Ante',
                email='sunderiyabuyan@gmail.com'
            )
            admin.set_password('AnteDB1213$')
            admin.save()
            
            print("✅ Admin user created successfully!")
            print("=" * 50)
            print("🔐 LOGIN CREDENTIALS:")
            print("   Username: Ante")
            print("   Password: AnteDB1213$")
            print("   Email: sunderiyabuyan@gmail.com")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function to set up everything"""
    print("🚀 Database Setup Script")
    print("=" * 60)
    
    # Step 1: Create tables
    if not force_create_tables():
        print("❌ Failed to create tables. Exiting.")
        return
    
    # Step 2: Create admin user
    if not create_admin_user():
        print("❌ Failed to create admin user. But tables exist.")
        return
    
    print("=" * 60)
    print("🎉 Database setup completed successfully!")
    print("🌐 You can now access your Railway app and log in!")

if __name__ == '__main__':
    main()