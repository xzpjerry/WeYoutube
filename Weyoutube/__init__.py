from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from Weyoutube.config import config

#######################
#### Configuration ####
#######################

db = SQLAlchemy()
socketio = SocketIO()
login_manager = LoginManager()

######################################
#### Application Factory Function ####
######################################

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    initialize_extensions(app)
    register_blueprints(app)
    return app

##########################
#### Helper Functions ####
##########################

def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)

    db.init_app(app)
    socketio.init_app(app)
    # Flask-Login configuration
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'cinema.index'
    login_manager.init_app(app=app)
    from Weyoutube.models import User
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

    app.app_context().push()

    if app.config.get('TESTING', False):
        db.create_all()

def register_blueprints(app):
    # Since the application instance is now created, register each Blueprint
    # with the Flask application instance (app)
    from Weyoutube.cinema import cinema_blueprint
    app.register_blueprint(cinema_blueprint)

app = create_app()