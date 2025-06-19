
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Use environment variable or default to development
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Use the simple Config class for now
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import main
    app.register_blueprint(main)

    # Import models so they're registered
    with app.app_context():
        from .models import user, products, sales

    return app
