# Import the core Flask class
from flask import Flask

# Import SQLAlchemy for database ORM
from flask_sqlalchemy import SQLAlchemy

# Import Flask-Login for user session management (login/logout)
from flask_login import LoginManager

# Import Flask-Mail to send emails (like ppassword reset, notifications)
from flask_mail import Mail

# Import Flask-Migrate for database migrations 
from flask_migrate import Migrate

# Import the configuration class (does app settings like secret keys and DB Uris)
from config import Config

# Import CSRF protection for secure form handling
from flask_wtf import CSRFProtect

# Import Flask-SocketIO to enable real-time WebSocket communication
from flask_socketio import SocketIO


# Initialize extensions without binding them to the app yet - basically delaying app creation until runtime
db = SQLAlchemy()                     # Handles database connections and models
login_manager = LoginManager()        # Manages user login sessions
mail = Mail()                         # Used to send emails
migrate = Migrate()                   # Handles database migrations
csrf = CSRFProtect()                  # Protects forms from CSRF attacks

# Set up Socket.IO for real-time communication
# - CORS is open to all origins 
# - async_mode is set to "threading" for compatibility
# - logger flags enable debug output in the terminal
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading", logger=True, engineio_logger=True)


# Factory function to create and configure the Flask app
def create_app():
    app = Flask(__name__)  # Create the Flask app instance
    app.config.from_object(Config)  # Load configuration from the Config class

    app.secret_key = app.config['SECRET_KEY']  # Set the secret key for sessions and CSRF

    # Initialize all extensions with the app
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # Register the main blueprint 
    from .routes import main
    app.register_blueprint(main)

    # Import models so they are registered with SQLAlchemy
    from app import models

    # Import socket event handlers so they get registered
    from app import socket_events

    return app  # Return the configured app instance
