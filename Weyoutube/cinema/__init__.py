"""
The recipes Blueprint handles the creation, modification, deletion,
and viewing of recipes for this application.
"""
from flask import Blueprint
cinema_blueprint = Blueprint('cinema', __name__, static_folder='static', template_folder='templates')

from . import routes
