import os
from app import create_app

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 7200))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting Flask Store Management System...")
    print(f"📍 Running on: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Check if database has data
    with app.app_context():
        from app.models.user import User
        if not User.query.first():
            print()
            print("⚠️  No admin user found in database!")
            print("🔧 Run: python populate_db.py")
            print("   or: python populate_db.py reset")
            print()
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        print("👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")