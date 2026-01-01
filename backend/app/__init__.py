from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    CORS(app)

    # Register database teardown
    from app import database
    app.teardown_appcontext(database.close_db)

    # Initialize database if it doesn't exist
    with app.app_context():
        database.init_db()

    from app import routes
    app.register_blueprint(routes.bp)

    return app
