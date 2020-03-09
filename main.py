from Weyoutube import create_app, socketio

# Call the Application Factory function to construct a Flask application instance
# using the standard configuration defined in /instance/flask.cfg
app = create_app('dev.cfg')
socketio.run(app, host='0.0.0.0', port=5000)