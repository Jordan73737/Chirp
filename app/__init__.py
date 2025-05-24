from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config
from flask_wtf import CSRFProtect


db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect() 
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.secret_key = app.config['SECRET_KEY'] 
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    from .routes import main
    app.register_blueprint(main)
    from app import models

    return app

