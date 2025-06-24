import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager, mail
from config import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configure the upload folder
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    login_manager.login_view = 'routes.login' # Adjusted for blueprint
    login_manager.login_message_category = 'info'

    with app.app_context():
        # Import models to ensure tables are created
        import models
        
        # Set up the user loader for Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

        # Import and register blueprints
        import routes
        app.register_blueprint(routes.bp)
        
        # Register Jinja2 global for format_status
        from utils import format_status
        app.jinja_env.globals['format_status'] = format_status
        
        # Create all database tables
        db.create_all()

    return app
