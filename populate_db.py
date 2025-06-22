
import os
import time
import sqlite3
from app import create_app, db
from app.models.user import User
from app.models.products import Product
from app.models.sales import Sale, SalesItem

def check_database_lock():
    """Check if database is locked and wait if necessary"""
    app = create_app()
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            conn.execute('BEGIN IMMEDIATE;')
            conn.rollback()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                retry_count += 1
                print(f"⚠️  Database is locked, waiting... (attempt {retry_count}/{max_retries})")
                time.sleep(2)
            else:
                raise e
    
    print("❌ Could not access database after multiple attempts")
    return False

def safe_operation(operation_func, operation_name):
    """Safely execute database operations with retry logic"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = operation_func()
            print(f"✅ {operation_name} completed successfully")
            return result
        except Exception as e:
            retry_count += 1
            if "database is locked" in str(e) and retry_count < max_retries:
                print(f"⚠️  {operation_name} failed, retrying... (attempt {retry_count}/{max_retries})")
                time.sleep(1)
                db.session.rollback()
            else:
                print(f"❌ {operation_name} failed: {str(e)}")
                db.session.rollback()
                raise e

def create_admin_user():
    """Create the admin user"""
    def _create():
        admin_user = User(
            username='admin',
            email='admin@store.com'
        )
        admin_user.set_password('StoreAdmin2025!')
        admin_user.save()
        return admin_user
    
    return safe_operation(_create, "Admin user creation")

def create_sample_products():
    """Create sample products"""
    def _create():
        sample_products = [
            Product(
                name='iPhone 15 Pro', 
                category='Electronics', 
                cost=800.00, 
                price=1199.99, 
                stock_level=25, 
                description='Latest iPhone Pro model with titanium design and A17 Pro chip'
            ),
            Product(
                name='MacBook Air M3', 
                category='Electronics', 
                cost=900.00, 
                price=1299.99, 
                stock_level=15, 
                description='Ultra-thin laptop with M3 chip and all-day battery life'
            ),
            Product(
                name='Nike Air Jordan 1', 
                category='Clothing', 
                cost=80.00, 
                price=170.00, 
                stock_level=8, 
                description='Classic basketball shoes in retro colorway'
            ),
            Product(
                name='Levi\'s 501 Jeans', 
                category='Clothing', 
                cost=35.00, 
                price=89.99, 
                stock_level=20, 
                description='Original straight leg jeans in classic blue denim'
            ),
            Product(
                name='Colombian Coffee Beans', 
                category='Food', 
                cost=12.00, 
                price=24.99, 
                stock_level=50, 
                description='Premium single-origin arabica coffee beans from Colombia'
            ),
            Product(
                name='Organic Green Tea', 
                category='Food', 
                cost=8.00, 
                price=18.99, 
                stock_level=30, 
                description='Certified organic loose leaf green tea from Japan'
            ),
            Product(
                name='Wireless Earbuds Pro', 
                category='Electronics', 
                cost=45.00, 
                price=99.99, 
                stock_level=40, 
                description='Noise-cancelling wireless earbuds with premium sound quality'
            ),
            Product(
                name='Ergonomic Laptop Stand', 
                category='Electronics', 
                cost=25.00, 
                price=49.99, 
                stock_level=15, 
                description='Adjustable aluminum laptop stand for improved ergonomics'
            ),
            Product(
                name='Bluetooth Wireless Mouse', 
                category='Electronics', 
                cost=18.00, 
                price=39.99, 
                stock_level=35, 
                description='Precision Bluetooth mouse with ergonomic design'
            ),
            Product(
                name='Cotton T-Shirt', 
                category='Clothing', 
                cost=8.00, 
                price=19.99, 
                stock_level=60, 
                description='100% organic cotton t-shirt in various colors'
            ),
            Product(
                name='Stainless Steel Water Bottle', 
                category='Home', 
                cost=12.00, 
                price=29.99, 
                stock_level=25, 
                description='Insulated stainless steel water bottle keeps drinks cold/hot'
            ),
            Product(
                name='Yoga Mat Pro', 
                category='Sports', 
                cost=20.00, 
                price=59.99, 
                stock_level=18, 
                description='Professional-grade yoga mat with superior grip and cushioning'
            )
        ]
        
        for product in sample_products:
            product.save()
        
        return sample_products
    
    return safe_operation(_create, "Sample products creation")

def create_sample_sales():
    """Create sample sales transactions"""
    def _create():
        sales_data = [
            {
                'products': [{'id': 1, 'quantity': 2, 'name': 'iPhone 15 Pro'}],
                'payment_type': 'Credit Card',
                'total': 2399.98
            },
            {
                'products': [{'id': 5, 'quantity': 3, 'name': 'Colombian Coffee Beans'}],
                'payment_type': 'Cash',
                'total': 74.97
            },
            {
                'products': [
                    {'id': 7, 'quantity': 1, 'name': 'Wireless Earbuds Pro'},
                    {'id': 9, 'quantity': 1, 'name': 'Bluetooth Wireless Mouse'}
                ],
                'payment_type': 'Debit Card',
                'total': 139.98
            },
            {
                'products': [{'id': 10, 'quantity': 5, 'name': 'Cotton T-Shirt'}],
                'payment_type': 'Credit Card',
                'total': 99.95
            },
            {
                'products': [
                    {'id': 11, 'quantity': 2, 'name': 'Stainless Steel Water Bottle'},
                    {'id': 12, 'quantity': 1, 'name': 'Yoga Mat Pro'}
                ],
                'payment_type': 'Mobile Payment',
                'total': 119.97
            }
        ]
        
        created_sales = []
        
        for sale_data in sales_data:
            # Create sale
            sale = Sale(
                total_amount=sale_data['total'],
                payment_type=sale_data['payment_type']
            )
            sale.save()
            
            # Create order items and update stock
            for product_data in sale_data['products']:
                product = Product.query.get(product_data['id'])
                if product and product.is_in_stock(product_data['quantity']):
                    # Create order item
                    sales_item = SalesItem(
                        sale_id=sale.id,
                        product_id=product_data['id'],
                        quantity=product_data['quantity'],
                        unit_price=product.price,
                        product_name=product_data['name']
                    )
                    sales_item.save()
                    
                    # Update stock
                    if product.reduce_stock(product_data['quantity']):
                        product.save()
            
            created_sales.append(sale)
        
        return created_sales
    
    return safe_operation(_create, "Sample sales creation")

def populate_database(reset=False):
    """Main function to populate the database"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting database population...")
        print("=" * 60)
        
        # Check database lock
        if not check_database_lock():
            print("❌ Cannot proceed with database population")
            return False
        
        # Reset database if requested
        if reset:
            print("🔄 Resetting database...")
            db.drop_all()
            db.create_all()
            print("✅ Database reset completed")
        else:
            # Create tables if they don't exist
            db.create_all()
        
        # Check if database is already populated
        if not reset and User.query.first():
            print("⚠️  Database already contains data")
            response = input("Do you want to continue and add more data? (y/N): ").strip().lower()
            if response != 'y':
                print("👋 Operation cancelled")
                return False
        
        try:
            # Create admin user
            print("\n📝 Creating admin user...")
            admin_user = create_admin_user()
            
            # Create sample products
            print("\n📦 Creating sample products...")
            products = create_sample_products()
            print(f"   Created {len(products)} products")
            
            # Create sample sales
            print("\n💰 Creating sample sales...")
            sales = create_sample_sales()
            print(f"   Created {len(sales)} sales transactions")
            
            print("\n" + "=" * 60)
            print("🎉 DATABASE POPULATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("ADMIN CREDENTIALS:")
            print("  Username: admin")
            print("  Password: StoreAdmin2025!")
            print("=" * 60)
            print(f"📊 SUMMARY:")
            print(f"  Users created: 1")
            print(f"  Products created: {len(products)}")
            print(f"  Sales created: {len(sales)}")
            print(f"  Total revenue: ${sum(sale.total_amount for sale in sales):.2f}")
            print("=" * 60)
            print("🌐 Ready to start your store management system!")
            print("   Run: python run.py")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Database population failed: {str(e)}")
            db.session.rollback()
            return False

def show_database_info():
    """Show current database information"""
    app = create_app()
    
    with app.app_context():
        print("📊 DATABASE INFORMATION")
        print("=" * 40)
        
        # Users
        user_count = User.query.count()
        print(f"👤 Users: {user_count}")
        if user_count > 0:
            users = User.query.all()
            for user in users:
                print(f"   - {user.username} ({user.email})")
        
        # Products
        product_count = Product.query.count()
        print(f"📦 Products: {product_count}")
        if product_count > 0:
            categories = db.session.query(Product.category, db.func.count(Product.id)).group_by(Product.category).all()
            for category, count in categories:
                print(f"   - {category}: {count} products")
        
        # Sales
        sale_count = Sale.query.count()
        total_revenue = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
        print(f"💰 Sales: {sale_count}")
        print(f"💵 Total Revenue: ${total_revenue:.2f}")
        
        # Low stock products
        low_stock = Product.query.filter(Product.stock_level <= 10).count()
        if low_stock > 0:
            print(f"⚠️  Low stock alerts: {low_stock} products")
        
        print("=" * 40)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'reset':
            print("🔄 Resetting and populating database...")
            populate_database(reset=True)
        elif command == 'info':
            show_database_info()
        elif command == 'help':
            print("Database Population Script")
            print("=" * 30)
            print("Usage: python populate_db.py [command]")
            print()
            print("Commands:")
            print("  (no args)  - Populate database (safe, won't overwrite)")
            print("  reset      - Reset and populate database")
            print("  info       - Show current database information")
            print("  help       - Show this help message")
            print()
            print("Examples:")
            print("  python populate_db.py")
            print("  python populate_db.py reset")
            print("  python populate_db.py info")
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python populate_db.py help' for available commands")
    else:
        # Default: safe population
        populate_database(reset=False)
